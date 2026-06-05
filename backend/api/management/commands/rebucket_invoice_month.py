"""
Correct invoice_month on existing Pluggy CC transactions from the AUTHORITATIVE
Pluggy billId -> bill dueDate mapping.

Itaú's statement closing day is not fixed — it drifts ~27-29 month to month — so
the date heuristic in sync_pluggy (used when a transaction has no billId yet)
mis-buckets charges dated near the boundary into an adjacent invoice month. Once
a bill closes, Pluggy stamps the transaction with a billId whose dueDate gives
the exact invoice month. This command re-reads the live billId for each existing
CC transaction and fixes invoice_month to match the bank.

Two corrections, both only when the stored invoice_month differs:
  1. billId present -> set invoice_month to the bill's dueDate month (exact).
  2. No billId yet, charge still tagged the JUST-CLOSED bill's month (the latest
     dueDate month): that bill is final — its total is fixed and it will not gain
     charges — so the charge belongs to the OPEN (next) bill. Applied only to
     due-next-month (Itaú-style) cards; NuBank's intra-month cycle is left to (1).

Does NOT change month_str (purchase month), so gastos_variaveis and recurring
links are unaffected; fatura_total uses Pluggy bill totals. Only per-invoice-month
CC transaction views move — toward the bank.

Dry-run by default. Pass --apply to write.
"""
import os
from collections import Counter
from datetime import date, timedelta

from django.core.management.base import BaseCommand

from api.models import Account, Profile, Transaction
from api.pluggy import PluggyClient
from api.management.commands.sync_pluggy import PROFILE_CONFIG


def _add_month(ym):
    y, m = int(ym[:4]), int(ym[5:7])
    return f'{y + 1}-01' if m == 12 else f'{y}-{m + 1:02d}'


class Command(BaseCommand):
    help = 'Fix invoice_month on existing Pluggy CC transactions from the Pluggy billId mapping.'

    def add_arguments(self, parser):
        parser.add_argument('--profile', help='Profile name. Default: all in PROFILE_CONFIG.')
        parser.add_argument('--apply', action='store_true', help='Write changes (default: dry-run).')
        parser.add_argument('--days', type=int, default=400, help='Pluggy lookback window.')

    def _profiles(self, arg):
        if arg:
            return Profile.objects.filter(name__iexact=arg)
        return Profile.objects.filter(name__in=list(PROFILE_CONFIG.keys()))

    def handle(self, *args, **opts):
        apply = opts['apply']
        grand = 0
        for profile in self._profiles(opts.get('profile')):
            self.stdout.write(f'\n=== {profile.name} ===')
            cfg = PROFILE_CONFIG.get(profile.name)
            if not cfg:
                self.stdout.write('  no Pluggy config for this profile — skipping')
                continue
            client = PluggyClient(os.environ.get('PLUGGY_CLIENT_ID', ''),
                                  os.environ.get('PLUGGY_CLIENT_SECRET', ''))
            amap = cfg['account_map']
            from_date = (date.today() - timedelta(days=opts['days'])).isoformat()
            to_date = date.today().isoformat()

            cc_ids, bill_map = [], {}
            max_due, latest_close, latest_close_inv = None, None, None
            for pid, vname in amap.items():
                a = Account.objects.filter(profile=profile, name=vname).first()
                if a and a.account_type == 'credit_card':
                    cc_ids.append(a.id)
                    try:
                        for b in client.get_bills(pid):
                            inv = b['dueDate'][:7]
                            bill_map[b['id']] = inv
                            if max_due is None or inv > max_due:
                                max_due = inv
                            ca = b.get('createdAt')
                            if ca:
                                cd = date.fromisoformat(ca[:10])
                                if latest_close is None or cd > latest_close:
                                    latest_close, latest_close_inv = cd, inv
                    except Exception as e:
                        self.stderr.write(f'  bills fail {vname}: {e}')

            # Is this an Itaú-style cycle (bill due the month AFTER it closes)?
            # NuBank closes mid-month and is due the same month — its open-bill
            # rule differs, so we only apply the unbilled fix to due-next-month
            # cards; NuBank still gets the authoritative billId correction.
            due_next_month = bool(
                latest_close and latest_close_inv == _add_month(latest_close.strftime('%Y-%m')))
            open_month = _add_month(max_due) if max_due else None

            # external_id -> authoritative invoice_month (billId)
            ext_invm = {}
            for pid, vname in amap.items():
                a = Account.objects.filter(profile=profile, name=vname).first()
                if not (a and a.account_type == 'credit_card'):
                    continue
                for t in client.get_transactions(pid, from_date, to_date):
                    bid = (t.get('creditCardMetadata') or {}).get('billId', '')
                    if bid and bid in bill_map:
                        ext_invm[t['id']] = bill_map[bid]

            moves = Counter()
            to_update = []
            for t in Transaction.objects.filter(
                profile=profile, account_id__in=cc_ids,
                source_file__startswith='pluggy:').exclude(external_id=''):
                auth = ext_invm.get(t.external_id)
                # No billId: the just-closed bill (max_due month) is FINAL — its
                # total is fixed and it won't gain charges — so any charge still
                # tagged that month without a billId belongs to the open (next)
                # bill. Itaú-style (due-next-month) cards only; NuBank's intra-
                # month cycle is left to the billId correction above.
                if (auth is None and due_next_month and open_month
                        and t.invoice_month == max_due):
                    auth = open_month
                if auth and auth != t.invoice_month:
                    moves[(t.invoice_month, auth)] += 1
                    to_update.append((t, auth))
                    self.stdout.write(
                        f'  {t.date} {t.invoice_month} -> {auth}  {t.installment_info:5} '
                        f'R${abs(t.amount):>8} {t.description[:30]}')

            for k, v in sorted(moves.items()):
                self.stdout.write(f'  [{k[0]} -> {k[1]}] x{v}')
            self.stdout.write(f'  invoice_month corrections: {len(to_update)}'
                              + ('' if apply else ' (dry-run)'))
            grand += len(to_update)

            if apply and to_update:
                for t, auth in to_update:
                    t.invoice_month = auth
                    t.save(update_fields=['invoice_month'])
                self.stdout.write(self.style.SUCCESS(f'  updated {len(to_update)} rows'))

        if apply:
            self.stdout.write(self.style.SUCCESS(f'\nTotal corrected: {grand}'))
        else:
            self.stdout.write(self.style.WARNING(
                f'\nDry-run. {grand} invoice_month corrections. Re-run with --apply.'))
