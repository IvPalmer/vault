from django.contrib import admin
from .models import (
    Profile,
    Account, Category, Subcategory, CategorizationRule,
    RenameRule, Transaction, RecurringMapping, BudgetConfig,
    BalanceOverride, RecurringTemplate, MetricasOrderConfig,
    CustomMetric,
)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active',)


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'account_type', 'is_active', 'profile')
    list_filter = ('profile', 'account_type', 'is_active')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category_type', 'default_limit', 'due_day', 'display_order', 'profile')
    list_filter = ('profile', 'category_type', 'is_active')
    search_fields = ('name',)


@admin.register(Subcategory)
class SubcategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'profile')
    list_filter = ('profile', 'category')


@admin.register(CategorizationRule)
class CategorizationRuleAdmin(admin.ModelAdmin):
    list_display = ('keyword', 'category', 'priority', 'is_active', 'profile')
    list_filter = ('profile', 'category', 'is_active')
    search_fields = ('keyword',)


@admin.register(RenameRule)
class RenameRuleAdmin(admin.ModelAdmin):
    list_display = ('keyword', 'display_name', 'is_active', 'profile')
    list_filter = ('profile',)
    search_fields = ('keyword', 'display_name')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('date', 'description', 'amount', 'account', 'category', 'month_str', 'profile')
    list_filter = ('profile', 'account', 'category', 'is_internal_transfer', 'is_installment')
    search_fields = ('description', 'description_original')
    date_hierarchy = 'date'


@admin.register(RecurringTemplate)
class RecurringTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'template_type', 'default_limit', 'is_active', 'profile')
    list_filter = ('profile', 'template_type', 'is_active')


@admin.register(RecurringMapping)
class RecurringMappingAdmin(admin.ModelAdmin):
    list_display = ('month_str', 'category', 'status', 'expected_amount', 'actual_amount', 'profile')
    list_filter = ('profile', 'status', 'month_str')


@admin.register(BudgetConfig)
class BudgetConfigAdmin(admin.ModelAdmin):
    list_display = ('month_str', 'category', 'limit_override', 'profile')
    list_filter = ('profile', 'month_str')


@admin.register(BalanceOverride)
class BalanceOverrideAdmin(admin.ModelAdmin):
    list_display = ('month_str', 'balance', 'profile')
    list_filter = ('profile',)


@admin.register(MetricasOrderConfig)
class MetricasOrderConfigAdmin(admin.ModelAdmin):
    list_display = ('month_str', 'is_locked', 'profile')
    list_filter = ('profile',)


@admin.register(CustomMetric)
class CustomMetricAdmin(admin.ModelAdmin):
    list_display = ('label', 'metric_type', 'is_active', 'profile')
    list_filter = ('profile', 'metric_type', 'is_active')
