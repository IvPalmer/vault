import logging
import os
import re

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

logger = logging.getLogger(__name__)

MONTH_STR_RE = re.compile(r'^\d{4}-(?:0[1-9]|1[0-2])$')


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
    RenameRule, Transaction, RecurringMapping, RecurringTemplate,
    BudgetConfig, BalanceOverride,
)
from .serializers import (
    AccountSerializer, CategorySerializer, SubcategorySerializer,
    CategorizationRuleSerializer, RenameRuleSerializer,
    TransactionSerializer, TransactionListSerializer,
    RecurringMappingSerializer, RecurringTemplateSerializer,
    BudgetConfigSerializer, BalanceOverrideSerializer,
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
)
from .models import CustomMetric


class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filterset_fields = ['category_type', 'is_active']
    search_fields = ['name']
    pagination_class = None  # Always return full list (used as dropdown data)


class SubcategoryViewSet(viewsets.ModelViewSet):
    queryset = Subcategory.objects.all()
    serializer_class = SubcategorySerializer
    filterset_fields = ['category']
    pagination_class = None


class CategorizationRuleViewSet(viewsets.ModelViewSet):
    queryset = CategorizationRule.objects.all()
    serializer_class = CategorizationRuleSerializer
    filterset_fields = ['category', 'is_active']
    search_fields = ['keyword']
    pagination_class = None  # Rules list needs to be complete for settings UI


class RenameRuleViewSet(viewsets.ModelViewSet):
    queryset = RenameRule.objects.all()
    serializer_class = RenameRuleSerializer
    search_fields = ['keyword', 'display_name']
    pagination_class = None


class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.select_related('account', 'category').all()
    filterset_fields = ['month_str', 'account', 'category', 'is_recurring', 'is_internal_transfer']
    search_fields = ['description', 'description_original']
    ordering_fields = ['date', 'amount', 'description']

    def get_serializer_class(self):
        if self.action == 'list':
            return TransactionListSerializer
        return TransactionSerializer

    @action(detail=False, methods=['get'])
    def months(self, request):
        """Return list of available months, sorted descending.

        Extends beyond real transaction data to include future months up to the
        last projected installment, so the user can browse forward projections.
        """
        real_months = list(
            Transaction.objects
            .values_list('month_str', flat=True)
            .distinct()
            .order_by('-month_str')
        )

        last_inst_month = get_last_installment_month()
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
        updated = Transaction.objects.filter(id__in=transaction_ids).update(**update_fields)

        # Learning feedback: find similar uncategorized + suggest rule
        feedback = {}
        if len(transaction_ids) == 1:
            try:
                feedback = find_similar_transactions(transaction_ids[0])
            except Transaction.DoesNotExist:
                pass

        return Response({'updated': updated, **feedback})


class RecurringMappingViewSet(viewsets.ModelViewSet):
    queryset = RecurringMapping.objects.select_related('template', 'category', 'transaction').all()
    serializer_class = RecurringMappingSerializer
    filterset_fields = ['month_str', 'status']

    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generate recurring mappings for a given month from RecurringTemplate."""
        month_str = request.data.get('month_str')
        if not month_str:
            return Response(
                {'error': 'month_str required'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        templates = RecurringTemplate.objects.filter(is_active=True)
        created = 0
        for tpl in templates:
            _, was_created = RecurringMapping.objects.get_or_create(
                template=tpl,
                month_str=month_str,
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
            month_str=month_str, status='missing'
        ).select_related('template', 'category')

        matched = 0
        for mapping in mappings:
            # For category-match mode, try by taxonomy category
            if mapping.match_mode == 'category' and mapping.category:
                txn = Transaction.objects.filter(
                    month_str=month_str,
                    category=mapping.category,
                    is_internal_transfer=False,
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
        return Response(get_metricas(month_str))


class RecurringDataView(APIView):
    """GET /api/analytics/recurring/?month_str=2026-01"""
    def get(self, request):
        month_str = request.query_params.get('month_str')
        err = _validate_month_str(month_str)
        if err:
            return err
        return Response(get_recurring_data(month_str))


class CardTransactionsView(APIView):
    """GET /api/analytics/cards/?month_str=2026-01&account=Master"""
    def get(self, request):
        month_str = request.query_params.get('month_str')
        err = _validate_month_str(month_str)
        if err:
            return err
        account_filter = request.query_params.get('account', None)
        return Response(get_card_transactions(month_str, account_filter))


class VariableTransactionsView(APIView):
    """GET /api/analytics/variable/?month_str=2026-01"""
    def get(self, request):
        month_str = request.query_params.get('month_str')
        err = _validate_month_str(month_str)
        if err:
            return err
        return Response(get_variable_transactions(month_str))


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
            return Response(get_mapping_candidates(month_str, category_id=category_id, mapping_id=mapping_id))
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
                transaction_id, category_id=category_id, mapping_id=mapping_id
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
            result = unmap_transaction(transaction_id, mapping_id=mapping_id)
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
            mapping = RecurringMapping.objects.get(id=mapping_id)
            mapping.match_mode = match_mode
            if match_mode == 'category' and category_id:
                # Only clear M2M when explicitly selecting a category
                # This prevents data loss from just clicking the tab
                mapping.transactions.clear()
                mapping.transaction = None
                mapping.actual_amount = None
                mapping.status = 'missing'  # Will be recomputed on next fetch
                try:
                    cat = Category.objects.get(id=category_id)
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

    SAMPLE_DATA_DIR = os.path.join(
        os.path.dirname(__file__), '..', '..', 'FinanceDashboard', 'SampleData'
    )

    def get(self, request):
        """Return current import status."""
        from django.db.models import Min, Max
        txn_count = Transaction.objects.count()
        month_count = Transaction.objects.values('month_str').distinct().count()
        date_range = Transaction.objects.aggregate(
            earliest=Min('date'), latest=Max('date')
        )
        accounts = {}
        for acct in Account.objects.all():
            c = Transaction.objects.filter(account=acct).count()
            if c > 0:
                accounts[acct.name] = c

        # List files in SampleData
        sample_dir = os.path.abspath(self.SAMPLE_DATA_DIR)
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
        else:
            return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)

    def _handle_upload(self, request):
        """Save uploaded files to SampleData with correct naming."""
        import re

        files = request.FILES.getlist('files')
        if not files:
            return Response({'error': 'No files provided'}, status=status.HTTP_400_BAD_REQUEST)

        sample_dir = os.path.abspath(self.SAMPLE_DATA_DIR)
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

        # Credit card CSV: itau-master-YYYYMMDD.csv or itau-visa-YYYYMMDD.csv
        card_match = re.match(
            r'itau-(master|visa)-(\d{4})(\d{2})\d{2}\.csv', lower
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

    def _handle_import(self, request):
        """Trigger a full re-import using the management command."""
        from django.core.management import call_command
        from io import StringIO

        stdout_capture = StringIO()
        stderr_capture = StringIO()

        try:
            call_command(
                'import_legacy_data',
                '--clear',
                stdout=stdout_capture,
                stderr=stderr_capture,
            )
            output = stdout_capture.getvalue()

            # Extract key stats from output
            txn_count = Transaction.objects.count()
            month_count = Transaction.objects.values('month_str').distinct().count()

            return Response({
                'success': True,
                'transactions': txn_count,
                'months': month_count,
                'output': output[-2000:],  # Last 2000 chars of output
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
            result = initialize_month(month_str)
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
            result = update_recurring_expected(mapping_id, expected_amount)
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
            result = update_recurring_item(mapping_id, **kwargs)
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
            result = add_custom_recurring(month_str, name, template_type, expected_amount)
            return Response(result, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        mapping_id = request.data.get('mapping_id')
        if not mapping_id:
            return Response({'error': 'mapping_id required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            result = delete_custom_recurring(mapping_id)
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
            result = skip_recurring(mapping_id)
            return Response(result)
        except RecurringMapping.DoesNotExist:
            return Response({'error': 'Mapping not found'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request):
        mapping_id = request.data.get('mapping_id')
        if not mapping_id:
            return Response({'error': 'mapping_id required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            result = unskip_recurring(mapping_id)
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
            result = save_balance_override(month_str, balance)
            return Response(result)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class BudgetConfigViewSet(viewsets.ModelViewSet):
    queryset = BudgetConfig.objects.select_related('category', 'template').all()
    serializer_class = BudgetConfigSerializer
    filterset_fields = ['month_str', 'category']


class BalanceOverrideViewSet(viewsets.ModelViewSet):
    queryset = BalanceOverride.objects.all()
    serializer_class = BalanceOverrideSerializer
    filterset_fields = ['month_str']


class ProjectionView(APIView):
    """GET /api/analytics/projection/?month_str=2025-12&months=6"""
    def get(self, request):
        month_str = request.query_params.get('month_str')
        err = _validate_month_str(month_str)
        if err:
            return err
        try:
            num_months = int(request.query_params.get('months', 6))
        except (ValueError, TypeError):
            return Response({'error': 'months must be an integer'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            return Response(get_projection(month_str, num_months))
        except Exception as e:
            logger.exception('ProjectionView error')
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class OrcamentoView(APIView):
    """GET /api/analytics/orcamento/?month_str=2025-12"""
    def get(self, request):
        month_str = request.query_params.get('month_str')
        err = _validate_month_str(month_str)
        if err:
            return err
        try:
            return Response(get_orcamento(month_str))
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
            return Response(get_installment_details(month_str))
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
                transaction_id, category_id, subcategory_id
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
            result = smart_categorize(month_str=month_str, dry_run=dry_run)
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
            return Response(get_recurring_templates())
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
            result = create_recurring_template(name, template_type, default_limit, due_day)
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
            result = update_recurring_template(template_id, **kwargs)
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
            result = delete_recurring_template(template_id)
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
            result = reapply_template_to_month(month_str)
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
        data = get_checking_transactions(month_str)
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
            result = auto_link_recurring(month_str)
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
            RecurringMapping.objects.filter(month_str=month_str)
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
            data = get_month_categories(month_str)
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
        return Response(get_metricas_order(month_str))

    def post(self, request):
        month_str = request.data.get('month_str')
        card_order = request.data.get('card_order')
        hidden_cards = request.data.get('hidden_cards')
        if not month_str or not card_order:
            return Response({'error': 'month_str and card_order required'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(save_metricas_order(month_str, card_order, hidden_cards))


class MetricasMakeDefaultView(APIView):
    """POST /api/analytics/metricas/make-default/  { card_order: [...], hidden_cards: [...] }"""
    def post(self, request):
        card_order = request.data.get('card_order')
        hidden_cards = request.data.get('hidden_cards')
        if not card_order:
            return Response({'error': 'card_order required'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(make_default_order(card_order, hidden_cards))


class MetricasLockView(APIView):
    """POST /api/analytics/metricas/lock/  { month_str, locked: true/false }"""
    def post(self, request):
        month_str = request.data.get('month_str')
        locked = request.data.get('locked')
        if not month_str or locked is None:
            return Response({'error': 'month_str and locked required'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(toggle_metricas_lock(month_str, locked))


class CustomMetricsView(APIView):
    """
    GET    /api/analytics/metricas/custom/  — List definitions + options
    POST   /api/analytics/metricas/custom/  — Create custom metric
    DELETE /api/analytics/metricas/custom/  — Delete { id }
    """
    def get(self, request):
        return Response(get_custom_metric_options())

    def post(self, request):
        metric_type = request.data.get('metric_type')
        label = request.data.get('label')
        config = request.data.get('config', {})
        color = request.data.get('color', 'var(--color-accent)')
        if not metric_type or not label:
            return Response({'error': 'metric_type and label required'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(create_custom_metric(metric_type, label, config, color), status=status.HTTP_201_CREATED)

    def delete(self, request):
        metric_id = request.data.get('id')
        if not metric_id:
            return Response({'error': 'id required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            return Response(delete_custom_metric(metric_id))
        except CustomMetric.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)


class TransactionRenameView(APIView):
    """
    POST /api/transactions/rename/
    Rename a transaction description with optional propagation to similar ones.

    Preview mode:  { transaction_id, new_description }
    → Returns renamed count + list of similar transactions for user confirmation.

    Apply mode:    { transaction_ids: [...], new_description, propagate: true }
    → Renames all selected + creates RenameRule for future imports.
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
                result = rename_transaction(transaction_id, new_description, propagate_ids=transaction_ids)
                return Response(result)
            except Transaction.DoesNotExist:
                return Response({'error': 'Transaction not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            # Preview mode
            transaction_id = request.data.get('transaction_id')
            if not transaction_id:
                return Response({'error': 'transaction_id required'}, status=status.HTTP_400_BAD_REQUEST)
            try:
                result = rename_transaction(transaction_id, new_description)
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
            return Response(find_similar_transactions(transaction_id))
        except Transaction.DoesNotExist:
            return Response({'error': 'Transaction not found'}, status=status.HTTP_404_NOT_FOUND)
