from tasks.models import Task
from billing.models import Invoice
from consultations.models import InvestigationRequest
from appointments.models import WebBooking
from django.utils import timezone


def global_context(request):
    if not request.user.is_authenticated:
        return {}
    from medicaregp.roles import is_doctor
    today = timezone.now().date()
    pending_tasks_count = Task.objects.filter(done=False).count()
    overdue_invoices_count = Invoice.objects.filter(
        status__in=['Sent', 'Draft'], due_date__lt=today
    ).count()
    pending_results_count = InvestigationRequest.objects.filter(status='submitted').count()
    web_bookings_count = WebBooking.objects.filter(status__in=WebBooking.ACTION_STATUSES).count()
    return {
        'is_doctor': is_doctor(request.user),
        'pending_tasks_count': pending_tasks_count,
        'overdue_invoices_count': overdue_invoices_count,
        'pending_results_count': pending_results_count,
        'web_bookings_count': web_bookings_count,
    }
