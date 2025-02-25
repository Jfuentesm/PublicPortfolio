# tenants/models.py

from django.db import models
from django_tenants.models import TenantMixin, DomainMixin

class TenantConfig(TenantMixin):
    tenant_id = models.AutoField(primary_key=True)
    tenant_name = models.CharField(max_length=100, unique=True)
    created_on = models.DateTimeField(auto_now_add=True)
    schema_name = models.CharField(max_length=63, unique=True)

    auto_create_schema = True
    auto_drop_schema = False

    class Meta:
        db_table = 'public.tenant_config'

    def __str__(self):
        return f"{self.tenant_name} (ID: {self.tenant_id})"

class TenantDomain(DomainMixin):
    tenant = models.ForeignKey(
        TenantConfig,
        related_name='domains',
        on_delete=models.CASCADE
    )

    class Meta:
        db_table = 'tenant_domain'

    def __str__(self):
        return f"Domain: {self.domain} -> Tenant: {self.tenant}"