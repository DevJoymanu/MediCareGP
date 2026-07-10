from django.urls import path

from . import views

urlpatterns = [
    path('consultation/<int:consultation_pk>/', views.differential_capture, name='differential_capture'),
    path('result/<int:pk>/', views.differential_result, name='differential_result'),
    path('result/<int:pk>/confirm/', views.differential_confirm, name='differential_confirm'),

    # Consultation workspace (single-screen) + its JSON endpoints
    path('workspace/new/', views.workspace_new, name='diagnosis_workspace_new'),
    path('consultation/<int:consultation_pk>/workspace/', views.workspace, name='diagnosis_workspace'),
    path('consultation/<int:consultation_pk>/workspace/run/', views.workspace_run, name='workspace_run'),
    path('consultation/<int:consultation_pk>/workspace/confirm/', views.workspace_confirm, name='workspace_confirm'),
    path('consultation/<int:consultation_pk>/workspace/notes/', views.workspace_save_notes, name='workspace_save_notes'),
    path('consultation/<int:consultation_pk>/workspace/complaint-check/', views.workspace_complaint_check, name='workspace_complaint_check'),
    path('icd10/search/', views.icd10_search, name='icd10_search'),
    path('patients/search/', views.workspace_patient_search, name='workspace_patient_search'),
    path('patients/appointments/', views.workspace_patient_appointments, name='workspace_patient_appointments'),
]
