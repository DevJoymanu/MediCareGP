from django import forms
from .models import Document


class DocumentForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super().clean()
        content = cleaned_data.get('content')
        attachment = cleaned_data.get('attachment')
        if not content and not attachment:
            raise forms.ValidationError('Add document content or upload an attachment.')
        return cleaned_data

    class Meta:
        model = Document
        exclude = ['date_issued']
        widgets = {
            'patient':    forms.Select(attrs={'class': 'crm-select', 'style': 'width:100%;'}),
            'doc_type':   forms.Select(attrs={'class': 'crm-select', 'style': 'width:100%;'}),
            'category':   forms.Select(attrs={'class': 'crm-select', 'style': 'width:100%;'}),
            'content':    forms.Textarea(attrs={'class': 'crm-input', 'rows': 8}),
            'issued_by':  forms.TextInput(attrs={'class': 'crm-input'}),
            'attachment': forms.ClearableFileInput(attrs={'class': 'crm-input'}),
        }
