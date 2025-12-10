# bursary/urls.py - PRODUCTION URLS
"""
Production URL configuration
"""

from django.urls import path
from . import views

# Import feature views
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
    # ========================
    #  CORE APPLICATION
    # ========================
    path("apply/", 
         views.BursaryApplicationCreateView.as_view(), 
         name="bursary-apply"),
    
    path("fast-api/", 
         views.fast_submit_api, 
         name="fast-api-submit"),
    
    # ========================
    #  APPLICATION MANAGEMENT
    # ========================
    path("applications/", 
         views.BursaryApplicationListView.as_view(), 
         name="bursary-list"),
    
    path("applications/<str:ref>/", 
         views.BursaryApplicationDetailView.as_view(), 
         name="bursary-detail"),
    
    path("applications/<str:ref>/update-status/", 
         views.BursaryApplicationUpdateStatusView.as_view(), 
         name="bursary-update-status"),
    
    # ========================
    #  APPLICATION EDITING
    # ========================
    path("applications/<str:ref>/edit/", 
         BursaryApplicationUpdateView.as_view(), 
         name="bursary-edit"),
    
    path("check-edit-eligibility/", 
         check_edit_eligibility, 
         name="check-edit"),
    
    path("get-application-for-edit/", 
         get_application_for_edit, 
         name="get-for-edit"),
    
    # ========================
    #  ANALYTICS
    # ========================
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
    
    # ========================
    #  SYSTEM INFO
    # ========================
    path("deadline/", 
         views.deadline_status, 
         name="deadline-status"),
    
    path("health/", 
         views.health_check, 
         name="health-check"),
    
    path("check-id-exists/", 
         views.check_id_exists, 
         name="check-id-exists"),
    
    # ========================
    #  AUTHENTICATION
    # ========================
    path("auth/login/", 
         views.api_login, 
         name="api-login"),
    
    path("auth/logout/", 
         views.api_logout, 
         name="api-logout"),
    
    path("logout/", 
         views.logout_view, 
         name="admin_logout"),
]
