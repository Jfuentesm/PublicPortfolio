from django.db import connection
from django_tenants.utils import schema_context

def get_iros_for_tenant(tenant=None):
    """
    Get IROs for a specific tenant or use the current schema if no tenant specified.
    Returns a list of IRO objects to ensure they're fully loaded before exiting schema context.
    """
    from apps.assessments.models import IRO  # Import here to avoid circular imports
    
    try:
        if tenant and hasattr(tenant, 'schema_name') and tenant.schema_name:
            # If a tenant is specified, use its schema
            from django_tenants.utils import schema_context
            try:
                with schema_context(tenant.schema_name):
                    try:
                        # Try to get all IROs for this tenant
                        iros = list(IRO.objects.filter(tenant=tenant))
                        return iros
                    except Exception as inner_e:
                        print(f"Error querying IROs in tenant schema {tenant.schema_name}: {str(inner_e)}")
                        return []
            except Exception as schema_e:
                print(f"Error switching to schema {tenant.schema_name}: {str(schema_e)}")
                return []
        else:
            # If no valid tenant, use the current schema but be careful about filtering
            try:
                from django.db import connection
                current_schema = connection.schema_name
                if current_schema and current_schema.startswith('tenant_'):
                    # We're in a tenant schema, get all IROs for this schema
                    try:
                        return list(IRO.objects.all())
                    except Exception as query_e:
                        print(f"Error querying IROs in current schema {current_schema}: {str(query_e)}")
                        return []
                else:
                    # We're in the public schema, we can't get IROs directly
                    return []
            except Exception as conn_e:
                print(f"Error determining current schema: {str(conn_e)}")
                return []
    except Exception as e:
        import traceback
        print(f"Error in get_iros_for_tenant: {str(e)}")
        print(traceback.format_exc())
        return []

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
        # If no tenant, use the current schema
        current_schema = connection.schema_name
        if current_schema.startswith('tenant_'):
            # We're in a tenant schema, try to get the IRO
            try:
                return IRO.objects.get(iro_id=iro_id)
            except IRO.DoesNotExist:
                return None
        else:
            # We're in the public schema, we can't get IROs directly
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