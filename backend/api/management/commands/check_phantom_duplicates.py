"""
Detect Pluggy/legacy phantom duplicate transactions and exit non-zero
when they exceed a threshold. Designed to run from cron after sync_pluggy.

Exit codes:
  0 — no phantom duplicates above threshold
  1 — phantom duplicates detected (count or value above threshold)

Output is structured (one line per profile) so cron logs are easy to scan.
"""
from collections import defaultdict

from django.core.management.base import BaseCommand

from api.models import Profile, Transaction
from api.services import _normalize_transaction_description


class Command(BaseCommand):
    help = 'Report phantom Pluggy/legacy duplicate transactions per profile'

    def add_arguments(self, parser):
        parser.add_argument(
            '--profile', help='Profile name or UUID. Defaults to all active profiles.',
        )
        parser.add_argument(
            '--max-rows', type=int, default=0,
            help='Exit 1 if phantom row count exceeds this. 0 = warn only, exit 0.',
        )
        parser.add_argument(
            '--max-value', type=float, default=0,
            help='Exit 1 if phantom total value (R$) exceeds this. 0 = warn only.',
        )
        parser.add_argument(
            '--min-len', type=int, default=4,
            help='Skip groups with normalized desc shorter than this (default 4).',
        )

    def _profiles(self, profile_arg):
        qs = Profile.objects.filter(is_active=True)
        if not profile_arg:
            return qs
        by_name = qs.filter(name__iexact=profile_arg)
        if by_name.exists():
            return by_name
        return Profile.objects.filter(id=profile_arg)

    def _phantom_groups(self, profile, min_len):
        """
        Detect phantom Pluggy/legacy pairs using the same logic as
        dedup_phantom_transactions: bucket by (account, abs_amt, desc_key)
        without date, then greedy-match Pluggy↔legacy within ±1 day.
        """
        buckets = defaultdict(list)
        rows = Transaction.objects.filter(profile=profile).values_list(
            'id', 'date', 'amount', 'account_id', 'description', 'source_file',
        )
        for tid, txn_date, amount, account_id, description, source_file in rows:
            desc_key = _normalize_transaction_description(description)
            if len(desc_key) < min_len:
                continue
            key = (account_id, abs(amount), desc_key)
            buckets[key].append({
                'id': tid, 'date': txn_date, 'amount': amount,
                'is_pluggy': (source_file or '').startswith('pluggy:'),
            })

        phantom = []
        for group in buckets.values():
            if len(group) < 2:
                continue
            pluggy = sorted([r for r in group if r['is_pluggy']], key=lambda r: r['date'])
            legacy = sorted([r for r in group if not r['is_pluggy']], key=lambda r: r['date'])
            if not pluggy or not legacy:
                continue
            unmatched = list(legacy)
            for p in pluggy:
                for l in unmatched:
                    if abs((p['date'] - l['date']).days) <= 1:
                        phantom.append({
                            'date': p['date'],
                            'amount': abs(p['amount']),
                            'count': 1,
                            'value': float(abs(p['amount'])),
                        })
                        unmatched.remove(l)
                        break
        return phantom

    def handle(self, *args, **options):
        profile_arg = options.get('profile')
        min_len = options['min_len']
        max_rows = options['max_rows']
        max_value = options['max_value']

        profiles = list(self._profiles(profile_arg))
        if not profiles:
            self.stderr.write(self.style.ERROR('No matching profile'))
            return

        any_breach = False
        for profile in profiles:
            groups = self._phantom_groups(profile, min_len)
            total_rows = sum(g['count'] for g in groups)
            total_value = sum(g['value'] for g in groups)
            line = (
                f'profile={profile.name} phantom_groups={len(groups)} '
                f'phantom_rows={total_rows} phantom_value=R${total_value:.2f}'
            )
            breach = (max_rows and total_rows > max_rows) or (max_value and total_value > max_value)
            if breach:
                any_breach = True
                self.stderr.write(self.style.WARNING(line + ' [THRESHOLD EXCEEDED]'))
            elif total_rows > 0:
                self.stdout.write(self.style.WARNING(line))
            else:
                self.stdout.write(self.style.SUCCESS(line))

        if any_breach:
            raise SystemExit(1)
