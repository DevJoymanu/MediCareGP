from django.urls import path
from . import views
urlpatterns = [
    path('', views.document_list, name='document_list'),
    path('new/', views.document_create, name='document_create'),
    path('<int:pk>/edit/', views.document_edit, name='document_edit'),
    path('<int:pk>/', views.document_detail, name='document_detail'),
    path('<int:pk>/delete/', views.document_delete, name='document_delete'),
    path('<int:pk>/print/', views.document_print, name='document_print'),
]
