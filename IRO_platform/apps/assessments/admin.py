# apps/assessments/admin.py

from django.contrib import admin
from .models import (
    Assessment, IRO, IROVersion, IRORelationship, ImpactAssessment, 
    RiskOppAssessment, Review, Signoff, AuditTrail, 
    ImpactMaterialityDef, FinMaterialityWeights, FinMaterialityMagnitudeDef
)

@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description', 'created_on', 'updated_on')
    search_fields = ('name', 'description')
    list_filter = ('created_on',)

@admin.register(IRO)
class IROAdmin(admin.ModelAdmin):
    list_display = ('iro_id', 'tenant', 'type', 'current_stage',
                    'last_assessment_date', 'assessment_count')
    search_fields = ('type', 'source_of_iro', 'esrs_standard')
    list_filter = ('current_stage', 'esrs_standard', 'updated_on')

@admin.register(IROVersion)
class IROVersionAdmin(admin.ModelAdmin):
    list_display = ('version_id', 'iro', 'tenant', 'version_number', 'title', 
                    'status', 'created_on')
    search_fields = ('title', 'description', 'sust_topic_level1', 'sust_topic_level2')
    list_filter = ('status', 'created_on')

@admin.register(IRORelationship)
class IRORelationshipAdmin(admin.ModelAdmin):
    list_display = ('relationship_id', 'tenant', 'source_iro', 'target_iro', 'relationship_type')
    search_fields = ('relationship_type', 'notes')
    list_filter = ('relationship_type', 'created_on')

@admin.register(ImpactAssessment)
class ImpactAssessmentAdmin(admin.ModelAdmin):
    list_display = ('impact_assessment_id', 'iro', 'tenant', 'time_horizon',
                    'actual_or_potential', 'impact_materiality_score')
    list_filter = ('time_horizon', 'actual_or_potential')
    search_fields = ('overall_rationale',)

@admin.register(RiskOppAssessment)
class RiskOppAssessmentAdmin(admin.ModelAdmin):
    list_display = ('risk_opp_assessment_id', 'iro', 'tenant', 'time_horizon', 
                    'financial_materiality_score')
    list_filter = ('time_horizon',)
    search_fields = ('overall_rationale',)

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('review_id', 'iro', 'tenant', 'reviewer_id', 'status', 'updated_on')
    list_filter = ('status', 'created_on', 'updated_on')
    search_fields = ('notes',)

@admin.register(Signoff)
class SignoffAdmin(admin.ModelAdmin):
    list_display = ('signoff_id', 'review', 'tenant', 'signed_by', 'signed_on')
    list_filter = ('signed_on',)
    search_fields = ('comments', 'signature_ref')

@admin.register(AuditTrail)
class AuditTrailAdmin(admin.ModelAdmin):
    list_display = ('audit_id', 'tenant', 'entity_type', 'entity_id', 'action', 'timestamp')
    list_filter = ('entity_type', 'action', 'timestamp')
    search_fields = ('data_diff',)

@admin.register(ImpactMaterialityDef)
class ImpactMaterialityDefAdmin(admin.ModelAdmin):
    list_display = ('def_id', 'tenant', 'version_num', 'dimension', 'score_value', 'valid_from', 'valid_to')
    list_filter = ('dimension', 'score_value', 'valid_from', 'valid_to')
    search_fields = ('definition_text',)

@admin.register(FinMaterialityWeights)
class FinMaterialityWeightsAdmin(admin.ModelAdmin):
    list_display = ('weight_id', 'tenant', 'version_num', 'dimension', 'weight', 'valid_from', 'valid_to')
    list_filter = ('dimension', 'version_num', 'valid_from', 'valid_to')
    search_fields = ('dimension',)

@admin.register(FinMaterialityMagnitudeDef)
class FinMaterialityMagnitudeDefAdmin(admin.ModelAdmin):
    list_display = ('def_id', 'tenant', 'version_num', 'score_value', 'valid_from', 'valid_to')
    list_filter = ('version_num', 'score_value', 'valid_from', 'valid_to')
    search_fields = ('definition_text',)