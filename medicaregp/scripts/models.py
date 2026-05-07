from django.db import models
from patients.models import Patient


class Document(models.Model):
    CATEGORY_CHOICES = [
        ('Clinical',       'Clinical Documents'),
        ('Administrative', 'Administrative Documents'),
        ('Compliance',     'Compliance & Legal Documents'),
    ]
    DOC_TYPES = [
        ('Consultation Note',        'Consultation Note'),
        ('Patient Medical History',  'Patient Medical History'),
        ('Referral Letter',          'Referral Letter'),
        ('Lab Request Form',         'Lab / Blood Test Request'),
        ('Radiology Request Form',   'Radiology Request (X-ray / Ultrasound)'),
        ('Lab Result',               'Lab Result'),
        ('Consent Form',             'Consent Form'),
        ('POPIA Consent',            'POPIA Consent Form'),
        ('Prescription',             'Prescription'),
        ('Sick Note',                'Sick / Medical Certificate'),
        ('Motivation Letter',        'Motivation Letter (Pre-authorisation)'),
        ('Claim Form',               'Medical Aid Claim Form'),
        ('Patient Intake Form',      'Patient Intake Form'),
        ('Vaccination Record',       'Vaccination Record'),
        ('Billing Statement',        'Billing Statement'),
        ('Practice Policy',          'Practice Policy'),
        ('Audit Log',                'Audit Log'),
        ('Record Retention Policy',  'Record Retention Policy'),
        ('Incident Report',          'Incident Report'),
    ]
    patient     = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='documents')
    category    = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='Clinical')
    doc_type    = models.CharField(max_length=40, choices=DOC_TYPES)
    content     = models.TextField(blank=True)
    attachment  = models.FileField(upload_to='documents/%Y/%m/', blank=True, null=True)
    date_issued = models.DateField(auto_now_add=True)
    issued_by   = models.CharField(max_length=100, default='Dr. Sarah Malan')
    notes       = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.doc_type} - {self.patient} ({self.date_issued})"

    class Meta:
        ordering = ['-date_issued']
