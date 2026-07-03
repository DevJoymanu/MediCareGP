from django.urls import path
from . import views
urlpatterns = [
    path('', views.patient_list, name='patient_list'),
    path('checkin/', views.patient_checkin, name='patient_checkin'),
    path('new/', views.patient_create, name='patient_create'),
    path('<int:pk>/', views.patient_detail, name='patient_detail'),
    path('<int:pk>/edit/', views.patient_edit, name='patient_edit'),
    path('<int:pk>/delete/', views.patient_delete, name='patient_delete'),
    path('<int:pk>/vitals/', views.vitals_add, name='vitals_add'),

    # Front office
    path('biometric/', views.biometric_identify, name='biometric_identify'),
    path('<int:pk>/biometric/enrol/', views.biometric_enrol, name='biometric_enrol'),
    path('<int:pk>/print-all/', views.patient_print_all, name='patient_print_all'),
]
