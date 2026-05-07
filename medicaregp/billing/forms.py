from django import forms
from django.forms import inlineformset_factory
from .models import Invoice, InvoiceItem


class InvoiceForm(forms.ModelForm):
    class Meta:
        model  = Invoice
        fields = ['patient', 'invoice_number', 'date_issued', 'due_date', 'status',
                  'icd10_code', 'procedure_codes', 'authorization_number',
                  'receipt_number', 'amount_paid', 'notes', 'issued_by']
        widgets = {
            'patient':              forms.Select(attrs={'class': 'crm-select', 'style': 'width:100%;'}),
            'invoice_number':       forms.TextInput(attrs={'class': 'crm-input'}),
            'date_issued':          forms.DateInput(attrs={'class': 'crm-input', 'type': 'date'}),
            'due_date':             forms.DateInput(attrs={'class': 'crm-input', 'type': 'date'}),
            'status':               forms.Select(attrs={'class': 'crm-select', 'style': 'width:100%;'}),
            'icd10_code':           forms.TextInput(attrs={'class': 'crm-input', 'placeholder': 'e.g. I10, E11.9'}),
            'procedure_codes':      forms.Textarea(attrs={'class': 'crm-input', 'rows': 2, 'placeholder': 'e.g. 0190 — Consultation\n0191 — Follow-up'}),
            'authorization_number': forms.TextInput(attrs={'class': 'crm-input', 'placeholder': 'Medical aid auth. number'}),
            'receipt_number':       forms.TextInput(attrs={'class': 'crm-input', 'placeholder': 'Receipt / payment reference'}),
            'amount_paid':          forms.NumberInput(attrs={'class': 'crm-input', 'step': '0.01', 'min': '0', 'placeholder': '0.00'}),
            'notes':                forms.Textarea(attrs={'class': 'crm-input', 'rows': 2}),
            'issued_by':            forms.TextInput(attrs={'class': 'crm-input'}),
        }


class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model  = InvoiceItem
        fields = ['description', 'procedure_code', 'quantity', 'unit_price']
        widgets = {
            'description':    forms.TextInput(attrs={'class': 'crm-input', 'placeholder': 'e.g. Consultation fee'}),
            'procedure_code': forms.TextInput(attrs={'class': 'crm-input', 'placeholder': '0190'}),
            'quantity':       forms.NumberInput(attrs={'class': 'crm-input', 'step': '0.01', 'min': '0'}),
            'unit_price':     forms.NumberInput(attrs={'class': 'crm-input', 'step': '0.01', 'min': '0'}),
        }


InvoiceItemFormSet = inlineformset_factory(
    Invoice, InvoiceItem,
    form=InvoiceItemForm,
    extra=3,
    can_delete=True,
    min_num=1,
    validate_min=True,
)


class SendEmailForm(forms.Form):
    to_email = forms.EmailField(
        label='Send to',
        widget=forms.EmailInput(attrs={'class': 'crm-input', 'placeholder': 'patient@email.com'})
    )
    subject = forms.CharField(
        label='Subject',
        widget=forms.TextInput(attrs={'class': 'crm-input'})
    )
    message = forms.CharField(
        label='Message',
        widget=forms.Textarea(attrs={'class': 'crm-input', 'rows': 4})
    )
