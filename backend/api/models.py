import uuid
from django.db import models


CATEGORY_TYPE_CHOICES = (
    ('Fixo', 'Fixo'),
    ('Variavel', 'Variável'),
    ('Income', 'Income'),
    ('Investimento', 'Investimento'),
)


class Account(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    account_type = models.CharField(max_length=20, choices=[
        ('checking', 'Checking'),
        ('credit_card', 'Credit Card'),
        ('manual', 'Manual'),
    ])
    closing_day = models.IntegerField(null=True, blank=True)
    due_day = models.IntegerField(null=True, blank=True)
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
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

    def __str__(self):
        return f"{self.name} ({self.category_type})"


class Subcategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('name', 'category')
        ordering = ['name']
        verbose_name_plural = 'Subcategories'

    def __str__(self):
        return f"{self.category.name} > {self.name}"


class CategorizationRule(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    keyword = models.CharField(max_length=200, unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='rules')
    subcategory = models.ForeignKey(
        Subcategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='rules'
    )
    priority = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-priority', 'keyword']

    def __str__(self):
        return f"{self.keyword} -> {self.category.name}"


class RenameRule(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    keyword = models.CharField(max_length=200, unique=True)
    display_name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['keyword']

    def __str__(self):
        return f"{self.keyword} -> {self.display_name}"


class Transaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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
    is_manually_categorized = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['month_str', 'account']),
            models.Index(fields=['category', 'month_str']),
            models.Index(fields=['date', 'amount', 'account']),
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
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, null=True, blank=True, related_name='recurring_mappings'
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
                fields=['category', 'month_str'],
                condition=models.Q(category__isnull=False),
                name='unique_category_month_non_null',
            ),
        ]
        ordering = ['month_str', 'display_order', 'category__display_order']

    def __str__(self):
        name = self.custom_name if self.is_custom else (self.category.name if self.category else '?')
        return f"{self.month_str} | {name} -> {self.status}"


class BudgetConfig(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='budget_configs')
    month_str = models.CharField(max_length=7)
    limit_override = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('category', 'month_str')
        ordering = ['month_str']

    def __str__(self):
        return f"{self.month_str} | {self.category.name} = R$ {self.limit_override}"


class BalanceOverride(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    month_str = models.CharField(max_length=7, unique=True)
    balance = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-month_str']

    def __str__(self):
        return f"{self.month_str}: R$ {self.balance}"


class MetricasOrderConfig(models.Model):
    """
    Stores metric card order per month.
    A row with month_str='__default__' is the global default order.
    All other rows are per-month overrides.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    month_str = models.CharField(max_length=20, unique=True)
    card_order = models.JSONField(default=list)
    hidden_cards = models.JSONField(default=list)
    is_locked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-month_str']

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
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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
