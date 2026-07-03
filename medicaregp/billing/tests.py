"""Tests for versioned tariffs: rate changes must never alter issued bills,
and billing must split medical vs surgical line items."""
from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase

from patients.models import Patient

from billing.models import Invoice, InvoiceItem, TariffCode, TariffRate


def make_patient():
    return Patient.objects.create(
        first_name='Naledi', last_name='Dlamini', date_of_birth=date(1975, 3, 2),
        gender='F', id_number='7503025800083', phone='0837654321')


class TariffVersioningTests(TestCase):
    def setUp(self):
        self.patient = make_patient()
        self.consult_tariff = TariffCode.objects.get(code='0190')   # Medical
        self.suture_tariff = TariffCode.objects.get(code='0221')    # Surgical

    def test_rate_on_picks_rate_in_force(self):
        TariffRate.objects.create(tariff=self.consult_tariff,
                                  effective_from=date(2026, 7, 1), amount=Decimal('600.00'))
        self.assertEqual(self.consult_tariff.rate_on(date(2026, 6, 30)).amount, Decimal('550.00'))
        self.assertEqual(self.consult_tariff.rate_on(date(2026, 7, 1)).amount, Decimal('600.00'))

    def test_tariff_change_does_not_alter_issued_bill(self):
        """Acceptance: changing a tariff does not retroactively alter bills."""
        invoice = Invoice.objects.create(
            patient=self.patient, invoice_number='INV-TEST-001',
            date_issued=date(2026, 6, 1), due_date=date(2026, 7, 1))
        rate = self.consult_tariff.rate_on(invoice.date_issued)
        InvoiceItem.objects.create(
            invoice=invoice, tariff=self.consult_tariff,
            procedure_code=self.consult_tariff.code,
            description=self.consult_tariff.description,
            quantity=1, unit_price=rate.amount)   # snapshot at billing time
        total_before = invoice.total()

        # Price rises later — issued invoice must not move.
        TariffRate.objects.create(tariff=self.consult_tariff,
                                  effective_from=date(2026, 6, 15), amount=Decimal('999.00'))
        invoice.refresh_from_db()
        self.assertEqual(invoice.total(), total_before)
        item = invoice.items.first()
        self.assertEqual(item.unit_price, rate.amount)

    def test_medical_and_surgical_line_items_split(self):
        """Acceptance: billing produces medical and surgical items separately."""
        invoice = Invoice.objects.create(
            patient=self.patient, invoice_number='INV-TEST-002',
            date_issued=date(2026, 6, 1), due_date=date(2026, 7, 1))
        InvoiceItem.objects.create(invoice=invoice, tariff=self.consult_tariff,
                                   description='Consult', quantity=1, unit_price=Decimal('550.00'))
        InvoiceItem.objects.create(invoice=invoice, tariff=self.suture_tariff,
                                   description='Sutures', quantity=1, unit_price=Decimal('650.00'))

        medical = invoice.medical_items()
        surgical = invoice.surgical_items()
        self.assertEqual(len(medical), 1)
        self.assertEqual(len(surgical), 1)
        self.assertEqual(medical[0].category, 'Medical')
        self.assertEqual(surgical[0].category, 'Surgical')
        self.assertEqual(invoice.medical_subtotal(), 550.00)
        self.assertEqual(invoice.surgical_subtotal(), 650.00)

    def test_item_category_follows_tariff(self):
        invoice = Invoice.objects.create(
            patient=self.patient, invoice_number='INV-TEST-003',
            date_issued=date(2026, 6, 1), due_date=date(2026, 7, 1))
        item = InvoiceItem.objects.create(
            invoice=invoice, tariff=self.suture_tariff, category='Medical',  # wrong on purpose
            description='Sutures', quantity=1, unit_price=Decimal('650.00'))
        self.assertEqual(item.category, 'Surgical')   # save() corrected it
