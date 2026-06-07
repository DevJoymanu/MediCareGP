"""
Public JSON API consumed by the Medical-Flow patient website.

Two endpoints, no payment:
  GET  /api/availability?date=YYYY-MM-DD  → bookable time slots for that day
  POST /api/bookings                      → create a booking request
  GET  /api/bookings/<reference>          → look a booking up

A booking is just a request: it lands in the reception "Web bookings" queue to be
confirmed into a real Appointment. Public + CSRF-exempt; spammed bots are dropped
by a honeypot field.
"""
import json
import secrets
import time
from datetime import datetime

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from . import booking_slots
from .models import WebBooking


def _json_body(request):
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except (ValueError, UnicodeDecodeError):
        return None


def _make_reference():
    stamp = format(int(time.time() * 1000), "X")
    rand = secrets.token_hex(3).upper()
    return f"RMR-{stamp}-{rand}"


def _parse_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


@require_http_methods(["GET"])
def availability(request):
    """GET /api/availability?date=YYYY-MM-DD → bookable slots for that day."""
    date = _parse_date(request.GET.get("date", ""))
    if date is None:
        return JsonResponse({"error": "A valid ?date=YYYY-MM-DD is required"}, status=400)
    return JsonResponse({"date": date.isoformat(), "slots": booking_slots.availability(date)})


@csrf_exempt
@require_http_methods(["POST"])
def create_booking(request):
    body = _json_body(request)
    if body is None:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    # Honeypot — bots fill hidden fields; silently pretend success.
    if body.get("website") or body.get("honeypot"):
        return JsonResponse({"reference": _make_reference()}, status=201)

    name  = (body.get("name") or "").strip()
    phone = (body.get("phone") or "").strip()
    email = (body.get("email") or "").strip()
    appt_type = (body.get("appointmentType") or "").strip()
    date  = _parse_date((body.get("date") or "").strip())
    slot  = (body.get("time") or body.get("timeSlot") or "").strip()  # "HH:MM"

    if len(name) < 2 or len(phone) < 10 or "@" not in email or not appt_type or date is None or not slot:
        return JsonResponse({"error": "Invalid booking data"}, status=400)

    # The chosen slot must be a real, future, still-free slot — this is where
    # double-bookings (against other web bookings AND CRM appointments) are caught.
    if not booking_slots.is_available(date, slot):
        return JsonResponse(
            {"error": "That time slot is no longer available — please choose another.",
             "slotTaken": True},
            status=409,
        )

    booking = WebBooking.objects.create(
        reference=_make_reference(),
        name=name,
        phone=phone,
        email=email,
        appointment_type=appt_type,
        appointment_date=date,
        appointment_time=slot,        # "HH:MM" → TimeField
        time_slot=slot,
        status="requested",
    )

    return JsonResponse({"reference": booking.reference}, status=201)


@require_http_methods(["GET"])
def get_booking(request, reference):
    try:
        booking = WebBooking.objects.get(reference=reference)
    except WebBooking.DoesNotExist:
        return JsonResponse({"error": "Booking not found"}, status=404)

    return JsonResponse({
        "reference":       booking.reference,
        "name":            booking.name,
        "appointmentType": booking.appointment_type,
        "appointmentDate": booking.appointment_date.isoformat(),
        "timeSlot":        booking.time_slot,
        "status":          booking.status,
    })
