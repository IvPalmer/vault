from rest_framework import serializers
from .models import (
    Profile, Account, Category, Subcategory, CategorizationRule,
    PluggyCategoryMapping, RenameRule, RecurringTemplate, Transaction,
    RecurringMapping, BudgetConfig, BalanceOverride, BankTemplate,
    SetupTemplate, FamilyNote, GoogleAccount, CalendarSelection,
    Project, PersonalTask, PersonalNote,
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


class PluggyCategoryMappingSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    subcategory_name = serializers.CharField(source='subcategory.name', read_only=True, default=None)

    class Meta:
        model = PluggyCategoryMapping
        fields = '__all__'


class CategorizationRuleSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    subcategory_name = serializers.CharField(source='subcategory.name', read_only=True, default=None)

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


class SetupTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SetupTemplate
        fields = '__all__'


class FamilyNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = FamilyNote
        fields = '__all__'


class GoogleAccountSerializer(serializers.ModelSerializer):
    connected = serializers.SerializerMethodField()

    class Meta:
        model = GoogleAccount
        fields = ['id', 'email', 'connected', 'authorized_scopes', 'created_at']

    def get_connected(self, obj):
        """Cheap heuristic: connected if refresh_token exists in token_data."""
        return bool(obj.token_data and obj.token_data.get('refresh_token'))


class CalendarSelectionSerializer(serializers.ModelSerializer):
    account_email = serializers.CharField(source='account.email', read_only=True)

    class Meta:
        model = CalendarSelection
        fields = [
            'id', 'account', 'account_email', 'calendar_id',
            'calendar_name', 'color', 'show_in_home', 'show_in_personal',
        ]


class ProjectSerializer(serializers.ModelSerializer):
    task_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'status', 'color', 'position', 'task_count', 'created_at', 'updated_at']

    def get_task_count(self, obj):
        return obj.tasks.exclude(status='done').count()


class PersonalTaskSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True, default=None)

    class Meta:
        model = PersonalTask
        fields = ['id', 'project', 'project_name', 'title', 'notes', 'due_date', 'priority', 'status', 'position', 'created_at', 'updated_at']


class PersonalNoteSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True, default=None)

    class Meta:
        model = PersonalNote
        fields = ['id', 'project', 'project_name', 'title', 'content', 'pinned', 'created_at', 'updated_at']
