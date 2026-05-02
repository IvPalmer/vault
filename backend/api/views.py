import logging
import os
import re
import subprocess

from django.db import models
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

logger = logging.getLogger(__name__)

MONTH_STR_RE = re.compile(r'^\d{4}-(?:0[1-9]|1[0-2])$')


def _safe_error_response(e, context='', status_code=status.HTTP_400_BAD_REQUEST):
    """Return a generic error response, logging the full exception.

    Avoids leaking internal error details to the client.
    """
    logger.exception(f'{context} error' if context else 'Unexpected error')
    if os.getenv('DEBUG', '0') == '1':
        return Response({'error': str(e)}, status=status_code)
    return Response({'error': 'An unexpected error occurred'}, status=status_code)


def _sanitize_applescript_string(s):
    """Sanitize a string for safe interpolation into AppleScript.

    Strips characters that could escape the string context:
    backslashes, double quotes, and AppleScript string concatenation.
    """
    if not s:
        return ''
    # Remove backslashes first, then double quotes
    sanitized = s.replace('\\', '').replace('"', '')
    # Remove any ampersands that could be used for string concatenation injection
    sanitized = sanitized.replace('&', '')
    # Strip control characters
    sanitized = re.sub(r'[\x00-\x1f\x7f]', '', sanitized)
    # Limit length to prevent abuse
    return sanitized[:500]


def _validate_month_str(month_str):
    """Validate month_str format (YYYY-MM). Returns error Response or None."""
    if not month_str:
        return Response({'error': 'month_str required'}, status=status.HTTP_400_BAD_REQUEST)
    if not MONTH_STR_RE.match(month_str):
        return Response(
            {'error': f'Invalid month_str format: {month_str}. Expected YYYY-MM.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return None

from .models import (
    Account, Category, Subcategory, CategorizationRule,
    PluggyCategoryMapping, RenameRule, Transaction, RecurringMapping,
    RecurringTemplate, BudgetConfig, BalanceOverride, Profile,
    BankTemplate, SetupTemplate, FamilyNote, SalaryConfig,
    GoogleAccount, CalendarSelection,
    Project, PersonalTask, PersonalNote,
    HealthExam, VitalReading, Pregnancy, PrenatalConsultation,
)
from .serializers import (
    AccountSerializer, CategorySerializer, SubcategorySerializer,
    CategorizationRuleSerializer, PluggyCategoryMappingSerializer,
    RenameRuleSerializer,
    TransactionSerializer, TransactionListSerializer,
    RecurringMappingSerializer, RecurringTemplateSerializer,
    BudgetConfigSerializer, BalanceOverrideSerializer,
    ProfileSerializer, BankTemplateSerializer, SetupTemplateSerializer,
    FamilyNoteSerializer,
    GoogleAccountSerializer, CalendarSelectionSerializer,
    ProjectSerializer, PersonalTaskSerializer, PersonalNoteSerializer,
    HealthExamSerializer, VitalReadingSerializer,
    PregnancySerializer, PrenatalConsultationSerializer,
)
from .services import (
    get_metricas,
    get_recurring_data, get_card_transactions, get_variable_transactions,
    get_mapping_candidates, map_transaction_to_category, unmap_transaction,
    initialize_month, update_recurring_expected, update_recurring_item,
    add_custom_recurring, delete_custom_recurring,
    skip_recurring, unskip_recurring, save_balance_override,
    get_projection, get_orcamento,
    smart_categorize, get_installment_details,
    get_recurring_templates, update_recurring_template,
    create_recurring_template, delete_recurring_template,
    get_last_installment_month,
    reapply_template_to_month,
    get_checking_transactions,
    get_month_categories,
    auto_link_recurring,
    get_metricas_order, save_metricas_order, make_default_order,
    toggle_metricas_lock, get_custom_metric_options,
    create_custom_metric, delete_custom_metric,
    find_similar_transactions, rename_transaction,
    categorize_installment_siblings,
    get_analytics_trends,
    get_spending_insights,
    analyze_statements_for_setup,
    compute_salary_projection,
    sync_salary_to_budget,
)
from .models import CustomMetric, MetricasOrderConfig, CategorizationRule


class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    pagination_class = None

    @action(detail=True, methods=['post'])
    def clone(self, request, pk=None):
        """Clone this profile's config (categories, rules, templates) to a new profile."""
        source = self.get_object()
        new_name = request.data.get('name')
        if not new_name:
            return Response({'error': 'name required'}, status=status.HTTP_400_BAD_REQUEST)

        from .models import Category, CategorizationRule, RenameRule, RecurringTemplate
        new_profile = Profile.objects.create(name=new_name)

        # Clone categories (need old->new ID mapping for rules)
        cat_map = {}
        for cat in Category.objects.filter(profile=source):
            old_id = cat.id
            cat.pk = None
            cat.id = None
            cat.profile = new_profile
            cat.save()
            cat_map[old_id] = cat

        # Clone categorization rules
        rules_count = 0
        for rule in CategorizationRule.objects.filter(profile=source):
            new_cat = cat_map.get(rule.category_id)
            if new_cat:
                rule.pk = None
                rule.id = None
                rule.profile = new_profile
                rule.category = new_cat
                rule.subcategory = None  # subcategories need separate cloning
                rule.save()
                rules_count += 1

        # Clone rename rules
        renames_count = 0
        for rr in RenameRule.objects.filter(profile=source):
            rr.pk = None
            rr.id = None
            rr.profile = new_profile
            rr.save()
            renames_count += 1

        # Clone recurring templates
        templates_count = 0
        for tpl in RecurringTemplate.objects.filter(profile=source):
            tpl.pk = None
            tpl.id = None
            tpl.profile = new_profile
            tpl.save()
            templates_count += 1

        return Response({
            'profile': ProfileSerializer(new_profile).data,
            'cloned': {
                'categories': len(cat_map),
                'rules': rules_count,
                'renames': renames_count,
                'templates': templates_count,
            }
        }, status=status.HTTP_201_CREATED)


class BankTemplateViewSet(viewsets.ModelViewSet):
    """Bank configuration templates — system-wide, not profile-scoped."""
    queryset = BankTemplate.objects.all()
    serializer_class = BankTemplateSerializer
    pagination_class = None


class AccountViewSet(viewsets.ModelViewSet):
    serializer_class = AccountSerializer
    filterset_fields = ['account_type']
    pagination_class = None

    def get_queryset(self):
        return Account.objects.filter(profile=self.request.profile)

    def perform_create(self, serializer):
        serializer.save(profile=self.request.profile)


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    filterset_fields = ['category_type', 'is_active']
    search_fields = ['name']
    pagination_class = None  # Always return full list (used as dropdown data)

    def get_queryset(self):
        qs = Category.objects.filter(profile=self.request.profile)
        # Default to active-only unless explicitly requested
        if 'is_active' not in self.request.query_params:
            qs = qs.filter(is_active=True)
        return qs

    def perform_create(self, serializer):
        serializer.save(profile=self.request.profile)


class SubcategoryViewSet(viewsets.ModelViewSet):
    serializer_class = SubcategorySerializer
    filterset_fields = ['category']
    pagination_class = None

    def get_queryset(self):
        return Subcategory.objects.filter(profile=self.request.profile)

    def perform_create(self, serializer):
        serializer.save(profile=self.request.profile)


class CategoryTreeView(APIView):
    """GET /api/categories/tree/ — Full category tree with transaction counts and Pluggy mapping info."""

    def get(self, request):
        profile = request.profile
        cats = Category.objects.filter(profile=profile, is_active=True).order_by('name')
        subs = Subcategory.objects.filter(profile=profile, category__in=cats)
        pluggy_maps = PluggyCategoryMapping.objects.filter(profile=profile).select_related('category', 'subcategory')

        # Count transactions per category and subcategory
        from django.db.models import Count
        cat_counts = dict(
            Transaction.objects.filter(profile=profile, category__in=cats)
            .values_list('category_id')
            .annotate(cnt=Count('id'))
            .values_list('category_id', 'cnt')
        )
        sub_counts = dict(
            Transaction.objects.filter(profile=profile, subcategory__in=subs)
            .values_list('subcategory_id')
            .annotate(cnt=Count('id'))
            .values_list('subcategory_id', 'cnt')
        )
        # Uncategorized count
        uncat_count = Transaction.objects.filter(profile=profile, category__isnull=True).count()
        # Transactions with category but no subcategory
        no_sub_counts = dict(
            Transaction.objects.filter(profile=profile, category__in=cats, subcategory__isnull=True)
            .values_list('category_id')
            .annotate(cnt=Count('id'))
            .values_list('category_id', 'cnt')
        )

        # Index pluggy mappings by category and subcategory
        pluggy_by_cat = {}
        pluggy_by_sub = {}
        for pm in pluggy_maps:
            pluggy_by_cat.setdefault(pm.category_id, []).append({
                'id': str(pm.id),
                'pluggy_id': pm.pluggy_category_id,
                'pluggy_name': pm.pluggy_category_name,
                'subcategory_id': str(pm.subcategory_id) if pm.subcategory_id else None,
            })
            if pm.subcategory_id:
                pluggy_by_sub.setdefault(pm.subcategory_id, []).append({
                    'id': str(pm.id),
                    'pluggy_id': pm.pluggy_category_id,
                    'pluggy_name': pm.pluggy_category_name,
                })

        # Build tree
        tree = []
        for cat in cats:
            cat_subs = []
            for sub in subs:
                if sub.category_id != cat.id:
                    continue
                cat_subs.append({
                    'id': str(sub.id),
                    'name': sub.name,
                    'transaction_count': sub_counts.get(sub.id, 0),
                    'pluggy_mappings': pluggy_by_sub.get(sub.id, []),
                })
            cat_subs.sort(key=lambda s: s['name'])
            tree.append({
                'id': str(cat.id),
                'name': cat.name,
                'category_type': cat.category_type,
                'transaction_count': cat_counts.get(cat.id, 0),
                'no_subcategory_count': no_sub_counts.get(cat.id, 0),
                'pluggy_mappings': pluggy_by_cat.get(cat.id, []),
                'subcategories': cat_subs,
            })

        return Response({
            'categories': tree,
            'uncategorized_count': uncat_count,
        })


class CategoryBulkReassignView(APIView):
    """POST /api/categories/bulk-reassign/ — Move transactions between categories/subcategories.
       GET  /api/categories/bulk/ — Browse all transactions with search/filter + installment grouping.
    """

    def get(self, request):
        """List all transactions with search, category/account filters, installment grouping."""
        import re as _re
        from .services import _extract_base_desc

        profile = request.profile
        search = request.query_params.get('search', '').strip()
        cat_id = request.query_params.get('category_id', '')
        sub_id = request.query_params.get('subcategory_id', '')
        account_id = request.query_params.get('account_id', '')
        date_from = request.query_params.get('date_from', '')
        date_to = request.query_params.get('date_to', '')
        uncat_only = request.query_params.get('uncategorized', '') == '1'
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 100))

        qs = Transaction.objects.filter(profile=profile).select_related(
            'account', 'category', 'subcategory'
        )

        if search:
            qs = qs.filter(description__icontains=search)
        if uncat_only:
            qs = qs.filter(category__isnull=True)
        elif sub_id:
            qs = qs.filter(subcategory_id=sub_id)
        elif cat_id:
            qs = qs.filter(category_id=cat_id)
        no_sub = request.query_params.get('no_subcategory', '') == '1'
        if no_sub:
            qs = qs.filter(subcategory__isnull=True)
        if account_id:
            qs = qs.filter(account_id=account_id)
        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)

        qs = qs.order_by('-date', '-id')

        # Fetch all matching for accurate grouping and count
        all_txns = list(qs[:5000])

        # Group installments — only credit card transactions, collapse sibling positions
        seen_groups = {}
        grouped = []
        inst_collapsed = {}  # txn.id -> number of siblings collapsed (including self)

        for t in all_txns:
            if t.is_installment and t.account and t.account.account_type == 'credit_card':
                m = _re.search(r'(\d{1,2})/(\d{1,2})', t.description)
                if not m and t.installment_info:
                    m = _re.match(r'(\d+)/(\d+)', t.installment_info)
                if m:
                    total = int(m.group(2))
                    base = _extract_base_desc(t.description)
                    key = (base, t.account_id, round(float(abs(t.amount)), 1), total)
                    if key in seen_groups:
                        rep_id = seen_groups[key]
                        inst_collapsed[rep_id] = inst_collapsed.get(rep_id, 1) + 1
                        continue
                    seen_groups[key] = t.id
                    inst_collapsed[t.id] = 1
            grouped.append(t)

        total_count = len(grouped)
        start = (page - 1) * page_size
        page_txns = grouped[start:start + page_size]

        # Get unique accounts for filter dropdown
        accounts = list(
            Transaction.objects.filter(profile=profile)
            .values_list('account__id', 'account__name')
            .distinct()
            .order_by('account__name')
        )

        return Response({
            'transactions': [{
                'id': str(t.id),
                'date': str(t.date),
                'description': t.description,
                'amount': float(t.amount),
                'account': t.account.name if t.account else '',
                'account_id': str(t.account_id) if t.account_id else '',
                'category_id': str(t.category_id) if t.category_id else None,
                'category_name': t.category.name if t.category else None,
                'subcategory_id': str(t.subcategory_id) if t.subcategory_id else None,
                'subcategory_name': t.subcategory.name if t.subcategory else None,
                'is_installment': t.is_installment,
                'installment_total': inst_collapsed.get(t.id, 0),
            } for t in page_txns],
            'total': total_count,
            'page': page,
            'page_size': page_size,
            'accounts': [{'id': str(a[0]), 'name': a[1]} for a in accounts if a[0]],
        })

    def post(self, request):
        profile = request.profile
        action = request.data.get('action')  # 'reassign_category', 'reassign_subcategory', 'clear_subcategory'

        if action == 'reassign_subcategory':
            # Move transactions from one subcategory to another (can be cross-category)
            from_sub_id = request.data.get('from_subcategory_id')
            to_sub_id = request.data.get('to_subcategory_id')
            to_cat_id = request.data.get('to_category_id')

            if not from_sub_id or not to_sub_id:
                return Response({'error': 'from_subcategory_id and to_subcategory_id required'}, status=400)

            from_sub = Subcategory.objects.get(id=from_sub_id, profile=profile)
            to_sub = Subcategory.objects.get(id=to_sub_id, profile=profile)
            to_cat = to_sub.category

            count = Transaction.objects.filter(
                profile=profile, subcategory=from_sub
            ).update(subcategory=to_sub, category=to_cat)

            # Update pluggy mappings pointing to old subcategory
            PluggyCategoryMapping.objects.filter(
                profile=profile, subcategory=from_sub
            ).update(subcategory=to_sub, category=to_cat)

            return Response({'updated': count, 'action': action})

        elif action == 'reassign_category':
            # Move ALL transactions from one category to another (keeps subcategory names, creates if needed)
            from_cat_id = request.data.get('from_category_id')
            to_cat_id = request.data.get('to_category_id')

            if not from_cat_id or not to_cat_id:
                return Response({'error': 'from_category_id and to_category_id required'}, status=400)

            from_cat = Category.objects.get(id=from_cat_id, profile=profile)
            to_cat = Category.objects.get(id=to_cat_id, profile=profile)

            # Map subcategories: for each sub in from_cat, find or create matching in to_cat
            sub_map = {}
            for from_sub in Subcategory.objects.filter(category=from_cat):
                to_sub, _ = Subcategory.objects.get_or_create(
                    name=from_sub.name, category=to_cat,
                    defaults={'profile': profile}
                )
                sub_map[from_sub.id] = to_sub

            # Reassign transactions
            count = 0
            for from_sub_id, to_sub in sub_map.items():
                count += Transaction.objects.filter(
                    profile=profile, subcategory_id=from_sub_id
                ).update(subcategory=to_sub, category=to_cat)

            # Transactions with category but no subcategory
            count += Transaction.objects.filter(
                profile=profile, category=from_cat, subcategory__isnull=True
            ).update(category=to_cat)

            # Update pluggy mappings
            for from_sub_id, to_sub in sub_map.items():
                PluggyCategoryMapping.objects.filter(
                    profile=profile, subcategory_id=from_sub_id
                ).update(subcategory=to_sub, category=to_cat)
            PluggyCategoryMapping.objects.filter(
                profile=profile, category=from_cat, subcategory__isnull=True
            ).update(category=to_cat)

            return Response({'updated': count, 'action': action})

        elif action == 'merge_subcategories':
            # Merge source into target subcategory (move txns, delete source)
            source_id = request.data.get('source_subcategory_id')
            target_id = request.data.get('target_subcategory_id')

            if not source_id or not target_id:
                return Response({'error': 'source_subcategory_id and target_subcategory_id required'}, status=400)

            source = Subcategory.objects.get(id=source_id, profile=profile)
            target = Subcategory.objects.get(id=target_id, profile=profile)

            count = Transaction.objects.filter(
                profile=profile, subcategory=source
            ).update(subcategory=target, category=target.category)

            PluggyCategoryMapping.objects.filter(
                profile=profile, subcategory=source
            ).update(subcategory=target)

            source.delete()
            return Response({'updated': count, 'merged_into': str(target.id), 'action': action})

        elif action == 'rename_subcategory':
            sub_id = request.data.get('subcategory_id')
            new_name = request.data.get('name', '').strip()
            if not sub_id or not new_name:
                return Response({'error': 'subcategory_id and name required'}, status=400)
            sub = Subcategory.objects.get(id=sub_id, profile=profile)
            sub.name = new_name
            sub.save(update_fields=['name'])
            return Response({'id': str(sub.id), 'name': sub.name, 'action': action})

        elif action == 'move_uncategorized':
            # Move uncategorized transactions to a specific category + optional subcategory
            to_cat_id = request.data.get('to_category_id')
            to_sub_id = request.data.get('to_subcategory_id')
            if not to_cat_id:
                return Response({'error': 'to_category_id required'}, status=400)
            to_cat = Category.objects.get(id=to_cat_id, profile=profile)
            to_sub = Subcategory.objects.get(id=to_sub_id, profile=profile) if to_sub_id else None
            count = Transaction.objects.filter(
                profile=profile, category__isnull=True
            ).update(category=to_cat, subcategory=to_sub)
            return Response({'updated': count, 'action': action})

        elif action == 'set_subcategory':
            # Assign subcategory to transactions that have category but no subcategory
            cat_id = request.data.get('category_id')
            to_sub_id = request.data.get('to_subcategory_id')
            if not cat_id or not to_sub_id:
                return Response({'error': 'category_id and to_subcategory_id required'}, status=400)
            cat = Category.objects.get(id=cat_id, profile=profile)
            to_sub = Subcategory.objects.get(id=to_sub_id, profile=profile)
            count = Transaction.objects.filter(
                profile=profile, category=cat, subcategory__isnull=True
            ).update(subcategory=to_sub)
            return Response({'updated': count, 'action': action})

        elif action == 'get_sample_transactions':
            # Return sample transactions for a subcategory or uncategorized
            # Installments are grouped: only one representative per purchase shown
            sub_id = request.data.get('subcategory_id')
            cat_id = request.data.get('category_id')
            all_in_cat = request.data.get('all_in_category', False)
            uncategorized = request.data.get('uncategorized', False)
            limit = int(request.data.get('limit', 50))

            if uncategorized:
                qs = Transaction.objects.filter(profile=profile, category__isnull=True)
            elif sub_id:
                qs = Transaction.objects.filter(profile=profile, subcategory_id=sub_id)
            elif cat_id and all_in_cat:
                qs = Transaction.objects.filter(profile=profile, category_id=cat_id)
            elif cat_id:
                qs = Transaction.objects.filter(profile=profile, category_id=cat_id, subcategory__isnull=True)
            else:
                return Response({'error': 'subcategory_id, category_id, or uncategorized required'}, status=400)

            from .services import _extract_base_desc
            import re as _re

            txns = list(qs.select_related('account', 'category', 'subcategory').order_by('-date')[:200])

            # Group installments: only credit card, keep one representative per purchase
            seen_installment_groups = {}
            result_txns = []
            installment_collapsed = {}  # txn.id -> count of siblings collapsed

            for t in txns:
                if t.is_installment and t.account and t.account.account_type == 'credit_card':
                    m = _re.search(r'(\d{1,2})/(\d{1,2})', t.description)
                    if not m and t.installment_info:
                        m = _re.match(r'(\d+)/(\d+)', t.installment_info)
                    if m:
                        total = int(m.group(2))
                        base = _extract_base_desc(t.description)
                        acct_id = t.account_id
                        amt_group = round(float(abs(t.amount)), 1)
                        key = (base, acct_id, amt_group, total)
                        if key in seen_installment_groups:
                            rep_id = seen_installment_groups[key]
                            installment_collapsed[rep_id] = installment_collapsed.get(rep_id, 1) + 1
                            continue
                        seen_installment_groups[key] = t.id
                        installment_collapsed[t.id] = 1

                result_txns.append(t)
                if len(result_txns) >= limit:
                    break

            return Response({
                'transactions': [{
                    'id': str(t.id),
                    'date': str(t.date),
                    'description': t.description,
                    'amount': float(t.amount),
                    'account': t.account.name if t.account else '',
                    'category_id': str(t.category_id) if t.category_id else None,
                    'subcategory_id': str(t.subcategory_id) if t.subcategory_id else None,
                    'is_installment': t.is_installment,
                    'installment_total': installment_collapsed.get(t.id, 0),
                } for t in result_txns]
            })

        elif action == 'recategorize_transaction':
            # Move a single transaction + all matching descriptions to a new category/subcategory
            # For installments, also propagate to all sibling positions
            txn_id = request.data.get('transaction_id')
            to_cat_id = request.data.get('to_category_id')
            to_sub_id = request.data.get('to_subcategory_id')

            if not txn_id or not to_cat_id:
                return Response({'error': 'transaction_id and to_category_id required'}, status=400)

            txn = Transaction.objects.get(id=txn_id, profile=profile)
            to_cat = Category.objects.get(id=to_cat_id, profile=profile)
            to_sub = Subcategory.objects.get(id=to_sub_id, profile=profile) if to_sub_id else None

            # Normalize description for matching (non-installment transactions)
            from django.db.models.functions import Lower, Trim
            desc_norm = txn.description.strip().lower()
            matching = Transaction.objects.filter(profile=profile).annotate(
                desc_norm=Trim(Lower('description'))
            ).filter(desc_norm=desc_norm)
            count = matching.update(category=to_cat, subcategory=to_sub)

            # For installments, also update all sibling positions
            sibling_count = 0
            if txn.is_installment:
                result = categorize_installment_siblings(
                    txn_id, to_cat_id, to_sub_id or None, profile=profile
                )
                sibling_count = result.get('updated', 0)

            return Response({
                'updated': count + sibling_count,
                'description': txn.description,
                'action': action,
            })

        elif action == 'bulk_uncategorize':
            # Remove category from all transactions in a subcategory or category
            sub_id = request.data.get('subcategory_id')
            cat_id = request.data.get('category_id')
            if sub_id:
                count = Transaction.objects.filter(
                    profile=profile, subcategory_id=sub_id
                ).update(category=None, subcategory=None)
            elif cat_id:
                count = Transaction.objects.filter(
                    profile=profile, category_id=cat_id
                ).update(category=None, subcategory=None)
            else:
                return Response({'error': 'subcategory_id or category_id required'}, status=400)
            return Response({'updated': count, 'action': action})

        elif action == 'uncategorize_transaction':
            # Remove category from a transaction + all matching descriptions
            # For installments, also clear all sibling positions
            txn_id = request.data.get('transaction_id')
            if not txn_id:
                return Response({'error': 'transaction_id required'}, status=400)

            txn = Transaction.objects.get(id=txn_id, profile=profile)
            desc_norm = txn.description.strip().lower()

            from django.db.models.functions import Lower, Trim
            matching = Transaction.objects.filter(profile=profile).annotate(
                desc_norm=Trim(Lower('description'))
            ).filter(desc_norm=desc_norm)

            count = matching.update(category=None, subcategory=None)

            # For installments, also clear siblings
            if txn.is_installment:
                import re as _re
                from .services import _extract_base_desc
                m = _re.search(r'(\d{1,2})/(\d{1,2})', txn.description)
                if not m and txn.installment_info:
                    m = _re.match(r'(\d+)/(\d+)', txn.installment_info)
                if m:
                    total = int(m.group(2))
                    base = _extract_base_desc(txn.description)
                    candidates = Transaction.objects.filter(
                        account_id=txn.account_id, is_installment=True, profile=profile
                    )
                    sibling_ids = []
                    for c in candidates:
                        if round(float(abs(c.amount)), 1) != round(float(abs(txn.amount)), 1):
                            continue
                        if _extract_base_desc(c.description) != base:
                            continue
                        cm = _re.search(r'(\d{1,2})/(\d{1,2})', c.description)
                        if not cm and c.installment_info:
                            cm = _re.match(r'(\d+)/(\d+)', c.installment_info)
                        if cm and int(cm.group(2)) == total:
                            sibling_ids.append(c.id)
                    if sibling_ids:
                        extra = Transaction.objects.filter(id__in=sibling_ids).update(
                            category=None, subcategory=None
                        )
                        count += extra

            return Response({
                'updated': count,
                'description': txn.description,
                'action': action,
            })

        elif action == 'create_category':
            name = request.data.get('name', '').strip()
            if not name:
                return Response({'error': 'name required'}, status=400)
            if Category.objects.filter(profile=profile, name__iexact=name).exists():
                return Response({'error': f'Categoria "{name}" ja existe'}, status=400)
            cat = Category.objects.create(profile=profile, name=name, category_type='variable')
            return Response({'id': str(cat.id), 'name': cat.name, 'action': action})

        elif action == 'create_subcategory':
            cat_id = request.data.get('category_id')
            name = request.data.get('name', '').strip()
            if not cat_id or not name:
                return Response({'error': 'category_id and name required'}, status=400)
            cat = Category.objects.get(id=cat_id, profile=profile)
            if Subcategory.objects.filter(category=cat, name__iexact=name, profile=profile).exists():
                return Response({'error': f'Subcategoria "{name}" ja existe em {cat.name}'}, status=400)
            sub = Subcategory.objects.create(profile=profile, category=cat, name=name)
            return Response({'id': str(sub.id), 'name': sub.name, 'category_id': str(cat.id), 'action': action})

        elif action == 'delete_category':
            cat_id = request.data.get('category_id')
            if not cat_id:
                return Response({'error': 'category_id required'}, status=400)
            cat = Category.objects.get(id=cat_id, profile=profile)
            # Move all transactions to uncategorized
            txn_count = Transaction.objects.filter(profile=profile, category=cat).update(
                category=None, subcategory=None
            )
            # Clean up subcategories and pluggy mappings
            Subcategory.objects.filter(category=cat, profile=profile).delete()
            PluggyCategoryMapping.objects.filter(category=cat, profile=profile).delete()
            cat.delete()
            return Response({'deleted': True, 'uncategorized': txn_count, 'action': action})

        elif action == 'delete_subcategory':
            sub_id = request.data.get('subcategory_id')
            if not sub_id:
                return Response({'error': 'subcategory_id required'}, status=400)
            sub = Subcategory.objects.get(id=sub_id, profile=profile)
            # Clear subcategory from transactions (keep category)
            txn_count = Transaction.objects.filter(profile=profile, subcategory=sub).update(
                subcategory=None
            )
            PluggyCategoryMapping.objects.filter(subcategory=sub, profile=profile).delete()
            sub.delete()
            return Response({'deleted': True, 'uncategorized': txn_count, 'action': action})

        return Response({'error': f'Unknown action: {action}'}, status=400)


class PluggyCategoryMappingViewSet(viewsets.ModelViewSet):
    serializer_class = PluggyCategoryMappingSerializer
    pagination_class = None

    def get_queryset(self):
        return PluggyCategoryMapping.objects.filter(
            profile=self.request.profile
        ).select_related('category', 'subcategory').order_by('pluggy_category_id')

    def perform_create(self, serializer):
        serializer.save(profile=self.request.profile)


class CategorizationRuleViewSet(viewsets.ModelViewSet):
    serializer_class = CategorizationRuleSerializer
    filterset_fields = ['category', 'is_active']
    search_fields = ['keyword']
    pagination_class = None  # Rules list needs to be complete for settings UI

    def get_queryset(self):
        return CategorizationRule.objects.filter(profile=self.request.profile)

    def perform_create(self, serializer):
        serializer.save(profile=self.request.profile)


class RenameRuleViewSet(viewsets.ModelViewSet):
    serializer_class = RenameRuleSerializer
    search_fields = ['keyword', 'display_name']
    pagination_class = None

    def get_queryset(self):
        return RenameRule.objects.filter(profile=self.request.profile)

    def perform_create(self, serializer):
        serializer.save(profile=self.request.profile)


class TransactionViewSet(viewsets.ModelViewSet):
    filterset_fields = ['month_str', 'account', 'category', 'is_recurring', 'is_internal_transfer']
    search_fields = ['description', 'description_original']
    ordering_fields = ['date', 'amount', 'description']

    def get_queryset(self):
        return Transaction.objects.filter(profile=self.request.profile).select_related('account', 'category')

    def get_serializer_class(self):
        if self.action == 'list':
            return TransactionListSerializer
        return TransactionSerializer

    def perform_create(self, serializer):
        serializer.save(profile=self.request.profile)

    @action(detail=False, methods=['get'])
    def months(self, request):
        """Return list of available months, sorted descending.

        Extends beyond real transaction data to include future months up to the
        last projected installment, so the user can browse forward projections.
        """
        real_months = list(
            Transaction.objects
            .filter(profile=request.profile)
            .values_list('month_str', flat=True)
            .distinct()
            .order_by('-month_str')
        )

        last_inst_month = get_last_installment_month(profile=request.profile)
        if last_inst_month and real_months:
            latest_real = real_months[0]
            if last_inst_month > latest_real:
                # Generate future months from latest_real+1 through last_inst_month
                from dateutil.relativedelta import relativedelta
                from datetime import datetime
                cursor = datetime.strptime(latest_real, '%Y-%m') + relativedelta(months=1)
                end = datetime.strptime(last_inst_month, '%Y-%m')
                future = []
                while cursor <= end:
                    future.append(cursor.strftime('%Y-%m'))
                    cursor += relativedelta(months=1)
                # Prepend future months (descending) before real months
                return Response(list(reversed(future)) + real_months)

        return Response(real_months)

    @action(detail=False, methods=['post'], url_path='bulk-categorize')
    def bulk_categorize(self, request):
        """Bulk re-categorize selected transactions with learning feedback."""
        transaction_ids = request.data.get('transaction_ids', [])
        category_id = request.data.get('category_id')
        subcategory_id = request.data.get('subcategory_id')
        if not transaction_ids or not category_id:
            return Response(
                {'error': 'transaction_ids and category_id required'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        update_fields = {'category_id': category_id, 'is_manually_categorized': True}
        if subcategory_id:
            update_fields['subcategory_id'] = subcategory_id
        updated = Transaction.objects.filter(
            id__in=transaction_ids, profile=request.profile
        ).update(**update_fields)

        # Learning feedback: find similar uncategorized + suggest rule
        feedback = {}
        if len(transaction_ids) == 1:
            try:
                feedback = find_similar_transactions(transaction_ids[0], profile=request.profile)
            except Transaction.DoesNotExist:
                pass

        return Response({'updated': updated, **feedback})


class RecurringMappingViewSet(viewsets.ModelViewSet):
    serializer_class = RecurringMappingSerializer
    filterset_fields = ['month_str', 'status']

    def get_queryset(self):
        return RecurringMapping.objects.filter(profile=self.request.profile).select_related('template', 'category', 'transaction')

    def perform_create(self, serializer):
        serializer.save(profile=self.request.profile)

    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generate recurring mappings for a given month from RecurringTemplate."""
        month_str = request.data.get('month_str')
        if not month_str:
            return Response(
                {'error': 'month_str required'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        templates = RecurringTemplate.objects.filter(is_active=True, profile=request.profile)
        created = 0
        for tpl in templates:
            _, was_created = RecurringMapping.objects.get_or_create(
                template=tpl,
                month_str=month_str,
                profile=request.profile,
                defaults={
                    'expected_amount': tpl.default_limit,
                    'status': 'missing',
                },
            )
            if was_created:
                created += 1
        return Response({'created': created, 'month_str': month_str})

    @action(detail=False, methods=['post'], url_path='auto-match')
    def auto_match(self, request):
        """Auto-match transactions to recurring mappings for a month."""
        month_str = request.data.get('month_str')
        if not month_str:
            return Response(
                {'error': 'month_str required'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Get unmapped entries
        mappings = RecurringMapping.objects.filter(
            month_str=month_str, status='missing', profile=request.profile
        ).select_related('template', 'category')

        matched = 0
        for mapping in mappings:
            # For category-match mode, try by taxonomy category
            if mapping.match_mode == 'category' and mapping.category:
                txn = Transaction.objects.filter(
                    month_str=month_str,
                    category=mapping.category,
                    is_internal_transfer=False,
                    profile=request.profile,
                ).first()
                if txn:
                    mapping.transaction = txn
                    mapping.actual_amount = txn.amount
                    mapping.status = 'suggested'
                    mapping.save()
                    matched += 1

        return Response({'matched': matched, 'month_str': month_str})


class AnalyticsMetricasView(APIView):
    """GET /api/analytics/metricas/?month_str=2026-01"""
    def get(self, request):
        month_str = request.query_params.get('month_str')
        err = _validate_month_str(month_str)
        if err:
            return err
        try:
            return Response(get_metricas(month_str, profile=request.profile))
        except Exception as e:
            logger.exception('AnalyticsMetricasView error')
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class RecurringDataView(APIView):
    """GET /api/analytics/recurring/?month_str=2026-01"""
    def get(self, request):
        month_str = request.query_params.get('month_str')
        err = _validate_month_str(month_str)
        if err:
            return err
        try:
            return Response(get_recurring_data(month_str, profile=request.profile))
        except Exception as e:
            logger.exception('RecurringDataView error')
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CardTransactionsView(APIView):
    """GET /api/analytics/cards/?month_str=2026-01&account=Master"""
    def get(self, request):
        month_str = request.query_params.get('month_str')
        err = _validate_month_str(month_str)
        if err:
            return err
        try:
            account_filter = request.query_params.get('account', None)
            return Response(get_card_transactions(month_str, account_filter, profile=request.profile))
        except Exception as e:
            logger.exception('CardTransactionsView error')
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class VariableTransactionsView(APIView):
    """GET /api/analytics/variable/?month_str=2026-01"""
    def get(self, request):
        month_str = request.query_params.get('month_str')
        err = _validate_month_str(month_str)
        if err:
            return err
        try:
            return Response(get_variable_transactions(month_str, profile=request.profile))
        except Exception as e:
            logger.exception('VariableTransactionsView error')
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class MappingCandidatesView(APIView):
    """GET /api/analytics/recurring/candidates/?month_str=2026-01&category_id=uuid&mapping_id=uuid"""
    def get(self, request):
        month_str = request.query_params.get('month_str')
        err = _validate_month_str(month_str)
        if err:
            return err
        category_id = request.query_params.get('category_id')
        mapping_id = request.query_params.get('mapping_id')
        if not category_id and not mapping_id:
            return Response(
                {'error': 'category_id or mapping_id required'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            return Response(get_mapping_candidates(month_str, category_id=category_id, mapping_id=mapping_id, profile=request.profile))
        except (RecurringMapping.DoesNotExist, Category.DoesNotExist) as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception('MappingCandidatesView error')
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class MapTransactionView(APIView):
    """
    POST /api/analytics/recurring/map/ — Map a transaction to a category or mapping
    DELETE /api/analytics/recurring/map/ — Unmap a transaction
    """
    def post(self, request):
        transaction_id = request.data.get('transaction_id')
        category_id = request.data.get('category_id')
        mapping_id = request.data.get('mapping_id')
        if not transaction_id or (not category_id and not mapping_id):
            return Response(
                {'error': 'transaction_id and (category_id or mapping_id) required'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            result = map_transaction_to_category(
                transaction_id, category_id=category_id, mapping_id=mapping_id, profile=request.profile
            )
            return Response(result)
        except (Transaction.DoesNotExist, RecurringMapping.DoesNotExist, Category.DoesNotExist) as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception('MapTransactionView.post error')
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        transaction_id = request.data.get('transaction_id')
        mapping_id = request.data.get('mapping_id')
        if not transaction_id:
            return Response(
                {'error': 'transaction_id required'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            result = unmap_transaction(transaction_id, mapping_id=mapping_id, profile=request.profile)
            return Response(result)
        except (Transaction.DoesNotExist, RecurringMapping.DoesNotExist) as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception('MapTransactionView.delete error')
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ToggleMatchModeView(APIView):
    """
    POST /api/analytics/recurring/match-mode/ — Toggle match_mode for a mapping
    Body: { mapping_id, match_mode: 'manual' | 'category', category_id (optional) }

    Switching to 'manual': preserves existing M2M linked transactions.
    Switching to 'category' WITH category_id: clears M2M, sets category FK.
    Switching to 'category' WITHOUT category_id: just sets mode (no data loss).
    """
    def post(self, request):
        mapping_id = request.data.get('mapping_id')
        match_mode = request.data.get('match_mode')
        category_id = request.data.get('category_id')
        if not mapping_id or match_mode not in ('manual', 'category'):
            return Response(
                {'error': 'mapping_id and match_mode (manual|category) required'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            mapping = RecurringMapping.objects.get(id=mapping_id, profile=request.profile)
            mapping.match_mode = match_mode
            if match_mode == 'category' and category_id:
                # Only clear M2M when explicitly selecting a category
                # This prevents data loss from just clicking the tab
                mapping.transactions.clear()
                mapping.transaction = None
                mapping.actual_amount = None
                mapping.status = 'missing'  # Will be recomputed on next fetch
                try:
                    cat = Category.objects.get(id=category_id, profile=request.profile)
                    mapping.category = cat
                except Category.DoesNotExist:
                    pass
            mapping.save()
            return Response({
                'mapping_id': str(mapping.id),
                'match_mode': mapping.match_mode,
                'category_id': str(mapping.category_id) if mapping.category_id else None,
            })
        except RecurringMapping.DoesNotExist:
            return Response({'error': 'Mapping not found'}, status=status.HTTP_404_NOT_FOUND)


class ImportStatementsView(APIView):
    """
    POST /api/import/upload/ — Upload statement files
    POST /api/import/run/ — Trigger full re-import from SampleData
    GET  /api/import/status/ — Get current data status
    """
    parser_classes = [MultiPartParser, FormParser]

    # Resolve SampleData dir to match where DataLoader reads from.
    # In Docker: FinanceDashboard is mounted at /app/legacy_data
    SAMPLE_DATA_DIR = os.path.join('/app', 'legacy_data', 'SampleData') if os.path.isdir('/app/legacy_data') else os.path.join(
        os.path.dirname(__file__), '..', '..', '..', 'FinanceDashboard', 'SampleData'
    )

    def get(self, request):
        """Return current import status."""
        from django.db.models import Min, Max
        profile = request.profile
        txn_count = Transaction.objects.filter(profile=profile).count()
        month_count = Transaction.objects.filter(profile=profile).values('month_str').distinct().count()
        date_range = Transaction.objects.filter(profile=profile).aggregate(
            earliest=Min('date'), latest=Max('date')
        )
        accounts = {}
        for acct in Account.objects.filter(profile=profile):
            c = Transaction.objects.filter(account=acct, profile=profile).count()
            if c > 0:
                accounts[acct.name] = c

        # List files in SampleData (profile-specific subdirectory)
        profile_name = request.profile.name if request.profile else 'Palmer'
        sample_dir = os.path.abspath(os.path.join(self.SAMPLE_DATA_DIR, profile_name))
        files = []
        if os.path.isdir(sample_dir):
            for f in sorted(os.listdir(sample_dir)):
                if f.startswith('.'):
                    continue
                fpath = os.path.join(sample_dir, f)
                files.append({
                    'name': f,
                    'size': os.path.getsize(fpath),
                    'modified': os.path.getmtime(fpath),
                })

        return Response({
            'transactions': txn_count,
            'months': month_count,
            'earliest': str(date_range['earliest']) if date_range['earliest'] else None,
            'latest': str(date_range['latest']) if date_range['latest'] else None,
            'accounts': accounts,
            'files': files,
        })

    def post(self, request):
        """Handle file upload or import trigger."""
        action = request.query_params.get('action', 'upload')

        if action == 'upload':
            return self._handle_upload(request)
        elif action == 'run':
            return self._handle_import(request)
        elif action == 'incremental':
            return self._handle_import(request, clear=False)
        else:
            return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)

    def _handle_upload(self, request):
        """Save uploaded files to SampleData with correct naming."""
        import re

        files = request.FILES.getlist('files')
        if not files:
            return Response({'error': 'No files provided'}, status=status.HTTP_400_BAD_REQUEST)

        profile_name = request.profile.name if request.profile else 'Palmer'
        sample_dir = os.path.abspath(os.path.join(self.SAMPLE_DATA_DIR, profile_name))
        os.makedirs(sample_dir, exist_ok=True)

        results = []
        for f in files:
            original_name = f.name
            target_name = self._resolve_filename(original_name, f)
            target_path = os.path.join(sample_dir, target_name)

            # Save file
            with open(target_path, 'wb') as dest:
                for chunk in f.chunks():
                    dest.write(chunk)

            results.append({
                'original': original_name,
                'saved_as': target_name,
                'size': f.size,
            })

        return Response({
            'uploaded': len(results),
            'files': results,
        })

    def _resolve_filename(self, original_name, file_obj):
        """
        Auto-detect file type and resolve to the correct SampleData filename.

        Credit card CSVs: itau-master-YYYYMMDD.csv → master-MMYY.csv
        OFX files: keep original name (bank naming convention)
        """
        import re
        lower = original_name.lower()

        # Credit card CSV: fatura-master-YYYYMMDD.csv, itau-master-YYYYMMDD.csv, etc.
        card_match = re.match(
            r'(?:itau|fatura)-(master|visa)-(\d{4})(\d{2})\d{2}\.csv', lower
        )
        if card_match:
            card_type = card_match.group(1)  # master or visa
            year = card_match.group(2)       # 2026
            month = card_match.group(3)      # 02
            # Invoice month is the current month (the export date's month)
            yy = year[2:]  # 26
            return f'{card_type}-{month}{yy}.csv'

        # Already correctly named card CSV: master-0226.csv
        if re.match(r'(master|visa)-\d{4}\.csv', lower):
            return original_name

        # OFX files: keep bank's naming
        if lower.endswith('.ofx'):
            return original_name

        # TXT bank extracts: keep naming
        if lower.endswith('.txt') and 'extrato' in lower:
            return original_name

        # Fallback: keep original name
        return original_name

    def _handle_import(self, request, clear=True):
        """Trigger import using the management command.

        clear=True: full re-import (wipes existing data first)
        clear=False: incremental import (adds new transactions, skips duplicates)
        """
        from django.core.management import call_command
        from io import StringIO

        stdout_capture = StringIO()
        stderr_capture = StringIO()

        profile_name = request.profile.name if request.profile else 'Palmer'
        profile = request.profile

        txn_before = Transaction.objects.filter(profile=profile).count()

        try:
            args = ['import_legacy_data', '--profile', profile_name]
            if clear:
                args.append('--clear')
            call_command(*args, stdout=stdout_capture, stderr=stderr_capture)
            output = stdout_capture.getvalue()

            txn_after = Transaction.objects.filter(profile=profile).count()
            month_count = Transaction.objects.filter(profile=profile).values('month_str').distinct().count()

            return Response({
                'success': True,
                'transactions': txn_after,
                'months': month_count,
                'new_transactions': txn_after - txn_before if not clear else txn_after,
                'output': output[-2000:],
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e),
                'output': stdout_capture.getvalue()[-1000:],
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RecurringInitializeView(APIView):
    """POST /api/analytics/recurring/initialize/ — Init month from template"""
    def post(self, request):
        month_str = request.data.get('month_str')
        if not month_str:
            return Response({'error': 'month_str required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            result = initialize_month(month_str, profile=request.profile)
            return Response(result)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class RecurringExpectedView(APIView):
    """PATCH /api/analytics/recurring/expected/ — Edit expected amount"""
    def patch(self, request):
        mapping_id = request.data.get('mapping_id')
        expected_amount = request.data.get('expected_amount')
        if not mapping_id or expected_amount is None:
            return Response(
                {'error': 'mapping_id and expected_amount required'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            result = update_recurring_expected(mapping_id, expected_amount, profile=request.profile)
            return Response(result)
        except RecurringMapping.DoesNotExist:
            return Response({'error': 'Mapping not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class RecurringUpdateView(APIView):
    """PATCH /api/analytics/recurring/update/ — Edit recurring item fields"""
    def patch(self, request):
        mapping_id = request.data.get('mapping_id')
        if not mapping_id:
            return Response(
                {'error': 'mapping_id required'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Extract optional fields
        kwargs = {}
        for field in ('name', 'template_type', 'expected_amount', 'due_day'):
            if field in request.data:
                kwargs[field] = request.data[field]
        # Accept category_type as alias for template_type (backward compat)
        if 'category_type' in request.data and 'template_type' not in kwargs:
            kwargs['template_type'] = request.data['category_type']
        if not kwargs:
            return Response(
                {'error': 'At least one field to update is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            result = update_recurring_item(mapping_id, profile=request.profile, **kwargs)
            return Response(result)
        except RecurringMapping.DoesNotExist:
            return Response({'error': 'Mapping not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class RecurringCustomView(APIView):
    """
    POST /api/analytics/recurring/custom/ — Add custom item
    DELETE /api/analytics/recurring/custom/ — Delete custom item
    """
    def post(self, request):
        month_str = request.data.get('month_str')
        name = request.data.get('name')
        # Accept both template_type and category_type for backward compat
        template_type = request.data.get('template_type') or request.data.get('category_type', 'Fixo')
        expected_amount = request.data.get('expected_amount', 0)
        if not month_str or not name:
            return Response(
                {'error': 'month_str and name required'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            result = add_custom_recurring(month_str, name, template_type, expected_amount, profile=request.profile)
            return Response(result, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        mapping_id = request.data.get('mapping_id')
        if not mapping_id:
            return Response({'error': 'mapping_id required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            result = delete_custom_recurring(mapping_id, profile=request.profile)
            return Response(result)
        except RecurringMapping.DoesNotExist:
            return Response({'error': 'Mapping not found'}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class RecurringSkipView(APIView):
    """
    POST /api/analytics/recurring/skip/ — Skip item
    DELETE /api/analytics/recurring/skip/ — Unskip item
    """
    def post(self, request):
        mapping_id = request.data.get('mapping_id')
        if not mapping_id:
            return Response({'error': 'mapping_id required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            result = skip_recurring(mapping_id, profile=request.profile)
            return Response(result)
        except RecurringMapping.DoesNotExist:
            return Response({'error': 'Mapping not found'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request):
        mapping_id = request.data.get('mapping_id')
        if not mapping_id:
            return Response({'error': 'mapping_id required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            result = unskip_recurring(mapping_id, profile=request.profile)
            return Response(result)
        except RecurringMapping.DoesNotExist:
            return Response({'error': 'Mapping not found'}, status=status.HTTP_404_NOT_FOUND)


class BalanceSaveView(APIView):
    """POST /api/analytics/balance/ — Save checking balance"""
    def post(self, request):
        month_str = request.data.get('month_str')
        balance = request.data.get('balance')
        if not month_str or balance is None:
            return Response(
                {'error': 'month_str and balance required'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            result = save_balance_override(month_str, balance, profile=request.profile)
            return Response(result)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class BudgetConfigViewSet(viewsets.ModelViewSet):
    serializer_class = BudgetConfigSerializer
    filterset_fields = ['month_str', 'category']

    def get_queryset(self):
        return BudgetConfig.objects.filter(profile=self.request.profile).select_related('category', 'template')

    def perform_create(self, serializer):
        serializer.save(profile=self.request.profile)


class BalanceOverrideViewSet(viewsets.ModelViewSet):
    serializer_class = BalanceOverrideSerializer
    filterset_fields = ['month_str']

    def get_queryset(self):
        return BalanceOverride.objects.filter(profile=self.request.profile)

    def perform_create(self, serializer):
        serializer.save(profile=self.request.profile)


class ProjectionView(APIView):
    """GET /api/analytics/projection/?month_str=2025-12&months=6"""
    def get(self, request):
        month_str = request.query_params.get('month_str')
        err = _validate_month_str(month_str)
        if err:
            return err
        try:
            num_months = int(request.query_params.get('months', 0))
        except (ValueError, TypeError):
            return Response({'error': 'months must be an integer'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            return Response(get_projection(month_str, num_months, profile=request.profile))
        except Exception as e:
            logger.exception('ProjectionView error')
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AnalyticsTrendsView(APIView):
    """GET /api/analytics/trends/?start_month=2025-12&end_month=2026-06&categories=id1,id2&accounts=mastercard"""
    def get(self, request):
        start_month = request.query_params.get('start_month') or None
        end_month = request.query_params.get('end_month') or None
        # Validate months if provided
        if start_month:
            err = _validate_month_str(start_month)
            if err:
                return err
        if end_month:
            err = _validate_month_str(end_month)
            if err:
                return err
        # Parse category IDs (comma-separated UUIDs)
        categories_raw = request.query_params.get('categories', '')
        category_ids = [c.strip() for c in categories_raw.split(',') if c.strip()] or None
        # Account filter
        account_filter = request.query_params.get('accounts', '') or None
        try:
            return Response(get_analytics_trends(start_month, end_month, category_ids, account_filter, profile=request.profile))
        except Exception as e:
            logger.exception('AnalyticsTrendsView error')
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class SpendingInsightsView(APIView):
    """GET /api/analytics/insights/"""
    def get(self, request):
        try:
            return Response(get_spending_insights(profile=request.profile))
        except Exception as e:
            logger.exception('SpendingInsightsView error')
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class OrcamentoView(APIView):
    """GET /api/analytics/orcamento/?month_str=2025-12"""
    def get(self, request):
        month_str = request.query_params.get('month_str')
        err = _validate_month_str(month_str)
        if err:
            return err
        try:
            return Response(get_orcamento(month_str, profile=request.profile))
        except Exception as e:
            logger.exception('OrcamentoView error')
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class InstallmentDetailsView(APIView):
    """GET /api/analytics/installments/?month_str=2026-02"""
    def get(self, request):
        month_str = request.query_params.get('month_str')
        err = _validate_month_str(month_str)
        if err:
            return err
        try:
            return Response(get_installment_details(month_str, profile=request.profile))
        except Exception as e:
            logger.exception('InstallmentDetailsView error')
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CategorizeInstallmentView(APIView):
    """
    POST /api/transactions/categorize-installment/
    Categorize an installment and propagate to all sibling installments.
    Body: { transaction_id, category_id, subcategory_id (optional) }
    """
    def post(self, request):
        transaction_id = request.data.get('transaction_id')
        category_id = request.data.get('category_id')
        subcategory_id = request.data.get('subcategory_id')
        if not transaction_id or not category_id:
            return Response(
                {'error': 'transaction_id and category_id required'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            result = categorize_installment_siblings(
                transaction_id, category_id, subcategory_id, profile=request.profile
            )
            return Response(result)
        except Transaction.DoesNotExist:
            return Response(
                {'error': 'Transaction not found'},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            logger.exception('CategorizeInstallmentView error')
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class SmartCategorizeView(APIView):
    """
    POST /api/analytics/smart-categorize/ — Apply smart categorization
    Uses rule-based + learning-based categorization to auto-categorize transactions.

    Body: { "month_str": "2026-02" (optional), "dry_run": true/false }
    """
    def post(self, request):
        month_str = request.data.get('month_str')
        dry_run = request.data.get('dry_run', False)
        try:
            result = smart_categorize(month_str=month_str, dry_run=dry_run, profile=request.profile)
            return Response(result)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class RecurringTemplatesView(APIView):
    """
    GET /api/analytics/recurring/templates/ — List recurring templates
    POST /api/analytics/recurring/templates/ — Create a new template
    PATCH /api/analytics/recurring/templates/ — Update a template
    DELETE /api/analytics/recurring/templates/ — Delete (deactivate) a template
    """
    def get(self, request):
        try:
            return Response(get_recurring_templates(profile=request.profile))
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        name = request.data.get('name')
        # Accept both template_type and category_type for backward compat
        template_type = request.data.get('template_type') or request.data.get('category_type', 'Fixo')
        default_limit = request.data.get('default_limit', 0)
        due_day = request.data.get('due_day')
        if not name:
            return Response({'error': 'name required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            result = create_recurring_template(name, template_type, default_limit, due_day, profile=request.profile)
            return Response(result, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        template_id = request.data.get('id')
        if not template_id:
            return Response({'error': 'id required'}, status=status.HTTP_400_BAD_REQUEST)
        kwargs = {}
        for field in ('name', 'template_type', 'default_limit', 'due_day', 'display_order'):
            if field in request.data:
                kwargs[field] = request.data[field]
        # Accept category_type as alias for template_type (backward compat)
        if 'category_type' in request.data and 'template_type' not in kwargs:
            kwargs['template_type'] = request.data['category_type']
        if not kwargs:
            return Response({'error': 'At least one field required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            result = update_recurring_template(template_id, profile=request.profile, **kwargs)
            return Response(result)
        except RecurringTemplate.DoesNotExist:
            return Response({'error': 'Template not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        template_id = request.data.get('id')
        if not template_id:
            return Response({'error': 'id required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            result = delete_recurring_template(template_id, profile=request.profile)
            return Response(result)
        except RecurringTemplate.DoesNotExist:
            return Response({'error': 'Template not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ReapplyTemplateView(APIView):
    """POST /api/analytics/recurring/reapply/ — Reapply template to a month"""
    def post(self, request):
        month_str = request.data.get('month_str')
        if not month_str:
            return Response({'error': 'month_str required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            result = reapply_template_to_month(month_str, profile=request.profile)
            return Response(result)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CheckingTransactionsView(APIView):
    """GET /api/analytics/checking/ — Checking account transactions for a month"""
    def get(self, request):
        month_str = request.query_params.get('month_str')
        err = _validate_month_str(month_str)
        if err:
            return err
        data = get_checking_transactions(month_str, profile=request.profile)
        return Response(data)


class AutoLinkRecurringView(APIView):
    """
    POST /api/analytics/recurring/auto-link/ — Auto-link unmatched recurring items
    Body: { month_str }
    Tries to match unlinked items by name similarity, amount, and previous month patterns.
    """
    def post(self, request):
        month_str = request.data.get('month_str')
        if not month_str:
            return Response({'error': 'month_str required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            result = auto_link_recurring(month_str, profile=request.profile)
            return Response(result)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class RecurringReorderView(APIView):
    """
    POST /api/analytics/recurring/reorder/
    Body: { month_str, ordered_mapping_ids: [uuid, uuid, ...] }
    Updates display_order on RecurringMapping rows for the given month.
    Assigns sequential display_order (0, 1, 2, ...) to ALL mappings in the month,
    using the provided list as the new order for those items and keeping
    unmentioned items in their original relative positions after the reordered ones.
    """
    def post(self, request):
        month_str = request.data.get('month_str')
        ordered_ids = request.data.get('ordered_mapping_ids', [])
        if not month_str or not ordered_ids:
            return Response(
                {'error': 'month_str and ordered_mapping_ids required'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        mappings = list(
            RecurringMapping.objects.filter(month_str=month_str, profile=request.profile)
            .order_by('display_order', 'template__display_order')
        )
        id_to_mapping = {str(m.id): m for m in mappings}
        ordered_set = set(ordered_ids)

        # Build final order: reordered items in their new positions,
        # unreferenced items keep their relative order
        reordered = [id_to_mapping[mid] for mid in ordered_ids if mid in id_to_mapping]
        others = [m for m in mappings if str(m.id) not in ordered_set]

        # If only a subset (tab filter), interleave: replace the slots
        # where reordered items were with the new order
        if len(reordered) < len(mappings):
            final = []
            reorder_iter = iter(reordered)
            for m in mappings:
                if str(m.id) in ordered_set:
                    final.append(next(reorder_iter))
                else:
                    final.append(m)
        else:
            final = reordered

        updated = 0
        for idx, m in enumerate(final):
            if m.display_order != idx:
                m.display_order = idx
                m.save(update_fields=['display_order'])
                updated += 1
        return Response({'updated': updated})


class MonthCategoriesView(APIView):
    """GET /api/analytics/month-categories/?month_str=2026-01"""
    def get(self, request):
        month_str = request.query_params.get('month_str')
        err = _validate_month_str(month_str)
        if err:
            return err
        try:
            data = get_month_categories(month_str, profile=request.profile)
            return Response(data)
        except Exception as e:
            logger.exception('MonthCategoriesView error')
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class MetricasOrderView(APIView):
    """
    GET  /api/analytics/metricas/order/?month_str=2026-01
    POST /api/analytics/metricas/order/  { month_str, card_order: [...] }
    """
    def get(self, request):
        month_str = request.query_params.get('month_str')
        err = _validate_month_str(month_str)
        if err:
            return err
        try:
            return Response(get_metricas_order(month_str, profile=request.profile))
        except Exception as e:
            logger.exception('MetricasOrderView.get error')
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        month_str = request.data.get('month_str')
        card_order = request.data.get('card_order')
        hidden_cards = request.data.get('hidden_cards')
        if not month_str or not card_order:
            return Response({'error': 'month_str and card_order required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            return Response(save_metricas_order(month_str, card_order, hidden_cards, profile=request.profile))
        except Exception as e:
            logger.exception('MetricasOrderView.post error')
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class MetricasMakeDefaultView(APIView):
    """POST /api/analytics/metricas/make-default/  { card_order: [...], hidden_cards: [...] }"""
    def post(self, request):
        card_order = request.data.get('card_order')
        hidden_cards = request.data.get('hidden_cards')
        if not card_order:
            return Response({'error': 'card_order required'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(make_default_order(card_order, hidden_cards, profile=request.profile))


class MetricasLockView(APIView):
    """POST /api/analytics/metricas/lock/  { month_str, locked: true/false }"""
    def post(self, request):
        month_str = request.data.get('month_str')
        locked = request.data.get('locked')
        if not month_str or locked is None:
            return Response({'error': 'month_str and locked required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            return Response(toggle_metricas_lock(month_str, locked, profile=request.profile))
        except Exception as e:
            logger.exception('MetricasLockView error')
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CustomMetricsView(APIView):
    """
    GET    /api/analytics/metricas/custom/  — List definitions + options
    POST   /api/analytics/metricas/custom/  — Create custom metric
    DELETE /api/analytics/metricas/custom/  — Delete { id }
    """
    def get(self, request):
        try:
            return Response(get_custom_metric_options(profile=request.profile))
        except Exception as e:
            logger.exception('CustomMetricsView.get error')
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        metric_type = request.data.get('metric_type')
        label = request.data.get('label')
        config = request.data.get('config', {})
        color = request.data.get('color', 'var(--color-accent)')
        if not metric_type or not label:
            return Response({'error': 'metric_type and label required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            return Response(create_custom_metric(metric_type, label, config, color, profile=request.profile), status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.exception('CustomMetricsView.post error')
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        metric_id = request.data.get('id')
        if not metric_id:
            return Response({'error': 'id required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            return Response(delete_custom_metric(metric_id, profile=request.profile))
        except CustomMetric.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)


class TransactionRenameView(APIView):
    """
    POST /api/transactions/rename/
    Rename a transaction description with optional propagation to similar ones.

    Preview mode:  { transaction_id, new_description }
    -> Returns renamed count + list of similar transactions for user confirmation.

    Apply mode:    { transaction_ids: [...], new_description, propagate: true }
    -> Renames all selected + creates RenameRule for future imports.
    """
    def post(self, request):
        new_description = request.data.get('new_description')
        if not new_description:
            return Response({'error': 'new_description required'}, status=status.HTTP_400_BAD_REQUEST)

        propagate = request.data.get('propagate', False)

        if propagate:
            # Apply mode
            transaction_ids = request.data.get('transaction_ids', [])
            transaction_id = request.data.get('transaction_id')
            if not transaction_id:
                return Response({'error': 'transaction_id required'}, status=status.HTTP_400_BAD_REQUEST)
            try:
                result = rename_transaction(transaction_id, new_description, profile=request.profile, propagate_ids=transaction_ids)
                return Response(result)
            except Transaction.DoesNotExist:
                return Response({'error': 'Transaction not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            # Preview mode
            transaction_id = request.data.get('transaction_id')
            if not transaction_id:
                return Response({'error': 'transaction_id required'}, status=status.HTTP_400_BAD_REQUEST)
            try:
                result = rename_transaction(transaction_id, new_description, profile=request.profile)
                return Response(result)
            except Transaction.DoesNotExist:
                return Response({'error': 'Transaction not found'}, status=status.HTTP_404_NOT_FOUND)


class TransactionSimilarView(APIView):
    """
    GET /api/transactions/similar/?transaction_id=uuid
    Find similar uncategorized transactions + rule suggestion for learning feedback.
    """
    def get(self, request):
        transaction_id = request.query_params.get('transaction_id')
        if not transaction_id:
            return Response({'error': 'transaction_id required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            return Response(find_similar_transactions(transaction_id, profile=request.profile))
        except Transaction.DoesNotExist:
            return Response({'error': 'Transaction not found'}, status=status.HTTP_404_NOT_FOUND)


class AnalyzeSetupView(APIView):
    """Analyze imported statements to suggest setup configuration."""

    def get(self, request):
        profile = getattr(request, 'profile', None)
        if not profile:
            return Response({'error': 'No profile selected'}, status=status.HTTP_400_BAD_REQUEST)

        result = analyze_statements_for_setup(profile)
        return Response(result)


class ProfileSetupView(APIView):
    """Execute full profile setup from wizard selections (atomic)."""

    def post(self, request, pk):
        from django.db import transaction
        from django.utils import timezone

        try:
            profile = Profile.objects.get(pk=pk)
        except Profile.DoesNotExist:
            return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)

        data = request.data
        counts = {'accounts': 0, 'categories': 0, 'recurring': 0, 'rename_rules': 0, 'categorization_rules': 0}

        try:
            with transaction.atomic():
                # --- Reset mode: wipe existing profile data ---
                if data.get('reset_mode'):
                    RecurringMapping.objects.filter(profile=profile).delete()
                    RecurringTemplate.objects.filter(profile=profile).delete()
                    CategorizationRule.objects.filter(profile=profile).delete()
                    RenameRule.objects.filter(profile=profile).delete()
                    BudgetConfig.objects.filter(profile=profile).delete()
                    MetricasOrderConfig.objects.filter(profile=profile).delete()
                    CustomMetric.objects.filter(profile=profile).delete()
                    Category.objects.filter(profile=profile).delete()
                    Account.objects.filter(profile=profile).delete()

                # --- 1. Update profile fields ---
                if 'name' in data and data['name']:
                    profile.name = data['name']
                if 'savings_target_pct' in data:
                    profile.savings_target_pct = data['savings_target_pct']
                if 'investment_target_pct' in data:
                    profile.investment_target_pct = data['investment_target_pct']
                if 'investment_allocation' in data:
                    profile.investment_allocation = data['investment_allocation']
                if 'budget_strategy' in data:
                    profile.budget_strategy = data['budget_strategy']
                if 'cc_display_mode' in data:
                    profile.cc_display_mode = data['cc_display_mode']

                profile.setup_completed = True
                profile.save()

                # --- 2. Create accounts from bank templates ---
                if 'bank_accounts' in data:
                    for acct_data in data['bank_accounts']:
                        template = None
                        if acct_data.get('bank_template_id'):
                            try:
                                template = BankTemplate.objects.get(pk=acct_data['bank_template_id'])
                            except BankTemplate.DoesNotExist:
                                pass

                        display_name = acct_data.get('display_name') or (template.display_name if template else 'Account')
                        acct_type = acct_data.get('account_type') or (template.account_type if template else 'checking')

                        _, created = Account.objects.get_or_create(
                            profile=profile,
                            name=display_name,
                            defaults={
                                'account_type': acct_type,
                                'closing_day': acct_data.get('closing_day') or (template.default_closing_day if template else None),
                                'due_day': acct_data.get('due_day') or (template.default_due_day if template else None),
                                'credit_limit': acct_data.get('credit_limit') or None,
                                'bank_template': template,
                            }
                        )
                        if created:
                            counts['accounts'] += 1

                # --- 3. Create categories ---
                category_map = {}  # name -> Category for rule linking
                if 'categories' in data:
                    for cat_data in data['categories']:
                        cat_name = cat_data.get('name', '') if isinstance(cat_data, dict) else str(cat_data)
                        if not cat_name:
                            continue
                        cat_type = cat_data.get('type', 'Variavel') if isinstance(cat_data, dict) else 'Variavel'
                        cat_limit = cat_data.get('limit', 0) if isinstance(cat_data, dict) else 0
                        cat_due = cat_data.get('due_day') if isinstance(cat_data, dict) else None

                        cat, created = Category.objects.get_or_create(
                            profile=profile,
                            name=cat_name,
                            defaults={
                                'category_type': cat_type,
                                'default_limit': cat_limit,
                                'due_day': cat_due,
                            }
                        )
                        category_map[cat_name] = cat
                        if created:
                            counts['categories'] += 1

                # Also map existing categories for rule linking
                for cat in Category.objects.filter(profile=profile):
                    if cat.name not in category_map:
                        category_map[cat.name] = cat

                # --- 4. Create recurring templates ---
                if 'recurring_templates' in data:
                    for tpl_data in data['recurring_templates']:
                        if not tpl_data.get('name'):
                            continue
                        _, created = RecurringTemplate.objects.get_or_create(
                            profile=profile,
                            name=tpl_data['name'],
                            defaults={
                                'template_type': tpl_data.get('type', 'Fixo'),
                                'default_limit': tpl_data.get('amount', 0),
                                'due_day': tpl_data.get('due_day'),
                            }
                        )
                        if created:
                            counts['recurring'] += 1

                # --- 5. Create rename rules ---
                if 'rename_rules' in data:
                    for rule_data in data['rename_rules']:
                        if not rule_data.get('keyword') or not rule_data.get('display_name'):
                            continue
                        _, created = RenameRule.objects.get_or_create(
                            profile=profile,
                            keyword=rule_data['keyword'],
                            defaults={'display_name': rule_data['display_name']}
                        )
                        if created:
                            counts['rename_rules'] += 1

                # --- 6. Create categorization rules ---
                if 'categorization_rules' in data:
                    for rule_data in data['categorization_rules']:
                        cat_name = rule_data.get('category_name', '')
                        cat = category_map.get(cat_name)
                        if not cat or not rule_data.get('keyword'):
                            continue
                        _, created = CategorizationRule.objects.get_or_create(
                            profile=profile,
                            keyword=rule_data['keyword'],
                            defaults={
                                'category': cat,
                                'priority': rule_data.get('priority', 0),
                            }
                        )
                        if created:
                            counts['categorization_rules'] += 1

                # --- 7. Set metricas order ---
                if 'metricas_config' in data:
                    mc = data['metricas_config']
                    MetricasOrderConfig.objects.update_or_create(
                        profile=profile,
                        month_str='__default__',
                        defaults={
                            'card_order': mc.get('card_order', []),
                            'hidden_cards': mc.get('hidden_cards', []),
                        }
                    )

                # --- 8. Initialize recurring mappings for current month ---
                now = timezone.now()
                current_month = now.strftime('%Y-%m')
                templates_qs = RecurringTemplate.objects.filter(profile=profile, is_active=True)
                for tmpl in templates_qs:
                    RecurringMapping.objects.get_or_create(
                        profile=profile,
                        template=tmpl,
                        month_str=current_month,
                        defaults={
                            'status': 'missing',
                            'expected_amount': tmpl.default_limit,
                            'display_order': tmpl.display_order,
                        }
                    )

        except Exception as e:
            logger.exception('ProfileSetupView error')
            return Response(
                {'error': f'Setup failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        serializer = ProfileSerializer(profile)
        return Response({
            'profile': serializer.data,
            'counts': counts,
        }, status=status.HTTP_200_OK)


class SetupTemplateViewSet(viewsets.ModelViewSet):
    """CRUD for saved setup templates."""
    serializer_class = SetupTemplateSerializer

    def get_queryset(self):
        profile = getattr(self.request, 'profile', None)
        if profile:
            # Return templates owned by this profile + global templates
            return SetupTemplate.objects.filter(
                models.Q(profile=profile) | models.Q(profile__isnull=True)
            )
        return SetupTemplate.objects.filter(profile__isnull=True)

    def perform_create(self, serializer):
        profile = getattr(self.request, 'profile', None)
        serializer.save(profile=profile)


class ExportSetupView(APIView):
    """Export current profile configuration as a SetupTemplate."""

    def post(self, request, pk):
        try:
            profile = Profile.objects.get(pk=pk)
        except Profile.DoesNotExist:
            return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)

        # Gather all profile config into template_data
        accounts_data = []
        for acct in Account.objects.filter(profile=profile, is_active=True):
            accounts_data.append({
                'bank_template_id': str(acct.bank_template_id) if acct.bank_template_id else None,
                'display_name': acct.name,
                'account_type': acct.account_type,
                'closing_day': acct.closing_day,
                'due_day': acct.due_day,
                'credit_limit': float(acct.credit_limit) if acct.credit_limit else None,
            })

        categories_data = []
        for cat in Category.objects.filter(profile=profile, is_active=True):
            categories_data.append({
                'name': cat.name,
                'type': cat.category_type,
                'limit': float(cat.default_limit) if cat.default_limit else 0,
                'due_day': cat.due_day,
            })

        recurring_data = []
        for tmpl in RecurringTemplate.objects.filter(profile=profile, is_active=True):
            recurring_data.append({
                'name': tmpl.name,
                'type': tmpl.template_type,
                'amount': float(tmpl.default_limit) if tmpl.default_limit else 0,
                'due_day': tmpl.due_day,
            })

        rename_rules_data = []
        for rule in RenameRule.objects.filter(profile=profile, is_active=True):
            rename_rules_data.append({
                'keyword': rule.keyword,
                'display_name': rule.display_name,
            })

        categorization_rules_data = []
        for rule in CategorizationRule.objects.filter(profile=profile, is_active=True):
            categorization_rules_data.append({
                'keyword': rule.keyword,
                'category_name': rule.category.name if rule.category else '',
                'priority': rule.priority,
            })

        # Get metricas config
        metricas_config = {}
        try:
            moc = MetricasOrderConfig.objects.get(profile=profile, month_str='__default__')
            metricas_config = {
                'card_order': moc.card_order or [],
                'hidden_cards': moc.hidden_cards or [],
            }
        except MetricasOrderConfig.DoesNotExist:
            pass

        template_data = {
            'bank_accounts': accounts_data,
            'categories': categories_data,
            'recurring_templates': recurring_data,
            'rename_rules': rename_rules_data,
            'categorization_rules': categorization_rules_data,
            'cc_display_mode': profile.cc_display_mode,
            'savings_target_pct': float(profile.savings_target_pct),
            'investment_target_pct': float(profile.investment_target_pct),
            'investment_allocation': profile.investment_allocation,
            'budget_strategy': profile.budget_strategy,
            'metricas_config': metricas_config,
        }

        # Create the template
        name = request.data.get('name', f'{profile.name} - Config')
        description = request.data.get('description', f'Exported from {profile.name}')

        template = SetupTemplate.objects.create(
            profile=profile,
            name=name,
            description=description,
            template_data=template_data,
        )

        return Response(SetupTemplateSerializer(template).data, status=status.HTTP_201_CREATED)


class ProfileSetupStateView(APIView):
    """Get current profile's full config for pre-filling the wizard in edit mode."""

    def get(self, request, pk):
        try:
            profile = Profile.objects.get(pk=pk)
        except Profile.DoesNotExist:
            return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)

        # Build same structure as template_data
        accounts_data = []
        for acct in Account.objects.filter(profile=profile, is_active=True):
            accounts_data.append({
                'bank_template_id': str(acct.bank_template_id) if acct.bank_template_id else None,
                'display_name': acct.name,
                'account_type': acct.account_type,
                'closing_day': acct.closing_day,
                'due_day': acct.due_day,
                'credit_limit': float(acct.credit_limit) if acct.credit_limit else None,
            })

        categories_data = []
        for cat in Category.objects.filter(profile=profile, is_active=True):
            categories_data.append({
                'name': cat.name,
                'type': cat.category_type,
                'limit': float(cat.default_limit) if cat.default_limit else 0,
                'due_day': cat.due_day,
            })

        recurring_data = []
        for tmpl in RecurringTemplate.objects.filter(profile=profile, is_active=True):
            recurring_data.append({
                'name': tmpl.name,
                'type': tmpl.template_type,
                'amount': float(tmpl.default_limit) if tmpl.default_limit else 0,
                'due_day': tmpl.due_day,
            })

        rename_rules_data = []
        for rule in RenameRule.objects.filter(profile=profile, is_active=True):
            rename_rules_data.append({
                'keyword': rule.keyword,
                'display_name': rule.display_name,
            })

        categorization_rules_data = []
        for rule in CategorizationRule.objects.filter(profile=profile, is_active=True):
            categorization_rules_data.append({
                'keyword': rule.keyword,
                'category_name': rule.category.name if rule.category else '',
                'priority': rule.priority,
            })

        metricas_config = {}
        try:
            moc = MetricasOrderConfig.objects.get(profile=profile, month_str='__default__')
            metricas_config = {
                'card_order': moc.card_order or [],
                'hidden_cards': moc.hidden_cards or [],
            }
        except MetricasOrderConfig.DoesNotExist:
            pass

        return Response({
            'name': profile.name,
            'bank_accounts': accounts_data,
            'categories': categories_data,
            'recurring_templates': recurring_data,
            'rename_rules': rename_rules_data,
            'categorization_rules': categorization_rules_data,
            'cc_display_mode': profile.cc_display_mode,
            'savings_target_pct': float(profile.savings_target_pct),
            'investment_target_pct': float(profile.investment_target_pct),
            'investment_allocation': profile.investment_allocation,
            'budget_strategy': profile.budget_strategy,
            'metricas_config': metricas_config,
        })


class FamilyNoteViewSet(viewsets.ModelViewSet):
    """Shared family notes — not profile-scoped."""
    queryset = FamilyNote.objects.all()
    serializer_class = FamilyNoteSerializer
    pagination_class = None


REMINDER_LISTS = ["R&R Tarefas", "R&R Casa", "R&R Compras"]


class RemindersView(APIView):
    """GET /api/home/reminders/?list=R&R Tarefas"""

    def get(self, request):
        list_name = request.query_params.get('list', 'R&R Tarefas')
        if list_name not in REMINDER_LISTS:
            return Response(
                {'error': f'Invalid list: {list_name}. Must be one of {REMINDER_LISTS}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        script = f'''tell application "Reminders"
    set output to ""
    set theList to list "{list_name}"
    set theReminders to (reminders of theList whose completed is false)
    repeat with r in theReminders
        set rName to name of r
        set rDue to ""
        try
            set rDue to due date of r as text
        end try
        set rPriority to priority of r
        set rNotes to ""
        try
            set rNotes to body of r
        end try
        set output to output & rName & "||" & rDue & "||" & rPriority & "||" & rNotes & "\\n"
    end repeat
    return output
end tell'''

        try:
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode != 0:
                return Response(
                    {'error': result.stderr.strip()},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            reminders = []
            raw = result.stdout.strip()
            if raw:
                for line in raw.split('\\n'):
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split('||')
                    reminders.append({
                        'name': parts[0] if len(parts) > 0 else '',
                        'due_date': parts[1] if len(parts) > 1 else '',
                        'priority': parts[2] if len(parts) > 2 else '',
                        'notes': parts[3] if len(parts) > 3 else '',
                    })

            return Response({
                'list': list_name,
                'reminders': reminders,
                'count': len(reminders),
            })
        except subprocess.TimeoutExpired:
            return Response(
                {'error': 'Reminders request timed out'},
                status=status.HTTP_504_GATEWAY_TIMEOUT,
            )
        except Exception as e:
            logger.exception('RemindersView error')
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RemindersListsView(APIView):
    """GET /api/home/reminders/lists/ — Return available reminder list names."""

    def get(self, request):
        script = '''tell application "Reminders"
    set listNames to {}
    repeat with l in lists
        set end of listNames to name of l
    end repeat
    return listNames
end tell'''

        try:
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode != 0:
                return Response(
                    {'error': result.stderr.strip()},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            raw = result.stdout.strip()
            lists = [name.strip() for name in raw.split(',') if name.strip()]
            return Response({'lists': lists})
        except subprocess.TimeoutExpired:
            return Response(
                {'error': 'Reminders request timed out'},
                status=status.HTTP_504_GATEWAY_TIMEOUT,
            )
        except Exception as e:
            logger.exception('RemindersListsView error')
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RemindersAddView(APIView):
    """POST /api/home/reminders/add/ — Create a new reminder."""

    def post(self, request):
        name = request.data.get('name')
        list_name = request.data.get('list', 'R&R Tarefas')
        if not name:
            return Response({'error': 'name required'}, status=status.HTTP_400_BAD_REQUEST)

        sanitized_name = _sanitize_applescript_string(name)
        if not sanitized_name:
            return Response({'error': 'Invalid name after sanitization'}, status=status.HTTP_400_BAD_REQUEST)
        script = f'''tell application "Reminders"
    tell list "{list_name}"
        make new reminder with properties {{name:"{sanitized_name}"}}
    end tell
    return "ok"
end tell'''

        try:
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode != 0:
                return Response(
                    {'error': result.stderr.strip()},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            return Response({'status': 'ok', 'name': name, 'list': list_name})
        except subprocess.TimeoutExpired:
            return Response(
                {'error': 'Reminders request timed out'},
                status=status.HTTP_504_GATEWAY_TIMEOUT,
            )
        except Exception as e:
            logger.exception('RemindersAddView error')
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RemindersCompleteView(APIView):
    """POST /api/home/reminders/complete/ — Mark a reminder as complete."""

    def post(self, request):
        reminder_name = request.data.get('reminder_name')
        list_name = request.data.get('list', 'R&R Tarefas')
        if not reminder_name:
            return Response({'error': 'reminder_name required'}, status=status.HTTP_400_BAD_REQUEST)

        sanitized_name = _sanitize_applescript_string(reminder_name)
        if not sanitized_name:
            return Response({'error': 'Invalid name after sanitization'}, status=status.HTTP_400_BAD_REQUEST)
        script = f'''tell application "Reminders"
    set theList to list "{list_name}"
    set theReminders to (reminders of theList whose name is "{sanitized_name}" and completed is false)
    if (count of theReminders) > 0 then
        set completed of item 1 of theReminders to true
        return "ok"
    else
        return "not_found"
    end if
end tell'''

        try:
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode != 0:
                return Response(
                    {'error': result.stderr.strip()},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            output = result.stdout.strip()
            if output == 'not_found':
                return Response(
                    {'error': f'Reminder "{reminder_name}" not found in "{list_name}"'},
                    status=status.HTTP_404_NOT_FOUND,
                )
            return Response({'status': 'ok', 'reminder_name': reminder_name, 'list': list_name})
        except subprocess.TimeoutExpired:
            return Response(
                {'error': 'Reminders request timed out'},
                status=status.HTTP_504_GATEWAY_TIMEOUT,
            )
        except Exception as e:
            logger.exception('RemindersCompleteView error')
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ═══════════════════════════════════════════════════════════
# Google Calendar
# ═══════════════════════════════════════════════════════════

from . import google_calendar as gcal
from . import google_auth


# ─── Calendar (per-profile, multi-account) ───────────────────────────


def _get_calendar_redirect_uri(request):
    """Build the OAuth redirect URI from the incoming request."""
    return 'http://localhost:8001/api/home/calendar/oauth-callback/'


class CalendarAccountsView(APIView):
    """GET /api/calendar/accounts/ — list connected Google accounts for current profile."""

    def get(self, request):
        accounts = GoogleAccount.objects.filter(profile=request.profile)
        serializer = GoogleAccountSerializer(accounts, many=True)
        return Response({'accounts': serializer.data})


class CalendarConnectView(APIView):
    """POST /api/calendar/connect/ — start OAuth flow for current profile."""

    def post(self, request):
        redirect_uri = _get_calendar_redirect_uri(request)
        auth_url, err = google_auth.start_auth_flow(
            profile_id=request.profile.id,
            redirect_uri=redirect_uri,
        )
        if err:
            return Response({'error': err}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({'auth_url': auth_url})


class CalendarOAuthCallbackView(APIView):
    """GET /api/calendar/oauth-callback/?code=...&state=..."""

    def get(self, request):
        code = request.query_params.get('code')
        state = request.query_params.get('state')
        if not code or not state:
            return Response(
                {'error': 'code and state are required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            redirect_uri = _get_calendar_redirect_uri(request)
            token_data, profile_id, email, _scopes = google_auth.complete_auth_flow(
                code, state, redirect_uri=redirect_uri,
            )

            # Create or update the account
            account, created = GoogleAccount.objects.update_or_create(
                profile_id=profile_id,
                email=email,
                defaults={'token_data': token_data},
            )

            from django.shortcuts import redirect
            return redirect('http://localhost:5175/home')
        except Exception as e:
            logger.exception('Calendar OAuth callback error')
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CalendarDisconnectView(APIView):
    """DELETE /api/calendar/accounts/<uuid:account_id>/ — disconnect a Google account."""

    def delete(self, request, account_id):
        try:
            account = GoogleAccount.objects.get(
                id=account_id, profile=request.profile,
            )
        except GoogleAccount.DoesNotExist:
            return Response({'error': 'Account not found'}, status=status.HTTP_404_NOT_FOUND)
        account.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CalendarAvailableView(APIView):
    """GET /api/calendar/available/<uuid:account_id>/ — list calendars for a connected account."""

    def get(self, request, account_id):
        try:
            account = GoogleAccount.objects.get(
                id=account_id, profile=request.profile,
            )
        except GoogleAccount.DoesNotExist:
            return Response({'error': 'Account not found'}, status=status.HTTP_404_NOT_FOUND)

        calendars = gcal.list_calendars_for_account(account)
        if calendars is None:
            return Response(
                {'error': 'Failed to fetch calendars — token may be expired', 'connected': False},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        return Response({'calendars': calendars})


class CalendarSelectionsView(APIView):
    """
    GET  /api/calendar/selections/ — get current profile's calendar selections.
    PUT  /api/calendar/selections/ — bulk replace selections.
    """

    def get(self, request):
        selections = CalendarSelection.objects.filter(
            profile=request.profile,
        ).select_related('account')
        serializer = CalendarSelectionSerializer(selections, many=True)
        return Response({'selections': serializer.data})

    def put(self, request):
        incoming = request.data.get('selections', [])
        profile = request.profile

        # Delete existing selections for this profile
        CalendarSelection.objects.filter(profile=profile).delete()

        created = []
        for sel in incoming:
            try:
                account = GoogleAccount.objects.get(
                    id=sel['account_id'], profile=profile,
                )
            except (GoogleAccount.DoesNotExist, KeyError):
                continue

            obj = CalendarSelection.objects.create(
                profile=profile,
                account=account,
                calendar_id=sel.get('calendar_id', ''),
                calendar_name=sel.get('calendar_name', ''),
                color=sel.get('color', ''),
                show_in_home=sel.get('show_in_home', False),
                show_in_personal=sel.get('show_in_personal', True),
            )
            created.append(obj)

        serializer = CalendarSelectionSerializer(created, many=True)
        return Response({'selections': serializer.data})


class CalendarEventsView(APIView):
    """GET /api/calendar/events/?context=home|personal&time_min=...&time_max=..."""

    def get(self, request):
        context = request.query_params.get('context', 'home')
        time_min = request.query_params.get('time_min')
        time_max = request.query_params.get('time_max')

        if not time_min or not time_max:
            return Response(
                {'error': 'time_min and time_max are required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get relevant selections
        if context == 'home':
            selections = CalendarSelection.objects.filter(
                show_in_home=True,
            ).select_related('account')
        else:
            selections = CalendarSelection.objects.filter(
                profile=request.profile,
                show_in_personal=True,
            ).select_related('account')

        # Deduplicate: same calendar_id across different accounts → fetch once
        seen = set()
        all_events = []

        for sel in selections:
            cache_key = sel.calendar_id
            if cache_key in seen:
                continue
            seen.add(cache_key)

            try:
                events = gcal.get_events_for_account(
                    sel.account, sel.calendar_id, time_min, time_max,
                )
            except Exception as e:
                logger.warning(f'Failed to fetch events for {sel.calendar_name}: {e}')
                continue

            if events is None:
                continue

            for evt in events:
                evt['calendar'] = sel.calendar_name
                evt['calendar_color'] = sel.color or ''
                all_events.append(evt)

        # ── ICS feeds ──
        from .models import ICSFeed
        from . import ics_parser

        if context == 'home':
            ics_feeds = ICSFeed.objects.filter(show_in_home=True, is_active=True)
        else:
            ics_feeds = ICSFeed.objects.filter(
                profile=request.profile, show_in_personal=True, is_active=True,
            )

        for feed in ics_feeds:
            try:
                ics_events = ics_parser.fetch_and_parse(
                    feed.url, time_min, time_max, feed.name, feed.color,
                )
                all_events.extend(ics_events)
            except Exception as e:
                logger.warning(f'Failed to parse ICS feed {feed.name}: {e}')

        # ── Apple Calendar (host sidecar) ──
        import requests as http_requests
        try:
            sidecar_url = os.environ.get('REMINDERS_SIDECAR_URL', 'http://host.docker.internal:5177')
            resp = http_requests.get(
                f'{sidecar_url}/api/home/calendar/events/',
                params={'time_min': time_min, 'time_max': time_max},
                timeout=5,
            )
            if resp.status_code == 200:
                apple_data = resp.json()
                for evt in apple_data.get('events', []):
                    # Skip calendars already covered by Google Calendar selections
                    # (avoid duplicates for calendars synced to both)
                    cal_name = evt.get('calendar', '')
                    if cal_name in seen:
                        continue
                    # Add color based on calendar name
                    if not evt.get('calendar_color'):
                        evt['calendar_color'] = '#34a853'  # default green for Apple
                    all_events.append(evt)
        except Exception as e:
            logger.debug(f'Apple Calendar sidecar unavailable: {e}')

        all_events.sort(key=lambda e: e.get('start', ''))

        return Response({'events': all_events, 'count': len(all_events)})


class CalendarAddEventView(APIView):
    """POST /api/calendar/add-event/ — create an event."""

    def post(self, request):
        account_id = request.data.get('account_id')
        calendar_id = request.data.get('calendar_id')
        title = request.data.get('title', '').strip()
        start = request.data.get('start', '').strip()
        end = request.data.get('end', '').strip()
        location = request.data.get('location', '').strip()

        if not title or not start or not account_id or not calendar_id:
            return Response(
                {'error': 'account_id, calendar_id, title, and start are required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            account = GoogleAccount.objects.get(
                id=account_id, profile=request.profile,
            )
        except GoogleAccount.DoesNotExist:
            return Response({'error': 'Account not found'}, status=status.HTTP_404_NOT_FOUND)

        result = gcal.add_event_for_account(
            account, calendar_id, title, start, end or start, location,
        )
        if result is None:
            return Response(
                {'error': 'Failed to create event — token may be expired'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        return Response(result, status=status.HTTP_201_CREATED)


class SalaryProjectionView(APIView):
    """
    GET /api/salary/projection/?months=12&month_str=2026-03
    Returns salary projection with live USD/BRL rate.
    """
    def get(self, request):
        months = int(request.query_params.get('months', 12))
        month_str = request.query_params.get('month_str')
        result = compute_salary_projection(request.profile, months, month_str)
        if 'error' in result:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        return Response(result)


class SalarySyncView(APIView):
    """
    POST /api/salary/sync/?months=12&month_str=2026-03
    Compute salary projection and write BudgetConfig overrides
    for the linked income template.
    """
    def post(self, request):
        months = int(request.query_params.get('months', 12))
        month_str = request.query_params.get('month_str')
        result = sync_salary_to_budget(request.profile, months, month_str)
        if 'error' in result:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        return Response(result)


class PluggySyncView(APIView):
    """
    POST /api/sync/pluggy/ — trigger Pluggy sync for current profile
    GET  /api/sync/pluggy/ — get last sync status
    """
    def post(self, request):
        from .models import Profile
        from django.core.cache import cache
        from django.utils import timezone
        save_balance = request.data.get('save_balance', True)
        all_output = []
        all_success = True
        for p in Profile.objects.filter(is_active=True):
            try:
                cmd = ['python', 'manage.py', 'sync_pluggy', '--profile', p.name, '--refresh']
                if save_balance:
                    cmd.append('--save-balance')
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                all_output.append(f'=== {p.name} ===\n{result.stdout}{result.stderr}')
                if result.returncode != 0:
                    all_success = False
                cache.set(f'pluggy_last_sync_{p.id}', timezone.now().isoformat(), timeout=None)
            except subprocess.TimeoutExpired:
                all_output.append(f'=== {p.name} === TIMEOUT')
                all_success = False
            except Exception as e:
                all_output.append(f'=== {p.name} === ERROR: {e}')
                all_success = False
        output = '\n'.join(all_output)
        return Response({
            'success': all_success,
            'output': output[-4000:],
        }, status=200 if all_success else 500)

    def get(self, request):
        from django.core.cache import cache
        profile = request.profile
        last_sync = cache.get(f'pluggy_last_sync_{profile.id}') if profile else None
        return Response({'last_sync': last_sync})


class SalaryConfigView(APIView):
    """
    GET /api/salary/config/ — return current config
    PUT /api/salary/config/ — update config
    """
    def get(self, request):
        try:
            cfg = SalaryConfig.objects.get(profile=request.profile)
            return Response({
                'hourly_rate_usd': float(cfg.hourly_rate_usd),
                'hours_per_day': float(cfg.hours_per_day),
                'wise_fee_pct': float(cfg.wise_fee_pct),
                'wise_fee_flat': float(cfg.wise_fee_flat),
                'tax_hold_pct': float(cfg.tax_hold_pct),
                'advance_total_usd': float(cfg.advance_total_usd),
                'advance_start_date': cfg.advance_start_date,
                'advance_num_cycles': cfg.advance_num_cycles,
                'income_template_id': str(cfg.income_template_id) if cfg.income_template_id else None,
                'is_active': cfg.is_active,
            })
        except SalaryConfig.DoesNotExist:
            return Response({'error': 'No SalaryConfig'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request):
        data = request.data
        cfg, _ = SalaryConfig.objects.update_or_create(
            profile=request.profile,
            defaults={
                'hourly_rate_usd': data.get('hourly_rate_usd', 52),
                'hours_per_day': data.get('hours_per_day', 8),
                'wise_fee_pct': data.get('wise_fee_pct', 0.0091),
                'wise_fee_flat': data.get('wise_fee_flat', 0.46),
                'tax_hold_pct': data.get('tax_hold_pct', 0.08),
                'advance_total_usd': data.get('advance_total_usd', 0),
                'advance_start_date': data.get('advance_start_date', ''),
                'advance_num_cycles': data.get('advance_num_cycles', 0),
                'income_template_id': data.get('income_template_id'),
                'is_active': data.get('is_active', True),
            },
        )
        return Response({'status': 'ok', 'id': str(cfg.id)})


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer

    def get_queryset(self):
        return Project.objects.filter(profile=self.request.profile)

    def perform_create(self, serializer):
        serializer.save(profile=self.request.profile)


class PersonalTaskViewSet(viewsets.ModelViewSet):
    serializer_class = PersonalTaskSerializer

    def get_queryset(self):
        qs = PersonalTask.objects.filter(profile=self.request.profile).select_related('project')
        project = self.request.query_params.get('project')
        if project:
            qs = qs.filter(project_id=project)
        status = self.request.query_params.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs

    def perform_create(self, serializer):
        serializer.save(profile=self.request.profile)


class PersonalNoteViewSet(viewsets.ModelViewSet):
    serializer_class = PersonalNoteSerializer

    def get_queryset(self):
        qs = PersonalNote.objects.filter(profile=self.request.profile).select_related('project')
        project = self.request.query_params.get('project')
        if project:
            qs = qs.filter(project_id=project)
        return qs

    def perform_create(self, serializer):
        serializer.save(profile=self.request.profile)


# ── ICS Feed Management ────────────────────────────────────

class ICSFeedView(APIView):
    """GET/POST /api/calendar/ics-feeds/ — list or create ICS subscriptions."""

    def get(self, request):
        from .models import ICSFeed
        feeds = ICSFeed.objects.filter(profile=request.profile)
        return Response([
            {
                'id': str(f.id), 'name': f.name, 'url': f.url,
                'color': f.color, 'show_in_home': f.show_in_home,
                'show_in_personal': f.show_in_personal, 'is_active': f.is_active,
            }
            for f in feeds
        ])

    def post(self, request):
        from .models import ICSFeed
        name = request.data.get('name', '').strip()
        url = request.data.get('url', '').strip()
        color = request.data.get('color', '#4285f4').strip()

        if not name or not url:
            return Response({'error': 'name and url are required'}, status=status.HTTP_400_BAD_REQUEST)

        feed = ICSFeed.objects.create(
            profile=request.profile, name=name, url=url, color=color,
            show_in_home=request.data.get('show_in_home', False),
            show_in_personal=request.data.get('show_in_personal', True),
        )
        return Response({'id': str(feed.id), 'name': feed.name, 'url': feed.url, 'color': feed.color})


class ICSFeedDetailView(APIView):
    """DELETE /api/calendar/ics-feeds/<uuid:feed_id>/"""

    def delete(self, request, feed_id):
        from .models import ICSFeed
        try:
            feed = ICSFeed.objects.get(id=feed_id, profile=request.profile)
            feed.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ICSFeed.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)


# ── Saúde / Health ────────────────────────────────────────────

class HealthExamViewSet(viewsets.ModelViewSet):
    """Health exams scoped per profile.
    Filters: ?tipo=hemograma&pregnancy_id=<uuid>&since=YYYY-MM-DD"""
    serializer_class = HealthExamSerializer

    def get_queryset(self):
        qs = HealthExam.objects.filter(profile=self.request.profile)
        tipo = self.request.query_params.get('tipo')
        if tipo:
            qs = qs.filter(tipo=tipo)
        preg = self.request.query_params.get('pregnancy_id')
        if preg:
            qs = qs.filter(pregnancy_id=preg)
        since = self.request.query_params.get('since')
        if since:
            qs = qs.filter(data__gte=since)
        return qs

    def perform_create(self, serializer):
        serializer.save(profile=self.request.profile)


class VitalReadingViewSet(viewsets.ModelViewSet):
    serializer_class = VitalReadingSerializer

    def get_queryset(self):
        qs = VitalReading.objects.filter(profile=self.request.profile)
        tipo = self.request.query_params.get('tipo')
        if tipo:
            qs = qs.filter(tipo=tipo)
        preg = self.request.query_params.get('pregnancy_id')
        if preg:
            qs = qs.filter(pregnancy_id=preg)
        return qs

    def perform_create(self, serializer):
        serializer.save(profile=self.request.profile)


class PregnancyViewSet(viewsets.ModelViewSet):
    """Pregnancies are shared between titular and gestante.
    Returns pregnancies where the current profile is EITHER titular OR gestante."""
    serializer_class = PregnancySerializer

    def get_queryset(self):
        from django.db.models import Q
        return Pregnancy.objects.filter(
            Q(titular=self.request.profile) | Q(gestante=self.request.profile)
        ).select_related('titular', 'gestante').prefetch_related('consultations')


class PrenatalConsultationViewSet(viewsets.ModelViewSet):
    serializer_class = PrenatalConsultationSerializer

    def get_queryset(self):
        from django.db.models import Q
        qs = PrenatalConsultation.objects.filter(
            Q(pregnancy__titular=self.request.profile) | Q(pregnancy__gestante=self.request.profile)
        ).select_related('pregnancy')
        preg = self.request.query_params.get('pregnancy_id')
        if preg:
            qs = qs.filter(pregnancy_id=preg)
        return qs
