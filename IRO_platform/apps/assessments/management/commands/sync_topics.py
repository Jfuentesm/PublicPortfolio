"""
Management command to synchronize topics from existing IROs.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django_tenants.utils import schema_context

from tenants.models import TenantConfig
from apps.assessments.topic_aggregator import sync_topics_from_iro_versions


class Command(BaseCommand):
    """
    Command to synchronize topics from existing IROs.
    This is useful for initializing the system with existing data.
    """
    help = 'Synchronize topics from existing IROs'

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            '--tenant',
            help='Tenant schema name to synchronize topics for. If not provided, all tenants will be processed.'
        )

    def handle(self, *args, **options):
        """Handle the command."""
        tenant_schema = options.get('tenant')

        if tenant_schema:
            # Synchronize topics for a specific tenant
            try:
                tenant = TenantConfig.objects.get(schema_name=tenant_schema)
                self.sync_topics_for_tenant(tenant)
            except TenantConfig.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Tenant with schema name "{tenant_schema}" does not exist.')
                )
        else:
            # Synchronize topics for all tenants
            tenants = TenantConfig.objects.all()
            for tenant in tenants:
                self.sync_topics_for_tenant(tenant)

        self.stdout.write(
            self.style.SUCCESS('Topic synchronization completed successfully.')
        )

    def sync_topics_for_tenant(self, tenant):
        """Synchronize topics for a specific tenant."""
        self.stdout.write(f'Synchronizing topics for tenant: {tenant.tenant_name}')
        
        with transaction.atomic():
            with schema_context(tenant.schema_name):
                # Synchronize topics from IRO versions
                sync_topics_from_iro_versions(tenant)
                
        self.stdout.write(
            self.style.SUCCESS(f'Topics synchronized for tenant: {tenant.tenant_name}')
        )
