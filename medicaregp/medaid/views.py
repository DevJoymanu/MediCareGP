"""Gateway actions. These handle billing/membership data only (non-clinical),
so both roles may use them — reception runs the front office."""
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from billing.models import Invoice
from patients.models import Patient

from .adapters import get_gateway
from .claim_builder import ClaimBuilder


@login_required
def verify_member(request, patient_pk):
    """Direct member verification against the patient's scheme."""
    patient = get_object_or_404(Patient, pk=patient_pk)
    if not patient.medical_aid_name:
        messages.error(request, 'Patient has no medical aid scheme on file.')
        return redirect('patient_detail', pk=patient_pk)
    gateway = get_gateway(patient.medical_aid_name)
    result = gateway.verify_member(patient.medical_aid_number or '', patient.id_number)
    level = messages.SUCCESS if result.verified else messages.WARNING
    messages.add_message(request, level, f'{result.scheme_name}: {result.message or "Member verified."}')
    return redirect('patient_detail', pk=patient_pk)


@login_required
@require_POST
def submit_claim(request, invoice_pk):
    """Build the whitelisted claim payload and submit it directly to the
    patient's scheme via its adapter."""
    invoice = get_object_or_404(Invoice.objects.select_related('patient'), pk=invoice_pk)
    scheme = invoice.patient.medical_aid_name
    if not scheme:
        messages.error(request, 'Patient has no medical aid scheme on file.')
        return redirect('invoice_detail', pk=invoice_pk)

    payload = ClaimBuilder.build(invoice, practice_number=settings.PRACTICE_NUMBER)
    result = get_gateway(scheme).submit_claim(payload)
    if result.submitted:
        messages.success(request, f'{result.scheme_name}: {result.message} (ref {result.reference})')
    else:
        messages.error(request, f'{result.scheme_name}: {result.message}')
    return redirect('invoice_detail', pk=invoice_pk)
