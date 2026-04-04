import uuid
from django.db import models


CATEGORY_TYPE_CHOICES = (
    ('Fixo', 'Fixo'),
    ('Variavel', 'Variável'),
    ('Income', 'Income'),
    ('Investimento', 'Investimento'),
)

TEMPLATE_TYPE_CHOICES = (
    ('Fixo', 'Fixo'),
    ('Income', 'Income'),
    ('Investimento', 'Investimento'),
    ('Cartao', 'Cartao'),
)


class Profile(models.Model):
    """
    User profile for multi-person household support.
    Each person (Palmer, Rafa, etc.) gets isolated data.
    No authentication — just a profile selector in the header.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    savings_target_pct = models.DecimalField(
        max_digits=5, decimal_places=2, default=20.00,
        help_text='Target savings percentage of income (e.g. 20 means 20%)',
    )
    cc_display_mode = models.CharField(
        max_length=20,
        choices=[('invoice', 'Invoice Month'), ('transaction', 'Transaction Month')],
        default='invoice',
        help_text='How CC transactions are grouped in monthly view',
    )
    investment_target_pct = models.DecimalField(
        max_digits=5, decimal_places=2, default=10.00,
        help_text='Target investment percentage of income',
    )
    investment_allocation = models.JSONField(
        default=dict, blank=True,
        help_text='Investment allocation breakdown, e.g. {"Renda Fixa": 40, "Renda Variavel": 40, "Crypto": 20}',
    )
    budget_strategy = models.CharField(
        max_length=30,
        choices=[
            ('percentage', 'Percentage of Income'),
            ('fixed', 'Fixed Amounts'),
            ('smart', 'Smart (Statement-based)'),
        ],
        default='percentage',
        help_text='How budget limits are calculated',
    )
    setup_completed = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class BankTemplate(models.Model):
    """
    Reusable bank configuration template. System-wide, not per-profile.
    Stores parsing config, file patterns, and display defaults.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bank_name = models.CharField(max_length=100)
    account_type = models.CharField(max_length=20, choices=[
        ('checking', 'Checking'),
        ('credit_card', 'Credit Card'),
        ('manual', 'Manual'),
    ])
    display_name = models.CharField(max_length=100)
    file_patterns = models.JSONField(default=list, help_text='Glob patterns for file detection, e.g. ["master-*.csv"]')
    file_format = models.CharField(max_length=20, choices=[
        ('csv', 'CSV'),
        ('ofx', 'OFX'),
        ('txt', 'TXT'),
    ], default='csv')
    sign_inversion = models.BooleanField(default=False, help_text='Negate amounts on import (for CC CSVs)')
    encoding = models.CharField(max_length=20, default='utf-8')
    payment_filter_patterns = models.JSONField(default=list, help_text='Regex patterns to filter payment entries')
    description_cleaner = models.CharField(max_length=100, blank=True, help_text='Cleaner function: "nubank", "itau", ""')
    default_closing_day = models.IntegerField(null=True, blank=True)
    default_due_day = models.IntegerField(null=True, blank=True)
    import_instructions = models.TextField(blank=True, help_text='User-facing import instructions (markdown)')
    is_builtin = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['bank_name', 'account_type', 'display_name']

    def __str__(self):
        return f"{self.bank_name} - {self.display_name}"


class Account(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='accounts', null=True, blank=True)
    bank_template = models.ForeignKey(
        'BankTemplate', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='accounts', help_text='Bank template this account was created from',
    )
    name = models.CharField(max_length=100)
    account_type = models.CharField(max_length=20, choices=[
        ('checking', 'Checking'),
        ('credit_card', 'Credit Card'),
        ('manual', 'Manual'),
    ])
    closing_day = models.IntegerField(null=True, blank=True)
    due_day = models.IntegerField(null=True, blank=True)
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    external_id = models.CharField(max_length=200, blank=True, default='',
                                    help_text='External account ID (e.g. Pluggy account UUID)')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        unique_together = ('profile', 'name')

    def __str__(self):
        return self.name


class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='categories', null=True, blank=True)
    name = models.CharField(max_length=100)
    category_type = models.CharField(max_length=20, choices=CATEGORY_TYPE_CHOICES, default='Variavel')
    default_limit = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    due_day = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'name']
        verbose_name_plural = 'Categories'
        unique_together = ('profile', 'name')

    def __str__(self):
        return f"{self.name} ({self.category_type})"


class Subcategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='subcategories', null=True, blank=True)
    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    default_limit = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('name', 'category')
        ordering = ['name']
        verbose_name_plural = 'Subcategories'

    def __str__(self):
        return f"{self.category.name} > {self.name}"


class CategorizationRule(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='categorization_rules', null=True, blank=True)
    keyword = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='rules')
    subcategory = models.ForeignKey(
        Subcategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='rules'
    )
    priority = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-priority', 'keyword']
        unique_together = ('profile', 'keyword')

    def __str__(self):
        return f"{self.keyword} -> {self.category.name}"


class PluggyCategoryMapping(models.Model):
    """Maps a Pluggy category ID to a Vault Category/Subcategory.
    Users can customize these mappings to override Pluggy's default classification."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='pluggy_category_mappings', null=True, blank=True)
    pluggy_category_id = models.CharField(max_length=20, help_text='Pluggy category ID (e.g. 10000000)')
    pluggy_category_name = models.CharField(max_length=100, help_text='Pluggy category display name')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='pluggy_mappings')
    subcategory = models.ForeignKey(
        Subcategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='pluggy_mappings'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('profile', 'pluggy_category_id')
        ordering = ['pluggy_category_id']

    def __str__(self):
        return f"{self.pluggy_category_name} -> {self.category.name}"


class RenameRule(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='rename_rules', null=True, blank=True)
    keyword = models.CharField(max_length=200)
    display_name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['keyword']
        unique_together = ('profile', 'keyword')

    def __str__(self):
        return f"{self.keyword} -> {self.display_name}"


class RecurringTemplate(models.Model):
    """
    Master template for recurring budget items (Aluguel, Salario, etc.).
    Separate from Category which is purely for transaction taxonomy.
    Each month, initialize_month() creates RecurringMapping rows from active templates.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='recurring_templates', null=True, blank=True)
    name = models.CharField(max_length=100)
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPE_CHOICES)
    default_limit = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    due_day = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'name']
        unique_together = ('profile', 'name')

    def __str__(self):
        return f"{self.name} ({self.template_type})"


class Transaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='transactions', null=True, blank=True)
    date = models.DateField(db_index=True)
    description = models.CharField(max_length=500)
    description_original = models.CharField(max_length=500, blank=True)
    raw_description = models.CharField(max_length=500, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='transactions')
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions'
    )
    subcategory = models.ForeignKey(
        Subcategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions'
    )
    source_file = models.CharField(max_length=200, blank=True)
    is_installment = models.BooleanField(default=False)
    installment_info = models.CharField(max_length=20, blank=True)
    is_recurring = models.BooleanField(default=False)
    is_internal_transfer = models.BooleanField(default=False)
    invoice_month = models.CharField(max_length=7, blank=True, db_index=True)
    invoice_close_date = models.DateField(null=True, blank=True)
    invoice_payment_date = models.DateField(null=True, blank=True)
    month_str = models.CharField(max_length=7, db_index=True)
    external_id = models.CharField(max_length=200, blank=True, default='', db_index=True)
    pluggy_category = models.CharField(max_length=100, blank=True, default='',
                                        help_text='Original category from Pluggy Open Finance')
    pluggy_category_id = models.CharField(max_length=20, blank=True, default='',
                                           help_text='Pluggy category ID (e.g. 10000000)')
    is_manually_categorized = models.BooleanField(default=False)
    card_last4 = models.CharField(max_length=4, blank=True, default='',
                                   help_text='Last 4 digits of credit card (from Pluggy creditCardMetadata)')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['month_str', 'account']),
            models.Index(fields=['category', 'month_str']),
            models.Index(fields=['date', 'amount', 'account']),
            models.Index(fields=['profile', 'month_str']),
        ]

    def save(self, *args, **kwargs):
        if self.date:
            self.month_str = self.date.strftime('%Y-%m')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.date} | {self.description} | R$ {self.amount}"


class RecurringMapping(models.Model):
    MATCH_MODE_CHOICES = (
        ('manual', 'Manual'),       # Explicitly linked transaction(s)
        ('category', 'Category'),   # Auto-match all txns in category
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='recurring_mappings', null=True, blank=True)
    template = models.ForeignKey(
        RecurringTemplate, on_delete=models.CASCADE, null=True, blank=True,
        related_name='recurring_mappings',
    )
    # Taxonomy category for match_mode='category' auto-matching only
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='category_matched_mappings',
    )
    # Legacy single-transaction FK (kept for backward compat during migration)
    transaction = models.ForeignKey(
        Transaction, on_delete=models.SET_NULL, null=True, blank=True, related_name='recurring_mappings'
    )
    # New: multiple transaction links
    transactions = models.ManyToManyField(
        Transaction, blank=True, related_name='recurring_mapping_links'
    )
    # Cross-month links: transactions from a DIFFERENT month linked here.
    # These get excluded from their original month's metrics and shown as
    # "Movido para {month_str}" in the source month's view.
    cross_month_transactions = models.ManyToManyField(
        Transaction, blank=True, related_name='cross_month_links'
    )
    match_mode = models.CharField(max_length=20, choices=MATCH_MODE_CHOICES, default='manual')
    month_str = models.CharField(max_length=7, db_index=True)
    status = models.CharField(max_length=20, choices=[
        ('mapped', 'Mapped'),
        ('missing', 'Missing'),
        ('suggested', 'Suggested'),
        ('skipped', 'Skipped'),
    ], default='missing')
    expected_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    actual_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)
    is_custom = models.BooleanField(default=False)
    custom_name = models.CharField(max_length=200, blank=True)
    custom_type = models.CharField(max_length=20, choices=CATEGORY_TYPE_CHOICES, blank=True)
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['profile', 'template', 'month_str'],
                condition=models.Q(template__isnull=False),
                name='unique_profile_template_month',
            ),
        ]
        ordering = ['month_str', 'display_order', 'template__display_order']

    def __str__(self):
        name = self.custom_name if self.is_custom else (self.template.name if self.template else '?')
        return f"{self.month_str} | {name} -> {self.status}"


class BudgetConfig(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='budget_configs', null=True, blank=True)
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, null=True, blank=True, related_name='budget_configs'
    )
    template = models.ForeignKey(
        RecurringTemplate, on_delete=models.CASCADE, null=True, blank=True, related_name='budget_configs'
    )
    month_str = models.CharField(max_length=7)
    limit_override = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['month_str']

    def __str__(self):
        name = self.category.name if self.category else (self.template.name if self.template else '?')
        return f"{self.month_str} | {name} = R$ {self.limit_override}"


class BalanceOverride(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='balance_overrides', null=True, blank=True)
    month_str = models.CharField(max_length=7)
    balance = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-month_str']
        unique_together = ('profile', 'month_str')

    def __str__(self):
        return f"{self.month_str}: R$ {self.balance}"


class BalanceAnchor(models.Model):
    """
    Stores a known checking account balance at a specific date,
    captured from OFX LEDGERBAL during import. Used to compute
    end-of-month balances for closed months.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='balance_anchors', null=True, blank=True)
    date = models.DateField()
    balance = models.DecimalField(max_digits=12, decimal_places=2)
    source_file = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
        unique_together = ('profile', 'date')

    def __str__(self):
        return f"{self.date}: R$ {self.balance}"


class MetricasOrderConfig(models.Model):
    """
    Stores metric card order per month.
    A row with month_str='__default__' is the global default order.
    All other rows are per-month overrides.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='metricas_order_configs', null=True, blank=True)
    month_str = models.CharField(max_length=20)
    card_order = models.JSONField(default=list)
    hidden_cards = models.JSONField(default=list)
    is_locked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-month_str']
        unique_together = ('profile', 'month_str')

    def __str__(self):
        locked = ' [LOCKED]' if self.is_locked else ''
        return f"MetricasOrder {self.month_str}{locked}"


class CustomMetric(models.Model):
    """
    User-defined metric card definitions.
    Global (not per-month); computed values vary by month.
    """
    METRIC_TYPE_CHOICES = (
        ('category_total', 'Category Total Spending'),
        ('category_remaining', 'Category Budget Remaining'),
        ('fixo_total', 'Fixed Expenses Total'),
        ('investimento_total', 'Investment Total'),
        ('income_total', 'Income Total'),
        ('recurring_item', 'Specific Recurring Item'),
        ('builtin_clone', 'Clone of Built-in Card'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='custom_metrics', null=True, blank=True)
    metric_type = models.CharField(max_length=30, choices=METRIC_TYPE_CHOICES)
    label = models.CharField(max_length=100)
    config = models.JSONField(default=dict)
    color = models.CharField(max_length=50, default='var(--color-accent)')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['label']

    def __str__(self):
        return f"CustomMetric: {self.label} ({self.metric_type})"


class SetupTemplate(models.Model):
    """
    Reusable setup configuration template. Can be saved from a wizard run
    and restored later to quickly reconfigure a profile.
    profile=null means it's a global/shared template.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, null=True, blank=True,
        related_name='setup_templates',
        help_text='Owner profile. Null for global templates.',
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    template_data = models.JSONField(
        default=dict,
        help_text='Full wizard state snapshot (bank_accounts, categories, recurring, rules, metricas, targets, etc.)',
    )
    is_builtin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f'{self.name} ({self.profile.name if self.profile else "Global"})'


class FamilyNote(models.Model):
    """
    Shared family bulletin board note. Not profile-scoped —
    visible to all household members.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200, blank=True)
    content = models.TextField()
    author_name = models.CharField(
        max_length=100,
        help_text='Free-text author name, e.g. "Palmer" or "Rafa"',
    )
    pinned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-pinned', '-updated_at']

    def __str__(self):
        return f"{self.author_name}: {self.title or self.content[:40]}"


class SalaryConfig(models.Model):
    """
    Salary calculation parameters for automated income projection.
    Computes: gross USD → advance deduction → Wise fee → BRL conversion → tax hold → net BRL.
    Payments arrive split into 2 per month for previous month's work.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='salary_config')
    hourly_rate_usd = models.DecimalField(max_digits=8, decimal_places=2, help_text='USD per hour')
    hours_per_day = models.DecimalField(max_digits=4, decimal_places=1, default=8.0)
    wise_fee_pct = models.DecimalField(max_digits=5, decimal_places=4, default=0.0091, help_text='Wise variable fee as decimal (0.0091 = 0.91%)')
    wise_fee_flat = models.DecimalField(max_digits=6, decimal_places=2, default=0.46, help_text='Wise flat fee in USD per transfer')
    tax_hold_pct = models.DecimalField(max_digits=5, decimal_places=4, default=0.08, help_text='% of BRL kept in enterprise for taxes')
    income_template = models.ForeignKey(
        RecurringTemplate, on_delete=models.SET_NULL, null=True, blank=True,
        help_text='Income template to update with projected salary',
    )
    advance_total_usd = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text='Total advance to be recouped')
    advance_recoup_pct = models.DecimalField(max_digits=5, decimal_places=4, default=0, help_text='% deducted per payment (e.g. 0.125 = 12.5%)')
    advance_start_date = models.CharField(max_length=7, blank=True, help_text='First deduction month (YYYY-MM)')
    advance_num_cycles = models.IntegerField(default=0, help_text='Number of pay cycles to deduct')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Salary {self.profile.name}: ${self.hourly_rate_usd}/h"


class GoogleAccount(models.Model):
    """
    OAuth credentials for a connected Google account.
    One profile can have multiple Google accounts.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name='google_accounts',
    )
    email = models.CharField(max_length=200, help_text='Google account email')
    token_data = models.JSONField(
        help_text='OAuth token JSON: access_token, refresh_token, token_uri, client_id, client_secret, scopes',
    )
    authorized_scopes = models.JSONField(
        default=list, blank=True,
        help_text='List of OAuth scopes this account has authorized',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.profile.name} — {self.email}"


class CalendarSelection(models.Model):
    """
    Which calendars from each Google account are enabled for display.
    Controls visibility in Home (shared) vs Pessoal (personal) views.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name='calendar_selections',
    )
    account = models.ForeignKey(
        GoogleAccount, on_delete=models.CASCADE, related_name='selections',
    )
    calendar_id = models.CharField(
        max_length=300, help_text='Google Calendar ID (email-like string)',
    )
    calendar_name = models.CharField(max_length=200, help_text='Display name')
    color = models.CharField(max_length=7, blank=True, help_text='Hex color override')
    show_in_home = models.BooleanField(default=False)
    show_in_personal = models.BooleanField(default=True)

    class Meta:
        ordering = ['calendar_name']
        unique_together = [('profile', 'account', 'calendar_id')]

    def __str__(self):
        return f"{self.calendar_name} ({self.account.email})"


class Project(models.Model):
    """Personal project for grouping tasks and notes."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='projects')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=[('active', 'Ativo'), ('paused', 'Pausado'), ('done', 'Concluido')],
        default='active',
    )
    color = models.CharField(max_length=7, blank=True)
    position = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['position', 'name']

    def __str__(self):
        return f"{self.profile.name}: {self.name}"


class PersonalTask(models.Model):
    """Individual task, optionally linked to a project."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='personal_tasks')
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    title = models.CharField(max_length=300)
    notes = models.TextField(blank=True)
    due_date = models.DateField(null=True, blank=True)
    priority = models.IntegerField(
        default=0,
        choices=[(0, 'Nenhuma'), (1, 'Baixa'), (2, 'Media'), (3, 'Alta')],
    )
    status = models.CharField(
        max_length=20,
        choices=[('todo', 'A fazer'), ('doing', 'Fazendo'), ('done', 'Feito')],
        default='todo',
    )
    position = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['position', '-priority', 'due_date']

    def __str__(self):
        return self.title


class PersonalNote(models.Model):
    """Profile-scoped personal note, optionally linked to a project."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='personal_notes')
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name='notes')
    title = models.CharField(max_length=200, blank=True)
    content = models.TextField()
    pinned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-pinned', '-updated_at']

    def __str__(self):
        return f"{self.title or self.content[:40]}"
