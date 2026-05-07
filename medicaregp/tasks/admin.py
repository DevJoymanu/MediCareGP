from django.contrib import admin
from .models import Task

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'patient', 'due_date', 'priority', 'done']
    list_filter = ['priority', 'done', 'due_date']
    search_fields = ['title', 'patient__first_name', 'patient__last_name']
