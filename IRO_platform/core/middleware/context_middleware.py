from django.urls import resolve
from tenants.models import TenantConfig
from apps.assessments.models import Assessment, IRO

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

        # Get tenant from request
        # In a multi-tenant setup with django-tenants, the tenant is already 
        # accessible through the request.tenant property
        if hasattr(request, 'tenant'):
            request.context['tenant'] = request.tenant

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
                request.context['iro'] = IRO.objects.get(iro_id=iro_id)
            except IRO.DoesNotExist:
                # Clear invalid context
                if 'iro_id' in request.session:
                    del request.session['iro_id']

        # Check URL parameters for context overrides
        if 'assessment_id' in request.GET:
            try:
                assessment_id = int(request.GET.get('assessment_id'))
                assessment = Assessment.objects.get(id=assessment_id)
                request.context['assessment'] = assessment
                request.session['assessment_id'] = assessment_id
            except (ValueError, Assessment.DoesNotExist):
                pass

        if 'iro_id' in request.GET:
            try:
                iro_id = int(request.GET.get('iro_id'))
                iro = IRO.objects.get(iro_id=iro_id)
                request.context['iro'] = iro
                request.session['iro_id'] = iro_id
            except (ValueError, IRO.DoesNotExist):
                pass

        # Process the request
        response = self.get_response(request)
        return response