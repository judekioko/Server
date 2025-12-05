from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import (
    PasswordResetView, 
    PasswordResetDoneView, 
    PasswordResetConfirmView, 
    PasswordResetCompleteView
)
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from bursary.views import api_login, api_logout

def home(request):
    return JsonResponse({
        "message": "Masinga NG-CDF Bursary API",
        "status": "running",
        "endpoints": {
            "admin": f"/{settings.ADMIN_URL}",
            "api_docs": "/api/docs/",
            "bursary_api": "/api/bursary/"
        }
    })

def health_check(request):
    return JsonResponse({"status": "healthy"})

urlpatterns = [
    path("", home, name="home"),
    path("health/", health_check, name="health"),
    path(settings.ADMIN_URL, admin.site.urls),
    path("api/bursary/", include("bursary.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("api/auth/login/", api_login, name="api-login"),
    path("api/auth/logout/", api_logout, name="api-logout"),
    
    # Password Reset URLs
    path("password-reset/", PasswordResetView.as_view(), name="password_reset"),
    path("password-reset/done/", PasswordResetDoneView.as_view(), name="password_reset_done"),
    path("password-reset/<uidb64>/<token>/", PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("password-reset/complete/", PasswordResetCompleteView.as_view(), name="password_reset_complete"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)