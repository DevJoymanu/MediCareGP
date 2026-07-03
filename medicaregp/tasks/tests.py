from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from tasks.models import Task


class DashboardTaskTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='secret123')
        self.task = Task.objects.create(
            title='Prepare referral notes',
            due_date=date(2026, 5, 2),
            priority='High',
        )

    def test_dashboard_can_mark_priority_task_complete(self):
        self.client.login(username='tester', password='secret123')

        response = self.client.post(
            reverse('dashboard'),
            {'action': 'toggle_task', 'task_id': self.task.pk},
        )

        self.assertRedirects(response, reverse('dashboard'))
        self.task.refresh_from_db()
        self.assertTrue(self.task.done)
