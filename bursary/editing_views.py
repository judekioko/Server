# bursary/editing_views.py
"""
Application Editing System
Allows users to edit applications within deadline
"""

import logging
from datetime import timedelta

from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import PermissionDenied, NotFound
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .models import BursaryApplication, ApplicationDeadline, ApplicationStatusLog
from .serializers import BursaryApplicationSerializer

logger = logging.getLogger(__name__)


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
        # 1. Check if status allows editing
        if application.status == 'approved':
            reason = "Application has been approved and cannot be edited"
            return (False, reason) if reason_required else False
        
        if application.status == 'rejected':
            reason = "Rejected applications cannot be edited. Please submit a new application"
            return (False, reason) if reason_required else False
        
        # 2. Check if within edit window (24 hours after submission)
        edit_window = timedelta(hours=24)
        time_since_submission = timezone.now() - application.submitted_at
        
        if time_since_submission > edit_window:
            reason = "Edit window expired. Applications can only be edited within 24 hours of submission"
            return (False, reason) if reason_required else False
        
        # 3. Check if deadline is still open
        active_deadline = ApplicationDeadline.objects.filter(is_active=True).first()
        if active_deadline and not active_deadline.is_open:
            reason = "Application deadline has passed"
            return (False, reason) if reason_required else False
        
        # All checks passed
        reason = "Application can be edited"
        return (True, reason) if reason_required else True
    
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
    
    def verify_ownership(self, obj, email):
        """Verify that the email matches the application owner"""
        if not email:
            raise PermissionDenied("Email is required for editing")
        
        if obj.email.lower() != email.lower():
            raise PermissionDenied("You can only edit your own application")
    
    def get_object(self):
        """Override to verify ownership"""
        reference_number = self.kwargs.get(self.lookup_field)
        email = self.request.data.get('email')
        
        try:
            obj = self.queryset.get(reference_number=reference_number)
        except BursaryApplication.DoesNotExist:
            raise NotFound("Application not found")
        
        # Verify ownership by email
        self.verify_ownership(obj, email)
        
        return obj
    
    def check_editability(self, application):
        """Check if the application can be edited"""
        can_edit, reason = ApplicationEditabilityChecker.can_edit(
            application, reason_required=True
        )
        
        if not can_edit:
            raise PermissionDenied(reason)
    
    def track_changes(self, instance, old_values):
        """Track and log changes made to the application"""
        changes = []
        for field, old_value in old_values.items():
            new_value = getattr(instance, field)
            if str(old_value) != str(new_value):
                changes.append(f"{field}: {old_value} → {new_value}")
        
        return changes
    
    def update(self, request, *args, **kwargs):
        """Override to check editability and track changes"""
        try:
            instance = self.get_object()
            
            # Check if can edit
            self.check_editability(instance)
            
            # Store old values for audit
            old_values = {
                'institution_name': instance.institution_name,
                'amount': instance.amount,
                'ward': instance.ward,
                'phone_number': instance.phone_number,
                'email': instance.email,
            }
            
            # Perform update
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            
            # Refresh instance to get updated values
            instance.refresh_from_db()
            
            # Track and log changes
            changes = self.track_changes(instance, old_values)
            
            if changes:
                ApplicationStatusLog.objects.create(
                    application=instance,
                    old_status=instance.status,
                    new_status=instance.status,
                    changed_by=None,  # Self-edit
                    reason=f"Application edited by applicant. Changes: {', '.join(changes)}"
                )
            
            logger.info(f"Application {instance.reference_number} edited successfully")
            
            return Response({
                'success': True,
                'message': 'Application updated successfully',
                'reference_number': instance.reference_number,
                'changes_made': len(changes),
                'edit_time_remaining': ApplicationEditabilityChecker.get_edit_time_remaining(instance),
                'status': instance.status
            })
            
        except (PermissionDenied, NotFound) as e:
            logger.warning(f"Edit failed: {str(e)}")
            return Response(
                {'success': False, 'error': str(e)},
                status=status.HTTP_403_FORBIDDEN if isinstance(e, PermissionDenied) 
                else status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error updating application: {str(e)}", exc_info=True)
            return Response(
                {'success': False, 'error': 'Failed to update application. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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
            {'success': False, 'error': 'reference_number and email are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        application = BursaryApplication.objects.get(reference_number=reference_number)
        
        # Verify ownership
        if application.email.lower() != email.lower():
            return Response(
                {'success': False, 'error': 'Email does not match application record'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check editability
        can_edit, reason = ApplicationEditabilityChecker.can_edit(application, reason_required=True)
        
        response_data = {
            'success': True,
            'can_edit': can_edit,
            'reason': reason,
            'reference_number': application.reference_number,
            'status': application.status,
            'submitted_at': application.submitted_at.isoformat(),
        }
        
        if can_edit:
            response_data['edit_time_remaining'] = ApplicationEditabilityChecker.get_edit_time_remaining(application)
        
        return Response(response_data)
        
    except BursaryApplication.DoesNotExist:
        return Response(
            {'success': False, 'error': 'Application not found'},
            status=status.HTTP_404_NOT_FOUND
        )


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
            {'success': False, 'error': 'reference_number and email are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        application = BursaryApplication.objects.get(reference_number=reference_number)
        
        # Verify ownership
        if application.email.lower() != email.lower():
            return Response(
                {'success': False, 'error': 'Email does not match application record'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if can edit
        can_edit, reason = ApplicationEditabilityChecker.can_edit(application, reason_required=True)
        
        if not can_edit:
            return Response(
                {'success': False, 'error': reason},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Serialize and return
        serializer = BursaryApplicationSerializer(application)
        
        return Response({
            'success': True,
            'application': serializer.data,
            'edit_time_remaining': ApplicationEditabilityChecker.get_edit_time_remaining(application),
            'can_edit': True
        })
        
    except BursaryApplication.DoesNotExist:
        return Response(
            {'success': False, 'error': 'Application not found'},
            status=status.HTTP_404_NOT_FOUND
        )