from django.contrib import admin
from .models import Appointment, WebBooking

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['patient','date','time','status']
    list_filter = ['status','date']
    search_fields = ['patient__first_name', 'patient__last_name', 'reason']


@admin.register(WebBooking)
class WebBookingAdmin(admin.ModelAdmin):
    list_display = ['reference', 'name', 'appointment_type', 'appointment_date', 'time_slot', 'status', 'created_at']
    list_filter = ['status', 'appointment_type', 'appointment_date']
    search_fields = ['reference', 'name', 'phone', 'email']
    readonly_fields = ['created_at', 'reviewed_at']
