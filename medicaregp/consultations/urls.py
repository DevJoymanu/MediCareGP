from django.urls import path
from . import views
urlpatterns = [
    path('', views.consultation_list, name='consultation_list'),
    path('new/', views.consultation_create, name='consultation_create'),
    path('<int:pk>/', views.consultation_detail, name='consultation_detail'),
    path('<int:pk>/edit/', views.consultation_edit, name='consultation_edit'),
    path('<int:pk>/delete/', views.consultation_delete, name='consultation_delete'),
    path('<int:pk>/print/', views.consultation_print, name='consultation_print'),
]
