from datetime import date, time

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from patients.models import Patient
from appointments.models import Appointment


class AppointmentCancelViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='secret123')
        self.patient = Patient.objects.create(
            first_name='Nomsa',
            last_name='Dlamini',
            date_of_birth=date(1990, 5, 10),
            gender='F',
            id_number='9005101234088',
            phone='0820000000',
        )
        self.appointment = Appointment.objects.create(
            patient=self.patient,
            date=date(2026, 4, 7),
            time=time(9, 30),
            reason='Routine checkup',
        )

    def test_cancel_requires_post(self):
        self.client.login(username='tester', password='secret123')

        response = self.client.get(reverse('appointment_cancel', args=[self.appointment.pk]))

        self.assertEqual(response.status_code, 200)
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, 'Scheduled')

    def test_post_cancels_appointment(self):
        self.client.login(username='tester', password='secret123')

        response = self.client.post(reverse('appointment_cancel', args=[self.appointment.pk]))

        self.assertRedirects(response, reverse('appointment_detail', args=[self.appointment.pk]))
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, 'Cancelled')

    def test_post_deletes_appointment(self):
        self.client.login(username='tester', password='secret123')

        response = self.client.post(reverse('appointment_delete', args=[self.appointment.pk]))

        self.assertRedirects(response, reverse('appointment_list'))
        self.assertFalse(Appointment.objects.filter(pk=self.appointment.pk).exists())
