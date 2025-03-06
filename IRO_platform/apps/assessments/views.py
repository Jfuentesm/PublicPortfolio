# apps/assessments/views.py
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
import json
from django_tenants.utils import schema_context
import tenants.models

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
    API view to return IRO data for Handsontable.
    """
    try:
        # Get the tenant from context
        tenant = request.context.get('tenant')
        
        # Early validation for tenant
        if tenant:
            # Verify tenant exists and has a valid schema_name
            if not hasattr(tenant, 'schema_name') or not tenant.schema_name:
                # Return empty array with status 200 instead of error
                print("No valid schema_name found for tenant")
                return JsonResponse([], safe=False)
        
        # Get IROs from utility function
        from apps.assessments.utils import get_iros_for_tenant, get_all_tenant_iros
        
        iros = []
        iro_queryset = []
        
        # Get the IRO queryset based on tenant context
        try:
            if tenant:
                print(f"Getting IROs for tenant: {tenant.tenant_name}")
                iro_queryset = get_iros_for_tenant(tenant)
            else:
                print("Getting IROs for all tenants")
                iro_queryset = get_all_tenant_iros()
        except Exception as e:
            import traceback
            print(f"Error getting IRO queryset: {str(e)}")
            print(traceback.format_exc())
            # Return empty array with status 200 instead of error
            return JsonResponse([], safe=False)
            
        # Prepare data for each IRO
        for iro in iro_queryset:
            try:
                # Initialize values with safe defaults
                impact_score = 0.0
                financial_score = 0.0
                title = f"IRO #{getattr(iro, 'iro_id', 'unknown')}"  # Safe default
                
                # Ensure we have a valid tenant for this IRO
                tenant_to_use = None
                try:
                    # First try to use the current context tenant
                    if tenant and hasattr(tenant, 'schema_name') and tenant.schema_name:
                        tenant_to_use = tenant
                    # If not available, try to use the IRO's tenant
                    elif hasattr(iro, 'tenant') and iro.tenant and hasattr(iro.tenant, 'schema_name') and iro.tenant.schema_name:
                        tenant_to_use = iro.tenant
                except Exception as tenant_err:
                    print(f"Error determining tenant for IRO {getattr(iro, 'iro_id', 'unknown')}: {str(tenant_err)}")
                
                # Only proceed with valid tenant and schema_name
                if tenant_to_use and tenant_to_use.schema_name:
                    from django_tenants.utils import schema_context
                    
                    # Get impact and financial scores
                    try:
                        with schema_context(tenant_to_use.schema_name):
                            from apps.assessments.models import ImpactAssessment, RiskOppAssessment
                            
                            impact_assessment = ImpactAssessment.objects.filter(iro=iro).order_by('-created_on').first()
                            if impact_assessment and impact_assessment.impact_materiality_score:
                                try:
                                    impact_score = float(impact_assessment.impact_materiality_score)
                                except (ValueError, TypeError):
                                    impact_score = 0.0
                                
                            risk_opp_assessment = RiskOppAssessment.objects.filter(iro=iro).order_by('-created_on').first()
                            if risk_opp_assessment and risk_opp_assessment.financial_materiality_score:
                                try:
                                    financial_score = float(risk_opp_assessment.financial_materiality_score)
                                except (ValueError, TypeError):
                                    financial_score = 0.0
                    except Exception as score_err:
                        print(f"Error getting assessment scores for IRO {getattr(iro, 'iro_id', 'unknown')}: {str(score_err)}")
                    
                    # Get the title safely
                    try:
                        # Try using the property method first
                        if hasattr(iro, 'title'):
                            title = str(iro.title) if iro.title is not None else title
                        else:
                            # If no title property, fetch title manually
                            from apps.assessments.models import IROVersion
                            with schema_context(tenant_to_use.schema_name):
                                version = None
                                if hasattr(iro, 'current_version_id') and iro.current_version_id:
                                    version = IROVersion.objects.filter(version_id=iro.current_version_id).first()
                                if not version and hasattr(iro, 'iro_id'):
                                    version = IROVersion.objects.filter(iro=iro).order_by('-version_number').first()
                                if version and version.title:
                                    title = str(version.title)
                    except Exception as title_err:
                        print(f"Error getting title for IRO {getattr(iro, 'iro_id', 'unknown')}: {str(title_err)}")
                
                # Safely get last_assessment_date
                last_assessment_date = ''
                if hasattr(iro, 'last_assessment_date') and iro.last_assessment_date:
                    try:
                        last_assessment_date = iro.last_assessment_date.strftime('%Y-%m-%d')
                    except Exception as date_err:
                        print(f"Error formatting last_assessment_date for IRO {getattr(iro, 'iro_id', 'unknown')}: {str(date_err)}")
                
                # Get iro_id safely
                iro_id = getattr(iro, 'iro_id', 0)
                # Make sure iro_id is an integer or a string representation of an integer
                if not isinstance(iro_id, (int, str)) or (isinstance(iro_id, str) and not iro_id.isdigit()):
                    iro_id = 0  # Default to 0 if not valid
                    print(f"WARNING: Invalid iro_id type: {type(iro_id)}, value: {iro_id}. Defaulting to 0.")
                
                # Get other fields safely with explicit string conversion and validation
                # Ensure type is one of the expected values
                raw_type = getattr(iro, 'type', '')
                if raw_type in ['Risk', 'Opportunity', 'Impact']:
                    iro_type = str(raw_type)
                else:
                    # Default to 'Risk' if not one of the expected values
                    iro_type = 'Risk'
                    print(f"WARNING: Invalid type for IRO {iro_id}: {raw_type}. Defaulting to 'Risk'.")
                
                # Normalize esrs_standard
                esrs_standard = str(getattr(iro, 'esrs_standard', '') or '')
                
                # Ensure current_stage is one of the expected values
                raw_stage = getattr(iro, 'current_stage', '')
                valid_stages = ['Draft', 'In_Review', 'Approved', 'Disclosed']
                if raw_stage in valid_stages:
                    current_stage = str(raw_stage)
                else:
                    # Default to 'Draft' if not one of the expected values
                    current_stage = 'Draft'
                    print(f"WARNING: Invalid current_stage for IRO {iro_id}: {raw_stage}. Defaulting to 'Draft'.")
                
                # Build the IRO data dictionary with safe defaults for all fields
                iro_data = {
                    'iro_id': iro_id,
                    'type': iro_type,
                    'title': title,
                    'esrs_standard': esrs_standard,
                    'current_stage': current_stage,
                    'impact_score': impact_score,
                    'financial_score': financial_score,
                    'last_assessment_date': last_assessment_date,
                }
                
                # Debug log to help identify issues
                print(f"DEBUG: Prepared IRO data for IRO {iro_id}: type={iro_type}, stage={current_stage}")
                
                iros.append(iro_data)
            except Exception as e:
                # Log error but continue with other IROs
                import traceback
                print(f"Error processing IRO {getattr(iro, 'iro_id', 'unknown')}: {str(e)}")
                print(traceback.format_exc())
                
                # Add a placeholder entry so the table isn't completely empty
                iros.append({
                    'iro_id': getattr(iro, 'iro_id', 'unknown'),
                    'type': 'Risk',  # Default to a valid value
                    'title': f"Error loading IRO #{getattr(iro, 'iro_id', 'unknown')}",
                    'esrs_standard': '',
                    'current_stage': 'Draft',  # Default to a valid value
                    'impact_score': 0.0,
                    'financial_score': 0.0,
                    'last_assessment_date': '',
                })
        
        # Always return status 200 with the data we have
        return JsonResponse(iros, safe=False)
                
    except Exception as e:
        # Log the exception for debugging
        import traceback
        print(f"Error in iro_data view: {str(e)}")
        print(traceback.format_exc())
        
        # Return an empty array with status 200 instead of error
        return JsonResponse([], safe=False)