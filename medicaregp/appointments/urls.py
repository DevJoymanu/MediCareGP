from django.urls import path
from . import views
from . import checkin_views
urlpatterns = [
    path('', views.appointment_list, name='appointment_list'),
    path('new/', views.appointment_create, name='appointment_create'),
    path('walk-in/', views.walk_in_create, name='walk_in_create'),
    path('waiting-room/', views.waiting_room, name='waiting_room'),
    path('waiting-room/status/', views.waiting_room_status, name='waiting_room_status'),
    path('<int:pk>/', views.appointment_detail, name='appointment_detail'),
    path('<int:pk>/edit/', views.appointment_edit, name='appointment_edit'),
    path('<int:pk>/status/', views.appointment_set_status, name='appointment_set_status'),
    path('<int:pk>/check-in/', views.appointment_check_in, name='appointment_check_in'),
    path('<int:pk>/start-consultation/', views.appointment_start_consultation, name='appointment_start_consultation'),
    path('pending-review/<int:pk>/queue/',   views.pending_review_queue,   name='pending_review_queue'),
    path('pending-review/<int:pk>/move/',    views.pending_review_move,    name='pending_review_move'),
    path('pending-review/<int:pk>/decline/', views.pending_review_decline, name='pending_review_decline'),
    path('pending-review/<int:pk>/notes/',   views.pending_review_notes,   name='pending_review_notes'),
    path('<int:pk>/cancel/', views.appointment_cancel, name='appointment_cancel'),
    path('<int:pk>/delete/', views.appointment_delete, name='appointment_delete'),
    # ── Staff check-in management ─────────────────────────────────────────────
    path('checkin/qr/',              checkin_views.checkin_qr_page,     name='checkin_qr_page'),
    path('checkin/pending/',         checkin_views.checkin_pending_json, name='checkin_pending_json'),
    path('checkin/<int:pk>/accept/', checkin_views.checkin_accept,      name='checkin_accept'),
    path('checkin/<int:pk>/decline/',checkin_views.checkin_decline,     name='checkin_decline'),
    path('checkin/<int:pk>/edit/',   checkin_views.checkin_edit,        name='checkin_edit'),
    # ── Online (website) bookings ─────────────────────────────────────────────
    path('web-bookings/',                  views.web_booking_list,    name='web_booking_list'),
    path('web-bookings/<int:pk>/convert/', views.web_booking_convert, name='web_booking_convert'),
    path('web-bookings/<int:pk>/dismiss/', views.web_booking_dismiss, name='web_booking_dismiss'),
]
