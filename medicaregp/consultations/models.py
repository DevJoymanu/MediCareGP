import uuid
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


class Provider(models.Model):
    """A lab or radiology practice the doctor refers to. Set up once, reused on requests."""
    KIND_CHOICES = [
        ('lab',       'Laboratory'),
        ('radiology', 'Radiology'),
        ('both',      'Both'),
    ]
    name        = models.CharField(max_length=200)
    kind        = models.CharField(max_length=10, choices=KIND_CHOICES, default='radiology')
    practice_no = models.CharField(max_length=50, blank=True, verbose_name='Practice number')
    email       = models.EmailField(blank=True, help_text='Where the results link / report is sent')
    phone       = models.CharField(max_length=40, blank=True)
    address     = models.TextField(blank=True)
    is_active   = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class InvestigationRequest(models.Model):
    """
    A single lab/radiology order tied to a consultation. Holds the whole lifecycle:
    request → provider submission (or doctor's manual entry) → doctor review (confirm/decline).
    """
    KIND_CHOICES = [
        ('lab',       'Laboratory'),
        ('radiology', 'Radiology'),
    ]
    STATUS_CHOICES = [
        ('sent',      'Awaiting results'),
        ('submitted', 'Submitted — awaiting review'),
        ('confirmed', 'Confirmed & filed'),
        ('declined',  'Declined'),
    ]
    DELIVER_CHOICES = [
        ('rooms',   'Deliver to rooms'),
        ('ward',    'Hospital ward'),
        ('patient', 'Give to patient'),
    ]

    consultation    = models.ForeignKey(Consultation, on_delete=models.CASCADE, related_name='investigation_requests')
    kind            = models.CharField(max_length=10, choices=KIND_CHOICES)
    requested_items = models.TextField(blank=True, verbose_name='Requested items', help_text='One exam/test per line')
    history         = models.TextField(blank=True, verbose_name='Clinical history')
    nappi_code      = models.CharField(max_length=50, blank=True, verbose_name='Nappi code')
    deliver_to      = models.CharField(max_length=10, choices=DELIVER_CHOICES, default='rooms')

    provider        = models.ForeignKey('Provider', on_delete=models.SET_NULL, null=True, blank=True, related_name='requests')
    provider_name   = models.CharField(max_length=200, blank=True, help_text='Used if no saved provider is selected')
    provider_email  = models.EmailField(blank=True)

    token           = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)
    status          = models.CharField(max_length=10, choices=STATUS_CHOICES, default='sent')

    # ── Provider submission (or doctor's manual entry) ────────────────────────
    result_text     = models.TextField(blank=True)
    result_file     = models.FileField(upload_to='investigation_results/%Y/%m/', blank=True, null=True)
    submitted_by    = models.CharField(max_length=200, blank=True, verbose_name='Submitted by')
    provider_note   = models.TextField(blank=True)
    decline_reason  = models.CharField(max_length=255, blank=True)
    honeypot        = models.CharField(max_length=100, blank=True)   # spam trap

    created_at      = models.DateTimeField(auto_now_add=True)
    submitted_at    = models.DateTimeField(null=True, blank=True)
    reviewed_at     = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = [('consultation', 'kind')]

    def __str__(self):
        return f"{self.get_kind_display()} request — {self.consultation.patient} ({self.get_status_display()})"

    @property
    def recipient_name(self):
        if self.provider:
            return self.provider.name
        return self.provider_name

    @property
    def recipient_email(self):
        if self.provider and self.provider.email:
            return self.provider.email
        return self.provider_email

    @property
    def result_filename(self):
        import os
        return os.path.basename(self.result_file.name) if self.result_file else ''

    @property
    def requested_items_list(self):
        return [line.strip() for line in (self.requested_items or '').splitlines() if line.strip()]
