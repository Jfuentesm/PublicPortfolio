from django.core.management.base import BaseCommand
from django.db import transaction, connection
from django.utils import timezone
from tenants.models import TenantConfig, TenantDomain
from apps.assessments.models import (
    Assessment, IRO, ImpactAssessment, RiskOppAssessment, 
    IROVersion, IRORelationship, Review, Signoff, AuditTrail
)
from django_tenants.utils import schema_context
import random

class Command(BaseCommand):
    """
    Creates two tenants (if they do not already exist),
    assessments for each tenant, and IROs with appropriate assessments based on type.
    - Demonstrates both positive and negative impact IROs
    - Creates IRO relationships
    - Populates review and signoff records
    - Demonstrates topic hierarchy using ESRS taxonomy (levels 1-3)
    - Shows variation in materiality scores across tenants/assessments
    """
    help = 'Prepopulate the database with sample data demonstrating all IRO types and relationships.'

    def handle(self, *args, **options):
        # 1) Ensure or create 2 tenants:
        #    - tenant1 with domain tenant1.localhost
        #    - tenant2 with domain tenant2.localhost
        tenant_data = [
            {
                "tenant_name": "tenant1",
                "schema_name": "tenant_tenant1",
                "domain": "tenant1.localhost"
            },
            {
                "tenant_name": "tenant2",
                "schema_name": "tenant_tenant2",
                "domain": "tenant2.localhost"
            }
        ]

        tenants = []
        for item in tenant_data:
            tenant = TenantConfig.objects.filter(tenant_name=item["tenant_name"]).first()
            if tenant:
                self.stdout.write(
                    self.style.WARNING(
                        f'Tenant "{item["tenant_name"]}" already exists. Using the existing tenant.'
                    )
                )
            else:
                tenant = TenantConfig(
                    tenant_name=item["tenant_name"],
                    schema_name=item["schema_name"]
                )
                tenant.save()
                # Create a corresponding domain
                TenantDomain.objects.create(
                    domain=item["domain"],
                    tenant=tenant,
                    is_primary=True
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created tenant "{item["tenant_name"]}" with domain "{item["domain"]}".'
                    )
                )
            tenants.append(tenant)
            
            # 2) For each tenant, create assessments
            assessments = self.create_assessments(tenant)
            
            # 3) For each tenant and each assessment, create unique IROs
            iros = []
            for assessment in assessments:
                created_iros = self.create_iros_for_assessment(tenant, assessment)
                iros.extend(created_iros)
            
            # 4) Create IRORelationships between some IROs
            self.create_iro_relationships(tenant, iros)
            
            # 5) Create Review and Signoff records for some IROs
            self.create_reviews_and_signoffs(tenant, iros)

    @transaction.atomic
    def create_assessments(self, tenant):
        # Log the current schema that Django is using
        current_schema = connection.schema_name
        self.stdout.write(self.style.NOTICE(f"Current schema before assessment creation: {current_schema}"))

        created_assessments = []
        # Important: Switch to the tenant's schema before querying or creating tenant models.
        with schema_context(tenant.schema_name):
            # Create assessments (first time and refresh)
            assessments = [
                {
                    "name": "First Time Assessment",
                    "description": "Initial assessment of IROs"
                },
                {
                    "name": "Annual Refresh",
                    "description": "Annual refresh of existing IROs"
                },
                {
                    "name": "Climate Risk Assessment",
                    "description": "Focused assessment on climate-related risks and impacts"
                }
            ]
            
            for assessment_data in assessments:
                # Check if assessment already exists
                assessment = Assessment.objects.filter(
                    name=assessment_data["name"], 
                    tenant=tenant
                ).first()
                
                if assessment:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Assessment "{assessment_data["name"]}" already exists for tenant {tenant.tenant_name}. Using the existing assessment.'
                        )
                    )
                else:
                    # Create a new assessment
                    assessment = Assessment.objects.create(
                        tenant=tenant,
                        name=assessment_data["name"],
                        description=assessment_data["description"]
                    )
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Created assessment "{assessment_data["name"]}" for tenant {tenant.tenant_name}.'
                        )
                    )
                created_assessments.append(assessment)
        
        return created_assessments

    @transaction.atomic
    def create_iros_for_assessment(self, tenant, assessment):
        # Log the current schema that Django is using
        current_schema = connection.schema_name
        self.stdout.write(self.style.NOTICE(f"Current schema before IRO creation for assessment {assessment.name}: {current_schema}"))

        created_iros = []

        # Important: Switch to the tenant's schema before querying or creating tenant models.
        with schema_context(tenant.schema_name):
            # Generate a title prefix for this tenant and assessment
            assessment_name_for_title = assessment.name.replace(" ", "_")
            title_prefix = f"{tenant.tenant_name}_{assessment_name_for_title}_"
            
            # Count IROs with titles starting with our prefix (via their current version)
            existing_count = IROVersion.objects.filter(
                title__startswith=title_prefix
            ).count()
            
            self.stdout.write(self.style.NOTICE(
                f"Found {existing_count} existing IROs with titles starting with '{title_prefix}'"
            ))
            
            if existing_count >= 10:
                self.stdout.write(
                    self.style.WARNING(
                        f'Already found {existing_count} IRO(s) for assessment "{assessment.name}" in tenant "{tenant.tenant_name}". Skipping creation.'
                    )
                )
                return created_iros

            # Sample sets of data for demonstration aligned with ESRS taxonomy
            iro_data = [
                # Risks
                {
                    "type": "Risk", 
                    "title": "Climate Transition Requirements",
                    "description": "Risk related to climate transition requirements and regulations",
                    "esrs_standard": "ESRS E1",
                    "sust_topic_level1": "Climate change",
                    "sust_topic_level2": "Climate change mitigation",
                    "materiality_score": 4.2
                },
                {
                    "type": "Risk", 
                    "title": "Water Scarcity Risk",
                    "description": "Risk from increasing water scarcity in key operational regions",
                    "esrs_standard": "ESRS E3",
                    "sust_topic_level1": "Water and marine resources",
                    "sust_topic_level2": "Water",
                    "sust_topic_level3": "Water consumption",
                    "materiality_score": 3.8
                },
                {
                    "type": "Risk", 
                    "title": "Supply Chain Disruption",
                    "description": "Risk of supply chain disruptions due to climate events",
                    "esrs_standard": "ESRS G1",
                    "sust_topic_level1": "Business conduct",
                    "sust_topic_level2": "Management of relationships with suppliers including payment practices",
                    "materiality_score": 2.6
                },
                
                # Opportunities
                {
                    "type": "Opportunity", 
                    "title": "Sustainable Product Development",
                    "description": "Opportunity for new sustainable product lines",
                    "esrs_standard": "ESRS E5",
                    "sust_topic_level1": "Circular economy",
                    "sust_topic_level2": "Resource outflows related to products and services",
                    "materiality_score": 4.5
                },
                {
                    "type": "Opportunity", 
                    "title": "Energy Efficiency",
                    "description": "Energy efficiency improvements across operations",
                    "esrs_standard": "ESRS E1",
                    "sust_topic_level1": "Climate change",
                    "sust_topic_level2": "Energy",
                    "materiality_score": 3.4
                },
                {
                    "type": "Opportunity", 
                    "title": "Inclusive Employment Practices",
                    "description": "Opportunity to improve diversity and inclusion in the workforce",
                    "esrs_standard": "ESRS S1",
                    "sust_topic_level1": "Own workforce",
                    "sust_topic_level2": "Equal treatment and opportunities for all",
                    "sust_topic_level3": "Diversity",
                    "materiality_score": 3.1
                },
                
                # Negative Impacts
                {
                    "type": "Impact", 
                    "title": "Negative: Carbon Emissions",
                    "description": "Negative impact from carbon emissions across operations",
                    "impact_subtype": "Negative",
                    "esrs_standard": "ESRS E1",
                    "sust_topic_level1": "Climate change",
                    "sust_topic_level2": "Climate change mitigation",
                    "materiality_score": 4.3
                },
                {
                    "type": "Impact", 
                    "title": "Negative: Water Pollution",
                    "description": "Negative impact from water pollution in manufacturing processes",
                    "impact_subtype": "Negative",
                    "esrs_standard": "ESRS E2",
                    "sust_topic_level1": "Pollution",
                    "sust_topic_level2": "Pollution of water",
                    "materiality_score": 3.6
                },
                
                # Positive Impacts
                {
                    "type": "Impact", 
                    "title": "Positive: Community Development",
                    "description": "Positive impact through community development programs",
                    "impact_subtype": "Positive",
                    "esrs_standard": "ESRS S3",
                    "sust_topic_level1": "Affected communities",
                    "sust_topic_level2": "Communities' economic, social, and cultural rights",
                    "materiality_score": 3.2
                },
                {
                    "type": "Impact", 
                    "title": "Positive: Workforce Diversity",
                    "description": "Positive impact from inclusive employment practices",
                    "impact_subtype": "Positive",
                    "esrs_standard": "ESRS S1",
                    "sust_topic_level1": "Own workforce",
                    "sust_topic_level2": "Equal treatment and opportunities for all",
                    "sust_topic_level3": "Diversity",
                    "materiality_score": 2.9
                }
            ]
            
            for idx, data in enumerate(iro_data):
                # Check schema again before each IRO creation to ensure it's consistent
                current_schema = connection.schema_name
                self.stdout.write(self.style.NOTICE(
                    f"Current schema before creating IRO #{idx+1} for assessment {assessment.name}: {current_schema}"
                ))
                
                # Create the IRO
                iro_obj = IRO.objects.create(
                    tenant=tenant,
                    type=data["type"],
                    current_stage=random.choice(['Draft', 'In_Review', 'Approved', 'Disclosed']),
                    source_of_iro='Scripted Demo',
                    esrs_standard=data.get("esrs_standard", ""),
                    assessment_count=1,
                    last_assessment_score=data["materiality_score"],  
                )
                
                # Format the title according to the pattern [tenant]_[assessment]_[iro id]
                formatted_title = f"{title_prefix}_{data['title']}_{iro_obj.iro_id}"
                
                # Create an IRO version for this IRO
                iro_version = IROVersion.objects.create(
                    iro=iro_obj,
                    tenant=tenant,
                    version_number=1,
                    title=formatted_title,
                    description=data["description"],
                    status='Approved',
                    created_by=1,  # Default user ID
                    sust_topic_level1=data.get("sust_topic_level1", ""),
                    sust_topic_level2=data.get("sust_topic_level2", ""),
                    sust_topic_level3=data.get("sust_topic_level3", ""),
                )
                
                # Update the IRO with its current version
                iro_obj.current_version_id = iro_version.version_id
                iro_obj.save()
                
                self.stdout.write(self.style.NOTICE(
                    f"Created IRO with ID: {iro_obj.iro_id}, title: {formatted_title}, type: {data['type']} in schema: {current_schema}"
                ))
                
                # Create the appropriate assessment based on IRO type
                if data["type"] == "Impact":
                    # Determine if this is a positive or negative impact
                    is_positive = data.get("impact_subtype", "") == "Positive"
                    
                    # Create ImpactAssessment only for Impact type
                    impact_assessment = ImpactAssessment.objects.create(
                        iro=iro_obj,
                        tenant=tenant,
                        time_horizon='Short-term' if idx % 3 == 0 else ('Medium-term' if idx % 3 == 1 else 'Long-term'),
                        actual_or_potential='Actual' if idx % 2 == 0 else 'Potential',
                        related_to_human_rights='Yes' if data.get("sust_topic_level1", "") in ["Own workforce", "Workers in the value chain", "Affected communities", "Consumers and end-users"] else 'No',
                        scale_score=random.randint(1, 5),
                        scope_score=random.randint(1, 5),
                        irremediability_score=random.randint(1, 5),
                        likelihood_score=random.randint(1, 5),
                        severity_score=data["materiality_score"] - 0.2,  # Slightly different for variation
                        impact_materiality_score=data["materiality_score"],
                        overall_rationale=f'{"Positive" if is_positive else "Negative"} impact rationale for {formatted_title}',
                    )
                    
                    self.stdout.write(self.style.NOTICE(
                        f"Created ImpactAssessment with ID: {impact_assessment.impact_assessment_id} for {'Positive' if is_positive else 'Negative'} Impact type IRO"
                    ))
                elif data["type"] in ["Risk", "Opportunity"]:
                    # Create RiskOppAssessment only for Risk or Opportunity types
                    risk_assessment = RiskOppAssessment.objects.create(
                        iro=iro_obj,
                        tenant=tenant,
                        time_horizon='Short-term' if idx % 3 == 0 else ('Medium-term' if idx % 3 == 1 else 'Long-term'),
                        workforce_risk=random.randint(1, 5),
                        operational_risk=random.randint(1, 5),
                        cost_of_capital_risk=random.randint(1, 5),
                        reputational_risk=random.randint(1, 5),
                        legal_compliance_risk=random.randint(1, 5),
                        likelihood_score=random.randint(1, 5),
                        financial_magnitude_score=data["materiality_score"] - 0.5,  # Slightly different for variation
                        financial_materiality_score=data["materiality_score"],
                        overall_rationale=f'Financial rationale for {formatted_title}',
                    )
                    
                    self.stdout.write(self.style.NOTICE(
                        f"Created RiskOppAssessment with ID: {risk_assessment.risk_opp_assessment_id} for {data['type']} type IRO"
                    ))
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created IRO #{iro_obj.iro_id} ({formatted_title}) of type {data["type"]} for assessment "{assessment.name}" and tenant: {tenant.tenant_name}'
                    )
                )
                
                created_iros.append(iro_obj)
                
                # Create an audit trail entry for the IRO creation
                AuditTrail.objects.create(
                    tenant=tenant,
                    entity_type='IRO',
                    entity_id=iro_obj.iro_id,
                    action='created',
                    user_id=1,  # Default user ID
                    data_diff={
                        'type': data["type"],
                        'title': formatted_title,
                        'description': data["description"],
                        'materiality_score': data["materiality_score"],
                    }
                )
        
        return created_iros

    @transaction.atomic
    def create_iro_relationships(self, tenant, iros):
        """Create relationships between IROs to track when an IRO is the result of splitting another."""
        if not iros or len(iros) < 3:  # Need at least 3 IROs to demonstrate splitting
            self.stdout.write(self.style.WARNING("Not enough IROs to create split relationships."))
            return
        
        with schema_context(tenant.schema_name):
            # Create sample relationships specifically for tracking IRO splitting
            relationship_types = ['split_from']
            
            # We'll select a few IROs to be "parent" IROs that have been split
            num_parent_iros = min(3, len(iros) // 3)  # Use up to 3 parent IROs
            
            for i in range(num_parent_iros):
                # Pick a parent IRO
                parent_idx = i
                parent_iro = iros[parent_idx]
                
                # Create 2 child IROs that resulted from splitting the parent
                child_indices = [(parent_idx + j + 1) % len(iros) for j in range(2)]
                child_iros = [iros[idx] for idx in child_indices]
                
                for child_iro in child_iros:
                    # Skip if same IRO
                    if parent_iro.iro_id == child_iro.iro_id:
                        continue
                    
                    # Check if this relationship already exists
                    existing_relationship = IRORelationship.objects.filter(
                        source_iro=parent_iro,
                        target_iro=child_iro
                    ).first()
                    
                    if existing_relationship:
                        self.stdout.write(self.style.WARNING(
                            f"Relationship already exists between IRO #{parent_iro.iro_id} and IRO #{child_iro.iro_id}. Skipping."
                        ))
                        continue
                    
                    relationship = IRORelationship.objects.create(
                        tenant=tenant,
                        source_iro=parent_iro,
                        target_iro=child_iro,
                        relationship_type='split_from',
                        created_by=1,  # Default user ID
                        notes=f"IRO #{child_iro.iro_id} was created as a result of splitting IRO #{parent_iro.iro_id}."
                    )
                    
                    self.stdout.write(self.style.SUCCESS(
                        f"Created split relationship: IRO #{child_iro.iro_id} was split from IRO #{parent_iro.iro_id}"
                    ))
                    
                    # Create audit trail entry for the relationship creation
                    AuditTrail.objects.create(
                        tenant=tenant,
                        entity_type='IRORelationship',
                        entity_id=relationship.relationship_id,
                        action='created',
                        user_id=1,  # Default user ID
                        data_diff={
                            'source_iro_id': parent_iro.iro_id,
                            'target_iro_id': child_iro.iro_id,
                            'relationship_type': 'split_from'
                        }
                    )

    @transaction.atomic
    def create_reviews_and_signoffs(self, tenant, iros):
        """Create review and signoff records for some IROs."""
        if not iros:
            self.stdout.write(self.style.WARNING("No IROs to create reviews and signoffs for."))
            return
        
        with schema_context(tenant.schema_name):
            # Create reviews for half of the IROs
            review_iros = iros[:len(iros)//2]
            
            for iro in review_iros:
                # Create a review for this IRO
                review = Review.objects.create(
                    tenant=tenant,
                    iro=iro,
                    reviewer_id=1,  # Default user ID
                    status='In_Review' if iro.current_stage == 'In_Review' else 'Draft',
                    notes=f"Please review this {iro.type} for completeness and accuracy."
                )
                
                self.stdout.write(self.style.SUCCESS(
                    f"Created review #{review.review_id} for IRO #{iro.iro_id} with status {review.status}"
                ))
                
                # Create audit trail entry for the review creation
                AuditTrail.objects.create(
                    tenant=tenant,
                    entity_type='Review',
                    entity_id=review.review_id,
                    action='created',
                    user_id=1,  # Default user ID
                    data_diff={
                        'iro_id': iro.iro_id,
                        'status': review.status,
                    }
                )
                
                # For IROs that are approved, create a signoff
                if iro.current_stage == 'Approved':
                    signoff = Signoff.objects.create(
                        tenant=tenant,
                        review=review,
                        signed_by=1,  # Default user ID
                        signature_ref=f"SIG-{tenant.tenant_name}-{iro.iro_id}",
                        comments=f"Approved this {iro.type} after thorough review."
                    )
                    
                    # Update the review status to match
                    review.status = 'Approved'
                    review.save()
                    
                    self.stdout.write(self.style.SUCCESS(
                        f"Created signoff #{signoff.signoff_id} for review #{review.review_id}"
                    ))
                    
                    # Create audit trail entry for the signoff
                    AuditTrail.objects.create(
                        tenant=tenant,
                        entity_type='Signoff',
                        entity_id=signoff.signoff_id,
                        action='created',
                        user_id=1,  # Default user ID
                        data_diff={
                            'review_id': review.review_id,
                            'iro_id': iro.iro_id,
                        }
                    )