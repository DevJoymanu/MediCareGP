from tasks.models import Task
from billing.models import Invoice
from django.utils import timezone


def global_context(request):
    if not request.user.is_authenticated:
        return {}
    today = timezone.now().date()
    pending_tasks_count = Task.objects.filter(done=False).count()
    overdue_invoices_count = Invoice.objects.filter(
        status__in=['Sent', 'Draft'], due_date__lt=today
    ).count()
    return {
        'pending_tasks_count': pending_tasks_count,
        'overdue_invoices_count': overdue_invoices_count,
    }
