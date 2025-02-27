# core/views.py
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET
from tenants.models import TenantConfig
from apps.assessments.models import Assessment, IRO, ImpactAssessment, RiskOppAssessment, AuditTrail, Review
from django_tenants.utils import schema_context
import json

def home_dashboard(request):
    # Get tenant from context middleware
    tenant = request.context.get('tenant')
    
    # Import the utility function
    from apps.assessments.utils import get_iros_for_tenant, get_all_tenant_iros
    
    # Get IROs based on tenant context
    if tenant:
        iro_queryset = get_iros_for_tenant(tenant)
    else:
        # If no tenant selected, get IROs from all tenant schemas
        iro_queryset = get_all_tenant_iros()
    
    # Calculate metrics for dashboard
    total_iros = len(iro_queryset)
    
    # Define high materiality as IROs with score > 3.5
    high_materiality_count = sum(1 for iro in iro_queryset if iro.last_assessment_score and iro.last_assessment_score > 3.5)
    
    # Count pending reviews
    if tenant:
        with schema_context(tenant.schema_name):
            pending_reviews_count = Review.objects.filter(status='In_Review', tenant=tenant).count()
    else:
        # Aggregate across all tenants
        pending_reviews_count = 0
        for t in TenantConfig.objects.all():
            with schema_context(t.schema_name):
                pending_reviews_count += Review.objects.filter(status='In_Review').count()
    
    # Count completed assessments (approved)
    completed_assessments_count = sum(1 for iro in iro_queryset if iro.current_stage == 'Approved')
    
    # Get recent activity from audit trail
    if tenant:
        with schema_context(tenant.schema_name):
            recent_activities = list(AuditTrail.objects.filter(tenant=tenant).order_by('-timestamp')[:5])
    else:
        # Aggregate across all tenants
        recent_activities = []
        for t in TenantConfig.objects.all():
            with schema_context(t.schema_name):
                tenant_activities = list(AuditTrail.objects.filter(tenant=t).order_by('-timestamp')[:5])
                recent_activities.extend(tenant_activities)
        # Re-sort combined list
        recent_activities.sort(key=lambda x: x.timestamp, reverse=True)
        recent_activities = recent_activities[:5]
    
    # Process activities to add color and icon information
    activity_data = []
    for activity in recent_activities:
        activity_info = {
            'timestamp': activity.timestamp,
            'action': activity.action,
            'description': f"{activity.entity_type} #{activity.entity_id} {activity.action}",
        }
        
        # Set icon and color based on action type
        if activity.action == 'created':
            activity_info['icon'] = 'plus'
            activity_info['icon_color'] = 'info'
        elif activity.action == 'updated':
            activity_info['icon'] = 'edit'
            activity_info['icon_color'] = 'warning'
        elif activity.action == 'approved':
            activity_info['icon'] = 'check'
            activity_info['icon_color'] = 'success'
        elif activity.action == 'deleted':
            activity_info['icon'] = 'trash'
            activity_info['icon_color'] = 'danger'
        else:
            activity_info['icon'] = 'clipboard-list'
            activity_info['icon_color'] = 'primary'
            
        activity_data.append(activity_info)
    
    # Get high priority IROs (highest scores)
    high_priority_iros = []
    
    # Sort IROs by last_assessment_score (if available)
    sorted_iros = sorted(
        [iro for iro in iro_queryset if iro.last_assessment_score], 
        key=lambda x: x.last_assessment_score, 
        reverse=True
    )
    
    for iro in sorted_iros[:10]:
        # Get the latest impact and financial scores
        if tenant:
            with schema_context(tenant.schema_name):
                impact_assessments = list(ImpactAssessment.objects.filter(iro=iro).order_by('-created_on'))
                risk_opp_assessments = list(RiskOppAssessment.objects.filter(iro=iro).order_by('-created_on'))
        else:
            # Use the IRO's tenant schema
            tenant_obj = iro.tenant
            with schema_context(tenant_obj.schema_name):
                impact_assessments = list(ImpactAssessment.objects.filter(iro=iro).order_by('-created_on'))
                risk_opp_assessments = list(RiskOppAssessment.objects.filter(iro=iro).order_by('-created_on'))
        
        impact_score = impact_assessments[0].impact_materiality_score if impact_assessments else 0.0
        financial_score = risk_opp_assessments[0].financial_materiality_score if risk_opp_assessments else 0.0
        
        high_priority_iros.append({
            'iro_id': iro.iro_id,
            'title': iro.title,
            'type': iro.type,
            'impact_score': float(impact_score) if impact_score else 0.0,
            'financial_score': float(financial_score) if financial_score else 0.0,
            'current_stage': iro.current_stage,
        })
    
    # Prepare data for materiality matrix
    matrix_data = []
    for iro in iro_queryset:
        if tenant:
            with schema_context(tenant.schema_name):
                impact_assessment = ImpactAssessment.objects.filter(iro=iro).order_by('-created_on').first()
                risk_opp_assessment = RiskOppAssessment.objects.filter(iro=iro).order_by('-created_on').first()
        else:
            # Use the IRO's tenant schema
            tenant_obj = iro.tenant
            with schema_context(tenant_obj.schema_name):
                impact_assessment = ImpactAssessment.objects.filter(iro=iro).order_by('-created_on').first()
                risk_opp_assessment = RiskOppAssessment.objects.filter(iro=iro).order_by('-created_on').first()
        
        if impact_assessment and risk_opp_assessment:
            matrix_data.append({
                'id': iro.iro_id,
                'title': iro.title,
                'type': iro.type,
                'impact_score': float(impact_assessment.impact_materiality_score or 0),
                'financial_score': float(risk_opp_assessment.financial_materiality_score or 0),
            })
    
    context = {
        'total_iros': total_iros,
        'high_materiality_count': high_materiality_count,
        'pending_reviews_count': pending_reviews_count,
        'completed_assessments_count': completed_assessments_count,
        'recent_activities': activity_data,
        'high_priority_iros': high_priority_iros,
        'high_priority_iros_json': json.dumps(high_priority_iros),  # Add JSON serialized data for Handsontable
        'materiality_matrix_data': json.dumps(matrix_data),
    }
    
    # Always add available tenants to context for the tenant selector, not just for staff users
    context['available_tenants'] = TenantConfig.objects.all()
    
    return render(request, 'home.html', context)

@require_GET
def set_context(request):
    """
    View to handle setting context values and redirecting.
    Can be called via AJAX or as a normal GET request.
    """
    redirect_url = request.GET.get('next', '/')
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    # Safely check if user is authenticated and staff
    is_staff = hasattr(request, 'user') and request.user.is_authenticated and request.user.is_staff
    
    # Check for tenant selection (admin only)
    if 'tenant_id' in request.GET and is_staff:
        try:
            tenant_id = int(request.GET.get('tenant_id'))
            tenant = TenantConfig.objects.get(tenant_id=tenant_id)
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