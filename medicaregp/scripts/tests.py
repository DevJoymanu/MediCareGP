from datetime import date

from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from patients.models import Patient
from scripts.forms import DocumentForm
from scripts.models import Document


class DocumentFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='secret123')
        self.patient = Patient.objects.create(
            first_name='Sizwe',
            last_name='Naidoo',
            date_of_birth=date(1985, 3, 14),
            gender='M',
            id_number='8503141234082',
            phone='0821111111',
        )

    def test_document_requires_content_or_attachment(self):
        form = DocumentForm(data={
            'patient': self.patient.pk,
            'category': 'Clinical',
            'doc_type': 'Lab Result',
            'content': '',
            'issued_by': 'Dr. Tamuka Chivonivoni',
        })

        self.assertFalse(form.is_valid())
        self.assertIn('Add document content or upload an attachment.', form.non_field_errors())

    def test_document_accepts_attachment_without_content(self):
        upload = SimpleUploadedFile('lab-result.txt', b'cholesterol panel')
        form = DocumentForm(
            data={
                'patient': self.patient.pk,
                'category': 'Clinical',
                'doc_type': 'Lab Result',
                'content': '',
                'issued_by': 'Dr. Tamuka Chivonivoni',
            },
            files={'attachment': upload},
        )

        self.assertTrue(form.is_valid(), form.errors)

    def test_document_edit_updates_record(self):
        document = Document.objects.create(
            patient=self.patient,
            category='Clinical',
            doc_type='Referral Letter',
            content='Initial content',
        )
        self.client.login(username='tester', password='secret123')

        response = self.client.post(reverse('document_edit', args=[document.pk]), data={
            'patient': self.patient.pk,
            'category': 'Administrative',
            'doc_type': 'Billing Statement',
            'content': 'Updated statement',
            'issued_by': 'Dr. Tamuka Chivonivoni',
        })

        self.assertRedirects(response, reverse('document_detail', args=[document.pk]))
        document.refresh_from_db()
        self.assertEqual(document.category, 'Administrative')
        self.assertEqual(document.doc_type, 'Billing Statement')

    def test_document_delete_removes_record(self):
        document = Document.objects.create(
            patient=self.patient,
            category='Compliance',
            doc_type='Incident Report',
            content='Report text',
        )
        self.client.login(username='tester', password='secret123')

        response = self.client.post(reverse('document_delete', args=[document.pk]))

        self.assertRedirects(response, reverse('document_list'))
        self.assertFalse(Document.objects.filter(pk=document.pk).exists())
