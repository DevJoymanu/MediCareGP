from django.urls import path
from . import checkin_views

urlpatterns = [
    path('<slug:token>/',               checkin_views.checkin_form,         name='checkin_form'),
    path('<slug:token>/lookup/',        checkin_views.checkin_lookup,       name='checkin_lookup'),
    path('<slug:token>/confirm/<int:pk>/', checkin_views.checkin_confirmation, name='checkin_confirmation'),
    path('phase2/<uuid:phase2_token>/', checkin_views.checkin_phase2,       name='checkin_phase2'),
]
