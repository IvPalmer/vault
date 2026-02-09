"""
Import legacy data from FinanceDashboard's flat files into PostgreSQL.

Usage:
    python manage.py import_legacy_data

This command:
1. Imports DataLoader from FinanceDashboard (portable Python ETL)
2. Calls load_all() to get normalized, deduplicated DataFrame (~7,135 rows)
3. Creates Account, Category, CategorizationRule, RenameRule, Subcategory records
4. Creates Transaction records from DataFrame rows
5. Prints verification counts
"""
import sys
import os
import json
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction as db_transaction

from api.models import (
    Account, Category, Subcategory, CategorizationRule,
    RenameRule, Transaction, BalanceOverride,
    RecurringTemplate, RecurringMapping,
)


# Path to the legacy FinanceDashboard code
LEGACY_DIR = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'FinanceDashboard')
LEGACY_DIR = os.path.abspath(LEGACY_DIR)


class Command(BaseCommand):
    help = 'Import legacy FinanceDashboard data into PostgreSQL'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all existing data before import',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            RecurringMapping.objects.all().delete()
            RecurringTemplate.objects.all().delete()
            Transaction.objects.all().delete()
            CategorizationRule.objects.all().delete()
            RenameRule.objects.all().delete()
            Subcategory.objects.all().delete()
            Category.objects.all().delete()
            Account.objects.all().delete()
            BalanceOverride.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('All data cleared.'))

        self._import_accounts()
        self._import_categories()
        self._import_recurring_templates()
        self._import_rules()
        self._import_rename_rules()
        self._import_subcategory_rules()
        self._import_transactions()
        self._import_balance_overrides()
        self._restore_from_backup()
        self._print_verification()

    def _import_accounts(self):
        self.stdout.write('\n=== Importing Accounts ===')
        accounts = [
            {'name': 'Checking', 'account_type': 'checking'},
            {'name': 'Mastercard Black', 'account_type': 'credit_card', 'closing_day': 30, 'due_day': 5},
            {'name': 'Visa Infinite', 'account_type': 'credit_card', 'closing_day': 30, 'due_day': 5},
            {'name': 'Mastercard - Rafa', 'account_type': 'credit_card', 'closing_day': 30, 'due_day': 5},
            {'name': 'Manual', 'account_type': 'manual'},
        ]
        for acct in accounts:
            obj, created = Account.objects.get_or_create(
                name=acct['name'],
                defaults=acct,
            )
            status = 'created' if created else 'exists'
            self.stdout.write(f'  {obj.name}: {status}')

    def _import_categories(self):
        self.stdout.write('\n=== Importing Categories (budget.json) ===')
        budget_path = os.path.join(LEGACY_DIR, 'budget.json')
        with open(budget_path) as f:
            budget = json.load(f)

        # Normalize type names: "Variável" -> "Variavel" for DB storage
        type_map = {
            'Fixo': 'Fixo',
            'Variável': 'Variavel',
            'Variavel': 'Variavel',
            'Variable': 'Variavel',
            'Income': 'Income',
            'Investimento': 'Investimento',
        }

        # ALL budget items go to Category (transaction taxonomy).
        # Template types ALSO go to RecurringTemplate (budget tracking).
        # These serve different purposes: Category = classify transactions,
        # RecurringTemplate = track monthly recurring budget items.
        order = 0
        for name, config in budget.items():
            cat_type = type_map.get(config['type'], 'Variavel')
            obj, created = Category.objects.get_or_create(
                name=name,
                defaults={
                    'category_type': cat_type,
                    'default_limit': Decimal(str(config.get('limit', 0))),
                    'due_day': config.get('day'),
                    'display_order': order,
                },
            )
            status = 'created' if created else 'exists'
            self.stdout.write(f'  {obj.name} ({cat_type}): {status}')
            order += 1

    def _import_recurring_templates(self):
        self.stdout.write('\n=== Importing Recurring Templates (budget.json) ===')
        budget_path = os.path.join(LEGACY_DIR, 'budget.json')
        with open(budget_path) as f:
            budget = json.load(f)

        # Normalize type names
        type_map = {
            'Fixo': 'Fixo',
            'Income': 'Income',
            'Investimento': 'Investimento',
        }

        template_types = {'Fixo', 'Income', 'Investimento'}
        order = 0
        imported = 0

        for name, config in budget.items():
            raw_type = config['type']
            # Normalize: "Variável" -> skip
            if raw_type in ('Variável', 'Variavel', 'Variable'):
                order += 1
                continue

            tpl_type = type_map.get(raw_type)
            if not tpl_type or tpl_type not in template_types:
                order += 1
                continue

            obj, created = RecurringTemplate.objects.get_or_create(
                name=name,
                defaults={
                    'template_type': tpl_type,
                    'default_limit': Decimal(str(config.get('limit', 0))),
                    'due_day': config.get('day'),
                    'is_active': True,
                    'display_order': order,
                },
            )
            status = 'created' if created else 'exists'
            self.stdout.write(f'  {obj.name} ({tpl_type}): {status}')
            if created:
                imported += 1
            order += 1

        self.stdout.write(f'  Imported {imported} recurring templates')

    def _import_rules(self):
        self.stdout.write('\n=== Importing Categorization Rules (rules.json) ===')
        rules_path = os.path.join(LEGACY_DIR, 'rules.json')
        with open(rules_path) as f:
            rules = json.load(f)

        imported = 0
        for keyword, category_name in rules.items():
            category = Category.objects.filter(name=category_name).first()
            if not category:
                # Try case-insensitive match
                category = Category.objects.filter(name__iexact=category_name).first()
            if not category:
                self.stdout.write(
                    self.style.WARNING(f'  SKIP: No category "{category_name}" for keyword "{keyword}"')
                )
                continue

            _, created = CategorizationRule.objects.get_or_create(
                keyword=keyword,
                defaults={'category': category},
            )
            if created:
                imported += 1

        self.stdout.write(f'  Imported {imported} rules')

    def _import_rename_rules(self):
        self.stdout.write('\n=== Importing Rename Rules (renames.json) ===')
        renames_path = os.path.join(LEGACY_DIR, 'renames.json')
        if not os.path.exists(renames_path):
            self.stdout.write('  renames.json not found, skipping')
            return

        with open(renames_path) as f:
            renames = json.load(f)

        imported = 0
        for keyword, display_name in renames.items():
            _, created = RenameRule.objects.get_or_create(
                keyword=keyword,
                defaults={'display_name': display_name},
            )
            if created:
                imported += 1

        self.stdout.write(f'  Imported {imported} rename rules')

    def _import_subcategory_rules(self):
        self.stdout.write('\n=== Importing Subcategory Rules (subcategory_rules.json) ===')
        sub_path = os.path.join(LEGACY_DIR, 'subcategory_rules.json')
        if not os.path.exists(sub_path):
            self.stdout.write('  subcategory_rules.json not found, skipping')
            return

        with open(sub_path) as f:
            sub_rules = json.load(f)

        imported = 0
        for parent_cat_name, keywords in sub_rules.items():
            # Find or fuzzy-match the parent category
            parent = Category.objects.filter(name=parent_cat_name).first()
            if not parent:
                parent = Category.objects.filter(name__iexact=parent_cat_name).first()
            if not parent:
                self.stdout.write(
                    self.style.WARNING(f'  SKIP: No parent category "{parent_cat_name}"')
                )
                continue

            # Collect unique subcategory names
            subcategory_names = set(keywords.values())
            for sub_name in subcategory_names:
                Subcategory.objects.get_or_create(
                    name=sub_name,
                    category=parent,
                )
                imported += 1

        self.stdout.write(f'  Imported {imported} subcategories')

    def _import_transactions(self):
        self.stdout.write('\n=== Importing Transactions (via DataLoader) ===')

        # Import DataLoader from legacy codebase
        sys.path.insert(0, LEGACY_DIR)
        try:
            from DataLoader import DataLoader
        except ImportError as e:
            self.stdout.write(self.style.ERROR(f'  Failed to import DataLoader: {e}'))
            return

        dl = DataLoader()
        dl.load_all()
        df = dl.transactions

        if df.empty:
            self.stdout.write(self.style.WARNING('  No transactions loaded from DataLoader'))
            return

        self.stdout.write(f'  DataLoader returned {len(df)} transactions')

        # Build lookup maps
        account_map = {a.name: a for a in Account.objects.all()}
        category_map = {c.name: c for c in Category.objects.all()}

        # Batch create
        batch = []
        skipped = 0

        for _, row in df.iterrows():
            account = account_map.get(row['account'])
            if not account:
                skipped += 1
                continue

            category = category_map.get(row.get('category', ''))

            # Handle NaN/NaT values
            import pandas as pd

            invoice_month = row.get('invoice_month', '')
            if pd.isna(invoice_month):
                invoice_month = ''

            invoice_close = row.get('invoice_close_date')
            if pd.isna(invoice_close):
                invoice_close = None
            else:
                invoice_close = invoice_close.date() if hasattr(invoice_close, 'date') else None

            invoice_pay = row.get('invoice_payment_date')
            if pd.isna(invoice_pay):
                invoice_pay = None
            else:
                invoice_pay = invoice_pay.date() if hasattr(invoice_pay, 'date') else None

            raw_desc = row.get('raw_description', '')
            if pd.isna(raw_desc):
                raw_desc = ''

            desc_orig = row.get('description_original', '')
            if pd.isna(desc_orig):
                desc_orig = ''

            installment_info = row.get('installment_info', '')
            if pd.isna(installment_info) or installment_info is None:
                installment_info = ''

            source_file = row.get('source', '')
            if pd.isna(source_file):
                source_file = ''

            month_str = row.get('month_str', '')
            if pd.isna(month_str):
                month_str = row['date'].strftime('%Y-%m') if not pd.isna(row['date']) else ''

            txn = Transaction(
                date=row['date'].date() if hasattr(row['date'], 'date') else row['date'],
                description=str(row['description']),
                description_original=str(desc_orig),
                raw_description=str(raw_desc),
                amount=Decimal(str(row['amount'])),
                account=account,
                category=category,
                source_file=str(source_file),
                is_installment=bool(row.get('is_installment', False)),
                installment_info=str(installment_info),
                is_recurring=bool(row.get('is_recurring', False)),
                is_internal_transfer=bool(row.get('is_internal_transfer', False)),
                invoice_month=str(invoice_month),
                invoice_close_date=invoice_close,
                invoice_payment_date=invoice_pay,
                month_str=str(month_str),
            )
            batch.append(txn)

        self.stdout.write(f'  Creating {len(batch)} transactions (skipped {skipped})...')

        # Use bulk_create in chunks
        CHUNK_SIZE = 500
        created_count = 0
        for i in range(0, len(batch), CHUNK_SIZE):
            chunk = batch[i:i + CHUNK_SIZE]
            Transaction.objects.bulk_create(chunk, ignore_conflicts=False)
            created_count += len(chunk)
            self.stdout.write(f'    Batch {i // CHUNK_SIZE + 1}: {len(chunk)} created')

        self.stdout.write(self.style.SUCCESS(f'  Total created: {created_count}'))

    def _import_balance_overrides(self):
        self.stdout.write('\n=== Importing Balance Overrides ===')
        override_path = os.path.join(LEGACY_DIR, '..', 'balance_overrides.json')
        if not os.path.exists(override_path):
            # Also check in FinanceDashboard dir
            override_path = os.path.join(LEGACY_DIR, 'balance_overrides.json')
        if not os.path.exists(override_path):
            self.stdout.write('  No balance_overrides.json found, skipping')
            return

        with open(override_path) as f:
            overrides = json.load(f)

        imported = 0
        for month_str, balance in overrides.items():
            _, created = BalanceOverride.objects.get_or_create(
                month_str=month_str,
                defaults={'balance': Decimal(str(balance))},
            )
            if created:
                imported += 1

        self.stdout.write(f'  Imported {imported} balance overrides')

    def _restore_from_backup(self):
        """Restore RecurringMapping and BudgetConfig from backup if it exists."""
        self.stdout.write('\n=== Restoring from backup (custom items + mappings) ===')
        backup_dir = os.path.join('/app', 'backups')
        if not os.path.exists('/app'):
            backup_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backups')
        backup_path = os.path.abspath(os.path.join(backup_dir, 'vault_backup.json'))

        if not os.path.exists(backup_path):
            self.stdout.write('  No backup file found, skipping')
            return

        from django.core.management import call_command
        call_command('db_restore', input=backup_path)

    def _print_verification(self):
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('VERIFICATION SUMMARY')
        self.stdout.write('=' * 60)

        self.stdout.write(f'  Accounts:            {Account.objects.count()}')
        self.stdout.write(f'  Categories:          {Category.objects.count()}')
        self.stdout.write(f'  Recurring Templates: {RecurringTemplate.objects.count()}')
        self.stdout.write(f'  Recurring Mappings:  {RecurringMapping.objects.count()}')
        self.stdout.write(f'  Subcategories:       {Subcategory.objects.count()}')
        self.stdout.write(f'  Categorization Rules:{CategorizationRule.objects.count()}')
        self.stdout.write(f'  Rename Rules:        {RenameRule.objects.count()}')
        self.stdout.write(f'  Transactions:        {Transaction.objects.count()}')
        self.stdout.write(f'  Balance Overrides:   {BalanceOverride.objects.count()}')

        self.stdout.write('\n  Transactions per Account:')
        for acct in Account.objects.all():
            count = Transaction.objects.filter(account=acct).count()
            if count > 0:
                self.stdout.write(f'    {acct.name}: {count}')

        # Month range
        from django.db.models import Min, Max
        agg = Transaction.objects.aggregate(
            earliest=Min('date'),
            latest=Max('date'),
        )
        if agg['earliest']:
            self.stdout.write(f'\n  Date range: {agg["earliest"]} to {agg["latest"]}')

        # Month count
        month_count = Transaction.objects.values('month_str').distinct().count()
        self.stdout.write(f'  Unique months: {month_count}')

        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('Import complete!'))
