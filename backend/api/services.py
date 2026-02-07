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
    RecurringMapping, BudgetConfig, CategorizationRule,
    MetricasOrderConfig, CustomMetric,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_expected_amount(category, month_str):
    """
    Return the expected amount for a category in a month.
    Uses BudgetConfig override if it exists, otherwise Category.default_limit.
    """
    try:
        bc = BudgetConfig.objects.get(category=category, month_str=month_str)
        return bc.limit_override
    except BudgetConfig.DoesNotExist:
        return category.default_limit


# ---------------------------------------------------------------------------
# A2-1: initialize_month
# ---------------------------------------------------------------------------

def initialize_month(month_str):
    """
    Create RecurringMapping rows for a month from Category template.
    Idempotent — skips categories that already have a mapping for the month.
    Returns dict with created count and total count.
    """
    categories = Category.objects.filter(
        category_type__in=['Fixo', 'Income', 'Investimento'],
        is_active=True,
        default_limit__gt=0,
    )
    created = 0
    for cat in categories:
        expected = _get_expected_amount(cat, month_str)
        _, was_created = RecurringMapping.objects.get_or_create(
            category=cat,
            month_str=month_str,
            defaults={
                'expected_amount': expected,
                'status': 'missing',
                'is_custom': False,
            },
        )
        if was_created:
            created += 1

    total = RecurringMapping.objects.filter(month_str=month_str).count()
    return {
        'month_str': month_str,
        'created': created,
        'total': total,
        'initialized': created > 0,
    }


# ---------------------------------------------------------------------------
# A2-2: get_recurring_data (REWRITE)
# ---------------------------------------------------------------------------

def get_recurring_data(month_str):
    """
    RECORRENTES — recurring items sourced from RecurringMapping table.

    Auto-initializes the month from Category template if no mappings exist.
    Each item carries a mapping_id for editing.
    Status is computed from the linked transaction or category-matched transactions.
    Suggestion logic is preserved for 'Faltando' items.

    Returns: dict with items grouped by type (fixo, income, investimento),
    plus 'all' list, and 'initialized' flag.
    """
    # Auto-initialize if no mappings exist for this month
    existing = RecurringMapping.objects.filter(month_str=month_str).count()
    was_initialized = False
    if existing == 0:
        result = initialize_month(month_str)
        was_initialized = result['initialized']

    # Fetch all mappings for this month
    mappings = RecurringMapping.objects.filter(
        month_str=month_str,
    ).select_related('category', 'transaction', 'transaction__account').prefetch_related(
        'transactions', 'transactions__account'
    ).order_by(
        'display_order', 'category__display_order', 'custom_name'
    )

    # Transaction pools for suggestion matching
    txns = Transaction.objects.filter(
        month_str=month_str,
    ).select_related('category', 'account')
    income_pool = txns.filter(amount__gt=0)
    expense_pool = txns.filter(amount__lt=0)

    all_expense_descs = list(expense_pool.values_list('description', flat=True).distinct())
    all_income_descs = list(income_pool.values_list('description', flat=True).distinct())

    def _get_type(mapping):
        """Get the category type for a mapping (handles custom items)."""
        if mapping.is_custom:
            return mapping.custom_type
        return mapping.category.category_type if mapping.category else ''

    def _get_name(mapping):
        """Get the display name for a mapping."""
        if mapping.is_custom:
            return mapping.custom_name
        return mapping.category.name if mapping.category else '?'

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
            'id': str(mapping.category.id) if mapping.category else None,
            'mapping_id': str(mapping.id),
            'name': name,
            'due_day': mapping.category.due_day if mapping.category else None,
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
            'category_type': cat_type,
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

def update_recurring_expected(mapping_id, expected_amount):
    """
    Update the expected amount for a RecurringMapping.
    Returns the updated mapping summary.
    """
    mapping = RecurringMapping.objects.select_related('category').get(id=mapping_id)
    mapping.expected_amount = Decimal(str(expected_amount))
    mapping.save()

    name = mapping.custom_name if mapping.is_custom else (
        mapping.category.name if mapping.category else '?'
    )

    return {
        'mapping_id': str(mapping.id),
        'name': name,
        'expected_amount': float(mapping.expected_amount),
    }


# ---------------------------------------------------------------------------
# A2-3b: update_recurring_item (general field update)
# ---------------------------------------------------------------------------

def update_recurring_item(mapping_id, **kwargs):
    """
    Update editable fields on a RecurringMapping: name, category_type,
    expected_amount, due_day.

    For category-based items, name/type changes convert them to custom items
    (is_custom=True) to preserve the override without affecting the template.
    """
    mapping = RecurringMapping.objects.select_related('category').get(id=mapping_id)

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
            mapping.custom_type = mapping.category.category_type if mapping.category else ''

    if 'category_type' in kwargs and kwargs['category_type'] is not None:
        new_type = kwargs['category_type']
        if mapping.is_custom:
            mapping.custom_type = new_type
        else:
            # Convert to custom to preserve override
            mapping.is_custom = True
            mapping.custom_name = mapping.category.name if mapping.category else '?'
            mapping.custom_type = new_type

    if 'due_day' in kwargs:
        due_day = int(kwargs['due_day']) if kwargs['due_day'] else None
        if mapping.category and not mapping.is_custom:
            mapping.category.due_day = due_day
            mapping.category.save()

    mapping.save()

    name = mapping.custom_name if mapping.is_custom else (
        mapping.category.name if mapping.category else '?'
    )
    cat_type = mapping.custom_type if mapping.is_custom else (
        mapping.category.category_type if mapping.category else ''
    )
    due_day_val = mapping.category.due_day if mapping.category else None

    return {
        'mapping_id': str(mapping.id),
        'name': name,
        'category_type': cat_type,
        'expected_amount': float(mapping.expected_amount),
        'due_day': due_day_val,
        'is_custom': mapping.is_custom,
    }


# ---------------------------------------------------------------------------
# A2-4: add_custom_recurring
# ---------------------------------------------------------------------------

def add_custom_recurring(month_str, name, category_type, expected_amount):
    """
    Add a custom one-off recurring item for a specific month.
    Custom items have is_custom=True and no category FK.
    """
    mapping = RecurringMapping.objects.create(
        month_str=month_str,
        is_custom=True,
        custom_name=name,
        custom_type=category_type,
        expected_amount=Decimal(str(expected_amount)),
        status='missing',
        category=None,
    )

    return {
        'mapping_id': str(mapping.id),
        'name': name,
        'category_type': category_type,
        'expected_amount': float(mapping.expected_amount),
        'month_str': month_str,
    }


# ---------------------------------------------------------------------------
# A2-5: delete_custom_recurring
# ---------------------------------------------------------------------------

def delete_custom_recurring(mapping_id):
    """
    Delete a custom recurring item. Only works for is_custom=True items.
    Raises ValueError if trying to delete a non-custom item.
    """
    mapping = RecurringMapping.objects.get(id=mapping_id)
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

def skip_recurring(mapping_id):
    """Mark a recurring item as skipped for this month."""
    mapping = RecurringMapping.objects.select_related('category').get(id=mapping_id)
    mapping.status = 'skipped'
    mapping.save()

    name = mapping.custom_name if mapping.is_custom else (
        mapping.category.name if mapping.category else '?'
    )
    return {
        'mapping_id': str(mapping.id),
        'name': name,
        'status': 'skipped',
    }


def unskip_recurring(mapping_id):
    """Restore a skipped recurring item back to missing status."""
    mapping = RecurringMapping.objects.select_related('category').get(id=mapping_id)
    mapping.status = 'missing'
    mapping.save()

    name = mapping.custom_name if mapping.is_custom else (
        mapping.category.name if mapping.category else '?'
    )
    return {
        'mapping_id': str(mapping.id),
        'name': name,
        'status': 'missing',
    }


# ---------------------------------------------------------------------------
# A2-7: save_balance_override
# ---------------------------------------------------------------------------

def save_balance_override(month_str, balance):
    """
    Save or update the checking account balance override for a month.
    """
    bo, created = BalanceOverride.objects.update_or_create(
        month_str=month_str,
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

def get_recurring_templates():
    """
    Return all Category items that serve as recurring templates.
    These are categories with default_limit > 0 and types used for recurring items.
    """
    categories = Category.objects.filter(
        category_type__in=['Fixo', 'Income', 'Investimento', 'Variavel'],
        is_active=True,
    ).order_by('display_order', 'name')

    items = []
    for cat in categories:
        items.append({
            'id': str(cat.id),
            'name': cat.name,
            'category_type': cat.category_type,
            'default_limit': float(cat.default_limit),
            'due_day': cat.due_day,
            'display_order': cat.display_order,
        })

    return {'templates': items, 'count': len(items)}


def update_recurring_template(category_id, **kwargs):
    """
    Update a Category template used for recurring items.
    Supported fields: name, category_type, default_limit, due_day, display_order
    """
    cat = Category.objects.get(id=category_id)

    if 'name' in kwargs and kwargs['name'] is not None:
        cat.name = kwargs['name'].strip()
    if 'category_type' in kwargs and kwargs['category_type'] is not None:
        cat.category_type = kwargs['category_type']
    if 'default_limit' in kwargs and kwargs['default_limit'] is not None:
        cat.default_limit = Decimal(str(kwargs['default_limit']))
    if 'due_day' in kwargs:
        cat.due_day = int(kwargs['due_day']) if kwargs['due_day'] else None
    if 'display_order' in kwargs and kwargs['display_order'] is not None:
        cat.display_order = int(kwargs['display_order'])

    cat.save()

    return {
        'id': str(cat.id),
        'name': cat.name,
        'category_type': cat.category_type,
        'default_limit': float(cat.default_limit),
        'due_day': cat.due_day,
        'display_order': cat.display_order,
    }


def create_recurring_template(name, category_type, default_limit, due_day=None):
    """
    Create a new Category to serve as a recurring template.
    """
    # Find max display_order for this type
    max_order = Category.objects.filter(
        category_type=category_type
    ).aggregate(m=Max('display_order'))['m'] or 0

    cat = Category.objects.create(
        name=name.strip(),
        category_type=category_type,
        default_limit=Decimal(str(default_limit)),
        due_day=due_day,
        is_active=True,
        display_order=max_order + 1,
    )

    return {
        'id': str(cat.id),
        'name': cat.name,
        'category_type': cat.category_type,
        'default_limit': float(cat.default_limit),
        'due_day': cat.due_day,
        'display_order': cat.display_order,
    }


def delete_recurring_template(category_id):
    """
    Deactivate a Category template (soft delete).
    Sets is_active=False and default_limit=0 so it won't appear in future months.
    """
    cat = Category.objects.get(id=category_id)
    cat.is_active = False
    cat.default_limit = Decimal('0.00')
    cat.save()

    return {
        'id': str(cat.id),
        'name': cat.name,
        'deleted': True,
    }


# ---------------------------------------------------------------------------
# Unified metrics (MÉTRICAS)
# Replaces the old get_summary_metrics() and get_control_metrics() functions.
# ---------------------------------------------------------------------------

def _get_prev_month_saldo(month_str):
    """
    Get the previous month's saldo projetado to use as this month's
    starting balance when no BalanceOverride is set.

    Calls get_metricas() for the previous month (with _cascade=False to
    prevent infinite recursion on months without a BO anchor).
    """
    prev_str = _month_str_add(month_str, -1)

    # Check if prev month has any transactions at all
    has_data = Transaction.objects.filter(month_str=prev_str).exists()
    if not has_data:
        # Also check if prev month has a BalanceOverride
        try:
            BalanceOverride.objects.get(month_str=prev_str)
        except BalanceOverride.DoesNotExist:
            return None

    # Compute prev month's full metricas to get its saldo_projetado
    prev_metricas = get_metricas(prev_str, _cascade=False)
    return Decimal(str(prev_metricas['saldo_projetado']))


def get_metricas(month_str, _cascade=True):
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
    other_month_mappings = RecurringMapping.objects.exclude(
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
    ).exclude(
        id__in=cross_month_exclude_ids
    ).select_related('category', 'account')

    income_txns = txns.filter(amount__gt=0)
    expense_txns = txns.filter(amount__lt=0)

    # Unfiltered pools for recurring matching (includes internal transfers,
    # but still excludes cross-month moved transactions)
    all_txns = Transaction.objects.filter(
        month_str=month_str
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
        month_str=month_str
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
    ).filter(
        Q(category__category_type='Income') | Q(is_custom=True, custom_type='Income')
    ).exclude(status='skipped').select_related('category', 'transaction').prefetch_related('transactions')

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
    ).filter(
        Q(category__category_type='Fixo') | Q(is_custom=True, custom_type='Fixo')
    ).exclude(status='skipped').select_related('category', 'transaction').prefetch_related('transactions')

    fixo_expected_total = Decimal('0.00')
    for m in fixo_mappings_all:
        fixo_expected_total += m.expected_amount

    schedule = _compute_installment_schedule(month_str, num_future_months=0)
    parcelas_total = Decimal(str(schedule.get(month_str, 0)))

    variable_budget = Category.objects.filter(
        category_type='Variavel', is_active=True,
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
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00'))

    # =====================================================================
    # 8. FATURA VISA — Visa Infinite
    # =====================================================================
    fatura_visa = abs(Transaction.objects.filter(
        invoice_month=month_str,
        account__name__icontains='Visa',
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
        bo = BalanceOverride.objects.get(month_str=month_str)
        balance_override = float(bo.balance)
    except BalanceOverride.DoesNotExist:
        pass

    # Cascade: compute previous month's projected ending balance
    prev_month_saldo = None
    prev_month_saldo_float = None
    if _cascade:
        prev_month_saldo = _get_prev_month_saldo(month_str)
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
        account_type='credit_card', is_active=True
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

    # Build cross-month moved info for UI
    cross_month_info = []
    for txn_id, target in cross_month_targets.items():
        try:
            t = Transaction.objects.get(id=txn_id)
            cross_month_info.append({
                'id': str(txn_id),
                'description': t.description,
                'amount': float(t.amount),
                'moved_to': target,
            })
        except Transaction.DoesNotExist:
            pass

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
    }

    # Append custom metrics computed from this month's data
    result_dict['custom_metrics'] = _compute_custom_metrics(month_str, result_dict)
    return result_dict


# ---------------------------------------------------------------------------
# Metricas order + custom metrics
# ---------------------------------------------------------------------------

BUILTIN_CARD_ORDER = [
    'entradas_atuais', 'entradas_projetadas', 'a_entrar', 'a_pagar',
    'dias_fechamento', 'gastos_atuais', 'gastos_projetados', 'gastos_fixos',
    'gastos_variaveis', 'diario_max', 'fatura_master', 'fatura_visa',
    'parcelas', 'saldo_projetado', 'saude',
]


def _compute_custom_metrics(month_str, metricas_data):
    """
    Compute values for all active CustomMetrics for the given month.
    Takes already-computed metricas_data to avoid circular calls.
    """
    custom_metrics = CustomMetric.objects.filter(is_active=True).order_by('label')
    if not custom_metrics.exists():
        return []

    results = []

    for cm in custom_metrics:
        card_id = f'custom_{str(cm.id)}'
        value = 'R$ 0'
        subtitle = ''
        color = cm.color

        if cm.metric_type == 'category_total':
            cat_id = cm.config.get('category_id')
            if cat_id:
                spent_agg = Transaction.objects.filter(
                    month_str=month_str,
                    category_id=cat_id,
                    amount__lt=0,
                    is_internal_transfer=False,
                ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
                spent = abs(spent_agg)
                value = f'R$ {int(spent):,}'.replace(',', '.')
                subtitle = 'gasto na categoria'

        elif cm.metric_type == 'category_remaining':
            cat_id = cm.config.get('category_id')
            if cat_id:
                try:
                    cat = Category.objects.get(id=cat_id)
                except Category.DoesNotExist:
                    continue
                # Get budget (override or default)
                try:
                    bc = BudgetConfig.objects.get(category_id=cat_id, month_str=month_str)
                    limit = float(bc.limit_override)
                except BudgetConfig.DoesNotExist:
                    limit = float(cat.default_limit)

                spent_agg = Transaction.objects.filter(
                    month_str=month_str,
                    category_id=cat_id,
                    amount__lt=0,
                    is_internal_transfer=False,
                ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
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


def _get_all_known_card_ids():
    """Return set of all valid card IDs (builtin + active custom)."""
    custom_ids = [
        f'custom_{str(cid)}'
        for cid in CustomMetric.objects.filter(is_active=True)
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


def get_metricas_order(month_str):
    """
    Return the card order + hidden cards + lock status for a month.
    Resolution: per-month override > global default > hardcoded BUILTIN_CARD_ORDER.
    """
    all_known_ids = _get_all_known_card_ids()

    # Global default
    global_hidden = []
    try:
        global_cfg = MetricasOrderConfig.objects.get(month_str='__default__')
        global_order = list(global_cfg.card_order)
        global_hidden = list(global_cfg.hidden_cards or [])
    except MetricasOrderConfig.DoesNotExist:
        global_order = list(all_known_ids)

    global_order, global_hidden = _reconcile_order(
        global_order, global_hidden, all_known_ids
    )

    # Per-month override
    try:
        month_cfg = MetricasOrderConfig.objects.get(month_str=month_str)
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


def save_metricas_order(month_str, card_order, hidden_cards=None):
    """Save card order (and optionally hidden cards) for a specific month."""
    defaults = {'card_order': card_order}
    if hidden_cards is not None:
        defaults['hidden_cards'] = hidden_cards
    cfg, created = MetricasOrderConfig.objects.update_or_create(
        month_str=month_str,
        defaults=defaults,
    )
    return {
        'month_str': month_str,
        'card_order': cfg.card_order,
        'hidden_cards': cfg.hidden_cards,
    }


def make_default_order(card_order, hidden_cards=None):
    """
    Set card_order as the global default and delete all unlocked per-month
    overrides so they inherit the new default.
    """
    defaults = {'card_order': card_order}
    if hidden_cards is not None:
        defaults['hidden_cards'] = hidden_cards
    MetricasOrderConfig.objects.update_or_create(
        month_str='__default__',
        defaults=defaults,
    )
    deleted_count, _ = MetricasOrderConfig.objects.filter(
        is_locked=False
    ).exclude(
        month_str='__default__'
    ).delete()
    return {'global_default': card_order, 'months_reset': deleted_count}


def toggle_metricas_lock(month_str, locked):
    """Lock or unlock a month's metricas order."""
    if locked:
        order_data = get_metricas_order(month_str)
        cfg, _ = MetricasOrderConfig.objects.update_or_create(
            month_str=month_str,
            defaults={
                'card_order': order_data['card_order'],
                'hidden_cards': order_data['hidden_cards'],
                'is_locked': True,
            },
        )
    else:
        try:
            cfg = MetricasOrderConfig.objects.get(month_str=month_str)
            cfg.is_locked = False
            cfg.save(update_fields=['is_locked', 'updated_at'])
        except MetricasOrderConfig.DoesNotExist:
            pass
    return {'month_str': month_str, 'is_locked': locked}


def get_custom_metric_options():
    """Return active custom metrics + available categories for the picker UI."""
    metrics = CustomMetric.objects.filter(is_active=True).order_by('label')
    categories = list(
        Category.objects.filter(is_active=True)
        .order_by('display_order', 'name')
        .values('id', 'name', 'category_type', 'default_limit')
    )
    # Convert UUID to string for JSON
    for c in categories:
        c['id'] = str(c['id'])
        c['default_limit'] = float(c['default_limit'])

    return {
        'metrics': [{
            'id': str(m.id),
            'metric_type': m.metric_type,
            'label': m.label,
            'config': m.config,
            'color': m.color,
        } for m in metrics],
        'available_categories': categories,
    }


def create_custom_metric(metric_type, label, config, color='var(--color-accent)'):
    """Create a new custom metric definition."""
    cm = CustomMetric.objects.create(
        metric_type=metric_type,
        label=label,
        config=config,
        color=color,
    )
    card_id = f'custom_{str(cm.id)}'
    # Append to all existing order configs
    for cfg in MetricasOrderConfig.objects.all():
        if card_id not in cfg.card_order:
            cfg.card_order.append(card_id)
            cfg.save(update_fields=['card_order'])
    return {'id': str(cm.id), 'card_id': card_id, 'label': cm.label}


def delete_custom_metric(metric_id):
    """Delete a custom metric and remove from all order configs."""
    cm = CustomMetric.objects.get(id=metric_id)
    card_id = f'custom_{str(cm.id)}'
    cm.delete()
    for cfg in MetricasOrderConfig.objects.all():
        if card_id in cfg.card_order:
            cfg.card_order.remove(card_id)
            cfg.save(update_fields=['card_order'])
    return {'deleted': True, 'card_id': card_id}


# ---------------------------------------------------------------------------
# Card transactions
# ---------------------------------------------------------------------------

def get_card_transactions(month_str, account_filter=None):
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
    ).select_related('account', 'category', 'subcategory').order_by('-date')

    if not qs.exists():
        qs = Transaction.objects.filter(
            month_str=month_str,
            invoice_month='',
            account__account_type='credit_card',
        ).select_related('account', 'category', 'subcategory').order_by('-date')

    if account_filter:
        qs = qs.filter(account__name__icontains=account_filter)

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
            'subcategory': txn.subcategory.name if txn.subcategory else '',
            'parcela': parcela,
            'is_installment': txn.is_installment,
        })

    return {
        'month_str': month_str,
        'transactions': results,
        'count': len(results),
        'total': float(sum(r['amount'] for r in results)),
    }


def get_installment_details(month_str):
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
    ).select_related('account', 'category', 'subcategory')

    if not real_installments.exists():
        real_installments = Transaction.objects.filter(
            month_str=month_str,
            invoice_month='',
            is_installment=True,
            amount__lt=0,
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
                    'date': txn.date.strftime('%Y-%m-%d'),
                    'description': txn.description,
                    'amount': float(abs(txn.amount)),
                    'account': txn.account.name if txn.account else '',
                    'category': txn.category.name if txn.category else 'Não categorizado',
                    'subcategory': txn.subcategory.name if txn.subcategory else '',
                    'parcela': txn.installment_info or '',
                    'source_month': month_str,
                })

        # Build items from deduplicated purchase groups (lowest position only)
        items = []
        for (base_desc, acct, amt, total_inst), (current, _, txn) in purchase_groups.items():
            parcela_str = f'{current}/{total_inst}'
            items.append({
                'date': txn.date.strftime('%Y-%m-%d'),
                'description': f'{base_desc} {parcela_str}',
                'amount': amt,
                'account': acct,
                'category': txn.category.name if txn.category else 'Não categorizado',
                'subcategory': txn.subcategory.name if txn.subcategory else '',
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

    for lookback in range(1, 13):
        source_month = _month_str_add(month_str, -lookback)
        # Prefer invoice_month; fall back to month_str for older imports
        inst_txns = Transaction.objects.filter(
            invoice_month=source_month,
            is_installment=True,
            amount__lt=0,
        ).select_related('account', 'category', 'subcategory')
        if not inst_txns.exists():
            inst_txns = Transaction.objects.filter(
                month_str=source_month,
                invoice_month='',
                is_installment=True,
                amount__lt=0,
            ).select_related('account', 'category', 'subcategory')
        if not inst_txns.exists():
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
                'date': projected_date.strftime('%Y-%m-%d'),
                'description': projected_desc,
                'amount': amt,
                'account': acct,
                'category': txn.category.name if txn.category else 'Não categorizado',
                'subcategory': txn.subcategory.name if txn.subcategory else '',
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
# Mapping candidates + map/unmap
# ---------------------------------------------------------------------------

def get_mapping_candidates(month_str, category_id=None, mapping_id=None):
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
        mapping = RecurringMapping.objects.select_related('category').get(id=mapping_id)
        cat = mapping.category
        expected = float(mapping.expected_amount)
        cat_name = mapping.custom_name if mapping.is_custom else (cat.name if cat else '?')
    elif category_id:
        cat = Category.objects.get(id=category_id)
        expected = float(cat.default_limit)
        cat_name = cat.name
        # Look up the mapping for this category+month (if it exists)
        mapping = RecurringMapping.objects.filter(
            category=cat, month_str=month_str
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
        Q(invoice_month=month_str, account__account_type='credit_card')
    ).select_related('account', 'category').order_by('-date').distinct()

    prior_qs = Transaction.objects.filter(
        Q(month_str=prev_month_str, account__account_type='checking') |
        Q(month_str=prev_month_str, account__account_type='manual')
    ).select_related('account', 'category').order_by('-date').distinct()

    # Build set of transactions already cross-month-moved to ANY mapping
    # (so they show as greyed out / "moved to X" in the prior month pool)
    cross_month_moved_ids = set()
    cross_month_target = {}  # txn_id -> target month_str
    for cm in RecurringMapping.objects.filter(
        month_str=month_str,
    ).prefetch_related('cross_month_transactions'):
        for t in cm.cross_month_transactions.all():
            cross_month_moved_ids.add(str(t.id))
            cross_month_target[str(t.id)] = month_str

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


def map_transaction_to_category(transaction_id, category_id=None, mapping_id=None):
    """
    Map a transaction to a recurring category or custom mapping.
    Updates the transaction's category FK and marks it as manually categorized.
    Adds the transaction to the mapping's M2M transactions set.
    Sets match_mode to 'manual' and recomputes actual_amount from all linked txns.

    Accepts either category_id (for category-based items) or mapping_id
    (for custom items without a category).
    """
    txn = Transaction.objects.select_related('account').get(id=transaction_id)

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
        # Recompute actual from all linked transactions
        total = sum(abs(t.amount) for t in mapping.transactions.all())
        mapping.actual_amount = total
        mapping.status = 'mapped'
        mapping.save()

    if mapping_id:
        mapping = RecurringMapping.objects.select_related('category').get(id=mapping_id)
        if mapping.category:
            txn.category = mapping.category
        txn.is_manually_categorized = True
        txn.save()
        _update_mapping(mapping)
        cat_name = mapping.custom_name if mapping.is_custom else (
            mapping.category.name if mapping.category else '?'
        )
        return {
            'transaction_id': str(txn.id),
            'mapping_id': str(mapping.id),
            'category_name': cat_name,
            'description': txn.description,
            'amount': float(txn.amount),
        }
    elif category_id:
        cat = Category.objects.get(id=category_id)
        txn.category = cat
        txn.is_manually_categorized = True
        txn.save()
        try:
            mapping = RecurringMapping.objects.get(
                category=cat,
                month_str=txn.month_str,
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


def unmap_transaction(transaction_id, mapping_id=None):
    """
    Remove a transaction from a recurring mapping's linked set.
    If mapping_id is given, remove from that specific mapping.
    Otherwise, find by category + month (legacy behavior).
    Resets transaction category to 'Não categorizado'.
    """
    txn = Transaction.objects.get(id=transaction_id)
    old_category = txn.category
    old_month = txn.month_str

    # Find or get the "Não categorizado" category
    uncat = Category.objects.filter(name='Não categorizado').first()
    txn.category = uncat
    txn.is_manually_categorized = False
    txn.save()

    # Find the mapping to unlink from
    mapping = None
    if mapping_id:
        try:
            mapping = RecurringMapping.objects.get(id=mapping_id)
        except RecurringMapping.DoesNotExist:
            pass
    elif old_category:
        try:
            mapping = RecurringMapping.objects.get(
                category=old_category,
                month_str=old_month,
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
            # Recompute actual from remaining linked transactions
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

def get_variable_transactions(month_str):
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


def _compute_installment_schedule(target_month_str, num_future_months=6):
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

    # Step 1: Check which target months have real CC statement data
    months_with_real_data = set()
    for offset in range(num_future_months + 1):
        check_month = _month_str_add(target_month_str, offset)
        # Prefer invoice_month; fall back to month_str for older imports
        inst_txns = Transaction.objects.filter(
            invoice_month=check_month,
            is_installment=True,
            amount__lt=0,
        ).select_related('account')
        if not inst_txns.exists():
            inst_txns = Transaction.objects.filter(
                month_str=check_month,
                invoice_month='',
                is_installment=True,
                amount__lt=0,
            ).select_related('account')
        if not inst_txns.exists():
            continue

        # Group by purchase, keep only the lowest position per group
        purchase_groups = {}
        non_parseable_total = 0.0
        for txn in inst_txns:
            info = txn.installment_info or ''
            m_match = re.match(r'(\d+)/(\d+)', info)
            if not m_match:
                dm = re.search(r'(\d{1,2})/(\d{1,2})', txn.description)
                if dm:
                    m_match = dm
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

        # Sum only the deduplicated amounts (one per purchase)
        deduped_total = sum(amt for (_, _, amt, _) in purchase_groups.keys())
        real_total = deduped_total + non_parseable_total
        if real_total > 0:
            schedule[check_month] = real_total
            months_with_real_data.add(check_month)

    # Step 2: Project for months WITHOUT real data from older statements.
    # Scan invoice_month-based statements, group by purchase, keep lowest
    # position, and project forward.
    seen_per_month = {}  # check_month -> set of purchase_id

    for lookback in range(1, 13):
        source_month = _month_str_add(target_month_str, -lookback)
        # Check invoice_month first; fall back to month_str for older imports
        inst_txns = Transaction.objects.filter(
            invoice_month=source_month,
            is_installment=True,
            amount__lt=0,
        ).select_related('account')
        if not inst_txns.exists():
            inst_txns = Transaction.objects.filter(
                month_str=source_month,
                invoice_month='',
                is_installment=True,
                amount__lt=0,
            ).select_related('account')
        if not inst_txns.exists():
            continue

        # Group by purchase, keep lowest position per source statement
        purchase_groups = {}
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
            amt = round(float(abs(txn.amount)), 2)
            base_desc = re.sub(r'\s*\d{1,2}/\d{1,2}\s*$', '', txn.description).strip()
            acct = txn.account.name if txn.account else ''

            group_key = (base_desc, acct, amt, total_inst)
            if group_key not in purchase_groups or current < purchase_groups[group_key]:
                purchase_groups[group_key] = current

        # Project each unique purchase forward
        for (base_desc, acct, amt, total_inst), current in purchase_groups.items():
            purchase_id = (base_desc, acct, amt, total_inst)

            for target_offset in range(num_future_months + 1):
                check_month = _month_str_add(target_month_str, target_offset)
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


def get_last_installment_month():
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


def get_projection(start_month_str, num_months=6):
    """
    PROJEÇÃO — Forward-looking financial projection.

    Starting from the balance override of start_month_str, projects
    income, fixed expenses, installments, and variable budget for
    each of the next num_months months.

    For the current month: uses actual RecurringMapping expected amounts.
    For future months: uses Category defaults / BudgetConfig overrides.
    Installments: parses "N/M" info to calculate remaining months.

    Returns per-month: income, fixo, installments, variable_budget,
    net, cumulative balance.
    """
    import re

    # Starting balance
    try:
        bo = BalanceOverride.objects.get(month_str=start_month_str)
        starting_balance = float(bo.balance)
    except BalanceOverride.DoesNotExist:
        starting_balance = 0.0

    # Category defaults
    cats = Category.objects.filter(is_active=True)
    income_cats = cats.filter(category_type='Income')
    fixo_cats = cats.filter(category_type='Fixo')
    invest_cats = cats.filter(category_type='Investimento')
    variable_cats = cats.filter(category_type='Variavel', default_limit__gt=0)

    total_income_default = float(
        income_cats.aggregate(t=Sum('default_limit'))['t'] or 0
    )
    total_fixo_default = float(
        fixo_cats.aggregate(t=Sum('default_limit'))['t'] or 0
    )
    total_invest_default = float(
        invest_cats.aggregate(t=Sum('default_limit'))['t'] or 0
    )
    total_variable_default = float(
        variable_cats.aggregate(t=Sum('default_limit'))['t'] or 0
    )

    # Active installments — compute from all recent CC statements
    installment_schedule = _compute_installment_schedule(
        start_month_str, num_future_months=num_months
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
            ).exclude(status='skipped').select_related('category')

            income = 0.0
            fixo = 0.0
            invest = 0.0
            for mp in mappings:
                cat_type = mp.custom_type if mp.is_custom else (
                    mp.category.category_type if mp.category else ''
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

def get_orcamento(month_str):
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
    ).order_by('display_order', 'name')

    # 6-month lookback for averages
    lookback_months = []
    for i in range(1, 7):
        lookback_months.append(_month_str_add(month_str, -i))

    categories = []
    total_limit = 0.0
    total_spent = 0.0

    for cat in variable_cats:
        # BudgetConfig override for this month
        try:
            bc = BudgetConfig.objects.get(category=cat, month_str=month_str)
            limit = float(bc.limit_override)
        except BudgetConfig.DoesNotExist:
            limit = float(cat.default_limit)

        # Current month spending (exclude internal transfers)
        spent_agg = Transaction.objects.filter(
            month_str=month_str,
            category=cat,
            amount__lt=0,
            is_internal_transfer=False,
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        spent = float(abs(spent_agg))

        # 6-month average (exclude internal transfers)
        avg_agg = Transaction.objects.filter(
            month_str__in=lookback_months,
            category=cat,
            amount__lt=0,
            is_internal_transfer=False,
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        avg_total = float(abs(avg_agg))
        # Count how many of the lookback months actually have data
        months_with_data = Transaction.objects.filter(
            month_str__in=lookback_months,
            category=cat,
            amount__lt=0,
            is_internal_transfer=False,
        ).values('month_str').distinct().count()
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


def smart_categorize(month_str=None, dry_run=False):
    """
    Apply smart categorization to uncategorized transactions.

    Strategy (in priority order):
    1. Rule-based: Apply existing CategorizationRule patterns
    2. Exact-match learning: If a description has been manually categorized
       in the past, apply the same category
    3. Token-similarity learning: If the normalized tokens of a description
       are similar to a past manually-categorized transaction, suggest that category
    4. Amount-pattern learning: For checking account recurring payments,
       match by similar amounts to past categorized transactions

    Args:
        month_str: Optional month to limit scope. If None, processes all months.
        dry_run: If True, returns what would be changed without saving.

    Returns:
        dict with categorized count and details.
    """
    nao_cat = Category.objects.filter(name='Não categorizado').first()
    if not nao_cat:
        return {'categorized': 0, 'details': [], 'error': 'No uncategorized category found'}

    # Get uncategorized transactions
    qs = Transaction.objects.filter(
        category=nao_cat,
        is_internal_transfer=False,
    ).select_related('account', 'category')
    if month_str:
        qs = qs.filter(month_str=month_str)

    uncategorized = list(qs)
    if not uncategorized:
        return {'categorized': 0, 'details': [], 'message': 'No uncategorized transactions'}

    # Build learning corpus from manually categorized transactions
    manual_txns = Transaction.objects.filter(
        is_manually_categorized=True,
    ).exclude(
        category=nao_cat,
    ).select_related('category')

    # Also use rule-categorized transactions (high confidence)
    rule_txns = Transaction.objects.filter(
        is_manually_categorized=False,
        is_internal_transfer=False,
    ).exclude(
        category=nao_cat,
    ).exclude(
        category__isnull=True,
    ).select_related('category')

    # Build description -> category mapping from manual categorizations
    desc_to_category = {}  # normalized_desc -> {category_id: count}
    for txn in manual_txns:
        norm = _normalize_description(txn.description)
        if norm not in desc_to_category:
            desc_to_category[norm] = Counter()
        desc_to_category[norm][txn.category_id] += 1

    # Build token -> category mapping for fuzzy matching
    token_to_category = {}  # token -> {category_id: count}
    for txn in list(manual_txns) + list(rule_txns[:2000]):  # Limit rule-based corpus
        if txn.category_id == nao_cat.id:
            continue
        tokens = _extract_tokens(txn.description)
        for token in tokens:
            if token not in token_to_category:
                token_to_category[token] = Counter()
            token_to_category[token][txn.category_id] += 1

    # Load active categorization rules
    rules = CategorizationRule.objects.filter(
        is_active=True,
    ).select_related('category').order_by('-priority')

    # Category lookup
    cat_lookup = {c.id: c for c in Category.objects.filter(is_active=True)}

    results = []

    for txn in uncategorized:
        desc_upper = txn.description.upper()
        matched_category = None
        match_method = None
        confidence = 0.0

        # Strategy 1: Rule-based matching
        for rule in rules:
            if rule.keyword.upper() in desc_upper:
                matched_category = rule.category
                match_method = 'rule'
                confidence = 1.0
                break

        # Strategy 2: Exact description match from manual categorizations
        if not matched_category:
            norm = _normalize_description(txn.description)
            if norm in desc_to_category:
                cat_counts = desc_to_category[norm]
                if cat_counts:
                    best_cat_id = cat_counts.most_common(1)[0][0]
                    if best_cat_id in cat_lookup:
                        matched_category = cat_lookup[best_cat_id]
                        match_method = 'exact_learning'
                        confidence = 0.95

        # Strategy 3: Token similarity matching
        if not matched_category:
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
                    # Require at least 2 matching tokens or a strong single token
                    matching_tokens = sum(1 for t in tokens if t in token_to_category)
                    if matching_tokens >= 2 or best_score >= 5:
                        matched_category = cat_lookup[best_cat_id]
                        match_method = 'token_learning'
                        confidence = min(0.9, 0.5 + matching_tokens * 0.1)

        if matched_category:
            results.append({
                'transaction_id': str(txn.id),
                'description': txn.description,
                'amount': float(txn.amount),
                'account': txn.account.name if txn.account else '',
                'new_category': matched_category.name,
                'new_category_id': str(matched_category.id),
                'method': match_method,
                'confidence': confidence,
            })

            if not dry_run:
                txn.category = matched_category
                txn.save(update_fields=['category', 'updated_at'])

    return {
        'categorized': len(results),
        'total_uncategorized': len(uncategorized),
        'details': results[:100],  # Limit response size
        'dry_run': dry_run,
    }


# ---------------------------------------------------------------------------
# Auto-link recurring items
# ---------------------------------------------------------------------------

def auto_link_recurring(month_str):
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
    ).exclude(
        status__in=['skipped', 'mapped'],
    ).select_related('category', 'transaction').prefetch_related('transactions')

    # Only process items with no linked transactions
    unlinked = [m for m in mappings if m.transactions.count() == 0 and not m.transaction]

    if not unlinked:
        return {'linked': 0, 'details': [], 'message': 'No unlinked items to process'}

    # Get all transactions for this month
    all_txns = Transaction.objects.filter(
        month_str=month_str,
    ).select_related('account', 'category')

    income_txns = list(all_txns.filter(amount__gt=0))
    expense_txns = list(all_txns.filter(amount__lt=0))

    # Build set of already-linked transaction IDs (across ALL mappings this month)
    already_linked = set()
    all_mappings = RecurringMapping.objects.filter(month_str=month_str).prefetch_related('transactions')
    for m in all_mappings:
        for t in m.transactions.all():
            already_linked.add(t.id)
        if m.transaction_id:
            already_linked.add(m.transaction_id)

    # Get previous month's links for pattern matching
    prev_month = _month_str_add(month_str, -1)
    prev_mappings = RecurringMapping.objects.filter(
        month_str=prev_month,
    ).select_related('category').prefetch_related('transactions')

    prev_links = {}  # category_id -> list of (description_normalized, amount)
    for pm in prev_mappings:
        cat_id = pm.category_id
        if not cat_id:
            continue
        linked = list(pm.transactions.all())
        if linked:
            prev_links[cat_id] = [
                (_normalize_description(t.description), float(abs(t.amount)))
                for t in linked
            ]
        elif pm.transaction:
            prev_links[cat_id] = [
                (_normalize_description(pm.transaction.description), float(abs(pm.transaction.amount)))
            ]

    results = []

    for mapping in unlinked:
        cat_type = mapping.custom_type if mapping.is_custom else (
            mapping.category.category_type if mapping.category else ''
        )
        name = mapping.custom_name if mapping.is_custom else (
            mapping.category.name if mapping.category else '?'
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
        cat_id = mapping.category_id
        if cat_id and cat_id in prev_links:
            for prev_desc, prev_amt in prev_links[cat_id]:
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

def reapply_template_to_month(month_str):
    """
    Delete all existing RecurringMapping rows for the month and re-initialize
    from the current Category template. This lets the user reset a month's
    recurring items after editing the template.
    """
    deleted_count = RecurringMapping.objects.filter(month_str=month_str).delete()[0]
    result = initialize_month(month_str)
    result['deleted'] = deleted_count
    return result


# ---------------------------------------------------------------------------
# Month Categories (for TransactionPicker category matching)
# ---------------------------------------------------------------------------

def get_month_categories(month_str):
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
# Checking Account Transactions
# ---------------------------------------------------------------------------

def get_checking_transactions(month_str):
    """
    Fetch all checking account transactions for a given month.
    Returns transactions grouped with summary totals.
    Cross-month-moved transactions are flagged (greyed out in UI).
    """
    txns = Transaction.objects.filter(
        month_str=month_str,
        account__account_type='checking',
    ).select_related('account', 'category').order_by('date')

    # Find cross-month-moved transaction IDs for this month
    cross_month_moved = {}
    other_month_mappings = RecurringMapping.objects.exclude(
        month_str=month_str
    ).prefetch_related('cross_month_transactions')
    for om in other_month_mappings:
        for ct in om.cross_month_transactions.filter(month_str=month_str):
            cross_month_moved[str(ct.id)] = om.month_str

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
            'is_internal_transfer': t.is_internal_transfer,
            'is_recurring': t.is_recurring,
            'moved_to_month': moved_to,
        })

    return {
        'month_str': month_str,
        'transactions': items,
        'count': len(items),
        'total_in': round(total_in, 2),
        'total_out': round(total_out, 2),
        'net': round(total_in + total_out, 2),
    }
