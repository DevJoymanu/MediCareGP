"""
Role-based access control (RBAC) for the CRM.

Two roles, implemented as Django auth Groups (created by the
patients.0008_role_groups data migration):

  Doctor    — full clinical access: symptoms, differentials, provisional
              diagnoses, consultations, vitals, investigation results.
  Reception — front office only: demographics, medical-aid details,
              appointments, billing. NO clinical data, ever.

Superusers count as doctors. Enforcement is SERVER-SIDE, not template-side:

  * View level     — @doctor_required raises PermissionDenied (HTTP 403)
                     for any non-doctor, even if they guess the URL.
  * Queryset level — reception_patient_queryset() defers every clinical
                     column so clinical data is never even selected from
                     the database for reception users.
  * Serializer lvl — patient_medical_aid_summary() whitelists the exact
                     fields the front office may see (used by biometric
                     check-in and reception patient views).
"""
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

DOCTOR_GROUP = 'Doctor'
RECEPTION_GROUP = 'Reception'

# Patient columns that constitute clinical data. Reception queries DEFER these
# (never selected from the DB); reception forms EXCLUDE them.
PATIENT_CLINICAL_FIELDS = [
    'blood_type',
    'allergies',
    'chronic_conditions',
    'current_medication',
    'previous_surgeries',
    'family_history',
    'smoking_status',
    'alcohol_use',
    'substance_use',
]

# The ONLY patient fields the biometric identify endpoint / reception
# medical-aid card may return. Whitelist, not blacklist.
MEDICAL_AID_FIELDS = [
    'id', 'first_name', 'last_name', 'file_number', 'date_of_birth',
    'medical_aid_name', 'medical_aid_plan', 'medical_aid_number',
    'principal_member_name', 'principal_member_id', 'dependant_code',
]


def is_doctor(user):
    return user.is_authenticated and (
        user.is_superuser or user.groups.filter(name=DOCTOR_GROUP).exists()
    )


def is_reception(user):
    return user.is_authenticated and not is_doctor(user)


def doctor_required(view_func):
    """Clinical views: authenticated + Doctor group (or superuser), else 403."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not is_doctor(request.user):
            raise PermissionDenied('Clinical data is restricted to doctors.')
        return view_func(request, *args, **kwargs)
    return login_required(_wrapped)


def reception_patient_queryset():
    """Patient queryset for front-office users — clinical columns are
    deferred, so they are never selected from the database."""
    from patients.models import Patient
    return Patient.objects.defer(*PATIENT_CLINICAL_FIELDS)


def patient_medical_aid_summary(patient_pk):
    """Whitelisted medical-aid dict for one patient (biometric check-in,
    reception views). Returns None if the patient does not exist."""
    from patients.models import Patient
    return Patient.objects.filter(pk=patient_pk).values(*MEDICAL_AID_FIELDS).first()
