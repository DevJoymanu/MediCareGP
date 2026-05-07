from datetime import date, time

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from appointments.models import Appointment
from consultations.models import Consultation
from scripts.models import Document
from patients.models import Patient


class PatientDetailViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='secret123')
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
