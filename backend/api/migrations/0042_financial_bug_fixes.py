from django.db import migrations, models
from django.db.models import Count
from django.core.management import call_command


PALMER_PROFILE_ID = 'a29184ea-9d4d-4c65-8300-386ed5b07fca'


def set_car_financing_end(apps, schema_editor):
    RecurringTemplate = apps.get_model('api', 'RecurringTemplate')
    for template in RecurringTemplate.objects.filter(profile_id=PALMER_PROFILE_ID):
        name = (template.name or '').lower()
        if 'financiamento' in name and 'carro' in name:
            template.contract_start = template.contract_start or '2024-09'
            template.end_month = '2026-08'
            template.save(update_fields=['contract_start', 'end_month'])


def unset_car_financing_end(apps, schema_editor):
    RecurringTemplate = apps.get_model('api', 'RecurringTemplate')
    for template in RecurringTemplate.objects.filter(profile_id=PALMER_PROFILE_ID):
        name = (template.name or '').lower()
        if 'financiamento' in name and 'carro' in name:
            template.contract_start = ''
            template.contract_term_months = None
            template.end_month = ''
            template.save(update_fields=['contract_start', 'contract_term_months', 'end_month'])


def coalesce_budget_config_duplicates(apps, schema_editor):
    BudgetConfig = apps.get_model('api', 'BudgetConfig')
    duplicate_keys = (
        BudgetConfig.objects
        .values('profile_id', 'template_id', 'category_id', 'month_str', 'pay_num')
        .annotate(row_count=Count('id'))
        .filter(row_count__gt=1)
    )
    for key in duplicate_keys:
        rows = list(BudgetConfig.objects.filter(
            profile_id=key['profile_id'],
            template_id=key['template_id'],
            category_id=key['category_id'],
            month_str=key['month_str'],
            pay_num=key['pay_num'],
        ).order_by('-updated_at', '-created_at'))
        keep = rows[0]
        BudgetConfig.objects.filter(id__in=[row.id for row in rows[1:]]).delete()
        keep.save(update_fields=['updated_at'])


def noop(apps, schema_editor):
    pass


def run_phantom_dedup(apps, schema_editor):
    call_command(
        'dedup_phantom_transactions',
        apply=True,
        database=schema_editor.connection.alias,
        verbosity=1,
    )


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0041_labmarker'),
    ]

    operations = [
        migrations.AddField(
            model_name='recurringtemplate',
            name='contract_start',
            field=models.CharField(blank=True, default='', max_length=7),
        ),
        migrations.AddField(
            model_name='recurringtemplate',
            name='contract_term_months',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='recurringtemplate',
            name='end_month',
            field=models.CharField(blank=True, default='', max_length=7),
        ),
        migrations.AddField(
            model_name='budgetconfig',
            name='pay_num',
            field=models.SmallIntegerField(default=0),
        ),
        migrations.RunPython(set_car_financing_end, unset_car_financing_end),
        migrations.RunPython(run_phantom_dedup, noop),
        migrations.RunPython(coalesce_budget_config_duplicates, noop),
        migrations.AddConstraint(
            model_name='budgetconfig',
            constraint=models.UniqueConstraint(
                condition=models.Q(template__isnull=False),
                fields=('profile', 'template', 'month_str', 'pay_num'),
                name='uniq_budget_tpl_month_pay',
            ),
        ),
        migrations.AddConstraint(
            model_name='budgetconfig',
            constraint=models.UniqueConstraint(
                condition=models.Q(category__isnull=False),
                fields=('profile', 'category', 'month_str', 'pay_num'),
                name='uniq_budget_cat_month_pay',
            ),
        ),
    ]
