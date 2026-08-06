"""
Backfill Transaction.pluggy_purchase_date from live Pluggy data and remove
installment rows that Pluggy re-listed (the SAME purchase + position ingested
more than once — landing in different invoice months or as no-billId copies).

Two complementary, conservative rules. Both KEEP the copy Pluggy still returns
today (authoritative invoice month) and delete only the stale duplicate(s);
recurring-mapping links are transferred onto the surviving keeper first, and a
row is never deleted unless a concrete surviving keeper is found.

  RULE 1 — live↔live: two rows whose external_ids are both in today's Pluggy
    fetch share the same purchase identity (card, purchaseDate, position, total,
    merchant, amount). Keep the billId-backed copy.

  RULE 2 — orphan with a live same-position twin: a row Pluggy no longer returns
    AND whose date is inside the fetch window (so "absent" means dropped, not
    out-of-range) that has the SAME (card, merchant, amount, position) as a live
    row. Only fires on genuine same-position duplication.

  RULE 4 — one purchase recorded under two purchaseDate stamps. Pluggy stamped
    the same plan 97 minutes apart, so every position exists twice with DIFFERENT
    identities and RULE 1 cannot group them (it keys on the full timestamp on
    purpose: two genuine same-day purchases differ by seconds). Same card,
    position, plan, merchant, amount and purchase DAY, with exactly one side
    backed by a bill -> the billed copy is authoritative and the other is the
    extra. This is what made ~R$2.4k of phantom card spending come back after
    every sync: deleting the row is useless while Pluggy keeps returning it, so
    the dedup has to recognise it on each run.

Dry-run by default. Pass --apply to delete.
"""
import os
import re
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction as dbtx

from api.models import Account, Profile, RecurringMapping, Transaction
from api.pluggy import PluggyClient
from api.management.commands.sync_pluggy import (
    PROFILE_CONFIG, _installment_identity, _merchant_base, _pluggy_brl_amount,
)


def _pos(info):
    if not info or '/' not in info:
        return None
    try:
        n, t = (int(x) for x in info.split('/'))
    except ValueError:
        return None
    return (n, t) if t > 1 else None


def _keep_score(t):
    links = t.recurring_mapping_links.count() + t.cross_month_links.count()
    if t.recurring_mappings.exists():
        links += 1
    return (links, 1 if t.is_manually_categorized else 0, 1 if t.invoice_month else 0,
            1 if t.pluggy_category_id else 0, -t.created_at.timestamp())


class Command(BaseCommand):
    help = 'Backfill pluggy_purchase_date and remove re-listed installment duplicates.'

    def add_arguments(self, parser):
        parser.add_argument('--profile', help='Profile name. Default: all in PROFILE_CONFIG.')
        parser.add_argument('--apply', action='store_true', help='Delete duplicates (default: dry-run).')
        parser.add_argument('--days', type=int, default=400, help='Pluggy lookback window.')
        parser.add_argument('--delete-id', help='Targeted merge: transaction to delete.')
        parser.add_argument('--keep-id', help='Targeted merge: transaction to keep.')
        parser.add_argument('--force', action='store_true',
                            help='Targeted merge: skip the compatibility guards.')
        parser.add_argument(
            '--strict', action='store_true',
            help='Treat a failed upstream fetch as fatal instead of logging and '
                 'continuing. Partial bill coverage changes which rows are '
                 'considered bill-backed, so a mutating run must refuse it.')


    def _profiles(self, arg):
        if arg:
            return Profile.objects.filter(name__iexact=arg)
        return Profile.objects.filter(name__in=list(PROFILE_CONFIG.keys()))

    def _fetch_live(self, profile, days):
        """Return (live_ext, ext_to_ident, inst_winner, billed_ext). ext_to_ident maps a
        live external_id -> its full installment identity; inst_winner maps an
        identity -> the external_id to keep (billId-backed preferred)."""
        cfg = PROFILE_CONFIG.get(profile.name)
        client = PluggyClient(os.environ.get('PLUGGY_CLIENT_ID', ''),
                              os.environ.get('PLUGGY_CLIENT_SECRET', ''))
        amap = cfg['account_map']
        from_date = (date.today() - timedelta(days=days)).isoformat()
        to_date = date.today().isoformat()
        bill_map = {}
        for pid, vname in amap.items():
            a = Account.objects.filter(profile=profile, name=vname).first()
            if a and a.account_type == 'credit_card':
                try:
                    for b in client.get_bills(pid):
                        bill_map[b['id']] = b['dueDate'][:7]
                except Exception as e:
                    self.stderr.write(f'  bills fail {vname}: {e}')
                    if self.strict:
                        raise CommandError(
                            f'--strict: cobertura incompleta, faturas de '
                            f'{vname} não carregaram ({e})')
        live_ext, ext_to_ident, inst_winner = set(), {}, {}
        billed_ext = set()   # external_ids whose billId resolves to a real bill
        for pid, vname in amap.items():
            a = Account.objects.filter(profile=profile, name=vname).first()
            if not (a and a.account_type == 'credit_card'):
                continue
            for t in client.get_transactions(pid, from_date, to_date):
                live_ext.add(t['id'])
                meta = t.get('creditCardMetadata') or {}
                desc = t.get('description') or t.get('descriptionRaw', '')
                ident = _installment_identity(meta, desc, _pluggy_brl_amount(t))
                if ident is None:
                    continue
                ext_to_ident[t['id']] = ident
                bid = meta.get('billId', '')
                has_bill = bool(bid and bid in bill_map)
                if has_bill:
                    billed_ext.add(t['id'])
                cur = inst_winner.get(ident)
                if cur is None or (has_bill and not cur[1]):
                    inst_winner[ident] = (t['id'], has_bill)
        return (live_ext, ext_to_ident,
                {k: v[0] for k, v in inst_winner.items()}, billed_ext)

    @staticmethod
    def _rule4(rows, ext_to_ident, billed_ext, decided=None):
        """See RULE 4 in the module docstring. Returns {delete_id: keep_id}."""
        decided = decided or {}
        out, by_plan = {}, defaultdict(list)
        for t in rows:
            ident = ext_to_ident.get(t.external_id)
            p = _pos(t.installment_info)
            if ident is None or not p:
                continue
            # ident = (card, purchaseDate, position, total, merchant, amount);
            # group on everything EXCEPT the timestamp, keeping the purchase DAY.
            by_plan[(ident[0], ident[2], ident[3], ident[4], ident[5],
                     ident[1][:10])].append(t)
        for grp in by_plan.values():
            if len(grp) < 2:
                continue
            billed = [t for t in grp if t.external_id in billed_ext]
            unbilled = [t for t in grp if t.external_id not in billed_ext]
            if not billed or not unbilled:
                continue        # no bill asymmetry — nothing to decide with
            keep = sorted(billed, key=_keep_score, reverse=True)[0]
            if keep.id in decided:
                continue
            for d in unbilled:
                if d.id not in decided:
                    out[d.id] = keep.id
        return out

    @staticmethod
    def _categorization_conflict(src, dst):
        """True when merging would have to pick between two human decisions."""
        return (src.is_manually_categorized and dst.is_manually_categorized
                and src.category_id != dst.category_id)

    def _transfer_links(self, src, dst):
        """Move every link off `src` onto `dst`, and carry categorization when
        the keeper has none — the row being deleted may be the categorized one
        (the keeper is chosen by link count first), and category drives every
        per-category total. Returns the mappings whose linked set changed."""
        RecurringMapping.objects.filter(transaction=src).update(transaction=dst)
        touched = set()
        for m in src.recurring_mapping_links.all():
            m.transactions.add(dst)
            touched.add(m)
        for m in src.cross_month_links.all():
            m.cross_month_transactions.add(dst)
            touched.add(m)
        if src.category_id and not dst.category_id:
            dst.category_id = src.category_id
            dst.subcategory_id = src.subcategory_id
            dst.is_manually_categorized = src.is_manually_categorized
            dst.save(update_fields=['category', 'subcategory',
                                    'is_manually_categorized'])
        return touched

    @staticmethod
    def _recompute_actual(mapping):
        """Both duplicates could be linked to the same mapping, so dropping one
        shrinks the linked set and leaves actual_amount stale (doubled). Same
        Income-vs-expense rule the service layer uses."""
        ctype = mapping.custom_type if mapping.is_custom else (
            mapping.template.template_type if mapping.template else '')
        txns = mapping.transactions.all()
        mapping.actual_amount = (sum(t.amount for t in txns) if ctype == 'Income'
                                 else sum(abs(t.amount) for t in txns))
        mapping.save(update_fields=['actual_amount'])

    def _targeted_merge(self, del_id, keep_id, apply, force):
        """Merge one reviewed pair. The rules decide sets; this decides nothing —
        a human already did, with the issued invoice in hand.

        Guarded so an id typo cannot turn a conservative maintenance command
        into arbitrary deletion.
        """
        try:
            d = Transaction.objects.get(id=del_id)
            k = Transaction.objects.get(id=keep_id)
        except Transaction.DoesNotExist as e:
            raise CommandError(f'Transação não encontrada: {e}')
        if d.id == k.id:
            raise CommandError('delete-id e keep-id são a mesma transação.')
        if not force:
            if d.profile_id != k.profile_id:
                raise CommandError('Perfis diferentes.')
            if d.account_id != k.account_id:
                raise CommandError('Contas diferentes — use --force se for intencional.')
            if (d.amount > 0) != (k.amount > 0):
                raise CommandError('Sinais opostos: um é estorno, o outro é compra.')
            if abs(abs(d.amount) - abs(k.amount)) > Decimal('0.01'):
                raise CommandError(
                    f'Valores diferentes ({d.amount} vs {k.amount}) — use --force.')
            if self._categorization_conflict(d, k):
                raise CommandError(
                    f'Duas categorizações manuais divergentes '
                    f'({d.category} vs {k.category}) — resolva antes.')
        self.stdout.write(
            f'  apagar {d.date} {d.installment_info or "-":6} R${abs(d.amount):>9} '
            f'fatura {d.invoice_month} ext {d.external_id[:8]} cat {d.category}')
        self.stdout.write(
            f'  manter {k.date} {k.installment_info or "-":6} R${abs(k.amount):>9} '
            f'fatura {k.invoice_month} ext {k.external_id[:8]} cat {k.category}')
        if not apply:
            self.stdout.write(self.style.WARNING('  (dry-run)'))
            return
        with dbtx.atomic():
            touched = self._transfer_links(d, k)
            d.delete()
            for m in touched:
                self._recompute_actual(m)
        self.stdout.write(self.style.SUCCESS('  merge aplicado'))

    def handle(self, *args, **opts):
        self.strict = opts.get('strict', False)
        if opts.get('delete_id') or opts.get('keep_id'):
            if not (opts.get('delete_id') and opts.get('keep_id')):
                raise CommandError('--delete-id e --keep-id andam juntos.')
            return self._targeted_merge(
                opts['delete_id'], opts['keep_id'], opts['apply'], opts['force'])
        apply = opts['apply']
        cutoff = date.today() - timedelta(days=opts['days'])
        grand = 0
        for profile in self._profiles(opts.get('profile')):
            self.stdout.write(f'\n=== {profile.name} ===')
            live_ext, ext_to_ident, inst_winner, billed_ext = self._fetch_live(
                profile, opts['days'])
            rows = list(Transaction.objects.filter(
                profile=profile, is_installment=True,
                source_file__startswith='pluggy:').exclude(external_id=''))
            by_id = {t.id: t for t in rows}

            # 1. Backfill purchase_date from live identity (purchaseDate = ident[1]).
            backfilled = 0
            for t in rows:
                ident = ext_to_ident.get(t.external_id)
                if t.pluggy_purchase_date is None and ident:
                    backfilled += 1
                    if apply:
                        t.pluggy_purchase_date = date.fromisoformat(ident[1][:10])
                        t.save(update_fields=['pluggy_purchase_date'])
            self.stdout.write(f'  purchase_date backfill: {backfilled}'
                              + ('' if apply else ' (dry-run)'))

            decided = {}  # delete_id -> keep_id

            # RULE 1: live↔live duplicate by full purchase identity.
            g = defaultdict(list)
            for t in rows:
                ident = ext_to_ident.get(t.external_id)
                if ident is not None:           # only live rows have an identity here
                    g[ident].append(t)
            for ident, grp in g.items():
                if len(grp) < 2:
                    continue
                we = inst_winner.get(ident)
                keep = next((r for r in grp if r.external_id == we), None) \
                    or sorted(grp, key=_keep_score, reverse=True)[0]
                for d in grp:
                    if d.id != keep.id:
                        decided[d.id] = keep.id

            # Live same-position index for RULE 2. Key = (card, merchant, amount,
            # position) -> {live row ids, distinct purchaseDates}. The orphan has
            # no purchaseDate, so RULE 2 only fires when this key maps to EXACTLY
            # ONE live purchaseDate (an unambiguous single purchase). If the same
            # merchant+amount+position belongs to several distinct purchases
            # (different purchaseDates — e.g. repeated PETZ buys), the orphan is
            # ambiguous and is left untouched.
            live_pos = defaultdict(lambda: {'ids': [], 'pdates': set()})
            # Same index keyed on the ACCOUNT instead of the card, for orphans
            # that predate card_last4 (833 of Palmer's 1135 installment rows and
            # 132 of Rafa's 184 carry no card at all, so keying RULE 2 on the
            # card alone silently retires the rule for most of the history —
            # that is why Rafa's duplicated RENEGOCIAÇÃO 1/2 sat undecidable for
            # months while its live, bill-backed twin sat right there).
            #
            # `rows` is scoped per profile, not per card, so the account FK is
            # what keeps a blank-card orphan on card X from adopting a live twin
            # on card Y — a series lives on one account and the FK is always
            # populated, unlike card_last4. The live side's card is taken from
            # the Pluggy identity rather than the stored column, so a live row
            # whose column happens to be blank cannot make the set look
            # unambiguous; the twin must still resolve to exactly one card.
            live_pos_acct = defaultdict(lambda: {'ids': [], 'pdates': set(), 'cards': set()})
            for t in rows:
                ident = ext_to_ident.get(t.external_id)
                p = _pos(t.installment_info)
                if ident is not None and p:
                    mb = _merchant_base(t.description)
                    e = live_pos[(t.card_last4 or '', mb, abs(t.amount), p)]
                    e['ids'].append(t.id)
                    e['pdates'].add(ident[1])
                    e2 = live_pos_acct[(t.account_id, mb, abs(t.amount), p)]
                    e2['ids'].append(t.id)
                    e2['pdates'].add(ident[1])
                    e2['cards'].add(ident[0] or '')

            # RULE 2: in-window orphan whose same-position live twin is unambiguous.
            for t in rows:
                if t.external_id in live_ext or t.id in decided or t.date < cutoff:
                    continue
                p = _pos(t.installment_info)
                if not p:
                    continue
                mb = _merchant_base(t.description)
                if t.card_last4:
                    e = live_pos.get((t.card_last4, mb, abs(t.amount), p))
                else:
                    e = live_pos_acct.get((t.account_id, mb, abs(t.amount), p))
                    if e and len(e['cards']) != 1:
                        continue   # twin spans more than one card — ambiguous
                if not e or len(e['pdates']) != 1:
                    continue   # no live twin, or ambiguous (repeated purchases)
                keep_id = next((c for c in e['ids'] if c not in decided), None)
                if keep_id is not None:
                    decided[t.id] = keep_id

            # Never merge across two conflicting human decisions — that would
            # silently discard one of them. Leave the pair for review.
            for del_id, keep_id in list(decided.items()):
                if self._categorization_conflict(by_id[del_id], by_id[keep_id]):
                    self.stdout.write(self.style.WARNING(
                        f'  SKIP {by_id[del_id].date} {by_id[del_id].description[:26]}: '
                        f'categorização manual conflitante '
                        f'({by_id[del_id].category} vs {by_id[keep_id].category})'))
                    del decided[del_id]

            # RULE 4 — one purchase, two purchaseDate stamps. Pluggy recorded the
            # ACUAS plan twice, 97 minutes apart (13:22:31Z and 15:00:01Z), so the
            # two copies of every position get DIFFERENT identities and RULE 1 —
            # which keys on the full timestamp on purpose, because two genuine
            # same-day purchases differ by seconds — can never group them.
            #
            # Decidable from live data without loosening that identity: same card,
            # same position of the same plan, same merchant, same amount, same
            # purchase DAY, and exactly one side backed by a bill. The bill is the
            # authority; the copy Pluggy cannot place on an invoice is the extra.
            decided.update(self._rule4(rows, ext_to_ident, billed_ext, decided))

            for del_id, keep_id in sorted(decided.items(), key=lambda kv: str(by_id[kv[0]].date)):
                d = by_id[del_id]
                self.stdout.write(
                    f'  DUP {d.date} im={d.invoice_month} {d.installment_info:6} '
                    f'R${abs(d.amount):>8} {d.description[:26]:26} keep={by_id[keep_id].external_id[:8]}')
            self.stdout.write(f'  duplicates to delete: {len(decided)}')
            grand += len(decided)

            if apply and decided:
                with dbtx.atomic():
                    touched = set()
                    for del_id, keep_id in decided.items():
                        d = by_id[del_id]
                        keep = by_id[keep_id]
                        touched |= self._transfer_links(d, keep)
                        d.delete()
                    for m in touched:
                        self._recompute_actual(m)
                self.stdout.write(self.style.SUCCESS(f'  deleted {len(decided)} rows'))

        if apply:
            self.stdout.write(self.style.SUCCESS(f'\nTotal deleted: {grand}'))
        else:
            self.stdout.write(self.style.WARNING(
                f'\nDry-run. {grand} duplicate rows would be deleted. Re-run with --apply.'))
