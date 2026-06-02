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
    path('suggest/', views.suggest_prescriptions, name='suggest_prescriptions'),
    path('icd10/', views.search_icd10, name='search_icd10'),
]
