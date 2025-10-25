# urls.py
from django.urls import path
from . import views
from .views import (
    BursaryApplicationCreateView,
    BursaryApplicationListView,
    BursaryApplicationDetailView,
    BursaryApplicationUpdateStatusView,
    application_status_history,
    deadline_status,
)

urlpatterns = [
    # Application submission and retrieval
    path("apply/", BursaryApplicationCreateView.as_view(), name="bursary-apply"),
    path("applications/", BursaryApplicationListView.as_view(), name="bursary-list"),
    path("applications/<str:reference_number>/", BursaryApplicationDetailView.as_view(), name="bursary-detail"),
    
    # Status management
    path("applications/<str:reference_number>/update-status/", BursaryApplicationUpdateStatusView.as_view(), name="bursary-update-status"),
    path("applications/<str:reference_number>/history/", application_status_history, name="bursary-status-history"),
    
    # Deadline information
    path("deadline/", deadline_status, name="deadline-status"),
    
    # Authentication
    path('logout/', views.logout_view, name='admin_logout'),
]
