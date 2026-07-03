from django.urls import path

from . import views

urlpatterns = [
    path('verify/<int:patient_pk>/', views.verify_member, name='medaid_verify_member'),
    path('submit-claim/<int:invoice_pk>/', views.submit_claim, name='medaid_submit_claim'),
]
