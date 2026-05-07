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
    def test_metric_sum_dedupes_pluggy_legacy_pair_only_once(self):
        """Pluggy + legacy versions of the same payment count as one."""
        profile = Profile.objects.create(name='Tester')
        account = Account.objects.create(profile=profile, name='Checking', account_type='checking')
        txns = [
            Transaction.objects.create(
                profile=profile, account=account, date=date(2026, 4, 10),
                description='PIX TRANSF Claudia10/04', amount=Decimal('-100.00'),
                source_file='pluggy:abc',
            ),
            Transaction.objects.create(
                profile=profile, account=account, date=date(2026, 4, 10),
                description='Claudia10 04', amount=Decimal('-100.00'),
                source_file='Checking',
            ),
        ]
        self.assertEqual(_deduped_transaction_sum(txns), Decimal('-100.00'))

    def test_metric_sum_keeps_legitimate_same_day_same_amount(self):
        """
        Two real same-source PIX to the same person same day same amount
        (e.g. user paid Claudia R$200 in morning AND afternoon) MUST count
        twice. Source-aware dedup prevents undercounting.
        """
        profile = Profile.objects.create(name='Tester')
        account = Account.objects.create(profile=profile, name='Checking', account_type='checking')
        txns = [
            Transaction.objects.create(
                profile=profile, account=account, date=date(2026, 4, 10),
                description='PIX TRANSF Claudia10/04', amount=Decimal('-200.00'),
                source_file='pluggy:abc1',
            ),
            Transaction.objects.create(
                profile=profile, account=account, date=date(2026, 4, 10),
                description='PIX TRANSF Claudia10/04', amount=Decimal('-200.00'),
                source_file='pluggy:abc2',
            ),
        ]
        self.assertEqual(_deduped_transaction_sum(txns), Decimal('-400.00'))

    def test_metric_sum_handles_max_count_pair(self):
        """
        If user has 2 real Pluggy payments and only 1 legacy entry (some
        legacy CSVs missed one), real count is max(pluggy=2, legacy=1)=2.
        """
        profile = Profile.objects.create(name='Tester')
        account = Account.objects.create(profile=profile, name='Checking', account_type='checking')
        txns = [
            Transaction.objects.create(
                profile=profile, account=account, date=date(2026, 4, 10),
                description='PIX TRANSF Claudia10/04', amount=Decimal('-100.00'),
                source_file='pluggy:a',
            ),
            Transaction.objects.create(
                profile=profile, account=account, date=date(2026, 4, 10),
                description='PIX TRANSF Claudia10/04', amount=Decimal('-100.00'),
                source_file='pluggy:b',
            ),
            Transaction.objects.create(
                profile=profile, account=account, date=date(2026, 4, 10),
                description='Claudia10 04', amount=Decimal('-100.00'),
                source_file='Checking',
            ),
        ]
        self.assertEqual(_deduped_transaction_sum(txns), Decimal('-200.00'))

    def test_dedup_command_preserves_consorcio_same_day_same_amount(self):
        """
        Real consórcio rows have unique numeric IDs in description
        (CONS PARCELA785892834991). Different IDs → different normalized
        keys → preserved separately even with same date+amount.
        """
        profile = Profile.objects.create(name='Tester')
        account = Account.objects.create(profile=profile, name='Checking', account_type='checking')
        for cota_id in ('785892834991', '785892834926'):
            Transaction.objects.create(
                profile=profile,
                account=account,
                date=date(2026, 1, 10),
                description=f'CONS PARCELA{cota_id}',
                amount=Decimal('-500.00'),
            )

        call_command('dedup_phantom_transactions', apply=True, stdout=StringIO())

        self.assertEqual(Transaction.objects.filter(profile=profile).count(), 2)

    def test_dedup_command_merges_pluggy_legacy_pix_pair(self):
        """
        The Pluggy "PIX TRANSF Claudia28/01" and legacy "Claudia28 01"
        formats normalize to the same key after stripping prefixes.
        Should be merged.
        """
        profile = Profile.objects.create(name='Tester')
        account = Account.objects.create(profile=profile, name='Checking', account_type='checking')
        Transaction.objects.create(
            profile=profile, account=account, date=date(2026, 1, 28),
            description='PIX TRANSF Claudia28/01', amount=Decimal('-2050.00'),
            external_id='pluggy-1', source_file='pluggy:abc',
        )
        Transaction.objects.create(
            profile=profile, account=account, date=date(2026, 1, 28),
            description='Claudia28 01', amount=Decimal('-2050.00'),
            external_id='legacy-1', source_file='Checking',
        )

        call_command('dedup_phantom_transactions', apply=True, stdout=StringIO())

        # Should keep one (the Pluggy version - higher keep_score)
        remaining = list(Transaction.objects.filter(profile=profile))
        self.assertEqual(len(remaining), 1)
        self.assertTrue(remaining[0].source_file.startswith('pluggy:'))

    def test_dedup_command_skips_same_source_pairs(self):
        """
        Two pluggy rows with same date+amount+description (legitimate distinct
        same-day payments to same person) MUST NOT be deleted by the command.
        """
        profile = Profile.objects.create(name='Tester')
        account = Account.objects.create(profile=profile, name='Checking', account_type='checking')
        Transaction.objects.create(
            profile=profile, account=account, date=date(2026, 1, 28),
            description='PIX TRANSF Claudia28/01', amount=Decimal('-200.00'),
            external_id='pluggy-a', source_file='pluggy:abc',
        )
        Transaction.objects.create(
            profile=profile, account=account, date=date(2026, 1, 28),
            description='PIX TRANSF Claudia28/01', amount=Decimal('-200.00'),
            external_id='pluggy-b', source_file='pluggy:def',
        )

        call_command('dedup_phantom_transactions', apply=True, stdout=StringIO())

        self.assertEqual(Transaction.objects.filter(profile=profile).count(), 2)

    def test_dedup_command_skips_short_descriptions(self):
        """
        Generic descriptions like 'IOF' (3 chars normalized) MUST NOT be
        deduped. Length threshold is >= 4.
        """
        profile = Profile.objects.create(name='Tester')
        account = Account.objects.create(profile=profile, name='Checking', account_type='checking')
        Transaction.objects.create(
            profile=profile, account=account, date=date(2026, 1, 28),
            description='IOF', amount=Decimal('-2.50'),
            source_file='pluggy:a',
        )
        Transaction.objects.create(
            profile=profile, account=account, date=date(2026, 1, 28),
            description='Iof', amount=Decimal('-2.50'),
            source_file='Checking',
        )

        call_command('dedup_phantom_transactions', apply=True, stdout=StringIO())

        self.assertEqual(Transaction.objects.filter(profile=profile).count(), 2)


class GetRecurringDataExpiredTests(TestCase):
    def test_expired_template_excluded_from_recurring_data(self):
        """Templates past their end_month should not appear in recurring UI."""
        from api.services import get_recurring_data
        from api.models import RecurringMapping

        profile = Profile.objects.create(name='Tester')
        active_tpl = RecurringTemplate.objects.create(
            profile=profile, name='Aluguel', template_type='Fixo',
            default_limit=Decimal('1000.00'),
        )
        expired_tpl = RecurringTemplate.objects.create(
            profile=profile, name='Carro Velho', template_type='Fixo',
            default_limit=Decimal('500.00'), end_month='2025-12',
        )
        # Mappings for both in May/26 (expired ended Dec/25)
        RecurringMapping.objects.create(
            profile=profile, template=active_tpl, month_str='2026-05',
            expected_amount=Decimal('1000.00'),
        )
        RecurringMapping.objects.create(
            profile=profile, template=expired_tpl, month_str='2026-05',
            expected_amount=Decimal('500.00'),
        )

        result = get_recurring_data('2026-05', profile=profile)
        names = [item['name'] for item in result.get('all', [])]
        self.assertIn('Aluguel', names)
        self.assertNotIn('Carro Velho', names)


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
