"""Front-office services: visit counting against medical-aid plan limits.

Non-clinical: counts consultations as "visits" but never touches their
content — reception only ever sees the numbers.
"""
from django.utils import timezone

from .models import MedicalAidPlanConfig, Patient


def plan_config_for(patient):
    """Best-match plan config: exact scheme+plan first, then the scheme-wide
    default (blank plan_name). None if the patient has no medical aid or no
    config exists."""
    if not patient.medical_aid_name:
        return None
    qs = MedicalAidPlanConfig.objects.filter(scheme_name__iexact=patient.medical_aid_name.strip())
    if patient.medical_aid_plan:
        exact = qs.filter(plan_name__iexact=patient.medical_aid_plan.strip()).first()
        if exact:
            return exact
    return qs.filter(plan_name='').first()


def visit_usage(patient, year=None):
    """Visits used vs plan limit for a calendar year.

    Returns None when no plan config applies, else a dict:
      {'used', 'limit', 'warn_at', 'remaining', 'status'} where status is
      'ok' | 'warning' (warn threshold reached) | 'over' (limit reached/passed).
    """
    config = plan_config_for(patient)
    if config is None:
        return None
    year = year or timezone.now().year
    used = patient.consultations.filter(date__year=year).count()
    warn_at = config.warn_threshold()
    if used >= config.visits_per_year:
        status = 'over'
    elif used >= warn_at:
        status = 'warning'
    else:
        status = 'ok'
    return {
        'year': year,
        'used': used,
        'limit': config.visits_per_year,
        'warn_at': warn_at,
        'remaining': max(0, config.visits_per_year - used),
        'status': status,
        'plan': str(config),
    }
