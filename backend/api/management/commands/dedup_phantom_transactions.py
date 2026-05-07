import uuid
from collections import defaultdict

from django.core.management.base import BaseCommand
from django.db import transaction as db_transaction

from api.models import Profile, RecurringMapping, Transaction
from api.services import _normalize_transaction_description as normalize_description


def dedupe_description_key(description):
    """Use the same normalization as services._normalize_transaction_description.

    Pluggy noise prefixes (PIX TRANSF, PAG BOLETO, etc.) are stripped so
    legacy CSV format and Pluggy verbose format collapse to the same key.
    """
    return normalize_description(description)


def keep_score(txn):
    linked_count = txn.recurring_mapping_links.count() + txn.cross_month_links.count()
    if txn.recurring_mappings.exists():
        linked_count += 1
    return (
        linked_count,
        1 if txn.is_manually_categorized else 0,
        1 if (txn.source_file or '').startswith('pluggy:') else 0,
        1 if txn.external_id else 0,
        1 if txn.pluggy_category_id else 0,
        txn.created_at,
    )


class Command(BaseCommand):
    help = 'Find and optionally delete known phantom duplicate transactions.'

    def add_arguments(self, parser):
        parser.add_argument('--profile', help='Profile name or UUID. Defaults to all profiles.')
        parser.add_argument('--apply', action='store_true', help='Delete duplicate rows. Omit for dry-run.')
        parser.add_argument('--dry-run', action='store_true', help='Preview duplicates without deleting rows.')
        parser.add_argument('--database', default='default', help='Database alias to use.')

    def _profiles(self, profile_arg):
        qs = Profile.objects.using(self.db_alias).all()
        if not profile_arg:
            return qs
        by_name = qs.filter(name__iexact=profile_arg)
        if by_name.exists():
            return by_name
        try:
            return qs.filter(id=uuid.UUID(profile_arg))
        except ValueError:
            return qs.none()

    def _find_groups(self, profile):
        buckets = defaultdict(list)
        txns = Transaction.objects.using(self.db_alias).filter(profile=profile).select_related('account').order_by(
            'account_id', 'amount', 'date', 'created_at'
        )
        for txn in txns:
            desc_key = dedupe_description_key(txn.description)
            # Skip rows with empty or extremely short normalized descriptions
            # (would over-match generic txns like "Compra"/"Saque" without identifier)
            if len(desc_key) < 3:
                continue
            key = (txn.account_id, abs(txn.amount), desc_key)
            buckets[key].append(txn)

        groups = []
        for rows in buckets.values():
            rows = sorted(rows, key=lambda t: (t.date, t.created_at))
            current = []
            for txn in rows:
                if not current or abs((txn.date - current[-1].date).days) <= 1:
                    current.append(txn)
                else:
                    if len(current) > 1:
                        groups.append(current)
                    current = [txn]
            if len(current) > 1:
                groups.append(current)
        return groups

    def _transfer_links(self, delete_txn, keep_txn):
        RecurringMapping.objects.using(self.db_alias).filter(transaction=delete_txn).update(transaction=keep_txn)
        for mapping in delete_txn.recurring_mapping_links.all():
            mapping.transactions.add(keep_txn)
        for mapping in delete_txn.cross_month_links.all():
            mapping.cross_month_transactions.add(keep_txn)

    def handle(self, *args, **options):
        apply = options['apply']
        self.db_alias = options['database']
        profiles = list(self._profiles(options.get('profile')))
        if not profiles:
            self.stderr.write(self.style.ERROR('No matching profile found'))
            return

        grand_total = 0
        for profile in profiles:
            groups = self._find_groups(profile)
            delete_ids = []
            self.stdout.write(f'\nProfile: {profile.name}')
            for group in groups:
                keep = sorted(group, key=keep_score, reverse=True)[0]
                duplicates = [txn for txn in group if txn.id != keep.id]
                delete_ids.extend(txn.id for txn in duplicates)
                total_amount = sum(abs(txn.amount) for txn in duplicates)
                self.stdout.write(
                    f'  {keep.date} {keep.account.name} {keep.description[:60]} '
                    f'R${abs(keep.amount)}: keep {keep.id}, delete {len(duplicates)} '
                    f'(phantom R${total_amount})'
                )
            self.stdout.write(f'  Total duplicate rows: {len(delete_ids)}')
            grand_total += len(delete_ids)

            if apply and delete_ids:
                with db_transaction.atomic(using=self.db_alias):
                    for group in groups:
                        keep = sorted(group, key=keep_score, reverse=True)[0]
                        for duplicate in [txn for txn in group if txn.id != keep.id]:
                            self._transfer_links(duplicate, keep)
                            duplicate.delete()
                self.stdout.write(self.style.SUCCESS(f'  Deleted {len(delete_ids)} rows'))

        if not apply:
            self.stdout.write(self.style.WARNING(
                f'\nDry-run only. Re-run with --apply to delete {grand_total} duplicate rows.'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(f'\nDeleted {grand_total} duplicate rows total.'))
