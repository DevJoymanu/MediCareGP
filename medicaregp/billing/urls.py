from django.urls import path
from . import views

urlpatterns = [
    path('',                                views.invoice_list,        name='invoice_list'),
    path('new/',                            views.invoice_create,      name='invoice_create'),
    path('<int:pk>/',                       views.invoice_detail,      name='invoice_detail'),
    path('<int:pk>/edit/',                  views.invoice_edit,        name='invoice_edit'),
    path('<int:pk>/delete/',                views.invoice_delete,      name='invoice_delete'),
    path('<int:pk>/print/',                 views.invoice_print,       name='invoice_print'),
    path('<int:pk>/send/',                  views.invoice_send_email,  name='invoice_send_email'),
    path('<int:pk>/mark-paid/',             views.invoice_mark_paid,   name='invoice_mark_paid'),

    # Payments & receipts
    path('<int:pk>/add-payment/',           views.payment_add,         name='payment_add'),
    path('receipt/<int:payment_pk>/print/', views.receipt_print,       name='receipt_print'),

    # Claim submissions
    path('<int:pk>/submit-claim/',          views.claim_submit,        name='claim_submit'),
    path('claim/<int:claim_pk>/update/',    views.claim_update,        name='claim_update'),

    # ERA import & EDI / BHF export
    path('era-import/',                     views.era_import,          name='era_import'),
    path('<int:pk>/edi-export/',            views.edi_export,          name='edi_export'),
    path('<int:pk>/bhf/',                   views.bhf_export,          name='bhf_export'),

    # Versioned tariff catalogue (medical / surgical)
    path('tariffs/',                        views.tariff_list,         name='tariff_list'),
    path('api/tariff-rate/',                views.tariff_rate_lookup,  name='tariff_rate_lookup'),

    # AJAX helpers for invoice form
    path('api/patient-consultations/<int:patient_id>/', views.patient_consultations, name='patient_consultations'),
    path('api/consultation-icd10/<int:consultation_id>/', views.consultation_icd10,  name='consultation_icd10'),
    path('api/nappi-search/',                            views.search_nappi,         name='search_nappi'),
]
