from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from medicaregp.roles import (doctor_required, is_doctor,
                              reception_patient_queryset)
from .models import Patient, Vitals
from .forms import PatientForm, ReceptionPatientForm, VitalsForm, FamilyMemberFormSet
from .services import visit_usage


def _patient_qs(request):
    """Role-scoped patient queryset: reception never selects clinical columns."""
    return Patient.objects.all() if is_doctor(request.user) else reception_patient_queryset()


def _patient_form_class(request):
    """Role-scoped form: reception's form excludes clinical fields entirely."""
    return PatientForm if is_doctor(request.user) else ReceptionPatientForm


@login_required
def patient_list(request):
    q = request.GET.get('q', '')
    patients = _patient_qs(request)
    if q:
        patients = patients.filter(
            Q(id_number__icontains=q) |
            Q(phone__icontains=q)
        )
    return render(request, 'patients/patient_list.html', {'patients': patients, 'q': q})


@login_required
def patient_detail(request, pk):
    if not is_doctor(request.user):
        # Front office: demographics + medical aid only — clinical columns are
        # deferred (never selected) and no clinical relations enter the context.
        patient = get_object_or_404(reception_patient_queryset(), pk=pk)
        return render(request, 'patients/patient_detail_reception.html', {
            'patient':        patient,
            'appointments':   patient.appointments.all(),
            'family_members': patient.family_members.all(),
            'usage':          visit_usage(patient),
        })
    patient = get_object_or_404(Patient, pk=pk)
    return render(request, 'patients/patient_detail.html', {
        'patient':        patient,
        'appointments':   patient.appointments.all(),
        'consultations':  patient.consultations.select_related('appointment').all(),
        'documents':      patient.documents.all(),
        'vitals':         patient.vitals.all()[:10],
        'family_members': patient.family_members.all(),
        'usage':          visit_usage(patient),
    })


@login_required
def patient_create(request):
    form_class = _patient_form_class(request)
    form = form_class(request.POST or None)
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
    patient = get_object_or_404(_patient_qs(request), pk=pk)
    form_class = _patient_form_class(request)
    form = form_class(request.POST or None, instance=patient)
    formset = FamilyMemberFormSet(request.POST or None, instance=patient)
    if form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, 'Patient record updated.')
        return redirect('patient_detail', pk=pk)
    return render(request, 'patients/patient_form.html', {
        'form': form, 'formset': formset, 'title': f'Edit — {patient}',
    })


@doctor_required
def patient_delete(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    if request.method == 'POST':
        name = str(patient)
        patient.delete()
        messages.success(request, f'Patient record deleted for {name}.')
        return redirect('patient_list')
    return render(request, 'patients/patient_confirm_delete.html', {'patient': patient})


@doctor_required
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


# ── Front office: biometric check-in (medical-aid details only) ────────────────

@login_required
def biometric_identify(request):
    """Biometric check-in. A submitted sample is hashed and matched; a match
    returns the patient's MEDICAL-AID DETAILS ONLY (whitelisted in
    medicaregp.roles.MEDICAL_AID_FIELDS) plus the visit-limit status.
    No clinical data is ever selected or rendered here."""
    from medicaregp.roles import patient_medical_aid_summary
    from .biometrics import get_provider

    context = {'searched': False}
    if request.method == 'POST':
        sample = request.POST.get('sample', '').strip()
        context['searched'] = True
        if sample:
            patient = get_provider().identify(sample)
            if patient:
                context['match'] = patient_medical_aid_summary(patient.pk)
                context['usage'] = visit_usage(patient)
                context['patient_pk'] = patient.pk
    return render(request, 'patients/biometric_identify.html', context)


@login_required
def biometric_enrol(request, pk):
    """Enrol (or re-enrol) a patient's biometric template. Stores only a
    one-way hash of the scanner's template output."""
    from .biometrics import get_provider

    patient = get_object_or_404(Patient, pk=pk)
    if request.method == 'POST':
        sample = request.POST.get('sample', '').strip()
        if sample:
            get_provider().enrol(patient, sample)
            messages.success(request, f'Biometric template enrolled for {patient}.')
        else:
            messages.error(request, 'No biometric sample received.')
    return redirect('patient_detail', pk=pk)


# ── Print All (RBAC-aware) ──────────────────────────────────────────────────────

@login_required
def patient_print_all(request, pk):
    """Print-friendly full record. Doctors get the complete record including
    clinical sections; reception's printout contains demographics + medical
    aid ONLY — the clinical sections are never queried for them."""
    include_clinical = is_doctor(request.user)
    if include_clinical:
        patient = get_object_or_404(Patient, pk=pk)
        context = {
            'patient':          patient,
            'include_clinical': True,
            'consultations':    patient.consultations.select_related('appointment').all(),
            'vitals':           patient.vitals.all(),
            'appointments':     patient.appointments.all(),
            'family_members':   patient.family_members.all(),
            'usage':            visit_usage(patient),
        }
    else:
        patient = get_object_or_404(reception_patient_queryset(), pk=pk)
        context = {
            'patient':          patient,
            'include_clinical': False,
            'appointments':     patient.appointments.all(),
            'family_members':   patient.family_members.all(),
            'usage':            visit_usage(patient),
        }
    return render(request, 'patients/patient_print_all.html', context)
