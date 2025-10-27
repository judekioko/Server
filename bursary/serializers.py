from rest_framework import serializers
from .models import BursaryApplication, ApplicationStatusLog, ApplicationDeadline


class ApplicationStatusLogSerializer(serializers.ModelSerializer):
    changed_by_username = serializers.CharField(source='changed_by.username', read_only=True)
    
    class Meta:
        model = ApplicationStatusLog
        fields = ['id', 'old_status', 'new_status', 'changed_by_username', 'reason', 'changed_at']
        read_only_fields = ['id', 'changed_at']


class BursaryApplicationSerializer(serializers.ModelSerializer):
    status_logs = ApplicationStatusLogSerializer(many=True, read_only=True)  # ✅ Fixed line

    class Meta:
        model = BursaryApplication
        fields = '__all__'
        read_only_fields = ['reference_number', 'submitted_at', 'status_logs']


class ApplicationDeadlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationDeadline
        fields = ['id', 'name', 'start_date', 'end_date', 'is_active', 'is_open', 'days_remaining']
        read_only_fields = ['is_open', 'days_remaining']
