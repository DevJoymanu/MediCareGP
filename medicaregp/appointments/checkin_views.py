import io
import base64
from datetime import datetime

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt  # noqa: F401 (kept for reference)
from django.views.decorators.http import require_POST

from patients.models import Patient
from .models import Appointment, CheckInRequest
from .checkin_utils import (
    check_id_rate_limit,
    check_ip_rate_limit,
    expire_old_requests,
    generate_daily_token,
    get_client_ip,
    validate_daily_token,
    validate_geolocation,
)


def _token_valid(token):
    return token == settings.CHECKIN_URL_TOKEN


# ── Helpers ───────────────────────────────────────────────────────────────────

def _update_patient_from_checkin(patient, req):
    """Fill in any blank patient fields from a CheckInRequest (phase 2 data)."""
    updated = []
    mapping = {
        'address':           req.address,
        'medical_aid_name':  req.medical_aid_name,
        'medical_aid_number':req.medical_aid_number,
        'allergies':         req.allergies,
        'chronic_conditions':req.chronic_conditions,
        'next_of_kin_name':  req.next_of_kin_name,
        'next_of_kin_phone': req.next_of_kin_phone,
        'blood_type':        req.blood_type,
    }
    for field, value in mapping.items():
        if value and not getattr(patient, field):
            setattr(patient, field, value)
            updated.append(field)
    if updated:
        patient.save(update_fields=updated)


# ── Public views (no login required) ─────────────────────────────────────────

def checkin_form(request, token):
    if not _token_valid(token):
        return render(request, 'checkin/blocked.html', {'reason': 'invalid_token'}, status=404)

    error = None

    if request.method == 'POST':
        # Security checks
        if request.POST.get('website'):  # honeypot
            return render(request, 'checkin/confirmation.html', {})  # silent drop

        if not validate_daily_token(request.POST.get('daily_token')):
            return render(request, 'checkin/blocked.html', {'reason': 'expired'})

        ip = get_client_ip(request)
        if not check_ip_rate_limit(ip):
            return render(request, 'checkin/blocked.html', {'reason': 'rate_limit'})

        id_number = request.POST.get('id_number', '').strip().upper()
        if not id_number:
            error = 'Please enter your ID or passport number.'
        else:
            if not check_id_rate_limit(id_number):
                return render(request, 'checkin/blocked.html', {'reason': 'rate_limit'})

            lat = _safe_float(request.POST.get('latitude'))
            lng = _safe_float(request.POST.get('longitude'))
            if not validate_geolocation(lat, lng):
                return render(request, 'checkin/blocked.html', {'reason': 'location'})

            # Expire stale requests before processing
            expire_old_requests()

            existing = Patient.objects.filter(id_number__iexact=id_number).first()
            is_new = existing is None
            reason = request.POST.get('reason_for_visit', '').strip()

            if not reason:
                error = 'Please describe your reason for visiting.'
            elif is_new:
                first_name = request.POST.get('first_name', '').strip()
                last_name  = request.POST.get('last_name', '').strip()
                dob_str    = request.POST.get('date_of_birth', '').strip()
                phone      = request.POST.get('phone_number', '').strip()
                gender     = request.POST.get('gender', '').strip()
                popia      = request.POST.get('popia_consent') == 'on'

                # Build date from hidden field or individual DD/MM/YYYY inputs
                if not dob_str:
                    dd   = request.POST.get('dob_dd',   '').strip()
                    mm   = request.POST.get('dob_mm',   '').strip()
                    yyyy = request.POST.get('dob_yyyy', '').strip()
                    if dd and mm and yyyy:
                        dob_str = f"{yyyy}-{mm.zfill(2)}-{dd.zfill(2)}"

                if not all([first_name, last_name, dob_str, phone, gender]):
                    error = 'Please fill in all required fields.'
                elif not popia:
                    error = 'Please accept the POPIA consent to continue.'
                else:
                    try:
                        dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
                    except ValueError:
                        error = 'Please enter a valid date of birth.'

                    if not error:
                        req = CheckInRequest.objects.create(
                            id_number=id_number,
                            first_name=first_name,
                            last_name=last_name,
                            date_of_birth=dob,
                            phone_number=phone,
                            gender=gender,
                            popia_consent=popia,
                            reason_for_visit=reason,
                            is_new_patient=True,
                            ip_address=ip,
                            latitude=lat,
                            longitude=lng,
                            daily_token=request.POST.get('daily_token', ''),
                        )
                        return redirect('checkin_confirmation', token=token, pk=req.pk)
            else:
                req = CheckInRequest.objects.create(
                    id_number=id_number,
                    reason_for_visit=reason,
                    is_new_patient=False,
                    patient=existing,
                    ip_address=ip,
                    latitude=lat,
                    longitude=lng,
                    daily_token=request.POST.get('daily_token', ''),
                )
                return redirect('checkin_confirmation', token=token, pk=req.pk)

    return render(request, 'checkin/form.html', {
        'daily_token': generate_daily_token(),
        'token': token,
        'error': error,
        'geolocation_enabled': settings.CHECKIN_GEOLOCATION_ENABLED,
        'practice_name': settings.PRACTICE_NAME,
    })


def checkin_lookup(request, token):
    """AJAX: returns patient record and any pending review for today."""
    if not _token_valid(token):
        return JsonResponse({'found': False})
    id_number = request.GET.get('id', '').strip().upper()
    if not id_number:
        return JsonResponse({'found': False})

    patient = Patient.objects.filter(id_number__iexact=id_number).first()
    if not patient:
        return JsonResponse({'found': False})

    from .models import PendingReview
    today = timezone.localdate()
    pr = PendingReview.objects.filter(
        consultation__patient=patient,
        date=today,
        status='pending',
    ).select_related('consultation').first()

    if pr:
        return JsonResponse({
            'found':         True,
            'name':          patient.first_name,
            'has_review':    True,
            'review_pk':     pr.pk,
            'review_for':    pr.consultation.assessment or '',
            'original_date': pr.consultation.date.strftime('%-d %B %Y'),
        })

    return JsonResponse({'found': True, 'name': patient.first_name, 'has_review': False})


def checkin_review_confirm(request, token, pk):
    """Patient self-confirms arrival for a scheduled review."""
    if not _token_valid(token):
        return render(request, 'checkin/blocked.html', {'reason': 'invalid_token'}, status=404)

    from .models import PendingReview
    pr = get_object_or_404(PendingReview, pk=pk, status='pending')

    if request.method == 'POST':
        pr.status = 'self_arrived'
        pr.save(update_fields=['status'])
        return render(request, 'checkin/review_confirmed.html', {
            'patient':       pr.consultation.patient,
            'practice_name': settings.PRACTICE_NAME,
        })

    return redirect('checkin_form', token=token)


def checkin_confirmation(request, token, pk):
    if not _token_valid(token):
        return render(request, 'checkin/blocked.html', {'reason': 'invalid_token'}, status=404)
    req = get_object_or_404(CheckInRequest, pk=pk)
    return render(request, 'checkin/confirmation.html', {
        'req': req,
        'practice_name': settings.PRACTICE_NAME,
        'phase2_url': f'/checkin/phase2/{req.phase2_token}/',
    })


def checkin_phase2(request, phase2_token):
    req = get_object_or_404(CheckInRequest, phase2_token=phase2_token, is_new_patient=True)

    if req.status == 'expired':
        return render(request, 'checkin/blocked.html', {'reason': 'expired'})

    saved = False
    if request.method == 'POST':
        req.address            = request.POST.get('address', '').strip()
        req.blood_type         = request.POST.get('blood_type', '').strip()
        req.medical_aid_name   = request.POST.get('medical_aid_name', '').strip()
        req.medical_aid_number = request.POST.get('medical_aid_number', '').strip()
        req.allergies          = request.POST.get('allergies', '').strip()
        req.chronic_conditions = request.POST.get('chronic_conditions', '').strip()
        req.next_of_kin_name   = request.POST.get('next_of_kin_name', '').strip()
        req.next_of_kin_phone  = request.POST.get('next_of_kin_phone', '').strip()
        req.phase2_completed   = True
        req.save()
        # If the patient was already accepted, update their record now
        if req.patient:
            _update_patient_from_checkin(req.patient, req)
        saved = True

    return render(request, 'checkin/phase2.html', {
        'req': req,
        'saved': saved,
        'practice_name': settings.PRACTICE_NAME,
        'blood_types': ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'],
    })


# ── Staff-only views (login required) ────────────────────────────────────────

@login_required
def checkin_pending_json(request):
    expire_old_requests()
    pending = CheckInRequest.objects.filter(status='pending').select_related('patient')
    data = []
    for req in pending:
        data.append({
            'pk':           req.pk,
            'display_name': req.display_name,
            'id_number':    req.id_number,
            'reason':       req.reason_for_visit,
            'is_new':       req.is_new_patient,
            'minutes_ago':  req.minutes_ago,
        })
    return JsonResponse({'pending': data, 'count': len(data)})


@login_required
@require_POST
def checkin_accept(request, pk):
    req = get_object_or_404(CheckInRequest, pk=pk, status='pending')

    if req.is_new_patient:
        try:
            patient = Patient.objects.create(
                id_number=req.id_number,
                first_name=req.first_name,
                last_name=req.last_name,
                date_of_birth=req.date_of_birth,
                phone=req.phone_number,
                gender=req.gender or 'O',
                address=req.address or '',
                blood_type=req.blood_type or None,
                medical_aid_name=req.medical_aid_name or None,
                medical_aid_number=req.medical_aid_number or None,
                allergies=req.allergies or None,
                chronic_conditions=req.chronic_conditions or None,
                next_of_kin_name=req.next_of_kin_name or None,
                next_of_kin_phone=req.next_of_kin_phone or None,
                popia_consent=req.popia_consent,
                consent_to_treat=True,
            )
        except IntegrityError:
            # Patient already exists — update with any new phase 2 data
            patient = Patient.objects.get(id_number__iexact=req.id_number)
            _update_patient_from_checkin(patient, req)
        req.patient = patient
    else:
        patient = req.patient
        # Returning patient — still update with any new phase 2 data submitted
        _update_patient_from_checkin(patient, req)

    now = timezone.localtime()
    Appointment.objects.create(
        patient=patient,
        date=now.date(),
        time=now.time().replace(second=0, microsecond=0),
        reason=req.reason_for_visit,
        status='Checked In',
        visit_type='Walk-In',
    )

    req.status = 'accepted'
    req.save(update_fields=['status', 'patient'])

    return JsonResponse({'success': True, 'patient_name': str(patient)})


@login_required
@require_POST
def checkin_decline(request, pk):
    req = get_object_or_404(CheckInRequest, pk=pk, status='pending')
    req.status = 'declined'
    req.save(update_fields=['status'])
    return JsonResponse({'success': True})


@login_required
def checkin_edit(request, pk):
    """Staff: view and edit a pending check-in request before accepting."""
    req = get_object_or_404(CheckInRequest, pk=pk, status='pending')

    if request.method == 'POST':
        # Save edits
        req.reason_for_visit = request.POST.get('reason_for_visit', req.reason_for_visit).strip()
        if req.is_new_patient:
            req.first_name   = request.POST.get('first_name', req.first_name).strip()
            req.last_name    = request.POST.get('last_name', req.last_name).strip()
            req.phone_number = request.POST.get('phone_number', req.phone_number).strip()
            req.gender       = request.POST.get('gender', req.gender)
            dob_str = request.POST.get('date_of_birth', '').strip()
            if dob_str:
                try:
                    req.date_of_birth = datetime.strptime(dob_str, '%Y-%m-%d').date()
                except ValueError:
                    pass
        req.save()

        if request.POST.get('action') == 'accept':
            # Inline accept after editing
            if req.is_new_patient:
                try:
                    patient = Patient.objects.create(
                        id_number=req.id_number,
                        first_name=req.first_name,
                        last_name=req.last_name,
                        date_of_birth=req.date_of_birth,
                        phone=req.phone_number,
                        gender=req.gender or 'O',
                        address=req.address or None,
                        blood_type=req.blood_type or None,
                        medical_aid_name=req.medical_aid_name or None,
                        medical_aid_number=req.medical_aid_number or None,
                        allergies=req.allergies or None,
                        chronic_conditions=req.chronic_conditions or None,
                        next_of_kin_name=req.next_of_kin_name or None,
                        next_of_kin_phone=req.next_of_kin_phone or None,
                        popia_consent=req.popia_consent,
                        consent_to_treat=True,
                    )
                except IntegrityError:
                    patient = Patient.objects.get(id_number__iexact=req.id_number)
                req.patient = patient
            else:
                patient = req.patient

            now = timezone.localtime()
            Appointment.objects.create(
                patient=patient,
                date=now.date(),
                time=now.time().replace(second=0, microsecond=0),
                reason=req.reason_for_visit,
                status='Checked In',
                visit_type='Walk-In',
            )
            req.status = 'accepted'
            req.save(update_fields=['status', 'patient'])
            from django.contrib import messages
            messages.success(request, f'{req.display_name} checked in and added to the waiting room.')

        return redirect('waiting_room')

    return render(request, 'checkin/edit_request.html', {'req': req})


@login_required
def checkin_qr_page(request):
    import qrcode
    token = settings.CHECKIN_URL_TOKEN
    url = request.build_absolute_uri(f'/checkin/{token}/')

    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')

    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    qr_b64 = base64.b64encode(buffer.getvalue()).decode()

    return render(request, 'checkin/qr_page.html', {
        'qr_b64': qr_b64,
        'checkin_url': url,
        'practice_name': settings.PRACTICE_NAME,
    })


# ── Helpers ───────────────────────────────────────────────────────────────────

def _safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
