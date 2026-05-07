from django.db import models
from django.utils import timezone


class Patient(models.Model):
    GENDER_CHOICES = [('M', 'Male'), ('F', 'Female'), ('O', 'Other')]
    BLOOD_TYPE_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-'),
    ]
    ID_TYPE_CHOICES = [
        ('SA_ID',    'South African ID'),
        ('Passport', 'Passport Number'),
    ]
    SMOKING_CHOICES = [
        ('Never',   'Never'),
        ('Former',  'Former smoker'),
        ('Current', 'Current smoker'),
    ]
    ALCOHOL_CHOICES = [
        ('None',       'None'),
        ('Occasional', 'Occasional'),
        ('Moderate',   'Moderate'),
        ('Heavy',      'Heavy'),
    ]

    # ── Personal ──────────────────────────────────────────────────────────────
    first_name      = models.CharField(max_length=100)
    last_name       = models.CharField(max_length=100)
    date_of_birth   = models.DateField()
    gender          = models.CharField(max_length=1, choices=GENDER_CHOICES)
    id_type         = models.CharField(max_length=10, choices=ID_TYPE_CHOICES, default='SA_ID')
    id_number       = models.CharField(max_length=30, unique=True)
    file_number     = models.CharField(max_length=20, blank=True, null=True, unique=True)

    # ── Contact ───────────────────────────────────────────────────────────────
    phone           = models.CharField(max_length=20)
    alt_phone       = models.CharField(max_length=20, blank=True, null=True, verbose_name='Alt. phone (home/work)')
    email           = models.EmailField(blank=True, null=True)
    address         = models.TextField(blank=True, null=True, verbose_name='Residential address')

    # ── Next of kin ──────────────────────────────────────────────────────────
    next_of_kin_name  = models.CharField(max_length=150, blank=True, null=True, verbose_name='Next of kin name')
    next_of_kin_phone = models.CharField(max_length=20,  blank=True, null=True, verbose_name='Next of kin phone')

    # ── Medical aid ───────────────────────────────────────────────────────────
    medical_aid_name      = models.CharField(max_length=100, blank=True, null=True, verbose_name='Medical aid scheme')
    medical_aid_plan      = models.CharField(max_length=100, blank=True, null=True, verbose_name='Plan / option')
    medical_aid_number    = models.CharField(max_length=50,  blank=True, null=True, verbose_name='Membership number')
    principal_member_name = models.CharField(max_length=150, blank=True, null=True)
    principal_member_id   = models.CharField(max_length=30,  blank=True, null=True, verbose_name='Principal member ID')
    dependant_code        = models.CharField(max_length=10,  blank=True, null=True)

    # ── Clinical ──────────────────────────────────────────────────────────────
    blood_type            = models.CharField(max_length=5, choices=BLOOD_TYPE_CHOICES, blank=True, null=True)
    allergies             = models.TextField(blank=True, null=True, help_text='Comma-separated (e.g. Penicillin, Sulfa drugs)')
    chronic_conditions    = models.TextField(blank=True, null=True, help_text='Comma-separated (e.g. Hypertension, Diabetes)')
    current_medication    = models.TextField(blank=True, null=True, help_text='List current chronic medication and dosages')
    previous_surgeries    = models.TextField(blank=True, null=True, help_text='Previous surgeries or hospitalisations with approximate dates')
    family_history        = models.TextField(blank=True, null=True, help_text='Relevant family medical history')

    # ── Lifestyle ─────────────────────────────────────────────────────────────
    smoking_status  = models.CharField(max_length=10, choices=SMOKING_CHOICES, blank=True, null=True)
    alcohol_use     = models.CharField(max_length=12, choices=ALCOHOL_CHOICES, blank=True, null=True)
    substance_use   = models.TextField(blank=True, null=True, help_text='Any other substance use (optional)')

    # ── Consent ───────────────────────────────────────────────────────────────
    popia_consent   = models.BooleanField(default=False, verbose_name='POPIA consent given')
    consent_to_treat= models.BooleanField(default=False, verbose_name='Consent to treat given')

    # ── Admin ─────────────────────────────────────────────────────────────────
    date_registered = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def allergies_list(self):
        if not self.allergies:
            return []
        return [a.strip() for a in self.allergies.split(',') if a.strip()]

    def chronic_list(self):
        if not self.chronic_conditions:
            return []
        return [c.strip() for c in self.chronic_conditions.split(',') if c.strip()]

    def get_age(self):
        today = timezone.now().date()
        dob = self.date_of_birth
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.file_number:
            self.file_number = f'GP-{self.pk:04d}'
            Patient.objects.filter(pk=self.pk).update(file_number=self.file_number)

    class Meta:
        ordering = ['last_name', 'first_name']


class Vitals(models.Model):
    patient           = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='vitals')
    date              = models.DateField()
    blood_pressure    = models.CharField(max_length=10, blank=True, null=True, help_text='e.g. 120/80')
    bp_systolic       = models.IntegerField(blank=True, null=True)
    bp_diastolic      = models.IntegerField(blank=True, null=True)
    pulse             = models.IntegerField(blank=True, null=True, help_text='bpm')
    weight            = models.DecimalField(max_digits=5, decimal_places=1, blank=True, null=True, help_text='kg')
    height            = models.IntegerField(blank=True, null=True, help_text='cm')
    temperature       = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True, help_text='°C')
    oxygen_saturation = models.IntegerField(blank=True, null=True, help_text='%')
    blood_glucose     = models.DecimalField(max_digits=5, decimal_places=1, blank=True, null=True, help_text='mmol/L')
    recorded_by       = models.CharField(max_length=100, default='Dr. Sarah Malan')

    def bmi(self):
        if self.weight and self.height:
            h_m = self.height / 100
            return round(float(self.weight) / (h_m ** 2), 1)
        return None

    def __str__(self):
        return f"{self.patient} vitals — {self.date}"

    class Meta:
        ordering = ['-date']
