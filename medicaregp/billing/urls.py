from django.urls import path
from . import views

urlpatterns = [
    path('',                    views.invoice_list,        name='invoice_list'),
    path('new/',                views.invoice_create,      name='invoice_create'),
    path('<int:pk>/',           views.invoice_detail,      name='invoice_detail'),
    path('<int:pk>/edit/',      views.invoice_edit,        name='invoice_edit'),
    path('<int:pk>/delete/',    views.invoice_delete,      name='invoice_delete'),
    path('<int:pk>/print/',     views.invoice_print,       name='invoice_print'),
    path('<int:pk>/send/',      views.invoice_send_email,  name='invoice_send_email'),
    path('<int:pk>/mark-paid/', views.invoice_mark_paid,   name='invoice_mark_paid'),
]
