# core/views.py
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views.decorators.http import require_GET
from tenants.models import TenantConfig
from apps.assessments.models import Assessment, IRO

@require_GET
def set_context(request):
    """
    View to handle setting context values and redirecting.
    Can be called via AJAX or as a normal GET request.
    """
    redirect_url = request.GET.get('next', '/')
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    # Check for tenant selection (admin only)
    if 'tenant_id' in request.GET and request.user.is_staff:
        try:
            tenant_id = int(request.GET.get('tenant_id'))
            tenant = TenantConfig.objects.get(tenant_id=tenant_id)
            # In a real multi-tenant situation, you'd need to handle tenant switching
            # differently depending on your setup
            request.session['tenant_id'] = tenant_id
        except (ValueError, TenantConfig.DoesNotExist):
            pass
    
    # Check for assessment selection
    if 'assessment_id' in request.GET:
        try:
            assessment_id = int(request.GET.get('assessment_id'))
            assessment = Assessment.objects.get(id=assessment_id)
            request.session['assessment_id'] = assessment_id
            # Clear IRO when assessment changes
            if 'iro_id' in request.session:
                del request.session['iro_id']
        except (ValueError, Assessment.DoesNotExist):
            pass
    
    # Check for IRO selection
    if 'iro_id' in request.GET:
        try:
            iro_id = int(request.GET.get('iro_id'))
            iro = IRO.objects.get(iro_id=iro_id)
            request.session['iro_id'] = iro_id
        except (ValueError, IRO.DoesNotExist):
            pass
    
    if is_ajax:
        # For AJAX requests, return updated context as JSON
        context = {
            'tenant': None,
            'assessment': None,
            'iro': None
        }
        
        # Populate context based on session values
        if 'tenant_id' in request.session:
            try:
                tenant = TenantConfig.objects.get(tenant_id=request.session['tenant_id'])
                context['tenant'] = {
                    'tenant_id': tenant.tenant_id,
                    'tenant_name': tenant.tenant_name
                }
            except TenantConfig.DoesNotExist:
                pass
        
        if 'assessment_id' in request.session:
            try:
                assessment = Assessment.objects.get(id=request.session['assessment_id'])
                context['assessment'] = {
                    'id': assessment.id,
                    'name': assessment.name,
                    'description': assessment.description
                }
            except Assessment.DoesNotExist:
                pass
        
        if 'iro_id' in request.session:
            try:
                iro = IRO.objects.get(iro_id=request.session['iro_id'])
                context['iro'] = {
                    'iro_id': iro.iro_id,
                    'title': iro.title if hasattr(iro, 'title') else f"IRO #{iro.iro_id}",
                    'type': iro.type
                }
            except IRO.DoesNotExist:
                pass
        
        return JsonResponse({
            'success': True,
            'context': context,
            'redirect_url': redirect_url if request.GET.get('reload', False) else None
        })
    else:
        # For non-AJAX requests, redirect to the specified next URL
        return redirect(redirect_url)