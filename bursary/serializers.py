from rest_framework import serializers
from .models import BursaryApplication, ApplicationStatusLog, ApplicationDeadline
import re


class ApplicationStatusLogSerializer(serializers.ModelSerializer):
    changed_by_username = serializers.CharField(source='changed_by.username', read_only=True)

    class Meta:
        model = ApplicationStatusLog
        fields = ['id', 'old_status', 'new_status', 'changed_by_username', 'reason', 'changed_at']
        read_only_fields = ['id', 'changed_at']


class BursaryApplicationSerializer(serializers.ModelSerializer):
    status_logs = ApplicationStatusLogSerializer(many=True, read_only=True)
    email = serializers.EmailField(required=True)  # ✅ Ensure email is validated properly
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = BursaryApplication
        fields = '__all__'
        read_only_fields = ['reference_number', 'submitted_at', 'status_logs']

    def validate_phone_number(self, value: str) -> str:
        """
        Accept common Kenyan formats:
        - 07XXXXXXXX
        - 01XXXXXXXX
        - +2547XXXXXXXX
        - 2547XXXXXXXX
        Normalize to +2547XXXXXXXX where possible.
        """
        digits = re.sub(r'\D', '', value or '')
        if digits.startswith('254') and len(digits) == 12:
            normalized = f"+{digits}"
        elif digits.startswith('0') and len(digits) == 10:
            normalized = f"+254{digits[1:]}"
        elif digits.startswith('7') and len(digits) == 9:
            normalized = f"+254{digits}"
        elif digits.startswith('1') and len(digits) == 9:
            normalized = f"+254{digits}"
        else:
            raise serializers.ValidationError("Enter a valid Kenyan phone number.")
        return normalized

    def validate_guardian_phone(self, value: str) -> str:
        return self.validate_phone_number(value)

    def validate_chief_phone(self, value: str) -> str:
        return self.validate_phone_number(value)

    def validate_sub_chief_phone(self, value: str) -> str:
        return self.validate_phone_number(value)

    def validate_id_number(self, value: str) -> str:
        """
        Kenyan National ID typically 7-8 digits for adults,
        allow 5-12 digits to cover edge cases and birth cert numbers.
        """
        if not re.fullmatch(r'\d{5,12}', value or ''):
            raise serializers.ValidationError("ID/Birth certificate number must be 5-12 digits.")
        return value

    def validate(self, attrs):
        """
        Cross-field validations:
        - If family_status is 'total-orphan', require both death certificates
        """
        family_status = attrs.get('family_status') or getattr(self.instance, 'family_status', None)
        father_dc = attrs.get('father_death_certificate') or getattr(self.instance, 'father_death_certificate', None)
        mother_dc = attrs.get('mother_death_certificate') or getattr(self.instance, 'mother_death_certificate', None)

        if family_status == 'total-orphan':
            if not father_dc or not mother_dc:
                raise serializers.ValidationError("Both father's and mother's death certificates are required for total orphan status.")

        return attrs


class ApplicationDeadlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationDeadline
        fields = ['id', 'name', 'start_date', 'end_date', 'is_active', 'is_open', 'days_remaining']
        read_only_fields = ['is_open', 'days_remaining']
