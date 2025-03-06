from django.core.management.base import BaseCommand
from django.db import transaction, connection
from django.utils import timezone
from tenants.models import TenantConfig, TenantDomain
from apps.assessments.models import Assessment, IRO, ImpactAssessment, RiskOppAssessment, IROVersion
from django_tenants.utils import schema_context

class Command(BaseCommand):
    """
    Creates two tenants (if they do not already exist),
    assessments for each tenant, and IROs with appropriate assessments based on type.
    """
    help = 'Prepopulate the database with 2 tenants, assessments, and IROs that are fully assessed.'

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
            
            # 2) For each tenant, create assessments
            assessments = self.create_assessments(tenant)
            
            # 3) For each tenant and each assessment, create unique IROs
            for assessment in assessments:
                self.create_iros_for_assessment(tenant, assessment)

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
            
            if existing_count >= 5:
                self.stdout.write(
                    self.style.WARNING(
                        f'Already found {existing_count} IRO(s) for assessment "{assessment.name}" in tenant "{tenant.tenant_name}". Skipping creation.'
                    )
                )
                return

            # Sample sets of data for demonstration.  
            iro_data = [
                {"type": "Risk", "description": "Risk related to climate transition requirements"},
                {"type": "Opportunity", "description": "Opportunity for new sustainable products"},
                {"type": "Impact", "description": "Impact from carbon emissions"},
                {"type": "Risk", "description": "Risk from increasing water scarcity"},
                {"type": "Opportunity", "description": "Energy efficiency improvements"}
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
                    current_stage='Approved',
                    source_of_iro='Scripted Demo',
                    esrs_standard='ESRS E1',
                    assessment_count=1,
                    last_assessment_score=3.5 + (idx * 0.3),  # Just an example
                )
                
                # Format the title according to the pattern [tenant]_[assessment]_[iro id]
                formatted_title = f"{tenant.tenant_name}_{assessment_name_for_title}_{iro_obj.iro_id}"
                
                # Create an IRO version for this IRO
                iro_version = IROVersion.objects.create(
                    iro=iro_obj,
                    tenant=tenant,
                    version_number=1,
                    title=formatted_title,
                    description=data["description"],
                    status='Approved',
                    created_by=1,  # Default user ID
                )
                
                # Update the IRO with its current version
                iro_obj.current_version_id = iro_version.version_id
                iro_obj.save()
                
                self.stdout.write(self.style.NOTICE(
                    f"Created IRO with ID: {iro_obj.iro_id}, title: {formatted_title}, type: {data['type']} in schema: {current_schema}"
                ))
                
                # Create the appropriate assessment based on IRO type
                if data["type"] == "Impact":
                    # Create ImpactAssessment only for Impact type
                    impact_assessment = ImpactAssessment.objects.create(
                        iro=iro_obj,
                        tenant=tenant,
                        time_horizon='Short-term',
                        actual_or_potential='Actual',
                        scale_score=4,
                        scope_score=3,
                        irremediability_score=3,
                        likelihood_score=4,
                        severity_score=3.8,
                        impact_materiality_score=3.8,
                        overall_rationale=f'Impact rationale for {formatted_title}',
                    )
                    
                    self.stdout.write(self.style.NOTICE(
                        f"Created ImpactAssessment with ID: {impact_assessment.impact_assessment_id} for Impact type IRO"
                    ))
                elif data["type"] in ["Risk", "Opportunity"]:
                    # Create RiskOppAssessment only for Risk or Opportunity types
                    risk_assessment = RiskOppAssessment.objects.create(
                        iro=iro_obj,
                        tenant=tenant,
                        time_horizon='Short-term',
                        workforce_risk=3,
                        operational_risk=4,
                        reputational_risk=3,
                        likelihood_score=3,
                        financial_magnitude_score=2.5,
                        financial_materiality_score=2.9,
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