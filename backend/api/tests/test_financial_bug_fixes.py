from datetime import date
from decimal import Decimal
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from api.models import (
    Account, BudgetConfig, Category, Profile, RecurringTemplate,
    SalaryConfig, Subcategory, Transaction,
)
from api.services import (
    _deduped_transaction_sum, get_metricas, sync_salary_to_budget,
    build_apple_amount_map, resolve_apple_subscription, _is_generic_apple,
)


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


class CrossMonthLinkedActualTests(TestCase):
    def test_cross_month_income_counts_once_toward_a_entrar(self):
        """A cross-month linked txn lives in BOTH `transactions` and
        `cross_month_transactions` (map_transaction_to_category writes both), so
        summing the two sets counts it twice and can mark a partially-received
        income as fully received, zeroing a_entrar."""
        from api.services import get_metricas, map_transaction_to_category
        from api.models import RecurringMapping, SalaryConfig

        profile = Profile.objects.create(name='Tester')
        account = Account.objects.create(
            profile=profile, name='Checking', account_type='checking',
        )
        tpl = RecurringTemplate.objects.create(
            profile=profile, name='FS', template_type='Income',
            default_limit=Decimal('44417.30'),
        )
        SalaryConfig.objects.create(
            profile=profile, hourly_rate_usd=Decimal('52.00'),
            income_template=tpl, is_active=True,
        )
        mapping = RecurringMapping.objects.create(
            profile=profile, template=tpl, month_str='2026-03',
            expected_amount=Decimal('44417.30'),
        )
        # Half the salary, paid on the last day of the PREVIOUS month and
        # linked forward into March — the real FS pattern.
        txn = Transaction.objects.create(
            profile=profile, account=account, date=date(2026, 2, 28),
            description='Pix recebido', amount=Decimal('22000.00'),
            month_str='2026-02',
        )
        map_transaction_to_category(txn.id, mapping_id=mapping.id, profile=profile)

        mapping.refresh_from_db()
        self.assertTrue(mapping.transactions.filter(id=txn.id).exists())
        self.assertTrue(mapping.cross_month_transactions.filter(id=txn.id).exists())

        result = get_metricas('2026-03', profile=profile)
        # One of the two salary transfers is in → the other is still pending.
        self.assertAlmostEqual(result['a_entrar'], 22417.30, places=2)
        self.assertAlmostEqual(result['entradas_atuais'], 22000.00, places=2)


class PendingSettlementTests(TestCase):
    """A bill's `expected` is a projection that drifts month to month, so any
    payment settles it. Income arrives in more than one payment, so what's left
    is genuinely pending."""

    def setUp(self):
        self.profile = Profile.objects.create(name='Tester')
        self.account = Account.objects.create(
            profile=self.profile, name='Checking', account_type='checking',
        )

    def _mapping(self, name, ttype, expected, actual=None):
        from api.models import RecurringMapping
        tpl = RecurringTemplate.objects.create(
            profile=self.profile, name=name, template_type=ttype,
            default_limit=Decimal(expected),
        )
        mapping = RecurringMapping.objects.create(
            profile=self.profile, template=tpl, month_str='2026-03',
            expected_amount=Decimal(expected),
        )
        if actual is not None:
            amount = Decimal(actual) if ttype == 'Income' else -Decimal(actual)
            txn = Transaction.objects.create(
                profile=self.profile, account=self.account, date=date(2026, 3, 10),
                description=name, amount=amount, month_str='2026-03',
            )
            mapping.transactions.add(txn)
            mapping.match_mode = 'manual'
            mapping.save()
        return mapping

    def test_bill_paid_under_projection_leaves_nothing_pending(self):
        """Rent projected at 5273.71, actually debited 5015.85 — the real debit
        replaces the projection; the 257.86 difference is not a debt."""
        self._mapping('ALUGUEL', 'Fixo', '5273.71', actual='5015.85')
        result = get_metricas('2026-03', profile=self.profile)
        self.assertAlmostEqual(result['a_pagar'], 0.0, places=2)

    def test_bill_paid_far_under_projection_still_settles(self):
        """Below the old 90% tolerance: still settled, since expected is only
        an estimate."""
        self._mapping('ACADEMIA', 'Fixo', '630.00', actual='400.00')
        result = get_metricas('2026-03', profile=self.profile)
        self.assertAlmostEqual(result['a_pagar'], 0.0, places=2)

    def test_unpaid_bill_is_fully_pending(self):
        self._mapping('ALUGUEL', 'Fixo', '5273.71')
        result = get_metricas('2026-03', profile=self.profile)
        self.assertAlmostEqual(result['a_pagar'], 5273.71, places=2)

    def test_income_overpaid_never_goes_negative(self):
        self._mapping('FS', 'Income', '40000.00', actual='42000.00')
        result = get_metricas('2026-03', profile=self.profile)
        self.assertAlmostEqual(result['a_entrar'], 0.0, places=2)

    def _salary_mapping(self, expected, payments):
        from api.models import RecurringMapping, SalaryConfig
        tpl = RecurringTemplate.objects.create(
            profile=self.profile, name='FS', template_type='Income',
            default_limit=Decimal(expected),
        )
        SalaryConfig.objects.create(
            profile=self.profile, hourly_rate_usd=Decimal('52.00'),
            income_template=tpl, is_active=True,
        )
        mapping = RecurringMapping.objects.create(
            profile=self.profile, template=tpl, month_str='2026-03',
            expected_amount=Decimal(expected), match_mode='manual',
        )
        for i, amount in enumerate(payments):
            txn = Transaction.objects.create(
                profile=self.profile, account=self.account,
                date=date(2026, 3, 1 + i), description='Pix recebido',
                amount=Decimal(amount), month_str='2026-03',
            )
            mapping.transactions.add(txn)
        return mapping

    def test_both_salary_payments_in_leave_no_residue(self):
        """The projection is a placeholder converted at a live FX rate: once both
        transfers land, the gap to `expected` is drift, not pending money."""
        self._salary_mapping('42398.12', ['20000.00', '20000.00'])
        result = get_metricas('2026-03', profile=self.profile)
        self.assertAlmostEqual(result['a_entrar'], 0.0, places=2)

    def test_one_of_two_salary_payments_keeps_the_other_pending(self):
        self._salary_mapping('44417.30', ['22000.00'])
        result = get_metricas('2026-03', profile=self.profile)
        self.assertAlmostEqual(result['a_entrar'], 22417.30, places=2)

    def test_salary_wrongly_split_into_three_still_settles(self):
        """Some months a transfer lands in the wrong month and gets linked back,
        leaving three payments — still fully received."""
        self._salary_mapping('42398.12', ['20000.00', '15000.00', '5000.00'])
        result = get_metricas('2026-03', profile=self.profile)
        self.assertAlmostEqual(result['a_entrar'], 0.0, places=2)

    def test_non_salary_income_settles_on_one_payment(self):
        """Rafa's SALARIO BOX has no SalaryConfig — one transfer is the whole
        thing, however far from the estimate."""
        self._mapping('SALARIO BOX', 'Income', '5500.00', actual='5200.00')
        result = get_metricas('2026-03', profile=self.profile)
        self.assertAlmostEqual(result['a_entrar'], 0.0, places=2)

    def test_status_salary_partial_until_both_payments_land(self):
        from api.services import get_recurring_data
        self._salary_mapping('44417.30', ['22000.00'])
        items = {i['name']: i for i in get_recurring_data('2026-03', profile=self.profile)['all']}
        self.assertEqual(items['FS']['status'], 'Parcial')

    def test_category_matched_bill_accumulates_instead_of_settling(self):
        """Assinaturas bundles every subscription charge into one category-mode
        item, so one R$19,90 charge must NOT settle the whole R$2153,90."""
        from api.models import Category, RecurringMapping
        cat = Category.objects.create(profile=self.profile, name='Assinaturas')
        tpl = RecurringTemplate.objects.create(
            profile=self.profile, name='Assinaturas', template_type='Fixo',
            default_limit=Decimal('2153.90'),
        )
        RecurringMapping.objects.create(
            profile=self.profile, template=tpl, category=cat, month_str='2026-03',
            expected_amount=Decimal('2153.90'), match_mode='category',
        )
        Transaction.objects.create(
            profile=self.profile, account=self.account, date=date(2026, 3, 4),
            description='NETFLIX', amount=Decimal('-19.90'), month_str='2026-03',
            category=cat,
        )
        result = get_metricas('2026-03', profile=self.profile)
        self.assertAlmostEqual(result['a_pagar'], 2134.00, places=2)

    def test_investment_toward_target_reads_partial(self):
        from api.services import get_recurring_data
        self._mapping('CONSORCIO', 'Investimento', '2000.00', actual='500.00')
        items = {i['name']: i for i in get_recurring_data('2026-03', profile=self.profile)['all']}
        self.assertEqual(items['CONSORCIO']['status'], 'Parcial')

    def test_legacy_fk_only_bill_settles(self):
        """Pre-M2M rows carry only the `transaction` FK. The count must follow the
        same fallback as the amount, or a paid bill reads as still owing."""
        from api.models import RecurringMapping
        tpl = RecurringTemplate.objects.create(
            profile=self.profile, name='ALUGUEL', template_type='Fixo',
            default_limit=Decimal('5273.71'),
        )
        txn = Transaction.objects.create(
            profile=self.profile, account=self.account, date=date(2026, 3, 10),
            description='ALUGUEL', amount=Decimal('-5015.85'), month_str='2026-03',
        )
        RecurringMapping.objects.create(
            profile=self.profile, template=tpl, month_str='2026-03',
            expected_amount=Decimal('5273.71'), transaction=txn, match_mode='manual',
        )
        result = get_metricas('2026-03', profile=self.profile)
        self.assertAlmostEqual(result['a_pagar'], 0.0, places=2)

    def test_status_bill_under_projection_reads_paid(self):
        from api.services import get_recurring_data
        self._mapping('ACADEMIA', 'Fixo', '630.00', actual='400.00')
        items = {i['name']: i for i in get_recurring_data('2026-03', profile=self.profile)['all']}
        self.assertEqual(items['ACADEMIA']['status'], 'Pago')


class CardBillPaymentNotSpendingTests(TestCase):
    """Paying the card bill moves money to settle purchases that were already
    counted. Counting the payment too doubles the card's spending."""

    def setUp(self):
        from api.models import RecurringMapping
        self.profile = Profile.objects.create(name='Tester')
        self.checking = Account.objects.create(
            profile=self.profile, name='Checking', account_type='checking',
        )
        self.card = Account.objects.create(
            profile=self.profile, name='Visa Infinite', account_type='credit_card',
        )
        # Purchases on the card, billed this month.
        for i, amount in enumerate(['-600.00', '-400.00']):
            Transaction.objects.create(
                profile=self.profile, account=self.card, date=date(2026, 3, 3 + i),
                description='STORE', amount=Decimal(amount), month_str='2026-03',
                invoice_month='2026-03',
            )
        # The bill payment, debited from checking. Pluggy words it exactly like a
        # consórcio/financing boleto, so only the Cartao link identifies it.
        self.payment = Transaction.objects.create(
            profile=self.profile, account=self.checking, date=date(2026, 3, 5),
            description='Pagamento de boleto ITAU UNIBANCO HOLDING S.',
            amount=Decimal('-1000.00'), month_str='2026-03',
        )
        tpl = RecurringTemplate.objects.create(
            profile=self.profile, name='Visa Infinite', template_type='Cartao',
            default_limit=Decimal('1000.00'),
        )
        mapping = RecurringMapping.objects.create(
            profile=self.profile, template=tpl, month_str='2026-03',
            expected_amount=Decimal('1000.00'), match_mode='manual',
        )
        mapping.transactions.add(self.payment)

    def test_bill_payment_is_not_counted_on_top_of_the_purchases(self):
        result = get_metricas('2026-03', profile=self.profile)
        # R$1.000 of purchases — NOT 2.000 (purchases + the payment settling them).
        self.assertAlmostEqual(result['gastos_atuais'], 1000.00, places=2)

    def test_real_boleto_with_a_lookalike_description_still_counts(self):
        """The consórcio boleto reads almost identically but is real spending —
        it has no Cartao link, so it must survive."""
        Transaction.objects.create(
            profile=self.profile, account=self.checking, date=date(2026, 3, 6),
            description='Pagamento de boleto BANCO ITAU UNIBANCO HOLD',
            amount=Decimal('-1633.31'), month_str='2026-03',
        )
        result = get_metricas('2026-03', profile=self.profile)
        self.assertAlmostEqual(result['gastos_atuais'], 2633.31, places=2)

    def test_category_matched_card_mapping_also_excludes_the_payment(self):
        """A Cartao mapping switched to category mode counts every transaction in
        its category as the payment — this must agree, or the double count is
        silently back."""
        from api.models import Category, RecurringMapping
        cat = Category.objects.create(profile=self.profile, name='Transferencias')
        self.payment.category = cat
        self.payment.save()
        mapping = RecurringMapping.objects.get(month_str='2026-03', template__name='Visa Infinite')
        mapping.transactions.clear()
        mapping.match_mode = 'category'
        mapping.category = cat
        mapping.save()

        result = get_metricas('2026-03', profile=self.profile)
        self.assertAlmostEqual(result['gastos_atuais'], 1000.00, places=2)

    def test_analytics_mirror_agrees_with_metricas(self):
        from api.services import _month_actual_income_expense
        metricas = get_metricas('2026-03', profile=self.profile)
        _income, expense = _month_actual_income_expense('2026-03', self.profile)
        self.assertAlmostEqual(float(expense), metricas['gastos_atuais'], places=2)


class SaudeDoMesTests(TestCase):
    """Health measures discretionary spending against the discretionary envelope.
    Commitments (fixo, the card bill, investments) are not overspending."""

    def setUp(self):
        from api.models import BalanceAnchor, Category, RecurringMapping
        self.profile = Profile.objects.create(name='Tester')
        self.account = Account.objects.create(
            profile=self.profile, name='Checking', account_type='checking',
        )
        # Real prior balance — the envelope starts from it.
        BalanceAnchor.objects.create(
            profile=self.profile, date=date(2026, 2, 28),
            balance=Decimal('10000.00'),
        )
        self.cat = Category.objects.create(profile=self.profile, name='Mercado')
        income_tpl = RecurringTemplate.objects.create(
            profile=self.profile, name='SALARIO', template_type='Income',
            default_limit=Decimal('10000.00'),
        )
        RecurringMapping.objects.create(
            profile=self.profile, template=income_tpl, month_str='2026-03',
            expected_amount=Decimal('10000.00'),
        )

    def _spend(self, amount):
        Transaction.objects.create(
            profile=self.profile, account=self.account, date=date(2026, 3, 10),
            description='MERCADO', amount=-Decimal(amount), month_str='2026-03',
            category=self.cat,
        )

    def test_spending_inside_the_envelope_is_healthy(self):
        self._spend('1000.00')
        result = get_metricas('2026-03', profile=self.profile)
        self.assertEqual(result['saude'], 'SAUDÁVEL')

    def test_spending_past_the_envelope_warns(self):
        self._spend('19500.00')
        result = get_metricas('2026-03', profile=self.profile)
        self.assertEqual(result['saude_level'], 'warning')

    def test_committed_fixo_alone_is_not_overspending(self):
        """Rent eats 9.000 of a 10.000 income and only 1.500 is discretionary,
        well inside the 9.000 envelope. The old ratio counted the rent as
        spending and called this ATENÇÃO — commitment is not overspending."""
        from api.models import RecurringMapping
        tpl = RecurringTemplate.objects.create(
            profile=self.profile, name='ALUGUEL', template_type='Fixo',
            default_limit=Decimal('9000.00'),
        )
        mapping = RecurringMapping.objects.create(
            profile=self.profile, template=tpl, month_str='2026-03',
            expected_amount=Decimal('9000.00'), match_mode='manual',
        )
        txn = Transaction.objects.create(
            profile=self.profile, account=self.account, date=date(2026, 3, 5),
            description='ALUGUEL', amount=Decimal('-9000.00'), month_str='2026-03',
        )
        mapping.transactions.add(txn)
        self._spend('1500.00')
        result = get_metricas('2026-03', profile=self.profile)
        self.assertEqual(result['saude'], 'SAUDÁVEL')

    def test_envelope_matches_the_card(self):
        """SAÚDE and the ORÇAMENTO VARIÁVEL card must read the same envelope."""
        self._spend('1000.00')
        result = get_metricas('2026-03', profile=self.profile)
        self.assertGreater(result['orcamento_variavel'], 0)
        self.assertEqual(result['saude'], 'SAUDÁVEL')


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


class AppleAmountCategorizationTests(TestCase):
    """Apple subscriptions arrive brandless ("APPLECOMBILL"); only the amount
    distinguishes the service. These cover the learn-from-history resolver and
    the retroactive fix command."""

    def setUp(self):
        self.profile = Profile.objects.create(name='Tester')
        self.acct = Account.objects.create(
            profile=self.profile, name='Visa', account_type='credit_card')
        self.cat = Category.objects.create(profile=self.profile, name='Assinaturas')
        self.subs = {
            n: Subcategory.objects.create(profile=self.profile, category=self.cat, name=n)
            for n in ['Apple One', 'Streaming Video', 'Software', 'Gaming']
        }

    def _txn(self, desc, iso_date, amount, sub=None, manual=False):
        return Transaction.objects.create(
            profile=self.profile, account=self.acct, date=date.fromisoformat(iso_date),
            description=desc, amount=Decimal(str(amount)), category=self.cat,
            subcategory=self.subs[sub] if sub else None,
            is_manually_categorized=manual,
        )

    def _seed_history(self):
        # Reconciled, brand-named ground truth.
        self._txn('Disney+ Premium (via Apple)', '2026-03-29', '-66.90', 'Streaming Video')
        self._txn('Disney+ Premium (via Apple)', '2026-04-29', '-66.90', 'Streaming Video')
        self._txn('Apple Developer Anual (via Apple)', '2026-01-30', '-548.46', 'Software')
        # Price-change collision: TV+ at 14.90 (older), Arcade at 14.90 (newer)
        # — recency must win, so 14.90 → Gaming.
        self._txn('Apple TV+ (via Apple)', '2025-09-14', '-14.90', 'Streaming Video')
        self._txn('Apple Arcade (via Apple)', '2026-04-14', '-14.90', 'Gaming')
        # Near-identical amounts that integer rounding would have collided.
        self._txn('Notion (via Apple)', '2026-03-10', '-29.99', 'Software')
        self._txn('iCloud Mini (via Apple)', '2026-03-10', '-29.90', 'Apple One')
        # Generic noise — must be EXCLUDED from the learned map.
        self._txn('Apple Services', '2026-02-24', '-66.90', 'Apple One')

    def test_build_map_excludes_generic_and_recency_wins(self):
        self._seed_history()
        m = build_apple_amount_map(self.profile)
        self.assertEqual(m[Decimal('66.90')]['description'], 'Disney+ Premium (via Apple)')
        self.assertEqual(m[Decimal('548.46')]['description'], 'Apple Developer Anual (via Apple)')
        # Recency: newest 14.90 is Apple Arcade.
        self.assertEqual(m[Decimal('14.90')]['description'], 'Apple Arcade (via Apple)')
        self.assertEqual(m[Decimal('14.90')]['subcategory_id'], self.subs['Gaming'].id)
        # Cent precision: 29.90 and 29.99 must NOT collide.
        self.assertEqual(m[Decimal('29.99')]['description'], 'Notion (via Apple)')
        self.assertEqual(m[Decimal('29.90')]['description'], 'iCloud Mini (via Apple)')

    def test_resolve_hits_known_amount_and_misses_novel(self):
        self._seed_history()
        m = build_apple_amount_map(self.profile)
        hit = resolve_apple_subscription(self.profile, Decimal('-66.90'), m)
        self.assertEqual(hit['description'], 'Disney+ Premium (via Apple)')
        self.assertEqual(hit['subcategory'], self.subs['Streaming Video'])
        # Novel amount → no history → abstain.
        self.assertIsNone(resolve_apple_subscription(self.profile, Decimal('-79.00'), m))
        self.assertTrue(_is_generic_apple('Apple Services'))
        self.assertFalse(_is_generic_apple('Disney+ Premium (via Apple)'))

    def test_recategorize_command_fixes_generic_respects_manual_and_novel(self):
        self._seed_history()
        wrong = self._txn('Apple Services', '2026-05-29', '-66.90', 'Apple One')  # → Disney+
        manual = self._txn('Apple Services', '2026-05-26', '-66.90', 'Software', manual=True)
        novel = self._txn('Apple Services', '2026-05-06', '-79.00', 'Apple One')  # no history

        call_command('recategorize_apple', profile='Tester', verbosity=0)

        wrong.refresh_from_db(); manual.refresh_from_db(); novel.refresh_from_db()
        # Generic 66.90 fixed to Disney+/Streaming Video.
        self.assertEqual(wrong.description, 'Disney+ Premium (via Apple)')
        self.assertEqual(wrong.subcategory, self.subs['Streaming Video'])
        # Manual override untouched.
        self.assertEqual(manual.description, 'Apple Services')
        self.assertEqual(manual.subcategory, self.subs['Software'])
        # Novel amount left generic.
        self.assertEqual(novel.description, 'Apple Services')
        self.assertEqual(novel.subcategory, self.subs['Apple One'])


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
        cmd.apple_amount_map = {}
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
