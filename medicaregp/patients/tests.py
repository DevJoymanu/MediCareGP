from datetime import date, time

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse

from appointments.models import Appointment
from consultations.models import Consultation
from scripts.models import Document
from patients.models import Patient


class PatientDetailViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='secret123')
        self.user.groups.add(Group.objects.get(name='Doctor'))
        self.patient = Patient.objects.create(
            first_name='Aphiwe',
            last_name='Zulu',
            date_of_birth=date(1995, 6, 1),
            gender='F',
            id_number='9506012345089',
            phone='0810000000',
        )
        self.appointment = Appointment.objects.create(
            patient=self.patient,
            date=date(2026, 4, 10),
            time=time(10, 15),
            reason='Consultation',
        )
        self.consultation = Consultation.objects.create(
            patient=self.patient,
            appointment=self.appointment,
            subjective='Headache',
            objective='Normal vitals',
            assessment='Tension headache',
            plan='Hydrate and rest',
        )
        self.document = Document.objects.create(
            patient=self.patient,
            doc_type='Prescription',
            content='Paracetamol 500mg',
        )

    def test_detail_includes_related_records(self):
        self.client.login(username='tester', password='secret123')

        response = self.client.get(reverse('patient_detail', args=[self.patient.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Appointments (1)')
        self.assertContains(response, 'Consultations (1)')
        self.assertContains(response, 'Documents (1)')
        self.assertContains(response, self.document.doc_type)


class ReceptionRBACTests(TestCase):
    """Reception must see demographics only — enforced at queryset/form
    level, not just hidden in templates."""

    def setUp(self):
        self.receptionist = User.objects.create_user('reception', password='pw')
        self.receptionist.groups.add(Group.objects.get(name='Reception'))
        self.patient = Patient.objects.create(
            first_name='Buhle', last_name='Khumalo',
            date_of_birth=date(1992, 2, 2), gender='F',
            id_number='9202025800088', phone='0824445555',
            medical_aid_name='Bonitas', medical_aid_number='MEM-777',
            allergies='CLINICAL-ALLERGY-Penicillin',
            chronic_conditions='CLINICAL-CHRONIC-Asthma',
            current_medication='CLINICAL-MED-Ventolin',
        )
        Consultation.objects.create(
            patient=self.patient, subjective='CLINICAL-NOTE severe wheeze')

    def test_reception_queryset_defers_clinical_fields(self):
        """Acceptance: the receptionist queryset excludes clinical fields —
        they are deferred and never selected from the database."""
        from medicaregp.roles import PATIENT_CLINICAL_FIELDS, reception_patient_queryset
        instance = reception_patient_queryset().get(pk=self.patient.pk)
        deferred = instance.get_deferred_fields()
        for field in PATIENT_CLINICAL_FIELDS:
            self.assertIn(field, deferred, f'{field} was selected for reception')

    def test_reception_patient_page_contains_no_clinical_values(self):
        self.client.force_login(self.receptionist)
        response = self.client.get(reverse('patient_detail', args=[self.patient.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Bonitas')               # medical aid: allowed
        for leaked in ['CLINICAL-ALLERGY', 'CLINICAL-CHRONIC', 'CLINICAL-MED', 'CLINICAL-NOTE']:
            self.assertNotContains(response, leaked)

    def test_reception_form_excludes_clinical_fields(self):
        from medicaregp.roles import PATIENT_CLINICAL_FIELDS
        from patients.forms import ReceptionPatientForm
        form = ReceptionPatientForm()
        for field in PATIENT_CLINICAL_FIELDS:
            self.assertNotIn(field, form.fields)

    def test_reception_post_cannot_write_clinical_fields(self):
        """A crafted POST from reception must not update clinical columns."""
        self.client.force_login(self.receptionist)
        url = reverse('patient_edit', args=[self.patient.pk])
        data = {
            'last_name': 'Khumalo', 'first_name': 'Buhle', 'title': '',
            'date_of_birth': '1992-02-02', 'gender': 'F', 'id_type': 'SA_ID',
            'id_number': '9202025800088', 'phone': '0824445555',
            'allergies': 'INJECTED-BY-RECEPTION',
            'family_members-TOTAL_FORMS': '0', 'family_members-INITIAL_FORMS': '0',
            'family_members-MIN_NUM_FORMS': '0', 'family_members-MAX_NUM_FORMS': '1000',
        }
        self.client.post(url, data)
        self.patient.refresh_from_db()
        self.assertEqual(self.patient.allergies, 'CLINICAL-ALLERGY-Penicillin')

    def test_reception_403_on_clinical_views(self):
        self.client.force_login(self.receptionist)
        consultation = self.patient.consultations.first()
        self.assertEqual(
            self.client.get(reverse('consultation_detail', args=[consultation.pk])).status_code, 403)
        self.assertEqual(
            self.client.get(reverse('vitals_add', args=[self.patient.pk])).status_code, 403)

    def test_reception_print_all_has_no_clinical_data(self):
        """Acceptance: receptionist's print contains no clinical data."""
        self.client.force_login(self.receptionist)
        response = self.client.get(reverse('patient_print_all', args=[self.patient.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'NO CLINICAL DATA')
        for leaked in ['CLINICAL-ALLERGY', 'CLINICAL-CHRONIC', 'CLINICAL-MED', 'CLINICAL-NOTE']:
            self.assertNotContains(response, leaked)


class BiometricCheckinTests(TestCase):
    def setUp(self):
        self.receptionist = User.objects.create_user('reception', password='pw')
        self.receptionist.groups.add(Group.objects.get(name='Reception'))
        self.patient = Patient.objects.create(
            first_name='Lwazi', last_name='Mthembu',
            date_of_birth=date(1985, 5, 5), gender='M',
            id_number='8505055800087', phone='0821119999',
            medical_aid_name='GEMS', medical_aid_plan='Emerald',
            medical_aid_number='GEMS-001', dependant_code='00',
            allergies='CLINICAL-ALLERGY-Sulfa')

    def test_biometric_match_returns_medical_aid_details_only(self):
        """Acceptance: biometric match returns medical-aid details only."""
        from patients.biometrics import get_provider
        get_provider().enrol(self.patient, 'FINGERPRINT-TEMPLATE-XYZ')

        self.client.force_login(self.receptionist)
        response = self.client.post(reverse('biometric_identify'),
                                    {'sample': 'FINGERPRINT-TEMPLATE-XYZ'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'GEMS')
        self.assertContains(response, 'GEMS-001')
        self.assertNotContains(response, 'CLINICAL-ALLERGY')
        # The whitelisted dict is the only patient data in context
        from medicaregp.roles import MEDICAL_AID_FIELDS
        self.assertEqual(set(response.context['match'].keys()), set(MEDICAL_AID_FIELDS))

    def test_no_match_for_unknown_sample(self):
        self.client.force_login(self.receptionist)
        response = self.client.post(reverse('biometric_identify'), {'sample': 'UNKNOWN'})
        self.assertContains(response, 'No enrolled patient matched')

    def test_only_hash_stored(self):
        from patients.biometrics import get_provider
        record = get_provider().enrol(self.patient, 'FINGERPRINT-TEMPLATE-XYZ')
        self.assertNotIn('FINGERPRINT', record.template_hash)
        self.assertEqual(len(record.template_hash), 64)   # sha256 hex


class VisitLimitTests(TestCase):
    def setUp(self):
        from patients.models import MedicalAidPlanConfig
        self.patient = Patient.objects.create(
            first_name='Zanele', last_name='Nkosi',
            date_of_birth=date(1970, 1, 1), gender='F',
            id_number='7001015800085', phone='0820001111',
            medical_aid_name='Bonitas', medical_aid_plan='BonFit')
        MedicalAidPlanConfig.objects.create(
            scheme_name='Bonitas', plan_name='BonFit', visits_per_year=5)  # warn at 4 (80%)

    def _add_visits(self, n):
        for _ in range(n):
            Consultation.objects.create(patient=self.patient)

    def test_visit_warning_triggers_at_threshold(self):
        """Acceptance: visit-limit warning triggers at threshold."""
        from patients.services import visit_usage
        self._add_visits(3)
        self.assertEqual(visit_usage(self.patient)['status'], 'ok')
        self._add_visits(1)   # 4 of 5 = warn threshold
        self.assertEqual(visit_usage(self.patient)['status'], 'warning')
        self._add_visits(1)   # 5 of 5
        self.assertEqual(visit_usage(self.patient)['status'], 'over')

    def test_scheme_wide_default_used_when_no_plan_match(self):
        from patients.models import MedicalAidPlanConfig
        from patients.services import visit_usage
        self.patient.medical_aid_plan = 'UnknownPlan'
        self.patient.save()
        self.assertIsNone(visit_usage(self.patient))
        MedicalAidPlanConfig.objects.create(
            scheme_name='Bonitas', plan_name='', visits_per_year=10)
        usage = visit_usage(self.patient)
        self.assertEqual(usage['limit'], 10)
