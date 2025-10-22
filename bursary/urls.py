# urls.py
from django.urls import path
from django.urls import path
from . import views
from .views import (
    BursaryApplicationCreateView,
    BursaryApplicationListView,
    BursaryApplicationDetailView,
)

urlpatterns = [
    path("apply/", BursaryApplicationCreateView.as_view(), name="bursary-apply"),
    path("applications/", BursaryApplicationListView.as_view(), name="bursary-list"),
    path("applications/<str:reference_number>/", BursaryApplicationDetailView.as_view(), name="bursary-detail"),
    path('logout/', views.logout_view, name='admin_logout'),
]


