"""
Doctor-only views for the provisional-diagnosis engine.

RBAC: every view is @doctor_required — reception hitting any of these URLs
gets HTTP 403 (enforced server-side, see medicaregp/roles.py).
"""
import json
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from consultations.icd10_data import ICD10_CODES
from consultations.models import Consultation
from medicaregp.roles import doctor_required
from patients.models import Patient

from . import engine
from .models import Condition, DifferentialResult, Symptom


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

    return render(request, 'diagnosis/symptom_checklist_simple.html', context)


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
    return render(request, 'diagnosis/results_simple.html', {
        'result': result,
        'result_pk': result.pk,
        'consultation_pk': result.consultation.pk,
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


# ── Consultation workspace (single-screen, explicit-Run) ─────────────────────

def _json_body(request):
    try:
        return json.loads(request.body.decode('utf-8'))
    except (ValueError, UnicodeDecodeError):
        return None


def _run_payload(result):
    """Client-side shape of one engine run (restores the panel on reload)."""
    return {
        'result_id': result.pk,
        'created_at': timezone.localtime(result.created_at).strftime('%H:%M'),
        'inputs': {
            'presenting_symptom_ids': result.inputs.get('presenting_symptom_ids', []),
            'working_symptom_ids': result.inputs.get('working_symptom_ids', []),
            'notes': result.inputs.get('notes', ''),
        },
        'output': result.output,
        'flags': result.inputs.get('first_occurrence_flags', []),
    }


@doctor_required
def workspace_new(request):
    """Blank workspace — no consultation yet. The doctor picks the patient
    from the info bar (or one-taps the waiting queue); that routes through
    consultation_create, which starts/reuses the consultation and reloads the
    workspace with everything preloaded."""
    from appointments.models import Appointment
    waiting = (Appointment.objects
               .filter(date=timezone.localdate(), status__in=('Checked In', 'With Doctor'))
               .select_related('patient').order_by('time'))
    return render(request, 'diagnosis/workspace.html', {
        'consultation': None,
        'patient': None,
        'waiting': waiting,
    })


@doctor_required
def workspace(request, consultation_pk):
    """The doctor's consultation workspace: 3-zone single screen — working
    area (complaint, symptoms, history, SOAP notes) + persistent differential
    panel. All diagnosis actions happen via the JSON endpoints below."""
    consultation = get_object_or_404(Consultation.objects.select_related('patient'), pk=consultation_pk)
    patient = consultation.patient

    symptoms = list(Symptom.objects.filter(active=True)
                    .order_by('name')
                    .values('id', 'name', 'kind', 'synonyms', 'body_region'))

    # First-occurrence, precomputed for the whole knowledge base so the client
    # can badge chips instantly (⚑) without a round-trip per symptom.
    flags = engine.first_occurrence_flags(
        patient, [s['id'] for s in symptoms], exclude_consultation=consultation)
    first_ids = [f['symptom_id'] for f in flags]

    last_run = consultation.differential_results.first()   # newest (Meta ordering)

    return render(request, 'diagnosis/workspace.html', {
        'consultation': consultation,
        'patient': patient,
        'patient_appointments': patient.appointments.order_by('-date', '-time')[:25],
        'visit_number': patient.consultations.count(),
        'allergies': patient.allergies_list(),
        'chronic': patient.chronic_list(),
        'prior_codes': sorted(engine.prior_icd10_codes(patient)),
        'existing_codes': consultation.icd10_codes_list,
        'regions': Symptom.BODY_REGION_CHOICES,
        'symptoms_data': symptoms,
        'first_ids': first_ids,
        'last_run_data': _run_payload(last_run) if last_run else None,
        'min_inputs': engine.MIN_INPUTS,
        'history_weight': engine.HISTORY_WEIGHT,
        'presenting_weight': engine.PRESENTING_WEIGHT,
    })


@doctor_required
@require_POST
def workspace_run(request, consultation_pk):
    """Explicit Run: score the current inputs, store the audit
    DifferentialResult, return the panel data as JSON."""
    consultation = get_object_or_404(Consultation.objects.select_related('patient'), pk=consultation_pk)
    patient = consultation.patient

    data = _json_body(request)
    if data is None:
        return HttpResponseBadRequest('Invalid JSON body.')

    presenting_ids = [int(i) for i in data.get('presenting', []) if str(i).isdigit()]
    working_ids    = [int(i) for i in data.get('working', []) if str(i).isdigit()]
    notes          = (data.get('notes') or '').strip()

    if not presenting_ids and not working_ids:
        return JsonResponse({'error': 'Add at least one symptom before running.'}, status=400)

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

    payload = _run_payload(result)
    payload['suggestions'] = engine.suggest_more_symptoms(output, presenting_ids, working_ids)
    return JsonResponse(payload)


@doctor_required
@require_POST
def workspace_confirm(request, consultation_pk):
    """Confirm the promoted provisional diagnoses: write ICD-10 codes to the
    consultation and freeze the run as an immutable snapshot (confirmed_at /
    confirmed_dx). Off-list (manual) codes are validated against ICD10_CODES."""
    consultation = get_object_or_404(Consultation, pk=consultation_pk)

    data = _json_body(request)
    if data is None:
        return HttpResponseBadRequest('Invalid JSON body.')

    promoted = data.get('promoted') or []
    if not promoted:
        return JsonResponse({'error': 'Promote at least one diagnosis before confirming.'}, status=400)

    result = None
    if data.get('result_id'):
        result = get_object_or_404(
            DifferentialResult, pk=data['result_id'], consultation=consultation)

    valid_codes = dict(ICD10_CODES)
    engine_codes = ({r['icd10_code'] for r in result.output.get('results', [])}
                    if result else set())

    clean = []
    for item in promoted:
        code = (item.get('code') or '').strip()
        name = (item.get('name') or '').strip()
        source = item.get('source') or 'engine'
        if not code:
            return JsonResponse({'error': 'A promoted diagnosis is missing its ICD-10 code.'}, status=400)
        if source == 'manual':
            if code not in valid_codes:
                return JsonResponse({'error': f'Unknown ICD-10 code: {code}'}, status=400)
            name = name or valid_codes[code]
        elif code not in engine_codes:
            return JsonResponse({'error': f'{code} is not in this run’s differential.'}, status=400)
        clean.append({'code': code, 'name': name, 'source': source})

    existing = consultation.icd10_codes_list
    existing_codes = {e.get('code') for e in existing}
    for dx in clean:
        if dx['code'] not in existing_codes:
            existing.append({'code': dx['code'], 'description': dx['name']})
            existing_codes.add(dx['code'])
    consultation.icd10_code = json.dumps(existing)

    if result:
        summary = '; '.join(
            f"{r['rank']}. {r['condition']} ({r['icd10_code']}) — score {r['score']} [{r['band']}]"
            for r in result.output.get('results', []))
        consultation.differential_diagnosis = (
            f"Provisional Diagnosis (engine v{result.engine_version}, "
            f"history weight {result.output['constants']['history_weight']}): {summary}")
        result.confirmed_at = timezone.now()
        result.confirmed_dx = clean
        result.save(update_fields=['confirmed_at', 'confirmed_dx'])
    consultation.save()

    # Confirming wraps up the visit: complete the linked appointment (same
    # behaviour the old create-form save had) and feed the Rx learner.
    from appointments.models import Appointment
    from consultations.views import _learn_from_consultation
    apt = consultation.appointment
    if apt and apt.status in ('Checked In', 'With Doctor'):
        apt.status = 'Completed'
        apt.save(update_fields=['status'])
    else:
        Appointment.objects.filter(
            patient=consultation.patient, date=timezone.localdate(),
            status__in=('Checked In', 'With Doctor'),
        ).update(status='Completed')
    _learn_from_consultation(consultation)

    return JsonResponse({'ok': True,
                         'redirect': reverse('consultation_detail', args=[consultation.pk])})


def _parse_date(raw):
    """ISO date string → date | None. Raises ValueError on garbage."""
    raw = (raw or '').strip()
    if not raw:
        return None
    from datetime import date as date_cls
    return date_cls.fromisoformat(raw)


@doctor_required
@require_POST
def workspace_save_notes(request, consultation_pk):
    """Save the working-area fields: chief complaint, quick vitals, SOAP,
    prescriptions, lab/radiology requests, follow-up and sick note — plus the
    linked appointment. One endpoint, one Save button."""
    consultation = get_object_or_404(Consultation.objects.select_related('patient'), pk=consultation_pk)
    data = _json_body(request)
    if data is None:
        return HttpResponseBadRequest('Invalid JSON body.')

    editable = ['chief_complaint', 'subjective', 'objective', 'assessment', 'plan',
                'bp_reading', 'prescriptions', 'lab_requests', 'radiology_requests',
                'sick_note_employer']
    changed = []
    for field in editable:
        if field in data:
            setattr(consultation, field, (data[field] or '').strip())
            changed.append(field)

    if 'weight_kg' in data:
        raw = str(data['weight_kg'] or '').strip()
        if raw:
            try:
                consultation.weight_kg = Decimal(raw)
            except InvalidOperation:
                return JsonResponse({'error': f'Invalid weight: {raw}'}, status=400)
        else:
            consultation.weight_kg = None
        changed.append('weight_kg')

    for field in ['follow_up_date', 'sick_note_start_date']:
        if field in data:
            try:
                setattr(consultation, field, _parse_date(data[field]))
            except ValueError:
                return JsonResponse({'error': f'Invalid date for {field}.'}, status=400)
            changed.append(field)

    if 'sick_note_issued' in data:
        consultation.sick_note_issued = bool(data['sick_note_issued'])
        changed.append('sick_note_issued')
    if 'sick_note_days' in data:
        raw = str(data['sick_note_days'] or '').strip()
        if raw and not raw.isdigit():
            return JsonResponse({'error': f'Invalid sick-note days: {raw}'}, status=400)
        consultation.sick_note_days = int(raw) if raw else None
        changed.append('sick_note_days')

    if 'appointment_id' in data:
        apt_id = data['appointment_id']
        if apt_id in (None, '', 0):
            consultation.appointment = None
        else:
            from appointments.models import Appointment
            apt = Appointment.objects.filter(pk=apt_id, patient=consultation.patient).first()
            if apt is None:
                return JsonResponse({'error': 'That appointment does not belong to this patient.'}, status=400)
            consultation.appointment = apt
        changed.append('appointment')

    if changed:
        consultation.save(update_fields=changed)
        if 'lab_requests' in changed or 'radiology_requests' in changed:
            from consultations.views import _sync_investigation_requests
            _sync_investigation_requests(consultation)
    return JsonResponse({'ok': True, 'saved_at': timezone.localtime().strftime('%H:%M')})


@doctor_required
@require_GET
def workspace_patient_search(request):
    """Type-ahead for the workspace Patient selector."""
    q = (request.GET.get('q') or '').strip()
    if len(q) < 2:
        return JsonResponse({'results': []})
    from django.db.models import Q
    matches = (Patient.objects.filter(
        Q(first_name__icontains=q) | Q(last_name__icontains=q) |
        Q(id_number__icontains=q) | Q(phone__icontains=q))
        .order_by('last_name', 'first_name')[:15])
    return JsonResponse({'results': [
        {'id': p.pk,
         'label': f'{p.first_name} {p.last_name}',
         'detail': f'{p.get_age()}y · {p.get_gender_display()}'
                   + (f' · {p.medical_aid_name}' if p.medical_aid_name else '')}
        for p in matches]})


@doctor_required
@require_GET
def workspace_patient_appointments(request):
    """A patient's recent appointments for the Linked Appointment selector."""
    patient = get_object_or_404(Patient, pk=request.GET.get('patient_id'))
    appointments = patient.appointments.order_by('-date', '-time')[:25]
    return JsonResponse({'results': [
        {'id': a.pk,
         'label': f'{a.date:%d %b %Y} {a.time:%H:%M} — {a.reason} ({a.status})'}
        for a in appointments]})


@doctor_required
@require_GET
def icd10_search(request):
    """Type-ahead for the off-list provisional-dx add: search the full ICD-10
    reference by code prefix or description substring."""
    q = (request.GET.get('q') or '').strip().lower()
    if len(q) < 2:
        return JsonResponse({'results': []})
    results = []
    for code, description in ICD10_CODES:
        if code.lower().startswith(q) or q in description.lower():
            results.append({'code': code, 'description': description})
            if len(results) >= 20:
                break
    return JsonResponse({'results': results})
