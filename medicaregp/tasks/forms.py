from django import forms
from .models import Task


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'patient', 'due_date', 'priority']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'crm-input', 'placeholder': 'Task description…'}),
            'patient': forms.Select(attrs={'class': 'crm-select'}),
            'due_date': forms.DateInput(attrs={'class': 'crm-input', 'type': 'date'}),
            'priority': forms.Select(attrs={'class': 'crm-select'}),
        }
