"""
Post-sync invariant audit. Runs after sync_pluggy/rebucket/dedup and reports
every state the sync pipeline should never produce.

Exists because every bug this checks for was silent: Pluggy rewrites
descriptions and re-delivers the same charge through a second endpoint, and the
flags derived from those fields are written once at INSERT and never revisited.
The car-financing boleto sat mis-flagged for five months; the duplicated ACUAS
positions rode three closed invoices. Nothing failed loudly — a human noticed a
number that looked wrong.

Checks (each independent; all are reported, exit code reflects the worst):

  A  orphan/mismatched category — subcategory set with category NULL, or a
     category that is not the subcategory's own parent. The budget cards filter
     by category, so the row silently leaves every per-category total.

  B  internal transfer on a committed item — a txn flagged
     is_internal_transfer=True while linked to a template-backed
     Fixo/Investimento recurring. A bill payment is internal; a financing
     boleto is real spending. The flag comes from the description, which
     Pluggy rewrites.

  C  settled without evidence — RecurringMapping status='mapped' with no linked
     transaction. Pending amounts read the transactions, so the row is not just
     cosmetic: the payment lands in variable spending instead of fixo.

  D  position billed twice — the same installment position on the same
     invoice_month. CANDIDATES, not proof: two separate purchases at the same
     merchant, same amount and same plan, made in one cycle, land position N on
     one invoice legitimately. Every group needs a human before anything is
     deleted.

  F  cross-month link integrity — a checking transaction claimed by more than
     one mapping (which would net an advance twice), a non-adjacent checking
     claim, or a malformed pair where an other-month transaction sits in
     `transactions` without its `cross_month_transactions` marker. Card links
     are exempt from adjacency: Pluggy stamps the purchase date, so a September
     instalment legitimately bills in February.

  G  bill reconciliation conflict — a closed Pluggy bill whose total disagrees
     with the stored invoice amount. Sync refuses to write and records it; this
     surfaces the ones nobody has resolved yet. Gates the exit code: it means a
     bank statement and the aggregator disagree about money.

  E  installment metadata missing — installment_info parsed from the
     description but is_installment=False. Today's sync sets both together, so
     these are historical rows; they are invisible to any check keyed on the
     flag, which is why dedup_installments never saw them.

Exit codes:
  0 — clean, or violations only in categories under their threshold
  1 — at least one threshold exceeded

Thresholds default to 0 (any violation fails). Pass --warn-only for a report
that never fails the cron job.
"""
import re
from collections import defaultdict

from django.core.management.base import BaseCommand

from api.models import (
    BillReconciliationConflict, Profile, RecurringMapping, Transaction,
)

# A mapping whose month is older than this is import backlog, not a live
# regression — same cutoff the carryover uses.
MIN_MONTH = '2026-01'

_POS_SUFFIX = re.compile(r'\s*\d{1,2}/\d{1,2}\s*$')


def _month_gap(a, b):
    """Months from b to a, or None if either is unparseable."""
    try:
        return ((int(a[:4]) * 12 + int(a[5:7]))
                - (int(b[:4]) * 12 + int(b[5:7])))
    except (ValueError, IndexError):
        return None


def _merchant_key(description):
    return _POS_SUFFIX.sub('', description or '').strip().upper()[:20]


class Command(BaseCommand):
    help = 'Audit invariants the sync pipeline must never violate.'

    def add_arguments(self, parser):
        parser.add_argument('--profile', help='Profile name. Default: all active.')
        parser.add_argument('--min-month', default=MIN_MONTH,
                            help=f'Ignore mappings older than this (default {MIN_MONTH}).')
        parser.add_argument('--warn-only', action='store_true',
                            help='Always exit 0. Report only.')
        parser.add_argument('--max-violations', type=int, default=0,
                            help='Per-check tolerance before failing (default 0).')
        # A, B and G gate. C ("mapped" with nothing linked) is import backlog
        # a human triages; E (no installment metadata) is a risk indicator, not
        # a wrong state; and D yields CANDIDATES — two real purchases can share
        # merchant, amount, plan and starting invoice. A and B are the only
        # states the pipeline cannot reach without regressing. G means a bank
        # statement and the aggregator disagree about money — always worth a stop.
        parser.add_argument('--fail-on', default='A,B,G',
                            help='Checks that gate the exit code (default A,B,G).')

    def _profiles(self, arg):
        qs = Profile.objects.filter(is_active=True)
        if arg:
            qs = qs.filter(name__iexact=arg)
        return list(qs)

    # ---- checks: each returns (count, [lines]) ----------------------------

    def _check_a(self, profile, min_month):
        # Scoped by month like check C: this is a regression detector for the
        # live pipeline, not a cleaner for years of imported backlog.
        lines = []
        rows = Transaction.objects.filter(
            profile=profile, subcategory__isnull=False, month_str__gte=min_month,
        ).select_related('subcategory__category', 'category')
        for t in rows:
            if t.category_id is None:
                why = f'sem categoria (sub {t.subcategory})'
            elif t.category_id != t.subcategory.category_id:
                why = (f'categoria {t.category.name} != pai da sub '
                       f'{t.subcategory.category.name} > {t.subcategory.name}')
            else:
                continue
            lines.append(
                f'{t.date} {t.month_str} R${abs(t.amount):>10} '
                f'{t.description[:32]} -> {why}')
        return len(lines), lines[:20]

    def _linked(self, mapping):
        """Every link form, deduped by id. cross_month_transactions is normally
        a subset of transactions, but restored or imported data need not hold
        that, so a check that reads only one of them can miss a link."""
        rows = {t.id: t for t in mapping.transactions.all()}
        rows.update({t.id: t for t in mapping.cross_month_transactions.all()})
        if mapping.transaction_id and mapping.transaction_id not in rows:
            rows[mapping.transaction_id] = mapping.transaction
        return list(rows.values())

    def _check_b(self, profile):
        lines = []
        mappings = RecurringMapping.objects.filter(
            profile=profile,
        ).select_related('template', 'transaction').prefetch_related(
            'transactions', 'cross_month_transactions')
        for m in mappings:
            # Template-backed only. A custom mapping is a hand-made bucket (a
            # trip, an event) that legitimately groups transfers, so its rows
            # carry no invariant. A Fixo/Investimento template is a real bill.
            if m.is_custom or not m.template:
                continue
            if m.template.template_type in ('Cartao', 'Income'):
                continue
            for t in self._linked(m):
                if t.is_internal_transfer:
                    lines.append(
                        f'{m.month_str} {m.template.name[:22]:22} '
                        f'R${abs(t.amount):>10} {t.description[:34]}')
        return len(lines), lines[:20]

    def _check_c(self, profile, min_month):
        lines = []
        mappings = RecurringMapping.objects.filter(
            profile=profile, status='mapped', month_str__gte=min_month,
        ).select_related('template', 'transaction').prefetch_related(
            'transactions', 'cross_month_transactions')
        for m in mappings:
            ttype = m.template.template_type if m.template else (m.custom_type or '')
            # Income is excluded on purpose: salary lands in two payments and a
            # partially-received month is legitimately mapped with the residue
            # still pending, so "no transaction" is not an invariant there.
            if ttype == 'Income' or m.match_mode == 'category':
                continue
            if self._linked(m):
                continue
            name = m.custom_name if m.is_custom else (m.template.name if m.template else '?')
            lines.append(f'{m.month_str} {name[:22]:22} esperado R${m.expected_amount:>10}')
        return len(lines), lines[:20]

    def _check_d(self, profile):
        groups = defaultdict(list)
        rows = Transaction.objects.filter(profile=profile).exclude(installment_info='')
        for t in rows:
            info = t.installment_info
            if '/' not in info or not t.invoice_month:
                continue
            try:
                pos, total = (int(x) for x in info.split('/'))
            except ValueError:
                continue
            if total <= 1:
                continue
            groups[(t.account_id, _merchant_key(t.description), abs(t.amount),
                    pos, total, t.invoice_month)].append(t)
        lines, count, value = [], 0, 0
        for key, grp in sorted(groups.items(), key=lambda kv: str(kv[0][1])):
            if len(grp) < 2:
                continue
            extra = len(grp) - 1
            count += extra
            value += float(abs(grp[0].amount)) * extra
            lines.append(
                f'{key[1][:20]:20} {key[3]}/{key[4]} R${abs(grp[0].amount):>10} '
                f'fatura {key[5]} x{len(grp)} ({", ".join(str(t.date) for t in grp)})')
        if lines:
            lines.append(f'valor duplicado: R$ {value:,.2f}')
        return count, lines[:20]

    def _check_f(self, profile):
        from api.models import Account
        checking = set(Account.objects.filter(
            profile=profile, account_type='checking').values_list('id', flat=True))
        lines, claims = [], defaultdict(list)
        mappings = RecurringMapping.objects.filter(
            profile=profile).prefetch_related('transactions', 'cross_month_transactions')
        for m in mappings:
            cross = {t.id: t for t in m.cross_month_transactions.all()}
            trans = {t.id: t for t in m.transactions.all()}
            for t in cross.values():
                if t.account_id in checking:
                    claims[t.id].append(m)
                    gap = _month_gap(m.month_str, t.month_str)
                    if gap is not None and abs(gap) > 1:
                        lines.append(
                            f'não-adjacente {m.month_str} <- {t.month_str} '
                            f'(gap {gap}) R$ {abs(t.amount)} txn {t.id}')
                if t.id not in trans:
                    lines.append(f'cross sem transactions {m.month_str} txn {t.id}')
            for t in trans.values():
                if t.month_str != m.month_str and t.id not in cross:
                    lines.append(
                        f'outro mês sem marcador cross {m.month_str} <- '
                        f'{t.month_str} R$ {abs(t.amount)} txn {t.id}')
        for txn_id, ms in claims.items():
            if len(ms) > 1:
                lines.append('reivindicação dupla txn %s por %s' % (
                    txn_id, ', '.join(sorted(m.month_str for m in ms))))
        return len(lines), lines[:20]

    def _check_g(self, profile):
        rows = BillReconciliationConflict.objects.filter(
            profile=profile, resolution='pending',
        ).order_by('month_str')
        return rows.count(), [
            f'{c.card_name} {c.month_str} | guardado R$ {c.stored_total} != '
            f'Pluggy R$ {c.pluggy_total} | fatura {c.bill_id[:8]} | id {c.id}'
            for c in rows[:20]
        ]

    def _check_e(self, profile):
        rows = Transaction.objects.filter(
            profile=profile, is_installment=False,
        ).exclude(installment_info='')
        return rows.count(), [
            f'{t.date} {t.installment_info:6} R${abs(t.amount):>10} {t.description[:34]}'
            for t in rows[:20]
        ]

    # ----------------------------------------------------------------------

    def handle(self, *args, **opts):
        min_month = opts['min_month']
        tolerance = opts['max_violations']
        gating = {c.strip().upper() for c in opts['fail_on'].split(',') if c.strip()}
        failed = False

        for profile in self._profiles(opts.get('profile')):
            self.stdout.write(f'\n=== {profile.name} ===')
            results = [
                ('A', f'categoria órfã ou divergente da sub (>= {min_month})',
                 *self._check_a(profile, min_month)),
                ('B', 'transferência interna em fixo/invest', *self._check_b(profile)),
                ('C', f'recorrente "pago" sem transação (>= {min_month})',
                 *self._check_c(profile, min_month)),
                ('D', 'parcela repetida na mesma fatura (candidatos)',
                 *self._check_d(profile)),
                ('E', 'parcela sem metadata (cega o dedup)', *self._check_e(profile)),
                ('F', 'vínculo cross-month inconsistente', *self._check_f(profile)),
                ('G', 'fatura: extrato vs Pluggy em conflito', *self._check_g(profile)),
            ]
            for code, label, count, lines in results:
                if count == 0:
                    self.stdout.write(self.style.SUCCESS(f'  OK   {code} {label}: 0'))
                    continue
                gates = code in gating and count > tolerance
                style = self.style.ERROR if gates else self.style.WARNING
                self.stdout.write(style(
                    f'  {"FAIL" if gates else "WARN"} {code} {label}: {count}'))
                for line in lines:
                    self.stdout.write(f'         {line}')
                if gates:
                    failed = True

        if failed and not opts['warn_only']:
            self.stderr.write(self.style.ERROR('\naudit_sync: invariantes violados'))
            raise SystemExit(1)
        self.stdout.write(self.style.SUCCESS('\naudit_sync: fim'))
