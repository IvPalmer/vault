import os

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from .models import (
    Account, Category, Subcategory, CategorizationRule,
    RenameRule, Transaction, RecurringMapping, BudgetConfig,
    BalanceOverride,
)
from .serializers import (
    AccountSerializer, CategorySerializer, SubcategorySerializer,
    CategorizationRuleSerializer, RenameRuleSerializer,
    TransactionSerializer, TransactionListSerializer,
    RecurringMappingSerializer, BudgetConfigSerializer,
    BalanceOverrideSerializer,
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
)


class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filterset_fields = ['category_type', 'is_active']
    search_fields = ['name']


class SubcategoryViewSet(viewsets.ModelViewSet):
    queryset = Subcategory.objects.all()
    serializer_class = SubcategorySerializer
    filterset_fields = ['category']


class CategorizationRuleViewSet(viewsets.ModelViewSet):
    queryset = CategorizationRule.objects.all()
    serializer_class = CategorizationRuleSerializer
    filterset_fields = ['category', 'is_active']
    search_fields = ['keyword']


class RenameRuleViewSet(viewsets.ModelViewSet):
    queryset = RenameRule.objects.all()
    serializer_class = RenameRuleSerializer
    search_fields = ['keyword', 'display_name']


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
        """Bulk re-categorize selected transactions."""
        transaction_ids = request.data.get('transaction_ids', [])
        category_id = request.data.get('category_id')
        if not transaction_ids or not category_id:
            return Response(
                {'error': 'transaction_ids and category_id required'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        updated = Transaction.objects.filter(id__in=transaction_ids).update(
            category_id=category_id, is_manually_categorized=True
        )
        return Response({'updated': updated})


class RecurringMappingViewSet(viewsets.ModelViewSet):
    queryset = RecurringMapping.objects.select_related('category', 'transaction').all()
    serializer_class = RecurringMappingSerializer
    filterset_fields = ['month_str', 'status']

    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generate recurring mappings for a given month."""
        month_str = request.data.get('month_str')
        if not month_str:
            return Response(
                {'error': 'month_str required'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Get categories that should have recurring mappings (Fixo, Income, Investimento)
        categories = Category.objects.filter(
            category_type__in=['Fixo', 'Income', 'Investimento'],
            is_active=True,
        )
        created = 0
        for cat in categories:
            _, was_created = RecurringMapping.objects.get_or_create(
                category=cat,
                month_str=month_str,
                defaults={
                    'expected_amount': cat.default_limit,
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
        ).select_related('category')

        matched = 0
        for mapping in mappings:
            # Try to find a transaction matching this category in this month
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
        if not month_str:
            return Response({'error': 'month_str required'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(get_metricas(month_str))


class RecurringDataView(APIView):
    """GET /api/analytics/recurring/?month_str=2026-01"""
    def get(self, request):
        month_str = request.query_params.get('month_str')
        if not month_str:
            return Response({'error': 'month_str required'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(get_recurring_data(month_str))


class CardTransactionsView(APIView):
    """GET /api/analytics/cards/?month_str=2026-01&account=Master"""
    def get(self, request):
        month_str = request.query_params.get('month_str')
        if not month_str:
            return Response({'error': 'month_str required'}, status=status.HTTP_400_BAD_REQUEST)
        account_filter = request.query_params.get('account', None)
        return Response(get_card_transactions(month_str, account_filter))


class VariableTransactionsView(APIView):
    """GET /api/analytics/variable/?month_str=2026-01"""
    def get(self, request):
        month_str = request.query_params.get('month_str')
        if not month_str:
            return Response({'error': 'month_str required'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(get_variable_transactions(month_str))


class MappingCandidatesView(APIView):
    """GET /api/analytics/recurring/candidates/?month_str=2026-01&category_id=uuid&mapping_id=uuid"""
    def get(self, request):
        month_str = request.query_params.get('month_str')
        category_id = request.query_params.get('category_id')
        mapping_id = request.query_params.get('mapping_id')
        if not month_str or (not category_id and not mapping_id):
            return Response(
                {'error': 'month_str and (category_id or mapping_id) required'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            return Response(get_mapping_candidates(month_str, category_id=category_id, mapping_id=mapping_id))
        except Exception as e:
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
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        transaction_id = request.data.get('transaction_id')
        if not transaction_id:
            return Response(
                {'error': 'transaction_id required'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            result = unmap_transaction(transaction_id)
            return Response(result)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


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
        for field in ('name', 'category_type', 'expected_amount', 'due_day'):
            if field in request.data:
                kwargs[field] = request.data[field]
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
        category_type = request.data.get('category_type', 'Fixo')
        expected_amount = request.data.get('expected_amount', 0)
        if not month_str or not name:
            return Response(
                {'error': 'month_str and name required'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            result = add_custom_recurring(month_str, name, category_type, expected_amount)
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
    queryset = BudgetConfig.objects.select_related('category').all()
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
        if not month_str:
            return Response({'error': 'month_str required'}, status=status.HTTP_400_BAD_REQUEST)
        num_months = int(request.query_params.get('months', 6))
        try:
            return Response(get_projection(month_str, num_months))
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class OrcamentoView(APIView):
    """GET /api/analytics/orcamento/?month_str=2025-12"""
    def get(self, request):
        month_str = request.query_params.get('month_str')
        if not month_str:
            return Response({'error': 'month_str required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            return Response(get_orcamento(month_str))
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class InstallmentDetailsView(APIView):
    """GET /api/analytics/installments/?month_str=2026-02"""
    def get(self, request):
        month_str = request.query_params.get('month_str')
        if not month_str:
            return Response({'error': 'month_str required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            return Response(get_installment_details(month_str))
        except Exception as e:
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
        category_type = request.data.get('category_type', 'Fixo')
        default_limit = request.data.get('default_limit', 0)
        due_day = request.data.get('due_day')
        if not name:
            return Response({'error': 'name required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            result = create_recurring_template(name, category_type, default_limit, due_day)
            return Response(result, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        category_id = request.data.get('id')
        if not category_id:
            return Response({'error': 'id required'}, status=status.HTTP_400_BAD_REQUEST)
        kwargs = {}
        for field in ('name', 'category_type', 'default_limit', 'due_day', 'display_order'):
            if field in request.data:
                kwargs[field] = request.data[field]
        if not kwargs:
            return Response({'error': 'At least one field required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            result = update_recurring_template(category_id, **kwargs)
            return Response(result)
        except Category.DoesNotExist:
            return Response({'error': 'Template not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        category_id = request.data.get('id')
        if not category_id:
            return Response({'error': 'id required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            result = delete_recurring_template(category_id)
            return Response(result)
        except Category.DoesNotExist:
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
        if not month_str:
            return Response({'error': 'month_str required'}, status=status.HTTP_400_BAD_REQUEST)
        data = get_checking_transactions(month_str)
        return Response(data)
