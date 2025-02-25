from django.core.management.base import BaseCommand
from tenants.models import TenantConfig, TenantDomain

class Command(BaseCommand):
    help = 'Initialize a new tenant (create if not exists); also ensures a matching domain.'

    def add_arguments(self, parser):
        parser.add_argument('--name', type=str, required=True, help='Name of the tenant (unique).')
        parser.add_argument('--domain', type=str, required=True, help='Domain name to map to this tenant (unique).')

    def handle(self, *args, **options):
        tenant_name = options['name']
        domain_name = options['domain']

        # 1) Check if a tenant with this name already exists
        existing_tenant = TenantConfig.objects.filter(tenant_name=tenant_name).first()
        if existing_tenant:
            self.stdout.write(
                self.style.WARNING(f'Tenant named "{tenant_name}" already exists. Checking associated domain...')
            )
            # 2) Ensure the corresponding domain is also set up
            domain_obj, created = TenantDomain.objects.get_or_create(
                domain=domain_name,
                tenant=existing_tenant,
                defaults={'is_primary': True}
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created domain "{domain_name}" for existing tenant "{tenant_name}".'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'Domain "{domain_name}" also already exists. No changes were made.'
                    )
                )
            return  # Done; no need to create a new tenant

        # 3) If tenant does not exist, create a new one
        tenant = TenantConfig(
            tenant_name=tenant_name,
            schema_name=f'tenant_{tenant_name}'
        )
        tenant.save()

        # 4) Create the domain for the newly created tenant
        domain = TenantDomain(
            domain=domain_name,
            tenant=tenant,
            is_primary=True
        )
        domain.save()

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created tenant "{tenant_name}" with domain "{domain_name}".'
            )
        )