"""
Restore user-created data (RecurringTemplate, RecurringMapping, BudgetConfig)
from a JSON backup file.

Usage:
    python manage.py db_restore                      # default: backups/vault_backup.json
    python manage.py db_restore --input my.json      # custom path
    python manage.py db_restore --clear              # clear existing before restore
"""
import json
import os
from decimal import Decimal

from django.core.management.base import BaseCommand

from api.models import (
    RecurringTemplate, RecurringMapping, BudgetConfig,
    Category, Transaction,
)


class Command(BaseCommand):
    help = 'Restore RecurringTemplate, RecurringMapping, and BudgetConfig from JSON backup'

    def add_arguments(self, parser):
        parser.add_argument(
            '--input', '-i',
            default=None,
            help='Input file path (default: backups/vault_backup.json)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing RecurringMapping and BudgetConfig before restore',
        )

    def handle(self, *args, **options):
        input_path = options['input']
        if not input_path:
            # /app in Docker maps to ./backend on host
            backup_dir = os.path.join('/app', 'backups')
            if not os.path.exists('/app'):
                # Running outside Docker
                backup_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backups')
            backup_dir = os.path.abspath(backup_dir)
            input_path = os.path.join(backup_dir, 'vault_backup.json')

        if not os.path.exists(input_path):
            self.stdout.write(self.style.ERROR(f'Backup file not found: {input_path}'))
            return

        with open(input_path) as f:
            data = json.load(f)

        self.stdout.write(f'Restoring from: {input_path}')
        self.stdout.write(f'Exported at: {data.get("exported_at", "unknown")}')

        if options['clear']:
            self.stdout.write('Clearing existing mappings and configs...')
            RecurringMapping.objects.all().delete()
            BudgetConfig.objects.all().delete()

        # --- Restore RecurringTemplate ---
        tpl_created = 0
        tpl_existed = 0
        # Build name→id map for FK resolution in mappings
        tpl_name_to_obj = {}
        for t in data.get('recurring_templates', []):
            obj, created = RecurringTemplate.objects.get_or_create(
                name=t['name'],
                defaults={
                    'template_type': t['template_type'],
                    'default_limit': Decimal(t['default_limit']),
                    'due_day': t.get('due_day'),
                    'is_active': t.get('is_active', True),
                    'display_order': t.get('display_order', 0),
                },
            )
            tpl_name_to_obj[t['name']] = obj
            if created:
                tpl_created += 1
            else:
                tpl_existed += 1
        self.stdout.write(f'  Templates: {tpl_created} created, {tpl_existed} existed')

        # Build lookup maps for FK resolution
        cat_name_map = {c.name: c for c in Category.objects.all()}

        # --- Restore RecurringMapping ---
        map_created = 0
        map_skipped = 0
        for m in data.get('recurring_mappings', []):
            # Resolve template FK by name (UUIDs change across DB rebuilds)
            template = None
            if m.get('template_name'):
                template = tpl_name_to_obj.get(m['template_name'])
            if not template and not m.get('is_custom'):
                self.stdout.write(self.style.WARNING(
                    f'  SKIP mapping: template "{m.get("template_name")}" not found'
                ))
                map_skipped += 1
                continue

            # Resolve category FK by name
            category = None
            if m.get('category_name'):
                category = cat_name_map.get(m['category_name'])

            # Check for existing (template + month_str uniqueness)
            if template:
                exists = RecurringMapping.objects.filter(
                    template=template, month_str=m['month_str']
                ).exists()
                if exists:
                    map_skipped += 1
                    continue

            mapping = RecurringMapping.objects.create(
                template=template,
                category=category,
                match_mode=m.get('match_mode', 'manual'),
                month_str=m['month_str'],
                status=m.get('status', 'missing'),
                expected_amount=Decimal(m.get('expected_amount', '0')),
                actual_amount=Decimal(m['actual_amount']) if m.get('actual_amount') else None,
                notes=m.get('notes', ''),
                is_custom=m.get('is_custom', False),
                custom_name=m.get('custom_name', ''),
                custom_type=m.get('custom_type', ''),
                display_order=m.get('display_order', 0),
            )

            # Re-link transactions by UUID if they still exist
            if m.get('transaction_ids'):
                existing_txns = Transaction.objects.filter(
                    id__in=m['transaction_ids']
                ).values_list('id', flat=True)
                if existing_txns:
                    mapping.transactions.set(existing_txns)

            if m.get('cross_month_transaction_ids'):
                existing_cross = Transaction.objects.filter(
                    id__in=m['cross_month_transaction_ids']
                ).values_list('id', flat=True)
                if existing_cross:
                    mapping.cross_month_transactions.set(existing_cross)

            map_created += 1

        self.stdout.write(f'  Mappings: {map_created} created, {map_skipped} skipped')

        # --- Restore BudgetConfig ---
        cfg_created = 0
        cfg_skipped = 0
        for b in data.get('budget_configs', []):
            template = None
            if b.get('template_name'):
                template = tpl_name_to_obj.get(b['template_name'])

            category = None
            if b.get('category_name'):
                category = cat_name_map.get(b['category_name'])

            if not template and not category:
                cfg_skipped += 1
                continue

            _, created = BudgetConfig.objects.get_or_create(
                template=template,
                category=category,
                month_str=b['month_str'],
                defaults={
                    'limit_override': Decimal(b['limit_override']),
                },
            )
            if created:
                cfg_created += 1
            else:
                cfg_skipped += 1

        self.stdout.write(f'  Configs: {cfg_created} created, {cfg_skipped} skipped')
        self.stdout.write(self.style.SUCCESS('Restore complete!'))
