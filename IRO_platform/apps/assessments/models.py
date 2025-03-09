# apps/assessments/models.py

from django.db import models
from tenants.models import TenantConfig


class Assessment(models.Model):
    """
    (Kept from your original code, in case you still need a top-level
     Assessment model. You can remove it if it's no longer used.)
    """
    tenant = models.ForeignKey(TenantConfig, on_delete=models.CASCADE, db_column="tenant_id", null=True, blank=True)
    name = models.CharField(max_length=200, help_text="Name of the assessment")
    description = models.TextField(blank=True, help_text="Optional description")
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        # This table also goes into each tenant schema if you want it that way. 
        db_table = 'assessment'


class IRO(models.Model):
    iro_id = models.AutoField(primary_key=True)
    tenant = models.ForeignKey(TenantConfig, on_delete=models.CASCADE, db_column="tenant_id")
    current_version_id = models.IntegerField(null=True, blank=True)
    current_stage = models.CharField(max_length=50, default='Draft')
    type = models.CharField(max_length=20)
    source_of_iro = models.CharField(max_length=255, null=True, blank=True)
    esrs_standard = models.CharField(max_length=100, null=True, blank=True)
    last_assessment_date = models.DateTimeField(null=True, blank=True)
    assessment_count = models.IntegerField(default=0)
    last_assessment_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'iro'
    
    @property
    def title(self):
        """Return the title from the current version of this IRO"""
        if self.current_version_id:
            try:
                version = IROVersion.objects.get(version_id=self.current_version_id)
                return version.title
            except IROVersion.DoesNotExist:
                pass
        
        # Fallback: try to get the latest version's title
        latest_version = IROVersion.objects.filter(iro=self).order_by('-version_number').first()
        if latest_version:
            return latest_version.title
        
        return f"IRO #{self.iro_id}"  # Fallback title
    
    @property
    def description(self):
        """Return the description from the current version of this IRO"""
        if self.current_version_id:
            try:
                version = IROVersion.objects.get(version_id=self.current_version_id)
                return version.description
            except IROVersion.DoesNotExist:
                pass
                
        # Fallback: try to get the latest version's description
        latest_version = IROVersion.objects.filter(iro=self).order_by('-version_number').first()
        if latest_version:
            return latest_version.description
            
        return ""  # Fallback description



class IROVersion(models.Model):
    version_id = models.AutoField(primary_key=True)
    iro = models.ForeignKey(IRO, on_delete=models.CASCADE, db_column="iro_id")
    tenant = models.ForeignKey(TenantConfig, on_delete=models.CASCADE, db_column="tenant_id")
    version_number = models.IntegerField()
    title = models.CharField(max_length=255)
    description = models.TextField()
    sust_topic_level1 = models.CharField(max_length=100, null=True, blank=True)
    sust_topic_level2 = models.CharField(max_length=100, null=True, blank=True)
    sust_topic_level3 = models.CharField(max_length=100, null=True, blank=True)
    value_chain_lv1 = models.JSONField(default=list)  # or ArrayField in Postgres
    value_chain_lv2 = models.JSONField(default=list)
    economic_activity = models.JSONField(default=list)
    status = models.CharField(max_length=50, default='Draft')
    created_by = models.IntegerField()
    created_on = models.DateTimeField(auto_now_add=True)
    parent_version_id = models.IntegerField(null=True, blank=True)
    split_type = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = 'iro_version'


class IRORelationship(models.Model):
    relationship_id = models.AutoField(primary_key=True)
    tenant = models.ForeignKey(TenantConfig, on_delete=models.CASCADE, db_column="tenant_id")
    source_iro = models.ForeignKey(IRO, on_delete=models.CASCADE, db_column="source_iro_id",
                                   related_name='source_relationships')
    target_iro = models.ForeignKey(IRO, on_delete=models.CASCADE, db_column="target_iro_id",
                                   related_name='target_relationships')
    relationship_type = models.CharField(max_length=50)
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.IntegerField()
    notes = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'iro_relationship'


class ImpactAssessment(models.Model):
    impact_assessment_id = models.AutoField(primary_key=True)
    iro = models.ForeignKey(IRO, on_delete=models.CASCADE, db_column="iro_id")
    tenant = models.ForeignKey(TenantConfig, on_delete=models.CASCADE, db_column="tenant_id")
    impact_materiality_def_version_id = models.IntegerField(null=True, blank=True)
    time_horizon = models.CharField(max_length=20)
    actual_or_potential = models.CharField(max_length=50, null=True, blank=True)
    related_to_human_rights = models.CharField(max_length=50, null=True, blank=True)
    scale_score = models.IntegerField(null=True, blank=True)
    scale_rationale = models.TextField(null=True, blank=True)
    scope_score = models.IntegerField(null=True, blank=True)
    scope_rationale = models.TextField(null=True, blank=True)
    irremediability_score = models.IntegerField(null=True, blank=True)
    irremediability_rationale = models.TextField(null=True, blank=True)
    likelihood_score = models.IntegerField(null=True, blank=True)
    likelihood_rationale = models.TextField(null=True, blank=True)
    severity_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    impact_materiality_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    overall_rationale = models.TextField(null=True, blank=True)
    related_documents = models.TextField(null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'impact_assessment'


class RiskOppAssessment(models.Model):
    risk_opp_assessment_id = models.AutoField(primary_key=True)
    iro = models.ForeignKey(IRO, on_delete=models.CASCADE, db_column="iro_id")
    tenant = models.ForeignKey(TenantConfig, on_delete=models.CASCADE, db_column="tenant_id")
    fin_materiality_def_version_id = models.IntegerField(null=True, blank=True)
    time_horizon = models.CharField(max_length=20)
    workforce_risk = models.IntegerField(null=True, blank=True)
    workforce_risk_rationale = models.TextField(null=True, blank=True)
    operational_risk = models.IntegerField(null=True, blank=True)
    operational_risk_rationale = models.TextField(null=True, blank=True)
    cost_of_capital_risk = models.IntegerField(null=True, blank=True)
    cost_of_capital_risk_rationale = models.TextField(null=True, blank=True)
    reputational_risk = models.IntegerField(null=True, blank=True)
    reputational_risk_rationale = models.TextField(null=True, blank=True)
    legal_compliance_risk = models.IntegerField(null=True, blank=True)
    legal_compliance_risk_rationale = models.TextField(null=True, blank=True)
    likelihood_score = models.IntegerField(null=True, blank=True)
    likelihood_rationale = models.TextField(null=True, blank=True)
    financial_magnitude_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    financial_materiality_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    overall_rationale = models.TextField(null=True, blank=True)
    related_documents = models.TextField(null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'risk_opp_assessment'


class Review(models.Model):
    review_id = models.AutoField(primary_key=True)
    iro = models.ForeignKey(IRO, on_delete=models.CASCADE, db_column="iro_id")
    tenant = models.ForeignKey(TenantConfig, on_delete=models.CASCADE, db_column="tenant_id")
    iro_version = models.ForeignKey(IROVersion, on_delete=models.SET_NULL, db_column="iro_version_id",
                                    null=True, blank=True)
    reviewer_id = models.IntegerField()
    status = models.CharField(max_length=50, default='Draft')
    notes = models.TextField(default='', blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'review'


class Signoff(models.Model):
    signoff_id = models.AutoField(primary_key=True)
    review = models.ForeignKey(Review, on_delete=models.CASCADE, db_column="review_id")
    tenant = models.ForeignKey(TenantConfig, on_delete=models.CASCADE, db_column="tenant_id")
    iro_version = models.ForeignKey(IROVersion, on_delete=models.SET_NULL, db_column="iro_version_id",
                                    null=True, blank=True)
    signed_by = models.IntegerField()
    signed_on = models.DateTimeField(auto_now_add=True)
    signature_ref = models.CharField(max_length=255, null=True, blank=True)
    comments = models.TextField(default='', blank=True)

    class Meta:
        db_table = 'signoff'


class AuditTrail(models.Model):
    audit_id = models.AutoField(primary_key=True)
    tenant = models.ForeignKey(TenantConfig, on_delete=models.CASCADE, db_column="tenant_id")
    entity_type = models.CharField(max_length=50)
    entity_id = models.IntegerField()
    action = models.CharField(max_length=50)
    user_id = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    data_diff = models.JSONField(default=dict)

    class Meta:
        db_table = 'audit_trail'


class ImpactMaterialityDef(models.Model):
    def_id = models.AutoField(primary_key=True)
    tenant = models.ForeignKey(TenantConfig, on_delete=models.CASCADE, db_column="tenant_id")
    version_num = models.IntegerField()
    dimension = models.CharField(max_length=50)
    score_value = models.IntegerField()
    definition_text = models.TextField()
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField(null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.IntegerField()

    class Meta:
        db_table = 'impact_materiality_def'


class FinMaterialityWeights(models.Model):
    weight_id = models.AutoField(primary_key=True)
    tenant = models.ForeignKey(TenantConfig, on_delete=models.CASCADE, db_column="tenant_id")
    version_num = models.IntegerField()
    dimension = models.CharField(max_length=50)
    weight = models.DecimalField(max_digits=5, decimal_places=2)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField(null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.IntegerField()

    class Meta:
        db_table = 'fin_materiality_weights'


class FinMaterialityMagnitudeDef(models.Model):
    def_id = models.AutoField(primary_key=True)
    tenant = models.ForeignKey(TenantConfig, on_delete=models.CASCADE, db_column="tenant_id")
    version_num = models.IntegerField()
    score_value = models.IntegerField()
    definition_text = models.TextField()
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField(null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.IntegerField()

    class Meta:
        db_table = 'fin_materiality_magnitude_def'


class Topic(models.Model):
    """
    Model representing a sustainability topic that groups related IROs.
    Topics can be at different levels (level1, level2, level3) forming a hierarchy.
    """
    topic_id = models.AutoField(primary_key=True)
    tenant = models.ForeignKey(TenantConfig, on_delete=models.CASCADE, db_column="tenant_id")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    parent_topic = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, 
                                    related_name='child_topics')
    level = models.IntegerField(default=1, help_text="Topic hierarchy level (1=highest, 3=lowest)")
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'topic'
        unique_together = ('tenant', 'name', 'level')

    def __str__(self):
        return self.name
    
    @property
    def iros(self):
        """
        Return all IROs associated with this topic at any level
        """
        from django.db.models import Q
        
        # Find all IRO versions that reference this topic
        if self.level == 1:
            return IRO.objects.filter(
                iroversion__sust_topic_level1=self.name
            ).distinct()
        elif self.level == 2:
            return IRO.objects.filter(
                iroversion__sust_topic_level2=self.name
            ).distinct()
        elif self.level == 3:
            return IRO.objects.filter(
                iroversion__sust_topic_level3=self.name
            ).distinct()
        return IRO.objects.none()
    
    def get_impact_materiality_score(self):
        """
        Calculate the average impact materiality score for all IROs in this topic
        """
        iros = self.iros
        if not iros.exists():
            return 0.0
            
        total_score = 0.0
        count = 0
        
        for iro in iros:
            impact_assessment = ImpactAssessment.objects.filter(iro=iro).order_by('-created_on').first()
            if impact_assessment and impact_assessment.impact_materiality_score:
                total_score += float(impact_assessment.impact_materiality_score)
                count += 1
                
        return total_score / count if count > 0 else 0.0
    
    def get_financial_materiality_score(self):
        """
        Calculate the average financial materiality score for all IROs in this topic
        """
        iros = self.iros
        if not iros.exists():
            return 0.0
            
        total_score = 0.0
        count = 0
        
        for iro in iros:
            risk_opp_assessment = RiskOppAssessment.objects.filter(iro=iro).order_by('-created_on').first()
            if risk_opp_assessment and risk_opp_assessment.financial_materiality_score:
                total_score += float(risk_opp_assessment.financial_materiality_score)
                count += 1
                
        return total_score / count if count > 0 else 0.0
    
    def get_materiality_quadrant(self):
        """
        Determine which materiality quadrant this topic belongs to based on
        average impact and financial materiality scores.
        
        Returns one of:
        - 'financially_material': Financially material but not impact material
        - 'double_material': Both financially and impact material
        - 'not_material': Neither financially nor impact material
        - 'impact_material': Impact material but not financially material
        """
        # Get materiality scores
        impact_score = self.get_impact_materiality_score()
        financial_score = self.get_financial_materiality_score()
        
        # Define materiality thresholds (can be adjusted as needed)
        threshold = 2.5  # Assuming scores are on a 0-5 scale
        
        # Determine quadrant
        if financial_score > threshold and impact_score <= threshold:
            return 'financially_material'
        elif financial_score > threshold and impact_score > threshold:
            return 'double_material'
        elif financial_score <= threshold and impact_score <= threshold:
            return 'not_material'
        else:  # financial_score <= threshold and impact_score > threshold
            return 'impact_material'
    
    def get_iro_count(self):
        """Return the number of IROs associated with this topic"""
        return self.iros.count()