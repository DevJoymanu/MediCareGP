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
        'title':                    req.title,
        'email':                    req.email,
        'alt_phone':                req.alt_phone,
        'occupation':               req.occupation,
        'home_language':            req.home_language,
        'marital_status':           req.marital_status,
        'employer':                 req.employer,
        'work_phone':               req.work_phone,
        'address':                  req.address,
        'residential_code':         req.residential_code,
        'postal_address':           req.postal_address,
        'postal_code':              req.postal_code,
        'responsible_surname':      req.responsible_surname,
        'responsible_first_name':   req.responsible_first_name,
        'responsible_title':        req.responsible_title,
        'responsible_id_number':    req.responsible_id_number,
        'responsible_email':        req.responsible_email,
        'responsible_tel_h':        req.responsible_tel_h,
        'responsible_tel_w':        req.responsible_tel_w,
        'responsible_cell':         req.responsible_cell,
        'work_address':             req.work_address,
        'work_code':                req.work_code,
        'blood_type':               req.blood_type,
        'medical_aid_name':         req.medical_aid_name,
        'medical_aid_plan':         req.medical_aid_plan,
        'medical_aid_number':       req.medical_aid_number,
        'principal_member_name':    req.principal_member_name,
        'principal_member_id':      req.principal_member_id,
        'dependant_code':           req.dependant_code,
        'allergies':                req.allergies,
        'chronic_conditions':       req.chronic_conditions,
        'current_medication':       req.current_medication,
        'previous_surgeries':       req.previous_surgeries,
        'family_history':           req.family_history,
        'smoking_status':           req.smoking_status,
        'alcohol_use':              req.alcohol_use,
        'substance_use':            req.substance_use,
        'next_of_kin_name':         req.next_of_kin_name,
        'next_of_kin_relationship': req.next_of_kin_relationship,
        'next_of_kin_address':      req.next_of_kin_address,
        'next_of_kin_phone':        req.next_of_kin_phone,
        'next_of_kin_email':        req.next_of_kin_email,
        'referred_by_name':         req.referred_by_name,
        'referred_by_phone':        req.referred_by_phone,
        'referred_by_email':        req.referred_by_email,
        'consent_to_treat':         req.consent_to_treat,
    }
    for field, value in mapping.items():
        if value and not getattr(patient, field, None):
            setattr(patient, field, value)
            updated.append(field)
    if updated:
        patient.save(update_fields=updated)


def _save_phase2_fields(req, post_data, complete=False):
    """Persist any phase 2 fields present in this request."""
    text_fields = [
        'title',
        'email',
        'alt_phone',
        'occupation',
        'home_language',
        'marital_status',
        'employer',
        'work_phone',
        'address',
        'residential_code',
        'postal_address',
        'postal_code',
        'responsible_surname',
        'responsible_first_name',
        'responsible_title',
        'responsible_id_number',
        'responsible_email',
        'responsible_tel_h',
        'responsible_tel_w',
        'responsible_cell',
        'work_address',
        'work_code',
        'blood_type',
        'medical_aid_name',
        'medical_aid_plan',
        'medical_aid_number',
        'principal_member_name',
        'principal_member_id',
        'dependant_code',
        'allergies',
        'chronic_conditions',
        'current_medication',
        'previous_surgeries',
        'family_history',
        'smoking_status',
        'alcohol_use',
        'substance_use',
        'next_of_kin_name',
        'next_of_kin_relationship',
        'next_of_kin_address',
        'next_of_kin_phone',
        'next_of_kin_email',
        'referred_by_name',
        'referred_by_phone',
        'referred_by_email',
    ]
    updated = []

    for field in text_fields:
        if field in post_data:
            setattr(req, field, post_data.get(field, '').strip())
            updated.append(field)

    if 'consent_to_treat' in post_data or complete:
        req.consent_to_treat = post_data.get('consent_to_treat') == 'on'
        updated.append('consent_to_treat')

    if complete:
        req.phase2_completed = True
        updated.append('phase2_completed')

    if updated:
        req.save(update_fields=updated)
    return updated


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
    if req.is_new_patient:
        # New patients: prompt them to complete their profile, then lands on complete.html
        return render(request, 'checkin/confirmation.html', {
            'req': req,
            'practice_name': settings.PRACTICE_NAME,
            'phase2_url': f'/checkin/phase2/{req.phase2_token}/',
        })
    # Returning patients: go straight to the thank-you screen
    return render(request, 'checkin/complete.html', {
        'name':          req.display_name.split()[0],
        'practice_name': settings.PRACTICE_NAME,
        'is_new':        False,
    })


def checkin_phase2(request, phase2_token):
    req = get_object_or_404(CheckInRequest, phase2_token=phase2_token, is_new_patient=True)

    if req.status == 'expired':
        return render(request, 'checkin/blocked.html', {'reason': 'expired'})

    saved = False
    if request.method == 'POST':
        _save_phase2_fields(req, request.POST, complete=True)
        if req.patient:
            _update_patient_from_checkin(req.patient, req)
        return redirect('checkin_phase2_done', phase2_token=req.phase2_token)

    return render(request, 'checkin/phase2.html', {
        'req': req,
        'practice_name': settings.PRACTICE_NAME,
        'blood_types': ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'],
    })


@require_POST
def checkin_phase2_save(request, phase2_token):
    """Save one phase 2 page without marking the profile complete."""
    req = get_object_or_404(CheckInRequest, phase2_token=phase2_token, is_new_patient=True)

    if req.status == 'expired':
        return JsonResponse({'success': False, 'error': 'expired'}, status=410)

    updated = _save_phase2_fields(req, request.POST, complete=False)
    if req.patient:
        _update_patient_from_checkin(req.patient, req)
    return JsonResponse({'success': True, 'updated': updated})


def checkin_phase2_done(request, phase2_token):
    """Final thank-you screen after phase 2 profile completion."""
    req = get_object_or_404(CheckInRequest, phase2_token=phase2_token)
    return render(request, 'checkin/complete.html', {
        'name':          req.first_name or req.display_name,
        'practice_name': settings.PRACTICE_NAME,
        'is_new':        req.is_new_patient,
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
                title=req.title or None,
                email=req.email or None,
                alt_phone=req.alt_phone or None,
                work_phone=req.work_phone or None,
                occupation=req.occupation or None,
                home_language=req.home_language or None,
                marital_status=req.marital_status or None,
                address=req.address or '',
                residential_code=req.residential_code or None,
                postal_address=req.postal_address or None,
                postal_code=req.postal_code or None,
                responsible_surname=req.responsible_surname or None,
                responsible_first_name=req.responsible_first_name or None,
                responsible_title=req.responsible_title or None,
                responsible_id_number=req.responsible_id_number or None,
                responsible_email=req.responsible_email or None,
                responsible_tel_h=req.responsible_tel_h or None,
                responsible_tel_w=req.responsible_tel_w or None,
                responsible_cell=req.responsible_cell or None,
                employer=req.employer or None,
                work_address=req.work_address or None,
                work_code=req.work_code or None,
                blood_type=req.blood_type or None,
                medical_aid_name=req.medical_aid_name or None,
                medical_aid_plan=req.medical_aid_plan or None,
                medical_aid_number=req.medical_aid_number or None,
                principal_member_name=req.principal_member_name or None,
                principal_member_id=req.principal_member_id or None,
                dependant_code=req.dependant_code or None,
                allergies=req.allergies or None,
                chronic_conditions=req.chronic_conditions or None,
                current_medication=req.current_medication or None,
                previous_surgeries=req.previous_surgeries or None,
                family_history=req.family_history or None,
                smoking_status=req.smoking_status or None,
                alcohol_use=req.alcohol_use or None,
                substance_use=req.substance_use or None,
                next_of_kin_name=req.next_of_kin_name or None,
                next_of_kin_relationship=req.next_of_kin_relationship or None,
                next_of_kin_address=req.next_of_kin_address or None,
                next_of_kin_phone=req.next_of_kin_phone or None,
                next_of_kin_email=req.next_of_kin_email or None,
                referred_by_name=req.referred_by_name or None,
                referred_by_phone=req.referred_by_phone or None,
                referred_by_email=req.referred_by_email or None,
                popia_consent=req.popia_consent,
                consent_to_treat=req.consent_to_treat,
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
                        title=req.title or None,
                        email=req.email or None,
                        alt_phone=req.alt_phone or None,
                        work_phone=req.work_phone or None,
                        occupation=req.occupation or None,
                        home_language=req.home_language or None,
                        marital_status=req.marital_status or None,
                        address=req.address or None,
                        residential_code=req.residential_code or None,
                        postal_address=req.postal_address or None,
                        postal_code=req.postal_code or None,
                        responsible_surname=req.responsible_surname or None,
                        responsible_first_name=req.responsible_first_name or None,
                        responsible_title=req.responsible_title or None,
                        responsible_id_number=req.responsible_id_number or None,
                        responsible_email=req.responsible_email or None,
                        responsible_tel_h=req.responsible_tel_h or None,
                        responsible_tel_w=req.responsible_tel_w or None,
                        responsible_cell=req.responsible_cell or None,
                        employer=req.employer or None,
                        work_address=req.work_address or None,
                        work_code=req.work_code or None,
                        blood_type=req.blood_type or None,
                        medical_aid_name=req.medical_aid_name or None,
                        medical_aid_plan=req.medical_aid_plan or None,
                        medical_aid_number=req.medical_aid_number or None,
                        principal_member_name=req.principal_member_name or None,
                        principal_member_id=req.principal_member_id or None,
                        dependant_code=req.dependant_code or None,
                        allergies=req.allergies or None,
                        chronic_conditions=req.chronic_conditions or None,
                        current_medication=req.current_medication or None,
                        previous_surgeries=req.previous_surgeries or None,
                        family_history=req.family_history or None,
                        smoking_status=req.smoking_status or None,
                        alcohol_use=req.alcohol_use or None,
                        substance_use=req.substance_use or None,
                        next_of_kin_name=req.next_of_kin_name or None,
                        next_of_kin_relationship=req.next_of_kin_relationship or None,
                        next_of_kin_address=req.next_of_kin_address or None,
                        next_of_kin_phone=req.next_of_kin_phone or None,
                        next_of_kin_email=req.next_of_kin_email or None,
                        referred_by_name=req.referred_by_name or None,
                        referred_by_phone=req.referred_by_phone or None,
                        referred_by_email=req.referred_by_email or None,
                        popia_consent=req.popia_consent,
                        consent_to_treat=req.consent_to_treat,
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
