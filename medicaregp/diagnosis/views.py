"""
Doctor-only views for the provisional-diagnosis engine.

RBAC: every view is @doctor_required — reception hitting any of these URLs
gets HTTP 403 (enforced server-side, see medicaregp/roles.py).
"""
import json

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from consultations.models import Consultation
from medicaregp.roles import doctor_required

from . import engine
from .models import DifferentialResult, Symptom


def _selected_ids(request, field):
    ids = request.POST.getlist(field)
    return [int(i) for i in ids if str(i).isdigit()]


@doctor_required
def differential_capture(request, consultation_pk):
    """Symptom capture + scoring. GET renders the capture form; POST runs the
    engine, stores an audit DifferentialResult, and shows the ranked list."""
    consultation = get_object_or_404(Consultation.objects.select_related('patient'), pk=consultation_pk)
    patient = consultation.patient
    symptoms = Symptom.objects.filter(active=True).order_by('kind', 'name')

    context = {
        'consultation': consultation,
        'patient': patient,
        'symptoms': symptoms,
        'min_inputs': engine.MIN_INPUTS,
        'history_weight': engine.HISTORY_WEIGHT,
        'presenting_weight': engine.PRESENTING_WEIGHT,
    }

    if request.method == 'POST':
        presenting_ids = _selected_ids(request, 'presenting')
        working_ids    = _selected_ids(request, 'working')
        notes          = request.POST.get('notes', '').strip()

        if not presenting_ids and not working_ids:
            messages.error(request, 'Select at least one symptom or complaint before scoring.')
            return render(request, 'diagnosis/differential_capture.html', context)

        output = engine.run_differential(patient, presenting_ids, working_ids, notes=notes)
        flags = engine.first_occurrence_flags(
            patient, presenting_ids + working_ids, exclude_consultation=consultation)

        result = DifferentialResult.objects.create(
            consultation=consultation,
            patient=patient,
            created_by=request.user,
            engine_version=engine.ENGINE_VERSION,
            inputs={
                'presenting_symptom_ids': sorted(set(presenting_ids)),
                'working_symptom_ids': sorted(set(working_ids)),
                'notes': notes,
                'patient_snapshot': {
                    'age': patient.get_age(),
                    'sex': patient.gender,
                    'chronic_conditions': patient.chronic_list(),
                    'smoking_status': patient.smoking_status or '',
                    'alcohol_use': patient.alcohol_use or '',
                },
                'first_occurrence_flags': flags,
            },
            output=output,
        )
        return redirect('differential_result', pk=result.pk)

    return render(request, 'diagnosis/differential_capture.html', context)


@doctor_required
def differential_result(request, pk):
    """Ranked Provisional Diagnosis list with full score breakdowns."""
    result = get_object_or_404(
        DifferentialResult.objects.select_related('consultation', 'patient'), pk=pk)
    presenting_ids = result.inputs.get('presenting_symptom_ids', [])
    working_ids = result.inputs.get('working_symptom_ids', [])
    suggestions = engine.suggest_more_symptoms(result.output, presenting_ids, working_ids)
    selected_names = dict(Symptom.objects.filter(
        id__in=presenting_ids + working_ids).values_list('id', 'name'))
    return render(request, 'diagnosis/differential_result.html', {
        'result': result,
        'consultation': result.consultation,
        'patient': result.patient,
        'output': result.output,
        'flags': result.inputs.get('first_occurrence_flags', []),
        'suggestions': suggestions,
        'presenting_names': [selected_names.get(i, '?') for i in presenting_ids],
        'working_names': [selected_names.get(i, '?') for i in working_ids],
    })


@doctor_required
def differential_confirm(request, pk):
    """Doctor confirms one or more provisional diagnoses: their ICD-10 codes
    are appended to the consultation's code list and the differential text is
    recorded on the consultation."""
    result = get_object_or_404(
        DifferentialResult.objects.select_related('consultation'), pk=pk)
    consultation = result.consultation

    if request.method != 'POST':
        return redirect('differential_result', pk=pk)

    chosen_ids = {int(i) for i in request.POST.getlist('confirm') if str(i).isdigit()}
    chosen = [r for r in result.output.get('results', []) if r['condition_id'] in chosen_ids]
    if not chosen:
        messages.error(request, 'Select at least one provisional diagnosis to confirm.')
        return redirect('differential_result', pk=pk)

    existing = consultation.icd10_codes_list
    existing_codes = {e.get('code') for e in existing}
    for r in chosen:
        if r['icd10_code'] not in existing_codes:
            existing.append({'code': r['icd10_code'], 'description': r['condition']})
            existing_codes.add(r['icd10_code'])
    consultation.icd10_code = json.dumps(existing)

    summary = '; '.join(
        f"{r['rank']}. {r['condition']} ({r['icd10_code']}) — score {r['score']} [{r['band']}]"
        for r in result.output.get('results', []))
    consultation.differential_diagnosis = (
        f"Provisional Diagnosis (engine v{result.engine_version}, "
        f"history weight {result.output['constants']['history_weight']}): {summary}")
    consultation.save()

    names = ', '.join(f"{r['condition']} ({r['icd10_code']})" for r in chosen)
    messages.success(request, f'Provisional diagnosis confirmed: {names}. ICD-10 codes added to the consultation.')
    return redirect('consultation_detail', pk=consultation.pk)
