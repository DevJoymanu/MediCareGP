from django import forms
from django.forms import inlineformset_factory
from .models import Patient, Vitals, FamilyMember

INPUT    = 'crm-input'
SELECT   = 'crm-select'
TEXTAREA = 'crm-input'


class PatientForm(forms.ModelForm):
    class Meta:
        model   = Patient
        exclude = ['date_registered', 'file_number']
        widgets = {
            # Personal
            'last_name':            forms.TextInput(attrs={'class': INPUT}),
            'first_name':           forms.TextInput(attrs={'class': INPUT}),
            'title':                forms.Select(attrs={'class': SELECT, 'style': 'width:100%;'}),
            'date_of_birth':        forms.DateInput(attrs={'class': INPUT, 'type': 'date'}),
            'gender':               forms.Select(attrs={'class': SELECT, 'style': 'width:100%;'}),
            'id_type':              forms.Select(attrs={'class': SELECT, 'style': 'width:100%;'}),
            'id_number':            forms.TextInput(attrs={'class': INPUT, 'placeholder': 'SA ID or passport number'}),
            'occupation':           forms.TextInput(attrs={'class': INPUT, 'placeholder': 'e.g. Teacher, Nurse'}),
            'home_language':        forms.TextInput(attrs={'class': INPUT, 'placeholder': 'e.g. Zulu, English'}),
            'marital_status':       forms.Select(attrs={'class': SELECT, 'style': 'width:100%;'}),
            # Contact
            'alt_phone':            forms.TextInput(attrs={'class': INPUT, 'placeholder': 'Home number Tel. (H)'}),
            'work_phone':           forms.TextInput(attrs={'class': INPUT, 'placeholder': 'Work number Tel. (W)'}),
            'phone':                forms.TextInput(attrs={'class': INPUT, 'placeholder': '+27 xx xxx xxxx'}),
            'email':                forms.EmailInput(attrs={'class': INPUT}),
            # Person responsible
            'postal_address':       forms.Textarea(attrs={'class': TEXTAREA, 'rows': 2}),
            'address':              forms.Textarea(attrs={'class': TEXTAREA, 'rows': 2}),
            'employer':             forms.TextInput(attrs={'class': INPUT, 'placeholder': 'e.g. Dept. of Education'}),
            'work_address':         forms.Textarea(attrs={'class': TEXTAREA, 'rows': 2}),
            # Next of kin
            'next_of_kin_name':         forms.TextInput(attrs={'class': INPUT}),
            'next_of_kin_relationship':  forms.TextInput(attrs={'class': INPUT, 'placeholder': 'e.g. Spouse, Parent, Sibling'}),
            'next_of_kin_address':       forms.Textarea(attrs={'class': TEXTAREA, 'rows': 2}),
            'next_of_kin_phone':         forms.TextInput(attrs={'class': INPUT, 'placeholder': '+27 xx xxx xxxx'}),
            'next_of_kin_email':         forms.EmailInput(attrs={'class': INPUT}),
            # Referred by
            'referred_by_name':     forms.TextInput(attrs={'class': INPUT}),
            'referred_by_phone':    forms.TextInput(attrs={'class': INPUT, 'placeholder': '+27 xx xxx xxxx'}),
            'referred_by_email':    forms.EmailInput(attrs={'class': INPUT}),
            # Medical aid
            'medical_aid_name':     forms.TextInput(attrs={'class': INPUT, 'placeholder': 'e.g. Discovery Health'}),
            'medical_aid_plan':     forms.TextInput(attrs={'class': INPUT, 'placeholder': 'e.g. Coastal Core'}),
            'medical_aid_number':   forms.TextInput(attrs={'class': INPUT}),
            'principal_member_name':forms.TextInput(attrs={'class': INPUT}),
            'principal_member_id':  forms.TextInput(attrs={'class': INPUT}),
            'dependant_code':       forms.TextInput(attrs={'class': INPUT, 'placeholder': 'e.g. 01'}),
            # Clinical
            'blood_type':           forms.Select(attrs={'class': SELECT, 'style': 'width:100%;'}),
            'allergies':            forms.TextInput(attrs={'class': INPUT, 'placeholder': 'e.g. Penicillin, Sulfa drugs'}),
            'chronic_conditions':   forms.TextInput(attrs={'class': INPUT, 'placeholder': 'e.g. Hypertension, Type 2 Diabetes'}),
            'current_medication':   forms.Textarea(attrs={'class': TEXTAREA, 'rows': 3, 'placeholder': 'List current medication and dosages'}),
            'previous_surgeries':   forms.Textarea(attrs={'class': TEXTAREA, 'rows': 3, 'placeholder': 'e.g. Appendectomy 2015, Cholecystectomy 2019'}),
            'family_history':       forms.Textarea(attrs={'class': TEXTAREA, 'rows': 3, 'placeholder': 'e.g. Father — T2DM, hypertension; Mother — breast cancer'}),
            # Lifestyle
            'smoking_status':       forms.Select(attrs={'class': SELECT, 'style': 'width:100%;'}),
            'alcohol_use':          forms.Select(attrs={'class': SELECT, 'style': 'width:100%;'}),
            'substance_use':        forms.Textarea(attrs={'class': TEXTAREA, 'rows': 2}),
            # Consent
            'popia_consent':        forms.CheckboxInput(attrs={'class': 'crm-checkbox'}),
            'consent_to_treat':     forms.CheckboxInput(attrs={'class': 'crm-checkbox'}),
        }


class FamilyMemberForm(forms.ModelForm):
    class Meta:
        model  = FamilyMember
        fields = ['name', 'gender', 'date_of_birth', 'allergies', 'notes']
        widgets = {
            'name':          forms.TextInput(attrs={'class': INPUT, 'placeholder': 'Full name'}),
            'gender':        forms.Select(attrs={'class': SELECT, 'style': 'width:100%;'}),
            'date_of_birth': forms.DateInput(attrs={'class': INPUT, 'type': 'date'}),
            'allergies':     forms.TextInput(attrs={'class': INPUT, 'placeholder': 'e.g. Penicillin'}),
            'notes':         forms.TextInput(attrs={'class': INPUT, 'placeholder': 'Other notes'}),
        }


FamilyMemberFormSet = inlineformset_factory(
    Patient, FamilyMember,
    form=FamilyMemberForm,
    extra=1,
    can_delete=True,
)


class VitalsForm(forms.ModelForm):
    class Meta:
        model  = Vitals
        fields = ['date', 'blood_pressure', 'bp_systolic', 'bp_diastolic',
                  'pulse', 'weight', 'height', 'temperature', 'oxygen_saturation',
                  'blood_glucose', 'recorded_by']
        widgets = {
            'date':              forms.DateInput(attrs={'class': INPUT, 'type': 'date'}),
            'blood_pressure':    forms.TextInput(attrs={'class': INPUT, 'placeholder': 'e.g. 120/80'}),
            'bp_systolic':       forms.NumberInput(attrs={'class': INPUT, 'placeholder': 'Systolic'}),
            'bp_diastolic':      forms.NumberInput(attrs={'class': INPUT, 'placeholder': 'Diastolic'}),
            'pulse':             forms.NumberInput(attrs={'class': INPUT, 'placeholder': 'bpm'}),
            'weight':            forms.NumberInput(attrs={'class': INPUT, 'step': '0.1', 'placeholder': 'kg'}),
            'height':            forms.NumberInput(attrs={'class': INPUT, 'placeholder': 'cm'}),
            'temperature':       forms.NumberInput(attrs={'class': INPUT, 'step': '0.1', 'placeholder': '°C'}),
            'oxygen_saturation': forms.NumberInput(attrs={'class': INPUT, 'placeholder': '%'}),
            'blood_glucose':     forms.NumberInput(attrs={'class': INPUT, 'step': '0.1', 'placeholder': 'mmol/L'}),
            'recorded_by':       forms.TextInput(attrs={'class': INPUT}),
        }
