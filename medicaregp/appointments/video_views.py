"""
Built-in 1:1 video consultation (WebRTC).

The two browsers exchange media peer-to-peer. Django only relays the WebRTC
handshake (offer / answer / ICE) via a tiny DB-backed message queue that each
side polls — no WebSockets, no media server, so it runs on the existing WSGI
stack. The doctor joins from the CRM (login required); the patient joins via an
unguessable token link (no login).
"""
import json
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from . import turn
from .models import Appointment, VideoRoom, VideoSignal


def _room_context(room, role, self_name, peer_name):
    return {
        'role':       role,
        'polite':     role == 'patient',          # perfect-negotiation: patient yields on glare
        'room_id':    str(room.room_id),
        'signal_url': reverse('video_signal', args=[room.room_id]),
        'ice_url':    reverse('video_ice', args=[room.room_id]),
        'self_name':  self_name,
        'peer_name':  peer_name,
    }


def ice_config(request, room_id):
    """Fresh ICE servers (with short-lived TURN creds) fetched by the call page at start."""
    get_object_or_404(VideoRoom, room_id=room_id)
    return JsonResponse({'iceServers': turn.build_ice_servers()})


@login_required
def turn_test(request):
    """Diagnostic page (staff) that checks whether the configured TURN relays work."""
    return render(request, 'video/turn_test.html', {'ice_url': reverse('video_turn_test_ice')})


@login_required
def turn_test_ice(request):
    return JsonResponse({
        'iceServers': turn.build_ice_servers(),
        'diagnostics': turn.diagnostics(),
    })


@login_required
def doctor_room(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    room, _ = VideoRoom.objects.get_or_create(appointment=appointment)
    return render(request, 'video/room.html',
                  _room_context(room, 'doctor', settings.PRACTICE_NAME, str(appointment.patient)))


def patient_room(request, patient_token):
    room = get_object_or_404(VideoRoom, patient_token=patient_token)
    return render(request, 'video/room.html',
                  _room_context(room, 'patient', str(room.appointment.patient), settings.PRACTICE_NAME))


@csrf_exempt
@require_http_methods(["GET", "POST"])
def signal(request, room_id):
    """Relay WebRTC signaling. POST a message; GET polls for the other peer's messages."""
    room = get_object_or_404(VideoRoom, room_id=room_id)

    if request.method == 'POST':
        try:
            body = json.loads(request.body.decode('utf-8') or '{}')
            role, kind, payload = body['role'], body['kind'], body['payload']
        except (ValueError, KeyError):
            return HttpResponseBadRequest('bad signal')
        if role not in ('doctor', 'patient'):
            return HttpResponseBadRequest('bad role')

        msg = VideoSignal.objects.create(room=room, role=role, kind=kind, payload=json.dumps(payload))
        # Opportunistic cleanup of stale signals (cheap at this volume).
        VideoSignal.objects.filter(created_at__lt=timezone.now() - timedelta(hours=6)).delete()
        return JsonResponse({'ok': True, 'id': msg.id})

    # GET — return messages from the *other* role since the client's cursor.
    role = request.GET.get('role')
    if role not in ('doctor', 'patient'):
        return HttpResponseBadRequest('bad role')
    try:
        since = int(request.GET.get('since', '0') or 0)
    except ValueError:
        since = 0

    qs = room.signals.filter(id__gt=since).exclude(role=role).order_by('id')
    messages = [{'id': s.id, 'kind': s.kind, 'payload': s.payload} for s in qs]
    cursor = messages[-1]['id'] if messages else since
    return JsonResponse({'messages': messages, 'cursor': cursor})
