from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Appointment
from .forms import AppointmentForm

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
