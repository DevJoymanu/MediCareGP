from django.contrib import admin
from .models import Consultation, Provider, InvestigationRequest

@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ['patient','date','get_assessment']
    search_fields = ['patient__first_name', 'patient__last_name', 'assessment']
    list_filter = ['date', 'follow_up_date']
    def get_assessment(self, obj): return obj.assessment[:80] if obj.assessment else ''
    get_assessment.short_description = 'Assessment'


@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display  = ['name', 'kind', 'practice_no', 'email', 'is_active']
    list_filter   = ['kind', 'is_active']
    search_fields = ['name', 'practice_no', 'email']


@admin.register(InvestigationRequest)
class InvestigationRequestAdmin(admin.ModelAdmin):
    list_display  = ['consultation', 'kind', 'status', 'recipient_name', 'created_at', 'submitted_at']
    list_filter   = ['kind', 'status', 'created_at']
    search_fields = ['consultation__patient__first_name', 'consultation__patient__last_name', 'provider_name']
    readonly_fields = ['token', 'created_at', 'submitted_at', 'reviewed_at']
