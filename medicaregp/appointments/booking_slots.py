"""
Bookable time-slot logic shared by the public website API.

A slot is identified by its "HH:MM" start time. It is considered TAKEN when any
active Appointment OR any live WebBooking occupies that exact date + time — so a
website booking and a CRM appointment can never land on the same slot.
"""
from datetime import datetime, timedelta, time as dtime

from django.conf import settings
from django.utils import timezone

from .models import Appointment, WebBooking

# Appointment statuses that free the slot up again.
_FREE_APPT_STATUSES = ['Cancelled', 'No-Show']
# WebBooking statuses that still hold the slot. 'converted' is excluded because it
# has already created an Appointment (counted above), and 'cancelled' is freed.
_HOLDING_WEB_STATUSES = ['requested', 'pending_payment', 'paid']


def _parse(hhmm):
    h, m = hhmm.split(':')
    return dtime(int(h), int(m))


def generate_slots():
    """All bookable "HH:MM" slot labels for a normal day, in order."""
    slots = []
    step = settings.BOOKING_SLOT_MINUTES
    anchor = datetime(2000, 1, 1)
    for start, end in settings.BOOKING_HOURS:
        cur = datetime.combine(anchor, _parse(start))
        end_dt = datetime.combine(anchor, _parse(end))
        while cur < end_dt:
            slots.append(cur.time().strftime('%H:%M'))
            cur += timedelta(minutes=step)
    return slots


def taken_times(date):
    """Set of "HH:MM" labels already occupied on `date`."""
    appt_times = (Appointment.objects
                  .filter(date=date)
                  .exclude(status__in=_FREE_APPT_STATUSES)
                  .values_list('time', flat=True))
    web_times = (WebBooking.objects
                 .filter(appointment_date=date, status__in=_HOLDING_WEB_STATUSES)
                 .exclude(appointment_time__isnull=True)
                 .values_list('appointment_time', flat=True))
    taken = set()
    for t in list(appt_times) + list(web_times):
        if t:
            taken.add(t.strftime('%H:%M'))
    return taken


def availability(date):
    """List of {time, available} for every slot on `date` (past slots today are unavailable)."""
    taken = taken_times(date)
    now = timezone.localtime()
    is_today = (date == now.date())
    out = []
    for slot in generate_slots():
        too_late = is_today and _parse(slot) <= now.time()
        out.append({'time': slot, 'available': (slot not in taken) and not too_late})
    return out


def is_available(date, hhmm):
    """True only if `hhmm` is a real, free, not-in-the-past slot on `date`."""
    return any(s['time'] == hhmm and s['available'] for s in availability(date))
