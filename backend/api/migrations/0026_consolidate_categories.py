"""
Consolidate old categories into Pluggy-based taxonomy.

1. Merge duplicate categories (accented old → Pluggy canonical)
2. Move CategorizationRules to new categories
3. Re-categorize 'Não categorizado' transactions using Pluggy data
4. Absorb old fixo categories into Pluggy equivalents where applicable
5. Deactivate empty old categories
"""
from django.db import migrations


# old_name → new_name (Pluggy canonical)
MERGE_MAP = {
    'Alimentação': 'Alimentacao',
    'Saúde': 'Saude',
    'Serviços': 'Servicos',
    'OUTROS': 'Outros',
    # Fixo categories that map to Pluggy categories
    'ACADEMIA (CC)': 'Saude',       # -> Saude > Academia
    'ALUGUEL': 'Moradia',
    'CONSORCIO': 'Emprestimos',
    'CONTADOR': 'Servicos',
    'IMPOSTO': 'Impostos',
    'INTERNET + CELULAR': 'Contas',
    'LUZ': 'Moradia',              # -> Moradia > Energia
    'PARCELA CARRO': 'Transporte',
    'PLANO DE SAUDE EU E RAFA': 'Seguros',
    'SEGURO CARRO (CC)': 'Seguros',
    'SEGURO DE VIDA (CC)': 'Seguros',
    'TARIFA ITAU': 'Tarifas Bancarias',
    'TERAPIA': 'Saude',
    'FAMILIA': 'Outros',
    'DSRPTV': 'Outros',
    'TTR': 'Outros',
    'FS': 'Renda',
    'Não categorizado': None,  # special: re-categorize via Pluggy, remainder stays
}


def consolidate(apps, schema_editor):
    Profile = apps.get_model('api', 'Profile')
    Category = apps.get_model('api', 'Category')
    Subcategory = apps.get_model('api', 'Subcategory')
    Transaction = apps.get_model('api', 'Transaction')
    CategorizationRule = apps.get_model('api', 'CategorizationRule')
    RecurringMapping = apps.get_model('api', 'RecurringMapping')
    PluggyCategoryMapping = apps.get_model('api', 'PluggyCategoryMapping')

    for profile in Profile.objects.all():
        cat_by_name = {c.name: c for c in Category.objects.filter(profile=profile)}

        # Build pluggy_category_id -> (category, subcategory) lookup
        pluggy_map = {}
        for pm in PluggyCategoryMapping.objects.filter(profile=profile).select_related('category', 'subcategory'):
            pluggy_map[pm.pluggy_category_id] = (pm.category, pm.subcategory)

        def resolve_pluggy(cat_id):
            if not cat_id:
                return None, None
            r = pluggy_map.get(cat_id)
            if r:
                return r
            parent = cat_id[:2] + '000000'
            return pluggy_map.get(parent, (None, None))

        # 1. Merge old categories into Pluggy ones
        for old_name, new_name in MERGE_MAP.items():
            if old_name == 'Não categorizado' or new_name is None:
                continue
            old_cat = cat_by_name.get(old_name)
            new_cat = cat_by_name.get(new_name)
            if not old_cat or not new_cat:
                continue

            # Move transactions
            Transaction.objects.filter(profile=profile, category=old_cat).update(category=new_cat)

            # Move subcategories
            for sub in Subcategory.objects.filter(category=old_cat):
                # Check if target already has this subcategory
                existing = Subcategory.objects.filter(category=new_cat, name=sub.name).first()
                if existing:
                    # Move transactions from old sub to existing
                    Transaction.objects.filter(profile=profile, subcategory=sub).update(subcategory=existing)
                    sub.delete()
                else:
                    sub.category = new_cat
                    sub.save()

            # Move categorization rules
            for rule in CategorizationRule.objects.filter(category=old_cat):
                # Check for duplicate keyword in target
                if CategorizationRule.objects.filter(profile=profile, keyword=rule.keyword, category=new_cat).exists():
                    rule.delete()
                else:
                    rule.category = new_cat
                    rule.save()

            # Move recurring mappings
            RecurringMapping.objects.filter(category=old_cat).update(category=new_cat)

            # Deactivate old category
            old_cat.is_active = False
            old_cat.save()

        # 2. Re-categorize 'Não categorizado' using Pluggy data
        nao_cat = cat_by_name.get('Não categorizado')
        if nao_cat:
            for txn in Transaction.objects.filter(
                profile=profile, category=nao_cat
            ).exclude(pluggy_category_id=''):
                vault_cat, vault_sub = resolve_pluggy(txn.pluggy_category_id)
                if vault_cat:
                    txn.category = vault_cat
                    txn.subcategory = vault_sub
                    txn.save(update_fields=['category', 'subcategory'])


def reverse(apps, schema_editor):
    pass  # Not reversible in a meaningful way


class Migration(migrations.Migration):
    dependencies = [
        ('api', '0025_seed_pluggy_categories'),
    ]
    operations = [
        migrations.RunPython(consolidate, reverse),
    ]
