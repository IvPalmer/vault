"""
Analytics services — business logic for summary, control metrics,
recurring budget tracking, and transaction management.
"""
import re
from collections import Counter
from datetime import datetime, timedelta
from decimal import Decimal
from difflib import get_close_matches, SequenceMatcher
from django.db.models import Sum, Q, F, Case, When, Value, CharField, Count, Max
from dateutil.relativedelta import relativedelta
from .models import (
    Transaction, Category, Account, BalanceOverride,
    RecurringMapping, RecurringTemplate, BudgetConfig, CategorizationRule,
    MetricasOrderConfig, CustomMetric,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_expected_amount(template, month_str, profile=None):
    """
    Return the expected amount for a recurring template in a month.
    Uses BudgetConfig override if it exists, otherwise template.default_limit.
    """
    try:
        bc = BudgetConfig.objects.get(template=template, month_str=month_str, profile=profile)
        return bc.limit_override
    except BudgetConfig.DoesNotExist:
        return template.default_limit


# ---------------------------------------------------------------------------
# A2-1: initialize_month
# ---------------------------------------------------------------------------

def initialize_month(month_str, profile=None):
    """
    Create RecurringMapping rows for a month from RecurringTemplate.
    Idempotent — skips templates that already have a mapping for the month.
    Returns dict with created count and total count.
    """
    templates = RecurringTemplate.objects.filter(
        is_active=True,
        default_limit__gt=0,
        profile=profile,
    )
    created = 0
    for tpl in templates:
        expected = _get_expected_amount(tpl, month_str, profile=profile)
        _, was_created = RecurringMapping.objects.get_or_create(
            template=tpl,
            month_str=month_str,
            profile=profile,
            defaults={
                'expected_amount': expected,
                'status': 'missing',
                'is_custom': False,
            },
        )
        if was_created:
            created += 1

    total = RecurringMapping.objects.filter(month_str=month_str, profile=profile).count()
    return {
        'month_str': month_str,
        'created': created,
        'total': total,
        'initialized': created > 0,
    }


# ---------------------------------------------------------------------------
# A2-2: get_recurring_data (REWRITE)
# ---------------------------------------------------------------------------

def get_recurring_data(month_str, profile=None):
    """
    RECORRENTES — recurring items sourced from RecurringMapping table.

    Auto-initializes the month from RecurringTemplate if no mappings exist.
    Each item carries a mapping_id for editing.
    Status is computed from the linked transaction or category-matched transactions.
    Suggestion logic is preserved for 'Faltando' items.

    Returns: dict with items grouped by type (fixo, income, investimento),
    plus 'all' list, and 'initialized' flag.
    """
    # Auto-initialize if no mappings exist for this month
    existing = RecurringMapping.objects.filter(month_str=month_str, profile=profile).count()
    was_initialized = False
    if existing == 0:
        result = initialize_month(month_str, profile=profile)
        was_initialized = result['initialized']

    # Fetch all mappings for this month
    mappings = RecurringMapping.objects.filter(
        month_str=month_str,
        profile=profile,
    ).select_related('template', 'category', 'transaction', 'transaction__account').prefetch_related(
        'transactions', 'transactions__account'
    ).order_by(
        'display_order', 'template__display_order', 'custom_name'
    )

    # Transaction pools for suggestion matching
    txns = Transaction.objects.filter(
        month_str=month_str,
        profile=profile,
    ).select_related('category', 'account')
    income_pool = txns.filter(amount__gt=0)
    expense_pool = txns.filter(amount__lt=0)

    all_expense_descs = list(expense_pool.values_list('description', flat=True).distinct())
    all_income_descs = list(income_pool.values_list('description', flat=True).distinct())

    def _get_type(mapping):
        """Get the template type for a mapping (handles custom items)."""
        if mapping.is_custom:
            return mapping.custom_type
        return mapping.template.template_type if mapping.template else ''

    def _get_name(mapping):
        """Get the display name for a mapping."""
        if mapping.is_custom:
            return mapping.custom_name
        return mapping.template.name if mapping.template else '?'

    def _compute_status_and_actual(mapping, cat_type):
        """
        Compute status and actual amount for a mapping based on match_mode:
        - 'category': sum all transactions in the category
        - 'manual': use M2M linked transactions (or legacy FK)
        """
        # If explicitly skipped, preserve that
        if mapping.status == 'skipped':
            return 'Pulado', float(mapping.actual_amount or 0)

        expected = float(mapping.expected_amount)

        if mapping.match_mode == 'category' and mapping.category:
            # Category match: sum all transactions in category
            if cat_type == 'Income':
                cat_txns = income_pool.filter(category=mapping.category)
            elif cat_type == 'Investimento':
                cat_txns = txns.filter(category=mapping.category)
            else:
                cat_txns = expense_pool.filter(category=mapping.category)

            actual_agg = cat_txns.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            actual = float(abs(actual_agg)) if cat_type != 'Income' else float(actual_agg)

            if actual == 0:
                return 'Faltando', 0
            elif expected == 0 or actual >= expected * 0.9:
                return 'Pago', actual
            else:
                return 'Parcial', actual

        # Manual mode: use M2M linked transactions
        linked = list(mapping.transactions.all())
        if linked:
            total = sum(float(abs(t.amount)) if cat_type != 'Income' else float(t.amount) for t in linked)
            if expected == 0 or total >= expected * 0.9:
                return 'Pago', total
            elif total > 0:
                return 'Parcial', total
            else:
                return 'Faltando', 0

        # Legacy fallback: single transaction FK
        if mapping.transaction:
            actual = float(abs(mapping.transaction.amount)) if cat_type != 'Income' else float(mapping.transaction.amount)
            if expected == 0 or actual >= expected * 0.9:
                return 'Pago', actual
            elif actual > 0:
                return 'Parcial', actual
            else:
                return 'Faltando', 0

        # No match found
        return 'Faltando', 0

    def _find_suggestion(mapping, cat_type, status, pool, all_descs):
        """Find a suggestion for 'Faltando' items."""
        if status != 'Faltando':
            return ''

        name = _get_name(mapping)
        expected = float(mapping.expected_amount)

        # Name similarity match
        if all_descs:
            close = get_close_matches(
                name.lower(),
                [d.lower() for d in all_descs],
                n=1, cutoff=0.5,
            )
            if close:
                for d in all_descs:
                    if d.lower() == close[0]:
                        match_txn = pool.filter(description=d).first()
                        if match_txn:
                            return f"{d} ({float(match_txn.amount):.2f})"
                        break

        # Amount match fallback
        if expected > 0 and cat_type != 'Income':
            tol = Decimal(str(expected * 0.05))
            limit_dec = Decimal(str(expected))
            exclude_q = Q(category=mapping.category) if mapping.category else Q()
            amt_match = pool.exclude(exclude_q).filter(
                amount__gte=-(limit_dec + tol),
                amount__lte=-(limit_dec - tol),
            ).first()
            if amt_match:
                return f"{amt_match.description} ({float(amt_match.amount):.2f})"

        return ''

    def _get_matched_info(mapping, cat_type):
        """Get matched transaction info based on match_mode.

        Returns match_type: 'direct' (single linked txn), 'multi' (multiple linked),
        'category' (category-matched), or None (no match).
        For multi/category, returns list of linked transaction IDs.
        """
        if mapping.match_mode == 'category' and mapping.category:
            # Category match mode
            if cat_type == 'Income':
                cat_txns = income_pool.filter(category=mapping.category)
            elif cat_type == 'Investimento':
                cat_txns = txns.filter(category=mapping.category)
            else:
                cat_txns = expense_pool.filter(category=mapping.category)

            count = cat_txns.count()
            if count > 0:
                primary = cat_txns.order_by(
                    '-amount' if cat_type == 'Income' else 'amount'
                ).first()
                desc = f"{count} transações via categoria" if count > 1 else primary.description
                return {
                    'matched_desc': desc,
                    'matched_source': primary.account.name if primary.account else '',
                    'matched_transaction_id': str(primary.id) if count == 1 else None,
                    'matched_transaction_ids': [str(t.id) for t in cat_txns[:20]],
                    'match_type': 'category',
                    'match_count': count,
                }

            return {
                'matched_desc': '',
                'matched_source': '',
                'matched_transaction_id': None,
                'matched_transaction_ids': [],
                'match_type': 'category',
                'match_count': 0,
            }

        # Manual mode: check M2M linked transactions
        linked = list(mapping.transactions.all())
        if linked:
            count = len(linked)
            primary = linked[0]
            if count == 1:
                return {
                    'matched_desc': primary.description,
                    'matched_source': primary.account.name if primary.account else '',
                    'matched_transaction_id': str(primary.id),
                    'matched_transaction_ids': [str(primary.id)],
                    'match_type': 'direct',
                    'match_count': 1,
                }
            else:
                return {
                    'matched_desc': f"{count} transações vinculadas",
                    'matched_source': '',
                    'matched_transaction_id': None,
                    'matched_transaction_ids': [str(t.id) for t in linked],
                    'match_type': 'multi',
                    'match_count': count,
                }

        # Legacy fallback: single transaction FK
        if mapping.transaction:
            txn = mapping.transaction
            return {
                'matched_desc': txn.description,
                'matched_source': txn.account.name if txn.account else '',
                'matched_transaction_id': str(txn.id),
                'matched_transaction_ids': [str(txn.id)],
                'match_type': 'direct',
                'match_count': 1,
            }

        return {
            'matched_desc': '',
            'matched_source': '',
            'matched_transaction_id': None,
            'matched_transaction_ids': [],
            'match_type': None,
            'match_count': 0,
        }

    # Build items from mappings
    fixo_items = []
    income_items = []
    investimento_items = []

    for mapping in mappings:
        cat_type = _get_type(mapping)
        name = _get_name(mapping)

        pool = expense_pool if cat_type in ('Fixo', 'Variavel') else (
            income_pool if cat_type == 'Income' else txns
        )
        all_descs = all_expense_descs if cat_type in ('Fixo', 'Variavel') else (
            all_income_descs if cat_type == 'Income' else all_expense_descs
        )

        status, actual = _compute_status_and_actual(mapping, cat_type)
        matched_info = _get_matched_info(mapping, cat_type)
        suggestion = _find_suggestion(mapping, cat_type, status, pool, all_descs)

        item = {
            'id': str(mapping.template.id) if mapping.template else None,
            'mapping_id': str(mapping.id),
            'name': name,
            'due_day': mapping.template.due_day if mapping.template else None,
            'expected': float(mapping.expected_amount),
            'actual': actual,
            'status': status,
            'matched_desc': matched_info['matched_desc'],
            'matched_source': matched_info['matched_source'],
            'matched_transaction_id': matched_info['matched_transaction_id'],
            'matched_transaction_ids': matched_info['matched_transaction_ids'],
            'match_type': matched_info['match_type'],
            'match_count': matched_info['match_count'],
            'match_mode': mapping.match_mode,
            'suggested': suggestion,
            'template_type': cat_type,
            'is_custom': mapping.is_custom,
            'is_skipped': mapping.status == 'skipped',
            'has_cross_month': mapping.cross_month_transactions.exists(),
            'cross_month_count': mapping.cross_month_transactions.count(),
        }

        if cat_type == 'Income':
            income_items.append(item)
        elif cat_type == 'Investimento':
            investimento_items.append(item)
        else:
            # Fixo + Variavel + any other type go into fixo list
            fixo_items.append(item)

    return {
        'month_str': month_str,
        'fixo': fixo_items,
        'income': income_items,
        'investimento': investimento_items,
        'all': income_items + fixo_items + investimento_items,
        'initialized': was_initialized,
    }


# ---------------------------------------------------------------------------
# A2-3: update_recurring_expected
# ---------------------------------------------------------------------------

def update_recurring_expected(mapping_id, expected_amount, profile=None):
    """
    Update the expected amount for a RecurringMapping.
    Returns the updated mapping summary.
    """
    mapping = RecurringMapping.objects.select_related('template').get(id=mapping_id, profile=profile)
    mapping.expected_amount = Decimal(str(expected_amount))
    mapping.save()

    name = mapping.custom_name if mapping.is_custom else (
        mapping.template.name if mapping.template else '?'
    )

    return {
        'mapping_id': str(mapping.id),
        'name': name,
        'expected_amount': float(mapping.expected_amount),
    }


# ---------------------------------------------------------------------------
# A2-3b: update_recurring_item (general field update)
# ---------------------------------------------------------------------------

def update_recurring_item(mapping_id, profile=None, **kwargs):
    """
    Update editable fields on a RecurringMapping: name, template_type,
    expected_amount, due_day.

    For template-based items, name/type changes convert them to custom items
    (is_custom=True) to preserve the override without affecting the template.
    """
    mapping = RecurringMapping.objects.select_related('template').get(id=mapping_id, profile=profile)

    if 'expected_amount' in kwargs and kwargs['expected_amount'] is not None:
        mapping.expected_amount = Decimal(str(kwargs['expected_amount']))

    if 'name' in kwargs and kwargs['name'] is not None:
        new_name = kwargs['name'].strip()
        if mapping.is_custom:
            mapping.custom_name = new_name
        else:
            # Convert to custom to preserve override
            mapping.is_custom = True
            mapping.custom_name = new_name
            mapping.custom_type = mapping.template.template_type if mapping.template else ''

    # Accept both template_type and category_type (backward compat)
    type_key = 'template_type' if 'template_type' in kwargs else ('category_type' if 'category_type' in kwargs else None)
    if type_key and kwargs[type_key] is not None:
        new_type = kwargs[type_key]
        if mapping.is_custom:
            mapping.custom_type = new_type
        else:
            # Convert to custom to preserve override
            mapping.is_custom = True
            mapping.custom_name = mapping.template.name if mapping.template else '?'
            mapping.custom_type = new_type

    if 'due_day' in kwargs:
        due_day = int(kwargs['due_day']) if kwargs['due_day'] else None
        if mapping.template and not mapping.is_custom:
            mapping.template.due_day = due_day
            mapping.template.save()

    mapping.save()

    name = mapping.custom_name if mapping.is_custom else (
        mapping.template.name if mapping.template else '?'
    )
    cat_type = mapping.custom_type if mapping.is_custom else (
        mapping.template.template_type if mapping.template else ''
    )
    due_day_val = mapping.template.due_day if mapping.template else None

    return {
        'mapping_id': str(mapping.id),
        'name': name,
        'template_type': cat_type,
        'expected_amount': float(mapping.expected_amount),
        'due_day': due_day_val,
        'is_custom': mapping.is_custom,
    }


# ---------------------------------------------------------------------------
# A2-4: add_custom_recurring
# ---------------------------------------------------------------------------

def add_custom_recurring(month_str, name, category_type, expected_amount, profile=None):
    """
    Add a custom one-off recurring item for a specific month.
    Custom items have is_custom=True and no template/category FK.
    """
    mapping = RecurringMapping.objects.create(
        month_str=month_str,
        is_custom=True,
        custom_name=name,
        custom_type=category_type,
        expected_amount=Decimal(str(expected_amount)),
        status='missing',
        template=None,
        category=None,
        profile=profile,
    )

    return {
        'mapping_id': str(mapping.id),
        'name': name,
        'template_type': category_type,
        'expected_amount': float(mapping.expected_amount),
        'month_str': month_str,
    }


# ---------------------------------------------------------------------------
# A2-5: delete_custom_recurring
# ---------------------------------------------------------------------------

def delete_custom_recurring(mapping_id, profile=None):
    """
    Delete a custom recurring item. Only works for is_custom=True items.
    Raises ValueError if trying to delete a non-custom item.
    """
    mapping = RecurringMapping.objects.get(id=mapping_id, profile=profile)
    if not mapping.is_custom:
        raise ValueError('Cannot delete non-custom recurring items. Use skip instead.')

    name = mapping.custom_name
    mapping.delete()

    return {
        'mapping_id': str(mapping_id),
        'deleted': True,
        'name': name,
    }


# ---------------------------------------------------------------------------
# A2-6: skip / unskip recurring
# ---------------------------------------------------------------------------

def skip_recurring(mapping_id, profile=None):
    """Mark a recurring item as skipped for this month."""
    mapping = RecurringMapping.objects.select_related('template').get(id=mapping_id, profile=profile)
    mapping.status = 'skipped'
    mapping.save()

    name = mapping.custom_name if mapping.is_custom else (
        mapping.template.name if mapping.template else '?'
    )
    return {
        'mapping_id': str(mapping.id),
        'name': name,
        'status': 'skipped',
    }


def unskip_recurring(mapping_id, profile=None):
    """Restore a skipped recurring item back to missing status."""
    mapping = RecurringMapping.objects.select_related('template').get(id=mapping_id, profile=profile)
    mapping.status = 'missing'
    mapping.save()

    name = mapping.custom_name if mapping.is_custom else (
        mapping.template.name if mapping.template else '?'
    )
    return {
        'mapping_id': str(mapping.id),
        'name': name,
        'status': 'missing',
    }


# ---------------------------------------------------------------------------
# A2-7: save_balance_override
# ---------------------------------------------------------------------------

def save_balance_override(month_str, balance, profile=None):
    """
    Save or update the checking account balance override for a month.
    """
    bo, created = BalanceOverride.objects.update_or_create(
        month_str=month_str,
        profile=profile,
        defaults={'balance': Decimal(str(balance))},
    )
    return {
        'month_str': month_str,
        'balance': float(bo.balance),
        'created': created,
    }


# ---------------------------------------------------------------------------
# Recurring template management (Settings)
# ---------------------------------------------------------------------------

def get_recurring_templates(profile=None):
    """
    Return all RecurringTemplate items used for recurring budget tracking.
    """
    templates = RecurringTemplate.objects.filter(
        is_active=True,
        profile=profile,
    ).order_by('display_order', 'name')

    items = []
    for tpl in templates:
        items.append({
            'id': str(tpl.id),
            'name': tpl.name,
            'template_type': tpl.template_type,
            'default_limit': float(tpl.default_limit),
            'due_day': tpl.due_day,
            'display_order': tpl.display_order,
        })

    return {'templates': items, 'count': len(items)}


def update_recurring_template(template_id, profile=None, **kwargs):
    """
    Update a RecurringTemplate used for recurring items.
    Supported fields: name, template_type, default_limit, due_day, display_order
    """
    tpl = RecurringTemplate.objects.get(id=template_id, profile=profile)

    if 'name' in kwargs and kwargs['name'] is not None:
        tpl.name = kwargs['name'].strip()
    if 'template_type' in kwargs and kwargs['template_type'] is not None:
        tpl.template_type = kwargs['template_type']
    if 'default_limit' in kwargs and kwargs['default_limit'] is not None:
        tpl.default_limit = Decimal(str(kwargs['default_limit']))
    if 'due_day' in kwargs:
        tpl.due_day = int(kwargs['due_day']) if kwargs['due_day'] else None
    if 'display_order' in kwargs and kwargs['display_order'] is not None:
        tpl.display_order = int(kwargs['display_order'])

    tpl.save()

    return {
        'id': str(tpl.id),
        'name': tpl.name,
        'template_type': tpl.template_type,
        'default_limit': float(tpl.default_limit),
        'due_day': tpl.due_day,
        'display_order': tpl.display_order,
    }


def create_recurring_template(name, template_type, default_limit, due_day=None, profile=None):
    """
    Create a new RecurringTemplate for recurring budget tracking.
    """
    # Find max display_order for this type
    max_order = RecurringTemplate.objects.filter(
        template_type=template_type,
        profile=profile,
    ).aggregate(m=Max('display_order'))['m'] or 0

    tpl = RecurringTemplate.objects.create(
        name=name.strip(),
        template_type=template_type,
        default_limit=Decimal(str(default_limit)),
        due_day=due_day,
        is_active=True,
        display_order=max_order + 1,
        profile=profile,
    )

    return {
        'id': str(tpl.id),
        'name': tpl.name,
        'template_type': tpl.template_type,
        'default_limit': float(tpl.default_limit),
        'due_day': tpl.due_day,
        'display_order': tpl.display_order,
    }


def delete_recurring_template(template_id, profile=None):
    """
    Deactivate a RecurringTemplate (soft delete).
    Sets is_active=False and default_limit=0 so it won't appear in future months.
    """
    tpl = RecurringTemplate.objects.get(id=template_id, profile=profile)
    tpl.is_active = False
    tpl.default_limit = Decimal('0.00')
    tpl.save()

    return {
        'id': str(tpl.id),
        'name': tpl.name,
        'deleted': True,
    }


# ---------------------------------------------------------------------------
# Unified metrics (MÉTRICAS)
# Replaces the old get_summary_metrics() and get_control_metrics() functions.
# ---------------------------------------------------------------------------

def _get_prev_month_saldo(month_str, profile=None):
    """
    Get the previous month's saldo projetado to use as this month's
    starting balance when no BalanceOverride is set.

    Calls get_metricas() for the previous month (with _cascade=False to
    prevent infinite recursion on months without a BO anchor).
    """
    prev_str = _month_str_add(month_str, -1)

    # Check if prev month has any transactions at all
    has_data = Transaction.objects.filter(month_str=prev_str, profile=profile).exists()
    if not has_data:
        # Also check if prev month has a BalanceOverride
        try:
            BalanceOverride.objects.get(month_str=prev_str, profile=profile)
        except BalanceOverride.DoesNotExist:
            return None

    # Compute prev month's full metricas to get its saldo_projetado
    prev_metricas = get_metricas(prev_str, _cascade=False, profile=profile)
    return Decimal(str(prev_metricas['saldo_projetado']))


def get_metricas(month_str, _cascade=True, profile=None):
    """
    MÉTRICAS — unified dashboard metrics replacing both get_summary_metrics
    and get_control_metrics. Returns 15 metrics computed with shared queries.

    _cascade: if True, attempts to cascade saldo from previous month.
              Set to False to prevent infinite recursion when called from
              _get_prev_month_saldo().
    """
    import calendar

    year = int(month_str[:4])
    month = int(month_str[5:7])
    today = datetime.now()
    is_current = (today.year == year and today.month == month)

    # --- Cross-month exclusions ---
    # Find transactions from THIS month that have been claimed by a DIFFERENT
    # month's recurring mapping. These should be excluded from this month's
    # income/expense totals to avoid double-counting.
    cross_month_exclude_ids = set()
    cross_month_targets = {}  # txn_id -> target month_str
    other_month_mappings = RecurringMapping.objects.filter(
        profile=profile,
    ).exclude(
        month_str=month_str
    ).prefetch_related('cross_month_transactions')
    for om in other_month_mappings:
        for t in om.cross_month_transactions.filter(month_str=month_str):
            cross_month_exclude_ids.add(t.id)
            cross_month_targets[t.id] = om.month_str

    # --- Shared transaction queries (exclude internal transfers + cross-month moved) ---
    txns = Transaction.objects.filter(
        month_str=month_str,
        is_internal_transfer=False,
        profile=profile,
    ).exclude(
        id__in=cross_month_exclude_ids
    ).select_related('category', 'account')

    income_txns = txns.filter(amount__gt=0)
    expense_txns = txns.filter(amount__lt=0)

    # Unfiltered pools for recurring matching (includes internal transfers,
    # but still excludes cross-month moved transactions)
    all_txns = Transaction.objects.filter(
        month_str=month_str,
        profile=profile,
    ).exclude(
        id__in=cross_month_exclude_ids
    ).select_related('category', 'account')
    all_income = all_txns.filter(amount__gt=0)
    all_expense = all_txns.filter(amount__lt=0)

    # --- Cross-month INCLUSIONS ---
    # Transactions from OTHER months that are cross-month linked TO this
    # month's recurring mappings. These should count toward this month's
    # income/expense totals (e.g., December salary linked to January).
    cross_month_include_income = Decimal('0.00')
    cross_month_include_expense = Decimal('0.00')
    this_month_mappings_cm = RecurringMapping.objects.filter(
        month_str=month_str,
        profile=profile,
    ).prefetch_related('cross_month_transactions')
    for m in this_month_mappings_cm:
        for t in m.cross_month_transactions.all():
            if t.amount > 0:
                cross_month_include_income += t.amount
            else:
                cross_month_include_expense += t.amount

    # =====================================================================
    # 1. ENTRADAS ATUAIS — actual income received this month
    #    Includes cross-month transactions linked TO this month's mappings
    # =====================================================================
    entradas_atuais = (income_txns.aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')) + cross_month_include_income

    # =====================================================================
    # 2. ENTRADAS PROJETADAS — total expected income from recurring template
    # =====================================================================
    income_mappings = RecurringMapping.objects.filter(
        month_str=month_str,
        profile=profile,
    ).filter(
        Q(template__template_type='Income') | Q(is_custom=True, custom_type='Income')
    ).exclude(status='skipped').select_related('template', 'category', 'transaction').prefetch_related('transactions')

    entradas_projetadas = Decimal('0.00')
    for m in income_mappings:
        entradas_projetadas += m.expected_amount

    # =====================================================================
    # 3. GASTOS ATUAIS — total actual expenses (CC + checking)
    #    Includes cross-month expense transactions linked TO this month
    # =====================================================================
    gastos_atuais = abs((expense_txns.aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')) + cross_month_include_expense)

    # =====================================================================
    # 4. GASTOS PROJETADOS — expected total expenses for the month
    #    = fixo template + installments + variable budget
    # =====================================================================
    fixo_mappings_all = RecurringMapping.objects.filter(
        month_str=month_str,
        profile=profile,
    ).filter(
        Q(template__template_type='Fixo') | Q(is_custom=True, custom_type='Fixo')
    ).exclude(status='skipped').select_related('template', 'category', 'transaction').prefetch_related('transactions')

    fixo_expected_total = Decimal('0.00')
    for m in fixo_mappings_all:
        fixo_expected_total += m.expected_amount

    schedule = _compute_installment_schedule(month_str, num_future_months=0, profile=profile)
    parcelas_total = Decimal(str(schedule.get(month_str, 0)))

    variable_budget = Category.objects.filter(
        category_type='Variavel', is_active=True,
        profile=profile,
    ).aggregate(total=Sum('default_limit'))['total'] or Decimal('0.00')

    gastos_projetados = fixo_expected_total + parcelas_total + variable_budget

    # --- Helper: compute actual for a recurring mapping ---
    def _get_actual_for_mapping(mapping, is_income=False):
        """Compute actual amount for a mapping based on its match_mode.
        Uses unfiltered pools (includes internal transfers) since recurring
        items may be paid via internal transfers (e.g., CC bill payments).
        Also includes cross-month transactions linked to this mapping.
        """
        pool = all_income if is_income else all_expense
        if mapping.match_mode == 'category' and mapping.category:
            agg = pool.filter(category=mapping.category).aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0.00')
            # Also add cross-month transactions for this mapping
            cross_total = sum(
                t.amount for t in mapping.cross_month_transactions.all()
            )
            combined = agg + cross_total
            return combined if is_income else abs(combined)
        else:
            # Manual mode: use M2M linked transactions + cross-month
            linked = list(mapping.transactions.all()) + list(mapping.cross_month_transactions.all())
            if linked:
                total = sum(t.amount for t in linked)
                return total if is_income else abs(total)
            # Legacy fallback: single transaction FK
            if mapping.transaction:
                amt = mapping.transaction.amount
                return amt if is_income else abs(amt)
            return Decimal('0.00')

    # =====================================================================
    # 5. GASTOS FIXOS — actual fixed expenses paid (linked + category-matched)
    # =====================================================================
    gastos_fixos = Decimal('0.00')
    for mapping in fixo_mappings_all:
        gastos_fixos += _get_actual_for_mapping(mapping, is_income=False)

    # =====================================================================
    # 6. GASTOS VARIÁVEIS — actual variable expenses from transactions
    #    Excludes transactions that are linked to Fixo recurring mappings
    #    (via M2M or category match) to avoid double-counting with gastos_fixos.
    # =====================================================================
    # Collect transaction IDs linked to Fixo mappings
    fixo_linked_txn_ids = set()
    for mapping in fixo_mappings_all:
        if mapping.match_mode == 'category' and mapping.category:
            # Category match: all transactions in the category count as fixo
            cat_txn_ids = all_expense.filter(
                category=mapping.category
            ).values_list('id', flat=True)
            fixo_linked_txn_ids.update(cat_txn_ids)
        else:
            # Manual mode: M2M linked transactions
            for t in mapping.transactions.all():
                fixo_linked_txn_ids.add(t.id)
            # Legacy FK
            if mapping.transaction_id:
                fixo_linked_txn_ids.add(mapping.transaction_id)

    variavel_qs = expense_txns.filter(category__category_type='Variavel')
    if fixo_linked_txn_ids:
        variavel_qs = variavel_qs.exclude(id__in=fixo_linked_txn_ids)
    gastos_variaveis = abs(variavel_qs.aggregate(
        total=Sum('amount'))['total'] or Decimal('0.00'))

    # =====================================================================
    # 7. FATURA MASTER — Mastercard Black + Mastercard - Rafa combined
    # =====================================================================
    fatura_master = abs(Transaction.objects.filter(
        invoice_month=month_str,
        account__name__icontains='Mastercard',
        profile=profile,
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00'))

    # =====================================================================
    # 8. FATURA VISA — Visa Infinite
    # =====================================================================
    fatura_visa = abs(Transaction.objects.filter(
        invoice_month=month_str,
        account__name__icontains='Visa',
        profile=profile,
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00'))

    # =====================================================================
    # 9. PARCELAS — installment total (already computed above)
    # =====================================================================
    # parcelas_total already set

    # =====================================================================
    # 10. A ENTRAR — pending income (from unlinked/unmatched recurring items)
    #     Uses match_mode to determine how to compute actual received.
    # =====================================================================
    a_entrar = Decimal('0.00')
    for mapping in income_mappings:
        expected = mapping.expected_amount
        actual = _get_actual_for_mapping(mapping, is_income=True)
        if actual >= expected:
            continue  # Fully received
        elif actual > 0:
            a_entrar += expected - actual  # Partial
        else:
            a_entrar += expected  # Nothing received

    # =====================================================================
    # 11. A PAGAR — pending fixed expenses (from unlinked/unmatched recurring)
    #     Uses match_mode to determine how to compute actual paid.
    # =====================================================================
    a_pagar = Decimal('0.00')
    for mapping in fixo_mappings_all:
        expected = mapping.expected_amount
        actual = _get_actual_for_mapping(mapping, is_income=False)
        if actual >= expected:
            continue  # Fully paid
        elif actual > 0:
            a_pagar += expected - actual  # Partial
        else:
            a_pagar += expected  # Not paid

    # =====================================================================
    # 12. BALANCE OVERRIDE + SALDO PROJETADO
    # =====================================================================
    balance_override = None
    try:
        bo = BalanceOverride.objects.get(month_str=month_str, profile=profile)
        balance_override = float(bo.balance)
    except BalanceOverride.DoesNotExist:
        pass

    # Cascade: compute previous month's projected ending balance
    prev_month_saldo = None
    prev_month_saldo_float = None
    if _cascade:
        prev_month_saldo = _get_prev_month_saldo(month_str, profile=profile)
        prev_month_saldo_float = float(prev_month_saldo) if prev_month_saldo is not None else None

    if balance_override is not None:
        # User manually set balance for this month — use it.
        # BO already reflects all realized transactions, so only add pending.
        saldo_projetado = Decimal(str(balance_override)) + a_entrar - a_pagar
    elif prev_month_saldo is not None:
        # No manual balance — cascade from previous month's projected saldo.
        # Starting from prev ending balance, add this month's realized +
        # pending income, subtract realized + pending expenses.
        saldo_projetado = (prev_month_saldo
                           + entradas_atuais + a_entrar
                           - gastos_atuais - a_pagar)
    else:
        # No anchor at all — fallback to simple computation
        saldo_projetado = entradas_atuais - gastos_fixos - gastos_variaveis - parcelas_total

    # =====================================================================
    # 13. DIAS ATÉ O FECHAMENTO
    # =====================================================================
    cc_account = Account.objects.filter(
        account_type='credit_card', is_active=True,
        profile=profile,
    ).first()
    closing_day = cc_account.closing_day if cc_account and cc_account.closing_day else 30

    def _safe_closing_date(y, m, day):
        max_day = calendar.monthrange(y, m)[1]
        return datetime(y, m, min(day, max_day))

    if is_current:
        if today.day <= min(closing_day, calendar.monthrange(today.year, today.month)[1]):
            closing_date = _safe_closing_date(today.year, today.month, closing_day)
        else:
            if today.month == 12:
                closing_date = _safe_closing_date(today.year + 1, 1, closing_day)
            else:
                closing_date = _safe_closing_date(today.year, today.month + 1, closing_day)
        dias_fechamento = max(0, (closing_date - today).days)
    else:
        dias_fechamento = -1

    # =====================================================================
    # 14. GASTO DIÁRIO MAX RECOMENDADO
    # =====================================================================
    if is_current:
        if month == 12:
            next_month = datetime(year + 1, 1, 1)
        else:
            next_month = datetime(year, month + 1, 1)
        last_day = next_month - timedelta(days=1)
        days_remaining = max(1, (last_day - today).days + 1)
        diario_recomendado = float(saldo_projetado / days_remaining)
    else:
        if month == 12:
            next_month = datetime(year + 1, 1, 1)
        else:
            next_month = datetime(year, month + 1, 1)
        days_in_month = (next_month - timedelta(days=1)).day
        diario_recomendado = float(saldo_projetado / days_in_month) if days_in_month > 0 else 0.0

    # =====================================================================
    # 15. SAÚDE DO MÊS
    # =====================================================================
    if float(saldo_projetado) <= 0:
        saude = 'CRÍTICO'
        saude_level = 'danger'
    elif float(gastos_atuais) > float(gastos_projetados) * 0.9:
        saude = 'ATENÇÃO'
        saude_level = 'warning'
    else:
        saude = 'SAUDÁVEL'
        saude_level = 'good'

    # Build cross-month moved info for UI (batch fetch)
    cross_month_info = []
    if cross_month_targets:
        cross_txns = {
            t.id: t for t in Transaction.objects.filter(
                id__in=list(cross_month_targets.keys()),
                profile=profile,
            )
        }
        for txn_id, target in cross_month_targets.items():
            t = cross_txns.get(txn_id)
            if t:
                cross_month_info.append({
                    'id': str(txn_id),
                    'description': t.description,
                    'amount': float(t.amount),
                    'moved_to': target,
                })

    result_dict = {
        'month_str': month_str,
        'balance_override': balance_override,
        'prev_month_saldo': prev_month_saldo_float,
        'entradas_atuais': float(entradas_atuais),
        'entradas_projetadas': float(entradas_projetadas),
        'gastos_atuais': float(gastos_atuais),
        'gastos_projetados': float(gastos_projetados),
        'gastos_fixos': float(gastos_fixos),
        'gastos_variaveis': float(gastos_variaveis),
        'fatura_master': float(fatura_master),
        'fatura_visa': float(fatura_visa),
        'parcelas': float(parcelas_total),
        'a_entrar': float(a_entrar),
        'a_pagar': float(a_pagar),
        'saldo_projetado': float(saldo_projetado),
        'dias_fechamento': dias_fechamento,
        'is_current_month': is_current,
        'diario_recomendado': round(diario_recomendado, 2),
        'saude': saude,
        'saude_level': saude_level,
        'cross_month_moved': cross_month_info,
        'savings_target_pct': float(profile.savings_target_pct) if profile else 20.0,
        'savings_rate': round(
            ((float(entradas_atuais) - float(gastos_atuais)) / float(entradas_atuais) * 100)
            if float(entradas_atuais) > 0 else 0.0,
            1
        ),
    }

    # Append custom metrics computed from this month's data
    result_dict['custom_metrics'] = _compute_custom_metrics(month_str, result_dict, profile=profile)
    return result_dict


# ---------------------------------------------------------------------------
# Metricas order + custom metrics
# ---------------------------------------------------------------------------

BUILTIN_CARD_ORDER = [
    'entradas_atuais', 'entradas_projetadas', 'a_entrar', 'a_pagar',
    'dias_fechamento', 'gastos_atuais', 'gastos_projetados', 'gastos_fixos',
    'gastos_variaveis', 'diario_max', 'fatura_master', 'fatura_visa',
    'parcelas', 'saldo_projetado', 'saude', 'meta_poupanca',
]


def _compute_custom_metrics(month_str, metricas_data, profile=None):
    """
    Compute values for all active CustomMetrics for the given month.
    Takes already-computed metricas_data to avoid circular calls.
    """
    custom_metrics = list(CustomMetric.objects.filter(is_active=True, profile=profile).order_by('label'))
    if not custom_metrics:
        return []

    # --- Pre-compute shared data to avoid N+1 queries ---

    # Collect all category IDs referenced by custom metrics
    cat_ids_needed = set()
    template_ids_needed = set()
    needs_fixo = False
    needs_invest = False
    needs_income = False
    for cm in custom_metrics:
        if cm.metric_type in ('category_total', 'category_remaining'):
            cid = cm.config.get('category_id')
            if cid:
                cat_ids_needed.add(cid)
        elif cm.metric_type == 'fixo_total':
            needs_fixo = True
        elif cm.metric_type == 'investimento_total':
            needs_invest = True
        elif cm.metric_type == 'income_total':
            needs_income = True
        elif cm.metric_type == 'recurring_item':
            tid = cm.config.get('template_id')
            if tid:
                template_ids_needed.add(tid)

    # Batch: categories lookup (1 query)
    cats_by_id = {}
    if cat_ids_needed:
        cats_by_id = {str(c.id): c for c in Category.objects.filter(id__in=cat_ids_needed, profile=profile)}

    # Batch: BudgetConfig overrides for referenced categories (1 query)
    budget_overrides = {}
    if cat_ids_needed:
        budget_overrides = {
            str(bc.category_id): float(bc.limit_override)
            for bc in BudgetConfig.objects.filter(
                category_id__in=cat_ids_needed, month_str=month_str, profile=profile,
            )
        }

    # Batch: category spending for referenced categories (1 query)
    cat_spending = {}
    if cat_ids_needed:
        cat_spending = dict(
            Transaction.objects.filter(
                month_str=month_str,
                category_id__in=cat_ids_needed,
                amount__lt=0,
                is_internal_transfer=False,
                profile=profile,
            ).values('category_id').annotate(
                total=Sum('amount')
            ).values_list('category_id', 'total')
        )

    # Pre-compute mapping totals by template type (batch queries)
    def _compute_mapping_totals(mappings_qs, is_income=False):
        """Compute total and count from prefetched mappings."""
        mappings = list(mappings_qs)
        # Pre-compute category totals for category-match mappings
        cat_match_ids = set()
        for m in mappings:
            if m.match_mode == 'category' and m.category_id:
                cat_match_ids.add(m.category_id)
        cat_totals = {}
        if cat_match_ids:
            amount_filter = dict(amount__gt=0) if is_income else dict(amount__lt=0)
            cat_totals = dict(
                Transaction.objects.filter(
                    month_str=month_str,
                    category_id__in=cat_match_ids,
                    profile=profile,
                    **amount_filter,
                ).values('category_id').annotate(
                    t=Sum('amount')
                ).values_list('category_id', 't')
            )

        total = Decimal('0.00')
        count = 0
        for mapping in mappings:
            linked = list(mapping.transactions.all()) + list(mapping.cross_month_transactions.all())
            if linked:
                amt = sum(t.amount for t in linked)
                total += abs(amt) if not is_income else amt
                count += 1
            elif mapping.match_mode == 'category' and mapping.category_id:
                agg = cat_totals.get(mapping.category_id, Decimal('0.00'))
                if agg:
                    total += abs(agg) if not is_income else agg
                    count += 1
        return total, count, len(mappings)

    # Pre-compute fixo/investimento/income totals (1 query each, only if needed)
    _fixo_cache = None
    _invest_cache = None
    _income_cache = None

    if needs_fixo:
        qs = RecurringMapping.objects.filter(
            month_str=month_str, template__template_type='Fixo', profile=profile,
        ).select_related('template', 'category').prefetch_related(
            'transactions', 'cross_month_transactions'
        )
        _fixo_cache = _compute_mapping_totals(qs)

    if needs_invest:
        qs = RecurringMapping.objects.filter(
            month_str=month_str, template__template_type='Investimento', profile=profile,
        ).select_related('template', 'category').prefetch_related(
            'transactions', 'cross_month_transactions'
        )
        _invest_cache = _compute_mapping_totals(qs)

    if needs_income:
        qs = RecurringMapping.objects.filter(
            month_str=month_str, template__template_type='Income', profile=profile,
        ).select_related('template', 'category').prefetch_related(
            'transactions', 'cross_month_transactions'
        )
        _income_cache = _compute_mapping_totals(qs, is_income=True)

    # Pre-fetch recurring_item mappings (1 query for all template_ids)
    item_mappings_by_template = {}
    if template_ids_needed:
        item_mappings = RecurringMapping.objects.filter(
            month_str=month_str, template_id__in=template_ids_needed, profile=profile,
        ).select_related('template', 'category').prefetch_related(
            'transactions', 'cross_month_transactions'
        )
        for m in item_mappings:
            item_mappings_by_template[str(m.template_id)] = m

    # --- Main loop: no database queries inside ---
    results = []

    for cm in custom_metrics:
        card_id = f'custom_{str(cm.id)}'
        value = 'R$ 0'
        subtitle = ''
        color = cm.color

        if cm.metric_type == 'category_total':
            cat_id = cm.config.get('category_id')
            if cat_id:
                spent_agg = cat_spending.get(cat_id, Decimal('0.00'))
                spent = abs(spent_agg)
                value = f'R$ {int(spent):,}'.replace(',', '.')
                subtitle = 'gasto na categoria'

        elif cm.metric_type == 'category_remaining':
            cat_id = cm.config.get('category_id')
            if cat_id:
                cat = cats_by_id.get(str(cat_id))
                if not cat:
                    continue
                # Get budget (override or default)
                limit = budget_overrides.get(str(cat_id), float(cat.default_limit))

                spent_agg = cat_spending.get(cat_id, Decimal('0.00'))
                spent = float(abs(spent_agg))
                remaining = max(0, limit - spent)
                pct = (spent / limit * 100) if limit > 0 else 0

                value = f'R$ {int(remaining):,}'.replace(',', '.')
                subtitle = f'{pct:.0f}% usado'
                if pct > 100:
                    color = 'var(--color-red)'
                elif pct > 80:
                    color = 'var(--color-orange)'
                else:
                    color = 'var(--color-green)'

        elif cm.metric_type == 'fixo_total':
            if _fixo_cache:
                total, paid, total_count = _fixo_cache
                value = f'R$ {int(total):,}'.replace(',', '.')
                subtitle = f'{paid} de {total_count} pagos'

        elif cm.metric_type == 'investimento_total':
            if _invest_cache:
                total, paid, total_count = _invest_cache
                value = f'R$ {int(total):,}'.replace(',', '.')
                subtitle = f'{paid} de {total_count} investidos'

        elif cm.metric_type == 'income_total':
            if _income_cache:
                total, received, total_count = _income_cache
                value = f'R$ {int(abs(total)):,}'.replace(',', '.')
                subtitle = f'{received} de {total_count} recebidos'

        elif cm.metric_type == 'recurring_item':
            template_id = cm.config.get('template_id')
            if template_id:
                mapping = item_mappings_by_template.get(str(template_id))
                if mapping:
                    linked = list(mapping.transactions.all()) + list(mapping.cross_month_transactions.all())
                    actual = Decimal('0.00')
                    if linked:
                        actual = abs(sum(t.amount for t in linked))
                    elif mapping.match_mode == 'category' and mapping.category:
                        is_income = mapping.template and mapping.template.template_type == 'Income'
                        cat_key = mapping.category_id
                        if is_income:
                            # For income items, need positive amounts
                            agg = Transaction.objects.filter(
                                month_str=month_str, category=mapping.category,
                                amount__gt=0,
                                profile=profile,
                            ).aggregate(t=Sum('amount'))['t'] or Decimal('0.00')
                        else:
                            agg = cat_spending.get(cat_key, Decimal('0.00'))
                        actual = abs(agg)
                    expected = float(mapping.expected_amount)
                    value = f'R$ {int(actual):,}'.replace(',', '.')
                    if expected > 0:
                        subtitle = f'de R$ {int(expected):,} esperado'.replace(',', '.')
                    else:
                        subtitle = mapping.template.name if mapping.template else ''
                else:
                    value = 'R$ 0'
                    subtitle = 'sem mapeamento'

        elif cm.metric_type == 'builtin_clone':
            # Clone a builtin card — just read the precomputed value
            builtin_key = cm.config.get('builtin_key')
            if builtin_key and builtin_key in metricas_data:
                raw = metricas_data[builtin_key]
                if isinstance(raw, (int, float, Decimal)):
                    value = f'R$ {int(abs(float(raw))):,}'.replace(',', '.')
                elif isinstance(raw, str):
                    value = raw
                else:
                    value = str(raw)
                subtitle = cm.config.get('subtitle', '')

        results.append({
            'id': str(cm.id),
            'card_id': card_id,
            'label': cm.label,
            'value': value,
            'subtitle': subtitle,
            'color': color,
            'metric_type': cm.metric_type,
        })

    return results


def _get_all_known_card_ids(profile=None):
    """Return set of all valid card IDs (builtin + active custom)."""
    custom_ids = [
        f'custom_{str(cid)}'
        for cid in CustomMetric.objects.filter(is_active=True, profile=profile)
            .order_by('label')
            .values_list('id', flat=True)
    ]
    return BUILTIN_CARD_ORDER + custom_ids


def _reconcile_order(order, hidden, all_known_ids):
    """
    Ensure order + hidden contain exactly all_known_ids.
    - New cards not in order or hidden get appended to order.
    - Stale cards (deleted) get removed from both.
    """
    all_known = set(all_known_ids)
    hidden_set = set(hidden)
    order_set = set(order)
    # Append genuinely new cards (not hidden, not in order)
    for cid in all_known_ids:
        if cid not in order_set and cid not in hidden_set:
            order.append(cid)
    # Remove stale
    order = [cid for cid in order if cid in all_known]
    hidden = [cid for cid in hidden if cid in all_known]
    return order, hidden


def get_metricas_order(month_str, profile=None):
    """
    Return the card order + hidden cards + lock status for a month.
    Resolution: per-month override > global default > hardcoded BUILTIN_CARD_ORDER.
    """
    all_known_ids = _get_all_known_card_ids(profile=profile)

    # Global default
    global_hidden = []
    try:
        global_cfg = MetricasOrderConfig.objects.get(month_str='__default__', profile=profile)
        global_order = list(global_cfg.card_order)
        global_hidden = list(global_cfg.hidden_cards or [])
    except MetricasOrderConfig.DoesNotExist:
        global_order = list(all_known_ids)

    global_order, global_hidden = _reconcile_order(
        global_order, global_hidden, all_known_ids
    )

    # Per-month override
    try:
        month_cfg = MetricasOrderConfig.objects.get(month_str=month_str, profile=profile)
        effective_order = list(month_cfg.card_order)
        effective_hidden = list(month_cfg.hidden_cards or [])
        is_locked = month_cfg.is_locked
        has_month_override = True
    except MetricasOrderConfig.DoesNotExist:
        effective_order = list(global_order)
        effective_hidden = list(global_hidden)
        is_locked = False
        has_month_override = False

    effective_order, effective_hidden = _reconcile_order(
        effective_order, effective_hidden, all_known_ids
    )

    return {
        'month_str': month_str,
        'card_order': effective_order,
        'hidden_cards': effective_hidden,
        'global_default_order': global_order,
        'global_hidden_cards': global_hidden,
        'is_locked': is_locked,
        'has_month_override': has_month_override,
    }


def save_metricas_order(month_str, card_order, hidden_cards=None, profile=None):
    """Save card order (and optionally hidden cards) for a specific month."""
    defaults = {'card_order': card_order}
    if hidden_cards is not None:
        defaults['hidden_cards'] = hidden_cards
    cfg, created = MetricasOrderConfig.objects.update_or_create(
        month_str=month_str,
        profile=profile,
        defaults=defaults,
    )
    return {
        'month_str': month_str,
        'card_order': cfg.card_order,
        'hidden_cards': cfg.hidden_cards,
    }


def make_default_order(card_order, hidden_cards=None, profile=None):
    """
    Set card_order as the global default and delete all unlocked per-month
    overrides so they inherit the new default.
    """
    defaults = {'card_order': card_order}
    if hidden_cards is not None:
        defaults['hidden_cards'] = hidden_cards
    MetricasOrderConfig.objects.update_or_create(
        month_str='__default__',
        profile=profile,
        defaults=defaults,
    )
    deleted_count, _ = MetricasOrderConfig.objects.filter(
        is_locked=False,
        profile=profile,
    ).exclude(
        month_str='__default__'
    ).delete()
    return {'global_default': card_order, 'months_reset': deleted_count}


def toggle_metricas_lock(month_str, locked, profile=None):
    """Lock or unlock a month's metricas order."""
    if locked:
        order_data = get_metricas_order(month_str, profile=profile)
        cfg, _ = MetricasOrderConfig.objects.update_or_create(
            month_str=month_str,
            profile=profile,
            defaults={
                'card_order': order_data['card_order'],
                'hidden_cards': order_data['hidden_cards'],
                'is_locked': True,
            },
        )
    else:
        try:
            cfg = MetricasOrderConfig.objects.get(month_str=month_str, profile=profile)
            cfg.is_locked = False
            cfg.save(update_fields=['is_locked', 'updated_at'])
        except MetricasOrderConfig.DoesNotExist:
            pass
    return {'month_str': month_str, 'is_locked': locked}


def get_custom_metric_options(profile=None):
    """Return active custom metrics + available categories + templates + builtin keys for the picker UI."""
    metrics = CustomMetric.objects.filter(is_active=True, profile=profile).order_by('label')
    categories = list(
        Category.objects.filter(is_active=True, profile=profile)
        .order_by('display_order', 'name')
        .values('id', 'name', 'category_type', 'default_limit')
    )
    # Convert UUID to string for JSON
    for c in categories:
        c['id'] = str(c['id'])
        c['default_limit'] = float(c['default_limit'])

    # Recurring templates for the "recurring_item" picker
    templates = list(
        RecurringTemplate.objects.filter(is_active=True, profile=profile)
        .order_by('template_type', 'name')
        .values('id', 'name', 'template_type', 'default_limit')
    )
    for t in templates:
        t['id'] = str(t['id'])
        t['default_limit'] = float(t['default_limit'])

    # Builtin card keys available for cloning
    builtin_cards = [
        {'key': 'entradas_atuais', 'label': 'ENTRADAS ATUAIS', 'subtitle': 'recebido no mes'},
        {'key': 'entradas_projetadas', 'label': 'ENTRADAS PROJETADAS', 'subtitle': 'receita esperada'},
        {'key': 'gastos_atuais', 'label': 'GASTOS ATUAIS', 'subtitle': 'gasto total no mes'},
        {'key': 'gastos_projetados', 'label': 'GASTOS PROJETADOS', 'subtitle': 'despesa esperada'},
        {'key': 'gastos_fixos', 'label': 'GASTOS FIXOS', 'subtitle': 'fixos pagos'},
        {'key': 'gastos_variaveis', 'label': 'GASTOS VARIAVEIS', 'subtitle': 'variaveis gastos'},
        {'key': 'fatura_master', 'label': 'FATURA MASTER', 'subtitle': 'mastercard total'},
        {'key': 'fatura_visa', 'label': 'FATURA VISA', 'subtitle': 'visa total'},
        {'key': 'parcelas', 'label': 'PARCELAS', 'subtitle': 'parcelamentos'},
        {'key': 'a_entrar', 'label': 'A ENTRAR', 'subtitle': 'receita pendente'},
        {'key': 'a_pagar', 'label': 'A PAGAR', 'subtitle': 'despesa pendente'},
        {'key': 'saldo_projetado', 'label': 'SALDO PROJETADO', 'subtitle': 'calculado'},
        {'key': 'diario_recomendado', 'label': 'GASTO DIARIO MAX', 'subtitle': 'recomendado por dia'},
    ]

    return {
        'metrics': [{
            'id': str(m.id),
            'metric_type': m.metric_type,
            'label': m.label,
            'config': m.config,
            'color': m.color,
        } for m in metrics],
        'available_categories': categories,
        'available_templates': templates,
        'available_builtins': builtin_cards,
    }


def create_custom_metric(metric_type, label, config, color='var(--color-accent)', profile=None):
    """Create a new custom metric definition."""
    cm = CustomMetric.objects.create(
        metric_type=metric_type,
        label=label,
        config=config,
        color=color,
        profile=profile,
    )
    card_id = f'custom_{str(cm.id)}'
    # Append to all existing order configs
    for cfg in MetricasOrderConfig.objects.filter(profile=profile):
        if card_id not in cfg.card_order:
            cfg.card_order.append(card_id)
            cfg.save(update_fields=['card_order'])
    return {'id': str(cm.id), 'card_id': card_id, 'label': cm.label}


def delete_custom_metric(metric_id, profile=None):
    """Delete a custom metric and remove from all order configs."""
    cm = CustomMetric.objects.get(id=metric_id, profile=profile)
    card_id = f'custom_{str(cm.id)}'
    cm.delete()
    for cfg in MetricasOrderConfig.objects.filter(profile=profile):
        if card_id in cfg.card_order:
            cfg.card_order.remove(card_id)
            cfg.save(update_fields=['card_order'])
    return {'deleted': True, 'card_id': card_id}


# ---------------------------------------------------------------------------
# Card transactions
# ---------------------------------------------------------------------------

def get_card_transactions(month_str, account_filter=None, profile=None):
    """
    CONTROLE CARTÕES — credit card transactions from the statement (invoice)
    being paid this month.

    Uses invoice_month to show the actual bill contents. E.g., viewing February
    shows the Feb invoice (paid Feb 5th), which contains January purchases.
    This aligns with cash flow: "How much is the CC taking from my account?"
    """
    import re

    # Prefer invoice_month; fall back to month_str for older imports without it
    qs = Transaction.objects.filter(
        invoice_month=month_str,
        account__account_type='credit_card',
        profile=profile,
    ).select_related('account', 'category', 'subcategory').order_by('-date')

    if not qs.exists():
        qs = Transaction.objects.filter(
            month_str=month_str,
            invoice_month='',
            account__account_type='credit_card',
            profile=profile,
        ).select_related('account', 'category', 'subcategory').order_by('-date')

    if account_filter:
        qs = qs.filter(account__name__icontains=account_filter)

    # Collect mapped transaction IDs for this month
    mapped_txn_ids = _get_mapped_transaction_ids(month_str, profile)

    results = []
    for txn in qs:
        # Extract installment info from description
        parcela = ''
        m = re.search(r'(\d{1,2}/\d{1,2})', txn.description)
        if m:
            parcela = m.group(1)
        elif txn.installment_info:
            parcela = txn.installment_info

        results.append({
            'id': str(txn.id),
            'date': txn.date.strftime('%Y-%m-%d'),
            'description': txn.description,
            'amount': float(txn.amount),
            'account': txn.account.name,
            'category': txn.category.name if txn.category else 'Não categorizado',
            'category_id': str(txn.category.id) if txn.category else None,
            'subcategory': txn.subcategory.name if txn.subcategory else '',
            'subcategory_id': str(txn.subcategory.id) if txn.subcategory else None,
            'parcela': parcela,
            'is_installment': txn.is_installment,
            'is_mapped': txn.id in mapped_txn_ids,
        })

    return {
        'month_str': month_str,
        'transactions': results,
        'count': len(results),
        'total': float(sum(r['amount'] for r in results)),
    }


def get_installment_details(month_str, profile=None):
    """
    INSTALLMENT BREAKDOWN — installments being charged on this month's bill.

    Uses invoice_month to get the actual CC statement for this month.

    CC statements may list ALL future positions for a purchase (01/03, 02/03,
    03/03 all on the same bill).  Only the LOWEST position per purchase is the
    actual charge for this bill — higher positions are previews of future bills.
    We deduplicate by (base_desc, account, amount, total) and keep only the
    lowest position per purchase.

    For months without a CC statement, projects installments from older
    statements.

    Returns: dict with 'source' ('real' or 'projected'), deduped installment
    items, count, and total.
    """
    # Check if this month has real installment data
    # Prefer invoice_month; fall back to month_str for older imports
    real_installments = Transaction.objects.filter(
        invoice_month=month_str,
        is_installment=True,
        amount__lt=0,
        profile=profile,
    ).select_related('account', 'category', 'subcategory')

    if not real_installments.exists():
        real_installments = Transaction.objects.filter(
            month_str=month_str,
            invoice_month='',
            is_installment=True,
            amount__lt=0,
            profile=profile,
        ).select_related('account', 'category', 'subcategory')

    if real_installments.exists():
        # Group by purchase identity, keep only the lowest position per group
        purchase_groups = {}  # key -> (current_pos, total_inst, txn)
        non_parseable_items = []

        for txn in real_installments.order_by('account__name', 'date'):
            m_match = re.search(r'(\d{1,2})/(\d{1,2})', txn.description)
            if not m_match and txn.installment_info:
                m_match = re.match(r'(\d+)/(\d+)', txn.installment_info)

            if m_match:
                current = int(m_match.group(1))
                total_inst = int(m_match.group(2))
                base_desc = re.sub(r'\s*\d{1,2}/\d{1,2}\s*$', '', txn.description).strip()
                acct = txn.account.name if txn.account else ''
                amt = round(float(abs(txn.amount)), 2)

                group_key = (base_desc, acct, amt, total_inst)
                if group_key not in purchase_groups or current < purchase_groups[group_key][0]:
                    purchase_groups[group_key] = (current, total_inst, txn)
            else:
                # Flagged as installment but no parseable N/M — include as-is
                non_parseable_items.append({
                    'id': str(txn.id),
                    'date': txn.date.strftime('%Y-%m-%d'),
                    'description': txn.description,
                    'amount': float(abs(txn.amount)),
                    'account': txn.account.name if txn.account else '',
                    'category': txn.category.name if txn.category else 'Não categorizado',
                    'category_id': str(txn.category.id) if txn.category else None,
                    'subcategory': txn.subcategory.name if txn.subcategory else '',
                    'subcategory_id': str(txn.subcategory.id) if txn.subcategory else None,
                    'parcela': txn.installment_info or '',
                    'source_month': month_str,
                })

        # Build items from deduplicated purchase groups (lowest position only)
        items = []
        for (base_desc, acct, amt, total_inst), (current, _, txn) in purchase_groups.items():
            parcela_str = f'{current}/{total_inst}'
            items.append({
                'id': str(txn.id),
                'date': txn.date.strftime('%Y-%m-%d'),
                'description': f'{base_desc} {parcela_str}',
                'amount': amt,
                'account': acct,
                'category': txn.category.name if txn.category else 'Não categorizado',
                'category_id': str(txn.category.id) if txn.category else None,
                'subcategory': txn.subcategory.name if txn.subcategory else '',
                'subcategory_id': str(txn.subcategory.id) if txn.subcategory else None,
                'parcela': parcela_str,
                'source_month': month_str,
            })

        items.extend(non_parseable_items)
        items.sort(key=lambda x: (x['account'], x['date']))

        total = sum(i['amount'] for i in items)
        return {
            'month_str': month_str,
            'source': 'real',
            'items': items,
            'count': len(items),
            'total': round(total, 2),
        }

    # No real data — project from previous CC statements.
    #
    # CC statements list ALL installment positions for a purchase on every
    # bill (01/06, 02/06, 03/06 etc. all on the same statement).  Only the
    # LOWEST position per purchase per source month represents the "current"
    # installment actually charged that month.  Higher positions are
    # informational and represent future months.
    #
    # Strategy:
    #   1. For each source month, group installments by (base_desc, account,
    #      amount, total) and keep only the lowest-position entry per group.
    #      That entry represents the real charge for that source month.
    #   2. Project the lowest position forward by lookback to get the
    #      target-month position.
    #   3. Deduplicate across source months: the same purchase projected from
    #      different source months yields the same target position; keep only
    #      the most recent source (lowest lookback).
    import calendar as _cal

    items = []
    seen = set()  # (base_desc, account, amount, total_inst) — one entry per purchase

    # Batch fetch all lookback months' installment transactions (2 queries)
    lookback_months_list = [_month_str_add(month_str, -i) for i in range(1, 13)]
    _lb_invoice_txns = list(Transaction.objects.filter(
        invoice_month__in=lookback_months_list,
        is_installment=True,
        amount__lt=0,
        profile=profile,
    ).select_related('account', 'category', 'subcategory'))
    _lb_by_invoice = {}
    for txn in _lb_invoice_txns:
        _lb_by_invoice.setdefault(txn.invoice_month, []).append(txn)

    _lb_months_with_invoice = set(_lb_by_invoice.keys())
    _lb_months_needing_fallback = set(lookback_months_list) - _lb_months_with_invoice
    _lb_by_fallback = {}
    if _lb_months_needing_fallback:
        _lb_fallback_txns = list(Transaction.objects.filter(
            month_str__in=_lb_months_needing_fallback,
            invoice_month='',
            is_installment=True,
            amount__lt=0,
            profile=profile,
        ).select_related('account', 'category', 'subcategory'))
        for txn in _lb_fallback_txns:
            _lb_by_fallback.setdefault(txn.month_str, []).append(txn)

    for lookback in range(1, 13):
        source_month = lookback_months_list[lookback - 1]
        inst_txns = _lb_by_invoice.get(source_month) or _lb_by_fallback.get(source_month) or []
        if not inst_txns:
            continue

        # Step 1: Group by purchase, keep only the lowest position per group
        purchase_groups = {}  # key -> (current_pos, total, txn)
        for txn in inst_txns:
            info = txn.installment_info or ''
            m_match = re.match(r'(\d+)/(\d+)', info)
            if not m_match:
                dm = re.search(r'(\d{1,2})/(\d{1,2})', txn.description)
                if dm:
                    m_match = dm
            if not m_match:
                continue

            current = int(m_match.group(1))
            total_inst = int(m_match.group(2))
            base_desc = re.sub(r'\s*\d{1,2}/\d{1,2}\s*$', '', txn.description).strip()
            acct = txn.account.name if txn.account else ''
            amt = round(float(abs(txn.amount)), 2)

            group_key = (base_desc, acct, amt, total_inst)

            if group_key not in purchase_groups or current < purchase_groups[group_key][0]:
                purchase_groups[group_key] = (current, total_inst, txn)

        # Step 2: Project each purchase's lowest position to the target month
        for group_key, (current, total_inst, txn) in purchase_groups.items():
            base_desc, acct, amt, _ = group_key
            position = current + lookback

            if position > total_inst:
                continue  # This purchase is fully paid off by target month

            # Step 3: Deduplicate across source months
            purchase_id = (base_desc, acct, amt, total_inst)
            if purchase_id in seen:
                continue  # Already projected from a more recent source month
            seen.add(purchase_id)

            parcela_str = f'{position}/{total_inst}'

            # Project the date into the target month
            target_dt = _parse_month(month_str)
            try:
                projected_date = txn.date.replace(year=target_dt.year, month=target_dt.month)
            except ValueError:
                last_day = _cal.monthrange(target_dt.year, target_dt.month)[1]
                projected_date = txn.date.replace(year=target_dt.year, month=target_dt.month, day=last_day)

            projected_desc = f'{base_desc} {parcela_str}'

            items.append({
                'id': str(txn.id),
                'date': projected_date.strftime('%Y-%m-%d'),
                'description': projected_desc,
                'amount': amt,
                'account': acct,
                'category': txn.category.name if txn.category else 'Não categorizado',
                'category_id': str(txn.category.id) if txn.category else None,
                'subcategory': txn.subcategory.name if txn.subcategory else '',
                'subcategory_id': str(txn.subcategory.id) if txn.subcategory else None,
                'parcela': parcela_str,
                'source_month': source_month,
            })

    # Sort by account then date
    items.sort(key=lambda x: (x['account'], x['date']))
    total = sum(i['amount'] for i in items)
    return {
        'month_str': month_str,
        'source': 'projected',
        'items': items,
        'count': len(items),
        'total': round(total, 2),
    }


# ---------------------------------------------------------------------------
# Installment sibling categorization
# ---------------------------------------------------------------------------

def categorize_installment_siblings(transaction_id, category_id, subcategory_id=None, profile=None):
    """
    Categorize an installment transaction AND all its siblings (same purchase,
    different months).

    Siblings are identified by matching:
    (base_description, account, |amount|, total_installments)

    Returns: dict with count of updated transactions and their IDs.
    """
    txn = Transaction.objects.select_related('account', 'category', 'subcategory').get(id=transaction_id, profile=profile)

    # Parse installment info
    m_match = re.search(r'(\d{1,2})/(\d{1,2})', txn.description)
    if not m_match and txn.installment_info:
        m_match = re.match(r'(\d+)/(\d+)', txn.installment_info)

    if not m_match:
        # Not a parseable installment — just update this one transaction
        update_fields = {'category_id': category_id, 'is_manually_categorized': True}
        if subcategory_id:
            update_fields['subcategory_id'] = subcategory_id
        else:
            update_fields['subcategory_id'] = None
        Transaction.objects.filter(id=transaction_id, profile=profile).update(**update_fields)
        return {'updated': 1, 'sibling_ids': [str(transaction_id)]}

    total_installments = int(m_match.group(2))
    base_desc = re.sub(r'\s*\d{1,2}/\d{1,2}\s*$', '', txn.description).strip()
    acct_id = txn.account_id
    amt = round(float(abs(txn.amount)), 2)

    # Find all siblings: same base description, same account, same |amount|,
    # is_installment=True, and installment count matches total
    candidates = Transaction.objects.filter(
        account_id=acct_id,
        is_installment=True,
        profile=profile,
    )

    sibling_ids = []
    for candidate in candidates:
        # Check amount matches (exact match after rounding)
        if round(float(abs(candidate.amount)), 2) != amt:
            continue
        # Check base description matches
        cand_base = re.sub(r'\s*\d{1,2}/\d{1,2}\s*$', '', candidate.description).strip()
        if cand_base != base_desc:
            continue
        # Check total installments match
        cm = re.search(r'(\d{1,2})/(\d{1,2})', candidate.description)
        if not cm and candidate.installment_info:
            cm = re.match(r'(\d+)/(\d+)', candidate.installment_info)
        if cm and int(cm.group(2)) == total_installments:
            sibling_ids.append(candidate.id)

    if not sibling_ids:
        sibling_ids = [txn.id]

    # Update all siblings
    update_fields = {'category_id': category_id, 'is_manually_categorized': True}
    if subcategory_id:
        update_fields['subcategory_id'] = subcategory_id
    else:
        update_fields['subcategory_id'] = None
    updated = Transaction.objects.filter(id__in=sibling_ids, profile=profile).update(**update_fields)

    return {
        'updated': updated,
        'sibling_ids': [str(sid) for sid in sibling_ids],
    }


# ---------------------------------------------------------------------------
# Mapping candidates + map/unmap
# ---------------------------------------------------------------------------

def get_mapping_candidates(month_str, category_id=None, mapping_id=None, profile=None):
    """
    Returns candidate transactions for mapping to a recurring category.
    Includes BOTH checking (month_str) and CC (invoice_month) transactions.
    Shows ALL transactions (including already-linked ones), sorted by relevance.

    Each candidate includes:
    - is_linked: linked to THIS specific mapping's M2M set
    - is_globally_linked: linked to ANY mapping this month (greyed out in UI)
    - source: 'checking' or 'credit_card' for frontend filtering

    Accepts either category_id (for category-based items) or mapping_id
    (for custom items without a category).
    """
    cat = None
    mapping = None
    expected = 0
    cat_name = ''

    if mapping_id:
        mapping = RecurringMapping.objects.select_related('template', 'category').get(id=mapping_id, profile=profile)
        cat = mapping.category
        expected = float(mapping.expected_amount)
        cat_name = mapping.custom_name if mapping.is_custom else (
            mapping.template.name if mapping.template else '?'
        )
    elif category_id:
        cat = Category.objects.get(id=category_id, profile=profile)
        expected = float(cat.default_limit)
        cat_name = cat.name
        # Look up the mapping for this category+month (if it exists)
        mapping = RecurringMapping.objects.filter(
            category=cat, month_str=month_str, profile=profile,
        ).first()

    # Build set of linked transaction IDs for THIS mapping
    linked_ids = set()
    if mapping:
        linked_ids = set(
            str(tid) for tid in mapping.transactions.values_list('id', flat=True)
        )

    # Build set of GLOBALLY linked transaction IDs (any mapping this month)
    globally_linked_ids = set()
    all_mappings = RecurringMapping.objects.filter(
        month_str=month_str,
        profile=profile,
    ).prefetch_related('transactions')
    for m in all_mappings:
        for t in m.transactions.all():
            globally_linked_ids.add(str(t.id))
        if m.transaction_id:
            globally_linked_ids.add(str(m.transaction_id))

    # Compute previous month string for cross-month linking
    y, m = int(month_str[:4]), int(month_str[5:7])
    if m == 1:
        prev_month_str = f'{y - 1}-12'
    else:
        prev_month_str = f'{y}-{m - 1:02d}'

    # Three separate pools:
    # 1. Checking transactions: month_str = target month (bank transactions in Feb)
    # 2. CC transactions: invoice_month = target month (credit card bill for Feb)
    # 3. Prior month: checking/manual from previous month (for cross-month linking)
    from django.db.models import Q
    qs = Transaction.objects.filter(
        Q(month_str=month_str, account__account_type='checking') |
        Q(month_str=month_str, account__account_type='manual') |
        Q(invoice_month=month_str, account__account_type='credit_card'),
        profile=profile,
    ).select_related('account', 'category').order_by('-date').distinct()

    prior_qs = Transaction.objects.filter(
        Q(month_str=prev_month_str, account__account_type='checking') |
        Q(month_str=prev_month_str, account__account_type='manual'),
        profile=profile,
    ).select_related('account', 'category').order_by('-date').distinct()

    # Build set of transactions already cross-month-moved to ANY mapping.
    # We need to check mappings from OTHER months that pulled transactions
    # from the current month (e.g., January's mapping pulling a December txn).
    # Also check if the current month's mappings pulled from the prior month.
    cross_month_moved_ids = set()
    cross_month_target = {}  # txn_id -> target month_str

    # Compute next month for forward cross-month detection
    if m == 12:
        next_month_str = f'{y + 1}-01'
    else:
        next_month_str = f'{y}-{m + 1:02d}'

    # Check all mappings that have cross-month transactions (current, next, and prev months)
    for cm in RecurringMapping.objects.filter(
        month_str__in=[month_str, next_month_str, prev_month_str],
        profile=profile,
    ).prefetch_related('cross_month_transactions'):
        for t in cm.cross_month_transactions.all():
            cross_month_moved_ids.add(str(t.id))
            cross_month_target[str(t.id)] = cm.month_str

    def _build_candidate(txn, source_pool):
        """Build a candidate dict from a transaction."""
        txn_id_str = str(txn.id)
        amt = float(abs(txn.amount))

        # Relevance score: closer to expected amount = higher
        if expected > 0:
            diff_pct = abs(amt - expected) / expected
        else:
            diff_pct = 1.0

        # Determine source type
        acct_type = txn.account.account_type if txn.account else 'checking'
        source = 'credit_card' if acct_type == 'credit_card' else 'checking'

        # For CC transactions, use invoice_month for display date context
        display_date = txn.date.strftime('%Y-%m-%d')
        if source == 'credit_card' and txn.invoice_month:
            display_date = f'{txn.invoice_month}-01'

        # Override source for prior month pool
        if source_pool == 'prior_month':
            source = 'prior_month'

        return {
            'id': txn_id_str,
            'date': display_date,
            'purchase_date': txn.date.strftime('%Y-%m-%d') if source == 'credit_card' else None,
            'description': txn.description,
            'amount': float(txn.amount),
            'account': txn.account.name if txn.account else '',
            'category': txn.category.name if txn.category else 'Não categorizado',
            'source': source,
            'is_installment': txn.is_installment,
            'installment_info': txn.installment_info or '',
            'is_linked': txn_id_str in linked_ids,
            'is_globally_linked': txn_id_str in globally_linked_ids and txn_id_str not in linked_ids,
            'is_cross_month': source_pool == 'prior_month',
            'cross_month_moved': txn_id_str in cross_month_moved_ids and txn_id_str not in linked_ids,
            'cross_month_target': cross_month_target.get(txn_id_str, None),
            '_diff_pct': diff_pct,
        }

    # Build candidates list
    results = []
    seen_ids = set()

    for txn in qs:
        txn_id_str = str(txn.id)
        if txn_id_str in seen_ids:
            continue
        seen_ids.add(txn_id_str)
        results.append(_build_candidate(txn, 'current'))

    for txn in prior_qs:
        txn_id_str = str(txn.id)
        if txn_id_str in seen_ids:
            continue
        seen_ids.add(txn_id_str)
        results.append(_build_candidate(txn, 'prior_month'))

    # Sort: best amount matches first, then by date
    results.sort(key=lambda r: (r['_diff_pct'], r['date']))

    # Remove internal sort key
    for r in results:
        del r['_diff_pct']

    # Count by source
    checking_count = sum(1 for r in results if r['source'] == 'checking')
    cc_count = sum(1 for r in results if r['source'] == 'credit_card')
    prior_count = sum(1 for r in results if r['source'] == 'prior_month')

    return {
        'month_str': month_str,
        'prev_month_str': prev_month_str,
        'category_id': str(cat.id) if cat else None,
        'category_name': cat_name,
        'expected': expected,
        'candidates': results,
        'total': len(results),
        'checking_count': checking_count,
        'cc_count': cc_count,
        'prior_count': prior_count,
    }


def map_transaction_to_category(transaction_id, category_id=None, mapping_id=None, profile=None):
    """
    Map a transaction to a recurring category or custom mapping.
    Updates the transaction's category FK and marks it as manually categorized.
    Adds the transaction to the mapping's M2M transactions set.
    Sets match_mode to 'manual' and recomputes actual_amount from all linked txns.

    Accepts either category_id (for category-based items) or mapping_id
    (for custom items without a category).
    """
    txn = Transaction.objects.select_related('account').get(id=transaction_id, profile=profile)

    def _update_mapping(mapping):
        """Add transaction to M2M set and recompute actual.
        If the transaction is from a different month, also track in cross_month_transactions."""
        mapping.transactions.add(txn)
        # Track cross-month link if transaction is from a different month
        if txn.month_str != mapping.month_str:
            mapping.cross_month_transactions.add(txn)
        # Also keep legacy FK pointing to first linked txn
        mapping.transaction = txn
        mapping.match_mode = 'manual'
        # Recompute actual from all linked transactions (abs for expenses, raw for income)
        cat_type = mapping.custom_type if mapping.is_custom else (
            mapping.template.template_type if mapping.template else ''
        )
        if cat_type == 'Income':
            total = sum(t.amount for t in mapping.transactions.all())
        else:
            total = sum(abs(t.amount) for t in mapping.transactions.all())
        mapping.actual_amount = total
        mapping.status = 'mapped'
        mapping.save()

    if mapping_id:
        mapping = RecurringMapping.objects.select_related('template', 'category').get(id=mapping_id, profile=profile)
        if mapping.category:
            txn.category = mapping.category
        txn.is_manually_categorized = True
        txn.save()
        _update_mapping(mapping)
        cat_name = mapping.custom_name if mapping.is_custom else (
            mapping.template.name if mapping.template else '?'
        )
        return {
            'transaction_id': str(txn.id),
            'mapping_id': str(mapping.id),
            'category_name': cat_name,
            'description': txn.description,
            'amount': float(txn.amount),
        }
    elif category_id:
        cat = Category.objects.get(id=category_id, profile=profile)
        txn.category = cat
        txn.is_manually_categorized = True
        txn.save()
        try:
            mapping = RecurringMapping.objects.get(
                category=cat,
                month_str=txn.month_str,
                profile=profile,
            )
            _update_mapping(mapping)
        except RecurringMapping.DoesNotExist:
            pass
        return {
            'transaction_id': str(txn.id),
            'category_id': str(cat.id),
            'category_name': cat.name,
            'description': txn.description,
            'amount': float(txn.amount),
        }
    else:
        raise ValueError('Either category_id or mapping_id must be provided')


def unmap_transaction(transaction_id, mapping_id=None, profile=None):
    """
    Remove a transaction from a recurring mapping's linked set.
    If mapping_id is given, remove from that specific mapping.
    Otherwise, find by category + month (legacy behavior).
    Resets transaction category to 'Não categorizado'.
    """
    txn = Transaction.objects.get(id=transaction_id, profile=profile)
    old_category = txn.category
    old_month = txn.month_str

    # Find or get the "Não categorizado" category
    uncat = Category.objects.filter(name='Não categorizado', profile=profile).first()
    txn.category = uncat
    txn.is_manually_categorized = False
    txn.save()

    # Find the mapping to unlink from
    mapping = None
    if mapping_id:
        try:
            mapping = RecurringMapping.objects.get(id=mapping_id, profile=profile)
        except RecurringMapping.DoesNotExist:
            pass
    elif old_category:
        try:
            mapping = RecurringMapping.objects.get(
                category=old_category,
                month_str=old_month,
                profile=profile,
            )
        except RecurringMapping.DoesNotExist:
            pass

    if mapping:
        # Remove from M2M
        mapping.transactions.remove(txn)
        # Also remove from cross-month tracking if present
        mapping.cross_month_transactions.remove(txn)
        # Clear legacy FK if it was this txn
        if mapping.transaction_id == txn.id:
            # Set FK to another linked txn if any, else None
            remaining = mapping.transactions.first()
            mapping.transaction = remaining

        remaining_count = mapping.transactions.count()
        if remaining_count > 0:
            # Recompute actual from remaining linked transactions (abs for expenses, raw for income)
            cat_type = mapping.custom_type if mapping.is_custom else (
                mapping.template.template_type if mapping.template else ''
            )
            if cat_type == 'Income':
                total = sum(t.amount for t in mapping.transactions.all())
            else:
                total = sum(abs(t.amount) for t in mapping.transactions.all())
            mapping.actual_amount = total
            mapping.status = 'mapped'
        else:
            mapping.actual_amount = None
            mapping.status = 'missing'
        mapping.save()

    return {
        'transaction_id': str(txn.id),
        'unmapped': True,
    }


# ---------------------------------------------------------------------------
# Variable transactions
# ---------------------------------------------------------------------------

def get_variable_transactions(month_str, profile=None):
    """
    Variable transactions for the VARIÁVEIS tab.
    Returns all variable-type expense transactions for a month.
    Excludes internal transfers (CC bill payments, etc.)
    """
    qs = Transaction.objects.filter(
        month_str=month_str,
        amount__lt=0,
        category__category_type='Variavel',
        is_internal_transfer=False,
        profile=profile,
    ).select_related('account', 'category').order_by('-date')

    results = []
    for txn in qs:
        results.append({
            'id': str(txn.id),
            'date': txn.date.strftime('%Y-%m-%d'),
            'description': txn.description,
            'amount': float(txn.amount),
            'category': txn.category.name if txn.category else 'Não categorizado',
            'account': txn.account.name,
        })

    return {
        'month_str': month_str,
        'transactions': results,
        'count': len(results),
        'total': float(sum(r['amount'] for r in results)),
    }


# ---------------------------------------------------------------------------
# B1: Projection service
# ---------------------------------------------------------------------------

def _parse_month(month_str):
    """Parse 'YYYY-MM' to a date object (first day of month)."""
    if not month_str:
        raise ValueError("month_str cannot be empty")
    return datetime.strptime(month_str, '%Y-%m').date()


def _month_str_add(month_str, months):
    """Add N months to a month_str and return new month_str."""
    dt = _parse_month(month_str)
    dt += relativedelta(months=months)
    return dt.strftime('%Y-%m')


def _compute_installment_schedule(target_month_str, num_future_months=6, profile=None):
    """
    Compute installment totals for target_month and future months.

    Uses invoice_month to identify CC statements. For each month:
    - If a CC statement (invoice) exists for that month, compute the deduped
      installment total (lowest position per purchase only).
    - If no statement exists, project from older statements.

    CC statements may list all future positions for a purchase (01/03, 02/03,
    03/03). Only the lowest position per purchase is the actual charge for
    that bill — we deduplicate before summing.

    Returns: dict { month_str: total_installment_amount }
    """
    schedule = {}  # month_str -> total amount

    # Pre-compute all month strings we'll need
    target_months = [_month_str_add(target_month_str, i) for i in range(num_future_months + 1)]
    lookback_months = [_month_str_add(target_month_str, -i) for i in range(1, 13)]
    all_months = set(target_months + lookback_months)

    # Batch fetch ALL installment transactions across all relevant months (2 queries total)
    # Query 1: invoice_month-based
    invoice_txns = list(Transaction.objects.filter(
        invoice_month__in=all_months,
        is_installment=True,
        amount__lt=0,
        profile=profile,
    ).select_related('account'))

    # Group by invoice_month
    txns_by_invoice_month = {}
    for txn in invoice_txns:
        txns_by_invoice_month.setdefault(txn.invoice_month, []).append(txn)

    # Query 2: month_str fallback for months without invoice_month data
    months_with_invoice = set(txns_by_invoice_month.keys())
    months_needing_fallback = all_months - months_with_invoice
    if months_needing_fallback:
        fallback_txns = list(Transaction.objects.filter(
            month_str__in=months_needing_fallback,
            invoice_month='',
            is_installment=True,
            amount__lt=0,
            profile=profile,
        ).select_related('account'))
        txns_by_fallback_month = {}
        for txn in fallback_txns:
            txns_by_fallback_month.setdefault(txn.month_str, []).append(txn)
    else:
        txns_by_fallback_month = {}

    def _get_txns_for_month(month):
        """Get installment transactions for a month (invoice_month preferred)."""
        return txns_by_invoice_month.get(month) or txns_by_fallback_month.get(month) or []

    def _parse_installment(txn):
        """Parse installment info from a transaction."""
        info = txn.installment_info or ''
        m_match = re.match(r'(\d+)/(\d+)', info)
        if not m_match:
            dm = re.search(r'(\d{1,2})/(\d{1,2})', txn.description)
            if dm:
                m_match = dm
        return m_match

    # Step 1: Check which target months have real CC statement data
    months_with_real_data = set()
    for check_month in target_months:
        inst_txns = _get_txns_for_month(check_month)
        if not inst_txns:
            continue

        purchase_groups = {}
        non_parseable_total = 0.0
        for txn in inst_txns:
            m_match = _parse_installment(txn)
            if not m_match:
                non_parseable_total += float(abs(txn.amount))
                continue

            current = int(m_match.group(1))
            total_inst = int(m_match.group(2))
            base_desc = re.sub(r'\s*\d{1,2}/\d{1,2}\s*$', '', txn.description).strip()
            acct = txn.account.name if txn.account else ''
            amt = round(float(abs(txn.amount)), 2)

            group_key = (base_desc, acct, amt, total_inst)
            if group_key not in purchase_groups or current < purchase_groups[group_key]:
                purchase_groups[group_key] = current

        deduped_total = sum(amt for (_, _, amt, _) in purchase_groups.keys())
        real_total = deduped_total + non_parseable_total
        if real_total > 0:
            schedule[check_month] = real_total
            months_with_real_data.add(check_month)

    # Step 2: Project for months WITHOUT real data from older statements.
    seen_per_month = {}

    for lookback in range(1, 13):
        source_month = lookback_months[lookback - 1]
        inst_txns = _get_txns_for_month(source_month)
        if not inst_txns:
            continue

        purchase_groups = {}
        for txn in inst_txns:
            m_match = _parse_installment(txn)
            if not m_match:
                continue

            current = int(m_match.group(1))
            total_inst = int(m_match.group(2))
            amt = round(float(abs(txn.amount)), 2)
            base_desc = re.sub(r'\s*\d{1,2}/\d{1,2}\s*$', '', txn.description).strip()
            acct = txn.account.name if txn.account else ''

            group_key = (base_desc, acct, amt, total_inst)
            if group_key not in purchase_groups or current < purchase_groups[group_key]:
                purchase_groups[group_key] = current

        for (base_desc, acct, amt, total_inst), current in purchase_groups.items():
            purchase_id = (base_desc, acct, amt, total_inst)

            for target_offset in range(num_future_months + 1):
                check_month = target_months[target_offset]
                if check_month in months_with_real_data:
                    continue
                delta = lookback + target_offset
                position = current + delta
                if position <= total_inst:
                    if check_month not in seen_per_month:
                        seen_per_month[check_month] = set()
                    if purchase_id in seen_per_month[check_month]:
                        continue
                    seen_per_month[check_month].add(purchase_id)
                    schedule[check_month] = schedule.get(check_month, 0) + amt

    return {m: round(v, 2) for m, v in schedule.items()}


def get_last_installment_month(profile=None):
    """
    Return the furthest future month_str that still has a projected installment.

    Groups installments by purchase per source month, using only the lowest
    position (the current charge), then computes how many months forward that
    purchase extends.  Returns the max projected month across all purchases.
    Returns None if no installments exist.
    """
    inst_txns = Transaction.objects.filter(
        is_installment=True,
        amount__lt=0,
        profile=profile,
    ).select_related('account').values_list(
        'invoice_month', 'month_str', 'installment_info', 'description', 'amount', 'account__name'
    )

    # Group by (source_month, base_desc, acct, amt, total) → lowest position
    # Prefer invoice_month; fall back to month_str for older imports without it
    purchase_groups = {}  # (source_month, base_desc, acct, amt, total) -> lowest_current
    for inv_month, txn_month, inst_info, desc, amount, acct_name in inst_txns:
        month_str = inv_month if inv_month else txn_month
        if not month_str:
            continue
        info = inst_info or ''
        m = re.match(r'(\d+)/(\d+)', info)
        if not m:
            dm = re.search(r'(\d{1,2})/(\d{1,2})', desc)
            if dm:
                m = dm
        if not m:
            continue

        current = int(m.group(1))
        total = int(m.group(2))
        base_desc = re.sub(r'\s*\d{1,2}/\d{1,2}\s*$', '', desc).strip()
        acct = acct_name or ''
        amt = round(float(abs(amount)), 2)

        key = (month_str, base_desc, acct, amt, total)
        if key not in purchase_groups or current < purchase_groups[key]:
            purchase_groups[key] = current

    furthest = None
    for (month_str, base_desc, acct, amt, total), current in purchase_groups.items():
        remaining = total - current
        if remaining > 0:
            end_month = _month_str_add(month_str, remaining)
            if furthest is None or end_month > furthest:
                furthest = end_month

    return furthest


def get_projection(start_month_str, num_months=6, profile=None):
    """
    PROJEÇÃO — Forward-looking financial projection.

    Starting from the balance override of start_month_str, projects
    income, fixed expenses, installments, and variable budget for
    each of the next num_months months.

    For the current month: uses actual RecurringMapping expected amounts.
    For future months: uses RecurringTemplate defaults / BudgetConfig overrides.
    Installments: parses "N/M" info to calculate remaining months.

    Returns per-month: income, fixo, installments, variable_budget,
    net, cumulative balance.
    """
    import re

    # Starting balance
    try:
        bo = BalanceOverride.objects.get(month_str=start_month_str, profile=profile)
        starting_balance = float(bo.balance)
    except BalanceOverride.DoesNotExist:
        starting_balance = 0.0

    # Template defaults for recurring items
    tpls = RecurringTemplate.objects.filter(is_active=True, profile=profile)
    income_tpls = tpls.filter(template_type='Income')
    fixo_tpls = tpls.filter(template_type='Fixo')
    invest_tpls = tpls.filter(template_type='Investimento')

    total_income_default = float(
        income_tpls.aggregate(t=Sum('default_limit'))['t'] or 0
    )
    total_fixo_default = float(
        fixo_tpls.aggregate(t=Sum('default_limit'))['t'] or 0
    )
    total_invest_default = float(
        invest_tpls.aggregate(t=Sum('default_limit'))['t'] or 0
    )
    # Variable budget comes from taxonomy Category (not templates)
    variable_cats = Category.objects.filter(
        category_type='Variavel', is_active=True, default_limit__gt=0,
        profile=profile,
    )
    total_variable_default = float(
        variable_cats.aggregate(t=Sum('default_limit'))['t'] or 0
    )

    # Active installments — compute from all recent CC statements
    installment_schedule = _compute_installment_schedule(
        start_month_str, num_future_months=num_months, profile=profile,
    )
    current_installment_total = installment_schedule.get(start_month_str, 0)

    # Build projection rows
    rows = []
    cumulative = starting_balance

    for i in range(num_months):
        month = _month_str_add(start_month_str, i)

        if i == 0:
            # Current month: use actual RecurringMapping data
            mappings = RecurringMapping.objects.filter(
                month_str=month,
                profile=profile,
            ).exclude(status='skipped').select_related('template')

            income = 0.0
            fixo = 0.0
            invest = 0.0
            for mp in mappings:
                cat_type = mp.custom_type if mp.is_custom else (
                    mp.template.template_type if mp.template else ''
                )
                expected = float(mp.expected_amount)
                if cat_type == 'Income':
                    income += expected
                elif cat_type == 'Fixo':
                    fixo += expected
                elif cat_type == 'Investimento':
                    invest += expected

            installments = current_installment_total
            variable = total_variable_default
        else:
            # Future months: use defaults + BudgetConfig overrides
            income = total_income_default
            fixo = total_fixo_default
            invest = total_invest_default
            installments = installment_schedule.get(month, 0)
            variable = total_variable_default

        net = income - fixo - invest - installments - variable
        cumulative += net

        rows.append({
            'month': month,
            'income': round(income, 2),
            'fixo': round(fixo, 2),
            'investimento': round(invest, 2),
            'installments': round(installments, 2),
            'variable': round(variable, 2),
            'net': round(net, 2),
            'cumulative': round(cumulative, 2),
        })

    return {
        'start_month': start_month_str,
        'starting_balance': starting_balance,
        'months': rows,
        'num_months': num_months,
    }


# ---------------------------------------------------------------------------
# B2: Variable budget (Orçamento) service
# ---------------------------------------------------------------------------

def get_orcamento(month_str, profile=None):
    """
    ORÇAMENTO — Variable spending budget tracking per category.

    For each variable category with a limit:
    - Current month spending from transactions
    - 6-month historical average
    - Remaining budget and percentage used
    - Status: ok / warning (>80%) / over (>100%)

    Returns per-category budget data + totals.
    """
    variable_cats = Category.objects.filter(
        is_active=True,
        category_type='Variavel',
        default_limit__gt=0,
        profile=profile,
    ).order_by('display_order', 'name')

    cat_ids = [c.id for c in variable_cats]

    # 6-month lookback for averages
    lookback_months = []
    for i in range(1, 7):
        lookback_months.append(_month_str_add(month_str, -i))

    # Batch: BudgetConfig overrides for this month (1 query)
    budget_overrides = {
        bc.category_id: float(bc.limit_override)
        for bc in BudgetConfig.objects.filter(
            category_id__in=cat_ids, month_str=month_str, profile=profile,
        )
    }

    # Batch: current month spending per category (1 query)
    current_spending = dict(
        Transaction.objects.filter(
            month_str=month_str,
            category_id__in=cat_ids,
            amount__lt=0,
            is_internal_transfer=False,
            profile=profile,
        ).values('category_id').annotate(
            total=Sum('amount')
        ).values_list('category_id', 'total')
    )

    # Batch: 6-month lookback spending per category (1 query)
    lookback_spending = dict(
        Transaction.objects.filter(
            month_str__in=lookback_months,
            category_id__in=cat_ids,
            amount__lt=0,
            is_internal_transfer=False,
            profile=profile,
        ).values('category_id').annotate(
            total=Sum('amount')
        ).values_list('category_id', 'total')
    )

    # Batch: months with data per category in lookback (1 query)
    from django.db.models import Count
    lookback_month_counts = dict(
        Transaction.objects.filter(
            month_str__in=lookback_months,
            category_id__in=cat_ids,
            amount__lt=0,
            is_internal_transfer=False,
            profile=profile,
        ).values('category_id').annotate(
            month_count=Count('month_str', distinct=True)
        ).values_list('category_id', 'month_count')
    )

    categories = []
    total_limit = 0.0
    total_spent = 0.0

    for cat in variable_cats:
        limit = budget_overrides.get(cat.id, float(cat.default_limit))

        spent_agg = current_spending.get(cat.id, Decimal('0.00'))
        spent = float(abs(spent_agg))

        avg_total = float(abs(lookback_spending.get(cat.id, Decimal('0.00'))))
        months_with_data = lookback_month_counts.get(cat.id, 0)
        avg_6m = avg_total / max(months_with_data, 1)

        remaining = max(0, limit - spent)
        pct = (spent / limit * 100) if limit > 0 else 0

        if pct > 100:
            status = 'over'
        elif pct > 80:
            status = 'warning'
        else:
            status = 'ok'

        total_limit += limit
        total_spent += spent

        categories.append({
            'id': str(cat.id),
            'name': cat.name,
            'limit': round(limit, 2),
            'spent': round(spent, 2),
            'remaining': round(remaining, 2),
            'pct': round(pct, 1),
            'avg_6m': round(avg_6m, 2),
            'status': status,
        })

    total_pct = (total_spent / total_limit * 100) if total_limit > 0 else 0

    return {
        'month_str': month_str,
        'categories': categories,
        'total_limit': round(total_limit, 2),
        'total_spent': round(total_spent, 2),
        'total_remaining': round(max(0, total_limit - total_spent), 2),
        'total_pct': round(total_pct, 1),
    }


# ---------------------------------------------------------------------------
# Smart Categorization — learning from past manually-categorized transactions
# ---------------------------------------------------------------------------

def _normalize_description(desc):
    """
    Normalize a description for matching purposes.
    Removes numbers, dates, IDs, and normalizes whitespace.
    """
    if not desc:
        return ''
    d = desc.upper().strip()
    # Remove trailing date patterns like "12/01", "05 02"
    d = re.sub(r'\d{2}/\d{2}$', '', d)
    d = re.sub(r'\d{2}\s+\d{2}$', '', d)
    # Remove long numeric sequences (IDs, card numbers)
    d = re.sub(r'\d{6,}', '', d)
    # Remove installment patterns
    d = re.sub(r'\d{1,2}/\d{1,2}', '', d)
    # Collapse whitespace
    d = re.sub(r'\s+', ' ', d).strip()
    return d


def _extract_tokens(desc):
    """Extract meaningful tokens from a description."""
    normalized = _normalize_description(desc)
    # Split on non-alpha
    tokens = re.findall(r'[A-ZÁÀÃÂÉÊÍÓÔÕÚÇ]+', normalized)
    # Filter out very short tokens and common stop words
    stop_words = {'DE', 'DO', 'DA', 'DOS', 'DAS', 'EM', 'NO', 'NA',
                  'COM', 'POR', 'PARA', 'UMA', 'UM', 'OS', 'AS',
                  'PIX', 'TED', 'DOC', 'PAG', 'INT'}
    return [t for t in tokens if len(t) >= 3 and t not in stop_words]


def smart_categorize(month_str=None, dry_run=False, profile=None):
    """
    Self-improving categorization engine with 5-strategy priority chain.

    Every categorized transaction (manual OR rule-based) is training data.
    Each strategy has a confidence score. Confidence tiers:
    - ≥0.85: auto-categorize silently
    - 0.70–0.84: auto-categorize but flag as "auto" for review
    - <0.70: leave uncategorized

    Strategy chain (priority order):
    1. Keyword Rules (1.0) — CategorizationRule table
    2. Exact Description Match (0.95) — normalized description → most common category
    3. Amount + Account Pattern (0.85) — recurring subscription detection
    4. Token Similarity (0.70) — weighted token scoring
    5. Leave uncategorized

    Also runs inconsistency detection in parallel.

    Args:
        month_str: Optional month to limit scope. If None, processes all months.
        dry_run: If True, returns what would be changed without saving.

    Returns:
        dict with categorized count, strategy breakdown, inconsistencies, and details.
    """
    nao_cat = Category.objects.filter(name='Não categorizado', profile=profile).first()
    if not nao_cat:
        return {'categorized': 0, 'details': [], 'error': 'No uncategorized category found'}

    # ── Get uncategorized transactions ──
    # When filtering by month, include both month_str matches AND
    # credit card transactions whose invoice_month matches (they appear
    # in that month's card view even though month_str is the billing cycle).
    qs = Transaction.objects.filter(
        category=nao_cat,
        is_internal_transfer=False,
        profile=profile,
    ).select_related('account', 'category')
    if month_str:
        from django.db.models import Q
        qs = qs.filter(
            Q(month_str=month_str) | Q(invoice_month=month_str)
        )

    uncategorized = list(qs)
    if not uncategorized:
        return {
            'categorized': 0, 'total_uncategorized': 0,
            'by_strategy': {}, 'inconsistencies': [],
            'details': [], 'dry_run': dry_run,
            'message': 'No uncategorized transactions',
        }

    # ── Category type guard ──
    # Learning strategies (2-4) must NEVER assign Fixo/Income/Investimento categories.
    # Those are managed exclusively by RecurringMapping. Only Variavel + Contas are
    # valid targets for auto-categorization via learning.
    variable_cat_ids = set(
        Category.objects.filter(
            category_type='Variavel', is_active=True,
            profile=profile,
        ).values_list('id', flat=True)
    )
    # Also include "Contas" (special catch-all for bank fees/charges)
    contas_cat = Category.objects.filter(name='Contas', is_active=True, profile=profile).first()
    if contas_cat:
        variable_cat_ids.add(contas_cat.id)

    # ── Build learning corpus from categorized transactions (Variavel only) ──
    # We only learn from Variavel categories to prevent Fixo/Income pollution.
    all_categorized = Transaction.objects.filter(
        is_internal_transfer=False,
        category_id__in=variable_cat_ids,
        profile=profile,
    ).select_related('category', 'subcategory', 'account')

    # Manual categorizations get 3x weight (higher trust)
    MANUAL_WEIGHT = 3

    # Description → category frequency map (normalized)
    desc_to_category = {}  # normalized_desc → Counter({category_id: weighted_count})
    # Description → subcategory frequency map
    desc_to_subcategory = {}  # normalized_desc → Counter({subcategory_id: weighted_count})
    for txn in all_categorized.iterator():
        norm = _normalize_description(txn.description)
        if not norm:
            continue
        if norm not in desc_to_category:
            desc_to_category[norm] = Counter()
        weight = MANUAL_WEIGHT if txn.is_manually_categorized else 1
        desc_to_category[norm][txn.category_id] += weight
        # Track subcategory if present
        if txn.subcategory_id:
            if norm not in desc_to_subcategory:
                desc_to_subcategory[norm] = Counter()
            desc_to_subcategory[norm][txn.subcategory_id] += weight

    # Token → category frequency map
    token_to_category = {}  # token → Counter({category_id: count})
    for txn in all_categorized.iterator():
        tokens = _extract_tokens(txn.description)
        weight = MANUAL_WEIGHT if txn.is_manually_categorized else 1
        for token in tokens:
            if token not in token_to_category:
                token_to_category[token] = Counter()
            token_to_category[token][txn.category_id] += weight

    # Amount + account pattern map for subscription detection
    # Key: (account_id, rounded_amount) → Counter({category_id: count})
    amt_account_map = {}
    # Amount → subcategory map
    amt_account_sub_map = {}
    for txn in all_categorized.iterator():
        key = (txn.account_id, round(float(txn.amount), 0))
        if key not in amt_account_map:
            amt_account_map[key] = Counter()
        amt_account_map[key][txn.category_id] += 1
        if txn.subcategory_id:
            if key not in amt_account_sub_map:
                amt_account_sub_map[key] = Counter()
            amt_account_sub_map[key][txn.subcategory_id] += 1

    # ── Load active categorization rules (ordered by priority) ──
    rules = list(CategorizationRule.objects.filter(
        is_active=True,
        profile=profile,
    ).select_related('category', 'subcategory').order_by('-priority'))

    # Category lookup — includes ALL active categories (rules can still assign Fixo)
    cat_lookup = {c.id: c for c in Category.objects.filter(is_active=True, profile=profile)}
    # Subcategory lookup — also track which subcategory belongs to which category
    from api.models import Subcategory
    sub_lookup = {s.id: s for s in Subcategory.objects.filter(profile=profile).select_related('category')}
    # Valid subcategory IDs per category: sub must belong to the same category
    sub_to_cat = {s.id: s.category_id for s in sub_lookup.values()}

    # ── Process each uncategorized transaction ──
    results = []
    by_strategy = Counter()

    # PIX / personal transfer pattern: short descriptions like "Rafaell04 02",
    # "Guilher20 01", "Renato 28 01" — person name + date digits on checking accounts.
    # These should only be categorized via explicit keyword rules, never by learning.
    import re
    _pix_pattern = re.compile(r'^[A-Za-z]{3,}\d{2}\s*\d{2}$')  # e.g. "Rafaell04 02"
    _pix_pattern2 = re.compile(r'^[A-Za-z]+\s+[A-Za-z]?\d{2}\s+\d{2}$')  # e.g. "Renato 28 01"

    def _is_pix_transfer(txn_obj):
        """Detect PIX/personal transfers that should not be auto-categorized by learning."""
        if txn_obj.account and txn_obj.account.account_type != 'checking':
            return False
        desc = txn_obj.description.strip()
        if _pix_pattern.match(desc) or _pix_pattern2.match(desc):
            return True
        # Also match "Pix Qrs ..." descriptions that aren't already rule-matched
        if desc.upper().startswith('PIX QRS') or desc.upper().startswith('PIX '):
            return True
        return False

    for txn in uncategorized:
        desc_upper = txn.description.upper()
        matched_category = None
        matched_subcategory = None
        match_method = None
        confidence = 0.0

        # Check if this is a PIX/personal transfer (skip learning strategies)
        is_pix = _is_pix_transfer(txn)

        # ── Strategy 1: Keyword Rules (confidence: 1.0) ──
        # Rules always apply, even for PIX transfers (user creates explicit rules)
        for rule in rules:
            if rule.keyword.upper() in desc_upper:
                matched_category = rule.category
                matched_subcategory = rule.subcategory
                match_method = 'rule'
                confidence = 1.0
                break

        # ── Strategy 2: Exact Description Match (confidence: 0.95) ──
        # NOTE: Learning corpus only contains Variavel categories, so
        # Fixo/Income/Investimento can never be assigned here.
        # Skip for PIX transfers — they need manual categorization.
        if not matched_category and not is_pix:
            norm = _normalize_description(txn.description)
            if norm and norm in desc_to_category:
                cat_counts = desc_to_category[norm]
                if cat_counts:
                    best_cat_id, best_count = cat_counts.most_common(1)[0]
                    total_count = sum(cat_counts.values())
                    # Require majority agreement (>50% of weighted votes)
                    if best_cat_id in cat_lookup and best_count > total_count * 0.5:
                        matched_category = cat_lookup[best_cat_id]
                        match_method = 'exact_match'
                        confidence = 0.95
                        # Propagate subcategory — only if it belongs to the matched category
                        if norm in desc_to_subcategory:
                            sub_counts = desc_to_subcategory[norm]
                            best_sub_id = sub_counts.most_common(1)[0][0]
                            if best_sub_id in sub_lookup and sub_to_cat.get(best_sub_id) == best_cat_id:
                                matched_subcategory = sub_lookup[best_sub_id]

        # ── Strategy 3: Amount + Account Pattern (confidence: 0.85) ──
        # Skip for PIX transfers
        if not matched_category and not is_pix:
            rounded_amt = round(float(txn.amount), 0)
            # Check exact amount match on same account
            key = (txn.account_id, rounded_amt)
            if key in amt_account_map:
                cat_counts = amt_account_map[key]
                if cat_counts:
                    best_cat_id, best_count = cat_counts.most_common(1)[0]
                    # Require at least 3 historical matches for this pattern
                    if best_count >= 3 and best_cat_id in cat_lookup:
                        matched_category = cat_lookup[best_cat_id]
                        match_method = 'amount_pattern'
                        confidence = 0.85
                        # Propagate subcategory — validate category ownership
                        if key in amt_account_sub_map:
                            sub_counts = amt_account_sub_map[key]
                            best_sub_id = sub_counts.most_common(1)[0][0]
                            if best_sub_id in sub_lookup and sub_to_cat.get(best_sub_id) == best_cat_id:
                                matched_subcategory = sub_lookup[best_sub_id]

            # Also check ±5% amount tolerance on same account
            if not matched_category:
                for delta in range(-2, 3):  # Check nearby rounded amounts
                    check_key = (txn.account_id, rounded_amt + delta)
                    if check_key in amt_account_map:
                        cat_counts = amt_account_map[check_key]
                        if cat_counts:
                            best_cat_id, best_count = cat_counts.most_common(1)[0]
                            if best_count >= 3 and best_cat_id in cat_lookup:
                                matched_category = cat_lookup[best_cat_id]
                                match_method = 'amount_pattern'
                                confidence = 0.80
                                # Propagate subcategory — validate category ownership
                                if check_key in amt_account_sub_map:
                                    sub_counts = amt_account_sub_map[check_key]
                                    best_sub_id = sub_counts.most_common(1)[0][0]
                                    if best_sub_id in sub_lookup and sub_to_cat.get(best_sub_id) == best_cat_id:
                                        matched_subcategory = sub_lookup[best_sub_id]
                                break

        # ── Strategy 4: Token Similarity (confidence: 0.70) ──
        # Skip for PIX transfers
        if not matched_category and not is_pix:
            tokens = _extract_tokens(txn.description)
            if tokens:
                cat_scores = Counter()
                for token in tokens:
                    if token in token_to_category:
                        for cat_id, count in token_to_category[token].items():
                            if cat_id in cat_lookup:
                                cat_scores[cat_id] += count

                if cat_scores:
                    best_cat_id, best_score = cat_scores.most_common(1)[0]
                    matching_tokens = sum(1 for t in tokens if t in token_to_category)
                    total_tokens = len(tokens)
                    # Require at least 2 matching tokens or strong single token
                    if matching_tokens >= 2 or best_score >= 5:
                        # Check that best score is dominant (>60% of total)
                        total_score = sum(cat_scores.values())
                        if best_score > total_score * 0.6:
                            matched_category = cat_lookup[best_cat_id]
                            match_method = 'token_similarity'
                            confidence = min(0.75, 0.5 + matching_tokens * 0.05)

        # ── Record result ──
        if matched_category and confidence >= 0.70:
            results.append({
                'transaction_id': str(txn.id),
                'description': txn.description,
                'amount': float(txn.amount),
                'account': txn.account.name if txn.account else '',
                'month_str': txn.month_str,
                'new_category': matched_category.name,
                'new_category_id': str(matched_category.id),
                'new_subcategory': matched_subcategory.name if matched_subcategory else None,
                'method': match_method,
                'confidence': round(confidence, 2),
            })
            by_strategy[match_method] += 1

            if not dry_run:
                txn.category = matched_category
                if matched_subcategory:
                    txn.subcategory = matched_subcategory
                txn.save(update_fields=['category', 'subcategory', 'updated_at'])

    # ── Inconsistency Detection ──
    inconsistencies = _detect_inconsistencies(nao_cat, profile=profile)

    return {
        'categorized': len(results),
        'total_uncategorized': len(uncategorized),
        'by_strategy': dict(by_strategy),
        'inconsistencies': inconsistencies,
        'details': results[:100],
        'dry_run': dry_run,
    }


def _detect_inconsistencies(nao_cat, profile=None):
    """
    Find descriptions that appear in multiple different categories.
    These indicate categorization conflicts that need manual resolution.
    """
    from django.db.models import Count

    # Get all non-uncategorized, non-transfer transactions
    txns = Transaction.objects.filter(
        is_internal_transfer=False,
        profile=profile,
    ).exclude(
        category=nao_cat,
    ).exclude(
        category__isnull=True,
    )

    # Group by normalized description and find those with multiple categories
    # We'll do this in Python for flexibility with normalization
    desc_categories = {}  # normalized_desc → {category_name: count}
    for txn in txns.select_related('category').iterator():
        norm = _normalize_description(txn.description)
        if not norm or len(norm) < 3:
            continue
        if norm not in desc_categories:
            desc_categories[norm] = Counter()
        desc_categories[norm][txn.category.name] += 1

    inconsistencies = []
    for desc, cat_counts in desc_categories.items():
        if len(cat_counts) > 1:
            total = sum(cat_counts.values())
            # Only report if significant (at least 5 transactions total)
            if total >= 5:
                inconsistencies.append({
                    'description': desc,
                    'categories': dict(cat_counts),
                    'total': total,
                })

    # Sort by total count descending
    inconsistencies.sort(key=lambda x: x['total'], reverse=True)
    return inconsistencies[:20]


def find_similar_transactions(transaction_id, profile=None):
    """
    Find transactions similar to the given one that are uncategorized.
    Used for learning feedback — when user categorizes one transaction,
    suggest applying the same category to similar ones.

    Returns similar uncategorized transactions + rule suggestion.
    """
    txn = Transaction.objects.select_related('account', 'category').get(id=transaction_id, profile=profile)
    nao_cat = Category.objects.filter(name='Não categorizado', profile=profile).first()
    if not nao_cat or not txn.category or txn.category == nao_cat:
        return {'similar_uncategorized': [], 'suggest_rule': None}

    norm = _normalize_description(txn.description)

    # Find uncategorized transactions with the same normalized description
    similar_qs = Transaction.objects.filter(
        category=nao_cat,
        is_internal_transfer=False,
        profile=profile,
    ).select_related('account')

    similar = []
    for candidate in similar_qs.iterator():
        if _normalize_description(candidate.description) == norm:
            similar.append({
                'id': str(candidate.id),
                'description': candidate.description,
                'amount': float(candidate.amount),
                'month_str': candidate.month_str,
                'account': candidate.account.name if candidate.account else '',
            })

    # Generate rule suggestion
    suggest_rule = None
    tokens = _extract_tokens(txn.description)
    if tokens:
        # Use the longest token as the keyword candidate
        keyword = max(tokens, key=len)
        # Count how many transactions this keyword would match
        would_match = Transaction.objects.filter(
            description__icontains=keyword,
            is_internal_transfer=False,
            profile=profile,
        ).exclude(category=txn.category).count()
        already_correct = Transaction.objects.filter(
            description__icontains=keyword,
            category=txn.category,
            profile=profile,
        ).count()

        if would_match > 0 or already_correct > 1:
            suggest_rule = {
                'keyword': keyword,
                'category_id': str(txn.category.id),
                'category_name': txn.category.name,
                'would_match': would_match,
                'already_correct': already_correct,
            }

    return {
        'similar_uncategorized': similar[:50],
        'suggest_rule': suggest_rule,
    }


def rename_transaction(transaction_id, new_description, propagate_ids=None, profile=None):
    """
    Rename a transaction's description and optionally propagate to similar ones.

    If propagate_ids is None: preview mode — returns similar transactions.
    If propagate_ids is a list: apply mode — renames those + creates RenameRule.

    Similarity: same raw_description/description_original, same account, amount ±15%.
    """
    txn = Transaction.objects.select_related('account').get(id=transaction_id, profile=profile)
    old_description = txn.description
    original_desc = txn.description_original or txn.raw_description or old_description

    # Always rename the target transaction
    txn.description = new_description
    txn.save(update_fields=['description', 'updated_at'])

    if propagate_ids is not None:
        # Apply mode: rename selected transactions + create RenameRule
        if propagate_ids:
            Transaction.objects.filter(
                id__in=propagate_ids,
                profile=profile,
            ).update(description=new_description)

        # Auto-create RenameRule for future imports
        norm_original = _normalize_description(original_desc)
        if norm_original and norm_original != _normalize_description(new_description):
            RenameRule.objects.get_or_create(
                keyword=norm_original,
                profile=profile,
                defaults={'display_name': new_description, 'is_active': True},
            )

        return {
            'renamed': 1 + len(propagate_ids),
            'rename_rule_created': True,
        }

    # Preview mode: find similar transactions
    amt = float(txn.amount)
    amt_low = amt * 1.15 if amt < 0 else amt * 0.85
    amt_high = amt * 0.85 if amt < 0 else amt * 1.15

    similar_qs = Transaction.objects.filter(
        account=txn.account,
        amount__gte=min(amt_low, amt_high),
        amount__lte=max(amt_low, amt_high),
        profile=profile,
    ).exclude(id=txn.id).select_related('account')

    # Filter by original description similarity
    norm_original = _normalize_description(original_desc)
    similar = []
    for candidate in similar_qs.iterator():
        cand_orig = candidate.description_original or candidate.raw_description or candidate.description
        if _normalize_description(cand_orig) == norm_original:
            similar.append({
                'id': str(candidate.id),
                'description': candidate.description,
                'amount': float(candidate.amount),
                'date': str(candidate.date),
                'month_str': candidate.month_str,
                'account': candidate.account.name if candidate.account else '',
            })

    return {
        'renamed': 1,
        'similar': similar[:100],
    }


# ---------------------------------------------------------------------------
# Auto-link recurring items
# ---------------------------------------------------------------------------

def auto_link_recurring(month_str, profile=None):
    """
    Try to automatically link unmatched recurring items to transactions.

    Strategies (in priority order):
    1. Previous month link: If the same recurring item was linked to a
       transaction last month, look for a similar transaction this month
       (same description pattern or same amount).
    2. Name similarity: Match the recurring item name against transaction
       descriptions using fuzzy matching.
    3. Amount match: Find transactions with amounts close to expected
       (within 10% tolerance).

    Only processes 'manual' mode items with status 'missing' (Faltando).
    Does NOT touch items that are already linked or in category mode.

    Returns: dict with linked count and details.
    """
    mappings = RecurringMapping.objects.filter(
        month_str=month_str,
        match_mode='manual',
        profile=profile,
    ).exclude(
        status__in=['skipped', 'mapped'],
    ).select_related('template', 'category', 'transaction').prefetch_related('transactions')

    # Only process items with no linked transactions
    unlinked = [m for m in mappings if m.transactions.count() == 0 and not m.transaction]

    if not unlinked:
        return {'linked': 0, 'details': [], 'message': 'No unlinked items to process'}

    # Get all transactions for this month
    all_txns = Transaction.objects.filter(
        month_str=month_str,
        profile=profile,
    ).select_related('account', 'category')

    income_txns = list(all_txns.filter(amount__gt=0))
    expense_txns = list(all_txns.filter(amount__lt=0))

    # Build set of already-linked transaction IDs (across ALL mappings this month)
    already_linked = set()
    all_mappings = RecurringMapping.objects.filter(month_str=month_str, profile=profile).prefetch_related('transactions')
    for m in all_mappings:
        for t in m.transactions.all():
            already_linked.add(t.id)
        if m.transaction_id:
            already_linked.add(m.transaction_id)

    # Get previous month's links for pattern matching
    prev_month = _month_str_add(month_str, -1)
    prev_mappings = RecurringMapping.objects.filter(
        month_str=prev_month,
        profile=profile,
    ).select_related('template').prefetch_related('transactions')

    prev_links = {}  # template_id -> list of (description_normalized, amount)
    for pm in prev_mappings:
        tpl_id = pm.template_id
        if not tpl_id:
            continue
        linked = list(pm.transactions.all())
        if linked:
            prev_links[tpl_id] = [
                (_normalize_description(t.description), float(abs(t.amount)))
                for t in linked
            ]
        elif pm.transaction:
            prev_links[tpl_id] = [
                (_normalize_description(pm.transaction.description), float(abs(pm.transaction.amount)))
            ]

    results = []

    for mapping in unlinked:
        cat_type = mapping.custom_type if mapping.is_custom else (
            mapping.template.template_type if mapping.template else ''
        )
        name = mapping.custom_name if mapping.is_custom else (
            mapping.template.name if mapping.template else '?'
        )
        expected = float(mapping.expected_amount)
        is_income = cat_type == 'Income'
        pool = income_txns if is_income else expense_txns

        # Filter out already-linked transactions
        available = [t for t in pool if t.id not in already_linked]
        if not available:
            continue

        matched_txns = []

        # Strategy 1: Match by previous month's transaction pattern
        tpl_id = mapping.template_id
        if tpl_id and tpl_id in prev_links:
            for prev_desc, prev_amt in prev_links[tpl_id]:
                for txn in available:
                    if txn.id in {t.id for t in matched_txns}:
                        continue
                    txn_desc = _normalize_description(txn.description)
                    txn_amt = float(abs(txn.amount))
                    # Exact description match
                    if txn_desc and prev_desc and txn_desc == prev_desc:
                        matched_txns.append(txn)
                        break
                    # Amount match (within 5%)
                    if prev_amt > 0 and abs(txn_amt - prev_amt) / prev_amt < 0.05:
                        # Also check at least some token overlap
                        prev_tokens = set(_extract_tokens(prev_desc))
                        txn_tokens = set(_extract_tokens(txn.description))
                        if prev_tokens & txn_tokens:
                            matched_txns.append(txn)
                            break

        # Strategy 2: Name similarity match
        if not matched_txns:
            name_upper = name.upper()
            name_tokens = set(_extract_tokens(name))
            best_match = None
            best_score = 0

            for txn in available:
                txn_tokens = set(_extract_tokens(txn.description))
                # Token overlap
                if name_tokens and txn_tokens:
                    overlap = len(name_tokens & txn_tokens)
                    total = max(len(name_tokens), 1)
                    score = overlap / total
                    if score > best_score and score >= 0.5:
                        best_score = score
                        best_match = txn

                # Direct substring match
                if name_upper in txn.description.upper() or txn.description.upper() in name_upper:
                    if len(name) >= 4:  # Avoid very short name matches
                        best_match = txn
                        best_score = 1.0
                        break

            if best_match and best_score >= 0.5:
                matched_txns = [best_match]

        # Strategy 3: Amount match (within 10%, single transaction)
        if not matched_txns and expected > 0:
            tol = expected * 0.10
            for txn in available:
                txn_amt = float(abs(txn.amount))
                if abs(txn_amt - expected) <= tol:
                    matched_txns = [txn]
                    break

        # Link matched transactions
        if matched_txns:
            for txn in matched_txns:
                mapping.transactions.add(txn)
                already_linked.add(txn.id)

            total = sum(abs(t.amount) for t in mapping.transactions.all())
            mapping.actual_amount = Decimal(str(total))
            mapping.status = 'mapped'
            mapping.transaction = matched_txns[0]  # Legacy FK
            mapping.save()

            results.append({
                'mapping_id': str(mapping.id),
                'name': name,
                'expected': expected,
                'actual': float(total),
                'linked_count': len(matched_txns),
                'linked': [
                    {
                        'id': str(t.id),
                        'description': t.description,
                        'amount': float(t.amount),
                    }
                    for t in matched_txns
                ],
            })

    return {
        'month_str': month_str,
        'linked': len(results),
        'total_unlinked': len(unlinked),
        'details': results,
    }


# ---------------------------------------------------------------------------
# Reapply Template to Month
# ---------------------------------------------------------------------------

def reapply_template_to_month(month_str, profile=None):
    """
    Delete all existing RecurringMapping rows for the month and re-initialize
    from the current RecurringTemplate. This lets the user reset a month's
    recurring items after editing the template.
    """
    deleted_count = RecurringMapping.objects.filter(month_str=month_str, profile=profile).delete()[0]
    result = initialize_month(month_str, profile=profile)
    result['deleted'] = deleted_count
    return result


# ---------------------------------------------------------------------------
# Month Categories (for TransactionPicker category matching)
# ---------------------------------------------------------------------------

def get_month_categories(month_str, profile=None):
    """
    Return categories with their transaction counts for a given month.
    Only includes expense transactions (amount < 0), excluding internal
    transfers. Categories are sorted by total_amount descending (biggest
    expenses first). Only categories with at least 1 transaction are included.
    """
    from django.db.models import Count, Sum, F

    qs = (
        Transaction.objects.filter(
            month_str=month_str,
            amount__lt=0,
            is_internal_transfer=False,
            category__isnull=False,
            profile=profile,
        )
        .values(
            'category__id',
            'category__name',
            'category__category_type',
        )
        .annotate(
            transaction_count=Count('id'),
            total_amount=Sum('amount'),
        )
        .filter(transaction_count__gte=1)
        .order_by('total_amount')  # most negative first = biggest expenses
    )

    categories = []
    for row in qs:
        categories.append({
            'id': str(row['category__id']),
            'name': row['category__name'],
            'category_type': row['category__category_type'],
            'transaction_count': row['transaction_count'],
            'total_amount': float(row['total_amount']),
        })

    return {
        'month_str': month_str,
        'categories': categories,
    }


# ---------------------------------------------------------------------------
# Mapped Transaction Helper
# ---------------------------------------------------------------------------

def _get_mapped_transaction_ids(month_str, profile):
    """
    Return a set of transaction UUIDs that are linked to any RecurringMapping
    for the given month (via M2M transactions or cross_month_transactions).
    """
    mappings = RecurringMapping.objects.filter(
        profile=profile, month_str=month_str,
    ).prefetch_related('transactions', 'cross_month_transactions')
    ids = set()
    for m in mappings:
        for t in m.transactions.all():
            ids.add(t.id)
        for t in m.cross_month_transactions.all():
            ids.add(t.id)
    return ids


# ---------------------------------------------------------------------------
# Checking Account Transactions
# ---------------------------------------------------------------------------

def get_checking_transactions(month_str, profile=None):
    """
    Fetch all checking account transactions for a given month.
    Returns transactions grouped with summary totals.
    Cross-month-moved transactions are flagged (greyed out in UI).
    """
    txns = Transaction.objects.filter(
        month_str=month_str,
        account__account_type='checking',
        profile=profile,
    ).select_related('account', 'category', 'subcategory').order_by('date')

    # Find cross-month-moved transaction IDs for this month
    cross_month_moved = {}
    other_month_mappings = RecurringMapping.objects.filter(
        profile=profile,
    ).exclude(
        month_str=month_str
    ).prefetch_related('cross_month_transactions')
    for om in other_month_mappings:
        for ct in om.cross_month_transactions.filter(month_str=month_str):
            cross_month_moved[str(ct.id)] = om.month_str

    # Collect all transaction IDs that are linked to recurring mappings this month
    mapped_txn_ids = _get_mapped_transaction_ids(month_str, profile)

    items = []
    total_in = 0.0
    total_out = 0.0

    for t in txns:
        amt = float(t.amount)
        tid = str(t.id)
        moved_to = cross_month_moved.get(tid)

        # Exclude moved transactions from totals
        if not moved_to:
            if amt > 0:
                total_in += amt
            else:
                total_out += amt

        items.append({
            'id': tid,
            'date': str(t.date),
            'description': t.description,
            'amount': amt,
            'category': t.category.name if t.category else 'Não categorizado',
            'category_id': str(t.category.id) if t.category else None,
            'subcategory': t.subcategory.name if t.subcategory else '',
            'subcategory_id': str(t.subcategory.id) if t.subcategory else None,
            'is_internal_transfer': t.is_internal_transfer,
            'is_recurring': t.is_recurring,
            'moved_to_month': moved_to,
            'is_mapped': t.id in mapped_txn_ids,
        })

    return {
        'month_str': month_str,
        'transactions': items,
        'count': len(items),
        'total_in': round(total_in, 2),
        'total_out': round(total_out, 2),
        'net': round(total_in + total_out, 2),
    }


# ---------------------------------------------------------------------------
# Phase 7: Analytics Trends
# ---------------------------------------------------------------------------

def get_analytics_trends(start_month=None, end_month=None, category_ids=None, account_filter=None, profile=None):
    """
    Aggregate data for the Analytics page charts.
    All queries are batched (no N+1).

    Params:
        start_month: 'YYYY-MM' or None (earliest available)
        end_month:   'YYYY-MM' or None (latest available)
        category_ids: list of UUID strings, or None/empty (all categories)
        account_filter: 'mastercard' | 'visa' | 'checking' | '' (all)

    Returns dict with: months, available_months, available_categories,
    spending_trends, category_breakdown, budget_adherence, card_analysis.
    """
    # -- 1. Determine month range -------------------------------------------
    all_months = list(
        Transaction.objects.filter(profile=profile)
        .values_list('month_str', flat=True)
        .distinct()
        .order_by('month_str')
    )
    if not all_months:
        return {
            'months': [],
            'available_months': {'min': None, 'max': None},
            'default_start': None,
            'available_categories': [],
            'spending_trends': [],
            'savings_rate': [],
            'category_breakdown': [],
            'category_trends': {'categories': [], 'data': []},
            'expense_composition': [],
            'budget_adherence': [],
            'card_analysis': [],
            'top_expenses': [],
            'summary_kpis': {},
        }

    data_min = all_months[0]
    data_max = all_months[-1]

    default_start = max(data_min, '2025-12')
    eff_start = start_month if start_month and start_month >= data_min else default_start
    eff_end = end_month if end_month and end_month <= data_max else data_max

    month_list = [m for m in all_months if eff_start <= m <= eff_end]

    # -- 2. Base querysets ---------------------------------------------------
    base_qs = Transaction.objects.filter(
        month_str__in=month_list,
        is_internal_transfer=False,
        profile=profile,
    )
    if category_ids:
        base_qs = base_qs.filter(category_id__in=category_ids)

    # -- 3. Spending trends (income vs expenses per month) ------------------
    income_by_month = dict(
        base_qs.filter(amount__gt=0)
        .values('month_str')
        .annotate(total=Sum('amount'))
        .values_list('month_str', 'total')
    )
    expenses_by_month = dict(
        base_qs.filter(amount__lt=0)
        .values('month_str')
        .annotate(total=Sum('amount'))
        .values_list('month_str', 'total')
    )

    spending_trends = []
    for m in month_list:
        inc = float(income_by_month.get(m, 0) or 0)
        exp = float(expenses_by_month.get(m, 0) or 0)
        spending_trends.append({
            'month': m,
            'income': round(inc, 2),
            'expenses': round(abs(exp), 2),
            'net': round(inc + exp, 2),
        })

    # -- 4. Category breakdown (total expenses per category, full range) ----
    cat_totals = (
        base_qs.filter(amount__lt=0, category__isnull=False)
        .values('category__id', 'category__name', 'category__category_type')
        .annotate(total=Sum('amount'))
        .order_by('total')  # most negative (biggest expense) first
    )
    category_breakdown = []
    for row in cat_totals:
        category_breakdown.append({
            'category_id': str(row['category__id']),
            'category': row['category__name'],
            'type': row['category__category_type'],
            'total': round(abs(float(row['total'])), 2),
        })

    # -- 5. Budget adherence (budget vs actual for end month) ---------------
    # Use the effective end month to show current budget status
    budget_month = eff_end

    # Get all budget configs for the target month (category-based)
    budget_configs = list(
        BudgetConfig.objects
        .filter(month_str=budget_month, category__isnull=False, profile=profile)
        .select_related('category')
    )

    # Also check Category.default_limit for categories without BudgetConfig
    budget_cat_ids = {bc.category_id for bc in budget_configs}
    cats_with_defaults = list(
        Category.objects
        .filter(is_active=True, default_limit__gt=0, profile=profile)
        .exclude(id__in=budget_cat_ids)
    )

    # Build budget map: category_id -> budget amount
    budget_map = {}
    for bc in budget_configs:
        budget_map[bc.category_id] = float(bc.limit_override)
    for cat in cats_with_defaults:
        budget_map[cat.id] = float(cat.default_limit)

    if budget_map:
        # Actual spending for the budget month by category
        actual_qs = (
            Transaction.objects.filter(
                month_str=budget_month,
                is_internal_transfer=False,
                amount__lt=0,
                category_id__in=budget_map.keys(),
                profile=profile,
            )
            .values('category__id', 'category__name')
            .annotate(total=Sum('amount'))
        )
        actual_map = {
            row['category__id']: {
                'name': row['category__name'],
                'actual': round(abs(float(row['total'])), 2),
            }
            for row in actual_qs
        }
    else:
        actual_map = {}

    budget_adherence = []
    for cat_id, budgeted in budget_map.items():
        info = actual_map.get(cat_id)
        cat_name = info['name'] if info else (
            next((bc.category.name for bc in budget_configs if bc.category_id == cat_id), None)
            or next((c.name for c in cats_with_defaults if c.id == cat_id), '?')
        )
        actual = info['actual'] if info else 0.0
        budget_adherence.append({
            'category_id': str(cat_id),
            'category': cat_name,
            'budgeted': round(budgeted, 2),
            'actual': actual,
            'pct': round((actual / budgeted * 100) if budgeted else 0, 1),
        })
    budget_adherence.sort(key=lambda x: x['pct'], reverse=True)

    # -- 6. Card analysis (spending by card/account per month) ---------------
    # Credit cards: use invoice_month for accurate billing alignment
    cc_qs = Transaction.objects.filter(
        invoice_month__in=month_list,
        account__account_type='credit_card',
        is_internal_transfer=False,
        amount__lt=0,
        profile=profile,
    )
    if category_ids:
        cc_qs = cc_qs.filter(category_id__in=category_ids)

    # Mastercard totals by month
    master_by_month = dict(
        cc_qs.filter(account__name__icontains='Mastercard')
        .values('invoice_month')
        .annotate(total=Sum('amount'))
        .values_list('invoice_month', 'total')
    )
    # Visa totals by month
    visa_by_month = dict(
        cc_qs.filter(account__name__icontains='Visa')
        .values('invoice_month')
        .annotate(total=Sum('amount'))
        .values_list('invoice_month', 'total')
    )
    # Checking totals by month (uses month_str)
    checking_qs = Transaction.objects.filter(
        month_str__in=month_list,
        account__account_type='checking',
        is_internal_transfer=False,
        amount__lt=0,
        profile=profile,
    )
    if category_ids:
        checking_qs = checking_qs.filter(category_id__in=category_ids)
    checking_by_month = dict(
        checking_qs
        .values('month_str')
        .annotate(total=Sum('amount'))
        .values_list('month_str', 'total')
    )

    card_analysis = []
    for m in month_list:
        card_analysis.append({
            'month': m,
            'mastercard': round(abs(float(master_by_month.get(m, 0) or 0)), 2),
            'visa': round(abs(float(visa_by_month.get(m, 0) or 0)), 2),
            'checking': round(abs(float(checking_by_month.get(m, 0) or 0)), 2),
        })

    # -- 7. Available categories (for filter dropdown) ----------------------
    available_categories = list(
        Transaction.objects.filter(
            month_str__in=month_list,
            is_internal_transfer=False,
            amount__lt=0,
            category__isnull=False,
            profile=profile,
        )
        .values('category__id', 'category__name', 'category__category_type')
        .annotate(cnt=Count('id'))
        .filter(cnt__gte=1)
        .order_by('category__name')
    )
    available_cats = [
        {
            'id': str(row['category__id']),
            'name': row['category__name'],
            'type': row['category__category_type'],
        }
        for row in available_categories
    ]

    # -- 8. Savings rate (computed from spending_trends, no extra query) ----
    savings_rate = []
    for st in spending_trends:
        inc = st['income']
        exp = st['expenses']
        rate = ((inc - exp) / inc * 100) if inc > 0 else 0
        savings_rate.append({
            'month': st['month'],
            'income': inc,
            'expenses': exp,
            'net': st['net'],
            'rate': round(rate, 1),
        })

    # -- 9. Category trends (per-category per-month, top 6 + Outros) ------
    cat_month_qs = (
        base_qs.filter(amount__lt=0, category__isnull=False)
        .values('month_str', 'category__name')
        .annotate(total=Sum('amount'))
        .order_by('month_str', 'category__name')
    )
    # Find top 6 categories by total spend
    cat_grand_totals = {}
    for row in cat_month_qs:
        name = row['category__name']
        cat_grand_totals[name] = cat_grand_totals.get(name, 0) + abs(float(row['total']))
    top_6_cats = sorted(cat_grand_totals, key=cat_grand_totals.get, reverse=True)[:6]
    top_6_set = set(top_6_cats)

    # Build per-month data with top 6 + Outros
    cat_trends_by_month = {m: {c: 0.0 for c in top_6_cats + ['Outros']} for m in month_list}
    for row in cat_month_qs:
        m = row['month_str']
        name = row['category__name']
        val = round(abs(float(row['total'])), 2)
        if m in cat_trends_by_month:
            if name in top_6_set:
                cat_trends_by_month[m][name] = val
            else:
                cat_trends_by_month[m]['Outros'] += val

    category_trends = {
        'categories': top_6_cats + (['Outros'] if any(cat_trends_by_month[m]['Outros'] > 0 for m in month_list) else []),
        'data': [
            {'month': m, **{k: round(v, 2) for k, v in cat_trends_by_month[m].items() if k in top_6_set or (k == 'Outros' and v > 0)}}
            for m in month_list
        ],
    }

    # -- 10. Expense composition (fixo/variavel/parcelas/investimento) -----
    type_month_qs = (
        base_qs.filter(amount__lt=0, category__isnull=False)
        .values('month_str', 'category__category_type')
        .annotate(total=Sum('amount'))
    )
    installment_month_qs = dict(
        base_qs.filter(amount__lt=0, is_installment=True)
        .values('month_str')
        .annotate(total=Sum('amount'))
        .values_list('month_str', 'total')
    )

    type_data = {m: {'Fixo': 0, 'Variavel': 0, 'Investimento': 0, 'Income': 0} for m in month_list}
    for row in type_month_qs:
        m = row['month_str']
        t = row['category__category_type']
        if m in type_data and t in type_data[m]:
            type_data[m][t] = abs(float(row['total']))

    expense_composition = []
    for m in month_list:
        parcelas_val = abs(float(installment_month_qs.get(m, 0) or 0))
        variavel_raw = type_data[m]['Variavel']
        expense_composition.append({
            'month': m,
            'fixo': round(type_data[m]['Fixo'], 2),
            'variavel': round(max(0, variavel_raw - parcelas_val), 2),
            'parcelas': round(parcelas_val, 2),
            'investimento': round(type_data[m]['Investimento'], 2),
        })

    # -- 11. Top 10 expenses ------------------------------------------------
    top_qs = (
        base_qs.filter(amount__lt=0)
        .select_related('category', 'account')
        .order_by('amount')[:10]
    )
    top_expenses = [
        {
            'description': t.description,
            'amount': round(abs(float(t.amount)), 2),
            'date': t.date.isoformat(),
            'month': t.month_str,
            'category': t.category.name if t.category else 'Sem categoria',
            'account': t.account.name,
        }
        for t in top_qs
    ]

    # -- 12. Summary KPIs (computed, no extra query) -------------------------
    num_months = len(month_list) or 1
    total_income = sum(st['income'] for st in spending_trends)
    total_expenses = sum(st['expenses'] for st in spending_trends)
    total_net = total_income - total_expenses
    avg_savings = (total_net / total_income * 100) if total_income > 0 else 0

    summary_kpis = {
        'avg_monthly_income': round(total_income / num_months, 2),
        'avg_monthly_expenses': round(total_expenses / num_months, 2),
        'avg_savings_rate': round(avg_savings, 1),
        'total_income': round(total_income, 2),
        'total_expenses': round(total_expenses, 2),
        'total_net': round(total_net, 2),
        'num_months': num_months,
        'best_month': max(spending_trends, key=lambda x: x['net'])['month'] if spending_trends else None,
        'worst_month': min(spending_trends, key=lambda x: x['net'])['month'] if spending_trends else None,
    }

    # -- 13. Monthly stacked by category (ALL categories, with totals) -------
    # Like the old Excel "Consumo por Ano/Mês e Categoria" chart
    all_cat_month_qs = (
        base_qs.filter(amount__lt=0, category__isnull=False)
        .values('month_str', 'category__name')
        .annotate(total=Sum('amount'))
        .order_by('month_str', 'category__name')
    )
    # Also count uncategorized
    uncat_month_qs = dict(
        base_qs.filter(amount__lt=0, category__isnull=True)
        .values('month_str')
        .annotate(total=Sum('amount'))
        .values_list('month_str', 'total')
    )
    # Collect all category names
    all_cat_names = set()
    monthly_cat_data = {m: {} for m in month_list}
    for row in all_cat_month_qs:
        m = row['month_str']
        name = row['category__name']
        if m in monthly_cat_data:
            monthly_cat_data[m][name] = round(abs(float(row['total'])), 2)
            all_cat_names.add(name)
    # Add uncategorized
    for m in month_list:
        uncat_val = abs(float(uncat_month_qs.get(m, 0) or 0))
        if uncat_val > 0:
            monthly_cat_data[m]['Sem categoria'] = round(uncat_val, 2)
            all_cat_names.add('Sem categoria')

    # Sort categories by grand total descending
    cat_totals_all = {}
    for m in month_list:
        for name, val in monthly_cat_data[m].items():
            cat_totals_all[name] = cat_totals_all.get(name, 0) + val
    sorted_cats = sorted(cat_totals_all, key=cat_totals_all.get, reverse=True)

    monthly_category_stacked = {
        'categories': sorted_cats,
        'data': [
            {
                'month': m,
                'total': round(sum(monthly_cat_data[m].values()), 2),
                **{cat: monthly_cat_data[m].get(cat, 0) for cat in sorted_cats},
            }
            for m in month_list
        ],
    }

    # -- 14. Category × Recurring Item breakdown --------------------------------
    # Groups spending by type: recurring template items for Fixo/Income/Investimento,
    # normalized descriptions for Variável categories.
    # "Gastos Fixos" groups all Fixo recurring items together,
    # Variável categories keep their description-level breakdown.
    import re
    def _normalize_desc(desc):
        """Group similar descriptions: strip installment suffixes, parcela IDs, dates."""
        s = desc.strip()
        s = re.sub(r'\s*\d{2}/\d{2,3}$', '', s)
        s = re.sub(r'(Cons Parcela)\d+', r'\1', s)
        s = re.sub(r'\d{2}\s+\d{2}$', '', s).strip()
        s = re.sub(r'(\d{2}\s+\d{2})$', '', s).strip()
        return s or desc

    # Build recurring template lookup: category_name → template for Fixo/Income/Investimento
    from api.models import RecurringTemplate as RT
    recurring_templates = {t.name: t for t in RT.objects.filter(is_active=True, profile=profile)}
    # Category type lookup
    cat_type_map = {c.name: c.category_type for c in Category.objects.filter(profile=profile)}

    # Query all expense transactions by category and description
    cat_desc_qs = (
        base_qs.filter(amount__lt=0, category__isnull=False)
        .values('category__name', 'category__category_type', 'description')
        .annotate(total=Sum('amount'))
        .order_by('category__name')
    )

    # Separate into: Fixo items (grouped under "Gastos Fixos") and Variável categories
    fixo_items = {}       # template_name → total
    variavel_cats = {}    # category_name → {desc → total}

    for row in cat_desc_qs:
        cat = row['category__name']
        cat_type = row['category__category_type']
        val = round(abs(float(row['total'])), 2)

        if cat_type in ('Fixo', 'Investimento'):
            # Each Fixo/Investimento category IS a recurring item
            fixo_items[cat] = fixo_items.get(cat, 0) + val
        else:
            # Variável: group by normalized description within category
            desc = _normalize_desc(row['description'])
            if cat not in variavel_cats:
                variavel_cats[cat] = {}
            variavel_cats[cat][desc] = variavel_cats[cat].get(desc, 0) + val

    # Build output
    category_desc_breakdown = []

    # 1) "Gastos Fixos" — all Fixo recurring template items as sub-items
    if fixo_items:
        sorted_fixo = sorted(fixo_items.items(), key=lambda x: x[1], reverse=True)
        items = []
        for name, val in sorted_fixo:
            tpl = recurring_templates.get(name)
            items.append({
                'name': name,
                'value': round(val, 2),
                'expected': float(tpl.default_limit) if tpl else None,
            })
        fixo_total = sum(v for _, v in sorted_fixo)
        category_desc_breakdown.append({
            'category': 'Gastos Fixos',
            'total': round(fixo_total, 2),
            'items': items,
            'is_recurring': True,
        })

    # 2) Variável categories — top 8 descriptions + Outros
    for cat in sorted_cats:
        if cat == 'Sem categoria' or cat not in variavel_cats:
            continue
        cat_type = cat_type_map.get(cat, 'Variavel')
        if cat_type in ('Fixo', 'Income', 'Investimento'):
            continue  # already handled above
        descs = variavel_cats[cat]
        sorted_descs = sorted(descs.items(), key=lambda x: x[1], reverse=True)
        top_items = sorted_descs[:8]
        rest_total = sum(v for _, v in sorted_descs[8:])
        items = [{'name': d, 'value': round(v, 2)} for d, v in top_items]
        if rest_total > 0:
            items.append({'name': 'Outros', 'value': round(rest_total, 2)})
        cat_total = sum(v for _, v in sorted_descs)
        category_desc_breakdown.append({
            'category': cat,
            'total': round(cat_total, 2),
            'items': items,
            'is_recurring': False,
        })
    category_desc_breakdown.sort(key=lambda x: x['total'], reverse=True)

    # Include savings target from profile for chart reference line
    savings_target = float(profile.savings_target_pct) if profile else 20.0

    return {
        'months': month_list,
        'available_months': {'min': data_min, 'max': data_max},
        'default_start': default_start,
        'available_categories': available_cats,
        'spending_trends': spending_trends,
        'savings_rate': savings_rate,
        'savings_target_pct': savings_target,
        'category_breakdown': category_breakdown,
        'category_trends': category_trends,
        'expense_composition': expense_composition,
        'budget_adherence': budget_adherence,
        'card_analysis': card_analysis,
        'top_expenses': top_expenses,
        'summary_kpis': summary_kpis,
        'monthly_category_stacked': monthly_category_stacked,
        'category_desc_breakdown': category_desc_breakdown,
    }


# ---------------------------------------------------------------------------
# Spending Insights (BUDG-03)
# ---------------------------------------------------------------------------

def get_spending_insights(profile=None):
    """
    Algorithmic spending analysis that generates actionable insights.
    Analyzes last 6 months of data for patterns, trends, and anomalies.
    """
    from django.db.models import Sum, Count, Avg

    # Get last 6 months of data
    all_months = list(
        Transaction.objects.filter(profile=profile)
        .values_list('month_str', flat=True)
        .distinct()
        .order_by('-month_str')[:6]
    )
    if len(all_months) < 2:
        return {'insights': [], 'summary': 'Dados insuficientes para gerar insights.'}

    all_months = sorted(all_months)
    latest = all_months[-1]
    prev = all_months[-2]

    insights = []

    # --- 1. Month-over-month spending change ---
    def _month_totals(month):
        inc = Transaction.objects.filter(
            profile=profile, month_str=month, is_internal_transfer=False, amount__gt=0
        ).aggregate(t=Sum('amount'))['t'] or 0
        exp = Transaction.objects.filter(
            profile=profile, month_str=month, is_internal_transfer=False, amount__lt=0
        ).aggregate(t=Sum('amount'))['t'] or 0
        return float(inc), abs(float(exp))

    curr_inc, curr_exp = _month_totals(latest)
    prev_inc, prev_exp = _month_totals(prev)

    if prev_exp > 0:
        exp_change = ((curr_exp - prev_exp) / prev_exp) * 100
        if exp_change > 15:
            insights.append({
                'type': 'warning',
                'icon': 'trending_up',
                'title': 'Gastos em alta',
                'message': f'Gastos subiram {exp_change:.0f}% em {latest} vs {prev} (R$ {curr_exp:,.0f} vs R$ {prev_exp:,.0f}).',
                'priority': 1,
            })
        elif exp_change < -10:
            insights.append({
                'type': 'positive',
                'icon': 'trending_down',
                'title': 'Gastos em queda',
                'message': f'Gastos caíram {abs(exp_change):.0f}% em {latest} vs {prev}. Continue assim!',
                'priority': 3,
            })

    # --- 2. Category spikes (top 3 biggest increases) ---
    cat_by_month = {}
    for m in [prev, latest]:
        rows = (
            Transaction.objects.filter(
                profile=profile, month_str=m, is_internal_transfer=False,
                amount__lt=0, category__isnull=False,
            )
            .values('category__name')
            .annotate(total=Sum('amount'))
        )
        cat_by_month[m] = {r['category__name']: abs(float(r['total'])) for r in rows}

    spikes = []
    for cat, curr_val in cat_by_month.get(latest, {}).items():
        prev_val = cat_by_month.get(prev, {}).get(cat, 0)
        if prev_val > 100:  # only meaningful if previous was substantial
            change = curr_val - prev_val
            pct = (change / prev_val) * 100
            if pct > 30 and change > 200:
                spikes.append((cat, change, pct, curr_val, prev_val))
    spikes.sort(key=lambda x: x[1], reverse=True)

    for cat, change, pct, curr_val, prev_val in spikes[:3]:
        insights.append({
            'type': 'warning',
            'icon': 'category',
            'title': f'{cat}: +{pct:.0f}%',
            'message': f'Gastou R$ {curr_val:,.0f} em {cat} (era R$ {prev_val:,.0f}). Diferença de R$ {change:,.0f}.',
            'priority': 2,
        })

    # --- 3. Savings rate vs target ---
    target = float(profile.savings_target_pct) if profile else 20.0
    if curr_inc > 0:
        savings_rate = ((curr_inc - curr_exp) / curr_inc) * 100
        if savings_rate < 0:
            insights.append({
                'type': 'danger',
                'icon': 'savings',
                'title': 'Gastando mais do que ganha',
                'message': f'Taxa de poupança: {savings_rate:.1f}%. Gastos excedem receitas em R$ {curr_exp - curr_inc:,.0f}.',
                'priority': 1,
            })
        elif savings_rate < target:
            gap = target - savings_rate
            insights.append({
                'type': 'warning',
                'icon': 'savings',
                'title': f'Abaixo da meta de poupança',
                'message': f'Taxa de poupança: {savings_rate:.1f}% (meta: {target:.0f}%). Faltam {gap:.1f}pp para atingir.',
                'priority': 2,
            })
        else:
            insights.append({
                'type': 'positive',
                'icon': 'savings',
                'title': 'Meta de poupança atingida!',
                'message': f'Taxa de poupança: {savings_rate:.1f}% (meta: {target:.0f}%). Parabéns!',
                'priority': 4,
            })

    # --- 4. Budget adherence (categories over limit) ---
    over_budget = []
    variavel_cats = Category.objects.filter(
        profile=profile, category_type='Variavel', is_active=True, default_limit__gt=0
    )
    for cat in variavel_cats:
        # Check for month override
        override = BudgetConfig.objects.filter(
            profile=profile, category=cat, month_str=latest
        ).first()
        limit = float(override.limit_override) if override else float(cat.default_limit)
        if limit <= 0:
            continue
        spent = abs(float(
            Transaction.objects.filter(
                profile=profile, month_str=latest, category=cat,
                is_internal_transfer=False, amount__lt=0,
            ).aggregate(t=Sum('amount'))['t'] or 0
        ))
        if spent > limit:
            over_pct = ((spent - limit) / limit) * 100
            over_budget.append((cat.name, spent, limit, over_pct))

    over_budget.sort(key=lambda x: x[3], reverse=True)
    for name, spent, limit, over_pct in over_budget[:3]:
        insights.append({
            'type': 'danger' if over_pct > 30 else 'warning',
            'icon': 'budget',
            'title': f'{name}: {over_pct:.0f}% acima',
            'message': f'Gastou R$ {spent:,.0f} de R$ {limit:,.0f} ({over_pct:.0f}% acima do orçamento).',
            'priority': 2,
        })

    # --- 5. Average trends (6-month spending trajectory) ---
    if len(all_months) >= 3:
        monthly_expenses = []
        for m in all_months:
            _, exp = _month_totals(m)
            monthly_expenses.append(exp)
        first_half_avg = sum(monthly_expenses[:len(monthly_expenses)//2]) / max(1, len(monthly_expenses)//2)
        second_half_avg = sum(monthly_expenses[len(monthly_expenses)//2:]) / max(1, len(monthly_expenses) - len(monthly_expenses)//2)

        if first_half_avg > 0:
            trend_pct = ((second_half_avg - first_half_avg) / first_half_avg) * 100
            if trend_pct > 10:
                insights.append({
                    'type': 'info',
                    'icon': 'timeline',
                    'title': 'Tendência de alta nos gastos',
                    'message': f'Gastos médios subiram {trend_pct:.0f}% nos últimos meses (R$ {first_half_avg:,.0f} → R$ {second_half_avg:,.0f}).',
                    'priority': 3,
                })
            elif trend_pct < -10:
                insights.append({
                    'type': 'positive',
                    'icon': 'timeline',
                    'title': 'Tendência de queda nos gastos',
                    'message': f'Gastos médios caíram {abs(trend_pct):.0f}% nos últimos meses. Boa evolução!',
                    'priority': 4,
                })

    # --- 6. New categories appearing ---
    prev_cats = set(cat_by_month.get(prev, {}).keys())
    curr_cats = set(cat_by_month.get(latest, {}).keys())
    new_cats = curr_cats - prev_cats
    new_significant = [(c, cat_by_month[latest][c]) for c in new_cats if cat_by_month[latest][c] > 100]
    new_significant.sort(key=lambda x: x[1], reverse=True)
    for cat, amount in new_significant[:2]:
        insights.append({
            'type': 'info',
            'icon': 'new',
            'title': f'Nova categoria: {cat}',
            'message': f'R$ {amount:,.0f} gastos em {cat} — categoria nova este mês.',
            'priority': 3,
        })

    # Sort by priority (1 = most urgent)
    insights.sort(key=lambda x: x['priority'])

    # Build summary
    if not insights:
        summary = 'Parabéns! Seus gastos estão estáveis e dentro do esperado.'
    else:
        warnings = sum(1 for i in insights if i['type'] in ('warning', 'danger'))
        positives = sum(1 for i in insights if i['type'] == 'positive')
        if warnings > positives:
            summary = f'{warnings} ponto(s) de atenção identificado(s). Revise os alertas abaixo.'
        else:
            summary = f'{positives} indicador(es) positivo(s). Bom trabalho no controle financeiro!'

    return {
        'insights': insights,
        'summary': summary,
        'months_analyzed': len(all_months),
        'latest_month': latest,
    }
