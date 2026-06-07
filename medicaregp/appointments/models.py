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
    title                = models.CharField(max_length=10, blank=True)
    email                = models.EmailField(blank=True)
    alt_phone            = models.CharField(max_length=20, blank=True)
    occupation           = models.CharField(max_length=100, blank=True)
    home_language        = models.CharField(max_length=50, blank=True)
    marital_status       = models.CharField(max_length=10, blank=True)
    employer             = models.CharField(max_length=150, blank=True)
    work_phone           = models.CharField(max_length=20, blank=True)
    address              = models.TextField(blank=True)
    residential_code     = models.CharField(max_length=10, blank=True)
    postal_address       = models.TextField(blank=True)
    postal_code          = models.CharField(max_length=10, blank=True)
    responsible_surname  = models.CharField(max_length=100, blank=True)
    responsible_first_name = models.CharField(max_length=100, blank=True)
    responsible_title    = models.CharField(max_length=10, blank=True)
    responsible_id_number = models.CharField(max_length=30, blank=True)
    responsible_email    = models.EmailField(blank=True)
    responsible_tel_h    = models.CharField(max_length=20, blank=True)
    responsible_tel_w    = models.CharField(max_length=20, blank=True)
    responsible_cell     = models.CharField(max_length=20, blank=True)
    work_address         = models.TextField(blank=True)
    work_code            = models.CharField(max_length=10, blank=True)
    blood_type           = models.CharField(max_length=5, blank=True)
    medical_aid_name     = models.CharField(max_length=100, blank=True)
    medical_aid_plan     = models.CharField(max_length=100, blank=True)
    medical_aid_number   = models.CharField(max_length=50, blank=True)
    principal_member_name = models.CharField(max_length=150, blank=True)
    principal_member_id  = models.CharField(max_length=30, blank=True)
    dependant_code       = models.CharField(max_length=10, blank=True)
    allergies            = models.TextField(blank=True)
    chronic_conditions   = models.TextField(blank=True)
    current_medication   = models.TextField(blank=True)
    previous_surgeries   = models.TextField(blank=True)
    family_history       = models.TextField(blank=True)
    smoking_status       = models.CharField(max_length=10, blank=True)
    alcohol_use          = models.CharField(max_length=12, blank=True)
    substance_use        = models.TextField(blank=True)
    next_of_kin_name     = models.CharField(max_length=150, blank=True)
    next_of_kin_relationship = models.CharField(max_length=50, blank=True)
    next_of_kin_address  = models.TextField(blank=True)
    next_of_kin_phone    = models.CharField(max_length=20, blank=True)
    next_of_kin_email    = models.EmailField(blank=True)
    referred_by_name     = models.CharField(max_length=150, blank=True)
    referred_by_phone    = models.CharField(max_length=20, blank=True)
    referred_by_email    = models.EmailField(blank=True)
    consent_to_treat     = models.BooleanField(default=False)
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


class WebBooking(models.Model):
    """
    An appointment request placed through the public patient website (Medical-Flow).

    The website collects only the basics (name, phone, email, service, a date and
    a specific time slot). A booking is NOT yet a real Appointment — it lands in
    the reception "Web bookings" queue where staff match/create the Patient and
    confirm the time, then convert it into an Appointment. There is no payment:
    everything is settled with the patient directly.
    """
    STATUS_CHOICES = [
        ('requested', 'Requested — awaiting confirmation'),
        ('converted', 'Converted to appointment'),
        ('cancelled', 'Cancelled'),
    ]

    # Statuses that need reception action (confirm/convert into an appointment).
    ACTION_STATUSES = ['requested']

    reference          = models.CharField(max_length=40, unique=True)
    name               = models.CharField(max_length=200)
    phone              = models.CharField(max_length=30)
    email              = models.EmailField(blank=True)
    appointment_type   = models.CharField(max_length=100)
    appointment_date   = models.DateField()
    appointment_time   = models.TimeField(null=True, blank=True)   # specific slot the patient chose
    time_slot          = models.CharField(max_length=100)          # human label, e.g. "09:30"
    status             = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested')

    # ── Honeypot / anti-spam ──────────────────────────────────────────────────
    honeypot           = models.CharField(max_length=100, blank=True)

    # ── CRM linkage (filled when reception confirms the booking) ──────────────
    matched_patient     = models.ForeignKey(Patient, on_delete=models.SET_NULL, null=True, blank=True,
                                            related_name='web_bookings')
    created_appointment = models.OneToOneField(Appointment, on_delete=models.SET_NULL, null=True, blank=True,
                                               related_name='web_booking')
    reviewed_at         = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.reference} — {self.name} ({self.get_status_display()})"

    @property
    def minutes_ago(self):
        delta = timezone.now() - self.created_at
        return max(0, int(delta.total_seconds() // 60))


class VideoRoom(models.Model):
    """
    A 1:1 WebRTC video-consultation room tied to an appointment. The browsers
    talk peer-to-peer; Django only relays the WebRTC handshake (see VideoSignal).
    The doctor joins from the CRM (login required); the patient joins via the
    unguessable `patient_token` link — no login.
    """
    appointment   = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='video_room')
    room_id       = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    patient_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at    = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"VideoRoom {self.room_id} (appt {self.appointment_id})"


class VideoSignal(models.Model):
    """
    One WebRTC signaling message (offer / answer / ICE candidate / bye), relayed
    between the two peers. Each peer polls for messages from the *other* role.
    Short-lived — old rows are pruned opportunistically.
    """
    ROLE_CHOICES = [('doctor', 'doctor'), ('patient', 'patient')]

    room       = models.ForeignKey(VideoRoom, on_delete=models.CASCADE, related_name='signals')
    role       = models.CharField(max_length=8, choices=ROLE_CHOICES)
    kind       = models.CharField(max_length=12)   # offer | answer | ice | bye
    payload    = models.TextField()                # JSON string
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']
