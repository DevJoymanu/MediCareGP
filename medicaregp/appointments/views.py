from urllib.parse import quote

from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.utils import timezone
from .models import Appointment, WebBooking, VideoRoom
from .forms import AppointmentForm, WalkInForm


# ── Online consultation (Doxy.me) helpers ─────────────────────────────────────

def _wa_link(phone, message):
    """A wa.me click-to-chat link to the patient's number, or '' if no number."""
    digits = ''.join(c for c in (phone or '') if c.isdigit())
    if digits.startswith('0'):
        digits = '27' + digits[1:]
    return f"https://wa.me/{digits}?text={quote(message)}" if digits else ''


def _appointment_is_online(appointment):
    try:
        if appointment.web_booking.appointment_type == settings.ONLINE_CONSULT_TYPE:
            return True
    except WebBooking.DoesNotExist:
        pass
    return 'online' in (appointment.reason or '').lower()

@login_required
def appointment_list(request):
    appointments = Appointment.objects.select_related('patient').all()
    status = request.GET.get('status','')
    date = request.GET.get('date','')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if status:
        appointments = appointments.filter(status=status)
    if date:
        appointments = appointments.filter(date=date)
    if date_from:
        appointments = appointments.filter(date__gte=date_from)
    if date_to:
        appointments = appointments.filter(date__lte=date_to)
    return render(request, 'appointments/appointment_list.html', {
        'appointments': appointments,
        'status': status,
        'date': date,
        'date_from': date_from,
        'date_to': date_to,
    })

@login_required
def appointment_detail(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    ctx = {'appointment': appointment}
    if _appointment_is_online(appointment):
        room, _ = VideoRoom.objects.get_or_create(appointment=appointment)
        patient_url = request.build_absolute_uri(
            reverse('video_patient_room', args=[room.patient_token]))
        msg = (f"Hi {appointment.patient.first_name}, here is your private video consultation link "
               f"for {appointment.date:%d %b %Y} at {appointment.time:%H:%M}: {patient_url}\n\n"
               f"Open it at your appointment time — it works in your browser, no app or login needed.")
        ctx.update({
            'is_online_consult': True,
            'video_doctor_url':  reverse('video_doctor_room', args=[appointment.pk]),
            'video_patient_url': patient_url,
            'video_wa_link':     _wa_link(appointment.patient.phone, msg),
        })
    return render(request, 'appointments/appointment_detail.html', ctx)

@login_required
def appointment_create(request):
    initial = {'date': timezone.localdate()}
    patient_id = request.GET.get('patient_id')
    if patient_id:
        initial['patient'] = patient_id
        # Pre-fill referring doctor from patient's last appointment if available
        last_apt = Appointment.objects.filter(patient_id=patient_id).order_by('-date').first()
        if last_apt and last_apt.referring_doctor:
            initial['referring_doctor'] = last_apt.referring_doctor
    form = AppointmentForm(request.POST or None, initial=initial)
    if form.is_valid():
        appointment = form.save()
        messages.success(request, f'Appointment scheduled for {appointment.patient}.')
        return redirect('appointment_list')
    return render(request, 'appointments/appointment_form.html', {'form':form,'title':'New Appointment'})

@login_required
def appointment_edit(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    form = AppointmentForm(request.POST or None, instance=appointment)
    if form.is_valid():
        form.save()
        messages.success(request, 'Appointment updated successfully.')
        return redirect('appointment_detail', pk=pk)
    return render(request, 'appointments/appointment_form.html', {'form':form,'title':'Edit Appointment'})

@login_required
def appointment_set_status(request, pk):
    if request.method == 'POST':
        appointment = get_object_or_404(Appointment, pk=pk)
        new_status = request.POST.get('status', '')
        if new_status in [s for s, _ in Appointment.STATUS_CHOICES]:
            appointment.status = new_status
            appointment.save(update_fields=['status'])
            messages.success(request, f'Status updated to {new_status}.')
    return redirect('appointment_detail', pk=pk)

@login_required
def appointment_cancel(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    if request.method == 'POST':
        appointment.status = 'Cancelled'
        appointment.save(update_fields=['status'])
        messages.success(request, 'Appointment cancelled.')
        return redirect('appointment_detail', pk=pk)
    return render(request, 'appointments/confirm_cancel.html', {'appointment': appointment})

@login_required
def appointment_delete(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    if request.method == 'POST':
        patient_name = str(appointment.patient)
        appointment.delete()
        messages.success(request, f'Appointment deleted for {patient_name}.')
        return redirect('appointment_list')
    return render(request, 'appointments/confirm_delete.html', {'appointment': appointment})

@login_required
def walk_in_create(request):
    initial = {}
    patient_id = request.GET.get('patient_id')
    if patient_id:
        initial['patient'] = patient_id
    form = WalkInForm(request.POST or None, initial=initial)
    if form.is_valid():
        appt = form.save(commit=False)
        now = timezone.localtime()
        appt.date = now.date()
        appt.time = now.time().replace(second=0, microsecond=0)
        appt.visit_type = 'Walk-In'
        appt.status = 'Checked In'
        appt.save()
        messages.success(request, f'{appt.patient} added to the waiting room.')
        return redirect('waiting_room')
    return render(request, 'appointments/walk_in_form.html', {'form': form})

@login_required
def waiting_room(request):
    from consultations.models import Consultation
    from .models import PendingReview
    today = timezone.localdate()

    # Auto-create PendingReview records for any follow-ups due today
    due = Consultation.objects.filter(follow_up_date=today).select_related('patient')
    for c in due:
        PendingReview.objects.get_or_create(consultation=c, date=today)

    pending_reviews = (PendingReview.objects
                       .filter(date=today, status__in=['pending', 'self_arrived'])
                       .select_related('consultation__patient', 'consultation'))

    in_consultation = (Appointment.objects
                       .filter(date=today, status='With Doctor')
                       .select_related('patient', 'pending_review__consultation')
                       .order_by('time')
                       .first())
    waiting = (Appointment.objects
               .filter(date=today, status='Checked In')
               .select_related('patient')
               .order_by('time'))
    scheduled = (Appointment.objects
                 .filter(date=today, status='Scheduled')
                 .select_related('patient')
                 .order_by('time'))
    from .models import CheckInRequest
    reviews_pending = pending_reviews.filter(status='pending').count()
    reviews_arrived = pending_reviews.filter(status='self_arrived').count()

    return render(request, 'appointments/waiting_room.html', {
        'in_consultation': in_consultation,
        'waiting':         waiting,
        'scheduled':       scheduled,
        'pending_reviews': pending_reviews,
        'today':           today,
        'init_reviews_pending': reviews_pending,
        'init_reviews_arrived': reviews_arrived,
        'init_checkins':        CheckInRequest.objects.filter(status='pending').count(),
    })


@login_required
def pending_review_queue(request, pk):
    from .models import PendingReview
    pr = get_object_or_404(PendingReview, pk=pk)
    if request.method == 'POST':
        appt = Appointment.objects.create(
            patient=pr.consultation.patient,
            date=timezone.localdate(),
            time=timezone.localtime().time(),
            reason=f'Review — follow-up from {pr.consultation.date}',
            status='Checked In',
            visit_type='Walk-In',
        )
        pr.status = 'queued'
        pr.appointment = appt
        pr.save(update_fields=['status', 'appointment'])
        messages.success(request, f'{pr.consultation.patient} added to the waiting room queue.')
    return redirect('waiting_room')


@login_required
def pending_review_move(request, pk):
    from .models import PendingReview
    pr = get_object_or_404(PendingReview, pk=pk)
    if request.method == 'POST':
        new_date = request.POST.get('new_date')
        if new_date:
            pr.consultation.follow_up_date = new_date
            pr.consultation.save(update_fields=['follow_up_date'])
            pr.status = 'moved'
            pr.rescheduled_date = new_date
            pr.save(update_fields=['status', 'rescheduled_date'])
            messages.success(request, f'Review moved to {new_date}.')
    return redirect('waiting_room')


@login_required
def pending_review_decline(request, pk):
    from .models import PendingReview
    pr = get_object_or_404(PendingReview, pk=pk)
    if request.method == 'POST':
        pr.status = 'declined'
        pr.save(update_fields=['status'])
        pr.consultation.follow_up_date = None
        pr.consultation.save(update_fields=['follow_up_date'])
        messages.success(request, f'Review for {pr.consultation.patient} declined.')
    return redirect('waiting_room')


@login_required
def pending_review_notes(request, pk):
    from .models import PendingReview
    pr = get_object_or_404(PendingReview, pk=pk)
    if request.method == 'POST':
        pr.notes = request.POST.get('notes', '').strip()
        pr.save(update_fields=['notes'])
        messages.success(request, 'Notes saved.')
    return redirect('waiting_room')

@login_required
def waiting_room_status(request):
    """Lightweight JSON endpoint — polled every 5 s by the waiting room."""
    from django.http import JsonResponse
    from .models import PendingReview, CheckInRequest
    today = timezone.localdate()
    in_progress      = Appointment.objects.filter(date=today, status='With Doctor').exists()
    waiting_count    = Appointment.objects.filter(date=today, status='Checked In').count()
    checkin_count    = CheckInRequest.objects.filter(status='pending').count()
    reviews_pending  = PendingReview.objects.filter(date=today, status='pending').count()
    reviews_arrived  = PendingReview.objects.filter(date=today, status='self_arrived').count()
    return JsonResponse({
        'in_progress':     in_progress,
        'waiting':         waiting_count,
        'checkins':        checkin_count,
        'reviews_pending': reviews_pending,
        'reviews_arrived': reviews_arrived,
    })


@login_required
def appointment_start_consultation(request, pk):
    """Receptionist hands off patient to doctor — marks With Doctor, stays on waiting room."""
    appointment = get_object_or_404(Appointment, pk=pk)
    appointment.status = 'With Doctor'
    appointment.save(update_fields=['status'])
    return redirect('waiting_room')


@login_required
def appointment_check_in(request, pk):
    if request.method == 'POST':
        appointment = get_object_or_404(Appointment, pk=pk)
        appointment.status = 'Checked In'
        appointment.save(update_fields=['status'])
        messages.success(request, f'{appointment.patient} checked in.')
    return redirect('waiting_room')


# ── Web bookings (from the public Medical-Flow website) ────────────────────────

@login_required
def web_booking_list(request):
    """Reception queue of website bookings. 'requested' bookings need confirming
    into an appointment; everything else is history."""
    status = request.GET.get('status', 'requested')
    bookings = WebBooking.objects.all()
    if status in dict(WebBooking.STATUS_CHOICES):
        bookings = bookings.filter(status=status)
    counts = {
        'requested': WebBooking.objects.filter(status='requested').count(),
        'converted': WebBooking.objects.filter(status='converted').count(),
        'cancelled': WebBooking.objects.filter(status='cancelled').count(),
    }
    return render(request, 'appointments/web_booking_list.html', {
        'bookings': bookings.select_related('matched_patient', 'created_appointment'),
        'status':   status,
        'counts':   counts,
    })


def _suggest_patients(booking):
    """Find likely existing-patient matches for a web booking (by phone / email / name)."""
    from patients.models import Patient
    digits = ''.join(ch for ch in booking.phone if ch.isdigit())[-9:]
    q = Q()
    if digits:
        q |= Q(phone__contains=digits) | Q(alt_phone__contains=digits)
    if booking.email:
        q |= Q(email__iexact=booking.email)
    name_parts = booking.name.split()
    if name_parts:
        q |= Q(last_name__icontains=name_parts[-1])
    if not q:
        return Patient.objects.none()
    return Patient.objects.filter(q).distinct()[:10]


@login_required
def web_booking_convert(request, pk):
    """Turn a paid web booking into a real Patient (matched or new) + Appointment."""
    from patients.models import Patient
    booking = get_object_or_404(WebBooking, pk=pk)

    if booking.status == 'converted' and booking.created_appointment_id:
        messages.info(request, 'This booking has already been converted.')
        return redirect('appointment_detail', pk=booking.created_appointment_id)

    suggestions = _suggest_patients(booking)
    first, *rest = booking.name.split()
    last = ' '.join(rest)
    error = None

    if request.method == 'POST':
        patient = None
        existing_id = request.POST.get('existing_patient')
        if existing_id:
            patient = get_object_or_404(Patient, pk=existing_id)
        else:
            id_number = (request.POST.get('id_number') or '').strip()
            dob       = request.POST.get('date_of_birth') or None
            gender    = request.POST.get('gender') or ''
            f_name    = (request.POST.get('first_name') or '').strip()
            l_name    = (request.POST.get('last_name') or '').strip()
            if not (id_number and dob and gender and f_name and l_name):
                error = 'To create a new patient, first/last name, ID number, date of birth and gender are all required.'
            elif Patient.objects.filter(id_number=id_number).exists():
                error = 'A patient with that ID number already exists — pick them from the matches instead.'
            else:
                patient = Patient.objects.create(
                    first_name=f_name, last_name=l_name, id_number=id_number,
                    date_of_birth=dob, gender=gender,
                    phone=booking.phone, email=booking.email or None,
                )

        if patient and not error:
            appt = Appointment.objects.create(
                patient=patient,
                date=request.POST.get('date') or booking.appointment_date,
                time=request.POST.get('time') or booking.appointment_time or '09:00',
                reason=request.POST.get('reason') or booking.appointment_type,
                status='Scheduled',
                visit_type='Scheduled',
                notes=f'Booked online ({booking.reference}) for {booking.time_slot}.',
            )
            booking.matched_patient = patient
            booking.created_appointment = appt
            booking.status = 'converted'
            booking.reviewed_at = timezone.now()
            booking.save(update_fields=['matched_patient', 'created_appointment', 'status', 'reviewed_at'])
            messages.success(request, f'Appointment created for {patient}.')
            return redirect('appointment_detail', pk=appt.pk)

    return render(request, 'appointments/web_booking_convert.html', {
        'booking':     booking,
        'suggestions': suggestions,
        'prefill':     {'first_name': first or '', 'last_name': last},
        'gender_choices': Patient.GENDER_CHOICES,
        'error':       error,
        'is_online_consult': booking.appointment_type == settings.ONLINE_CONSULT_TYPE,
    })


@login_required
def web_booking_dismiss(request, pk):
    booking = get_object_or_404(WebBooking, pk=pk)
    if request.method == 'POST':
        booking.status = 'cancelled'
        booking.save(update_fields=['status'])
        messages.success(request, f'Booking {booking.reference} dismissed.')
    return redirect('web_booking_list')
