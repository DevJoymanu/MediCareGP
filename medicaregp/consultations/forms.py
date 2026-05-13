from django import forms
from appointments.models import Appointment
from .models import Consultation

INPUT    = 'crm-input'
SELECT   = 'crm-select'
TEXTAREA = 'crm-input'


class ConsultationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        patient_id = None
        if self.is_bound:
            patient_id = self.data.get('patient')
        elif self.instance.pk:
            patient_id = self.instance.patient_id
        else:
            patient_id = self.initial.get('patient')

        if patient_id:
            self.fields['appointment'].queryset = Appointment.objects.filter(
                patient_id=patient_id).order_by('-date', '-time')
        else:
            self.fields['appointment'].queryset = Appointment.objects.none()

    class Meta:
        model  = Consultation
        fields = [
            'patient', 'appointment',
            'weight_kg', 'bp_reading',
            'chief_complaint', 'review', 'subjective', 'assessment',
            'objective', 'differential_diagnosis', 'plan',
            'icd10_code', 'prescriptions', 'follow_up_date',
            'referral_to', 'referral_reason',
            'lab_requests', 'radiology_requests',
            'sick_note_issued', 'sick_note_days', 'sick_note_start_date', 'sick_note_employer',
        ]
        widgets = {
            'patient':               forms.Select(attrs={'class': SELECT, 'style': 'width:100%;'}),
            'appointment':           forms.Select(attrs={'class': SELECT, 'style': 'width:100%;'}),
            'weight_kg':             forms.NumberInput(attrs={'class': INPUT, 'step': '0.1', 'placeholder': 'kg'}),
            'bp_reading':            forms.TextInput(attrs={'class': INPUT, 'placeholder': '120/80'}),
            'chief_complaint':       forms.Textarea(attrs={'class': TEXTAREA, 'rows': 3, 'placeholder': 'Reason for visit…'}),
            'review':                forms.Textarea(attrs={'class': TEXTAREA, 'rows': 4, 'placeholder': 'How is the patient progressing? Response to treatment, medication adherence, any concerns since last visit…'}),
            'subjective':            forms.Textarea(attrs={'class': TEXTAREA, 'rows': 10, 'placeholder': 'Clinical notes — presenting complaint, history, examination findings, results discussed…'}),
            'assessment':            forms.Textarea(attrs={'class': TEXTAREA, 'rows': 3, 'placeholder': 'Assessment / Diagnosis'}),
            'objective':             forms.Textarea(attrs={'class': TEXTAREA, 'rows': 3, 'placeholder': 'Objective findings'}),
            'differential_diagnosis':forms.Textarea(attrs={'class': TEXTAREA, 'rows': 2, 'placeholder': 'Alternative diagnoses considered…'}),
            'plan':                  forms.Textarea(attrs={'class': TEXTAREA, 'rows': 3, 'placeholder': 'Management plan'}),
            'icd10_code':            forms.TextInput(attrs={'class': INPUT, 'placeholder': 'e.g. J06.9'}),
            'prescriptions':         forms.Textarea(attrs={'class': TEXTAREA, 'rows': 8, 'placeholder': 'Azithromycin 500mg — 1 daily × 3/7\nPredn 20mg — 1 daily × 5/7\nBenylin …'}),
            'follow_up_date':        forms.DateInput(attrs={'class': INPUT, 'type': 'date'}),
            'referral_to':           forms.TextInput(attrs={'class': INPUT, 'placeholder': 'e.g. Dr. A. Nkosi — Cardiologist'}),
            'referral_reason':       forms.Textarea(attrs={'class': TEXTAREA, 'rows': 2}),
            'lab_requests':          forms.Textarea(attrs={'class': TEXTAREA, 'rows': 4, 'placeholder': 'TSH\nLFTs\nU/E + Creat\nLipogram\nFBC'}),
            'radiology_requests':    forms.Textarea(attrs={'class': TEXTAREA, 'rows': 2, 'placeholder': 'e.g. Chest X-ray PA'}),
            'sick_note_issued':      forms.CheckboxInput(attrs={'class': 'crm-checkbox'}),
            'sick_note_days':        forms.NumberInput(attrs={'class': INPUT, 'min': 1, 'placeholder': 'Days'}),
            'sick_note_start_date':  forms.DateInput(attrs={'class': INPUT, 'type': 'date'}),
            'sick_note_employer':    forms.TextInput(attrs={'class': INPUT, 'placeholder': 'Employer / company name'}),
        }
