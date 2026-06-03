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


class PluggyBilledDuplicateSkipTests(TestCase):
    """Regression for the over-aggressive 'unbilled dup' skip that suppressed
    real charges on an OPEN bill.

    The old guard skipped any no-billId CC transaction whose heuristic
    invoice_month merely *had a bill* (``invoice_month in billed_months``).
    On an open bill, recent purchases (last days before close) have no billId
    yet, so real charges like ICATU (the 28th) were silently dropped every
    cycle. The fix only skips a no-billId copy when a billed twin of THAT exact
    purchase exists, and resolves it before touching the dedup indices.
    """

    def _cmd(self, profile, bill_map):
        from api.management.commands.sync_pluggy import Command
        cmd = Command()
        cmd.profile = profile
        cmd.dry_run = False
        cmd.verbosity = 0
        cmd.bill_map = bill_map
        cmd.bill_totals = {}
        cmd.card_account_map = {}
        cmd.rename_rules = []
        cmd.pluggy_mappings = {}
        cmd.categorization_rules = []
        return cmd

    def _ptxn(self, _id, desc, iso_date, amount, bill_id=None, total_inst=None):
        meta = {}
        if bill_id:
            meta['billId'] = bill_id
        if total_inst:
            meta.update(totalInstallments=total_inst, installmentNumber=1)
        return {
            'id': _id,
            'description': desc,
            'descriptionRaw': desc,
            'amount': amount,  # Pluggy CC: positive = charge
            'date': iso_date,
            'creditCardMetadata': meta or None,
        }

    def test_open_bill_and_recurring_charges_kept_only_true_dups_skipped(self):
        profile = Profile.objects.create(name='Tester')
        # Itaú-style: closes the 30th, due the 5th next month (due_offset 1).
        card = Account.objects.create(
            profile=profile, name='Visa Infinite', account_type='credit_card',
            closing_day=30, due_day=5,
        )
        # Pluggy maps the APRIL ICATU charge's billId to invoice 2026-06 — the
        # SAME invoice month the heuristic gives the no-billId MAY charge. That
        # cross-month collision is exactly what an invoice_month-keyed skip got
        # wrong; identity-by-date must keep both.
        bill_map = {'B-MAR': '2026-04', 'B-ICATU-APR': '2026-06', 'B-MAY': '2026-06'}

        pluggy_txns = [
            # Baseline billed charge.
            self._ptxn('t-store', 'STORE OLD', '2026-03-05', 100.0, bill_id='B-MAR'),
            # April instance of a RECURRING charge, billed (billId -> 2026-06),
            # same amount+desc as the May instance below, ~30 days earlier.
            self._ptxn('t-icatu-apr', 'ICATUSEGUROS*Icat', '2026-04-28', 493.83,
                       bill_id='B-ICATU-APR'),
            # NuBank-style genuine duplicate: account-level copy FIRST (no
            # billId), then its billId twin 1 day off. Tests that the skipped
            # copy does NOT poison the content index and drop the twin too.
            self._ptxn('t-petz-acct', 'PETZ DIGITAL', '2026-05-30', 283.65),
            self._ptxn('t-petz-bill', 'PETZ DIGITAL', '2026-05-29', 283.65, bill_id='B-MAY'),
            # MAY instance of the recurring charge, no billId yet (the ICATU
            # failure mode). Heuristic invoice_month = 2026-06 collides with the
            # April instance's billId month, but the dates are ~30 days apart ->
            # NOT a duplicate -> must be KEPT.
            self._ptxn('t-icatu-may', 'ICATUSEGUROS*Icat', '2026-05-28', 493.83),
        ]

        cmd = self._cmd(profile, bill_map)
        new, skipped, updated = cmd._sync_transactions(pluggy_txns, card)

        # Both recurring instances survive (different months, same amount/desc).
        icatu = Transaction.objects.filter(description__icontains='ICATU')
        self.assertEqual(icatu.count(), 2)
        self.assertTrue(icatu.filter(date=date(2026, 5, 28),
                                     amount=Decimal('-493.83')).exists())

        # PETZ kept exactly once (the billId twin), account-level dup dropped.
        self.assertEqual(
            Transaction.objects.filter(description__icontains='PETZ').count(), 1)

        # 4 created (store, icatu-apr, petz-billed, icatu-may); 1 skipped (petz-acct).
        self.assertEqual(new, 4)
        self.assertEqual(skipped, 1)

    def test_billed_dup_key_is_signed(self):
        """The billed-twin gate keys on the SIGNED amount, so a no-billId
        refund (-X) is not collapsed onto a billed same-merchant purchase (+X)
        by THIS gate. (Same-day same-amount refunds are still collapsed by the
        pre-existing abs-keyed synced dedup — out of scope here; the assertion
        below only covers the gate added by this fix.)"""
        profile = Profile.objects.create(name='Tester')
        card = Account.objects.create(
            profile=profile, name='Visa Infinite', account_type='credit_card',
            closing_day=30, due_day=5,
        )
        bill_map = {'B-MAY': '2026-06'}
        # Refund 2 days after the billed purchase — outside the ±1 day window of
        # every dedup path, so it must survive end-to-end.
        pluggy_txns = [
            self._ptxn('t-buy', 'STORE X', '2026-05-20', 50.0, bill_id='B-MAY'),
            self._ptxn('t-refund', 'STORE X', '2026-05-22', -50.0),
        ]
        cmd = self._cmd(profile, bill_map)
        new, skipped, updated = cmd._sync_transactions(pluggy_txns, card)

        store = Transaction.objects.filter(description__icontains='STORE X')
        self.assertEqual(store.count(), 2)
        self.assertEqual(
            set(store.values_list('amount', flat=True)),
            {Decimal('-50.00'), Decimal('50.00')},
        )
        self.assertEqual(new, 2)
        self.assertEqual(skipped, 0)
