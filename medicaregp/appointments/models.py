from django.db import models
from patients.models import Patient


class Appointment(models.Model):
    STATUS_CHOICES = [
        ('Scheduled', 'Scheduled'),
        ('Completed',  'Completed'),
        ('Cancelled',  'Cancelled'),
        ('No-Show',    'No-Show'),
    ]

    patient              = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    date                 = models.DateField()
    time                 = models.TimeField()
    reason               = models.CharField(max_length=255)
    status               = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Scheduled')
    notes                = models.TextField(blank=True, null=True)

    # ── Reception / admin ─────────────────────────────────────────────────────
    referring_doctor     = models.CharField(max_length=200, blank=True, null=True, verbose_name='Referring doctor')
    authorization_number = models.CharField(max_length=100, blank=True, null=True, verbose_name='Auth. number (medical aid)')
    icd10_code           = models.CharField(max_length=20,  blank=True, null=True, verbose_name='ICD-10 code')

    def __str__(self):
        return f"{self.patient} - {self.date}"

    class Meta:
        ordering = ['date', 'time']
