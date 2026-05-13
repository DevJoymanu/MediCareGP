import io
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from appointments.models import Appointment
from patients.models import Patient
from .models import Consultation, ConditionPrescriptionLink
from .forms import ConsultationForm


# ── Prescription suggestion helpers ──────────────────────────────────────────

def _parse_conditions(text):
    """Split an assessment field into individual condition strings."""
    import re
    if not text:
        return []
    # Split on newline, comma, semicolon, or numbered list markers
    parts = re.split(r'[\n,;]|\d+\.', text)
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


# ── Standard views ────────────────────────────────────────────────────────────

@login_required
def suggest_prescriptions(request):
    """
    AJAX: given assessment text, return ranked prescription suggestions.
    Matches against ConditionPrescriptionLink using the conditions parsed
    from the assessment field.
    """
    assessment = request.GET.get('assessment', '').strip()
    if not assessment:
        return JsonResponse({'suggestions': []})

    conditions = _parse_conditions(assessment)
    if not conditions:
        # Fallback: treat whole assessment as one condition
        conditions = [assessment[:200]]

    # Build query: match any condition substring
    q = Q()
    for c in conditions:
        q |= Q(condition__icontains=c)

    links = (
        ConditionPrescriptionLink.objects
        .filter(q)
        .order_by('-count')
        .values('prescription', 'count', 'condition')[:10]
    )

    # Deduplicate by prescription text, keeping highest count
    seen = {}
    for link in links:
        rx = link['prescription']
        if rx not in seen or link['count'] > seen[rx]['count']:
            seen[rx] = link

    suggestions = sorted(seen.values(), key=lambda x: -x['count'])[:6]
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


@login_required
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


@login_required
def consultation_detail(request, pk):
    consultation = get_object_or_404(Consultation, pk=pk)
    return render(request, 'consultations/consultation_detail.html', {'consultation': consultation})


@login_required
def consultation_create(request):
    initial = {}
    patient_id     = request.GET.get('patient_id')
    appointment_id = request.GET.get('appointment_id')

    resolved_patient = None

    if appointment_id:
        apt = Appointment.objects.filter(pk=appointment_id).first()
        if apt:
            initial['appointment']    = apt.pk
            initial['patient']        = apt.patient.pk
            initial['chief_complaint'] = apt.reason
            resolved_patient = apt.patient
            if request.method == 'GET' and apt.status == 'Checked In':
                apt.status = 'With Doctor'
                apt.save(update_fields=['status'])

    if patient_id and not resolved_patient:
        resolved_patient = Patient.objects.filter(pk=patient_id).first()
        if resolved_patient:
            initial['patient'] = resolved_patient.pk

    if resolved_patient:
        last = Consultation.objects.filter(
            patient=resolved_patient
        ).order_by('-date').first()
        if last:
            if last.weight_kg:
                initial['weight_kg']  = last.weight_kg
            if last.bp_reading:
                initial['bp_reading'] = last.bp_reading

    form = ConsultationForm(request.POST or None, initial=initial)
    if form.is_valid():
        consultation = form.save()
        today = timezone.localdate()
        if consultation.appointment and consultation.appointment.status in ('Checked In', 'With Doctor'):
            consultation.appointment.status = 'Completed'
            consultation.appointment.save(update_fields=['status'])
        else:
            # Fallback: complete any checked-in appointment for this patient today
            Appointment.objects.filter(
                patient=consultation.patient,
                date=today,
                status__in=('Checked In', 'With Doctor'),
            ).update(status='Completed')
        _learn_from_consultation(consultation)
        messages.success(request, f'Consultation saved for {consultation.patient}.')
        return redirect('consultation_detail', pk=consultation.pk)

    return render(request, 'consultations/consultation_form.html', {'form': form, 'title': 'New Consultation'})


@login_required
def consultation_edit(request, pk):
    consultation = get_object_or_404(Consultation, pk=pk)
    form = ConsultationForm(request.POST or None, instance=consultation)
    if form.is_valid():
        form.save()
        messages.success(request, 'Consultation updated successfully.')
        return redirect('consultation_detail', pk=pk)
    return render(request, 'consultations/consultation_form.html', {'form': form, 'title': 'Edit Consultation'})


@login_required
def consultation_delete(request, pk):
    consultation = get_object_or_404(Consultation, pk=pk)
    if request.method == 'POST':
        patient_name = str(consultation.patient)
        consultation.delete()
        messages.success(request, f'Consultation deleted for {patient_name}.')
        return redirect('consultation_list')
    return render(request, 'consultations/confirm_delete.html', {'consultation': consultation})


@login_required
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


@login_required
def consultation_print(request, pk):
    consultation = get_object_or_404(Consultation, pk=pk)
    return render(request, 'consultations/consultation_print.html', {'consultation': consultation})


# ── Sick note views ───────────────────────────────────────────────────────────

@login_required
def sick_note_pdf(request, pk):
    consultation = get_object_or_404(Consultation, pk=pk, sick_note_issued=True)
    buffer = _build_sick_note_pdf(consultation)
    patient_name = str(consultation.patient).replace(' ', '_')
    filename = f'SickNote_{patient_name}_{consultation.date}.pdf'
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
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
