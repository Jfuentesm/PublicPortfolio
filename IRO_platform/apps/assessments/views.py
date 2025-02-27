# Add these imports at the top if not already present
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
import json

from .models import Assessment, IRO

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

class IROCreateView(CreateView):
    model = IRO
    template_name = 'assessments/iro_form.html'
    fields = ['type', 'source_of_iro', 'esrs_standard']
    success_url = reverse_lazy('assessments:iro-list')
    
    def form_valid(self, form):
        # Set tenant from context
        form.instance.tenant = self.request.context.get('tenant')
        return super().form_valid(form)

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
    API view to return IRO data for Handsontable.
    """
    iros = []
    
    try:
        # Get the tenant from context
        tenant = request.context.get('tenant')
        
        # Get IROs from utility function
        from apps.assessments.utils import get_iros_for_tenant, get_all_tenant_iros
        
        if tenant:
            iro_queryset = get_iros_for_tenant(tenant)
        else:
            iro_queryset = get_all_tenant_iros()
            
        # Prepare data for each IRO
        for iro in iro_queryset:
            try:
                # Get the impact and financial scores
                impact_score = 0.0
                financial_score = 0.0
                
                # Use the tenant from the IRO if we don't have one
                tenant_to_use = tenant or iro.tenant
                
                from django_tenants.utils import schema_context
                with schema_context(tenant_to_use.schema_name):
                    from apps.assessments.models import ImpactAssessment, RiskOppAssessment
                    
                    impact_assessment = ImpactAssessment.objects.filter(iro=iro).order_by('-created_on').first()
                    if impact_assessment and impact_assessment.impact_materiality_score:
                        impact_score = float(impact_assessment.impact_materiality_score)
                        
                    risk_opp_assessment = RiskOppAssessment.objects.filter(iro=iro).order_by('-created_on').first()
                    if risk_opp_assessment and risk_opp_assessment.financial_materiality_score:
                        financial_score = float(risk_opp_assessment.financial_materiality_score)
                
                iros.append({
                    'iro_id': iro.iro_id,
                    'type': iro.type,
                    'title': iro.title,
                    'esrs_standard': iro.esrs_standard or '',
                    'current_stage': iro.current_stage,
                    'impact_score': impact_score,
                    'financial_score': financial_score,
                    'last_assessment_date': iro.last_assessment_date.strftime('%Y-%m-%d') if iro.last_assessment_date else '',
                })
            except Exception as e:
                # Log error but continue with other IROs
                import traceback
                print(f"Error processing IRO {iro.iro_id}: {str(e)}")
                print(traceback.format_exc())
                
    except Exception as e:
        # Log the exception for debugging
        import traceback
        print(f"Error in iro_data view: {str(e)}")
        print(traceback.format_exc())
        
    return JsonResponse(iros, safe=False)