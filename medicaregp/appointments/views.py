from datetime import date, datetime

from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
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
    initial = {}
    patient_id = request.GET.get('patient_id')
    if patient_id:
        initial['patient'] = patient_id
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
        appt.date = date.today()
        appt.time = datetime.now().time().replace(second=0, microsecond=0)
        appt.visit_type = 'Walk-In'
        appt.status = 'Checked In'
        appt.save()
        messages.success(request, f'{appt.patient} added to the waiting room.')
        return redirect('waiting_room')
    return render(request, 'appointments/walk_in_form.html', {'form': form})

@login_required
def waiting_room(request):
    today = date.today()
    waiting = (Appointment.objects
               .filter(date=today, status='Checked In')
               .select_related('patient')
               .order_by('time'))
    scheduled = (Appointment.objects
                 .filter(date=today, status='Scheduled')
                 .select_related('patient')
                 .order_by('time'))
    return render(request, 'appointments/waiting_room.html', {
        'waiting': waiting,
        'scheduled': scheduled,
        'today': today,
    })

@login_required
def appointment_check_in(request, pk):
    if request.method == 'POST':
        appointment = get_object_or_404(Appointment, pk=pk)
        appointment.status = 'Checked In'
        appointment.save(update_fields=['status'])
        messages.success(request, f'{appointment.patient} checked in.')
    return redirect('waiting_room')
