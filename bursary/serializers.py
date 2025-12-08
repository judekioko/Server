# bursary/serializers.py - PRODUCTION OPTIMIZED
"""
Ultra-fast serializers optimized for production
- Minimal validation for speed
- Background processing for complex tasks
- Immediate response (under 150ms)
"""

import re
from rest_framework import serializers
from .models import BursaryApplication, ApplicationStatusLog, ApplicationDeadline


class FastApplicationSerializer(serializers.ModelSerializer):
    """
    Ultra-fast serializer for application submission
    Returns response in under 150ms by doing only essential validations
    Complex validations run in background
    """
    
    # Critical fields with minimal validation
    email = serializers.EmailField(required=True)
    phone_number = serializers.CharField(required=True, max_length=15)
    id_number = serializers.CharField(required=True, max_length=50)
    amount = serializers.IntegerField(min_value=1, required=True)
    data_consent = serializers.BooleanField(required=True)
    residency_confirm = serializers.BooleanField(required=True)
    confirmation = serializers.BooleanField(required=True)
    
    class Meta:
        model = BursaryApplication
        fields = [
            # Personal Info
            'full_name', 'email', 'gender', 'phone_number', 'id_number',
            'guardian_phone', 'guardian_id',
            
            # Residence
            'ward', 'village', 'chief_name', 'chief_phone',
            'sub_chief_name', 'sub_chief_phone',
            
            # Institution
            'level_of_study', 'institution_type', 'institution_name',
            'admission_number', 'amount', 'mode_of_study', 'year_of_study',
            
            # Family
            'family_status', 'father_income', 'mother_income',
            
            # Disability
            'disability',
            
            # Consent (CRITICAL)
            'data_consent', 'communication_consent', 'residency_confirm', 'confirmation'
        ]
    
    def validate_phone_number(self, value):
        """Fast phone validation"""
        if not value:
            return value
            
        # Remove all non-digits
        digits = re.sub(r'\D', '', value)
        
        # Accept various Kenyan formats
        if len(digits) >= 9:
            if digits.startswith('254') and len(digits) == 12:
                return f"+{digits}"
            elif digits.startswith('0') and len(digits) == 10:
                return f"+254{digits[1:]}"
            elif digits.startswith('7') and len(digits) == 9:
                return f"+254{digits}"
            elif digits.startswith('1') and len(digits) == 9:
                return f"+254{digits}"
        
        # If we can't validate, accept as-is (will validate in background)
        return value
    
    def validate_id_number(self, value):
        """Fast ID validation"""
        if not value:
            return value
            
        # Allow 5-12 digits for now (background will validate properly)
        if re.fullmatch(r'\d{5,12}', value):
            return value
        # Accept anyway - background validation will catch issues
        return value
    
    def validate(self, attrs):
        """
        ONLY validate critical fields for immediate response
        Background thread handles complex validations
        """
        # CRITICAL: Must have consent and confirmation
        if not attrs.get('data_consent'):
            raise serializers.ValidationError({
                'data_consent': 'You must consent to data processing.'
            })
        
        if not attrs.get('residency_confirm'):
            raise serializers.ValidationError({
                'residency_confirm': 'You must confirm Masinga residency.'
            })
        
        if not attrs.get('confirmation'):
            raise serializers.ValidationError({
                'confirmation': 'You must confirm all details are correct.'
            })
        
        # Quick phone format check
        phone = attrs.get('phone_number', '')
        if phone and not re.search(r'\d', phone):
            raise serializers.ValidationError({
                'phone_number': 'Enter a valid phone number.'
            })
        
        return attrs


class FullApplicationSerializer(serializers.ModelSerializer):
    """Complete serializer for admin/read operations"""
    status_logs = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    edit_time_remaining = serializers.SerializerMethodField()
    
    class Meta:
        model = BursaryApplication
        fields = '__all__'
        read_only_fields = ['reference_number', 'submitted_at', 'status']
    
    def get_status_logs(self, obj):
        logs = obj.status_logs.all().order_by('-changed_at')[:10]
        return ApplicationStatusLogSerializer(logs, many=True).data
    
    def get_can_edit(self, obj):
        """Check if application can be edited"""
        from django.utils import timezone
        from datetime import timedelta
        
        # Applications can only be edited within 24 hours
        edit_window = timedelta(hours=24)
        time_since_submission = timezone.now() - obj.submitted_at
        
        return (
            obj.status in ['pending', 'under_review'] and
            time_since_submission <= edit_window
        )
    
    def get_edit_time_remaining(self, obj):
        """Get time remaining for editing"""
        from django.utils import timezone
        from datetime import timedelta
        
        edit_window = timedelta(hours=24)
        time_since_submission = timezone.now() - obj.submitted_at
        time_remaining = edit_window - time_since_submission
        
        if time_remaining.total_seconds() <= 0:
            return "Expired"
        
        hours = int(time_remaining.total_seconds() // 3600)
        minutes = int((time_remaining.total_seconds() % 3600) // 60)
        
        if hours > 0:
            return f"{hours} hour(s) {minutes} minute(s)"
        return f"{minutes} minute(s)"


class ApplicationStatusLogSerializer(serializers.ModelSerializer):
    changed_by_username = serializers.CharField(source='changed_by.username', read_only=True)
    
    class Meta:
        model = ApplicationStatusLog
        fields = ['id', 'old_status', 'new_status', 'changed_by', 
                 'changed_by_username', 'reason', 'changed_at']
        read_only_fields = ['id', 'changed_at']


class ApplicationDeadlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationDeadline
        fields = ['id', 'name', 'start_date', 'end_date', 
                 'is_active', 'is_open', 'days_remaining']
        read_only_fields = ['is_open', 'days_remaining']


# Alias for backward compatibility with existing code
BursaryApplicationSerializer = FastApplicationSerializer