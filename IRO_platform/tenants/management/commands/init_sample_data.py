# tenants/management/commands/init_sample_data.py

from django.core.management.base import BaseCommand
from django.db import transaction, connection
from tenants.models import TenantConfig, TenantDomain
from apps.assessments.models import IRO, ImpactAssessment, RiskOppAssessment
from django_tenants.utils import schema_context

class Command(BaseCommand):
    """
    Creates two tenants (if they do not already exist),
    and for each tenant creates 5 IROs (fully assessed).
    """
    help = 'Prepopulate the database with 2 tenants, each having 5 IROs that are fully assessed.'

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
            
            # 2) For each tenant, create 5 IROs fully assessed
            self.create_fully_assessed_iros(tenant)

    @transaction.atomic
    def create_fully_assessed_iros(self, tenant):
        # Log the current schema that Django is using
        current_schema = connection.schema_name
        self.stdout.write(self.style.NOTICE(f"Current schema before IRO creation: {current_schema}"))

        # Important: Switch to the tenant's schema before querying or creating tenant models.
        with schema_context(tenant.schema_name):
            # If the tenant already has 5 or more IROs, skip creation to avoid duplicates.
            existing_count = IRO.objects.filter(tenant=tenant).count()
            self.stdout.write(self.style.NOTICE(
                f"Found {existing_count} existing IROs for tenant {tenant.tenant_name}"
            ))
            
            if existing_count >= 5:
                self.stdout.write(
                    self.style.WARNING(
                        f'Tenant "{tenant.tenant_name}" already has {existing_count} IRO(s). Skipping creation.'
                    )
                )
                return

            # Sample sets of data for demonstration.  
            iro_types = ["Risk", "Opportunity", "Impact", "Risk", "Opportunity"]
            
            for idx in range(5):
                # Check schema again before each IRO creation to ensure it's consistent
                current_schema = connection.schema_name
                self.stdout.write(self.style.NOTICE(
                    f"Current schema before creating IRO #{idx+1}: {current_schema}"
                ))
                
                iro_obj = IRO.objects.create(
                    tenant=tenant,
                    type=iro_types[idx],
                    current_stage='Approved',
                    source_of_iro='Scripted Demo',
                    esrs_standard='ESRS E1',
                    assessment_count=1,
                    last_assessment_score=3.5 + (idx * 0.3),  # Just an example
                )
                
                self.stdout.write(self.style.NOTICE(
                    f"Created IRO with ID: {iro_obj.iro_id} in schema: {current_schema}"
                ))
                
                # Create ImpactAssessment
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
                    overall_rationale=f'Impact rationale for IRO #{iro_obj.iro_id}',
                )
                
                self.stdout.write(self.style.NOTICE(
                    f"Created ImpactAssessment with ID: {impact_assessment.impact_assessment_id}"
                ))

                # Create RiskOppAssessment
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
                    overall_rationale=f'Financial rationale for IRO #{iro_obj.iro_id}',
                )
                
                self.stdout.write(self.style.NOTICE(
                    f"Created RiskOppAssessment with ID: {risk_assessment.risk_opp_assessment_id}"
                ))

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created IRO #{iro_obj.iro_id} and its assessments for tenant: {tenant.tenant_name}'
                    )
                )
        
        # After exiting the `with schema_context(...)` block, Django reverts
        # to the default (public) schema.
        current_schema = connection.schema_name
        self.stdout.write(self.style.NOTICE(
            f"Current schema after all IRO creation: {current_schema}"
        ))