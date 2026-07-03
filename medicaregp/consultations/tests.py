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

    def test_patient_query_prefills_form(self):
        self.client.login(username='tester', password='secret123')

        response = self.client.get(reverse('consultation_create') + f'?patient_id={self.patient.pk}')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form'].initial['patient'], self.patient.pk)
        self.assertQuerysetEqual(
            response.context['form'].fields['appointment'].queryset,
            Appointment.objects.filter(patient=self.patient).order_by('-date', '-time'),
            transform=lambda x: x,
        )

    def test_appointment_query_prefills_patient_and_appointment(self):
        self.client.login(username='tester', password='secret123')

        response = self.client.get(reverse('consultation_create') + f'?appointment_id={self.appointment.pk}')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form'].initial['patient'], self.patient.pk)
        self.assertEqual(response.context['form'].initial['appointment'], self.appointment.pk)

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
