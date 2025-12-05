from rest_framework import serializers
from .models import BursaryApplication, ApplicationStatusLog, ApplicationDeadline
import re


class ApplicationStatusLogSerializer(serializers.ModelSerializer):
    changed_by_username = serializers.CharField(source='changed_by.username', read_only=True)

    class Meta:
        model = ApplicationStatusLog
        fields = ['id', 'old_status', 'new_status', 'changed_by_other', 'reason', 'changed_at']
        read_only_fields = ['id', 'changed_at']


class BursaryApplicationSerializer(serializers.ModelSerializer):
    status_logs = ApplicationStatusLogSerializer(many=True, read_only=True)
    email = serializers.EmailField(required=True)
    amount = serializers.IntegerField(min_value=1)
    data_consent = serializers.BooleanField(required=True)
    residency_confirm = serializers.BooleanField(required=True)

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
        if not value:
            return value
            
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
        if not value:
            return value
            
        if not re.fullmatch(r'\d{5,12}', value or ''):
            raise serializers.ValidationError("ID/Birth certificate number must be 5-12 digits.")
        return value

    def validate(self, attrs):
        """
        CORRECTED Cross-field validations for family status documents
        """
        print("=== SERIALIZER VALIDATION DEBUG ===")
        print(f"Family status: {attrs.get('family_status')}")
        
        # Validate consent fields
        if not attrs.get('data_consent', False):
            raise serializers.ValidationError(
                "You must consent to data processing to submit your application."
            )
        
        if not attrs.get('residency_confirm', False):
            raise serializers.ValidationError(
                "You must confirm your residency in Masinga Constituency."
            )
        
        # Validate disability proof if disability is checked
        if attrs.get('disability', False) and not attrs.get('disability_proof'):
            raise serializers.ValidationError(
                "Disability proof document is required when disability is indicated."
            )
        
        # Validate family status requirements - SIMPLIFIED AND CORRECTED
        family_status = attrs.get('family_status')
        
        if family_status == 'total-orphan':
            # For total orphan, check multiple possible document combinations
            single_parent_proof = attrs.get('single_parent_proof')
            father_dc = attrs.get('father_death_certificate')
            mother_dc = attrs.get('mother_death_certificate')
            deceased_single_parent_dc = attrs.get('deceased_single_parent_certificate')
            
            print(f"Total orphan documents:")
            print(f"  - single_parent_proof: {'Yes' if single_parent_proof else 'No'}")
            print(f"  - father_dc: {'Yes' if father_dc else 'No'}")
            print(f"  - mother_dc: {'Yes' if mother_dc else 'No'}")
            print(f"  - deceased_single_parent_dc: {'Yes' if deceased_single_parent_dc else 'No'}")
            
            # Check different valid combinations
            valid_combinations = [
                # From two-parent family: both parents' death certificates
                (father_dc and mother_dc),
                # From single-parent family: single parent proof + deceased parent certificate
                (single_parent_proof and deceased_single_parent_dc),
                # Alternative: single parent proof + one parent death certificate
                (single_parent_proof and (father_dc or mother_dc))
            ]
            
            if not any(valid_combinations):
                raise serializers.ValidationError(
                    "For total orphan status, please provide either: "
                    "1. Both parents' death certificates (if from two-parent family), OR "
                    "2. Single parent proof + death certificate of the deceased parent (if from single-parent family)."
                )
        
        elif family_status == 'single-parent':
            if not attrs.get('single_parent_proof'):
                raise serializers.ValidationError(
                    "Single parent proof document is required for single parent status."
                )
        
        elif family_status == 'partial-orphan':
            # For partial orphan, need single parent proof + at least one death certificate
            single_parent_proof = attrs.get('single_parent_proof')
            father_dc = attrs.get('father_death_certificate')
            mother_dc = attrs.get('mother_death_certificate')
            deceased_single_parent_dc = attrs.get('deceased_single_parent_certificate')
            
            if not single_parent_proof:
                raise serializers.ValidationError(
                    "Single parent proof document is required for partial orphan status."
                )
            
            # Check for at least one death certificate
            if not father_dc and not mother_dc and not deceased_single_parent_dc:
                raise serializers.ValidationError(
                    "At least one death certificate is required for partial orphan status."
                )
        
        # Validate chief letter is required
        if not attrs.get('chief_letter'):
            raise serializers.ValidationError(
                "Letter from Chief/Sub-Chief is mandatory. Please upload the signed and stamped letter."
            )
        
        # Validate admission letter or transcript based on year of study
        year_of_study = attrs.get('year_of_study')
        
        if year_of_study == 'first-year':
            if not attrs.get('admission_letter'):
                raise serializers.ValidationError(
                    "Admission letter is required for first-year students."
                )
        elif year_of_study:
            # Continuing students (second-year and above) need transcript
            if not attrs.get('transcript'):
                raise serializers.ValidationError(
                    "Latest academic transcript is required for continuing students."
                )
        
        print("=== VALIDATION PASSED ===")
        return attrs


class ApplicationDeadlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationDeadline
        fields = ['id', 'name', 'start_date', 'end_date', 'is_active', 'is_open', 'days_remaining']
        read_only_fields = ['is_open', 'days_remaining']