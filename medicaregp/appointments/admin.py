from django.contrib import admin
from .models import Appointment

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['patient','date','time','status']
    list_filter = ['status','date']
    search_fields = ['patient__first_name', 'patient__last_name', 'reason']
