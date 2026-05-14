from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.utils import timezone
from .models import Appointment
from .forms import AppointmentForm, WalkInForm

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
    return render(request, 'appointments/appointment_detail.html', {'appointment':appointment})

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
    return render(request, 'appointments/waiting_room.html', {
        'in_consultation': in_consultation,
        'waiting':         waiting,
        'scheduled':       scheduled,
        'pending_reviews': pending_reviews,
        'today':           today,
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
    from .models import PendingReview
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
