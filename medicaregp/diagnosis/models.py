"""
Knowledge base + audit trail for the deterministic provisional-diagnosis
engine (see diagnosis/engine.py for the scoring rules).

Everything here is admin-editable: conditions, symptoms, the weighted
symptom→condition links, and the explicit history-modifier rules. Tuning the
knowledge base never requires a redeploy.
"""
from django.conf import settings
from django.db import models

from consultations.models import Consultation
from patients.models import Patient


class Condition(models.Model):
    """A diagnosable condition, always carrying its ICD-10 code."""
    name        = models.CharField(max_length=200, unique=True)
    icd10_code  = models.CharField(max_length=10, verbose_name='ICD-10 code')
    description = models.TextField(blank=True, null=True)
    active      = models.BooleanField(default=True, help_text='Inactive conditions are excluded from scoring.')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.icd10_code})'


class Symptom(models.Model):
    """A symptom or clinical sign the doctor can select during capture."""
    KIND_CHOICES = [
        ('symptom', 'Symptom (reported)'),
        ('sign',    'Sign (observed)'),
    ]
    BODY_REGION_CHOICES = [
        ('head',    'Head & face'),
        ('throat',  'Throat & neck'),
        ('chest',   'Chest & respiratory'),
        ('abdomen', 'Abdomen & digestive'),
        ('pelvis',  'Pelvis & urinary'),
        ('limbs',   'Limbs, joints & back'),
        ('skin',    'Skin'),
        ('mental',  'Mood & sleep'),
        ('general', 'General / systemic'),
    ]
    name        = models.CharField(max_length=200, unique=True)
    kind        = models.CharField(max_length=10, choices=KIND_CHOICES, default='symptom')
    body_region = models.CharField(max_length=10, choices=BODY_REGION_CHOICES, default='general',
                                   help_text='Region used by the body-map picker in the consultation workspace.')
    synonyms = models.CharField(max_length=300, blank=True, null=True,
                                help_text='Comma-separated alternates, e.g. "pyrexia, high temperature"')
    active   = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class SymptomConditionLink(models.Model):
    """Weighted association: how strongly a symptom points at a condition.

    Weight scale 1–10 (10 = near-pathognomonic, 1 = weak association).
    """
    symptom   = models.ForeignKey(Symptom, on_delete=models.CASCADE, related_name='condition_links')
    condition = models.ForeignKey(Condition, on_delete=models.CASCADE, related_name='symptom_links')
    weight    = models.PositiveSmallIntegerField(default=5, help_text='1 (weak) – 10 (near-pathognomonic)')
    note      = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        unique_together = [('symptom', 'condition')]
        ordering = ['condition__name', '-weight']

    def __str__(self):
        return f'{self.symptom} → {self.condition} (w={self.weight})'


class HistoryModifierRule(models.Model):
    """Explicit rule that raises or lowers a condition's score based on the
    patient's stored history/demographics. Positive delta = confirming
    factor, negative delta = contradicting factor. All rules that match are
    applied; nothing is implicit.
    """
    FACTOR_CHOICES = [
        ('age_band',      'Age band (match value "min-max" years, e.g. "0-5" or "50-120")'),
        ('sex',           'Sex (match value "M", "F" or "O")'),
        ('chronic',       'Chronic condition on file (substring match, e.g. "diabetes")'),
        ('prior_episode', 'Prior episode of this condition (match value ignored)'),
        ('smoking',       'Smoking status (match value "Current" / "Former" / "Never")'),
        ('alcohol',       'Alcohol use (match value "Heavy" / "Moderate" / "Occasional" / "None")'),
    ]
    condition   = models.ForeignKey(Condition, on_delete=models.CASCADE, related_name='history_rules')
    factor      = models.CharField(max_length=20, choices=FACTOR_CHOICES)
    match_value = models.CharField(max_length=100, blank=True, default='',
                                   help_text='What the factor must equal/contain — see factor choices.')
    delta       = models.SmallIntegerField(help_text='Score points added (confirming) or subtracted (contradicting).')
    note        = models.CharField(max_length=200, blank=True, null=True,
                                   help_text='Shown to the doctor as the plain-language "why".')
    active      = models.BooleanField(default=True)

    class Meta:
        ordering = ['condition__name', 'factor']

    def __str__(self):
        sign = '+' if self.delta >= 0 else ''
        return f'{self.condition.name}: {self.factor}={self.match_value} → {sign}{self.delta}'


class DifferentialResult(models.Model):
    """Audit record of one engine run: exact inputs + ranked output.

    Stored so results are reproducible, reviewable, and so first-occurrence
    checks can consult structured prior symptom captures.
    """
    consultation   = models.ForeignKey(Consultation, on_delete=models.CASCADE, related_name='differential_results')
    patient        = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='differential_results')
    created_at     = models.DateTimeField(auto_now_add=True)
    created_by     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    engine_version = models.CharField(max_length=10)
    inputs         = models.JSONField(help_text='Exact engine inputs: presenting/working symptom ids, free-text notes, history snapshot.')
    output         = models.JSONField(help_text='Ranked provisional-diagnosis list with full score breakdowns.')

    # Frozen-snapshot confirmation: set once when the doctor confirms their
    # provisional dx from this run. The consultation-details view renders THIS
    # stored output, never a fresh run — the knowledge base is admin-editable,
    # so re-computing later could silently show different numbers than the
    # doctor saw (medico-legal problem).
    confirmed_at = models.DateTimeField(null=True, blank=True)
    confirmed_dx = models.JSONField(null=True, blank=True,
                                    help_text='Diagnoses the doctor promoted & confirmed: '
                                              '[{"code", "name", "source": "engine"|"manual"}].')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Provisional diagnosis run — {self.patient} @ {self.created_at:%Y-%m-%d %H:%M}'
