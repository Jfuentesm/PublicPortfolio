"""
Serializers for the assessments app.

This module provides serializers for the models in the assessments app,
particularly for the Topic model and aggregated materiality information.
"""

from rest_framework import serializers
from apps.assessments.models import Topic, IRO, ImpactAssessment, RiskOppAssessment


class TopicSerializer(serializers.ModelSerializer):
    """Serializer for the Topic model"""
    impact_score = serializers.SerializerMethodField()
    financial_score = serializers.SerializerMethodField()
    iro_count = serializers.SerializerMethodField()
    quadrant = serializers.SerializerMethodField()
    
    class Meta:
        model = Topic
        fields = [
            'topic_id', 'name', 'description', 'level', 
            'impact_score', 'financial_score', 'iro_count', 'quadrant'
        ]
    
    def get_impact_score(self, obj):
        return obj.get_impact_materiality_score()
    
    def get_financial_score(self, obj):
        return obj.get_financial_materiality_score()
    
    def get_iro_count(self, obj):
        return obj.get_iro_count()
    
    def get_quadrant(self, obj):
        return obj.get_materiality_quadrant()


class PriorityIROSerializer(serializers.ModelSerializer):
    """Serializer for priority IROs in the quick-edit table"""
    title = serializers.CharField(read_only=True)
    impact_score = serializers.FloatField(read_only=True)
    financial_score = serializers.FloatField(read_only=True)
    topic = serializers.CharField(read_only=True)
    
    class Meta:
        model = IRO
        fields = [
            'iro_id', 'title', 'type', 'topic', 
            'impact_score', 'financial_score', 'current_stage'
        ]


class RecentActivitySerializer(serializers.Serializer):
    """Serializer for recent activity data"""
    timestamp = serializers.DateTimeField()
    action = serializers.CharField()
    description = serializers.CharField()
    icon = serializers.CharField()
    icon_color = serializers.CharField()


class TopicMaterialityQuadrantSerializer(serializers.Serializer):
    """Serializer for topic-level materiality quadrant data"""
    financially_material = TopicSerializer(many=True)
    double_material = TopicSerializer(many=True)
    not_material = TopicSerializer(many=True)
    impact_material = TopicSerializer(many=True)
