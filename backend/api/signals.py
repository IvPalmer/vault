"""
Auto-backup RecurringTemplate and RecurringMapping data to JSON
whenever records are created, updated, or deleted.

The backup file at backend/backups/vault_backup.json is part of the repo
and survives Docker volume rebuilds.
"""
import json
import os
import threading
from datetime import datetime
from decimal import Decimal

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

# Debounce: avoid writing to disk on every single save during bulk operations
_backup_timer = None
_DEBOUNCE_SECONDS = 2


class _DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)


def _get_backup_path():
    backup_dir = os.path.join('/app', 'backups')
    if not os.path.exists('/app'):
        backup_dir = os.path.join(os.path.dirname(__file__), '..', 'backups')
    backup_dir = os.path.abspath(backup_dir)
    os.makedirs(backup_dir, exist_ok=True)
    return os.path.join(backup_dir, 'vault_backup.json')


def _do_backup():
    """Perform the actual backup write."""
    from api.models import RecurringTemplate, RecurringMapping, BudgetConfig

    data = {
        'exported_at': datetime.now().isoformat(),
        'auto_backup': True,
        'recurring_templates': [],
        'recurring_mappings': [],
        'budget_configs': [],
    }

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

    path = _get_backup_path()
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, cls=_DecimalEncoder)


def _schedule_backup():
    """Debounced backup: waits 2s after last change before writing."""
    global _backup_timer
    if _backup_timer is not None:
        _backup_timer.cancel()
    _backup_timer = threading.Timer(_DEBOUNCE_SECONDS, _do_backup)
    _backup_timer.daemon = True
    _backup_timer.start()


def _on_recurring_change(sender, **kwargs):
    """Signal handler for RecurringTemplate/RecurringMapping/BudgetConfig changes."""
    _schedule_backup()


def connect_signals():
    """Connect post_save and post_delete signals. Called from AppConfig.ready()."""
    from api.models import RecurringTemplate, RecurringMapping, BudgetConfig

    for model in (RecurringTemplate, RecurringMapping, BudgetConfig):
        post_save.connect(_on_recurring_change, sender=model)
        post_delete.connect(_on_recurring_change, sender=model)
