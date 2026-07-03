"""Tests for the medical-aid gateway boundary: no clinical data leaves the
server, secrets never appear in source/reprs, adapters are pluggable."""
import os
from datetime import date
from decimal import Decimal
from pathlib import Path

from django.test import TestCase

from billing.models import ClaimSubmission, Invoice, InvoiceItem
from consultations.models import Consultation
from patients.models import Patient

from medaid.adapters import ADAPTERS, get_gateway
from medaid.adapters.manual import ManualAdapter
from medaid.claim_builder import FORBIDDEN_KEYS, ClaimBuilder
from medaid.models import SchemeConfig


def make_invoice():
    patient = Patient.objects.create(
        first_name='Sipho', last_name='Ndlovu', date_of_birth=date(1988, 8, 8),
        gender='M', id_number='8808085800081', phone='0821112222',
        medical_aid_name='Discovery Health', medical_aid_plan='Coastal Core',
        medical_aid_number='123456789', dependant_code='01',
        allergies='Penicillin', chronic_conditions='Diabetes',
        current_medication='Metformin 500mg bd')
    consultation = Consultation.objects.create(
        patient=patient,
        chief_complaint='SECRET-COMPLAINT chest pain on exertion',
        subjective='SECRET-NOTES patient reports crushing pain',
        assessment='SECRET-ASSESSMENT likely angina',
        icd10_code='[{"code": "I20.9", "description": "Angina pectoris"}]')
    invoice = Invoice.objects.create(
        patient=patient, consultation=consultation,
        invoice_number='INV-MEDAID-001',
        date_issued=date(2026, 7, 1), due_date=date(2026, 8, 1),
        icd10_code='[{"code": "I20.9", "description": "Angina pectoris"}]')
    InvoiceItem.objects.create(invoice=invoice, procedure_code='0190',
                               description='Consultation', quantity=1,
                               unit_price=Decimal('550.00'))
    return invoice


class ClaimBuilderTests(TestCase):
    def test_payload_contains_billing_essentials(self):
        payload = ClaimBuilder.build(make_invoice(), practice_number='MP0123456')
        self.assertEqual(payload['member']['member_number'], '123456789')
        self.assertEqual(payload['claim']['icd10_codes'], ['I20.9'])
        self.assertEqual(payload['claim']['lines'][0]['tariff_code'], '0190')

    def test_no_clinical_keys_or_values_in_payload(self):
        """Acceptance: no clinical notes in any outbound payload."""
        payload = ClaimBuilder.build(make_invoice(), practice_number='MP0123456')
        flat = str(payload)
        for key in FORBIDDEN_KEYS:
            self.assertNotIn(f"'{key}'", flat)
        for leaked in ['SECRET-COMPLAINT', 'SECRET-NOTES', 'SECRET-ASSESSMENT',
                       'Penicillin', 'Metformin', 'Diabetes']:
            self.assertNotIn(leaked, flat)

    def test_builder_refuses_forbidden_keys(self):
        with self.assertRaises(ValueError):
            ClaimBuilder._assert_no_clinical_keys({'claim': {'subjective': 'notes'}})


class GatewayAdapterTests(TestCase):
    def test_unconfigured_scheme_falls_back_to_manual(self):
        gateway = get_gateway('Unknown Scheme XYZ')
        self.assertIsInstance(gateway, ManualAdapter)

    def test_configured_scheme_uses_registered_adapter(self):
        SchemeConfig.objects.create(scheme_name='Discovery Health', adapter='manual',
                                    endpoint_url='https://portal.example.test')
        gateway = get_gateway('discovery health')   # case-insensitive
        self.assertIsInstance(gateway, ADAPTERS['manual'])
        self.assertEqual(gateway.config.scheme_name, 'Discovery Health')

    def test_manual_submit_records_claim_submission(self):
        invoice = make_invoice()
        payload = ClaimBuilder.build(invoice, practice_number='MP0123456')
        result = get_gateway(invoice.patient.medical_aid_name).submit_claim(payload)
        self.assertTrue(result.submitted)
        self.assertTrue(result.requires_manual_action)
        self.assertTrue(ClaimSubmission.objects.filter(
            invoice=invoice, submission_reference=result.reference).exists())


class SecretHandlingTests(TestCase):
    def test_config_stores_env_names_not_values(self):
        os.environ['TEST_SCHEME_PASSWORD'] = 'super-secret-value'
        try:
            config = SchemeConfig.objects.create(
                scheme_name='Test Scheme', adapter='manual',
                password_env='TEST_SCHEME_PASSWORD')
            # resolved only on demand, from env
            self.assertEqual(config.credentials()['password'], 'super-secret-value')
            # never in str/repr (what ends up in logs)
            self.assertNotIn('super-secret-value', str(config))
            self.assertNotIn('super-secret-value', repr(config))
            # never persisted in the DB row
            for field in ('username_env', 'password_env', 'api_key_env', 'notes',
                          'scheme_name', 'endpoint_url'):
                self.assertNotEqual(getattr(config, field), 'super-secret-value')
        finally:
            del os.environ['TEST_SCHEME_PASSWORD']

    def test_no_hardcoded_secrets_in_medaid_source(self):
        """Acceptance: secrets are not present in source."""
        app_dir = Path(__file__).resolve().parent
        suspicious = ('password =', 'api_key =', 'secret =', 'token =')
        for py in app_dir.rglob('*.py'):
            if py.name == 'tests.py':
                continue
            text = py.read_text(encoding='utf-8').lower()
            for needle in suspicious:
                for line in text.splitlines():
                    if needle in line and '"' in line.split(needle)[-1]:
                        self.fail(f'Possible hardcoded secret in {py.name}: {line.strip()}')
