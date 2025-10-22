 # serializers.py
from rest_framework import serializers
from .models import BursaryApplication

class BursaryApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = BursaryApplication
        fields = '__all__'
        read_only_fields = ['reference_number', 'submitted_at']