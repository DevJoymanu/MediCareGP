from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from . import views
from consultations import portal_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # ── Public patient website (Medical-Flow) ─────────────────────────────────
    path('', views.website_home, name='website_home'),
    path('api/', include('appointments.api_urls')),
    path('video/', include('appointments.video_urls')),

    # ── CRM back-office ───────────────────────────────────────────────────────
    path('app/', views.dashboard, name='dashboard'),
    path('analytics/', views.analytics, name='analytics'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('patients/', include('patients.urls')),
    path('appointments/', include('appointments.urls')),
    path('consultations/', include('consultations.urls')),
    path('documents/', include('scripts.urls')),
    path('tasks/', include('tasks.urls')),
    path('billing/', include('billing.urls')),
    path('diagnosis/', include('diagnosis.urls')),
    path('medaid/', include('medaid.urls')),
    path('checkin/', include('appointments.checkin_urls')),
    path('results/', include('consultations.portal_urls')),

    # ── Standing lab / radiology results portals (shared-password) ────────────
    path('lab/',              portal_views.provider_portal,        {'kind': 'lab'},       name='lab_portal'),
    path('lab/logout/',       portal_views.provider_portal_logout, {'kind': 'lab'},       name='lab_portal_logout'),
    path('lab/<int:pk>/',     portal_views.provider_portal_submit, {'kind': 'lab'},       name='lab_portal_submit'),
    path('radiology/',          portal_views.provider_portal,        {'kind': 'radiology'}, name='radiology_portal'),
    path('radiology/logout/',   portal_views.provider_portal_logout, {'kind': 'radiology'}, name='radiology_portal_logout'),
    path('radiology/<int:pk>/', portal_views.provider_portal_submit, {'kind': 'radiology'}, name='radiology_portal_submit'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
