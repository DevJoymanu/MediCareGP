"""
BHF (Board of Healthcare Funders) claim file generator.

Generates a pipe-delimited flat file in the standard BHF format accepted by
Healthbridge and other South African medical aid clearinghouses.

File structure:
  H  — File header (one per file)
  P  — Patient / member record (one per claim)
  C  — Claim line / service item (one per procedure)
  T  — File trailer (one per file)

Upload the generated .bhf file via the Healthbridge web portal:
  https://www.healthbridge.co.za  →  Claims  →  Upload Batch File
"""

from django.conf import settings


_PLACE_OF_SERVICE = '11'   # 11 = Office / consulting rooms (standard for GP)
_FILE_VERSION     = '2'    # BHF file format version


def _safe(value, default=''):
    """Return stripped string or default for None/blank values."""
    return str(value).strip() if value else default


def _date(d):
    """Format a date as CCYYMMDD for BHF."""
    return d.strftime('%Y%m%d') if d else ''


def _gender(patient):
    mapping = {'M': 'M', 'F': 'F', 'O': 'U'}
    return mapping.get(patient.gender, 'U')


def _initials(first_name):
    parts = (first_name or '').split()
    return ''.join(p[0].upper() for p in parts if p)


def _title_code(patient):
    mapping = {
        'Mr': '01', 'Mrs': '02', 'Miss': '03',
        'Ms': '04', 'Dr': '05', 'Prof': '06',
    }
    return mapping.get(patient.title or '', '01')


def generate(invoice, batch_number=None):
    """
    Generate a BHF-format claim file string for the given Invoice.

    Returns a string (the file content) ready to be written or served as a
    download. The caller supplies an optional batch_number; one is derived
    from the invoice number if omitted.
    """
    practice_no = _safe(
        getattr(settings, 'PRACTICE_NUMBER', ''),
        'MP0000000',
    )
    hb_practice_no = _safe(
        getattr(settings, 'HEALTHBRIDGE_PRACTICE_NO', ''),
        practice_no,
    )

    patient      = invoice.patient
    service_date = _date(invoice.date_issued)
    batch_no     = batch_number or invoice.invoice_number.replace('-', '')
    lines        = []

    # ── H — File header ────────────────────────────────────────────────────────
    # H|PracticeNo|BillingPracticeNo|TreatingPracticeNo|FileDate|BatchNo|Version
    lines.append('|'.join([
        'H',
        hb_practice_no,     # billing practice number (Healthbridge-registered)
        practice_no,         # treating practice number (HPCSA)
        practice_no,         # responsible practice number
        service_date,        # file creation date
        batch_no,            # batch/claim reference
        _FILE_VERSION,
    ]))

    # ── P — Patient / member record ────────────────────────────────────────────
    # P|AccountNo|Surname|Initials|Title|DOB|Sex|MedAidNo|SchemeName|PlanOption
    #   |DependantCode|AuthNo|MainMemberSurname|MainMemberInitials|MainMemberID
    lines.append('|'.join([
        'P',
        _safe(invoice.invoice_number),           # account / invoice number
        _safe(patient.last_name),
        _initials(patient.first_name),
        _title_code(patient),
        _date(patient.date_of_birth),
        _gender(patient),
        _safe(patient.medical_aid_number),
        _safe(patient.medical_aid_name),
        _safe(patient.medical_aid_plan),
        _safe(patient.dependant_code, '00'),
        _safe(invoice.authorization_number),
        _safe(patient.principal_member_name or patient.last_name),
        _initials(patient.principal_member_name or patient.first_name),
        _safe(patient.principal_member_id or patient.id_number),
    ]))

    # ── C — Claim / service lines (one per invoice item) ──────────────────────
    # C|LineNo|ServiceDate|TariffCode|NAPPICode|Description|Qty|UnitPrice
    #   |DiscountPct|LineAmount|ICD10Code|PlaceOfService|AuthNo
    total_amount = 0.0
    for idx, item in enumerate(invoice.items.all(), start=1):
        line_total = float(item.line_total())
        total_amount += line_total
        lines.append('|'.join([
            'C',
            str(idx),
            service_date,
            _safe(item.procedure_code),          # NRPL tariff code
            '',                                   # NAPPI code (medicines only)
            _safe(item.description)[:60],
            str(int(item.quantity)) if item.quantity == int(item.quantity) else str(item.quantity),
            f'{float(item.unit_price):.2f}',
            '0.00',                               # discount %
            f'{line_total:.2f}',
            _safe(invoice.icd10_code),
            _PLACE_OF_SERVICE,
            _safe(invoice.authorization_number),
        ]))

    # ── T — File trailer ───────────────────────────────────────────────────────
    # T|TotalRecords|TotalAmount
    # TotalRecords = number of C records
    record_count = len(invoice.items.all())
    lines.append('|'.join([
        'T',
        str(record_count),
        f'{total_amount:.2f}',
    ]))

    return '\r\n'.join(lines) + '\r\n'
