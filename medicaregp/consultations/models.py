from django.db import models
from patients.models import Patient
from appointments.models import Appointment


class Consultation(models.Model):
    patient     = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='consultations')
    appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, blank=True, related_name='consultations')
    date        = models.DateField(auto_now_add=True)

    # ── Visit vitals (quick capture) ──────────────────────────────────────────
    weight_kg                = models.DecimalField(max_digits=5, decimal_places=1, blank=True, null=True, verbose_name='Weight (kg)')
    bp_reading               = models.CharField(max_length=10, blank=True, null=True, verbose_name='BP (e.g. 120/80)')

    # ── Clinical notes ────────────────────────────────────────────────────────
    chief_complaint          = models.TextField(blank=True, null=True, verbose_name='Reason for visit')
    subjective               = models.TextField(blank=True, null=True, verbose_name='Clinical Notes')
    objective                = models.TextField(blank=True, null=True, verbose_name='O — Objective (Examination findings)')
    assessment               = models.TextField(blank=True, null=True, verbose_name='Assessment / Diagnosis')
    differential_diagnosis   = models.TextField(blank=True, null=True, verbose_name='Differential diagnosis')
    plan                     = models.TextField(blank=True, null=True, verbose_name='P — Plan (Treatment)')

    # ── Coding & referrals ────────────────────────────────────────────────────
    icd10_code               = models.CharField(max_length=20, blank=True, null=True, verbose_name='ICD-10 code')
    referral_to              = models.CharField(max_length=200, blank=True, null=True, verbose_name='Referral to (specialist / facility)')
    referral_reason          = models.TextField(blank=True, null=True)

    # ── Prescriptions & follow-up ─────────────────────────────────────────────
    prescriptions            = models.TextField(blank=True, null=True)
    follow_up_date           = models.DateField(blank=True, null=True)

    # ── Sick note ─────────────────────────────────────────────────────────────
    sick_note_issued         = models.BooleanField(default=False)
    sick_note_days           = models.PositiveIntegerField(blank=True, null=True, verbose_name='Sick note (days)')
    sick_note_start_date     = models.DateField(blank=True, null=True)
    sick_note_employer       = models.CharField(max_length=200, blank=True, null=True)

    # ── Lab / radiology requests ──────────────────────────────────────────────
    lab_requests             = models.TextField(blank=True, null=True, verbose_name='Lab / blood test requests', help_text='One per line')
    radiology_requests       = models.TextField(blank=True, null=True, verbose_name='Radiology requests (X-ray, ultrasound, etc.)', help_text='One per line')

    def __str__(self):
        return f"{self.patient} - {self.date}"

    class Meta:
        ordering = ['-date']
