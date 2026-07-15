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

Dry-run by default. Pass --apply to delete.
"""
import os
import re
from collections import defaultdict
from datetime import date, timedelta

from django.core.management.base import BaseCommand
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

    def _profiles(self, arg):
        if arg:
            return Profile.objects.filter(name__iexact=arg)
        return Profile.objects.filter(name__in=list(PROFILE_CONFIG.keys()))

    def _fetch_live(self, profile, days):
        """Return (live_ext, ext_to_ident, inst_winner). ext_to_ident maps a
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
        live_ext, ext_to_ident, inst_winner = set(), {}, {}
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
                cur = inst_winner.get(ident)
                if cur is None or (has_bill and not cur[1]):
                    inst_winner[ident] = (t['id'], has_bill)
        return live_ext, ext_to_ident, {k: v[0] for k, v in inst_winner.items()}

    def _transfer_links(self, src, dst):
        RecurringMapping.objects.filter(transaction=src).update(transaction=dst)
        for m in src.recurring_mapping_links.all():
            m.transactions.add(dst)
        for m in src.cross_month_links.all():
            m.cross_month_transactions.add(dst)

    def handle(self, *args, **opts):
        apply = opts['apply']
        cutoff = date.today() - timedelta(days=opts['days'])
        grand = 0
        for profile in self._profiles(opts.get('profile')):
            self.stdout.write(f'\n=== {profile.name} ===')
            live_ext, ext_to_ident, inst_winner = self._fetch_live(profile, opts['days'])
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
            for t in rows:
                ident = ext_to_ident.get(t.external_id)
                p = _pos(t.installment_info)
                if ident is not None and p:
                    e = live_pos[(t.card_last4 or '', _merchant_base(t.description), abs(t.amount), p)]
                    e['ids'].append(t.id)
                    e['pdates'].add(ident[1])

            # RULE 2: in-window orphan whose same-position live twin is unambiguous.
            for t in rows:
                if t.external_id in live_ext or t.id in decided or t.date < cutoff:
                    continue
                p = _pos(t.installment_info)
                if not p:
                    continue
                e = live_pos.get((t.card_last4 or '', _merchant_base(t.description), abs(t.amount), p))
                if not e or len(e['pdates']) != 1:
                    continue   # no live twin, or ambiguous (repeated purchases)
                keep_id = next((c for c in e['ids'] if c not in decided), None)
                if keep_id is not None:
                    decided[t.id] = keep_id

            for del_id, keep_id in sorted(decided.items(), key=lambda kv: str(by_id[kv[0]].date)):
                d = by_id[del_id]
                self.stdout.write(
                    f'  DUP {d.date} im={d.invoice_month} {d.installment_info:6} '
                    f'R${abs(d.amount):>8} {d.description[:26]:26} keep={by_id[keep_id].external_id[:8]}')
            self.stdout.write(f'  duplicates to delete: {len(decided)}')
            grand += len(decided)

            if apply and decided:
                with dbtx.atomic():
                    for del_id, keep_id in decided.items():
                        d = by_id[del_id]
                        keep = by_id[keep_id]
                        self._transfer_links(d, keep)
                        d.delete()
                self.stdout.write(self.style.SUCCESS(f'  deleted {len(decided)} rows'))

        if apply:
            self.stdout.write(self.style.SUCCESS(f'\nTotal deleted: {grand}'))
        else:
            self.stdout.write(self.style.WARNING(
                f'\nDry-run. {grand} duplicate rows would be deleted. Re-run with --apply.'))
