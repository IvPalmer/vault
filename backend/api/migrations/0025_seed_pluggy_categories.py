"""
Seed Vault categories from Pluggy's taxonomy and create default PluggyCategoryMapping rows.

Pluggy's categoryId hierarchy:
  - First 2 digits = parent category (e.g. 19 = Transportation)
  - Remaining digits = subcategory (e.g. 19010000 = Taxi and ride-hailing)
  - 00000000 suffix = parent level

This migration:
1. Creates Category rows for each Pluggy parent category
2. Creates Subcategory rows for each Pluggy subcategory
3. Creates PluggyCategoryMapping rows linking pluggy_category_id -> Vault Category/Subcategory
"""
from django.db import migrations

# Pluggy taxonomy: (pluggy_category_id, pluggy_name, vault_category_name, vault_subcategory_name)
# Parent categories use None for subcategory.
# We use Portuguese names for the Vault categories to match the app's locale.
PLUGGY_TAXONOMY = [
    # Income
    ('01000000', 'Income', 'Renda', None),
    ('01030000', 'Entrepreneurial activities', 'Renda', 'Atividade Empresarial'),
    # Loans & financing
    ('02000000', 'Loans and financing', 'Emprestimos', None),
    ('02010000', 'Late payment and overdraft costs', 'Emprestimos', 'Juros e Multas'),
    ('02020000', 'Interests charged', 'Emprestimos', 'Juros Cobrados'),
    # Investments
    ('03000000', 'Investments', 'Investimentos', None),
    ('03020000', 'Fixed income', 'Investimentos', 'Renda Fixa'),
    ('03060000', 'Proceeds interests and dividends', 'Investimentos', 'Rendimentos'),
    # Transfers (internal - not real expenses)
    ('04000000', 'Same person transfer', 'Transferencias', None),
    ('05000000', 'Transfers', 'Transferencias', None),
    ('05020000', 'Transfer - Cash', 'Transferencias', 'Dinheiro'),
    ('05070000', 'Transfer - PIX', 'Transferencias', 'PIX'),
    ('05080000', 'Transfer - TED', 'Transferencias', 'TED'),
    ('05100000', 'Credit card payment', 'Transferencias', 'Pagamento Cartao'),
    # Services
    ('07000000', 'Services', 'Servicos', None),
    ('07010000', 'Telecommunications', 'Contas', 'Telecomunicacoes'),
    ('07010001', 'Internet', 'Contas', 'Internet'),
    ('07010002', 'Mobile', 'Contas', 'Celular'),
    ('07010003', 'TV', 'Contas', 'TV'),
    ('07020000', 'Education', 'Educacao', None),
    ('07020002', 'University', 'Educacao', 'Faculdade'),
    ('07020003', 'School', 'Educacao', 'Escola'),
    ('07030000', 'Wellness and fitness', 'Saude', 'Bem-estar'),
    ('07030001', 'Gyms and fitness centers', 'Saude', 'Academia'),
    ('07030003', 'Wellness', 'Saude', 'Bem-estar'),
    ('07040000', 'Tickets', 'Lazer', 'Ingressos'),
    ('07040003', 'Cinema, theater and concerts', 'Lazer', 'Cinema e Teatro'),
    # Shopping
    ('08000000', 'Shopping', 'Compras', None),
    ('08010000', 'Online shopping', 'Compras', 'Online'),
    ('08020000', 'Electronics', 'Compras', 'Eletronicos'),
    ('08030000', 'Pet supplies and vet', 'Pet', None),
    ('08040000', 'Clothing', 'Compras', 'Roupas'),
    ('08050000', 'Kids and toys', 'Compras', 'Criancas'),
    ('08060000', 'Bookstore', 'Compras', 'Livros'),
    ('08070000', 'Sports goods', 'Compras', 'Esportes'),
    ('08080000', 'Office supplies', 'Compras', 'Escritorio'),
    ('08090000', 'Cashback', 'Compras', 'Cashback'),
    # Digital services
    ('09000000', 'Digital services', 'Servicos Digitais', None),
    ('09020000', 'Video streaming', 'Servicos Digitais', 'Streaming Video'),
    ('09030000', 'Music streaming', 'Servicos Digitais', 'Streaming Musica'),
    # Food
    ('10000000', 'Groceries', 'Alimentacao', 'Mercado'),
    ('11010000', 'Eating out', 'Alimentacao', 'Restaurante'),
    ('11020000', 'Food delivery', 'Alimentacao', 'Delivery'),
    # Travel
    ('12000000', 'Travel', 'Viagem', None),
    ('12010000', 'Airport and airlines', 'Viagem', 'Aereo'),
    ('12020000', 'Accomodation', 'Viagem', 'Hospedagem'),
    # Donations
    ('13000000', 'Donations', 'Doacoes', None),
    # Taxes
    ('15000000', 'Taxes', 'Impostos', None),
    ('15030000', 'Tax on financial operations', 'Impostos', 'IOF'),
    # Bank fees
    ('16000000', 'Bank fees', 'Tarifas Bancarias', None),
    # Housing
    ('17000000', 'Housing', 'Moradia', None),
    ('17020002', 'Electricity', 'Moradia', 'Energia'),
    ('17030000', 'Houseware', 'Casa', None),
    # Healthcare
    ('18000000', 'Healthcare', 'Saude', None),
    ('18020000', 'Pharmacy', 'Saude', 'Farmacia'),
    ('18030000', 'Optometry', 'Saude', 'Otica'),
    ('18040000', 'Hospital clinics and labs', 'Saude', 'Clinica'),
    # Transportation
    ('19000000', 'Transportation', 'Transporte', None),
    ('19010000', 'Taxi and ride-hailing', 'Transporte', 'Taxi e Ride'),
    ('19040000', 'Bicycle', 'Transporte', 'Bicicleta'),
    ('19050000', 'Automotive', 'Transporte', 'Automovel'),
    ('19050001', 'Gas stations', 'Transporte', 'Combustivel'),
    ('19050002', 'Parking', 'Transporte', 'Estacionamento'),
    ('19050003', 'Tolls and in vehicle payment', 'Transporte', 'Pedagio'),
    ('19050005', 'Vehicle maintenance', 'Transporte', 'Manutencao'),
    # Insurance
    ('20000000', 'Insurance', 'Seguros', None),
    ('200300000', 'Health insurance', 'Seguros', 'Plano de Saude'),
    ('200400000', 'Vehicle insurance', 'Seguros', 'Seguro Veiculo'),
    # Leisure
    ('21000000', 'Leisure', 'Lazer', None),
]


def seed_pluggy_categories(apps, schema_editor):
    Profile = apps.get_model('api', 'Profile')
    Category = apps.get_model('api', 'Category')
    Subcategory = apps.get_model('api', 'Subcategory')
    PluggyCategoryMapping = apps.get_model('api', 'PluggyCategoryMapping')

    for profile in Profile.objects.all():
        # Build category cache
        cat_cache = {}
        for cat_name in set(row[2] for row in PLUGGY_TAXONOMY):
            cat, _ = Category.objects.get_or_create(
                profile=profile, name=cat_name,
                defaults={'category_type': 'Variavel', 'is_active': True},
            )
            cat_cache[cat_name] = cat

        # Build subcategory cache and create mappings
        sub_cache = {}
        for pluggy_id, pluggy_name, vault_cat_name, vault_sub_name in PLUGGY_TAXONOMY:
            cat = cat_cache[vault_cat_name]

            sub = None
            if vault_sub_name:
                cache_key = (vault_cat_name, vault_sub_name)
                if cache_key not in sub_cache:
                    sub, _ = Subcategory.objects.get_or_create(
                        category=cat, name=vault_sub_name,
                        defaults={'profile': profile},
                    )
                    sub_cache[cache_key] = sub
                sub = sub_cache[cache_key]

            PluggyCategoryMapping.objects.get_or_create(
                profile=profile, pluggy_category_id=pluggy_id,
                defaults={
                    'pluggy_category_name': pluggy_name,
                    'category': cat,
                    'subcategory': sub,
                },
            )


def reverse_seed(apps, schema_editor):
    PluggyCategoryMapping = apps.get_model('api', 'PluggyCategoryMapping')
    PluggyCategoryMapping.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ('api', '0024_add_pluggy_category_fields'),
    ]
    operations = [
        migrations.RunPython(seed_pluggy_categories, reverse_seed),
    ]
