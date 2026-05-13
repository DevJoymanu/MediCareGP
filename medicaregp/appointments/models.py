import uuid
from django.db import models
from django.utils import timezone
from datetime import timedelta
from patients.models import Patient


class Appointment(models.Model):
    STATUS_CHOICES = [
        ('Scheduled',    'Scheduled'),
        ('Checked In',   'Checked In'),
        ('With Doctor',  'With Doctor'),
        ('Completed',    'Completed'),
        ('Cancelled',    'Cancelled'),
        ('No-Show',      'No-Show'),
    ]

    VISIT_TYPE_CHOICES = [
        ('Scheduled', 'Scheduled'),
        ('Walk-In',   'Walk-In'),
    ]

    patient              = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    date                 = models.DateField()
    time                 = models.TimeField()
    reason               = models.CharField(max_length=255)
    status               = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Scheduled')
    visit_type           = models.CharField(max_length=20, choices=VISIT_TYPE_CHOICES, default='Scheduled')
    notes                = models.TextField(blank=True, null=True)

    # ── Reception / admin ─────────────────────────────────────────────────────
    referring_doctor     = models.CharField(max_length=200, blank=True, null=True, verbose_name='Referring doctor')
    authorization_number = models.CharField(max_length=100, blank=True, null=True, verbose_name='Auth. number (medical aid)')
    icd10_code           = models.CharField(max_length=20,  blank=True, null=True, verbose_name='ICD-10 code')

    def __str__(self):
        return f"{self.patient} - {self.date}"

    class Meta:
        ordering = ['date', 'time']


class PendingReview(models.Model):
    STATUS_CHOICES = [
        ('pending',      'Pending Arrival'),
        ('self_arrived', 'Self Check-In Confirmed'),
        ('queued',       'Added to Queue'),
        ('moved',        'Moved to Another Date'),
        ('declined',     'Declined'),
        ('completed',    'Review Completed'),
    ]
    consultation     = models.ForeignKey('consultations.Consultation', on_delete=models.CASCADE, related_name='pending_reviews')
    date             = models.DateField()
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes            = models.TextField(blank=True, null=True)
    rescheduled_date = models.DateField(blank=True, null=True)
    appointment      = models.OneToOneField('Appointment', on_delete=models.SET_NULL, null=True, blank=True, related_name='pending_review')
    created_at       = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        unique_together = [('consultation', 'date')]

    def __str__(self):
        return f"Review — {self.consultation.patient} on {self.date}"


class CheckInRequest(models.Model):
    STATUS_CHOICES = [
        ('pending',  'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('expired',  'Expired'),
    ]
    GENDER_CHOICES = [('M', 'Male'), ('F', 'Female'), ('O', 'Other')]

    # ── Phase 1 fields (always collected) ────────────────────────────────────
    id_number        = models.CharField(max_length=30)
    reason_for_visit = models.TextField()
    is_new_patient   = models.BooleanField(default=False)

    # ── Phase 1 — new patient basic info ─────────────────────────────────────
    first_name    = models.CharField(max_length=100, blank=True)
    last_name     = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    phone_number  = models.CharField(max_length=20, blank=True)
    gender        = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    popia_consent = models.BooleanField(default=False)

    # ── Phase 2 — extended profile (filled while waiting) ────────────────────
    address              = models.TextField(blank=True)
    blood_type           = models.CharField(max_length=5, blank=True)
    medical_aid_name     = models.CharField(max_length=100, blank=True)
    medical_aid_number   = models.CharField(max_length=50, blank=True)
    allergies            = models.TextField(blank=True)
    chronic_conditions   = models.TextField(blank=True)
    next_of_kin_name     = models.CharField(max_length=150, blank=True)
    next_of_kin_phone    = models.CharField(max_length=20, blank=True)
    phase2_completed     = models.BooleanField(default=False)
    phase2_token         = models.UUIDField(default=uuid.uuid4, unique=True)

    # ── Status & linking ─────────────────────────────────────────────────────
    status  = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    patient = models.ForeignKey(Patient, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='checkin_requests')

    # ── Security ─────────────────────────────────────────────────────────────
    ip_address  = models.GenericIPAddressField(blank=True, null=True)
    latitude    = models.FloatField(blank=True, null=True)
    longitude   = models.FloatField(blank=True, null=True)
    daily_token = models.CharField(max_length=64)
    honeypot    = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.display_name} — {self.status} — {self.created_at:%Y-%m-%d %H:%M}"

    @property
    def display_name(self):
        if self.patient:
            return str(self.patient)
        name = f"{self.first_name} {self.last_name}".strip()
        return name or self.id_number

    @property
    def is_expired(self):
        return self.created_at < timezone.now() - timedelta(hours=2)

    @property
    def minutes_ago(self):
        delta = timezone.now() - self.created_at
        return max(0, int(delta.total_seconds() // 60))
