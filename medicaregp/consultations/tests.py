from datetime import date, time

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse

from appointments.models import Appointment
from consultations.models import Consultation
from patients.models import Patient


class ConsultationCreateViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='secret123')
        # Consultation views are doctor-only under RBAC (medicaregp/roles.py)
        self.user.groups.add(Group.objects.get(name='Doctor'))
        self.patient = Patient.objects.create(
            first_name='Thabo',
            last_name='Nkosi',
            date_of_birth=date(1988, 8, 12),
            gender='M',
            id_number='8808125678083',
            phone='0830000000',
        )
        self.appointment = Appointment.objects.create(
            patient=self.patient,
            date=date(2026, 4, 9),
            time=time(11, 0),
            reason='Follow-up',
        )

    def test_patient_start_creates_consultation_and_opens_workspace(self):
        self.client.login(username='tester', password='secret123')

        response = self.client.get(reverse('consultation_create') + f'?patient_id={self.patient.pk}')

        consultation = Consultation.objects.get(patient=self.patient)
        self.assertRedirects(response, reverse('diagnosis_workspace', args=[consultation.pk]))

    def test_patient_start_is_idempotent_same_day(self):
        """Double-clicking Start must not create a second consultation."""
        self.client.login(username='tester', password='secret123')
        url = reverse('consultation_create') + f'?patient_id={self.patient.pk}'
        self.client.get(url)
        self.client.get(url)
        self.assertEqual(Consultation.objects.filter(patient=self.patient).count(), 1)

    def test_appointment_start_links_appointment_and_prefills_complaint(self):
        self.client.login(username='tester', password='secret123')
        self.appointment.status = 'Checked In'
        self.appointment.save(update_fields=['status'])

        response = self.client.get(
            reverse('consultation_create') + f'?appointment_id={self.appointment.pk}')

        consultation = Consultation.objects.get(appointment=self.appointment)
        self.assertRedirects(response, reverse('diagnosis_workspace', args=[consultation.pk]))
        self.assertEqual(consultation.patient, self.patient)
        self.assertEqual(consultation.chief_complaint, 'Follow-up')
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, 'With Doctor')

    def test_no_patient_renders_start_picker(self):
        self.client.login(username='tester', password='secret123')
        response = self.client.get(reverse('consultation_create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'New consultation')
        self.assertContains(response, 'Linked Appointment')

    def test_start_vitals_params_stamp_consultation(self):
        self.client.login(username='tester', password='secret123')
        self.client.get(reverse('consultation_create') +
                        f'?patient_id={self.patient.pk}&wt=70.5&bp=118/76')
        consultation = Consultation.objects.get(patient=self.patient)
        self.assertEqual(str(consultation.weight_kg), '70.5')
        self.assertEqual(consultation.bp_reading, '118/76')

    def test_start_carries_forward_last_vitals(self):
        Consultation.objects.create(
            patient=self.patient, weight_kg='81.5', bp_reading='130/85')
        self.client.login(username='tester', password='secret123')

        self.client.get(
            reverse('consultation_create') + f'?appointment_id={self.appointment.pk}')

        consultation = Consultation.objects.get(appointment=self.appointment)
        self.assertEqual(str(consultation.weight_kg), '81.5')
        self.assertEqual(consultation.bp_reading, '130/85')

    def test_post_deletes_consultation(self):
        consultation = Consultation.objects.create(
            patient=self.patient,
            appointment=self.appointment,
            subjective='Pain',
            objective='Stable',
            assessment='Muscle strain',
            plan='Rest',
        )
        self.client.login(username='tester', password='secret123')

        response = self.client.post(reverse('consultation_delete', args=[consultation.pk]))

        self.assertRedirects(response, reverse('consultation_list'))
        self.assertFalse(Consultation.objects.filter(pk=consultation.pk).exists())
