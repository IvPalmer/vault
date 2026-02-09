"""
Backup user-created data (RecurringTemplate, RecurringMapping, BudgetConfig)
to a JSON file so it survives Docker volume rebuilds.

Usage:
    python manage.py db_backup                     # default: backups/vault_backup.json
    python manage.py db_backup --output my.json    # custom path
"""
import json
import os
from datetime import datetime
from decimal import Decimal

from django.core.management.base import BaseCommand

from api.models import (
    RecurringTemplate, RecurringMapping, BudgetConfig,
)


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)


class Command(BaseCommand):
    help = 'Backup RecurringTemplate, RecurringMapping, and BudgetConfig to JSON'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output', '-o',
            default=None,
            help='Output file path (default: backups/vault_backup.json)',
        )

    def handle(self, *args, **options):
        output = options['output']
        if not output:
            # /app in Docker maps to ./backend on host
            backup_dir = os.path.join('/app', 'backups')
            if not os.path.exists('/app'):
                # Running outside Docker
                backup_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backups')
            backup_dir = os.path.abspath(backup_dir)
            os.makedirs(backup_dir, exist_ok=True)
            output = os.path.join(backup_dir, 'vault_backup.json')

        data = {
            'exported_at': datetime.now().isoformat(),
            'recurring_templates': [],
            'recurring_mappings': [],
            'budget_configs': [],
        }

        # --- RecurringTemplate ---
        for t in RecurringTemplate.objects.all().order_by('display_order'):
            data['recurring_templates'].append({
                'id': str(t.id),
                'name': t.name,
                'template_type': t.template_type,
                'default_limit': str(t.default_limit),
                'due_day': t.due_day,
                'is_active': t.is_active,
                'display_order': t.display_order,
            })

        # --- RecurringMapping ---
        for m in RecurringMapping.objects.select_related('template', 'category').all():
            txn_ids = list(m.transactions.values_list('id', flat=True))
            cross_ids = list(m.cross_month_transactions.values_list('id', flat=True))
            data['recurring_mappings'].append({
                'id': str(m.id),
                'template_id': str(m.template_id) if m.template_id else None,
                'template_name': m.template.name if m.template else None,
                'category_id': str(m.category_id) if m.category_id else None,
                'category_name': m.category.name if m.category else None,
                'transaction_id': str(m.transaction_id) if m.transaction_id else None,
                'transaction_ids': [str(tid) for tid in txn_ids],
                'cross_month_transaction_ids': [str(tid) for tid in cross_ids],
                'match_mode': m.match_mode,
                'month_str': m.month_str,
                'status': m.status,
                'expected_amount': str(m.expected_amount),
                'actual_amount': str(m.actual_amount) if m.actual_amount is not None else None,
                'notes': m.notes,
                'is_custom': m.is_custom,
                'custom_name': m.custom_name,
                'custom_type': m.custom_type,
                'display_order': m.display_order,
            })

        # --- BudgetConfig ---
        for b in BudgetConfig.objects.select_related('category', 'template').all():
            data['budget_configs'].append({
                'id': str(b.id),
                'category_id': str(b.category_id) if b.category_id else None,
                'category_name': b.category.name if b.category else None,
                'template_id': str(b.template_id) if b.template_id else None,
                'template_name': b.template.name if b.template else None,
                'month_str': b.month_str,
                'limit_override': str(b.limit_override),
            })

        with open(output, 'w') as f:
            json.dump(data, f, indent=2, cls=DecimalEncoder)

        tpl_count = len(data['recurring_templates'])
        map_count = len(data['recurring_mappings'])
        cfg_count = len(data['budget_configs'])
        self.stdout.write(self.style.SUCCESS(
            f'Backup saved to {output}\n'
            f'  Templates: {tpl_count}\n'
            f'  Mappings:  {map_count}\n'
            f'  Configs:   {cfg_count}'
        ))
