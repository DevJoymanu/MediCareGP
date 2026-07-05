import io
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from medicaregp.roles import doctor_required
from django.core.mail import EmailMessage
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from appointments.models import Appointment
from patients.models import Patient
from .models import Consultation, ConditionPrescriptionLink, Provider, InvestigationRequest
from .forms import ConsultationForm, ProviderForm
from .icd10_data import ICD10_CODES


# ── Prescription suggestion helpers ──────────────────────────────────────────

def _parse_conditions(text):
    """Split an assessment field into individual condition strings."""
    import re
    if not text:
        return []
    # Split on: newline, comma, semicolon, forward-slash, period+space, or numbered list markers
    parts = re.split(r'[\n,;/]|\.\s+|\d+[.\)]\s*', text)
    return [p.strip() for p in parts if len(p.strip()) > 3]


def _parse_prescriptions(text):
    """Split a prescriptions field into individual lines."""
    if not text:
        return []
    return [p.strip() for p in text.splitlines() if p.strip()]


def _learn_from_consultation(consultation):
    """
    Update ConditionPrescriptionLink counts based on a saved consultation.
    Called after every consultation save.
    """
    conditions    = _parse_conditions(consultation.assessment)
    prescriptions = _parse_prescriptions(consultation.prescriptions)
    if not conditions or not prescriptions:
        return
    for condition in conditions:
        for prescription in prescriptions:
            obj, created = ConditionPrescriptionLink.objects.get_or_create(
                condition=condition,
                prescription=prescription,
                defaults={'count': 1, 'is_seeded': False},
            )
            if not created:
                ConditionPrescriptionLink.objects.filter(pk=obj.pk).update(
                    count=obj.count + 1
                )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_sick_note_pdf(consultation):
    """Return a BytesIO containing the sick note PDF."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )

    styles = getSampleStyleSheet()
    purple = colors.HexColor('#7e22ce')
    dark   = colors.HexColor('#1e293b')
    grey   = colors.HexColor('#64748b')

    def style(name, **kw):
        s = ParagraphStyle(name, parent=styles['Normal'], **kw)
        return s

    header_style    = style('H', fontSize=18, fontName='Helvetica-Bold', textColor=purple, spaceAfter=2)
    subheader_style = style('SH', fontSize=9, fontName='Helvetica', textColor=grey, spaceAfter=0)
    title_style     = style('T', fontSize=14, fontName='Helvetica-Bold', textColor=dark, alignment=TA_CENTER, spaceBefore=6, spaceAfter=6)
    body_style      = style('B', fontSize=10, fontName='Helvetica', textColor=dark, leading=16, spaceAfter=4)
    label_style     = style('L', fontSize=9, fontName='Helvetica-Bold', textColor=grey, spaceAfter=1)
    value_style     = style('V', fontSize=11, fontName='Helvetica-Bold', textColor=dark, spaceAfter=10)
    footer_style    = style('F', fontSize=9, fontName='Helvetica', textColor=grey, alignment=TA_CENTER)
    sign_style      = style('SG', fontSize=10, fontName='Helvetica-Bold', textColor=dark, spaceAfter=2)

    p  = consultation.patient
    c  = consultation
    start = c.sick_note_start_date
    days  = c.sick_note_days or 1
    end   = start + timedelta(days=days - 1) if start else None

    def fmt(d):
        return d.strftime('%-d %B %Y') if d else '—'

    story = []

    # ── Letterhead ────────────────────────────────────────────────────────────
    letterhead_data = [[
        Paragraph(getattr(settings, 'PRACTICE_NAME', 'General Practitioner'), header_style),
        Paragraph(
            f"{getattr(settings, 'PRACTICE_SUBTITLE', 'General Practitioner')}<br/>"
            f"{getattr(settings, 'PRACTICE_ADDRESS', '')}<br/>"
            f"Tel: {getattr(settings, 'PRACTICE_PHONE', '')}  |  "
            f"Email: {getattr(settings, 'PRACTICE_EMAIL', '')}",
            style('LH_right', fontSize=8, fontName='Helvetica', textColor=grey, alignment=TA_RIGHT, leading=13)
        ),
    ]]
    lh_table = Table(letterhead_data, colWidths=[90 * mm, 80 * mm])
    lh_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(lh_table)
    story.append(Spacer(1, 3 * mm))
    story.append(HRFlowable(width='100%', thickness=2, color=purple, spaceAfter=6 * mm))

    # ── Certificate title ─────────────────────────────────────────────────────
    story.append(Paragraph('MEDICAL CERTIFICATE', title_style))
    story.append(HRFlowable(width='100%', thickness=0.5, color=colors.HexColor('#e2e8f0'), spaceAfter=6 * mm))

    # ── Intro sentence ────────────────────────────────────────────────────────
    story.append(Paragraph(
        f'This is to certify that I have examined the patient named below on '
        f'<b>{fmt(c.date)}</b> and found them unfit for duty/school for the period indicated.',
        body_style
    ))
    story.append(Spacer(1, 4 * mm))

    # ── Patient details table ─────────────────────────────────────────────────
    def row(label, value):
        return [
            Paragraph(label, label_style),
            Paragraph(str(value) if value else '—', value_style),
        ]

    detail_data = [
        row('PATIENT FULL NAME', f'{p.first_name} {p.last_name}'),
        row('ID / PASSPORT NUMBER', p.id_number),
        row('DATE OF EXAMINATION', fmt(c.date)),
    ]
    if c.sick_note_employer:
        detail_data.append(row('EMPLOYER / INSTITUTION', c.sick_note_employer))

    detail_table = Table(detail_data, colWidths=[55 * mm, 115 * mm])
    detail_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f5ff')),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#fafafa')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(detail_table)
    story.append(Spacer(1, 5 * mm))

    # ── Period box ────────────────────────────────────────────────────────────
    period_text = (
        f'<b>UNFIT FOR DUTY FROM:</b>  {fmt(start)}  '
        f'<b>TO:</b>  {fmt(end)}  '
        f'<b>({days} day{"s" if days != 1 else ""})</b>'
    )
    period_table = Table(
        [[Paragraph(period_text, style('PT', fontSize=11, fontName='Helvetica', textColor=dark, alignment=TA_CENTER))]],
        colWidths=[170 * mm]
    )
    period_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f5f3ff')),
        ('BOX', (0, 0), (-1, -1), 1.5, purple),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(period_table)
    story.append(Spacer(1, 8 * mm))

    # ── Signature block ───────────────────────────────────────────────────────
    sig_data = [[
        Paragraph(
            '_______________________________<br/>'
            f'<b>{getattr(settings, "PRACTICE_NAME", "")}</b><br/>'
            f'{getattr(settings, "PRACTICE_SUBTITLE", "General Practitioner")}<br/>'
            f'{getattr(settings, "PRACTICE_REG", "")}',
            style('SB', fontSize=10, fontName='Helvetica', textColor=dark, leading=16)
        ),
        Paragraph(
            f'Date issued: <b>{fmt(timezone.localdate())}</b>',
            style('DI', fontSize=10, fontName='Helvetica', textColor=dark, alignment=TA_RIGHT)
        ),
    ]]
    sig_table = Table(sig_data, colWidths=[100 * mm, 70 * mm])
    sig_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'BOTTOM')]))
    story.append(sig_table)
    story.append(Spacer(1, 8 * mm))
    story.append(HRFlowable(width='100%', thickness=0.5, color=colors.HexColor('#e2e8f0'), spaceAfter=3 * mm))

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(Paragraph(
        'This certificate is issued in terms of applicable legislation and is valid only as presented. '
        'Any alteration renders this document invalid.',
        footer_style
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer


# ── Investigation requests (lab / radiology) ──────────────────────────────────

def _sync_investigation_requests(consultation):
    """
    Ensure an InvestigationRequest exists for each kind that has request text.
    Idempotent: refreshes the requested-items snapshot but never duplicates.
    """
    from .models import InvestigationRequest
    pairs = [('lab', consultation.lab_requests), ('radiology', consultation.radiology_requests)]
    for kind, text in pairs:
        text = (text or '').strip()
        if not text:
            continue
        inv, created = InvestigationRequest.objects.get_or_create(
            consultation=consultation,
            kind=kind,
            defaults={
                'requested_items': text,
                'history': (consultation.chief_complaint or consultation.assessment or '').strip(),
            },
        )
        if not created and inv.requested_items != text:
            inv.requested_items = text
            inv.save(update_fields=['requested_items'])


# Map a free-text request line to a standard radiology modality (for the checklist).
_RADIOLOGY_MODALITIES = [
    ('X-rays',                            ('x-ray', 'xray', 'x ray', 'radiograph')),
    ('Ultrasound',                        ('ultrasound', 'sonar', 'u/s', 'us ')),
    ('Doppler Ultrasound (colour flow)',  ('doppler',)),
    ('Mammogram',                         ('mammogram', 'mammo')),
    ('4D Ultrasound',                     ('4d',)),
    ('Immigration',                       ('immigration',)),
]


def _classify_radiology_items(items):
    """Return (rows, other) where rows is [(modality_label, [matched lines]), ...] and
    other is the list of lines that didn't match a standard modality."""
    buckets = {label: [] for label, _ in _RADIOLOGY_MODALITIES}
    other = []
    for line in items:
        low = line.lower()
        matched = None
        for label, keywords in _RADIOLOGY_MODALITIES:
            if any(k in low for k in keywords):
                matched = label
                break
        if matched:
            buckets[matched].append(line)
        else:
            other.append(line)
    rows = [(label, buckets[label]) for label, _ in _RADIOLOGY_MODALITIES]
    return rows, other


def _build_request_pdf(consultation, inv, request):
    """Letterheaded lab/radiology request form, mirroring the imaging-request layout.
    Results are submitted via the standing /lab/ and /radiology/ portals, so no
    per-patient link or QR is printed on the form the patient carries."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
                                    Table, TableStyle)
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm,
                            topMargin=16 * mm, bottomMargin=16 * mm)

    styles = getSampleStyleSheet()
    purple = colors.HexColor('#7e22ce')
    dark   = colors.HexColor('#1e293b')
    grey   = colors.HexColor('#64748b')

    def style(name, **kw):
        return ParagraphStyle(name, parent=styles['Normal'], **kw)

    header_style = style('H',  fontSize=17, fontName='Helvetica-Bold', textColor=purple, spaceAfter=2)
    title_style  = style('T',  fontSize=14, fontName='Helvetica-Bold', textColor=dark, alignment=TA_CENTER, spaceBefore=4, spaceAfter=4)
    body_style   = style('B',  fontSize=10, fontName='Helvetica', textColor=dark, leading=15)
    label_style  = style('L',  fontSize=8,  fontName='Helvetica-Bold', textColor=grey)
    value_style  = style('V',  fontSize=10.5, fontName='Helvetica-Bold', textColor=dark)
    section_style= style('SEC',fontSize=10, fontName='Helvetica-Bold', textColor=colors.white)
    small_style  = style('SM', fontSize=8.5, fontName='Helvetica', textColor=grey, alignment=TA_CENTER, leading=11)

    p   = consultation.patient
    c   = consultation
    is_rad = inv.kind == 'radiology'

    def fmt(d):
        return f'{d.day} {d:%B %Y}' if d else '—'

    story = []

    # ── Letterhead (referring practice) ───────────────────────────────────────
    lh = [[
        Paragraph(getattr(settings, 'PRACTICE_NAME', 'General Practitioner'), header_style),
        Paragraph(
            f"{getattr(settings, 'PRACTICE_SUBTITLE', 'General Practitioner')}<br/>"
            f"{getattr(settings, 'PRACTICE_ADDRESS', '')}<br/>"
            f"Tel: {getattr(settings, 'PRACTICE_PHONE', '')}  |  {getattr(settings, 'PRACTICE_EMAIL', '')}<br/>"
            f"Practice No: {getattr(settings, 'PRACTICE_NUMBER', '')}",
            style('LHr', fontSize=8, fontName='Helvetica', textColor=grey, alignment=TA_RIGHT, leading=12)),
    ]]
    t = Table(lh, colWidths=[95 * mm, 79 * mm])
    t.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
    story.append(t)
    story.append(Spacer(1, 3 * mm))
    story.append(HRFlowable(width='100%', thickness=2, color=purple, spaceAfter=4 * mm))

    # ── Title ──────────────────────────────────────────────────────────────────
    story.append(Paragraph('IMAGING REQUEST FORM' if is_rad else 'PATHOLOGY / LABORATORY REQUEST', title_style))
    story.append(Spacer(1, 3 * mm))

    # ── Recipient ──────────────────────────────────────────────────────────────
    recipient = inv.recipient_name or '—'
    rec_extra = []
    if inv.provider and inv.provider.practice_no:
        rec_extra.append(f"Practice No: {inv.provider.practice_no}")
    if inv.recipient_email:
        rec_extra.append(inv.recipient_email)
    story.append(Paragraph(
        f"<b>To:</b> {recipient}" + (f"  &nbsp;<font color='#64748b'>({'  |  '.join(rec_extra)})</font>" if rec_extra else ''),
        body_style))
    story.append(Spacer(1, 3 * mm))

    # ── Patient / referrer / medical aid block ────────────────────────────────
    def cell(label, val):
        return [Paragraph(label, label_style), Paragraph(str(val) if val else '—', value_style)]

    detail = [
        cell("PATIENT'S NAME", f'{p.first_name} {p.last_name}') + cell("DATE", fmt(timezone.localdate())),
        cell("REFERRING DOCTOR", getattr(settings, 'PRACTICE_NAME', '')) + cell("PRACTICE NO", getattr(settings, 'PRACTICE_NUMBER', '')),
        cell("MEDICAL AID", p.medical_aid_name) + cell("MEDICAL AID NO", p.medical_aid_number),
    ]
    dt = Table(detail, colWidths=[33 * mm, 54 * mm, 30 * mm, 57 * mm])
    dt.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f5ff')),
        ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#f8f5ff')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(dt)
    story.append(Spacer(1, 4 * mm))

    # ── Section header helper ──────────────────────────────────────────────────
    def section(text):
        st = Table([[Paragraph(text, section_style)]], colWidths=[174 * mm])
        st.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), purple),
            ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ]))
        return st

    items = inv.requested_items_list

    if is_rad:
        # ── Examination required: modality checklist ──────────────────────────
        story.append(section('EXAMINATION REQUIRED'))
        story.append(Spacer(1, 2 * mm))
        rows, other = _classify_radiology_items(items)
        check_rows = []
        for label, matched in rows:
            ticked = '[X]' if matched else '[ &nbsp; ]'
            detail_txt = ', '.join(matched) if matched else ''
            check_rows.append([
                Paragraph(f"{ticked}  {label}", body_style),
                Paragraph(detail_txt, body_style),
            ])
        check_rows.append([
            Paragraph(("[X]" if other else "[ &nbsp; ]") + "  Whole body / Other", body_style),
            Paragraph(', '.join(other), body_style),
        ])
        ct = Table(check_rows, colWidths=[70 * mm, 104 * mm])
        ct.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LINEBELOW', (1, 0), (1, -1), 0.4, colors.HexColor('#cbd5e1')),
        ]))
        story.append(ct)
    else:
        # ── Lab: simple list of requested tests ───────────────────────────────
        story.append(section('TESTS REQUESTED'))
        story.append(Spacer(1, 2 * mm))
        list_rows = [[Paragraph(f"•  {line}", body_style)] for line in items] or [[Paragraph('—', body_style)]]
        lt = Table(list_rows, colWidths=[174 * mm])
        lt.setStyle(TableStyle([
            ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(lt)

    story.append(Spacer(1, 4 * mm))

    # ── History + Nappi ────────────────────────────────────────────────────────
    story.append(Paragraph(f"<b>History / Clinical notes:</b> {inv.history or '—'}", body_style))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph(f"<b>Nappi Code:</b> {inv.nappi_code or '—'}", body_style))
    story.append(Spacer(1, 5 * mm))

    # ── Signature ──────────────────────────────────────────────────────────────
    sig = [[
        Paragraph('_______________________________<br/>'
                  f"<b>{getattr(settings, 'PRACTICE_NAME', '')}</b><br/>"
                  f"{getattr(settings, 'PRACTICE_SUBTITLE', 'General Practitioner')} — "
                  f"Date: {fmt(timezone.localdate())}",
                  style('SBl', fontSize=9.5, fontName='Helvetica', textColor=dark, leading=14)),
    ]]
    story.append(Table(sig, colWidths=[174 * mm]))
    story.append(Spacer(1, 4 * mm))

    # ── Films and Report: deliver-to ───────────────────────────────────────────
    if is_rad:
        def opt(key, lbl):
            return ('[X] ' if inv.deliver_to == key else '[ &nbsp; ] ') + lbl
        story.append(section('FILMS AND REPORT'))
        story.append(Spacer(1, 2 * mm))
        story.append(Paragraph(
            f"<b>Deliver to:</b>&nbsp;&nbsp; {opt('rooms', 'Rooms')} &nbsp;&nbsp; "
            f"{opt('ward', 'Hospital ward')} &nbsp;&nbsp; {opt('patient', 'To be given to patient')}",
            body_style))
        story.append(Spacer(1, 4 * mm))

    doc.build(story)
    buffer.seek(0)
    return buffer


def _request_pdf_response(request, pk, kind):
    consultation = get_object_or_404(Consultation, pk=pk)
    _sync_investigation_requests(consultation)
    inv = consultation.investigation_requests.filter(kind=kind).first()
    if not inv:
        messages.error(request, f'No {kind} requests recorded on this consultation.')
        return redirect('consultation_detail', pk=pk)
    buffer = _build_request_pdf(consultation, inv, request)
    label = 'Radiology' if kind == 'radiology' else 'Lab'
    filename = f'{label}_Request_{str(consultation.patient).replace(" ", "_")}_{consultation.date}.pdf'
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@doctor_required
def radiology_request_pdf(request, pk):
    return _request_pdf_response(request, pk, 'radiology')


@doctor_required
def lab_request_pdf(request, pk):
    return _request_pdf_response(request, pk, 'lab')


# ── Prepare a request (set provider / history / nappi / deliver-to) ───────────

@doctor_required
@require_POST
def prepare_request(request, pk):
    consultation = get_object_or_404(Consultation, pk=pk)
    kind = request.POST.get('kind')
    if kind not in ('lab', 'radiology'):
        messages.error(request, 'Unknown request type.')
        return redirect('consultation_detail', pk=pk)

    _sync_investigation_requests(consultation)
    inv = consultation.investigation_requests.filter(kind=kind).first()
    if not inv:
        messages.error(request, f'No {kind} requests recorded on this consultation.')
        return redirect('consultation_detail', pk=pk)

    provider_id = request.POST.get('provider') or None
    inv.provider = Provider.objects.filter(pk=provider_id).first() if provider_id else None
    inv.history    = request.POST.get('history', '').strip()
    inv.nappi_code = request.POST.get('nappi_code', '').strip()
    deliver_to     = request.POST.get('deliver_to', '').strip()
    if deliver_to in dict(InvestigationRequest.DELIVER_CHOICES):
        inv.deliver_to = deliver_to
    inv.save(update_fields=['provider', 'history', 'nappi_code', 'deliver_to'])
    messages.success(request, f'{inv.get_kind_display()} request updated.')
    return redirect('consultation_detail', pk=pk)


# ── Email the request to the provider / patient ───────────────────────────────

def _send_request_email(request, pk, kind):
    consultation = get_object_or_404(Consultation, pk=pk)
    _sync_investigation_requests(consultation)
    inv = consultation.investigation_requests.filter(kind=kind).first()
    if not inv:
        return JsonResponse({'error': f'No {kind} requests on this consultation.'}, status=400)

    patient = consultation.patient
    if kind == 'radiology':
        recipient = patient.email
        if not recipient:
            return JsonResponse({'error': 'No email address on file for this patient.'}, status=400)
        who = f'{patient.first_name} {patient.last_name}'
    else:
        recipient = request.POST.get('to', '').strip() or inv.recipient_email or getattr(settings, 'LAB_EMAIL', '')
        if not recipient:
            return JsonResponse({'error': 'No lab email address. Add one to the provider or type a recipient.'}, status=400)
        who = inv.recipient_name or 'the laboratory'

    buffer = _build_request_pdf(consultation, inv, request)
    label = 'Radiology' if kind == 'radiology' else 'Lab'
    filename = f'{label}_Request_{str(patient).replace(" ", "_")}_{consultation.date}.pdf'

    body = (
        f'Dear {who},\n\n'
        f'Please find attached a {label.lower()} request from '
        f'{getattr(settings, "PRACTICE_NAME", "your doctor")} for '
        f'{patient.first_name} {patient.last_name}.\n\n'
    )
    if kind == 'radiology':
        body += (
            'Please present this form at the radiology practice. The practice submits '
            'results back to us via our secure radiology portal.\n\n'
        )
    else:
        lab_portal_url = request.build_absolute_uri(reverse('lab_portal'))
        body += (
            'Results can be submitted back to us securely via our lab portal:\n'
            f'{lab_portal_url}\n\n'
        )
    body += (
        f'Kind regards,\n{getattr(settings, "PRACTICE_NAME", "")}\n'
        f'{getattr(settings, "PRACTICE_PHONE", "")}'
    )

    email = EmailMessage(
        subject=f'{label} Request — {patient.first_name} {patient.last_name}',
        body=body,
        from_email=getattr(settings, 'PRACTICE_EMAIL', None) or settings.DEFAULT_FROM_EMAIL,
        to=[recipient],
    )
    email.attach(filename, buffer.read(), 'application/pdf')
    try:
        email.send()
        return JsonResponse({'success': True, 'email': recipient})
    except Exception as exc:
        return JsonResponse({'error': str(exc)}, status=500)


@doctor_required
@require_POST
def radiology_request_email(request, pk):
    return _send_request_email(request, pk, 'radiology')


@doctor_required
@require_POST
def lab_request_email(request, pk):
    return _send_request_email(request, pk, 'lab')


# ── Doctor review of submitted results (confirm / decline) ────────────────────

@doctor_required
def investigations_pending(request):
    pending = (InvestigationRequest.objects
               .filter(status='submitted')
               .select_related('consultation__patient', 'provider')
               .order_by('-submitted_at'))
    return render(request, 'consultations/investigations_pending.html', {'pending': pending})


@doctor_required
def investigation_review(request, pk):
    inv = get_object_or_404(
        InvestigationRequest.objects.select_related('consultation__patient', 'provider'), pk=pk)
    return render(request, 'consultations/investigation_review.html', {'inv': inv})


@doctor_required
@require_POST
def investigation_confirm(request, pk):
    inv = get_object_or_404(InvestigationRequest, pk=pk)
    # allow the doctor to edit / supply results inline (manual-entry fallback)
    result_text = request.POST.get('result_text')
    if result_text is not None:
        inv.result_text = result_text.strip()
    upload = request.FILES.get('result_file')
    if upload:
        inv.result_file = upload
    inv.status      = 'confirmed'
    inv.reviewed_at = timezone.now()
    inv.save()
    messages.success(request, f'{inv.get_kind_display()} results confirmed and filed for {inv.consultation.patient}.')
    return redirect('consultation_detail', pk=inv.consultation_id)


@doctor_required
@require_POST
def investigation_decline(request, pk):
    inv = get_object_or_404(InvestigationRequest, pk=pk)
    inv.status         = 'declined'
    inv.decline_reason = request.POST.get('decline_reason', '').strip()
    inv.reviewed_at    = timezone.now()
    inv.save(update_fields=['status', 'decline_reason', 'reviewed_at'])
    messages.info(request, f'{inv.get_kind_display()} results declined — the provider can resubmit.')
    return redirect('investigations_pending')


# ── Standard views ────────────────────────────────────────────────────────────

@login_required
def search_icd10(request):
    """
    AJAX: search ICD-10 codes by code prefix or description substring.
    Returns up to 12 matches ordered by code-prefix hits first.
    """
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse({'results': []})

    q_upper = q.upper()
    q_lower = q.lower()

    code_matches = []
    desc_matches = []

    for code, desc in ICD10_CODES:
        if code.upper().startswith(q_upper):
            code_matches.append({'code': code, 'description': desc})
        elif q_lower in desc.lower():
            desc_matches.append({'code': code, 'description': desc})

    results = (code_matches + desc_matches)[:12]
    return JsonResponse({'results': results})


@doctor_required
def suggest_prescriptions(request):
    """
    AJAX: given assessment text (and optional selected ICD-10 codes), return
    ranked prescription suggestions matched against ConditionPrescriptionLink.
    """
    import json as _json
    assessment = request.GET.get('assessment', '').strip()
    icd10_raw  = request.GET.get('icd10', '').strip()

    conditions = _parse_conditions(assessment)

    # Augment with descriptions from selected ICD-10 codes
    if icd10_raw:
        try:
            icd10_list = _json.loads(icd10_raw)
            for item in icd10_list:
                desc = item.get('description', '').strip()
                if len(desc) > 3 and desc not in conditions:
                    conditions.append(desc)
        except (ValueError, TypeError, AttributeError):
            pass

    if not conditions:
        if assessment:
            conditions = [assessment[:200]]
        else:
            return JsonResponse({'suggestions': []})

    # Build query: match any condition substring
    q = Q()
    for c in conditions:
        q |= Q(condition__icontains=c)

    links = (
        ConditionPrescriptionLink.objects
        .filter(q)
        .order_by('-count')
        .values('prescription', 'count', 'condition')[:30]
    )

    # Deduplicate by prescription text, keeping highest count
    seen = {}
    for link in links:
        rx = link['prescription']
        if rx not in seen or link['count'] > seen[rx]['count']:
            seen[rx] = link

    suggestions = sorted(seen.values(), key=lambda x: -x['count'])[:12]
    total_consultations = Consultation.objects.count()

    return JsonResponse({
        'suggestions': [
            {
                'prescription': s['prescription'],
                'count':        s['count'],
                'condition':    s['condition'],
            }
            for s in suggestions
        ],
        'total_consultations': total_consultations,
    })


# ── Referral providers (lab / radiology practices) ────────────────────────────

@login_required
def provider_list(request):
    providers = Provider.objects.all()
    return render(request, 'consultations/provider_list.html', {'providers': providers})


@login_required
def provider_create(request):
    form = ProviderForm(request.POST or None)
    if form.is_valid():
        provider = form.save()
        messages.success(request, f'Provider "{provider.name}" added.')
        return redirect('provider_list')
    return render(request, 'consultations/provider_form.html', {'form': form, 'title': 'Add Provider'})


@login_required
def provider_edit(request, pk):
    provider = get_object_or_404(Provider, pk=pk)
    form = ProviderForm(request.POST or None, instance=provider)
    if form.is_valid():
        form.save()
        messages.success(request, 'Provider updated.')
        return redirect('provider_list')
    return render(request, 'consultations/provider_form.html', {'form': form, 'title': 'Edit Provider'})


@doctor_required
def consultation_list(request):
    from django.db.models import Q
    q   = request.GET.get('q', '')
    tab = request.GET.get('tab', 'all')

    qs = Consultation.objects.select_related('patient').all()

    if tab == 'consultations':
        qs = qs.filter(reviewed_consultation__isnull=True)
    elif tab == 'reviews':
        qs = qs.filter(reviewed_consultation__isnull=False)

    if q:
        qs = qs.filter(
            Q(patient__first_name__icontains=q) |
            Q(patient__last_name__icontains=q) |
            Q(assessment__icontains=q)
        )

    counts = {
        'all':           Consultation.objects.count(),
        'consultations': Consultation.objects.filter(reviewed_consultation__isnull=True).count(),
        'reviews':       Consultation.objects.filter(reviewed_consultation__isnull=False).count(),
    }

    return render(request, 'consultations/consultation_list.html', {
        'consultations': qs,
        'q':      q,
        'tab':    tab,
        'counts': counts,
    })


def _diagnosis_snapshot_context(consultation):
    """Frozen diagnosis-reasoning snapshot for the details view. Prefers the
    confirmed run; falls back to the latest. Renders STORED output only —
    never a fresh engine run (the knowledge base is admin-editable, so
    re-computing could show different numbers than the doctor saw)."""
    snapshot = (consultation.differential_results.filter(confirmed_at__isnull=False).first()
                or consultation.differential_results.first())
    if snapshot is None:
        return {'diagnosis_snapshot': None}

    confirms, contras, seen = [], [], set()
    for r in snapshot.output.get('results', []):
        for f in r.get('breakdown', {}).get('history_factors', []):
            label = f.get('note') or f.get('factor') or ''
            key = (f.get('kind'), label, r.get('condition'))
            if key in seen:
                continue
            seen.add(key)
            delta = f.get('delta', 0)
            entry = f"{label} — {r.get('condition')} ({'+' if delta >= 0 else ''}{delta})"
            (confirms if f.get('kind') == 'confirming' else contras).append(entry)

    from diagnosis.models import Symptom
    names = dict(Symptom.objects.filter(
        id__in=snapshot.inputs.get('presenting_symptom_ids', []) +
               snapshot.inputs.get('working_symptom_ids', [])
    ).values_list('id', 'name'))
    return {
        'diagnosis_snapshot': snapshot,
        'xc_confirms': confirms,
        'xc_contras': contras,
        'snapshot_presenting': [names.get(i, '?') for i in snapshot.inputs.get('presenting_symptom_ids', [])],
        'snapshot_working': [names.get(i, '?') for i in snapshot.inputs.get('working_symptom_ids', [])],
    }


@doctor_required
def consultation_detail(request, pk):
    consultation = get_object_or_404(Consultation, pk=pk)
    _sync_investigation_requests(consultation)
    context = {
        'consultation': consultation,
        'providers':    Provider.objects.filter(is_active=True),
        'embed':        request.GET.get('embed'),
    }
    context.update(_diagnosis_snapshot_context(consultation))
    return render(request, 'consultations/consultation_detail.html', context)


@doctor_required
def consultation_create(request):
    """Start a consultation and land straight in the consultation workspace.

    With a known patient (patient_id and/or appointment_id) the Consultation
    row is created (or today's is reused — idempotent against double-clicks)
    and the doctor is redirected to the workspace immediately. With no
    patient, the blank workspace opens: the doctor picks the patient from
    its info bar and the preloaded consultation appears.
    """
    patient_id     = request.GET.get('patient_id')
    appointment_id = request.GET.get('appointment_id')

    apt = Appointment.objects.filter(pk=appointment_id).select_related('patient').first() if appointment_id else None
    patient = apt.patient if apt else (Patient.objects.filter(pk=patient_id).first() if patient_id else None)

    if patient:
        today = timezone.localdate()

        # Idempotent start: reuse the consultation already linked to this
        # appointment, or (patient-only start) today's appointment-less one.
        if apt:
            consultation = Consultation.objects.filter(appointment=apt).first()
        else:
            consultation = Consultation.objects.filter(
                patient=patient, date=today, appointment__isnull=True).first()

        if consultation is None:
            consultation = Consultation(
                patient=patient, appointment=apt,
                chief_complaint=(apt.reason if apt else '') or '')
            # Carry forward last visit's vitals as a starting point.
            last = Consultation.objects.filter(patient=patient).order_by('-date').first()
            if last:
                consultation.weight_kg  = last.weight_kg
                consultation.bp_reading = last.bp_reading
            consultation.save()

        # Vitals typed on the start picker override the carried-forward ones.
        wt = (request.GET.get('wt') or '').strip()
        bp = (request.GET.get('bp') or '').strip()
        if wt or bp:
            from decimal import Decimal, InvalidOperation
            if wt:
                try:
                    consultation.weight_kg = Decimal(wt)
                except InvalidOperation:
                    pass
            if bp:
                consultation.bp_reading = bp[:10]
            consultation.save(update_fields=['weight_kg', 'bp_reading'])

        if apt and apt.status == 'Checked In':
            apt.status = 'With Doctor'
            apt.save(update_fields=['status'])

        return redirect('diagnosis_workspace', consultation_pk=consultation.pk)

    # No patient yet — open the blank workspace; the doctor picks the patient there.
    return redirect('diagnosis_workspace_new')


@doctor_required
def consultation_edit(request, pk):
    consultation = get_object_or_404(Consultation, pk=pk)
    form = ConsultationForm(request.POST or None, instance=consultation)
    if form.is_valid():
        form.save()
        _sync_investigation_requests(consultation)
        messages.success(request, 'Consultation updated successfully.')
        return redirect('consultation_detail', pk=pk)
    return render(request, 'consultations/consultation_form.html', {'form': form, 'title': 'Edit Consultation'})


@doctor_required
def consultation_delete(request, pk):
    consultation = get_object_or_404(Consultation, pk=pk)
    if request.method == 'POST':
        patient_name = str(consultation.patient)
        consultation.delete()
        messages.success(request, f'Consultation deleted for {patient_name}.')
        return redirect('consultation_list')
    return render(request, 'consultations/confirm_delete.html', {'consultation': consultation})


@doctor_required
def consultation_review(request, pk):
    """Start a new review consultation linked to an existing one."""
    original = get_object_or_404(Consultation, pk=pk)

    if request.method == 'POST':
        review = Consultation(
            patient=original.patient,
            reviewed_consultation=original,
        )
        review.weight_kg      = request.POST.get('weight_kg') or None
        review.bp_reading     = request.POST.get('bp_reading') or None
        review.review         = request.POST.get('review') or None
        review.assessment     = request.POST.get('assessment') or None
        review.prescriptions  = request.POST.get('prescriptions') or None
        review.lab_requests   = request.POST.get('lab_requests') or None
        review.follow_up_date = request.POST.get('follow_up_date') or None
        review.save()
        _learn_from_consultation(review)
        _sync_investigation_requests(review)

        # Clear the patient from the waiting room queue
        from appointments.models import PendingReview
        today = timezone.localdate()
        pr = original.pending_reviews.filter(date=today).first()
        if pr:
            if pr.appointment and pr.appointment.status in ('Checked In', 'With Doctor'):
                pr.appointment.status = 'Completed'
                pr.appointment.save(update_fields=['status'])
            pr.status = 'completed'
            pr.save(update_fields=['status'])
        else:
            # Fallback: complete any checked-in appointment for this patient today
            Appointment.objects.filter(
                patient=original.patient,
                date=today,
                status__in=('Checked In', 'With Doctor'),
            ).update(status='Completed')

        messages.success(request, f'Review saved for {original.patient}.')
        return redirect('consultation_detail', pk=review.pk)

    if request.method == 'GET':
        from appointments.models import Appointment as Appt
        today = timezone.localdate()
        pr = original.pending_reviews.filter(date=today).first()
        if pr and pr.appointment and pr.appointment.status == 'Checked In':
            pr.appointment.status = 'With Doctor'
            pr.appointment.save(update_fields=['status'])

    last = Consultation.objects.filter(
        patient=original.patient
    ).order_by('-date').first()

    return render(request, 'consultations/consultation_review.html', {
        'original':    original,
        'last_weight': last.weight_kg  if last and last.weight_kg  else '',
        'last_bp':     last.bp_reading if last and last.bp_reading else '',
    })


@doctor_required
def consultation_print(request, pk):
    consultation = get_object_or_404(Consultation, pk=pk)
    return render(request, 'consultations/consultation_print.html', {'consultation': consultation})


# ── Sick note views ───────────────────────────────────────────────────────────

@doctor_required
def sick_note_pdf(request, pk):
    consultation = get_object_or_404(Consultation, pk=pk, sick_note_issued=True)
    buffer = _build_sick_note_pdf(consultation)
    patient_name = str(consultation.patient).replace(' ', '_')
    filename = f'SickNote_{patient_name}_{consultation.date}.pdf'
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@doctor_required
def sick_note_email(request, pk):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    consultation = get_object_or_404(Consultation, pk=pk, sick_note_issued=True)
    patient      = consultation.patient

    if not patient.email:
        return JsonResponse({'error': 'No email address on file for this patient.'}, status=400)

    buffer   = _build_sick_note_pdf(consultation)
    filename = f'SickNote_{str(patient).replace(" ", "_")}_{consultation.date}.pdf'

    from datetime import timedelta
    start = consultation.sick_note_start_date
    days  = consultation.sick_note_days or 1
    end   = start + timedelta(days=days - 1) if start else None
    fmt   = lambda d: d.strftime('%-d %B %Y') if d else '—'

    body = (
        f'Dear {patient.first_name},\n\n'
        f'Please find attached your medical certificate issued on {fmt(consultation.date)} '
        f'by {getattr(settings, "PRACTICE_NAME", "your doctor")}.\n\n'
        f'Certificate details:\n'
        f'  • Unfit for duty from: {fmt(start)}\n'
        f'  • Unfit for duty to:   {fmt(end)}\n'
        f'  • Duration:            {days} day{"s" if days != 1 else ""}\n'
    )
    if consultation.sick_note_employer:
        body += f'  • Employer/Institution: {consultation.sick_note_employer}\n'

    body += (
        f'\nThis certificate has been generated electronically and is valid as presented.\n\n'
        f'Kind regards,\n'
        f'{getattr(settings, "PRACTICE_NAME", "")}\n'
        f'{getattr(settings, "PRACTICE_PHONE", "")}'
    )

    email = EmailMessage(
        subject=f'Medical Certificate — {patient.first_name} {patient.last_name}',
        body=body,
        from_email=getattr(settings, 'PRACTICE_EMAIL', None) or settings.DEFAULT_FROM_EMAIL,
        to=[patient.email],
    )
    email.attach(filename, buffer.read(), 'application/pdf')

    try:
        email.send()
        return JsonResponse({'success': True, 'email': patient.email})
    except Exception as exc:
        return JsonResponse({'error': str(exc)}, status=500)
