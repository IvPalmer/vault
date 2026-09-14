"""smart_categorize's subcategory pass.

Until 2026-09-14 the engine only looked at rows with NO category. A row that
sync categorized at Pluggy's parent level (NETFLIX.COM → Assinaturas, no
subcategory) was never revisited, even with five earlier NETFLIX.COM rows
carrying Streaming Video. The Subcategoria column stayed "—" every month.
"""
from datetime import date
from decimal import Decimal

from django.test import TestCase

from api.models import (
    Account, CategorizationRule, Category, PluggyCategoryMapping, Profile,
    Subcategory, Transaction,
)
from api.services import smart_categorize


class SubcategoryPassTests(TestCase):
    def setUp(self):
        self.p = Profile.objects.create(name='Tester')
        self.cc = Account.objects.create(profile=self.p, name='MC Black', account_type='credit_card')
        self.subs = Category.objects.create(profile=self.p, name='Assinaturas', category_type='Variavel')
        self.video = Subcategory.objects.create(profile=self.p, category=self.subs, name='Streaming Video')
        self.ai = Subcategory.objects.create(profile=self.p, category=self.subs, name='AI')
        self.seguros = Category.objects.create(profile=self.p, name='Seguros', category_type='Fixo')
        self.veic = Subcategory.objects.create(profile=self.p, category=self.seguros, name='Seguro Veiculo')

    def _txn(self, d, desc, amount='-44.90', category=None, sub=None, pluggy=''):
        return Transaction.objects.create(
            profile=self.p, account=self.cc, date=d, description=desc,
            amount=Decimal(amount), category=category, subcategory=sub,
            pluggy_category_id=pluggy,
        )

    def test_history_fills_the_subcategory_of_a_categorized_row(self):
        for m in range(4, 9):
            self._txn(date(2026, m, 11), 'NETFLIX.COM', category=self.subs, sub=self.video)
        row = self._txn(date(2026, 9, 11), 'NETFLIX.COM', category=self.subs)

        r = smart_categorize(profile=self.p, min_confidence=0.90)

        row.refresh_from_db()
        self.assertEqual(row.subcategory, self.video)
        self.assertEqual(row.category, self.subs)
        self.assertEqual(r['subcategorized'], 1)
        self.assertEqual(r['categorized'], 0)

    def test_runs_even_when_nothing_is_uncategorized(self):
        """The early return for 'no uncategorized rows' must not skip the pass."""
        self._txn(date(2026, 7, 11), 'NETFLIX.COM', category=self.subs, sub=self.video)
        self._txn(date(2026, 8, 11), 'NETFLIX.COM', category=self.subs, sub=self.video)
        row = self._txn(date(2026, 9, 11), 'NETFLIX.COM', category=self.subs)
        self.assertFalse(Transaction.objects.filter(profile=self.p, category__isnull=True).exists())

        smart_categorize(profile=self.p, min_confidence=0.90)

        row.refresh_from_db()
        self.assertEqual(row.subcategory, self.video)

    def test_split_or_single_history_does_not_fill(self):
        self._txn(date(2026, 7, 11), 'OPENAI *CHATGPT SUBSCR', category=self.subs, sub=self.video)
        self._txn(date(2026, 8, 11), 'OPENAI *CHATGPT SUBSCR', category=self.subs, sub=self.ai)
        split = self._txn(date(2026, 9, 11), 'OPENAI *CHATGPT SUBSCR', category=self.subs)
        self._txn(date(2026, 8, 11), 'PATREON* MEMBERSHIP', category=self.subs, sub=self.ai)
        single = self._txn(date(2026, 9, 11), 'PATREON* MEMBERSHIP', category=self.subs)

        smart_categorize(profile=self.p, min_confidence=0.90)

        split.refresh_from_db(); single.refresh_from_db()
        self.assertIsNone(split.subcategory)
        self.assertIsNone(single.subcategory)

    def test_history_is_per_category_and_digits_are_ignored(self):
        """BRADESCO AUT*07de → AUT*08de is the same charge; a Seguros row
        learns from Seguros history only."""
        self._txn(date(2026, 7, 12), 'BRADESCO AUT*06deRIO DE JANEIRBR', '-275.14', self.seguros, self.veic)
        self._txn(date(2026, 8, 12), 'BRADESCO AUT*07deRIO DE JANEIRBR', '-275.14', self.seguros, self.veic)
        row = self._txn(date(2026, 9, 11), 'BRADESCO AUT*08deRIO DE JANEIRBR', '-275.14', self.seguros)
        other = self._txn(date(2026, 9, 11), 'BRADESCO AUT*08deRIO DE JANEIRBR', '-275.14', self.subs)

        smart_categorize(profile=self.p, min_confidence=0.90)

        row.refresh_from_db(); other.refresh_from_db()
        self.assertEqual(row.subcategory, self.veic)
        self.assertIsNone(other.subcategory)

    def test_rule_refines_subcategory_but_never_moves_the_category(self):
        CategorizationRule.objects.create(profile=self.p, keyword='NETFLIX', category=self.subs,
                                          subcategory=self.video, priority=100)
        CategorizationRule.objects.create(profile=self.p, keyword='BRADESCO', category=self.seguros,
                                          subcategory=self.veic, priority=100)
        netflix = self._txn(date(2026, 9, 11), 'NETFLIX.COM', category=self.subs)
        wrong_cat = self._txn(date(2026, 9, 11), 'BRADESCO AUT*08de', '-275.14', category=self.subs)

        smart_categorize(profile=self.p, min_confidence=0.90)

        netflix.refresh_from_db(); wrong_cat.refresh_from_db()
        self.assertEqual(netflix.subcategory, self.video)
        self.assertEqual(wrong_cat.category, self.subs)
        self.assertIsNone(wrong_cat.subcategory)

    def test_pluggy_mapping_subcategory_is_backfilled(self):
        PluggyCategoryMapping.objects.create(profile=self.p, pluggy_category_id='09010000',
                                             category=self.subs, subcategory=self.video)
        row = self._txn(date(2026, 9, 11), 'SOME STREAMING', category=self.subs, pluggy='09010000')
        other_cat = self._txn(date(2026, 9, 11), 'SOME STREAMING', category=self.seguros, pluggy='09010000')

        smart_categorize(profile=self.p, min_confidence=0.90)

        row.refresh_from_db(); other_cat.refresh_from_db()
        self.assertEqual(row.subcategory, self.video)
        self.assertIsNone(other_cat.subcategory)

    def test_dry_run_reports_without_writing(self):
        self._txn(date(2026, 7, 11), 'NETFLIX.COM', category=self.subs, sub=self.video)
        self._txn(date(2026, 8, 11), 'NETFLIX.COM', category=self.subs, sub=self.video)
        row = self._txn(date(2026, 9, 11), 'NETFLIX.COM', category=self.subs)

        r = smart_categorize(profile=self.p, dry_run=True, min_confidence=0.90)

        row.refresh_from_db()
        self.assertIsNone(row.subcategory)
        self.assertEqual(r['subcategorized'], 1)
        self.assertTrue(any(d['method'] == 'sub:exact_match' for d in r['details']))

    def test_month_scope_is_respected(self):
        self._txn(date(2026, 7, 11), 'NETFLIX.COM', category=self.subs, sub=self.video)
        self._txn(date(2026, 8, 11), 'NETFLIX.COM', category=self.subs, sub=self.video)
        old = self._txn(date(2026, 6, 11), 'NETFLIX.COM', category=self.subs)
        new = self._txn(date(2026, 9, 11), 'NETFLIX.COM', category=self.subs)

        smart_categorize(month_str='2026-09', profile=self.p, min_confidence=0.90)

        old.refresh_from_db(); new.refresh_from_db()
        self.assertIsNone(old.subcategory)
        self.assertEqual(new.subcategory, self.video)

    # -- codex review ----------------------------------------------------

    def test_manually_touched_rows_are_left_alone(self):
        """"Remover subcategoria" leaves a manual row with category and no
        subcategory; the nightly pass must not put it back."""
        self._txn(date(2026, 7, 11), 'NETFLIX.COM', category=self.subs, sub=self.video)
        self._txn(date(2026, 8, 11), 'NETFLIX.COM', category=self.subs, sub=self.video)
        row = self._txn(date(2026, 9, 11), 'NETFLIX.COM', category=self.subs)
        row.is_manually_categorized = True
        row.save()

        smart_categorize(profile=self.p, min_confidence=0.90)

        row.refresh_from_db()
        self.assertIsNone(row.subcategory)

    def test_rule_beats_pluggy_mapping(self):
        soft = Subcategory.objects.create(profile=self.p, category=self.subs, name='Software')
        PluggyCategoryMapping.objects.create(profile=self.p, pluggy_category_id='09000000',
                                             category=self.subs, subcategory=soft)
        CategorizationRule.objects.create(profile=self.p, keyword='NETFLIX', category=self.subs,
                                          subcategory=self.video, priority=100)
        row = self._txn(date(2026, 9, 11), 'NETFLIX.COM', category=self.subs, pluggy='09000000')

        smart_categorize(profile=self.p, min_confidence=0.90)

        row.refresh_from_db()
        self.assertEqual(row.subcategory, self.video)

    def test_installment_siblings_beat_merchant_history(self):
        """Two DECATHLON siblings say Roupas; three unrelated DECATHLON charges
        say Geral. The blank third sibling must follow its own purchase."""
        compras = Category.objects.create(profile=self.p, name='Compras Gerais', category_type='Variavel')
        roupas = Subcategory.objects.create(profile=self.p, category=compras, name='Roupas e Acessorios')
        geral = Subcategory.objects.create(profile=self.p, category=compras, name='Geral')
        for d, desc in [(date(2026, 3, 5), 'DECATHLON'), (date(2026, 4, 5), 'DECATHLON'), (date(2026, 5, 5), 'DECATHLON')]:
            self._txn(d, desc, '-80.00', compras, geral)
        kw = dict(amount='-127.99', category=compras)
        for pos in ('01/03', '02/03'):
            t = self._txn(date(2026, 7, 10), f'DECATHLON         {pos}', sub=roupas, **kw)
            t.is_installment, t.installment_info = True, pos
            t.save()
        blank = self._txn(date(2026, 9, 10), 'DECATHLON         03/03', **kw)
        blank.is_installment, blank.installment_info = True, '03/03'
        blank.save()

        smart_categorize(profile=self.p, min_confidence=0.90)

        blank.refresh_from_db()
        self.assertEqual(blank.subcategory, roupas)

    def test_dry_run_and_apply_agree(self):
        """Preview must be what apply does — same fixture as the siblings test."""
        compras = Category.objects.create(profile=self.p, name='Compras Gerais', category_type='Variavel')
        roupas = Subcategory.objects.create(profile=self.p, category=compras, name='Roupas e Acessorios')
        geral = Subcategory.objects.create(profile=self.p, category=compras, name='Geral')
        for d in (date(2026, 3, 5), date(2026, 4, 5), date(2026, 5, 5)):
            self._txn(d, 'DECATHLON', '-80.00', compras, geral)
        for pos in ('01/03', '02/03'):
            t = self._txn(date(2026, 7, 10), f'DECATHLON         {pos}', '-127.99', compras, roupas)
            t.is_installment, t.installment_info = True, pos
            t.save()
        blank = self._txn(date(2026, 9, 10), 'DECATHLON         03/03', '-127.99', compras)
        blank.is_installment, blank.installment_info = True, '03/03'
        blank.save()

        preview = smart_categorize(profile=self.p, dry_run=True, min_confidence=0.90)
        blank.refresh_from_db()
        self.assertIsNone(blank.subcategory)
        applied = smart_categorize(profile=self.p, min_confidence=0.90)
        blank.refresh_from_db()

        self.assertEqual(blank.subcategory, roupas)
        for k in ('categorized', 'subcategorized', 'installment_reconciled'):
            self.assertEqual(preview[k], applied[k], k)
        self.assertTrue(preview['dry_run'])
        self.assertFalse(applied['dry_run'])


class ClearSubcategoryViaApiTests(TestCase):
    """The UI's "Remover subcategoria" is PATCH {subcategory: null}. That click
    must survive the nightly pass, so the PATCH marks the row manual."""

    def setUp(self):
        self.p = Profile.objects.create(name='Tester')
        self.cc = Account.objects.create(profile=self.p, name='MC Black', account_type='credit_card')
        self.subs = Category.objects.create(profile=self.p, name='Assinaturas', category_type='Variavel')
        self.video = Subcategory.objects.create(profile=self.p, category=self.subs, name='Streaming Video')
        for m in (7, 8):
            Transaction.objects.create(profile=self.p, account=self.cc, date=date(2026, m, 11),
                                       description='NETFLIX.COM', amount=Decimal('-44.90'),
                                       category=self.subs, subcategory=self.video)
        self.row = Transaction.objects.create(profile=self.p, account=self.cc, date=date(2026, 9, 11),
                                              description='NETFLIX.COM', amount=Decimal('-44.90'),
                                              category=self.subs, subcategory=self.video)

    def test_patch_clearing_subcategory_sticks_through_the_nightly_pass(self):
        from unittest import mock
        with mock.patch('api.middleware.VAULT_INTERNAL_TOKEN', 's3cret'):
            resp = self.client.patch(
                f'/api/transactions/{self.row.id}/', data='{"subcategory": null}',
                content_type='application/json',
                HTTP_X_INTERNAL_TOKEN='s3cret', HTTP_X_PROFILE_ID=str(self.p.id),
            )
        self.assertEqual(resp.status_code, 200, resp.content[:200])
        self.row.refresh_from_db()
        self.assertIsNone(self.row.subcategory)
        self.assertTrue(self.row.is_manually_categorized)

        smart_categorize(profile=self.p, min_confidence=0.90)

        self.row.refresh_from_db()
        self.assertIsNone(self.row.subcategory)
