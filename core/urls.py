# core/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.admin_dashboard import admin_dashboard_view
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),

    # Admin Dashboard
    path('admin/dashboard/', admin_dashboard_view, name='admin-dashboard'),
    path('admin/', admin.site.urls),

    # Bursary app URLs
    path('bursary/', include('bursary.urls')),

    # =========================
    # Admin Password Reset URLs
    # =========================
    path('admin/password_reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='registration/password_reset_form.html'
         ), 
         name='password_reset'),
    
    path('admin/password_reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='registration/password_reset_done.html'
         ), 
         name='password_reset_done'),
    
    path('admin/reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='registration/password_reset_confirm.html'
         ), 
         name='password_reset_confirm'),
    
    path('admin/reset/done/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='registration/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
