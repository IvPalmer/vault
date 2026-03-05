"""
Backfill pluggy_category and pluggy_category_id on existing Pluggy-synced transactions.
Also applies Pluggy category mapping to uncategorized transactions.

Usage:
    python manage.py backfill_pluggy_categories --profile Palmer
    python manage.py backfill_pluggy_categories --profile Palmer --dry-run
    python manage.py backfill_pluggy_categories --profile Palmer --recategorize
"""
import os
import logging
from collections import Counter

from django.core.management.base import BaseCommand

from api.models import (
    Account, Category, PluggyCategoryMapping, Profile, Transaction,
)
from api.pluggy import PluggyClient

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Backfill Pluggy category data on existing transactions'

    def add_arguments(self, parser):
        parser.add_argument('--profile', required=True)
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--recategorize', action='store_true',
                            help='Re-categorize ALL non-manually-categorized transactions using Pluggy mappings')

    def handle(self, *args, **options):
        client_id = os.environ.get('PLUGGY_CLIENT_ID', '')
        client_secret = os.environ.get('PLUGGY_CLIENT_SECRET', '')
        item_id = os.environ.get('PLUGGY_ITEM_ID', '')

        if not all([client_id, client_secret, item_id]):
            self.stderr.write(self.style.ERROR('Missing Pluggy credentials'))
            return

        try:
            profile = Profile.objects.get(name=options['profile'])
        except Profile.DoesNotExist:
            self.stderr.write(self.style.ERROR(f'Profile not found'))
            return

        dry_run = options['dry_run']
        recategorize = options['recategorize']

        # Load Pluggy category mappings
        pluggy_mappings = {}
        for pm in PluggyCategoryMapping.objects.filter(profile=profile).select_related('category', 'subcategory'):
            pluggy_mappings[pm.pluggy_category_id] = (pm.category, pm.subcategory)

        def resolve_pluggy_cat(cat_id):
            if not cat_id:
                return None, None
            result = pluggy_mappings.get(cat_id)
            if result:
                return result
            parent_id = cat_id[:2] + '000000'
            return pluggy_mappings.get(parent_id, (None, None))

        client = PluggyClient(client_id, client_secret)

        # Get all accounts with external_id (Pluggy accounts)
        accounts = Account.objects.filter(profile=profile).exclude(external_id='')
        self.stdout.write(f'Found {accounts.count()} Pluggy-linked accounts')

        # Fetch transactions from Pluggy API and build ext_id -> category map
        ext_id_to_cat = {}
        for acct in accounts:
            self.stdout.write(f'\nFetching Pluggy data for {acct.name}...')
            txns = client.get_transactions(acct.external_id, '2025-01-01', '2026-12-31', page_size=500)
            for t in txns:
                cat = t.get('category') or ''
                cat_id = t.get('categoryId') or ''
                if cat:
                    ext_id_to_cat[t['id']] = (cat, cat_id)
            self.stdout.write(f'  {len(txns)} transactions, {sum(1 for t in txns if t.get("category"))} with category')

        # Update existing Vault transactions
        vault_txns = Transaction.objects.filter(
            profile=profile
        ).exclude(external_id='').select_related('category', 'subcategory')

        updated_cat_field = 0
        updated_vault_cat = 0
        stats = Counter()

        for txn in vault_txns.iterator():
            pluggy_data = ext_id_to_cat.get(txn.external_id)
            if not pluggy_data:
                continue

            p_cat, p_cat_id = pluggy_data
            changed_fields = []

            # Always backfill pluggy_category fields
            if not txn.pluggy_category and p_cat:
                txn.pluggy_category = p_cat
                txn.pluggy_category_id = p_cat_id
                changed_fields += ['pluggy_category', 'pluggy_category_id']
                updated_cat_field += 1

            # Apply Vault category from Pluggy mapping
            should_categorize = (
                (not txn.category and not txn.is_manually_categorized) or
                (recategorize and not txn.is_manually_categorized)
            )
            if should_categorize and p_cat_id:
                vault_cat, vault_sub = resolve_pluggy_cat(p_cat_id)
                if vault_cat:
                    txn.category = vault_cat
                    txn.subcategory = vault_sub
                    if 'category' not in changed_fields:
                        changed_fields += ['category', 'subcategory']
                    updated_vault_cat += 1
                    stats[vault_cat.name] += 1

            if changed_fields and not dry_run:
                txn.save(update_fields=changed_fields)

        action = 'Would update' if dry_run else 'Updated'
        self.stdout.write(self.style.SUCCESS(
            f'\n{action}: {updated_cat_field} pluggy_category fields, '
            f'{updated_vault_cat} vault categories'))

        if stats:
            self.stdout.write('\nCategory distribution:')
            for cat, count in stats.most_common():
                self.stdout.write(f'  {count:4d}  {cat}')
