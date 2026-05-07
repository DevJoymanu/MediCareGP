from django.contrib import admin
from .models import Patient

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['last_name','first_name','phone','medical_aid_name','date_registered']
    search_fields = ['first_name','last_name','id_number','phone']
    list_filter = ['gender','date_registered']
