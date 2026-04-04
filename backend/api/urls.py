from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProfileViewSet, BankTemplateViewSet,
    AccountViewSet, CategoryViewSet, SubcategoryViewSet,
    CategoryTreeView, CategoryBulkReassignView,
    PluggyCategoryMappingViewSet, CategorizationRuleViewSet, RenameRuleViewSet,
    TransactionViewSet, RecurringMappingViewSet,
    BudgetConfigViewSet, BalanceOverrideViewSet,
    AnalyticsMetricasView,
    RecurringDataView, CardTransactionsView, VariableTransactionsView,
    MappingCandidatesView, MapTransactionView, ToggleMatchModeView,
    ImportStatementsView,
    RecurringInitializeView, RecurringExpectedView, RecurringUpdateView,
    RecurringCustomView, RecurringSkipView, BalanceSaveView,
    ProjectionView, OrcamentoView, AnalyticsTrendsView, SpendingInsightsView,
    SmartCategorizeView, InstallmentDetailsView,
    RecurringTemplatesView, ReapplyTemplateView,
    CheckingTransactionsView,
    MonthCategoriesView,
    AutoLinkRecurringView,
    RecurringReorderView,
    MetricasOrderView, MetricasMakeDefaultView, MetricasLockView,
    CustomMetricsView,
    TransactionRenameView,
    TransactionSimilarView,
    CategorizeInstallmentView,
    AnalyzeSetupView,
    ProfileSetupView,
    SetupTemplateViewSet,
    ExportSetupView,
    ProfileSetupStateView,
    FamilyNoteViewSet,
    RemindersView, RemindersAddView, RemindersCompleteView, RemindersListsView,
    CalendarAccountsView, CalendarConnectView, CalendarOAuthCallbackView,
    CalendarDisconnectView, CalendarAvailableView, CalendarSelectionsView,
    CalendarEventsView, CalendarAddEventView,
    SalaryProjectionView, SalarySyncView, SalaryConfigView,
    PluggySyncView,
    ProjectViewSet, PersonalTaskViewSet, PersonalNoteViewSet,
)
from .auth_views import GoogleLoginView, TokenRefreshView, AuthMeView
from .google_views import (
    GoogleConnectView, GoogleOAuthCallbackView, GoogleAccountsView,
    GmailMessagesView, GmailMessageDetailView, GmailSendView,
    GmailTrashView, GmailLabelsView,
    DriveFilesView, DriveFileContentView, SpreadsheetView, DocumentView,
)

router = DefaultRouter()
router.register(r'profiles', ProfileViewSet, basename='profile')
router.register(r'bank-templates', BankTemplateViewSet, basename='banktemplate')
router.register(r'accounts', AccountViewSet, basename='account')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'subcategories', SubcategoryViewSet, basename='subcategory')
router.register(r'pluggy-category-mappings', PluggyCategoryMappingViewSet, basename='pluggycategorymapping')
router.register(r'rules', CategorizationRuleViewSet, basename='categorizationrule')
router.register(r'renames', RenameRuleViewSet, basename='renamerule')
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'recurring-mappings', RecurringMappingViewSet, basename='recurringmapping')
router.register(r'budget-configs', BudgetConfigViewSet, basename='budgetconfig')
router.register(r'balance-overrides', BalanceOverrideViewSet, basename='balanceoverride')
router.register(r'setup-templates', SetupTemplateViewSet, basename='setuptemplate')
router.register(r'home/notes', FamilyNoteViewSet, basename='familynote')
router.register(r'pessoal/projects', ProjectViewSet, basename='project')
router.register(r'pessoal/tasks', PersonalTaskViewSet, basename='personaltask')
router.register(r'pessoal/notes', PersonalNoteViewSet, basename='personalnote')

urlpatterns = [
    # Auth
    path('auth/google/', GoogleLoginView.as_view(), name='auth-google'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='auth-refresh'),
    path('auth/me/', AuthMeView.as_view(), name='auth-me'),
    # Category manager
    path('categories/tree/', CategoryTreeView.as_view(), name='category-tree'),
    path('categories/bulk/', CategoryBulkReassignView.as_view(), name='category-bulk'),
    # Transaction rename + similar must be BEFORE router include
    # (router's transactions/<pk>/ would capture "rename" and "similar" as pk values)
    path('transactions/rename/', TransactionRenameView.as_view(), name='transaction-rename'),
    path('transactions/similar/', TransactionSimilarView.as_view(), name='transaction-similar'),
    path('transactions/categorize-installment/', CategorizeInstallmentView.as_view(), name='categorize-installment'),
    path('', include(router.urls)),
    path('analytics/metricas/order/', MetricasOrderView.as_view(), name='metricas-order'),
    path('analytics/metricas/make-default/', MetricasMakeDefaultView.as_view(), name='metricas-make-default'),
    path('analytics/metricas/lock/', MetricasLockView.as_view(), name='metricas-lock'),
    path('analytics/metricas/custom/', CustomMetricsView.as_view(), name='metricas-custom'),
    path('analytics/metricas/', AnalyticsMetricasView.as_view(), name='analytics-metricas'),
    path('analytics/recurring/', RecurringDataView.as_view(), name='analytics-recurring'),
    path('analytics/cards/', CardTransactionsView.as_view(), name='analytics-cards'),
    path('analytics/variable/', VariableTransactionsView.as_view(), name='analytics-variable'),
    path('analytics/recurring/candidates/', MappingCandidatesView.as_view(), name='mapping-candidates'),
    path('analytics/recurring/map/', MapTransactionView.as_view(), name='map-transaction'),
    path('analytics/recurring/match-mode/', ToggleMatchModeView.as_view(), name='toggle-match-mode'),
    # Phase A: new recurring management endpoints
    path('analytics/recurring/initialize/', RecurringInitializeView.as_view(), name='recurring-initialize'),
    path('analytics/recurring/expected/', RecurringExpectedView.as_view(), name='recurring-expected'),
    path('analytics/recurring/update/', RecurringUpdateView.as_view(), name='recurring-update'),
    path('analytics/recurring/custom/', RecurringCustomView.as_view(), name='recurring-custom'),
    path('analytics/recurring/skip/', RecurringSkipView.as_view(), name='recurring-skip'),
    path('analytics/balance/', BalanceSaveView.as_view(), name='balance-save'),
    # Phase 7: analytics trends
    path('analytics/trends/', AnalyticsTrendsView.as_view(), name='analytics-trends'),
    # Spending insights (BUDG-03)
    path('analytics/insights/', SpendingInsightsView.as_view(), name='spending-insights'),
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
    path('analytics/month-categories/', MonthCategoriesView.as_view(), name='analytics-month-categories'),
    path('analytics/recurring/auto-link/', AutoLinkRecurringView.as_view(), name='auto-link-recurring'),
    path('analytics/recurring/reorder/', RecurringReorderView.as_view(), name='recurring-reorder'),
    # Salary projection
    path('salary/projection/', SalaryProjectionView.as_view(), name='salary-projection'),
    path('salary/sync/', SalarySyncView.as_view(), name='salary-sync'),
    path('salary/config/', SalaryConfigView.as_view(), name='salary-config'),
    path('sync/pluggy/', PluggySyncView.as_view(), name='sync-pluggy'),
    path('import/', ImportStatementsView.as_view(), name='import-statements'),
    # Setup wizard
    path('profiles/<uuid:pk>/setup/', ProfileSetupView.as_view(), name='profile-setup'),
    path('profiles/<uuid:pk>/export-setup/', ExportSetupView.as_view(), name='export-setup'),
    path('profiles/<uuid:pk>/setup-state/', ProfileSetupStateView.as_view(), name='profile-setup-state'),
    path('analytics/analyze-setup/', AnalyzeSetupView.as_view(), name='analyze-setup'),
    # Home / Family Hub
    path('home/reminders/', RemindersView.as_view(), name='home-reminders'),
    path('home/reminders/lists/', RemindersListsView.as_view(), name='home-reminders-lists'),
    path('home/reminders/add/', RemindersAddView.as_view(), name='home-reminders-add'),
    path('home/reminders/complete/', RemindersCompleteView.as_view(), name='home-reminders-complete'),
    # Calendar (per-profile, multi-account)
    path('calendar/accounts/', CalendarAccountsView.as_view(), name='calendar-accounts'),
    path('calendar/connect/', CalendarConnectView.as_view(), name='calendar-connect'),
    path('calendar/oauth-callback/', CalendarOAuthCallbackView.as_view(), name='calendar-oauth-callback'),
    # Google Cloud Console has this as the authorized redirect URI
    path('home/calendar/oauth-callback/', CalendarOAuthCallbackView.as_view(), name='calendar-oauth-callback-legacy'),
    path('calendar/accounts/<uuid:account_id>/', CalendarDisconnectView.as_view(), name='calendar-disconnect'),
    path('calendar/available/<uuid:account_id>/', CalendarAvailableView.as_view(), name='calendar-available'),
    path('calendar/selections/', CalendarSelectionsView.as_view(), name='calendar-selections'),
    path('calendar/events/', CalendarEventsView.as_view(), name='calendar-events'),
    path('calendar/add-event/', CalendarAddEventView.as_view(), name='calendar-add-event'),
    # Google Suite (OAuth + Gmail + Drive)
    path('google/connect/', GoogleConnectView.as_view(), name='google-connect'),
    path('google/oauth-callback/', GoogleOAuthCallbackView.as_view(), name='google-oauth-callback'),
    path('google/accounts/', GoogleAccountsView.as_view(), name='google-accounts'),
    # Gmail
    path('google/gmail/messages/', GmailMessagesView.as_view(), name='gmail-messages'),
    path('google/gmail/messages/<str:message_id>/', GmailMessageDetailView.as_view(), name='gmail-message-detail'),
    path('google/gmail/send/', GmailSendView.as_view(), name='gmail-send'),
    path('google/gmail/trash/<str:message_id>/', GmailTrashView.as_view(), name='gmail-trash'),
    path('google/gmail/labels/', GmailLabelsView.as_view(), name='gmail-labels'),
    # Drive
    path('google/drive/files/', DriveFilesView.as_view(), name='drive-files'),
    path('google/drive/files/<str:file_id>/content/', DriveFileContentView.as_view(), name='drive-file-content'),
    path('google/drive/sheets/<str:spreadsheet_id>/', SpreadsheetView.as_view(), name='drive-spreadsheet'),
    path('google/drive/docs/<str:document_id>/', DocumentView.as_view(), name='drive-document'),
]
