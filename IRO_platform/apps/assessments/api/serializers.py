# apps/assessments/api/serializers.py
from rest_framework import serializers
from ..models import IRO

class IROSerializer(serializers.ModelSerializer):
    class Meta:
        model = IRO
        fields = "__all__"