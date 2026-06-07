"""Public website API — mounted at /api/ (see medicaregp/urls.py)."""
from django.urls import path
from . import api_views

urlpatterns = [
    path('availability', api_views.availability, name='api_availability'),
    path('bookings', api_views.create_booking, name='api_create_booking'),
    path('bookings/<str:reference>', api_views.get_booking, name='api_get_booking'),
]
