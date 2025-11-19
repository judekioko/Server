# bursary/duplicate_detection.py
"""
Duplicate Application Detection System
Prevents users from submitting multiple applications
"""

from django.db.models import Q
from datetime import timedelta
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class DuplicateApplicationDetector:
    """
    Detect duplicate applications based on multiple criteria
    """
    
    @staticmethod
    def check_duplicates(data):
        """
        Check for duplicate applications
        Returns: {
            'is_duplicate': bool,
            'reason': str,
            'existing_applications': queryset
        }
        """
        from .models import BursaryApplication
        
        id_number = data.get('id_number')
        email = data.get('email')
        phone_number = data.get('phone_number')
        
        # Get current academic year cutoff (last 6 months)
        six_months_ago = timezone.now() - timedelta(days=180)
        
        # Hard block: any existing application with the same ID number
        exact_id_matches = BursaryApplication.objects.filter(id_number=id_number)
        if exact_id_matches.exists():
            first_match = exact_id_matches.first()
            logger.warning(f"Duplicate detected: ID {id_number} already has application")
            return {
                'is_duplicate': True,
                'reason': f'An application with ID number {id_number} already exists. Reference: {first_match.reference_number}',
                'existing_applications': exact_id_matches,
                'match_type': 'exact_id'
            }
        
        # Check for email + phone combination (strong indicator)
        email_phone_matches = BursaryApplication.objects.filter(
            Q(email=email) & Q(phone_number=phone_number),
            submitted_at__gte=six_months_ago
        ).exclude(status='rejected')
        
        if email_phone_matches.exists():
            logger.warning(f"Duplicate detected: Email {email} + Phone {phone_number}")
            return {
                'is_duplicate': True,
                'reason': f'An application with this email and phone number already exists. Reference: {email_phone_matches.first().reference_number}',
                'existing_applications': email_phone_matches,
                'match_type': 'email_phone'
            }
        
        # Check for suspicious similarity (same institution + admission number)
        institution_name = data.get('institution_name')
        admission_number = data.get('admission_number')
        
        if institution_name and admission_number:
            institution_matches = BursaryApplication.objects.filter(
                institution_name__iexact=institution_name,
                admission_number=admission_number,
                submitted_at__gte=six_months_ago
            ).exclude(status='rejected')
            
            if institution_matches.exists():
                logger.warning(f"Duplicate detected: Same institution + admission number")
                return {
                    'is_duplicate': True,
                    'reason': f'An application for {institution_name} with admission number {admission_number} already exists. Reference: {institution_matches.first().reference_number}',
                    'existing_applications': institution_matches,
                    'match_type': 'institution_admission'
                }
        
        # Fuzzy match: Same name + ward + institution (potential typo in ID)
        full_name = data.get('full_name')
        ward = data.get('ward')
        
        if full_name and ward and institution_name:
            fuzzy_matches = BursaryApplication.objects.filter(
                full_name__iexact=full_name,
                ward=ward,
                institution_name__iexact=institution_name,
                submitted_at__gte=six_months_ago
            ).exclude(status='rejected')
            
            if fuzzy_matches.exists():
                logger.info(f"Potential duplicate detected (fuzzy): {full_name} in {ward}")
                return {
                    'is_duplicate': False,  # Don't block, just warn
                    'is_suspicious': True,
                    'reason': f'A similar application was found. If this is not you, proceed. Reference: {fuzzy_matches.first().reference_number}',
                    'existing_applications': fuzzy_matches,
                    'match_type': 'fuzzy'
                }
        
        # No duplicates found
        return {
            'is_duplicate': False,
            'reason': None,
            'existing_applications': None
        }
    
    @staticmethod
    def allow_reapplication(existing_app):
        """
        Check if user should be allowed to reapply
        (e.g., if previous application was rejected > 3 months ago)
        """
        if existing_app.status == 'rejected':
            three_months_ago = timezone.now() - timedelta(days=90)
            if existing_app.submitted_at < three_months_ago:
                return True, "Previous application was rejected over 3 months ago"
        
        return False, "Active application exists"


class DuplicatePreventionMixin:
    """
    Mixin for views to check duplicates before saving
    """
    
    def perform_create(self, serializer):
        """Override to check for duplicates"""
        from rest_framework.exceptions import ValidationError
        
        data = serializer.validated_data
        
        # Run duplicate check
        duplicate_check = DuplicateApplicationDetector.check_duplicates(data)
        
        if duplicate_check['is_duplicate']:
            logger.warning(f"Blocked duplicate application: {duplicate_check['reason']}")
            raise ValidationError({
                'duplicate_error': duplicate_check['reason'],
                'existing_reference': duplicate_check['existing_applications'].first().reference_number if duplicate_check['existing_applications'] else None
            })
        
        # If suspicious but not duplicate, add warning to response
        if duplicate_check.get('is_suspicious'):
            logger.info(f"Suspicious application allowed: {duplicate_check['reason']}")
            # Could send notification to admin here
        
        # Proceed with creation
        return super().perform_create(serializer)


# =========================
# Duplicate Check API View
# =========================
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status


@api_view(['POST'])
@permission_classes([AllowAny])
def check_duplicate_application(request):
    """
    API endpoint to check for duplicates before submission
    Frontend can call this to warn user
    """
    required_fields = ['id_number', 'email', 'phone_number']
    
    # Validate required fields
    for field in required_fields:
        if not request.data.get(field):
            return Response(
                {'error': f'{field} is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # Run duplicate check
    duplicate_check = DuplicateApplicationDetector.check_duplicates(request.data)
    
    if duplicate_check['is_duplicate']:
        return Response({
            'is_duplicate': True,
            'message': duplicate_check['reason'],
            'existing_reference': duplicate_check['existing_applications'].first().reference_number,
            'match_type': duplicate_check['match_type']
        }, status=status.HTTP_200_OK)
    
    if duplicate_check.get('is_suspicious'):
        return Response({
            'is_duplicate': False,
            'is_suspicious': True,
            'warning': duplicate_check['reason']
        }, status=status.HTTP_200_OK)
    
    return Response({
        'is_duplicate': False,
        'message': 'No duplicate found'
    }, status=status.HTTP_200_OK)


# =========================
# Admin Action to Find Duplicates
# =========================
from django.contrib import admin
from django.http import HttpResponse
import csv


def find_all_duplicates(modeladmin, request, queryset):
    """
    Admin action to export potential duplicates
    """
    from .models import BursaryApplication
    from collections import defaultdict
    
    # Group by ID number
    id_groups = defaultdict(list)
    email_groups = defaultdict(list)
    
    for app in BursaryApplication.objects.all():
        id_groups[app.id_number].append(app)
        email_groups[app.email].append(app)
    
    # Find duplicates
    duplicates = []
    
    for id_num, apps in id_groups.items():
        if len(apps) > 1:
            duplicates.extend(apps)
    
    for email, apps in email_groups.items():
        if len(apps) > 1 and apps not in duplicates:
            duplicates.extend(apps)
    
    # Export to CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="duplicate_applications.csv"'
    writer = csv.writer(response)
    
    writer.writerow([
        'Reference Number', 'Full Name', 'ID Number', 'Email', 
        'Phone', 'Institution', 'Status', 'Submitted At'
    ])
    
    for app in duplicates:
        writer.writerow([
            app.reference_number,
            app.full_name,
            app.id_number,
            app.email,
            app.phone_number,
            app.institution_name,
            app.status,
            app.submitted_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    modeladmin.message_user(request, f"Found {len(duplicates)} potential duplicate applications")
    return response

find_all_duplicates.short_description = "Export Duplicate Applications"