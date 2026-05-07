from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Task
from .forms import TaskForm


@login_required
def task_list(request):
    today = timezone.now().date()
    tasks = Task.objects.select_related('patient').all()
    pending = tasks.filter(done=False).order_by(
        'due_date'
    )
    # Sort pending by priority then date
    priority_order = {'High': 0, 'Medium': 1, 'Low': 2}
    pending = sorted(pending, key=lambda t: (priority_order.get(t.priority, 1), t.due_date))
    done = tasks.filter(done=True).order_by('-due_date')

    form = TaskForm()
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            form = TaskForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Task added.')
                return redirect('task_list')
        elif action == 'toggle':
            task_id = request.POST.get('task_id')
            task = get_object_or_404(Task, pk=task_id)
            task.done = not task.done
            task.save(update_fields=['done'])
            return redirect('task_list')
        elif action == 'delete':
            task_id = request.POST.get('task_id')
            task = get_object_or_404(Task, pk=task_id)
            task.delete()
            messages.success(request, 'Task removed.')
            return redirect('task_list')

    total_pending = len(pending)
    priority_data = [
        ('High',   '#ef4444', sum(1 for t in pending if t.priority == 'High')),
        ('Medium', '#f59e0b', sum(1 for t in pending if t.priority == 'Medium')),
        ('Low',    '#22c55e', sum(1 for t in pending if t.priority == 'Low')),
    ]

    return render(request, 'tasks/task_list.html', {
        'pending': pending,
        'done': done,
        'form': form,
        'today': today,
        'priority_data': priority_data,
        'total_pending': total_pending,
    })
