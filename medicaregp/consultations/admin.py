from django.contrib import admin
from .models import Consultation

@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ['patient','date','get_assessment']
    search_fields = ['patient__first_name', 'patient__last_name', 'assessment']
    list_filter = ['date', 'follow_up_date']
    def get_assessment(self, obj): return obj.assessment[:80] if obj.assessment else ''
    get_assessment.short_description = 'Assessment'
