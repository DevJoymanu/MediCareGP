from django.contrib import admin
from .models import Patient

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['last_name','first_name','phone','medical_aid_name','date_registered']
    search_fields = ['first_name','last_name','id_number','phone']
    list_filter = ['gender','date_registered']


from .models import MedicalAidPlanConfig, BiometricTemplate


@admin.register(MedicalAidPlanConfig)
class MedicalAidPlanConfigAdmin(admin.ModelAdmin):
    list_display = ['scheme_name', 'plan_name', 'visits_per_year', 'warn_at', 'notes']
    list_editable = ['visits_per_year', 'warn_at']
    search_fields = ['scheme_name', 'plan_name']


@admin.register(BiometricTemplate)
class BiometricTemplateAdmin(admin.ModelAdmin):
    list_display = ['patient', 'enrolled_at']
    search_fields = ['patient__first_name', 'patient__last_name']
    readonly_fields = ['template_hash', 'enrolled_at']
