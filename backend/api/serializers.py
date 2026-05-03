from rest_framework import serializers
from .models import (
    Profile, Account, Category, Subcategory, CategorizationRule,
    PluggyCategoryMapping, RenameRule, RecurringTemplate, Transaction,
    RecurringMapping, BudgetConfig, BalanceOverride, BankTemplate,
    SetupTemplate, FamilyNote, GoogleAccount, CalendarSelection,
    Project, PersonalTask, PersonalNote, DashboardState,
    HealthExam, VitalReading, Pregnancy, PrenatalConsultation,
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


class DashboardStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DashboardState
        fields = ['state', 'updated_at']
        read_only_fields = ['updated_at']


# ── Saúde ─────────────────────────────────────────────────────

class HealthExamSerializer(serializers.ModelSerializer):
    profile_name = serializers.CharField(source='profile.name', read_only=True)
    tipo_label = serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta:
        model = HealthExam
        fields = [
            'id', 'profile', 'profile_name', 'tipo', 'tipo_label', 'nome', 'data',
            'valores', 'arquivo_path', 'laboratorio', 'medico', 'notes',
            'pregnancy', 'checkpoint_id', 'created_at', 'updated_at',
        ]
        read_only_fields = ['profile', 'created_at', 'updated_at']


class VitalReadingSerializer(serializers.ModelSerializer):
    tipo_label = serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta:
        model = VitalReading
        fields = ['id', 'profile', 'tipo', 'tipo_label', 'data', 'valor', 'notes', 'pregnancy', 'created_at']
        read_only_fields = ['profile', 'created_at']


class PrenatalConsultationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrenatalConsultation
        fields = [
            'id', 'pregnancy', 'data', 'ig_semanas', 'obstetra',
            'pa_sis', 'pa_dia', 'peso_kg', 'fcf_bpm', 'altura_uterina_cm',
            'queixas', 'conduta', 'proxima_consulta', 'created_at',
        ]
        read_only_fields = ['created_at']


class PregnancySerializer(serializers.ModelSerializer):
    titular_name = serializers.CharField(source='titular.name', read_only=True)
    gestante_name = serializers.CharField(source='gestante.name', read_only=True)
    consultations = PrenatalConsultationSerializer(many=True, read_only=True)
    ig_atual_semanas = serializers.SerializerMethodField()
    dias_ate_dpp = serializers.SerializerMethodField()
    cobertura_parto = serializers.SerializerMethodField()
    completed_checkpoint_ids = serializers.SerializerMethodField()

    class Meta:
        model = Pregnancy
        fields = [
            'id', 'titular', 'titular_name', 'gestante', 'gestante_name',
            'confirmada_em', 'dum', 'dpp', 'status', 'notes',
            'plano_nome', 'plano_vigencia_inicio', 'carencia_obstetrica_dias',
            'consultations', 'ig_atual_semanas', 'dias_ate_dpp', 'cobertura_parto',
            'completed_checkpoint_ids',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_ig_atual_semanas(self, obj):
        if not obj.dum:
            return None
        from datetime import date
        delta = date.today() - obj.dum
        weeks, days = divmod(delta.days, 7)
        return f'{weeks}+{days}'

    def get_dias_ate_dpp(self, obj):
        if not obj.dpp:
            return None
        from datetime import date
        return (obj.dpp - date.today()).days

    def get_completed_checkpoint_ids(self, obj):
        """Distinct checkpoint_ids of HealthExam records linked to this
        pregnancy OR belonging to the gestante. Returns list of strings."""
        from django.db.models import Q
        qs = obj.gestante.health_exams.filter(
            Q(pregnancy=obj) | Q(pregnancy__isnull=True)
        ).exclude(checkpoint_id='').values_list('checkpoint_id', flat=True).distinct()
        return list(qs)

    def get_cobertura_parto(self, obj):
        """Returns dict with status of obstetric coverage vs DPP.

        status:
          - 'ok' — DPP after end of carência → covered
          - 'risco' — DPP before end of carência → uncovered (returns dias_descoberto)
          - 'pending' — missing DPP or vigencia data
        """
        if not obj.dpp or not obj.plano_vigencia_inicio:
            return {'status': 'pending', 'plano': obj.plano_nome or None}
        from datetime import timedelta
        fim_carencia = obj.plano_vigencia_inicio + timedelta(days=obj.carencia_obstetrica_dias)
        if obj.dpp >= fim_carencia:
            return {
                'status': 'ok',
                'plano': obj.plano_nome,
                'fim_carencia': fim_carencia.isoformat(),
            }
        return {
            'status': 'risco',
            'plano': obj.plano_nome,
            'fim_carencia': fim_carencia.isoformat(),
            'dias_descoberto': (fim_carencia - obj.dpp).days,
        }
