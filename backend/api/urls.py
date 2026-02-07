from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AccountViewSet, CategoryViewSet, SubcategoryViewSet,
    CategorizationRuleViewSet, RenameRuleViewSet,
    TransactionViewSet, RecurringMappingViewSet,
    BudgetConfigViewSet, BalanceOverrideViewSet,
    AnalyticsMetricasView,
    RecurringDataView, CardTransactionsView, VariableTransactionsView,
    MappingCandidatesView, MapTransactionView,
    ImportStatementsView,
    RecurringInitializeView, RecurringExpectedView, RecurringUpdateView,
    RecurringCustomView, RecurringSkipView, BalanceSaveView,
    ProjectionView, OrcamentoView,
    SmartCategorizeView, InstallmentDetailsView,
    RecurringTemplatesView, ReapplyTemplateView,
    CheckingTransactionsView,
)

router = DefaultRouter()
router.register(r'accounts', AccountViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'subcategories', SubcategoryViewSet)
router.register(r'rules', CategorizationRuleViewSet)
router.register(r'renames', RenameRuleViewSet)
router.register(r'transactions', TransactionViewSet)
router.register(r'recurring-mappings', RecurringMappingViewSet)
router.register(r'budget-configs', BudgetConfigViewSet)
router.register(r'balance-overrides', BalanceOverrideViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('analytics/metricas/', AnalyticsMetricasView.as_view(), name='analytics-metricas'),
    path('analytics/recurring/', RecurringDataView.as_view(), name='analytics-recurring'),
    path('analytics/cards/', CardTransactionsView.as_view(), name='analytics-cards'),
    path('analytics/variable/', VariableTransactionsView.as_view(), name='analytics-variable'),
    path('analytics/recurring/candidates/', MappingCandidatesView.as_view(), name='mapping-candidates'),
    path('analytics/recurring/map/', MapTransactionView.as_view(), name='map-transaction'),
    # Phase A: new recurring management endpoints
    path('analytics/recurring/initialize/', RecurringInitializeView.as_view(), name='recurring-initialize'),
    path('analytics/recurring/expected/', RecurringExpectedView.as_view(), name='recurring-expected'),
    path('analytics/recurring/update/', RecurringUpdateView.as_view(), name='recurring-update'),
    path('analytics/recurring/custom/', RecurringCustomView.as_view(), name='recurring-custom'),
    path('analytics/recurring/skip/', RecurringSkipView.as_view(), name='recurring-skip'),
    path('analytics/balance/', BalanceSaveView.as_view(), name='balance-save'),
    # Phase B: projection + orçamento
    path('analytics/projection/', ProjectionView.as_view(), name='analytics-projection'),
    path('analytics/orcamento/', OrcamentoView.as_view(), name='analytics-orcamento'),
    # Installment details
    path('analytics/installments/', InstallmentDetailsView.as_view(), name='analytics-installments'),
    # Smart categorization
    path('analytics/smart-categorize/', SmartCategorizeView.as_view(), name='smart-categorize'),
    # Recurring templates (Settings)
    path('analytics/recurring/templates/', RecurringTemplatesView.as_view(), name='recurring-templates'),
    path('analytics/recurring/reapply/', ReapplyTemplateView.as_view(), name='recurring-reapply'),
    # Checking account
    path('analytics/checking/', CheckingTransactionsView.as_view(), name='analytics-checking'),
    path('import/', ImportStatementsView.as_view(), name='import-statements'),
]
