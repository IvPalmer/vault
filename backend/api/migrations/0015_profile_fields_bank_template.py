import uuid
from django.db import migrations, models
import django.db.models.deletion


def set_existing_profiles_setup_completed(apps, schema_editor):
    """Existing profiles are already configured, so mark setup_completed=True."""
    Profile = apps.get_model('api', 'Profile')
    Profile.objects.all().update(setup_completed=True)


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0014_backfill_nubank_invoice_month'),
    ]

    operations = [
        # --- Profile new fields ---
        migrations.AddField(
            model_name='profile',
            name='cc_display_mode',
            field=models.CharField(
                choices=[('invoice', 'Invoice Month'), ('transaction', 'Transaction Month')],
                default='invoice',
                help_text='How CC transactions are grouped in monthly view',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='profile',
            name='investment_target_pct',
            field=models.DecimalField(
                decimal_places=2, default=10.0,
                help_text='Target investment percentage of income',
                max_digits=5,
            ),
        ),
        migrations.AddField(
            model_name='profile',
            name='investment_allocation',
            field=models.JSONField(
                blank=True, default=dict,
                help_text='Investment allocation breakdown, e.g. {"Renda Fixa": 40, "Renda Variavel": 40, "Crypto": 20}',
            ),
        ),
        migrations.AddField(
            model_name='profile',
            name='budget_strategy',
            field=models.CharField(
                choices=[
                    ('percentage', 'Percentage of Income'),
                    ('fixed', 'Fixed Amounts'),
                    ('smart', 'Smart (Statement-based)'),
                ],
                default='percentage',
                help_text='How budget limits are calculated',
                max_length=30,
            ),
        ),
        migrations.AddField(
            model_name='profile',
            name='setup_completed',
            field=models.BooleanField(default=False),
        ),
        # --- BankTemplate model ---
        migrations.CreateModel(
            name='BankTemplate',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('bank_name', models.CharField(max_length=100)),
                ('account_type', models.CharField(choices=[('checking', 'Checking'), ('credit_card', 'Credit Card'), ('manual', 'Manual')], max_length=20)),
                ('display_name', models.CharField(max_length=100)),
                ('file_patterns', models.JSONField(default=list, help_text='Glob patterns for file detection, e.g. ["master-*.csv"]')),
                ('file_format', models.CharField(choices=[('csv', 'CSV'), ('ofx', 'OFX'), ('txt', 'TXT')], default='csv', max_length=20)),
                ('sign_inversion', models.BooleanField(default=False, help_text='Negate amounts on import (for CC CSVs)')),
                ('encoding', models.CharField(default='utf-8', max_length=20)),
                ('payment_filter_patterns', models.JSONField(default=list, help_text='Regex patterns to filter payment entries')),
                ('description_cleaner', models.CharField(blank=True, help_text='Cleaner function: "nubank", "itau", ""', max_length=100)),
                ('default_closing_day', models.IntegerField(blank=True, null=True)),
                ('default_due_day', models.IntegerField(blank=True, null=True)),
                ('import_instructions', models.TextField(blank=True, help_text='User-facing import instructions (markdown)')),
                ('is_builtin', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['bank_name', 'account_type', 'display_name'],
            },
        ),
        # --- Account.bank_template FK ---
        migrations.AddField(
            model_name='account',
            name='bank_template',
            field=models.ForeignKey(
                blank=True, null=True,
                help_text='Bank template this account was created from',
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='accounts',
                to='api.banktemplate',
            ),
        ),
        # --- Backfill setup_completed for existing profiles ---
        migrations.RunPython(
            set_existing_profiles_setup_completed,
            migrations.RunPython.noop,
        ),
    ]
