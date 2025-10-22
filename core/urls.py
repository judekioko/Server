# core/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.admin_dashboard import admin_dashboard_view
from . import views

urlpatterns = [
    path('', views.home, name='home'),
     path('admin/dashboard/', admin_dashboard_view, name='admin-dashboard'),
    path('admin/', admin.site.urls),
    path('bursary/', include('bursary.urls')),
]

# For s# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)