import uuid
from django.db import migrations


BUILTIN_TEMPLATES = [
    {
        'bank_name': 'Itau',
        'account_type': 'checking',
        'display_name': 'Itau Conta Corrente',
        'file_patterns': ['Extrato*.ofx', 'Extrato*.txt'],
        'file_format': 'ofx',
        'encoding': 'latin1',
        'import_instructions': 'Exportar do Itau: Extrato > Exportar > OFX/Money. Arquivo: Extrato*.ofx',
    },
    {
        'bank_name': 'Itau',
        'account_type': 'credit_card',
        'display_name': 'Itau Mastercard',
        'file_patterns': ['master-*.csv'],
        'file_format': 'csv',
        'sign_inversion': True,
        'default_closing_day': 30,
        'default_due_day': 5,
        'payment_filter_patterns': ['PAGAMENTO EFETUADO', 'DEVOLUCAO SALDO CREDOR', 'EST DEVOL SALDO CREDOR'],
        'import_instructions': 'Exportar fatura do Itau como CSV. Renomear: master-MMYY.csv (ex: master-0126.csv para Jan/2026)',
    },
    {
        'bank_name': 'Itau',
        'account_type': 'credit_card',
        'display_name': 'Itau Visa',
        'file_patterns': ['visa-*.csv'],
        'file_format': 'csv',
        'sign_inversion': True,
        'default_closing_day': 30,
        'default_due_day': 5,
        'payment_filter_patterns': ['PAGAMENTO EFETUADO', 'DEVOLUCAO SALDO CREDOR', 'EST DEVOL SALDO CREDOR'],
        'import_instructions': 'Exportar fatura do Itau como CSV. Renomear: visa-MMYY.csv (ex: visa-0126.csv para Jan/2026)',
    },
    {
        'bank_name': 'NuBank',
        'account_type': 'checking',
        'display_name': 'NuBank Conta',
        'file_patterns': ['NU_*.ofx'],
        'file_format': 'ofx',
        'encoding': 'utf-8',
        'description_cleaner': 'nubank',
        'import_instructions': 'Exportar extrato NuBank como OFX. Arquivo: NU_*.ofx',
    },
    {
        'bank_name': 'NuBank',
        'account_type': 'credit_card',
        'display_name': 'NuBank Cartao',
        'file_patterns': ['Nubank_*.ofx'],
        'file_format': 'ofx',
        'encoding': 'utf-8',
        'default_closing_day': 22,
        'default_due_day': 7,
        'description_cleaner': 'nubank',
        'import_instructions': 'Exportar fatura NuBank como OFX. Arquivo: Nubank_YYYY-MM-DD.ofx',
    },
]

# Map existing account names to bank template display_names for backfill
ACCOUNT_NAME_TO_TEMPLATE = {
    # Palmer's accounts (Itau)
    'Checking': 'Itau Conta Corrente',
    'Mastercard Black': 'Itau Mastercard',
    'Mastercard - Rafa': 'Itau Mastercard',
    'Visa Infinite': 'Itau Visa',
    # Rafa's accounts (NuBank)
    'NuBank Conta': 'NuBank Conta',
    'NuBank Cartão': 'NuBank Cartao',
    'NuBank Cartao': 'NuBank Cartao',
}


def seed_bank_templates(apps, schema_editor):
    BankTemplate = apps.get_model('api', 'BankTemplate')
    Account = apps.get_model('api', 'Account')

    # Create built-in templates
    template_map = {}  # display_name -> BankTemplate instance
    for tmpl_data in BUILTIN_TEMPLATES:
        defaults = {
            'bank_name': tmpl_data['bank_name'],
            'account_type': tmpl_data['account_type'],
            'file_patterns': tmpl_data.get('file_patterns', []),
            'file_format': tmpl_data.get('file_format', 'csv'),
            'sign_inversion': tmpl_data.get('sign_inversion', False),
            'encoding': tmpl_data.get('encoding', 'utf-8'),
            'payment_filter_patterns': tmpl_data.get('payment_filter_patterns', []),
            'description_cleaner': tmpl_data.get('description_cleaner', ''),
            'default_closing_day': tmpl_data.get('default_closing_day'),
            'default_due_day': tmpl_data.get('default_due_day'),
            'import_instructions': tmpl_data.get('import_instructions', ''),
            'is_builtin': True,
        }
        obj, _ = BankTemplate.objects.get_or_create(
            display_name=tmpl_data['display_name'],
            defaults=defaults,
        )
        template_map[tmpl_data['display_name']] = obj

    # Backfill existing accounts
    for account in Account.objects.filter(bank_template__isnull=True):
        template_display_name = ACCOUNT_NAME_TO_TEMPLATE.get(account.name)
        if template_display_name and template_display_name in template_map:
            account.bank_template = template_map[template_display_name]
            account.save(update_fields=['bank_template'])


def reverse_seed(apps, schema_editor):
    BankTemplate = apps.get_model('api', 'BankTemplate')
    Account = apps.get_model('api', 'Account')
    # Unlink accounts first, then delete built-in templates
    Account.objects.filter(bank_template__isnull=False).update(bank_template=None)
    BankTemplate.objects.filter(is_builtin=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0015_profile_fields_bank_template'),
    ]

    operations = [
        migrations.RunPython(seed_bank_templates, reverse_seed),
    ]
