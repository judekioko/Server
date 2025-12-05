# bursary/editing_views.py
"""
Application Editing System
Allows users to edit applications within deadline
"""

from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.utils import timezone
from datetime import timedelta
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import BursaryApplication, ApplicationDeadline, ApplicationStatusLog
from .serializers import BursaryApplicationSerializer
import logging

logger = logging.getLogger(__name__)


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners to edit their applications
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only to owner (by reference number + email)
        email = request.data.get('email') or request.query_params.get('email')
        return obj.email == email


class ApplicationEditabilityChecker:
    """
    Check if an application can be edited
    """
    
    @staticmethod
    def can_edit(application, reason_required=False):
        """
        Check if application can be edited
        
        Returns: (bool, str) - (can_edit, reason)
        """
        reasons = []
        
        # 1. Check if status allows editing
        if application.status == 'approved':
            reasons.append("Application has been approved and cannot be edited")
            return False, reasons[0] if reason_required else False
        
        if application.status == 'rejected':
            reasons.append("Rejected applications cannot be edited. Please submit a new application")
            return False, reasons[0] if reason_required else False
        
        # 2. Check if within edit window (24 hours after submission)
        edit_window = timedelta(hours=24)
        time_since_submission = timezone.now() - application.submitted_at
        
        if time_since_submission > edit_window:
            hours_remaining = 24 - (time_since_submission.total_seconds() / 3600)
            reasons.append(f"Edit window expired. Applications can only be edited within 24 hours of submission")
            return False, reasons[0] if reason_required else False
        
        # 3. Check if deadline is still open
        active_deadline = ApplicationDeadline.objects.filter(is_active=True).first()
        if active_deadline and not active_deadline.is_open:
            reasons.append("Application deadline has passed")
            return False, reasons[0] if reason_required else False
        
        # All checks passed
        return True, "Application can be edited" if reason_required else True
    
    @staticmethod
    def get_edit_time_remaining(application):
        """
        Get time remaining for editing in human-readable format
        """
        edit_window = timedelta(hours=24)
        time_since_submission = timezone.now() - application.submitted_at
        time_remaining = edit_window - time_since_submission
        
        if time_remaining.total_seconds() <= 0:
            return "Expired"
        
        hours = int(time_remaining.total_seconds() // 3600)
        minutes = int((time_remaining.total_seconds() % 3600) // 60)
        
        if hours > 0:
            return f"{hours} hour(s) {minutes} minute(s)"
        return f"{minutes} minute(s)"


# =========================
# Edit Application View
# =========================
@method_decorator(csrf_exempt, name='dispatch')
class BursaryApplicationUpdateView(generics.UpdateAPIView):
    """
    Update/Edit an application
    """
    queryset = BursaryApplication.objects.all()
    serializer_class = BursaryApplicationSerializer
    permission_classes = [AllowAny]
    authentication_classes = []
    lookup_field = "reference_number"
    
    def get_object(self):
        """Override to verify ownership"""
        obj = super().get_object()
        
        # Verify ownership by email
        email = self.request.data.get('email')
        if obj.email != email:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only edit your own application")
        
        return obj
    
    def update(self, request, *args, **kwargs):
        """Override to check editability"""
        try:
            instance = self.get_object()
            
            # Check if can edit
            can_edit, reason = ApplicationEditabilityChecker.can_edit(instance, reason_required=True)
            
            if not can_edit:
                return Response(
                    {'error': reason},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Store old values for audit
            old_values = {
                'institution_name': instance.institution_name,
                'amount': instance.amount,
                'ward': instance.ward,
            }
            
            # Perform update
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            
            # Create audit log
            changes = []
            for field, old_value in old_values.items():
                new_value = getattr(instance, field)
                if old_value != new_value:
                    changes.append(f"{field}: {old_value} → {new_value}")
            
            if changes:
                ApplicationStatusLog.objects.create(
                    application=instance,
                    old_status=instance.status,
                    new_status=instance.status,
                    changed_by=None,  # Self-edit
                    reason=f"Application edited by applicant. Changes: {', '.join(changes)}"
                )
            
            logger.info(f"Application {instance.reference_number} edited by applicant")
            
            return Response({
                'message': 'Application updated successfully',
                'reference_number': instance.reference_number,
                'changes_made': len(changes),
                'edit_time_remaining': ApplicationEditabilityChecker.get_edit_time_remaining(instance)
            })
            
        except Exception as e:
            logger.error(f"Error updating application: {str(e)}")
            return Response(
                {'error': 'Failed to update application'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# =========================
# Check Edit Eligibility
# =========================
@api_view(['POST'])
@permission_classes([AllowAny])
def check_edit_eligibility(request):
    """
    Check if an application can be edited
    Requires: reference_number and email
    """
    reference_number = request.data.get('reference_number')
    email = request.data.get('email')
    
    if not reference_number or not email:
        return Response(
            {'error': 'reference_number and email are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        application = BursaryApplication.objects.get(reference_number=reference_number)
        
        # Verify ownership
        if application.email != email:
            return Response(
                {'error': 'Email does not match application record'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check editability
        can_edit, reason = ApplicationEditabilityChecker.can_edit(application, reason_required=True)
        
        response_data = {
            'can_edit': can_edit,
            'reason': reason,
            'status': application.status,
            'submitted_at': application.submitted_at.isoformat(),
        }
        
        if can_edit:
            response_data['edit_time_remaining'] = ApplicationEditabilityChecker.get_edit_time_remaining(application)
        
        return Response(response_data)
        
    except BursaryApplication.DoesNotExist:
        return Response(
            {'error': 'Application not found'},
            status=status.HTTP_404_NOT_FOUND
        )


# =========================
# Retrieve Application for Editing
# =========================
@api_view(['POST'])
@permission_classes([AllowAny])
def get_application_for_edit(request):
    """
    Get full application details for editing
    Requires: reference_number and email
    """
    reference_number = request.data.get('reference_number')
    email = request.data.get('email')
    
    if not reference_number or not email:
        return Response(
            {'error': 'reference_number and email are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        application = BursaryApplication.objects.get(reference_number=reference_number)
        
        # Verify ownership
        if application.email != email:
            return Response(
                {'error': 'Email does not match application record'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if can edit
        can_edit, reason = ApplicationEditabilityChecker.can_edit(application, reason_required=True)
        
        if not can_edit:
            return Response(
                {'error': reason},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Serialize and return
        serializer = BursaryApplicationSerializer(application)
        
        return Response({
            'application': serializer.data,
            'edit_time_remaining': ApplicationEditabilityChecker.get_edit_time_remaining(application),
            'can_edit': True
        })
        
    except BursaryApplication.DoesNotExist:
        return Response(
            {'error': 'Application not found'},
            status=status.HTTP_404_NOT_FOUND
        )


# =========================
# URLs for editing
# =========================
"""
Add to bursary/urls.py:

from .editing_views import (
    BursaryApplicationUpdateView,
    check_edit_eligibility,
    get_application_for_edit
)

urlpatterns += [
    path('applications/<str:reference_number>/edit/', 
         BursaryApplicationUpdateView.as_view(), 
         name='bursary-edit'),
    path('check-edit-eligibility/', 
         check_edit_eligibility, 
         name='check-edit'),
    path('get-application-for-edit/', 
         get_application_for_edit, 
         name='get-for-edit'),
]
"""