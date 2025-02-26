from django.db import connection
from django_tenants.utils import schema_context

def get_iros_for_tenant(tenant=None):
    """
    Get IROs for a specific tenant or use the current schema if no tenant specified.
    Returns a list of IRO objects to ensure they're fully loaded before exiting schema context.
    """
    from apps.assessments.models import IRO  # Import here to avoid circular imports
    
    if tenant:
        # If a tenant is specified, use its schema
        with schema_context(tenant.schema_name):
            return list(IRO.objects.filter(tenant=tenant))
    else:
        # If no tenant, use the current schema
        return list(IRO.objects.all())

def get_iro_by_id(iro_id, tenant=None):
    """
    Get a specific IRO by ID for a tenant.
    Returns the IRO object or None if not found.
    """
    from apps.assessments.models import IRO  # Import here to avoid circular imports
    
    if tenant:
        with schema_context(tenant.schema_name):
            try:
                return IRO.objects.get(iro_id=iro_id, tenant=tenant)
            except IRO.DoesNotExist:
                return None
    else:
        try:
            return IRO.objects.get(iro_id=iro_id)
        except IRO.DoesNotExist:
            return None

def get_all_tenant_iros():
    """
    Get IROs from all tenant schemas.
    This is useful for admin views or aggregate dashboards.
    """
    from tenants.models import TenantConfig
    from apps.assessments.models import IRO
    
    all_iros = []
    
    for tenant in TenantConfig.objects.all():
        with schema_context(tenant.schema_name):
            # Convert QuerySet to list to ensure objects are fully loaded
            tenant_iros = list(IRO.objects.filter(tenant=tenant))
            all_iros.extend(tenant_iros)
    
    return all_iros