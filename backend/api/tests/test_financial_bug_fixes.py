from datetime import date
from decimal import Decimal
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from api.models import Account, BudgetConfig, Profile, RecurringTemplate, SalaryConfig, Transaction
from api.services import _deduped_transaction_sum, sync_salary_to_budget


class RecurringTemplateContractTests(TestCase):
    def test_contract_term_bounds_active_months(self):
        profile = Profile.objects.create(name='Tester')
        template = RecurringTemplate.objects.create(
            profile=profile,
            name='Financiamento Carro',
            template_type='Fixo',
            default_limit=Decimal('1000.00'),
            contract_start='2026-05',
            contract_term_months=3,
        )

        self.assertFalse(template.is_active_in_month('2026-04'))
        self.assertTrue(template.is_active_in_month('2026-05'))
        self.assertTrue(template.is_active_in_month('2026-07'))
        self.assertFalse(template.is_active_in_month('2026-08'))


class TransactionDedupTests(TestCase):
    def test_metric_sum_dedupes_case_variants_only_once(self):
        profile = Profile.objects.create(name='Tester')
        account = Account.objects.create(profile=profile, name='Checking', account_type='checking')
        txns = [
            Transaction.objects.create(
                profile=profile,
                account=account,
                date=date(2026, 4, 10),
                description='JUROS LIMITE DA CONTA',
                amount=Decimal('-100.00'),
            ),
            Transaction.objects.create(
                profile=profile,
                account=account,
                date=date(2026, 4, 10),
                description='Juros Limite Da Conta',
                amount=Decimal('-100.00'),
            ),
        ]

        self.assertEqual(_deduped_transaction_sum(txns), Decimal('-100.00'))

    def test_dedup_command_preserves_consorcio_same_day_same_amount(self):
        profile = Profile.objects.create(name='Tester')
        account = Account.objects.create(profile=profile, name='Checking', account_type='checking')
        for _ in range(2):
            Transaction.objects.create(
                profile=profile,
                account=account,
                date=date(2026, 1, 10),
                description='CONS PARCELA',
                amount=Decimal('-500.00'),
            )

        call_command('dedup_phantom_transactions', apply=True, stdout=StringIO())

        self.assertEqual(Transaction.objects.filter(profile=profile).count(), 2)


class SalaryBudgetSyncTests(TestCase):
    @patch('api.services._get_wise_fees', return_value=None)
    @patch('api.services._get_usd_brl_rate', return_value=5.0)
    def test_salary_sync_writes_one_budget_config_per_payment(self, *_mocks):
        profile = Profile.objects.create(name='Tester')
        template = RecurringTemplate.objects.create(
            profile=profile,
            name='FS',
            template_type='Income',
            default_limit=Decimal('0.00'),
        )
        SalaryConfig.objects.create(
            profile=profile,
            hourly_rate_usd=Decimal('50.00'),
            hours_per_day=Decimal('8.0'),
            wise_fee_pct=Decimal('0.0000'),
            wise_fee_flat=Decimal('0.00'),
            tax_hold_pct=Decimal('0.0000'),
            income_template=template,
            is_active=True,
        )

        sync_salary_to_budget(profile, num_months=1, start_month_str='2026-04')

        configs = BudgetConfig.objects.filter(
            profile=profile,
            template=template,
            month_str='2026-04',
        ).order_by('pay_num')
        self.assertEqual(list(configs.values_list('pay_num', flat=True)), [1, 2])
        self.assertEqual(sum((cfg.limit_override for cfg in configs), Decimal('0.00')), Decimal('44000.00'))
