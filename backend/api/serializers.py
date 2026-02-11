from rest_framework import serializers
from .models import (
    Profile, Account, Category, Subcategory, CategorizationRule,
    RenameRule, RecurringTemplate, Transaction, RecurringMapping,
    BudgetConfig, BalanceOverride, BankTemplate,
)


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = '__all__'


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = '__all__'


class SubcategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Subcategory
        fields = '__all__'


class CategorySerializer(serializers.ModelSerializer):
    subcategories = SubcategorySerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = '__all__'


class CategorizationRuleSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = CategorizationRule
        fields = '__all__'


class RenameRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = RenameRule
        fields = '__all__'


class TransactionSerializer(serializers.ModelSerializer):
    account_name = serializers.CharField(source='account.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True, default=None)

    class Meta:
        model = Transaction
        fields = '__all__'


class TransactionListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""
    account_name = serializers.CharField(source='account.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True, default=None)

    class Meta:
        model = Transaction
        fields = [
            'id', 'date', 'description', 'amount', 'account', 'account_name',
            'category', 'category_name', 'is_installment', 'installment_info',
            'is_internal_transfer', 'month_str',
        ]


class RecurringTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecurringTemplate
        fields = '__all__'


class RecurringMappingSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source='template.name', read_only=True, default=None)
    template_type = serializers.CharField(source='template.template_type', read_only=True, default=None)
    category_name = serializers.CharField(source='category.name', read_only=True, default=None)
    transaction_description = serializers.CharField(
        source='transaction.description', read_only=True, default=None
    )

    class Meta:
        model = RecurringMapping
        fields = '__all__'


class BudgetConfigSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = BudgetConfig
        fields = '__all__'


class BalanceOverrideSerializer(serializers.ModelSerializer):
    class Meta:
        model = BalanceOverride
        fields = '__all__'


class BankTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankTemplate
        fields = '__all__'
