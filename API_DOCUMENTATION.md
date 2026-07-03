# 📡 API Documentation

This document covers the programmatic interfaces for the diagnosis engine, medical-aid gateway, and other integrations.

---

## Table of Contents

1. [Diagnosis Engine](#diagnosis-engine)
2. [Medical-Aid Gateway](#medical-aid-gateway)
3. [Biometric Provider](#biometric-provider)
4. [Billing & Tariffs](#billing--tariffs)
5. [Public APIs](#public-apis)
6. [Authentication](#authentication)

---

## Diagnosis Engine

### Purpose

Suggests likely diagnoses based on patient symptoms and history using deterministic weighted scoring (no AI/randomness).

### Entry Point: `diagnosis.engine.run_differential()`

```python
from diagnosis import engine

# Inputs:
# - patient: Patient object
# - presenting_symptom_ids: list of Symptom.id for current symptoms
# - working_symptom_ids: list of Symptom.id for historical symptoms

result = engine.run_differential(
    patient=patient,
    presenting_symptom_ids=[fever_id, cough_id],
    working_symptom_ids=[shortness_of_breath_id]
)
```

### Output Structure

```python
{
    'title': 'Provisional Diagnosis',
    'needs_more_data': False,
    'constants': {
        'history_weight': '0.70',
        'presenting_weight': '0.30',
    },
    'results': [
        {
            'condition_id': 123,
            'icd10_code': 'J20.9',
            'name': 'Acute bronchitis',
            'score': '8.50',
            'confidence_band': 'High',  # High / Medium / Low
            'presenting_match_count': 2,  # How many presenting symptoms matched
            'history_match_count': 1,
            'matching_symptoms': ['Cough', 'Fever'],
            'why': 'Matched 2 of 3 presenting symptoms + 1 history',
            'breakdown': {
                'formula': '(0.70 * history_score) + (0.30 * presenting_score)',
                'history_score': '7.50',
                'presenting_score': '9.20',
                'history_factors': [
                    {
                        'kind': 'confirming',
                        'rule': 'Current smoker',
                        'adjustment': '+2.0',
                    },
                    {
                        'kind': 'contradicting',
                        'rule': 'Age < 30',
                        'adjustment': '-1.5',
                    },
                ],
            },
        },
        # ... up to 10 results
    ],
}
```

### Constants

| Constant | Value | Purpose |
|----------|-------|---------|
| `HISTORY_WEIGHT` | 0.70 | History-based symptoms weighted 70% |
| `PRESENTING_WEIGHT` | 0.30 | Current symptoms weighted 30% |
| `TOP_N` | 10 | Return top 10 ranked diagnoses |
| `MIN_THRESHOLD` | 0.0 | No minimum score (include all) |

### Confidence Bands

| Band | Score Range | Use Case |
|------|-------------|----------|
| High | ≥ 7.0 | Strong match, high confidence |
| Medium | 4.0–6.9 | Moderate match, consider |
| Low | < 4.0 | Weak match, more data needed |

### History Modifiers

Rules that adjust diagnosis score based on patient profile:

```python
# Example rules (in diagnosis/seed_data.py):
HistoryModifierRule.objects.create(
    condition=asthma,
    rule_type='age_band',
    age_min=25, age_max=65,
    factor=Decimal('1.5'),
    kind='confirming',  # or 'contradicting'
    description='Asthma common in working-age adults',
)

HistoryModifierRule.objects.create(
    condition=asthma,
    rule_type='smoking_status',
    smoking_status='Current',
    factor=Decimal('2.0'),
    kind='confirming',
    description='Smoking worsens asthma',
)

HistoryModifierRule.objects.create(
    condition=dysmenorrhea,
    rule_type='gender',
    gender='M',
    factor=Decimal('-10.0'),
    kind='contradicting',
    description='Dysmenorrhea impossible in males',
)
```

### Knowledge Base

**Conditions** and **Symptoms** are managed in Django admin:
- `/admin/diagnosis/condition/`
- `/admin/diagnosis/symptom/`
- `/admin/diagnosis/symptomconditionlink/`
- `/admin/diagnosis/historymodifierrule/`

Each Condition has:
- **ICD-10 code** (e.g., `J20.9`)
- **Name** (e.g., "Acute bronchitis")
- **Base score** (0–10, used as starting point)

Each Symptom has:
- **Name** (e.g., "Fever")
- **Links to conditions** via `SymptomConditionLink`:
  - **weight**: how much this symptom contributes to the condition's score
  - **confirming/contradicting**: whether presence or absence matters

### First-Occurrence Flags

System flags symptoms that haven't been recorded before for this patient:

```python
flags = engine.first_occurrence_flags(patient, [fever_id])
# Returns:
# [
#     {
#         'symptom_id': 1,
#         'symptom_name': 'Fever',
#         'message': 'First recorded fever in patient history',
#         'prior_narrative_mentions': 0,
#         'prior_engine_runs': 0,
#     }
# ]
```

**Use case:** Alert doctor to new/unusual symptoms.

### View-Level Integration

#### `differential_capture` (GET + POST)
- **Route:** `/diagnosis/<consultation_id>/capture/`
- **Method:** GET shows symptom checklist form; POST runs engine
- **Auth:** `@doctor_required` (403 if receptionist)
- **Response:** Renders form (GET) or redirects to results (POST)

```python
# POST body:
{
    'presenting': [1, 2, 3],  # Symptom IDs (current)
    'working': [4, 5],        # Symptom IDs (history)
}
```

#### `differential_result` (GET)
- **Route:** `/diagnosis/result/<result_id>/`
- **Response:** HTML template showing top 3–10 diagnoses
- **Auth:** `@doctor_required`

#### `differential_confirm` (POST)
- **Route:** `/diagnosis/result/<result_id>/confirm/`
- **Input:** `confirm=<condition_id>`
- **Effect:** Appends ICD-10 code to consultation's `icd10_codes` list
- **Auth:** `@doctor_required`

### Testing Determinism

```python
# The engine MUST produce identical output for identical inputs:
run1 = engine.run_differential(patient, [fever_id, cough_id], [sob_id])
run2 = engine.run_differential(patient, [cough_id, fever_id], [sob_id])
assert run1 == run2  # Order of input IDs should not matter
```

---

## Medical-Aid Gateway

### Purpose

Submit insurance claims and retrieve eligibility/remittance data.

### Architecture

```
Invoice (billing)
    ↓
ClaimBuilder.build(invoice) → sanitized claim payload
    ↓
SchemeConfig → adapter type (manual / direct / custom)
    ↓
Adapter.submit_claim(payload) → claim submission
    ↓
Gateway response (queued / rejected / accepted)
```

### ClaimBuilder

Ensures **no clinical data** leaves the server.

```python
from medaid.claim_builder import ClaimBuilder

builder = ClaimBuilder()
claim = builder.build(invoice, practice_number='MediCareGP001')

# Output structure:
{
    'claim_number': 'CLM-20260703-001',
    'practice_number': 'MediCareGP001',
    'patient': {
        'member_number': 'ABC123456',
        'first_name': 'Thabo',
        'last_name': 'Mokoena',
    },
    'items': [
        {
            'code': 'CONS',
            'description': 'Consultation',
            'amount': '350.00',
            'quantity': 1,
        },
    ],
    'total': '350.00',
    'currency': 'ZAR',
}
```

**Whitelist-only:** Only these fields included:
- `patient.member_number`, `first_name`, `last_name`
- `items.code`, `description`, `amount`, `quantity`
- No clinical narrative, allergies, medications, or diagnoses

**Guard against leakage:**
```python
# ClaimBuilder._assert_no_clinical_keys() recursively scans payload
FORBIDDEN_KEYS = {
    'subjective', 'objective', 'assessment', 'plan',
    'allergies', 'medications', 'chronic_conditions',
    'notes', 'narrative', 'clinical', 'diagnosis_details',
    'medical_history', ...
}
```

### Gateway Interface

```python
from medaid.gateway import MedicalAidGateway, MemberDetails, EligibilityResult

# All adapters implement this:
class MedicalAidGateway:
    def verify_member(self, member_number) -> MemberDetails:
        """Returns member details or None if not found."""
        pass

    def check_eligibility(self, member_number) -> EligibilityResult:
        """Returns eligibility status."""
        pass

    def submit_claim(self, claim_payload) -> ClaimResult:
        """Submits claim. Returns tracking number or error."""
        pass

    def get_remittance(self, claim_number) -> RemittanceResult:
        """Fetches payment status."""
        pass
```

### Adapters

#### ManualAdapter (Fallback)

No external API. Records submission in database.

```python
from medaid.adapters.manual import ManualAdapter

adapter = ManualAdapter()
result = adapter.submit_claim(claim_payload)

# Result:
{
    'status': 'submitted',
    'tracking_number': 'SUB-20260703-12345',
    'message': 'Claim queued for manual processing',
    'submitted_at': '2026-07-03T14:30:00Z',
}
```

#### Custom Adapter Template

```python
# medicaregp/medaid/adapters/custom_scheme.py
from medaid.gateway import MedicalAidGateway, ClaimResult
import requests
import os

class CustomSchemeAdapter(MedicalAidGateway):
    def __init__(self, scheme_config):
        self.scheme_config = scheme_config
        self.username = os.getenv(scheme_config.username_env)
        self.password = os.getenv(scheme_config.password_env)

    def submit_claim(self, claim_payload):
        # Call external API
        response = requests.post(
            self.scheme_config.endpoint_url,
            json=claim_payload,
            auth=(self.username, self.password),
            timeout=30,
        )
        if response.status_code == 200:
            return ClaimResult(
                status='accepted',
                tracking_number=response.json()['claim_number'],
                message='Claim accepted',
                submitted_at=datetime.now(timezone.utc),
            )
        else:
            return ClaimResult(
                status='rejected',
                error=f'API returned {response.status_code}',
                submitted_at=datetime.now(timezone.utc),
            )
```

### SchemeConfig Model

Stores scheme-specific configuration without hardcoding secrets.

```python
from medaid.models import SchemeConfig

# Create:
SchemeConfig.objects.create(
    scheme_name='MyScheme',
    adapter_type='custom_scheme',  # or 'manual'
    endpoint_url='https://api.myscheme.com/claims',
    username_env='MYSCHEME_USERNAME',  # Env var names, not values
    password_env='MYSCHEME_PASSWORD',
    api_key_env='MYSCHEME_API_KEY',
)

# Retrieve:
config = SchemeConfig.objects.get(scheme_name='MyScheme')
username = config.credentials()['username']  # Fetches from env at call time
```

### View-Level Integration

#### `verify_member` (GET)
- **Route:** `/medaid/verify/<member_number>/`
- **Response:** JSON with member details or 404
- **Auth:** `@doctor_required`

```json
{
    "member_number": "ABC123456",
    "first_name": "Thabo",
    "last_name": "Mokoena",
    "plan_name": "Essential",
    "status": "Active"
}
```

#### `submit_claim` (POST)
- **Route:** `/medaid/claim/<invoice_id>/submit/`
- **Input:** `invoice_id`
- **Response:** JSON with claim tracking number
- **Auth:** `@doctor_required`

```json
{
    "status": "submitted",
    "tracking_number": "CLM-20260703-001",
    "message": "Claim submitted to Momentum Health",
    "submitted_at": "2026-07-03T14:30:00Z"
}
```

---

## Biometric Provider

### Purpose

Pluggable interface for patient identification (fingerprint, iris, etc.).

### Interface

```python
from patients.biometrics import BiometricProvider

class BiometricProvider:
    def enrol(self, patient, template_sample):
        """Store patient's biometric template (hashed only)."""
        pass

    def identify(self, template_sample):
        """Scan a sample. Return patient or None if no match."""
        pass
```

### Current Implementation: SHA-256 Simulator

```python
from patients.biometrics import HashBiometricProvider

provider = HashBiometricProvider()

# Enrol:
provider.enrol(patient, "fingerprint_data_from_scanner")
# Stores SHA-256 hash in BiometricTemplate.template_hash

# Identify:
matching_patient = provider.identify("fingerprint_data_from_scanner")
# Returns patient if hash matches, else None
```

### Real SDK Integration

To use a real biometric scanner:

```python
# medicaregp/settings.py
BIOMETRIC_PROVIDER = 'mycompany.biometric_providers.NeurotechProvider'

# mycompany/biometric_providers.py
from patients.biometrics import BiometricProvider
import myneurotech_sdk

class NeurotechProvider(BiometricProvider):
    def __init__(self):
        self.scanner = myneurotech_sdk.Scanner()

    def enrol(self, patient, template_sample):
        # Scanner returns a template object
        from patients.models import BiometricTemplate
        BiometricTemplate.objects.update_or_create(
            patient=patient,
            defaults={'template_hash': hash(template_sample)}
        )

    def identify(self, template_sample):
        from patients.models import BiometricTemplate
        template = BiometricTemplate.objects.filter(
            template_hash=hash(template_sample)
        ).first()
        return template.patient if template else None
```

### View-Level Integration

#### `biometric_identify` (POST)
- **Route:** `/patients/biometric/`
- **Input:** Scanned template (form field `sample`)
- **Response:** HTML showing matched patient + medical-aid details (whitelisted only)
- **Auth:** `@login_required`

#### `biometric_enrol` (POST)
- **Route:** `/patients/<id>/biometric/enrol/`
- **Input:** Scanned template (form field `sample`)
- **Effect:** Stores hash, not template
- **Auth:** `@login_required`

---

## Billing & Tariffs

### Tariff Versioning

Tariffs are **immutable** and **append-only** to preserve historical pricing.

```python
from billing.models import TariffCode, TariffRate

# Create a tariff code (e.g., "Consultation"):
code = TariffCode.objects.create(
    code='CONS',
    description='Consultation',
    category='Medical',  # Medical or Surgical
)

# Add rates at different times (immutable):
TariffRate.objects.create(
    tariff_code=code,
    effective_from=date(2026, 1, 1),
    amount=Decimal('350.00'),
)

TariffRate.objects.create(
    tariff_code=code,
    effective_from=date(2026, 7, 1),
    amount=Decimal('375.00'),  # Rate increase
)

# Invoice items snapshot the rate at billing time:
InvoiceItem.objects.create(
    invoice=invoice,
    tariff=code,
    unit_price=Decimal('350.00'),  # Locked in, never changes
    quantity=1,
)
```

### Invoice Endpoints

#### `tariff_list` (GET)
- **Route:** `/billing/tariffs/`
- **Response:** JSON list of TariffCode with current rates

```json
[
    {
        "code": "CONS",
        "description": "Consultation",
        "category": "Medical",
        "current_rate": "350.00",
        "effective_from": "2026-01-01"
    }
]
```

#### `tariff_rate_lookup` (GET)
- **Route:** `/billing/tariff/<code>/rates/`
- **Response:** JSON history of rates for a code

```json
{
    "code": "CONS",
    "rates": [
        {
            "amount": "350.00",
            "effective_from": "2026-01-01"
        },
        {
            "amount": "375.00",
            "effective_from": "2026-07-01"
        }
    ]
}
```

---

## Public APIs

These endpoints do NOT require authentication (use honeypot + CSRF exemption).

### Appointment Booking

#### `POST /api/bookings`

Book an online appointment from the public website.

```bash
curl -X POST http://localhost:8000/api/bookings \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "phone": "0821234567",
    "date": "2026-07-10",
    "slot": 2,
    "reason": "General consultation",
    "appointment_type": "Consultation"
  }'
```

**Response (success):**
```json
{
    "id": 123,
    "status": "requested",
    "booking_reference": "WEB-20260703-12345",
    "message": "Booking received. We'll confirm shortly."
}
```

**Response (slot taken):**
```json
{
    "error": "slotTaken",
    "message": "Slot no longer available. Please choose another."
}
```

**Response (validation error):**
```json
{
    "error": "validationError",
    "details": {
        "email": ["Invalid email format"]
    }
}
```

### Availability Check

#### `GET /api/availability?date=YYYY-MM-DD`

Get available booking slots for a date.

```bash
curl "http://localhost:8000/api/availability?date=2026-07-10"
```

**Response:**
```json
{
    "date": "2026-07-10",
    "slots": [
        {
            "slot_number": 1,
            "time": "09:00",
            "available": true
        },
        {
            "slot_number": 2,
            "time": "09:30",
            "available": false,
            "booked_by": "existing_appointment"
        },
        {
            "slot_number": 3,
            "time": "10:00",
            "available": true
        }
    ],
    "booking_interval_minutes": 30
}
```

### Patient Check-In (Token)

#### `POST /appointments/checkin/<token>`

Patient self check-in via QR code.

**Response:**
```json
{
    "patient_id": 123,
    "patient_name": "John Doe",
    "appointment_id": 456,
    "checked_in_at": "2026-07-03T14:30:00Z",
    "message": "Check-in successful"
}
```

### Results Portal (Token)

#### `GET /results/<token>`

Patient views lab/radiology results by UUID token.

**Response:** HTML page showing investigation request details and results (if uploaded).

---

## Authentication

### Django Session Auth (Staff)

All staff endpoints use Django session auth:

```python
@login_required
def consultation_detail(request, pk):
    ...
```

User must have a session cookie (obtained via `/login/`).

### Role-Based Access Control (RBAC)

```python
from medicaregp.roles import doctor_required, is_doctor

@doctor_required  # Returns 403 if user not in 'Doctor' group
def differential_capture(request, pk):
    ...

if is_doctor(request.user):
    # Show full patient record
else:
    # Show demographics + medical aid only
```

### Groups

Two groups exist:

| Group | Permissions |
|-------|-------------|
| **Doctor** | Full access to clinical data, diagnosis, consultations |
| **Reception** | Demographics + medical aid only, check-in, scheduling |

Assign via Django admin or code:

```python
from django.contrib.auth.models import Group

user.groups.add(Group.objects.get(name='Doctor'))
```

### Token-Based Public Access

Patient-facing views use UUID tokens (no login required):

```python
# Patient joins video call:
# GET /video/join/<token>/
# Token is generated per invitation, unguessable UUID

# Results portal:
# GET /results/<token>/
# Token generated when investigation request created
```

---

## CSRF & Honeypot

Public JSON endpoints are protected:

```python
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

@csrf_exempt
@require_http_methods(["POST"])
def api_bookings(request):
    # Manually validate honeypot
    if request.POST.get('website'):
        return JsonResponse({'error': 'Invalid'}, status=400)
    ...
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 302 | Redirect (e.g., successful POST) |
| 400 | Bad request (validation error) |
| 403 | Forbidden (RBAC violation) |
| 404 | Not found |
| 409 | Conflict (e.g., slot taken) |
| 500 | Server error (log and alert) |

### Error Response Format

```json
{
    "error": "error_code",
    "message": "Human-readable message",
    "details": {}  # Optional context
}
```

---

## Rate Limiting

Not implemented yet. Consider adding if API grows.

---

## Testing

All endpoints have test coverage in:
- `diagnosis/tests.py` (45 tests)
- `medaid/tests.py` (coverage for claim builder, adapters)
- `consultations/tests.py` (view-level tests)
- `patients/tests.py` (biometric, visit usage)
- `billing/tests.py` (tariff versioning)

Run full suite: `python manage.py test`

---

**Last updated:** 2026-07-03  
**Django version:** 4.2  
**API version:** 1.0
