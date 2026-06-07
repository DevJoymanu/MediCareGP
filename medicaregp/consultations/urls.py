from django.urls import path
from . import views
urlpatterns = [
    path('', views.consultation_list, name='consultation_list'),
    path('new/', views.consultation_create, name='consultation_create'),
    path('<int:pk>/', views.consultation_detail, name='consultation_detail'),
    path('<int:pk>/edit/', views.consultation_edit, name='consultation_edit'),
    path('<int:pk>/delete/', views.consultation_delete, name='consultation_delete'),
    path('<int:pk>/review/', views.consultation_review, name='consultation_review'),
    path('<int:pk>/print/', views.consultation_print, name='consultation_print'),
    path('<int:pk>/sick-note/pdf/', views.sick_note_pdf, name='sick_note_pdf'),
    path('<int:pk>/sick-note/email/', views.sick_note_email, name='sick_note_email'),
    path('<int:pk>/lab-request/pdf/', views.lab_request_pdf, name='lab_request_pdf'),
    path('<int:pk>/radiology-request/pdf/', views.radiology_request_pdf, name='radiology_request_pdf'),
    path('<int:pk>/lab-request/email/', views.lab_request_email, name='lab_request_email'),
    path('<int:pk>/radiology-request/email/', views.radiology_request_email, name='radiology_request_email'),
    path('<int:pk>/prepare-request/', views.prepare_request, name='prepare_request'),

    # ── Investigation results review ────────────────────────────────────────
    path('investigations/pending/', views.investigations_pending, name='investigations_pending'),
    path('investigations/<int:pk>/review/', views.investigation_review, name='investigation_review'),
    path('investigations/<int:pk>/confirm/', views.investigation_confirm, name='investigation_confirm'),
    path('investigations/<int:pk>/decline/', views.investigation_decline, name='investigation_decline'),
    path('suggest/', views.suggest_prescriptions, name='suggest_prescriptions'),
    path('icd10/', views.search_icd10, name='search_icd10'),

    # ── Referral providers ──────────────────────────────────────────────────
    path('providers/',             views.provider_list,   name='provider_list'),
    path('providers/new/',         views.provider_create, name='provider_create'),
    path('providers/<int:pk>/edit/', views.provider_edit, name='provider_edit'),
]
