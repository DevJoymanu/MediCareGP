from django.contrib import admin
from .models import Document

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['patient','category','doc_type','date_issued', 'has_attachment']
    list_filter = ['category', 'doc_type', 'date_issued']
    search_fields = ['patient__first_name', 'patient__last_name', 'content', 'issued_by']

    def has_attachment(self, obj):
        return bool(obj.attachment)
    has_attachment.boolean = True
    has_attachment.short_description = 'Attachment'
