from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from patients.models import Patient
from appointments.models import Appointment
from consultations.models import Consultation
from scripts.models import Document
from tasks.models import Task
from billing.models import Invoice
from consultations.models import InvestigationRequest
from appointments.models import WebBooking
from medicaregp.roles import is_doctor


# Path to the compiled Medical-Flow React site (built into Django static).
_WEBSITE_INDEX = settings.BASE_DIR / 'static' / 'website' / 'index.html'


def website_home(request):
    """Serve the public patient website (compiled React SPA) at the site root."""
    try:
        html = _WEBSITE_INDEX.read_text(encoding='utf-8')
    except FileNotFoundError:
        return HttpResponse(
            "<h1>Website not built yet</h1>"
            "<p>Run the gp-website build into <code>static/website/</code>. "
            "The CRM is at <a href='/app/'>/app/</a>.</p>",
            status=200,
        )
    return HttpResponse(html)


@login_required
def dashboard(request):
    today = timezone.now().date()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'toggle_task':
            task = get_object_or_404(Task, pk=request.POST.get('task_id'))
            task.done = not task.done
            task.save(update_fields=['done'])
        return redirect('dashboard')

    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    todays_appointments = Appointment.objects.filter(date=today).select_related('patient').order_by('time')
    pending_tasks = Task.objects.filter(done=False).select_related('patient').order_by('due_date')
    priority_order = {'High': 0, 'Medium': 1, 'Low': 2}
    pending_tasks = sorted(pending_tasks, key=lambda t: (priority_order.get(t.priority, 1), t.due_date))

    follow_ups = Consultation.objects.filter(
        follow_up_date__gte=today
    ).select_related('patient').order_by('follow_up_date')

    recent_patients = Patient.objects.order_by('-date_registered')[:4]

    context = {
        'today': today,
        'total_patients': Patient.objects.count(),
        'todays_appointments': todays_appointments,
        'todays_count': todays_appointments.count(),
        'scheduled_today': todays_appointments.filter(status='Scheduled').count(),
        'pending_tasks': pending_tasks[:4],
        'pending_tasks_count': len(pending_tasks),
        'follow_ups': follow_ups[:3],
        'recent_patients': recent_patients,
        'week_appointments': Appointment.objects.filter(date__gte=week_start, date__lte=week_end).count(),
        'week_consultations': Consultation.objects.filter(date__gte=week_start, date__lte=week_end).count(),
    }
    return render(request, 'dashboard.html', context)


@login_required
def analytics(request):
    from datetime import date
    today = timezone.now().date()

    # 14-day trend
    trend = []
    for i in range(13, -1, -1):
        d = today - timedelta(days=i)
        count = Appointment.objects.filter(date=d).count()
        trend.append({'day': d.strftime('%-d'), 'count': count, 'is_today': d == today})

    status_data = []
    total = Appointment.objects.count()
    for s, label in Appointment.STATUS_CHOICES:
        cnt = Appointment.objects.filter(status=s).count()
        status_data.append({
            'status': label,
            'count': cnt,
            'pct': round(cnt / total * 100) if total else 0,
            'color': {'Scheduled': '#3b82f6', 'Completed': '#22c55e', 'Cancelled': '#ef4444', 'No-Show': '#f59e0b'}.get(s, '#94a3b8'),
        })

    # Chronic conditions frequency
    cond_freq = {}
    for p in Patient.objects.all():
        for c in p.chronic_list():
            cond_freq[c] = cond_freq.get(c, 0) + 1
    top_conditions = sorted(cond_freq.items(), key=lambda x: -x[1])[:6]
    max_cond = max((v for _, v in top_conditions), default=1)

    patient_count = Patient.objects.count()
    all_patients = list(Patient.objects.all())
    with_aid      = sum(1 for p in all_patients if p.medical_aid_name)
    with_allergies= sum(1 for p in all_patients if p.allergies_list())
    with_chronic  = sum(1 for p in all_patients if p.chronic_list())
    female_count  = sum(1 for p in all_patients if p.gender == 'F')
    male_count    = sum(1 for p in all_patients if p.gender == 'M')

    patient_overview = [
        ('With Medical Aid',        with_aid,       '#22c55e'),
        ('With Allergies',          with_allergies, '#ef4444'),
        ('With Chronic Conditions', with_chronic,   '#f59e0b'),
        ('Female patients',         female_count,   '#ec4899'),
        ('Male patients',           male_count,     '#3b82f6'),
    ]

    context = {
        'trend': trend,
        'trend_max': max((d['count'] for d in trend), default=1),
        'status_data': status_data,
        'top_conditions': top_conditions,
        'max_cond': max_cond,
        'total_patients': patient_count,
        'total_appointments': total,
        'total_consultations': Consultation.objects.count(),
        'total_documents': Document.objects.count(),
        'patient_overview': patient_overview,
    }
    return render(request, 'analytics.html', context)
