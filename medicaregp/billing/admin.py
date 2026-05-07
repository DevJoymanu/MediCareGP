from django.contrib import admin
from .models import Invoice, InvoiceItem


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display  = ['invoice_number', 'patient', 'date_issued', 'due_date', 'status']
    list_filter   = ['status', 'date_issued']
    search_fields = ['invoice_number', 'patient__first_name', 'patient__last_name']
    inlines       = [InvoiceItemInline]
