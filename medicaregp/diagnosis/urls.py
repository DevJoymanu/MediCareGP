from django.urls import path

from . import views

urlpatterns = [
    path('consultation/<int:consultation_pk>/', views.differential_capture, name='differential_capture'),
    path('result/<int:pk>/', views.differential_result, name='differential_result'),
    path('result/<int:pk>/confirm/', views.differential_confirm, name='differential_confirm'),
]
