from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Patient, Vitals
from .forms import PatientForm, VitalsForm, FamilyMemberFormSet


@login_required
def patient_list(request):
    q = request.GET.get('q', '')
    patients = Patient.objects.all()
    if q:
        patients = patients.filter(
            Q(id_number__icontains=q) |
            Q(phone__icontains=q) |
            Q(first_name__icontains=q) | Q(last_name__icontains=q)
        )
    return render(request, 'patients/patient_list.html', {'patients': patients, 'q': q})


@login_required
def patient_detail(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    return render(request, 'patients/patient_detail.html', {
        'patient':        patient,
        'appointments':   patient.appointments.all(),
        'consultations':  patient.consultations.select_related('appointment').all(),
        'documents':      patient.documents.all(),
        'vitals':         patient.vitals.all()[:10],
        'family_members': patient.family_members.all(),
    })


@login_required
def patient_create(request):
    form = PatientForm(request.POST or None)
    formset = FamilyMemberFormSet(request.POST or None)
    if form.is_valid() and formset.is_valid():
        patient = form.save()
        formset.instance = patient
        formset.save()
        messages.success(request, f'Patient record created for {patient}.')
        return redirect('patient_detail', pk=patient.pk)
    return render(request, 'patients/patient_form.html', {
        'form': form, 'formset': formset, 'title': 'New Patient Registration',
    })


@login_required
def patient_edit(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    form = PatientForm(request.POST or None, instance=patient)
    formset = FamilyMemberFormSet(request.POST or None, instance=patient)
    if form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, 'Patient record updated.')
        return redirect('patient_detail', pk=pk)
    return render(request, 'patients/patient_form.html', {
        'form': form, 'formset': formset, 'title': f'Edit — {patient}',
    })


@login_required
def patient_delete(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    if request.method == 'POST':
        name = str(patient)
        patient.delete()
        messages.success(request, f'Patient record deleted for {name}.')
        return redirect('patient_list')
    return render(request, 'patients/patient_confirm_delete.html', {'patient': patient})


@login_required
def vitals_add(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    from django.utils import timezone
    form = VitalsForm(request.POST or None, initial={'date': timezone.now().date(), 'recorded_by': 'Dr. Tamuka Chivonivoni'})
    if form.is_valid():
        v = form.save(commit=False)
        if v.blood_pressure and '/' in v.blood_pressure:
            try:
                parts = v.blood_pressure.split('/')
                v.bp_systolic  = int(parts[0].strip())
                v.bp_diastolic = int(parts[1].strip())
            except (ValueError, IndexError):
                pass
        v.patient = patient
        v.save()
        messages.success(request, 'Vitals recorded.')
        return redirect('patient_detail', pk=pk)
    return render(request, 'patients/vitals_form.html', {'form': form, 'patient': patient})
