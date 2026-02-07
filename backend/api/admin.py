from django.contrib import admin
from .models import (
    Account, Category, Subcategory, CategorizationRule,
    RenameRule, Transaction, RecurringMapping, BudgetConfig,
    BalanceOverride,
)


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'account_type', 'is_active')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category_type', 'default_limit', 'due_day', 'display_order')
    list_filter = ('category_type', 'is_active')
    search_fields = ('name',)


@admin.register(Subcategory)
class SubcategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    list_filter = ('category',)


@admin.register(CategorizationRule)
class CategorizationRuleAdmin(admin.ModelAdmin):
    list_display = ('keyword', 'category', 'priority', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('keyword',)


@admin.register(RenameRule)
class RenameRuleAdmin(admin.ModelAdmin):
    list_display = ('keyword', 'display_name', 'is_active')
    search_fields = ('keyword', 'display_name')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('date', 'description', 'amount', 'account', 'category', 'month_str')
    list_filter = ('account', 'category', 'is_internal_transfer', 'is_installment')
    search_fields = ('description', 'description_original')
    date_hierarchy = 'date'


@admin.register(RecurringMapping)
class RecurringMappingAdmin(admin.ModelAdmin):
    list_display = ('month_str', 'category', 'status', 'expected_amount', 'actual_amount')
    list_filter = ('status', 'month_str')


@admin.register(BudgetConfig)
class BudgetConfigAdmin(admin.ModelAdmin):
    list_display = ('month_str', 'category', 'limit_override')
    list_filter = ('month_str',)


@admin.register(BalanceOverride)
class BalanceOverrideAdmin(admin.ModelAdmin):
    list_display = ('month_str', 'balance')
