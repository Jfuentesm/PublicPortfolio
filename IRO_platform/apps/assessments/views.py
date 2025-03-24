# apps/assessments/views.py
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
import json
from django_tenants.utils import schema_context
import tenants.models
import logging
from .models import Assessment, IRO

logger = logging.getLogger('apps')


# Define the class-based views needed for URLs
class AssessmentListView(ListView):
    model = Assessment
    template_name = 'assessments/assessment_list.html'
    context_object_name = 'assessments'
    
    def get_queryset(self):
        # Get tenant from context middleware
        tenant = self.request.context.get('tenant')
        if tenant:
            return Assessment.objects.filter(tenant=tenant)
        return Assessment.objects.all()

class AssessmentCreateView(CreateView):
    model = Assessment
    template_name = 'assessments/assessment_form.html'
    fields = ['name', 'description']
    success_url = reverse_lazy('assessments:list')
    
    def form_valid(self, form):
        # Set tenant from context
        form.instance.tenant = self.request.context.get('tenant')
        return super().form_valid(form)

class AssessmentUpdateView(UpdateView):
    model = Assessment
    template_name = 'assessments/assessment_form.html'
    fields = ['name', 'description']
    success_url = reverse_lazy('assessments:list')

class IROListView(ListView):
    model = IRO
    template_name = 'assessments/iro_list.html'
    context_object_name = 'iros'
    
    def get_queryset(self):
        # Get tenant from context middleware
        tenant = self.request.context.get('tenant')
        if tenant:
            return IRO.objects.filter(tenant=tenant)
        return IRO.objects.all()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add available tenants to context
        context['available_tenants'] = tenants.models.TenantConfig.objects.all()
        
        # Add available assessments for the selected tenant
        if self.request.context.get('tenant'):
            tenant = self.request.context.get('tenant')
            with schema_context(tenant.schema_name):
                context['available_assessments'] = list(Assessment.objects.filter(tenant=tenant))
        else:
            context['available_assessments'] = []
        
        # Add available IROs for the selected tenant
        if self.request.context.get('tenant'):
            tenant = self.request.context.get('tenant')
            with schema_context(tenant.schema_name):
                context['available_iros'] = list(IRO.objects.filter(tenant=tenant))
        else:
            context['available_iros'] = []
        
        return context

class IROCreateView(CreateView):
    model = IRO
    template_name = 'assessments/iro_form.html'
    fields = ['type', 'source_of_iro', 'esrs_standard']
    success_url = reverse_lazy('assessments:iro-list')
    
    def form_valid(self, form):
        # Set tenant from context
        form.instance.tenant = self.request.context.get('tenant')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add available tenants to context
        context['available_tenants'] = tenants.models.TenantConfig.objects.all()
        
        # Add available assessments for the selected tenant
        if self.request.context.get('tenant'):
            tenant = self.request.context.get('tenant')
            with schema_context(tenant.schema_name):
                context['available_assessments'] = list(Assessment.objects.filter(tenant=tenant))
        else:
            context['available_assessments'] = []
        
        # Add available IROs for the selected tenant
        if self.request.context.get('tenant'):
            tenant = self.request.context.get('tenant')
            with schema_context(tenant.schema_name):
                context['available_iros'] = list(IRO.objects.filter(tenant=tenant))
        else:
            context['available_iros'] = []
        
        return context

class IROUpdateView(UpdateView):
    model = IRO
    template_name = 'assessments/iro_form.html'
    fields = ['type', 'source_of_iro', 'esrs_standard', 'current_stage']
    success_url = reverse_lazy('assessments:iro-list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add latest version information
        iro = self.get_object()
        context['latest_version'] = iro.iroversion_set.order_by('-version_number').first()
        
        # Add available tenants to context
        context['available_tenants'] = tenants.models.TenantConfig.objects.all()
        
        # Add available assessments for the selected tenant
        if self.request.context.get('tenant'):
            tenant = self.request.context.get('tenant')
            with schema_context(tenant.schema_name):
                context['available_assessments'] = list(Assessment.objects.filter(tenant=tenant))
        else:
            context['available_assessments'] = []
        
        # Add available IROs for the selected tenant
        if self.request.context.get('tenant'):
            tenant = self.request.context.get('tenant')
            with schema_context(tenant.schema_name):
                context['available_iros'] = list(IRO.objects.filter(tenant=tenant))
        else:
            context['available_iros'] = []
        
        return context

# ContextMixin needed for API views
class ContextMixin:
    """
    Mixin to filter queryset based on tenant context.
    Used by API views to respect tenant boundaries.
    """
    def get_queryset(self):
        queryset = super().get_queryset()
        tenant = self.request.context.get('tenant')
        if tenant:
            return queryset.filter(tenant=tenant)
        return queryset

# Add these functions to the end of apps/assessments/views.py

@require_POST
def iro_save(request):
    """
    View to save IRO changes from Handsontable.
    Expects a JSON POST with 'changes' and 'contextData'.
    """
    try:
        data = json.loads(request.body)
        changes = data.get('changes', [])
        context_data = data.get('contextData', {})
        
        # Extract tenant and assessment from context
        tenant = None
        if 'tenant' in context_data and context_data['tenant']:
            tenant_id = context_data['tenant']
            from tenants.models import TenantConfig
            tenant = TenantConfig.objects.get(tenant_id=tenant_id)
        
        # Process changes
        updated_rows = 0
        for row_change in changes:
            row_data = row_change.get('data')
            iro_changes = row_change.get('changes', {})
            
            if 'iro_id' in row_data:
                iro_id = row_data['iro_id']
                
                # Get the IRO instance
                from apps.assessments.utils import get_iro_by_id
                iro = get_iro_by_id(iro_id, tenant)
                
                if iro:
                    # Update fields based on changes
                    for field, value in iro_changes.items():
                        if hasattr(iro, field):
                            setattr(iro, field, value)
                    
                    # Save the changes
                    iro.save()
                    updated_rows += 1
        
        return JsonResponse({
            'success': True,
            'message': f"Updated {updated_rows} IROs"
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

@require_POST
def assessment_save(request):
    """
    View to save Assessment changes from Handsontable.
    """
    try:
        data = json.loads(request.body)
        changes = data.get('changes', [])
        context_data = data.get('contextData', {})
        
        # Extract tenant from context
        tenant = None
        if 'tenant' in context_data and context_data['tenant']:
            tenant_id = context_data['tenant']
            from tenants.models import TenantConfig
            tenant = TenantConfig.objects.get(tenant_id=tenant_id)
        
        # Process changes
        updated_rows = 0
        for row_change in changes:
            row_data = row_change.get('data')
            assessment_changes = row_change.get('changes', {})
            
            if 'id' in row_data:
                assessment_id = row_data['id']
                
                try:
                    from apps.assessments.models import Assessment
                    assessment = Assessment.objects.get(id=assessment_id)
                    
                    # Update fields based on changes
                    for field, value in assessment_changes.items():
                        if hasattr(assessment, field):
                            setattr(assessment, field, value)
                    
                    # Save the changes
                    assessment.save()
                    updated_rows += 1
                except Assessment.DoesNotExist:
                    pass
        
        return JsonResponse({
            'success': True,
            'message': f"Updated {updated_rows} assessments"
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

def assessment_data(request):
    """
    API view to return assessment data for Handsontable.
    """
    assessments = []
    
    tenant = request.context.get('tenant')
    
    from apps.assessments.models import Assessment
    if tenant:
        from django_tenants.utils import schema_context
        with schema_context(tenant.schema_name):
            assessment_queryset = Assessment.objects.filter(tenant=tenant)
            
            for assessment in assessment_queryset:
                assessments.append({
                    'id': assessment.id,
                    'name': assessment.name,
                    'description': assessment.description,
                    'created_on': assessment.created_on.strftime('%Y-%m-%d %H:%M:%S'),
                    'updated_on': assessment.updated_on.strftime('%Y-%m-%d %H:%M:%S')
                })
    else:
        # Handle case where we need to aggregate assessments from all tenants
        from tenants.models import TenantConfig
        for t in TenantConfig.objects.all():
            with schema_context(t.schema_name):
                assessment_queryset = Assessment.objects.filter(tenant=t)
                
                for assessment in assessment_queryset:
                    assessments.append({
                        'id': assessment.id,
                        'name': assessment.name,
                        'description': assessment.description,
                        'created_on': assessment.created_on.strftime('%Y-%m-%d %H:%M:%S'),
                        'updated_on': assessment.updated_on.strftime('%Y-%m-%d %H:%M:%S')
                    })
        
    return JsonResponse(assessments, safe=False)

def iro_data(request):
    """
    API view to return IRO data for Handsontable with enhanced logging.
    """
    logger.info("Entering iro_data view for path: %s", request.path)
    try:
        tenant = request.context.get('tenant')
        logger.debug("Tenant from context: %s", tenant.tenant_name if tenant else "None")

        if tenant and not tenant.schema_name:
            logger.warning("Tenant has no schema_name: %s", tenant.tenant_name)
            return JsonResponse([], safe=False)

        from apps.assessments.utils import get_iros_for_tenant, get_all_tenant_iros
        iros = []

        try:
            if tenant:
                logger.info("Fetching IROs for tenant: %s", tenant.tenant_name)
                iro_queryset = get_iros_for_tenant(tenant)
            else:
                logger.info("Fetching IROs for all tenants")
                iro_queryset = get_all_tenant_iros()
            logger.debug("IRO queryset count: %d", len(iro_queryset))
        except Exception as e:
            logger.error("Error fetching IRO queryset: %s", str(e), exc_info=True)
            return JsonResponse([], safe=False)

        for iro in iro_queryset:
            try:
                tenant_to_use = tenant or iro.tenant
                if not tenant_to_use or not tenant_to_use.schema_name:
                    logger.warning("Invalid tenant for IRO %s", iro.iro_id)
                    continue

                with schema_context(tenant_to_use.schema_name):
                    from apps.assessments.models import ImpactAssessment, RiskOppAssessment
                    impact_assessment = ImpactAssessment.objects.filter(iro=iro).order_by('-created_on').first()
                    risk_opp_assessment = RiskOppAssessment.objects.filter(iro=iro).order_by('-created_on').first()

                    impact_score = float(impact_assessment.impact_materiality_score or 0) if impact_assessment else 0.0
                    financial_score = float(risk_opp_assessment.financial_materiality_score or 0) if risk_opp_assessment else 0.0
                    title = iro.title or f"IRO #{iro.iro_id}"

                iro_data = {
                    'iro_id': iro.iro_id,
                    'type': iro.type if iro.type in ['Risk', 'Opportunity', 'Impact'] else 'Risk',
                    'title': title,
                    'esrs_standard': str(iro.esrs_standard or ''),
                    'current_stage': iro.current_stage if iro.current_stage in ['Draft', 'In_Review', 'Approved', 'Disclosed'] else 'Draft',
                    'impact_score': impact_score,
                    'financial_score': financial_score,
                    'last_assessment_date': iro.last_assessment_date.strftime('%Y-%m-%d') if iro.last_assessment_date else '',
                }
                iros.append(iro_data)
                logger.debug("Prepared IRO data: %s", iro_data)
            except Exception as e:
                logger.error("Error processing IRO %s: %s", iro.iro_id, str(e), exc_info=True)
                iros.append({
                    'iro_id': iro.iro_id,
                    'type': 'Risk',
                    'title': f"Error loading IRO #{iro.iro_id}",
                    'esrs_standard': '',
                    'current_stage': 'Draft',
                    'impact_score': 0.0,
                    'financial_score': 0.0,
                    'last_assessment_date': '',
                })

        logger.info("Returning %d IROs", len(iros))
        return JsonResponse(iros, safe=False)

    except Exception as e:
        logger.error("Fatal error in iro_data: %s", str(e), exc_info=True)
        return JsonResponse([], safe=False)