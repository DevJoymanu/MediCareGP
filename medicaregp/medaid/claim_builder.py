"""
ClaimBuilder — the privacy boundary between the CRM and any medical aid.

Every outbound claim payload is built HERE and only here, from an explicit
WHITELIST of non-clinical billing fields. Clinical narrative (SOAP notes,
symptoms, differentials, assessments) is structurally excluded: this module
never reads those fields at all, so no adapter can leak them. ICD-10 codes
are included — they are standard claim-coding data required by schemes —
but never any free-text clinical content.

There is a test asserting no clinical field name or value appears in a
built payload.
"""

# Field names that must NEVER appear in an outbound payload (tested).
FORBIDDEN_KEYS = {
    'chief_complaint', 'subjective', 'objective', 'assessment', 'plan',
    'differential_diagnosis', 'review', 'prescriptions', 'notes',
    'allergies', 'chronic_conditions', 'current_medication',
    'previous_surgeries', 'family_history', 'lab_requests',
    'radiology_requests',
}


class ClaimBuilder:
    """Builds the minimum non-clinical claim payload from an Invoice."""

    @staticmethod
    def build(invoice, practice_number):
        patient = invoice.patient
        payload = {
            'practice': {
                'practice_number': practice_number,
            },
            'member': {
                'scheme_name': patient.medical_aid_name or '',
                'scheme_plan': patient.medical_aid_plan or '',   # named to avoid the forbidden clinical 'plan' key
                'member_number': patient.medical_aid_number or '',
                'principal_member_name': patient.principal_member_name or '',
                'dependant_code': patient.dependant_code or '',
                'patient_first_name': patient.first_name,
                'patient_last_name': patient.last_name,
                'patient_date_of_birth': patient.date_of_birth.isoformat(),
            },
            'claim': {
                'invoice_number': invoice.invoice_number,
                'date_of_service': invoice.date_issued.isoformat(),
                'authorization_number': invoice.authorization_number or '',
                'icd10_codes': [e.get('code', '') for e in invoice.icd10_codes_list],
                'lines': [
                    {
                        'tariff_code': item.procedure_code or (item.tariff.code if item.tariff_id else ''),
                        'nappi_code': item.nappi_code or '',
                        'description': item.description or '',
                        'category': item.category,
                        'diagnosis_code': item.diag_code or '',
                        'quantity': str(item.quantity),
                        'unit_price': str(item.unit_price),
                        'line_total': str(item.line_total()),
                    }
                    for item in invoice.items.all()
                ],
                'subtotal': str(invoice.subtotal()),
                'vat': str(invoice.vat_amount()),
                'total': str(invoice.total()),
            },
        }
        ClaimBuilder._assert_no_clinical_keys(payload)
        return payload

    @staticmethod
    def _assert_no_clinical_keys(obj):
        """Defence in depth: refuse to emit a payload containing any
        forbidden clinical key, however it got there."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key in FORBIDDEN_KEYS:
                    raise ValueError(f'Clinical field "{key}" must never leave the server.')
                ClaimBuilder._assert_no_clinical_keys(value)
        elif isinstance(obj, (list, tuple)):
            for value in obj:
                ClaimBuilder._assert_no_clinical_keys(value)
