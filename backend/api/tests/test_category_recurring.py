"""Tests for category-based recurring items (e.g. Assinaturas).

Covers the expected-amount derivation, CC-share detection, and that
initialize_month propagates match_mode/category/derived-expected onto the
monthly mapping. Budget-neutrality (subs leave variável, fixo_for_budget
unchanged) is validated against live prod data separately.
"""
from datetime import date
from decimal import Decimal

from django.test import TestCase

from api.models import (
    Account, Category, Profile, RecurringMapping, RecurringTemplate, Transaction,
)
from api.services import (
    _category_actual_for_month,
    _category_cc_share,
    create_recurring_template,
    derive_expected_amount,
    initialize_month,
)


class CategoryRecurringTests(TestCase):
    def setUp(self):
        self.p = Profile.objects.create(name='Tester')
        self.cc = Account.objects.create(profile=self.p, name='MC Black', account_type='credit_card')
        self.chk = Account.objects.create(profile=self.p, name='Checking', account_type='checking')
        self.cat = Category.objects.create(profile=self.p, name='Assinaturas')

    def _txn(self, d, amount, account=None, category=None):
        return Transaction.objects.create(
            profile=self.p, account=account or self.cc, date=d,
            description='sub', amount=Decimal(amount), category=category or self.cat,
        )

    def test_category_actual_for_month_gross_excludes_internal(self):
        self._txn(date(2026, 4, 5), '-2000')
        Transaction.objects.create(
            profile=self.p, account=self.cc, date=date(2026, 4, 6),
            description='internal', amount=Decimal('-500'), category=self.cat,
            is_internal_transfer=True,
        )
        self.assertEqual(_category_actual_for_month(self.cat, '2026-04', profile=self.p), Decimal('2000.00'))

    def test_derive_avg_3m(self):
        self._txn(date(2026, 2, 5), '-2000')
        self._txn(date(2026, 3, 5), '-2200')
        self._txn(date(2026, 4, 5), '-1800')
        tpl = RecurringTemplate.objects.create(
            profile=self.p, name='Assinaturas', template_type='Fixo',
            match_mode='category', category=self.cat,
            expected_source='avg_3m', expected_lookback_months=3,
        )
        # avg(Feb,Mar,Apr) = (2000+2200+1800)/3 = 2000
        self.assertEqual(derive_expected_amount(tpl, '2026-05', profile=self.p), Decimal('2000.00'))

    def test_derive_prev_month(self):
        self._txn(date(2026, 3, 5), '-2200')
        self._txn(date(2026, 4, 5), '-1800')
        tpl = RecurringTemplate.objects.create(
            profile=self.p, name='A', template_type='Fixo',
            match_mode='category', category=self.cat, expected_source='prev_month',
        )
        self.assertEqual(derive_expected_amount(tpl, '2026-05', profile=self.p), Decimal('1800.00'))

    def test_derive_max_floor_avg(self):
        self._txn(date(2026, 4, 5), '-1000')
        tpl = RecurringTemplate.objects.create(
            profile=self.p, name='A', template_type='Fixo',
            match_mode='category', category=self.cat,
            expected_source='max_floor_avg', expected_floor_amount=Decimal('1500.00'),
            expected_lookback_months=1,
        )
        # avg(Apr)=1000, floor 1500 → 1500
        self.assertEqual(derive_expected_amount(tpl, '2026-05', profile=self.p), Decimal('1500.00'))

    def test_prev_month_falls_back_when_prior_empty(self):
        # Only Apr has data; deriving for a future month whose prior months are empty
        # must fall back to the most recent non-zero month instead of returning 0.
        self._txn(date(2026, 4, 5), '-1500')
        tpl = RecurringTemplate.objects.create(
            profile=self.p, name='A', template_type='Fixo',
            match_mode='category', category=self.cat, expected_source='prev_month',
        )
        self.assertEqual(derive_expected_amount(tpl, '2026-08', profile=self.p), Decimal('1500.00'))

    def test_derive_manual_falls_back_to_default_limit(self):
        tpl = RecurringTemplate.objects.create(
            profile=self.p, name='Aluguel', template_type='Fixo',
            default_limit=Decimal('5000.00'),  # match_mode defaults to 'manual'
        )
        self.assertEqual(derive_expected_amount(tpl, '2026-05', profile=self.p), Decimal('5000.00'))

    def test_cc_share_predominantly_cc(self):
        self._txn(date(2026, 5, 5), '-1800', account=self.cc)
        self._txn(date(2026, 5, 6), '-200', account=self.chk)
        share = _category_cc_share(
            self.cat, '2026-05', profile=self.p, cc_account_ids={self.cc.id},
        )
        self.assertGreaterEqual(share, Decimal('0.5'))  # 1800/2000 = 0.9

    def test_cc_share_mostly_checking(self):
        self._txn(date(2026, 5, 5), '-200', account=self.cc)
        self._txn(date(2026, 5, 6), '-1800', account=self.chk)
        share = _category_cc_share(
            self.cat, '2026-05', profile=self.p, cc_account_ids={self.cc.id},
        )
        self.assertLess(share, Decimal('0.5'))  # 200/2000 = 0.1

    def test_initialize_month_creates_category_mapping(self):
        self._txn(date(2026, 4, 5), '-2000')
        tpl = RecurringTemplate.objects.create(
            profile=self.p, name='Assinaturas', template_type='Fixo',
            match_mode='category', category=self.cat,
            expected_source='avg_3m', expected_lookback_months=1,
            default_limit=Decimal('0.00'),  # no default — must still be initialized
        )
        initialize_month('2026-05', profile=self.p)
        m = RecurringMapping.objects.get(template=tpl, month_str='2026-05')
        self.assertEqual(m.match_mode, 'category')
        self.assertEqual(m.category_id, self.cat.id)
        self.assertEqual(m.expected_amount, Decimal('2000.00'))

    # --- API input validation (hardening) ---
    def test_create_rejects_category_mode_non_fixo(self):
        with self.assertRaises(ValueError):
            create_recurring_template(
                'X', 'Income', 0, profile=self.p,
                match_mode='category', category_id=str(self.cat.id), expected_source='avg_3m',
            )

    def test_create_rejects_invalid_category(self):
        with self.assertRaises(ValueError):
            create_recurring_template(
                'X', 'Fixo', 0, profile=self.p,
                match_mode='category',
                category_id='00000000-0000-0000-0000-000000000000', expected_source='avg_3m',
            )

    def test_create_rejects_invalid_expected_source(self):
        with self.assertRaises(ValueError):
            create_recurring_template(
                'X', 'Fixo', 0, profile=self.p,
                match_mode='category', category_id=str(self.cat.id), expected_source='bogus',
            )

    def test_create_clamps_lookback(self):
        res = create_recurring_template(
            'X', 'Fixo', 0, profile=self.p,
            match_mode='category', category_id=str(self.cat.id),
            expected_source='avg_3m', expected_lookback_months=99,
        )
        tpl = RecurringTemplate.objects.get(id=res['id'])
        self.assertEqual(tpl.expected_lookback_months, 12)
