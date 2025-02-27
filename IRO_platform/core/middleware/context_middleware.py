from django.urls import resolve
from django.db import connection
from tenants.models import TenantConfig
from apps.assessments.models import Assessment, IRO
from django_tenants.utils import schema_context

class ContextMiddleware:
    """
    Middleware to manage hierarchical context:
    - tenant (company)
    - assessment (first time vs refresh)
    - IRO (specific IRO being assessed)
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Initialize context attributes
        request.context = {
            'tenant': None,
            'assessment': None,
            'iro': None
        }

        # Check for tenant in session first (manually selected tenant)
        if 'tenant_id' in request.session:
            try:
                tenant_id = request.session['tenant_id']
                tenant = TenantConfig.objects.get(tenant_id=tenant_id)
                request.context['tenant'] = tenant
            except TenantConfig.DoesNotExist:
                # Clear invalid tenant from session
                if 'tenant_id' in request.session:
                    del request.session['tenant_id']
        # Fallback to request.tenant (set by django-tenants based on domain)
        elif hasattr(request, 'tenant'):
            request.context['tenant'] = request.tenant
        # Final fallback: try to determine tenant from the current schema
        elif connection.schema_name.startswith('tenant_'):
            # Extract tenant name from schema_name (tenant_tenant1 -> tenant1)
            tenant_name = connection.schema_name[7:]
            try:
                tenant = TenantConfig.objects.get(tenant_name=tenant_name)
                request.context['tenant'] = tenant
            except TenantConfig.DoesNotExist:
                pass

        # If we still don't have a tenant and we're visiting the root domain,
        # try to set a default tenant
        if not request.context['tenant'] and request.get_host() in ('localhost', '127.0.0.1'):
            try:
                # Try to use the first tenant as default for the root domain
                default_tenant = TenantConfig.objects.first()
                if default_tenant:
                    request.context['tenant'] = default_tenant
                    request.session['tenant_id'] = default_tenant.tenant_id
            except Exception:
                pass

        # Check session for stored context values
        if 'assessment_id' in request.session:
            try:
                assessment_id = request.session['assessment_id']
                request.context['assessment'] = Assessment.objects.get(id=assessment_id)
            except Assessment.DoesNotExist:
                # Clear invalid context
                if 'assessment_id' in request.session:
                    del request.session['assessment_id']

        if 'iro_id' in request.session:
            try:
                iro_id = request.session['iro_id']
                if request.context['tenant']:
                    from apps.assessments.utils import get_iro_by_id
                    iro = get_iro_by_id(iro_id, request.context['tenant'])
                    request.context['iro'] = iro
            except Exception:
                if 'iro_id' in request.session:
                    del request.session['iro_id']

        # ----------------------------------------------------------------
        # Removed "and is_staff" so that any user can switch tenants freely
        # ----------------------------------------------------------------
        if 'tenant_id' in request.GET: 
            try:
                tenant_id = int(request.GET.get('tenant_id'))
                tenant = TenantConfig.objects.get(tenant_id=tenant_id)
                request.context['tenant'] = tenant
                request.session['tenant_id'] = tenant_id
            except (ValueError, TenantConfig.DoesNotExist):
                pass

        if 'assessment_id' in request.GET:
            try:
                assessment_id = int(request.GET.get('assessment_id'))
                assessment = Assessment.objects.get(id=assessment_id)
                request.context['assessment'] = assessment
                request.session['assessment_id'] = assessment_id
                # Clear IRO when assessment changes
                if 'iro_id' in request.session:
                    del request.session['iro_id']
            except (ValueError, Assessment.DoesNotExist):
                pass

        if 'iro_id' in request.GET:
            try:
                iro_id = int(request.GET.get('iro_id'))
                if request.context['tenant']:
                    from apps.assessments.utils import get_iro_by_id
                    iro = get_iro_by_id(iro_id, request.context['tenant'])
                    if iro:
                        request.context['iro'] = iro
                        request.session['iro_id'] = iro_id
            except Exception:
                pass

        # Process the request
        response = self.get_response(request)
        return response