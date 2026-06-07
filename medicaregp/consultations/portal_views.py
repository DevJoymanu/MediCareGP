"""
Public, no-login results portal for lab / radiology providers.

A provider opens the unique link printed on the request form (with the QR code),
enters the results + uploads their report, and submits. The submission lands in the
doctor's "Pending results" queue for review (confirm / decline). Mirrors the patient
self-check-in token flow in appointments/checkin_views.py.
"""
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import InvestigationRequest


def result_portal(request, token):
    inv = InvestigationRequest.objects.filter(token=token).select_related(
        'consultation__patient', 'provider').first()

    if inv is None:
        return render(request, 'results/invalid.html',
                      {'reason': 'invalid', 'practice_name': settings.PRACTICE_NAME}, status=404)

    # Already reviewed & filed — portal is closed.
    if inv.status == 'confirmed':
        return render(request, 'results/invalid.html',
                      {'reason': 'closed', 'practice_name': settings.PRACTICE_NAME})

    error = None
    if request.method == 'POST':
        if request.POST.get('website'):                       # honeypot — silent drop
            return redirect('result_done', token=inv.token)

        result_text   = request.POST.get('result_text', '').strip()
        submitted_by  = request.POST.get('submitted_by', '').strip()
        provider_note = request.POST.get('provider_note', '').strip()
        upload        = request.FILES.get('result_file')

        if not result_text and not upload:
            error = 'Please enter the results or attach a report file before submitting.'
        else:
            inv.result_text    = result_text
            inv.submitted_by   = submitted_by
            inv.provider_note  = provider_note
            inv.decline_reason = ''                           # clear any prior decline
            if upload:
                inv.result_file = upload
            inv.status       = 'submitted'
            inv.submitted_at = timezone.now()
            inv.save()
            return redirect('result_done', token=inv.token)

    return render(request, 'results/portal.html', {
        'inv':           inv,
        'patient':       inv.consultation.patient,
        'practice_name': settings.PRACTICE_NAME,
        'error':         error,
        'is_resubmit':   inv.status in ('submitted', 'declined'),
    })


def result_done(request, token):
    inv = get_object_or_404(InvestigationRequest, token=token)
    return render(request, 'results/done.html', {
        'inv':           inv,
        'practice_name': settings.PRACTICE_NAME,
    })
