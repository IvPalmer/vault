# Data migration: Copy Category template records to RecurringTemplate
# and update RecurringMapping + BudgetConfig FKs.

from django.db import migrations


def forward(apps, schema_editor):
    Category = apps.get_model('api', 'Category')
    RecurringTemplate = apps.get_model('api', 'RecurringTemplate')
    RecurringMapping = apps.get_model('api', 'RecurringMapping')
    BudgetConfig = apps.get_model('api', 'BudgetConfig')

    # 1) Copy template Category records → RecurringTemplate (keeping same UUID)
    template_cat_ids = set()
    template_cats = Category.objects.filter(
        category_type__in=['Fixo', 'Income', 'Investimento']
    )
    for cat in template_cats:
        RecurringTemplate.objects.create(
            id=cat.id,  # keep same UUID for easy FK remapping
            name=cat.name,
            template_type=cat.category_type,
            default_limit=cat.default_limit,
            due_day=cat.due_day,
            is_active=cat.is_active,
            display_order=cat.display_order,
        )
        template_cat_ids.add(cat.id)

    # 2) Update RecurringMapping: set template FK, clear category FK for template-based items
    for mapping in RecurringMapping.objects.filter(category__isnull=False):
        if mapping.category_id in template_cat_ids:
            mapping.template_id = mapping.category_id  # same UUID
            mapping.category_id = None  # no longer a taxonomy reference
            mapping.save(update_fields=['template_id', 'category_id'])

    # 3) Update BudgetConfig: remap template-based configs
    for config in BudgetConfig.objects.filter(category__isnull=False):
        if config.category_id in template_cat_ids:
            config.template_id = config.category_id  # same UUID
            config.category_id = None
            config.save(update_fields=['template_id', 'category_id'])

    # 4) Delete the template records from Category table
    Category.objects.filter(id__in=template_cat_ids).delete()


def reverse(apps, schema_editor):
    """Reverse: copy RecurringTemplate back to Category, re-link FKs."""
    Category = apps.get_model('api', 'Category')
    RecurringTemplate = apps.get_model('api', 'RecurringTemplate')
    RecurringMapping = apps.get_model('api', 'RecurringMapping')
    BudgetConfig = apps.get_model('api', 'BudgetConfig')

    template_ids = set()
    for tpl in RecurringTemplate.objects.all():
        Category.objects.create(
            id=tpl.id,
            name=tpl.name,
            category_type=tpl.template_type,
            default_limit=tpl.default_limit,
            due_day=tpl.due_day,
            is_active=tpl.is_active,
            display_order=tpl.display_order,
        )
        template_ids.add(tpl.id)

    for mapping in RecurringMapping.objects.filter(template__isnull=False):
        if mapping.template_id in template_ids:
            mapping.category_id = mapping.template_id
            mapping.template_id = None
            mapping.save(update_fields=['category_id', 'template_id'])

    for config in BudgetConfig.objects.filter(template__isnull=False):
        if config.template_id in template_ids:
            config.category_id = config.template_id
            config.template_id = None
            config.save(update_fields=['category_id', 'template_id'])

    RecurringTemplate.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0008_add_recurring_template_model'),
    ]

    operations = [
        migrations.RunPython(forward, reverse),
    ]
