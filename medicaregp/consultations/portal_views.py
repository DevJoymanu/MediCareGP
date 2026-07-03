"""
Public, no-login results portals for lab / radiology providers.

Two flavours, both feeding the doctor's "Pending results" review queue:

1. Per-request token portal (`/results/<token>/`) — legacy links already issued on
   older referral forms still work.
2. Standing practice portals (`/lab/` and `/radiology/`) — a provider logs in once
   with the shared portal password, sees every outstanding request of that kind,
   picks the patient and submits results. This is how new referrals are handled, so
   no per-patient link/QR has to be printed on the form the patient carries.
"""
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .models import InvestigationRequest


PORTAL_LABELS = {'lab': 'Laboratory', 'radiology': 'Radiology'}


def _portal_password(kind):
    return getattr(settings, f'{kind.upper()}_PORTAL_PASSWORD', '')


def _session_key(kind):
    return f'portal_authed_{kind}'


def _handle_submission(request, inv):
    """Apply a results POST to `inv`. Returns an error string, or None on success."""
    result_text   = request.POST.get('result_text', '').strip()
    submitted_by  = request.POST.get('submitted_by', '').strip()
    provider_note = request.POST.get('provider_note', '').strip()
    upload        = request.FILES.get('result_file')

    if not result_text and not upload:
        return 'Please enter the results or attach a report file before submitting.'

    inv.result_text    = result_text
    inv.submitted_by   = submitted_by
    inv.provider_note  = provider_note
    inv.decline_reason = ''                                # clear any prior decline
    if upload:
        inv.result_file = upload
    inv.status       = 'submitted'
    inv.submitted_at = timezone.now()
    inv.save()
    return None


# ── Per-request token portal (legacy links) ───────────────────────────────────

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
        error = _handle_submission(request, inv)
        if not error:
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


# ── Standing practice portals (/lab/, /radiology/) ─────────────────────────────

def provider_portal(request, kind):
    """Password gate, then a list of outstanding requests for this kind."""
    label = PORTAL_LABELS[kind]
    skey  = _session_key(kind)
    error = None

    if request.method == 'POST' and not request.session.get(skey):
        if request.POST.get('website'):                       # honeypot
            return redirect(f'{kind}_portal')
        if request.POST.get('password', '') == _portal_password(kind):
            request.session[skey] = True
            return redirect(f'{kind}_portal')
        error = 'Incorrect password. Please try again.'

    if not request.session.get(skey):
        return render(request, 'results/provider_login.html', {
            'kind':          kind,
            'label':         label,
            'error':         error,
            'practice_name': settings.PRACTICE_NAME,
        })

    requests = (InvestigationRequest.objects
                .filter(kind=kind)
                .exclude(status='confirmed')
                .select_related('consultation__patient', 'provider')
                .order_by('status', '-created_at'))

    return render(request, 'results/provider_portal.html', {
        'kind':          kind,
        'label':         label,
        'requests':      requests,
        'practice_name': settings.PRACTICE_NAME,
        'done':          request.GET.get('done'),
    })


def provider_portal_submit(request, kind, pk):
    """Open one request from the portal list and submit its results."""
    if not request.session.get(_session_key(kind)):
        return redirect(f'{kind}_portal')

    inv = get_object_or_404(
        InvestigationRequest.objects.select_related('consultation__patient', 'provider'),
        pk=pk, kind=kind)

    if inv.status == 'confirmed':
        return render(request, 'results/invalid.html',
                      {'reason': 'closed', 'practice_name': settings.PRACTICE_NAME})

    error = None
    if request.method == 'POST':
        if request.POST.get('website'):                       # honeypot
            return redirect(f'{kind}_portal')
        error = _handle_submission(request, inv)
        if not error:
            return redirect(f"{reverse(f'{kind}_portal')}?done=1")

    return render(request, 'results/portal.html', {
        'inv':           inv,
        'patient':       inv.consultation.patient,
        'practice_name': settings.PRACTICE_NAME,
        'error':         error,
        'is_resubmit':   inv.status in ('submitted', 'declined'),
        'back_url':      reverse(f'{kind}_portal'),
    })


def provider_portal_logout(request, kind):
    request.session.pop(_session_key(kind), None)
    return redirect(f'{kind}_portal')
