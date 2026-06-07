"""Built-in WebRTC video consultation — mounted at /video/ (see medicaregp/urls.py)."""
from django.urls import path
from . import video_views

urlpatterns = [
    path('appointment/<int:pk>/',          video_views.doctor_room,  name='video_doctor_room'),
    path('join/<uuid:patient_token>/',     video_views.patient_room, name='video_patient_room'),
    path('turn-test/',                     video_views.turn_test,     name='video_turn_test'),
    path('turn-test/ice/',                 video_views.turn_test_ice, name='video_turn_test_ice'),
    path('<uuid:room_id>/signal/',         video_views.signal,       name='video_signal'),
    path('<uuid:room_id>/ice/',            video_views.ice_config,   name='video_ice'),
]
