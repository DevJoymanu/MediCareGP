from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from appointments.models import Appointment
from patients.models import Patient
from .models import Consultation
from .forms import ConsultationForm

@login_required
def consultation_list(request):
    from django.db.models import Q
    q = request.GET.get('q', '')
    consultations = Consultation.objects.select_related('patient').all()
    if q:
        consultations = consultations.filter(
            Q(patient__first_name__icontains=q) | Q(patient__last_name__icontains=q) | Q(assessment__icontains=q)
        )
    return render(request, 'consultations/consultation_list.html', {'consultations': consultations, 'q': q})

@login_required
def consultation_detail(request, pk):
    consultation = get_object_or_404(Consultation, pk=pk)
    return render(request, 'consultations/consultation_detail.html', {'consultation':consultation})

@login_required
def consultation_create(request):
    initial = {}
    patient_id = request.GET.get('patient_id')
    appointment_id = request.GET.get('appointment_id')
    if patient_id:
        patient = Patient.objects.filter(pk=patient_id).first()
        if patient:
            initial['patient'] = patient.pk
    if appointment_id:
        apt = Appointment.objects.filter(pk=appointment_id).first()
        if apt:
            initial['appointment'] = apt.pk
            initial['patient'] = apt.patient.pk
    form = ConsultationForm(request.POST or None, initial=initial)
    if form.is_valid():
        consultation = form.save()
        messages.success(request, f'Consultation created for {consultation.patient}.')
        return redirect('consultation_list')
    return render(request, 'consultations/consultation_form.html', {'form':form,'title':'New Consultation'})

@login_required
def consultation_edit(request, pk):
    consultation = get_object_or_404(Consultation, pk=pk)
    form = ConsultationForm(request.POST or None, instance=consultation)
    if form.is_valid():
        form.save()
        messages.success(request, 'Consultation updated successfully.')
        return redirect('consultation_detail', pk=pk)
    return render(request, 'consultations/consultation_form.html', {'form':form,'title':'Edit Consultation'})

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
def consultation_print(request, pk):
    consultation = get_object_or_404(Consultation, pk=pk)
    return render(request, 'consultations/consultation_print.html', {'consultation':consultation})
