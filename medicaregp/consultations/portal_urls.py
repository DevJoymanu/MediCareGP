from django.urls import path
from . import portal_views

urlpatterns = [
    path('<uuid:token>/',      portal_views.result_portal, name='result_portal'),
    path('<uuid:token>/done/', portal_views.result_done,   name='result_done'),
]
