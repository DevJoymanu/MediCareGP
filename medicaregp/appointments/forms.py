from django import forms
from .models import Appointment


class AppointmentForm(forms.ModelForm):
    class Meta:
        model  = Appointment
        fields = '__all__'
        widgets = {
            'patient':              forms.Select(attrs={'class': 'crm-select', 'style': 'width:100%;'}),
            'date':                 forms.DateInput(attrs={'class': 'crm-input', 'type': 'date'}),
            'time':                 forms.TimeInput(attrs={'class': 'crm-input', 'type': 'time'}),
            'reason':               forms.TextInput(attrs={'class': 'crm-input'}),
            'status':               forms.Select(attrs={'class': 'crm-select', 'style': 'width:100%;'}),
            'visit_type':           forms.Select(attrs={'class': 'crm-select', 'style': 'width:100%;'}),
            'notes':                forms.Textarea(attrs={'class': 'crm-input', 'rows': 3}),
            'referring_doctor':     forms.TextInput(attrs={'class': 'crm-input', 'placeholder': 'e.g. Dr. B. Adams — GP, Cape Town'}),
            'authorization_number': forms.TextInput(attrs={'class': 'crm-input', 'placeholder': 'Medical aid auth. number'}),
            'icd10_code':           forms.TextInput(attrs={'class': 'crm-input', 'placeholder': 'e.g. J45, I10'}),
        }


class WalkInForm(forms.ModelForm):
    class Meta:
        model  = Appointment
        fields = ['patient', 'reason']
        widgets = {
            'patient': forms.Select(attrs={'class': 'crm-select', 'style': 'width:100%;'}),
            'reason':  forms.TextInput(attrs={'class': 'crm-input', 'placeholder': 'e.g. Headache, follow-up, chest pain'}),
        }
