"""Tests for auto_link_recurring — the matcher behind "⚡ Auto-link" and the
daily pipeline stage.

Every scenario here is a reduction of a real September/2026 simulation on prod
data, where the old matcher got 4 of 6 links wrong: LUZ took the accountant's
PIX, CONTADOR then took a gas station, VIVO took the Bradesco car insurance,
FAMILIA took a charity donation. The rule that falls out: a recurring item is
recognised by the DESCRIPTION it had in a previous month; amount is only a
tiebreak between candidates that already share that description, never a
matching signal on its own.
"""
from datetime import date
from decimal import Decimal

from django.test import TestCase

from api.models import (
    Account, Profile, RecurringMapping, RecurringTemplate, Transaction,
)
from api.services import auto_link_recurring


class AutoLinkRecurringTests(TestCase):
    def setUp(self):
        self.p = Profile.objects.create(name='Tester')
        self.chk = Account.objects.create(profile=self.p, name='Checking', account_type='checking')
        self.cc = Account.objects.create(profile=self.p, name='MC Black', account_type='credit_card')

    # -- helpers ---------------------------------------------------------

    def _tpl(self, name, ttype='Fixo', expected='0'):
        return RecurringTemplate.objects.create(
            profile=self.p, name=name, template_type=ttype,
            default_limit=Decimal(expected),
        )

    def _mapping(self, tpl, month, expected=None, linked=()):
        m = RecurringMapping.objects.create(
            profile=self.p, template=tpl, month_str=month,
            expected_amount=Decimal(expected) if expected is not None else tpl.default_limit,
            status='mapped' if linked else 'missing',
        )
        for t in linked:
            m.transactions.add(t)
        if linked:
            m.transaction = linked[0]
            m.save()
        return m

    def _txn(self, d, desc, amount, account=None):
        return Transaction.objects.create(
            profile=self.p, account=account or self.chk, date=d,
            description=desc, amount=Decimal(amount),
        )

    def _linked(self, mapping):
        mapping.refresh_from_db()
        return sorted(t.description for t in mapping.transactions.all())

    # -- scenarios -------------------------------------------------------

    def test_previous_month_description_wins_over_boilerplate_overlap(self):
        """LUZ (NEOENERGIA) must not steal the accountant's PIX just because
        both start with "Pagamento de Pix QR Code" and are within 5%."""
        luz = self._tpl('LUZ', expected='350')
        contador = self._tpl('CONTADOR', expected='350')
        # August: both linked to their own PIX. LUZ mapping is created FIRST so
        # the old order-dependent loop processed it first.
        self._mapping(luz, '2026-08', linked=[
            self._txn(date(2026, 8, 18), 'Pagamento de Pix QR Code NEOENERGIA BRASILIA', '-361.50')])
        self._mapping(contador, '2026-08', linked=[
            self._txn(date(2026, 8, 11), 'Pagamento de Pix QR Code COUNTS CONTABILIDADE LTDA', '-375.00')])
        m_luz = self._mapping(luz, '2026-09')
        m_cont = self._mapping(contador, '2026-09')
        counts = self._txn(date(2026, 9, 11), 'Pagamento de Pix QR Code COUNTS CONTABILIDADE LTDA', '-375.00')
        self._txn(date(2026, 9, 2), 'POSTO NOSSA SENHORA DA', '-333.53', account=self.cc)

        r = auto_link_recurring('2026-09', profile=self.p)

        self.assertEqual(self._linked(m_cont), [counts.description])
        self.assertEqual(self._linked(m_luz), [])
        m_luz.refresh_from_db()
        self.assertEqual(m_luz.status, 'missing')
        self.assertEqual(r['linked'], 1)

    def test_amount_alone_never_links(self):
        """VIVO (R$295 last month) must not take a R$275 Bradesco insurance
        charge just because it is within 10% of the expected amount."""
        vivo = self._tpl('VIVO', expected='270')
        self._mapping(vivo, '2026-08', linked=[
            self._txn(date(2026, 8, 26), 'Débito automático DA VIVO-DF 1', '-295.00')])
        m_vivo = self._mapping(vivo, '2026-09')
        self._txn(date(2026, 9, 11), 'BRADESCO AUT*08deRIO DE JANEIRBR', '-275.14', account=self.cc)

        auto_link_recurring('2026-09', profile=self.p)

        self.assertEqual(self._linked(m_vivo), [])

    def test_name_similarity_is_skipped_when_a_previous_pattern_is_known(self):
        """FAMILIA is paid to Roberto every month. When Roberto's PIX has not
        arrived yet, the item stays Faltando — it must not grab a charity
        donation whose description happens to contain "FAMILIAS"."""
        fam = self._tpl('FAMILIA', expected='630')
        self._mapping(fam, '2026-08', linked=[
            self._txn(date(2026, 8, 23), 'Pix enviado ROBERTO ALVARENGA PALMER', '-630.00')])
        m_fam = self._mapping(fam, '2026-09')
        self._txn(date(2026, 9, 9),
                  'Pix enviado ASSOCIACAO DE APOIO A PORTADORES DE CANCER E FAMILIAS CARENTES', '-50.00')

        auto_link_recurring('2026-09', profile=self.p)

        self.assertEqual(self._linked(m_fam), [])

    def test_name_similarity_still_links_a_brand_new_item(self):
        """An item with no link history anywhere can only be recognised by its
        name — whole-word, so FAMILIA does not match FAMILIAS."""
        vivo = self._tpl('VIVO', expected='270')
        m_vivo = self._mapping(vivo, '2026-09')
        fam = self._tpl('FAMILIA', expected='630')
        m_fam = self._mapping(fam, '2026-09')
        vivo_txn = self._txn(date(2026, 9, 26), 'Débito automático DA VIVO-DF 1', '-295.00')
        self._txn(date(2026, 9, 9), 'Pix enviado ASSOCIACAO FAMILIAS CARENTES', '-50.00')

        auto_link_recurring('2026-09', profile=self.p)

        self.assertEqual(self._linked(m_vivo), [vivo_txn.description])
        self.assertEqual(self._linked(m_fam), [])

    def test_two_cards_share_a_description_and_are_told_apart_by_the_bill(self):
        """Both card payments are "Pagamento de boleto ITAU UNIBANCO". The
        Cartao expected amount IS the bill total, so the payment closest to
        each bill goes to that card — and a lone Mastercard payment must not
        be handed to the Visa just because Visa's mapping comes first."""
        visa = self._tpl('Visa Infinite', ttype='Cartao')
        master = self._tpl('Mastercard Black', ttype='Cartao')
        boleto = 'Pagamento de boleto ITAU UNIBANCO HOLDING S.A.'
        self._mapping(visa, '2026-08', expected='3431.74', linked=[
            self._txn(date(2026, 8, 5), boleto, '-3431.74')])
        self._mapping(master, '2026-08', expected='12396.16', linked=[
            self._txn(date(2026, 8, 5), boleto, '-12396.16')])
        m_visa = self._mapping(visa, '2026-09', expected='5021.30')
        m_master = self._mapping(master, '2026-09', expected='13132.55')
        pay_master = self._txn(date(2026, 9, 2), boleto, '-13132.55')

        auto_link_recurring('2026-09', profile=self.p)
        self.assertEqual([float(t.amount) for t in m_master.transactions.all()], [-13132.55])
        self.assertEqual(self._linked(m_visa), [])

        pay_visa = self._txn(date(2026, 9, 3), boleto, '-5021.30')
        auto_link_recurring('2026-09', profile=self.p)
        self.assertEqual([float(t.amount) for t in m_visa.transactions.all()], [-5021.30])
        self.assertEqual([float(t.amount) for t in m_master.transactions.all()], [-13132.55])
        self.assertNotEqual(pay_master.id, pay_visa.id)

    def test_multi_payment_item_takes_as_many_as_last_month(self):
        """CONSORCIO is five parcels with the same description; all five link."""
        cons = self._tpl('CONSORCIO ITAU', ttype='Investimento', expected='5925.39')
        aug = [self._txn(date(2026, 8, 8), f'Pagamento de consórcio CONS PARCELA 4021108{i}', a)
               for i, a in enumerate(['-1292.38', '-1292.38', '-1292.38', '-1113.02', '-1113.02'])]
        self._mapping(cons, '2026-08', linked=aug)
        m = self._mapping(cons, '2026-09')
        for i, a in enumerate(['-1292.38', '-1292.38', '-1292.38', '-1113.02', '-1113.02']):
            self._txn(date(2026, 9, 8), f'Pagamento de consórcio CONS PARCELA 4021109{i}', a)
        self._txn(date(2026, 9, 9), 'Pagamento de consórcio CONS PARCELA 40211099', '-1292.38')

        auto_link_recurring('2026-09', profile=self.p)

        m.refresh_from_db()
        self.assertEqual(m.transactions.count(), 5)
        self.assertEqual(m.status, 'mapped')
        self.assertEqual(m.actual_amount, Decimal('6103.18'))

    def test_digits_inside_the_description_do_not_break_identity(self):
        """Bradesco stamps the month into the description (AUT*07de → AUT*08de)."""
        seg = self._tpl('SEGURO CARRO BRADESCO', expected='273.25')
        self._mapping(seg, '2026-08', linked=[
            self._txn(date(2026, 8, 12), 'BRADESCO AUT*07deRIO DE JANEIRBR', '-275.14', account=self.cc)])
        m = self._mapping(seg, '2026-09')
        sep = self._txn(date(2026, 9, 11), 'BRADESCO AUT*08deRIO DE JANEIRBR', '-275.14', account=self.cc)

        auto_link_recurring('2026-09', profile=self.p)

        self.assertEqual(self._linked(m), [sep.description])

    def test_pattern_is_found_up_to_three_months_back(self):
        """A month with the item skipped/unlinked must not erase the pattern."""
        luz = self._tpl('LUZ', expected='350')
        self._mapping(luz, '2026-06', linked=[
            self._txn(date(2026, 6, 18), 'Pagamento de Pix QR Code NEOENERGIA BRASILIA', '-340.00')])
        self._mapping(luz, '2026-07')
        self._mapping(luz, '2026-08')
        m = self._mapping(luz, '2026-09')
        sep = self._txn(date(2026, 9, 18), 'Pagamento de Pix QR Code NEOENERGIA BRASILIA', '-372.00')

        auto_link_recurring('2026-09', profile=self.p)

        self.assertEqual(self._linked(m), [sep.description])

    def test_dry_run_reports_but_writes_nothing(self):
        contador = self._tpl('CONTADOR', expected='350')
        self._mapping(contador, '2026-08', linked=[
            self._txn(date(2026, 8, 11), 'Pagamento de Pix QR Code COUNTS CONTABILIDADE LTDA', '-375.00')])
        m = self._mapping(contador, '2026-09')
        self._txn(date(2026, 9, 11), 'Pagamento de Pix QR Code COUNTS CONTABILIDADE LTDA', '-375.00')

        r = auto_link_recurring('2026-09', profile=self.p, dry_run=True)

        self.assertEqual(r['linked'], 1)
        self.assertTrue(r['dry_run'])
        self.assertEqual(self._linked(m), [])
        m.refresh_from_db()
        self.assertEqual(m.status, 'missing')

    def test_nothing_to_do_still_returns_the_full_shape(self):
        r = auto_link_recurring('2026-09', profile=self.p)
        self.assertEqual(r['linked'], 0)
        self.assertEqual(r['total_unlinked'], 0)
        self.assertEqual(r['details'], [])

    # -- codex review round 1 ----------------------------------------------

    def test_second_salary_parcel_is_linked_on_a_later_run(self):
        """Salary arrives in two PIX (end of month, day 15). The daily run
        links the first one; when the second lands, the item must take it
        too instead of being skipped as already mapped."""
        fs = self._tpl('FS', ttype='Income', expected='44000')
        pix = 'Pix recebido RAPHAEL AZEVEDO PALMER'
        self._mapping(fs, '2026-08', linked=[
            self._txn(date(2026, 8, 1), pix, '22900.00'),
            self._txn(date(2026, 8, 15), pix, '21600.00')])
        m = self._mapping(fs, '2026-09')
        first = self._txn(date(2026, 9, 1), pix, '23000.00')

        auto_link_recurring('2026-09', profile=self.p)
        self.assertEqual([t.id for t in m.transactions.all()], [first.id])

        second = self._txn(date(2026, 9, 15), pix, '21500.00')
        r = auto_link_recurring('2026-09', profile=self.p)
        self.assertEqual(r['linked'], 1)
        self.assertEqual({t.id for t in m.transactions.all()}, {first.id, second.id})
        m.refresh_from_db()
        self.assertEqual(m.actual_amount, Decimal('44500.00'))
        # A third same-description credit does not fit: only two slots exist.
        self._txn(date(2026, 9, 20), pix, '22000.00')
        auto_link_recurring('2026-09', profile=self.p)
        self.assertEqual(m.transactions.count(), 2)

    def test_transaction_moved_to_another_month_is_not_relinked(self):
        """A September PIX the user allocated to August (cross-month link)
        is owned; September's item must not take it again."""
        contador = self._tpl('CONTADOR', expected='350')
        pix = 'Pagamento de Pix QR Code COUNTS CONTABILIDADE LTDA'
        m_aug = self._mapping(contador, '2026-08', linked=[
            self._txn(date(2026, 8, 11), pix, '-375.00')])
        m_sep = self._mapping(contador, '2026-09')
        moved = self._txn(date(2026, 9, 2), pix, '-375.00')
        m_aug.transactions.add(moved)
        m_aug.cross_month_transactions.add(moved)

        auto_link_recurring('2026-09', profile=self.p)

        self.assertEqual(self._linked(m_sep), [])

    def test_expected_amount_typed_by_the_user_admits_a_big_change(self):
        """LUZ jumped from R$350 to R$600 and the user set expected to 600:
        the unique NEOENERGIA payment must still link (guard vs expected)."""
        luz = self._tpl('LUZ', expected='350')
        self._mapping(luz, '2026-08', linked=[
            self._txn(date(2026, 8, 18), 'Pagamento de Pix QR Code NEOENERGIA BRASILIA', '-350.00')])
        m = self._mapping(luz, '2026-09', expected='600')
        sep = self._txn(date(2026, 9, 18), 'Pagamento de Pix QR Code NEOENERGIA BRASILIA', '-600.00')

        auto_link_recurring('2026-09', profile=self.p)

        self.assertEqual(self._linked(m), [sep.description])

    def test_renamed_item_does_not_inherit_the_template_pattern(self):
        """VIVO was renamed to CLARO for September (is_custom keeps the
        template FK). It must be matched by its new name, not by VIVO's
        history — and VIVO's old charge must not be pulled in."""
        vivo = self._tpl('VIVO', expected='270')
        self._mapping(vivo, '2026-08', linked=[
            self._txn(date(2026, 8, 26), 'Débito automático DA VIVO-DF 1', '-295.00')])
        m = self._mapping(vivo, '2026-09')
        m.is_custom = True
        m.custom_name = 'CLARO'
        m.custom_type = 'Fixo'
        m.save()
        self._txn(date(2026, 9, 26), 'Débito automático DA VIVO-DF 1', '-295.00')
        claro = self._txn(date(2026, 9, 20), 'Débito automático CLARO SA', '-120.00')

        auto_link_recurring('2026-09', profile=self.p)

        self.assertEqual(self._linked(m), [claro.description])

    def test_card_without_a_bill_total_yet_is_not_guessed(self):
        """Both cards share the description and the bill totals are what
        tell them apart; before sync writes them (expected 0) neither card
        may take a payment on last month's amount."""
        visa = self._tpl('Visa Infinite', ttype='Cartao')
        master = self._tpl('Mastercard Black', ttype='Cartao')
        boleto = 'Pagamento de boleto ITAU UNIBANCO HOLDING S.A.'
        self._mapping(visa, '2026-08', expected='100', linked=[
            self._txn(date(2026, 8, 5), boleto, '-100.00')])
        self._mapping(master, '2026-08', expected='200', linked=[
            self._txn(date(2026, 8, 5), boleto, '-200.00')])
        m_visa = self._mapping(visa, '2026-09', expected='0')
        m_master = self._mapping(master, '2026-09', expected='0')
        self._txn(date(2026, 9, 5), boleto, '-200.00')
        self._txn(date(2026, 9, 5), boleto, '-100.00')

        auto_link_recurring('2026-09', profile=self.p)

        self.assertEqual(self._linked(m_visa), [])
        self.assertEqual(self._linked(m_master), [])

    # -- codex review round 2 ----------------------------------------------

    def test_legacy_fk_only_link_is_kept_when_a_second_payment_is_added(self):
        fs = self._tpl('FS', ttype='Income', expected='44000')
        pix = 'Pix recebido RAPHAEL AZEVEDO PALMER'
        self._mapping(fs, '2026-08', linked=[
            self._txn(date(2026, 8, 1), pix, '22900.00'),
            self._txn(date(2026, 8, 15), pix, '21600.00')])
        first = self._txn(date(2026, 9, 1), pix, '23000.00')
        m = RecurringMapping.objects.create(  # legacy shape: FK only, no M2M
            profile=self.p, template=fs, month_str='2026-09',
            expected_amount=Decimal('44000'), status='mapped', transaction=first)
        second = self._txn(date(2026, 9, 15), pix, '21500.00')

        auto_link_recurring('2026-09', profile=self.p)
        self.assertEqual({t.id for t in m.transactions.all()}, {first.id, second.id})

        self._txn(date(2026, 9, 20), pix, '22000.00')
        auto_link_recurring('2026-09', profile=self.p)
        self.assertEqual(m.transactions.count(), 2)

    def test_a_renamed_month_does_not_become_the_template_pattern(self):
        """Aug VIVO → Sep renamed to CLARO → Oct plain VIVO must inherit
        August's VIVO pattern, not September's CLARO."""
        vivo = self._tpl('VIVO', expected='270')
        self._mapping(vivo, '2026-08', linked=[
            self._txn(date(2026, 8, 26), 'Débito automático DA VIVO-DF 1', '-295.00')])
        m_sep = self._mapping(vivo, '2026-09', linked=[
            self._txn(date(2026, 9, 20), 'Débito automático CLARO SA', '-120.00')])
        m_sep.is_custom, m_sep.custom_name, m_sep.custom_type = True, 'CLARO', 'Fixo'
        m_sep.save()
        m_oct = self._mapping(vivo, '2026-10')
        self._txn(date(2026, 10, 20), 'Débito automático CLARO SA', '-120.00')
        vivo_oct = self._txn(date(2026, 10, 26), 'Débito automático DA VIVO-DF 1', '-295.00')

        auto_link_recurring('2026-10', profile=self.p)

        self.assertEqual(self._linked(m_oct), [vivo_oct.description])

    def test_a_renamed_current_link_still_consumes_a_slot(self):
        fs = self._tpl('FS', ttype='Income', expected='44000')
        pix = 'Pix recebido RAPHAEL AZEVEDO PALMER'
        self._mapping(fs, '2026-08', linked=[
            self._txn(date(2026, 8, 1), pix, '22900.00'),
            self._txn(date(2026, 8, 15), pix, '21600.00')])
        m = self._mapping(fs, '2026-09', linked=[
            self._txn(date(2026, 9, 1), 'Salário parte 1', '23000.00'),
            self._txn(date(2026, 9, 15), pix, '21500.00')])
        self._txn(date(2026, 9, 20), pix, '22000.00')

        auto_link_recurring('2026-09', profile=self.p)

        self.assertEqual(m.transactions.count(), 2)

    def test_monthly_expected_is_not_a_per_parcel_reference(self):
        """Five consórcio parcels; a same-description debit of the whole
        monthly amount must not displace a real parcel."""
        cons = self._tpl('CONSORCIO ITAU', ttype='Investimento', expected='5925.39')
        self._mapping(cons, '2026-08', linked=[
            self._txn(date(2026, 8, 8), f'Pagamento de consórcio CONS PARCELA 4021108{i}', a)
            for i, a in enumerate(['-1292.38', '-1292.38', '-1292.38', '-1113.02', '-1113.02'])])
        m = self._mapping(cons, '2026-09')
        for i, a in enumerate(['-1293.38', '-1293.38', '-1293.38', '-1114.02', '-1114.02']):
            self._txn(date(2026, 9, 8), f'Pagamento de consórcio CONS PARCELA 4021109{i}', a)
        whole = self._txn(date(2026, 9, 9), 'Pagamento de consórcio CONS PARCELA 40211099', '-5925.39')

        auto_link_recurring('2026-09', profile=self.p)

        self.assertEqual(m.transactions.count(), 5)
        self.assertNotIn(whole.id, {t.id for t in m.transactions.all()})

    def test_card_without_a_bill_total_is_not_linked_by_name_either(self):
        master = self._tpl('Mastercard Black', ttype='Cartao')
        m = self._mapping(master, '2026-09', expected='0')
        self._txn(date(2026, 9, 5), 'Int Mc Black', '-30.00', account=self.cc)

        auto_link_recurring('2026-09', profile=self.p)

        self.assertEqual(self._linked(m), [])
