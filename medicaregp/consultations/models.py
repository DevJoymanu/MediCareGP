from django.db import models
from patients.models import Patient
from appointments.models import Appointment


class Consultation(models.Model):
    patient               = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='consultations')
    appointment           = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, blank=True, related_name='consultations')
    date                  = models.DateField(auto_now_add=True)
    reviewed_consultation = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews', verbose_name='Review of')

    # ── Visit vitals (quick capture) ──────────────────────────────────────────
    weight_kg                = models.DecimalField(max_digits=5, decimal_places=1, blank=True, null=True, verbose_name='Weight (kg)')
    bp_reading               = models.CharField(max_length=10, blank=True, null=True, verbose_name='BP (e.g. 120/80)')

    # ── Clinical notes ────────────────────────────────────────────────────────
    chief_complaint          = models.TextField(blank=True, null=True, verbose_name='Reason for visit')
    review                   = models.TextField(blank=True, null=True, verbose_name='Review', help_text='Progress since last visit — current treatment response, adherence, concerns')
    subjective               = models.TextField(blank=True, null=True, verbose_name='Clinical Notes')
    objective                = models.TextField(blank=True, null=True, verbose_name='O — Objective (Examination findings)')
    assessment               = models.TextField(blank=True, null=True, verbose_name='Assessment / Diagnosis')
    differential_diagnosis   = models.TextField(blank=True, null=True, verbose_name='Differential diagnosis')
    plan                     = models.TextField(blank=True, null=True, verbose_name='P — Plan (Treatment)')

    # ── Coding & referrals ────────────────────────────────────────────────────
    icd10_code               = models.TextField(blank=True, null=True, verbose_name='ICD-10 code(s)')
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

    @property
    def icd10_codes_list(self):
        """Return list of {code, description} dicts. Handles old single-code strings."""
        import json
        if not self.icd10_code:
            return []
        try:
            parsed = json.loads(self.icd10_code)
            if isinstance(parsed, list):
                return parsed
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
        # Legacy: plain code string like "J06.9"
        return [{'code': self.icd10_code, 'description': self.icd10_code}]

    def __str__(self):
        return f"{self.patient} - {self.date}"

    class Meta:
        ordering = ['-date']


class ConditionPrescriptionLink(models.Model):
    """
    Tally of how often a condition is paired with a prescription.
    Pre-seeded from SA Standard Treatment Guidelines.
    Grows as the doctor uses the system.
    """
    condition    = models.CharField(max_length=200, db_index=True)
    prescription = models.CharField(max_length=500)
    count        = models.IntegerField(default=1)
    is_seeded    = models.BooleanField(default=False)
    last_seen    = models.DateField(auto_now=True)

    class Meta:
        unique_together = [('condition', 'prescription')]
        ordering        = ['-count']

    def __str__(self):
        return f"{self.condition} → {self.prescription[:60]} ({self.count})"
