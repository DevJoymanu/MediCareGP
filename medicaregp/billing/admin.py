from django.contrib import admin
from .models import Invoice, InvoiceItem, Payment, ClaimSubmission


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1


class PaymentInline(admin.TabularInline):
    model  = Payment
    extra  = 0
    fields = ['date', 'amount', 'method', 'reference', 'receipt_number']
    readonly_fields = ['receipt_number']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display  = ['invoice_number', 'patient', 'date_issued', 'due_date', 'status']
    list_filter   = ['status', 'date_issued']
    search_fields = ['invoice_number', 'patient__first_name', 'patient__last_name']
    inlines       = [InvoiceItemInline, PaymentInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display  = ['receipt_number', 'invoice', 'date', 'amount', 'method']
    list_filter   = ['method', 'date']
    search_fields = ['receipt_number', 'invoice__invoice_number']
    readonly_fields = ['receipt_number']


@admin.register(ClaimSubmission)
class ClaimSubmissionAdmin(admin.ModelAdmin):
    list_display  = ['invoice', 'scheme_name', 'status', 'submitted_at']
    list_filter   = ['status', 'scheme_name']
    search_fields = ['invoice__invoice_number', 'scheme_name']
