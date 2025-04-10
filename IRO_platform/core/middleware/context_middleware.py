# core/middleware/context_middleware.py

from django.urls import resolve
from django.db import connection
from tenants.models import TenantConfig
from apps.assessments.models import Assessment, IRO
from django_tenants.utils import schema_context
import logging

logger = logging.getLogger('core')

class ContextMiddleware:
    """
    Middleware to manage hierarchical context: tenant, assessment, IRO.
    Ensures tenant context is set and logged consistently.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.context = {'tenant': None, 'assessment': None, 'iro': None}

        # Log initial context setup with tenant field
        logger.debug(
            "Initializing context for request: %s",
            request.path,
            extra={'tenant': 'NotSetYet'}
        )

        # Check session for tenant
        if 'tenant_id' in request.session:
            try:
                tenant_id = request.session['tenant_id']
                with schema_context('public'):
                    tenant = TenantConfig.objects.get(tenant_id=tenant_id)
                    if not tenant.schema_name:
                        logger.warning(
                            "Tenant %s has no schema_name",
                            tenant_id,
                            extra={'tenant': str(tenant_id)}
                        )
                        del request.session['tenant_id']
                    else:
                        request.context['tenant'] = tenant
                        logger.info(
                            "Tenant set from session: %s",
                            tenant.tenant_name,
                            extra={'tenant': tenant.tenant_name}
                        )
            except TenantConfig.DoesNotExist:
                logger.warning(
                    "Tenant ID %s not found, clearing session",
                    request.session.get('tenant_id'),
                    extra={'tenant': str(request.session.get('tenant_id', 'Unknown'))}
                )
                if 'tenant_id' in request.session:
                    del request.session['tenant_id']

        # Fallback to request.tenant from django-tenants
        elif hasattr(request, 'tenant'):
            request.context['tenant'] = request.tenant
            logger.info(
                "Tenant set from request.tenant: %s",
                request.tenant.tenant_name,
                extra={'tenant': request.tenant.tenant_name}
            )
        # Fallback to current schema
        elif connection.schema_name.startswith('tenant_'):
            tenant_name = connection.schema_name[7:]
            with schema_context('public'):
                try:
                    tenant = TenantConfig.objects.get(tenant_name=tenant_name)
                    request.context['tenant'] = tenant
                    logger.info(
                        "Tenant inferred from schema: %s",
                        tenant_name,
                        extra={'tenant': tenant_name}
                    )
                except TenantConfig.DoesNotExist:
                    logger.warning(
                        "No tenant found for schema: %s",
                        connection.schema_name,
                        extra={'tenant': 'Unknown'}
                    )

        # Default tenant for root domain
        if not request.context['tenant'] and request.get_host() in ('localhost', '127.0.0.1'):
            with schema_context('public'):
                tenant = TenantConfig.objects.first()
                if tenant:
                    request.context['tenant'] = tenant
                    request.session['tenant_id'] = tenant.tenant_id
                    logger.info(
                        "Set default tenant: %s",
                        tenant.tenant_name,
                        extra={'tenant': tenant.tenant_name}
                    )

        # Assessment context
        if 'assessment_id' in request.session and request.context['tenant']:
            try:
                tenant = request.context['tenant']
                with schema_context(tenant.schema_name):
                    assessment = Assessment.objects.get(id=request.session['assessment_id'])
                    request.context['assessment'] = assessment
                    logger.debug(
                        "Assessment set: %s",
                        assessment.name,
                        extra={'tenant': tenant.tenant_name}
                    )
            except Assessment.DoesNotExist:
                logger.warning(
                    "Assessment ID %s not found",
                    request.session.get('assessment_id'),
                    extra={'tenant': request.context['tenant'].tenant_name if request.context['tenant'] else 'Unknown'}
                )
                if 'assessment_id' in request.session:
                    del request.session['assessment_id']

        # IRO context
        if 'iro_id' in request.session and request.context['tenant']:
            try:
                from apps.assessments.utils import get_iro_by_id
                tenant = request.context['tenant']
                iro = get_iro_by_id(request.session['iro_id'], tenant)
                request.context['iro'] = iro
                logger.debug(
                    "IRO set: %s",
                    iro.title if iro else "None",
                    extra={'tenant': tenant.tenant_name}
                )
            except Exception as e:
                logger.warning(
                    "Error setting IRO: %s",
                    str(e),
                    extra={'tenant': request.context['tenant'].tenant_name if request.context['tenant'] else 'Unknown'}
                )
                if 'iro_id' in request.session:
                    del request.session['iro_id']

        # Handle GET parameters
        if 'tenant_id' in request.GET:
            try:
                tenant_id = int(request.GET['tenant_id'])
                with schema_context('public'):
                    tenant = TenantConfig.objects.get(tenant_id=tenant_id)
                    request.context['tenant'] = tenant
                    request.session['tenant_id'] = tenant_id
                    logger.info(
                        "Tenant updated via GET: %s",
                        tenant.tenant_name,
                        extra={'tenant': tenant.tenant_name}
                    )
            except (ValueError, TenantConfig.DoesNotExist):
                logger.warning(
                    "Invalid tenant_id in GET: %s",
                    request.GET['tenant_id'],
                    extra={'tenant': 'Unknown'}
                )

        # Process request
        response = self.get_response(request)
        
        # Get context values for logging
        tenant_name = request.context['tenant'].tenant_name if request.context['tenant'] else None
        assessment_name = request.context['assessment'].name if request.context['assessment'] else None
        iro_title = request.context['iro'].title if request.context['iro'] else None
        
        # Log with tenant field consistently included
        logger.debug(
            "Context after processing: tenant=%s, assessment=%s, iro=%s",
            tenant_name, assessment_name, iro_title,
            extra={'tenant': tenant_name or 'Unknown'}
        )
        
        return response