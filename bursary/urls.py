# bursary/urls.py - WORKING VERSION
"""
Complete URL configuration - working version
"""

from django.urls import path
from . import views

# Import feature views
from .duplicate_detection import check_duplicate_application
from .editing_views import (
    BursaryApplicationUpdateView,
    check_edit_eligibility,
    get_application_for_edit
)
from .analytics import (
    analytics_overview,
    analytics_comprehensive,
    export_analytics_csv,
    export_applications_csv,
    export_applications_xlsx,
    analytics_dashboard_view
)

urlpatterns = [
    # ===========================
    # FAST ENDPOINT (Only the one we have)
    # ===========================
    path("fast-submit/", 
         views.fast_submit_application, 
         name="fast-submit"),
    
    # ===========================
    # Core Application Endpoints
    # ===========================
    path("apply/", 
         views.BursaryApplicationCreateView.as_view(), 
         name="bursary-apply"),
    
    path("applications/", 
         views.BursaryApplicationListView.as_view(), 
         name="bursary-list"),
    
    path("applications/<str:reference_number>/", 
         views.BursaryApplicationDetailView.as_view(), 
         name="bursary-detail"),
    
    # ===========================
    # Status Management
    # ===========================
    path("applications/<str:reference_number>/update-status/", 
         views.BursaryApplicationUpdateStatusView.as_view(), 
         name="bursary-update-status"),
    
    path("applications/<str:reference_number>/history/", 
         views.application_status_history, 
         name="bursary-status-history"),
    
    # ===========================
    # Application Editing
    # ===========================
    path("applications/<str:reference_number>/edit/", 
         BursaryApplicationUpdateView.as_view(), 
         name="bursary-edit"),
    
    path("check-edit-eligibility/", 
         check_edit_eligibility, 
         name="check-edit"),
    
    path("get-application-for-edit/", 
         get_application_for_edit, 
         name="get-for-edit"),
    
    # ===========================
    # Duplicate Detection
    # ===========================
    path("check-duplicate/", 
         check_duplicate_application, 
         name="check-duplicate"),
    
    # ===========================
    # Analytics
    # ===========================
    path("analytics/overview/", 
         analytics_overview, 
         name="analytics-overview"),
    
    path("analytics/comprehensive/", 
         analytics_comprehensive, 
         name="analytics-comprehensive"),
    
    path("analytics/export-csv/", 
         export_analytics_csv, 
         name="analytics-export"),

    path("applications/export-csv/", 
         export_applications_csv, 
         name="applications-export-csv"),

    path("applications/export-xlsx/", 
         export_applications_xlsx, 
         name="applications-export-xlsx"),
    
    path("analytics/dashboard/", 
         analytics_dashboard_view, 
         name="analytics-dashboard"),
    
    # ===========================
    # Deadline Information
    # ===========================
    path("deadline/", 
         views.deadline_status, 
         name="deadline-status"),
    
    # ===========================
    # Authentication
    # ===========================
    path('logout/', 
         views.logout_view, 
         name='admin_logout'),
]
