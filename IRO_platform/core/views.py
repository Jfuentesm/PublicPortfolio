# core/views.py
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET
from tenants.models import TenantConfig
from apps.assessments.models import Assessment, IRO, ImpactAssessment, RiskOppAssessment, AuditTrail, Review
from django_tenants.utils import schema_context
import json
import logging
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST


def home_dashboard(request):
    # Get tenant from context middleware
    tenant = request.context.get('tenant')
    
    # Import the utility function
    from apps.assessments.utils import get_iros_for_tenant, get_all_tenant_iros
    from apps.assessments.topic_aggregator import (
        get_topics_by_materiality_quadrant, 
        get_priority_iros,
        sync_topics_from_iro_versions
    )
    
    # Ensure all topics are synced from IRO versions
    sync_topics_from_iro_versions(tenant)
    
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
    high_priority_iros = get_priority_iros(tenant, limit=10)
    
    # Add debug logging to check what data is being returned
    logger = logging.getLogger(__name__)
    logger.debug("Priority IROs before JSON serialization: %s", high_priority_iros)
    
    # Ensure we have valid data before JSON serialization
    if high_priority_iros is None:
        high_priority_iros = []
    
    # Serialize the data to JSON, handling potential errors
    try:
        high_priority_iros_json = json.dumps(high_priority_iros)
        logger.debug("Priority IROs after JSON serialization: %s", high_priority_iros_json[:100] + '...' if len(high_priority_iros_json) > 100 else high_priority_iros_json)
    except Exception as e:
        logger.error("Error serializing priority IROs to JSON: %s", str(e))
        high_priority_iros_json = '[]'
    
    # Get topics by materiality quadrant
    topic_quadrants = get_topics_by_materiality_quadrant(tenant)
    
    context = {
        'total_iros': total_iros,
        'high_materiality_count': high_materiality_count,
        'pending_reviews_count': pending_reviews_count,
        'completed_assessments_count': completed_assessments_count,
        'recent_activities': activity_data,
        'high_priority_iros': high_priority_iros,
        'high_priority_iros_json': high_priority_iros_json,
        'topic_quadrants': topic_quadrants,
        'topic_quadrants_json': json.dumps(topic_quadrants),
    }
    
    # Always add available tenants to context for the tenant selector, not just for staff users
    context['available_tenants'] = TenantConfig.objects.all()
    
    # ADD THIS SECTION: Fetch available assessments for the selected tenant
    available_assessments = []
    if tenant:
        with schema_context(tenant.schema_name):
            available_assessments = list(Assessment.objects.filter(tenant=tenant))
    context['available_assessments'] = available_assessments
    
    # If we have a tenant but no IROs selected yet, prepare available IROs list
    available_iros = []
    if tenant:
        with schema_context(tenant.schema_name):
            available_iros = list(IRO.objects.filter(tenant=tenant))
    context['available_iros'] = available_iros
    
    return render(request, 'home.html', context)

@require_GET
def set_context(request):
    """
    View to handle setting context values and redirecting.
    Can be called via AJAX or as a normal GET request.
    """
    from django_tenants.utils import schema_context
    
    redirect_url = request.GET.get('next', '/')
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    # Safely check if user is authenticated and staff
    is_staff = hasattr(request, 'user') and request.user.is_authenticated and request.user.is_staff
    
    # Check for tenant selection (admin only)
    if 'tenant_id' in request.GET and is_staff:
        try:
            tenant_id = int(request.GET.get('tenant_id'))
            # Always query TenantConfig from public schema
            with schema_context('public'):
                tenant = TenantConfig.objects.get(tenant_id=tenant_id)
                request.session['tenant_id'] = tenant_id
        except (ValueError, TenantConfig.DoesNotExist):
            pass
    
    
    # Check for assessment selection
    if 'assessment_id' in request.GET:
        try:
            assessment_id = int(request.GET.get('assessment_id'))
            tenant = request.context.get('tenant')
            if tenant:
                with schema_context(tenant.schema_name):
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
            if request.context.get('tenant'):
                from apps.assessments.utils import get_iro_by_id
                iro = get_iro_by_id(iro_id, request.context.get('tenant'))
                if iro:
                    request.session['iro_id'] = iro_id
        except ValueError:
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
                # Always query TenantConfig from public schema
                with schema_context('public'):
                    tenant = TenantConfig.objects.get(tenant_id=request.session['tenant_id'])
                    context['tenant'] = {
                        'tenant_id': tenant.tenant_id,
                        'tenant_name': tenant.tenant_name
                    }
            except TenantConfig.DoesNotExist:
                pass
        
        if 'assessment_id' in request.session and 'tenant_id' in request.session:
            try:
                # Get tenant for schema context
                with schema_context('public'):
                    tenant = TenantConfig.objects.get(tenant_id=request.session['tenant_id'])
                
                # Get assessment using tenant's schema
                with schema_context(tenant.schema_name):
                    assessment = Assessment.objects.get(id=request.session['assessment_id'])
                    context['assessment'] = {
                        'id': assessment.id,
                        'name': assessment.name,
                        'description': assessment.description
                    }
            except (TenantConfig.DoesNotExist, Assessment.DoesNotExist):
                pass
        
        if 'iro_id' in request.session and 'tenant_id' in request.session:
            try:
                # Get tenant for schema context
                with schema_context('public'):
                    tenant = TenantConfig.objects.get(tenant_id=request.session['tenant_id'])
                
                # Get IRO using tenant's schema
                from apps.assessments.utils import get_iro_by_id
                iro = get_iro_by_id(request.session['iro_id'], tenant)
                if iro:
                    context['iro'] = {
                        'iro_id': iro.iro_id,
                        'title': iro.title if hasattr(iro, 'title') else f"IRO #{iro.iro_id}",
                        'type': iro.type
                    }
            except TenantConfig.DoesNotExist:
                pass
        
        return JsonResponse({
            'success': True,
            'context': context,
            'redirect_url': redirect_url if request.GET.get('reload', False) else None
        })
    else:
        # For non-AJAX requests, redirect to the specified next URL
        return redirect(redirect_url)
    

# Get the frontend logger
frontend_logger = logging.getLogger('frontend')

@require_POST
@csrf_exempt  # In production, you should use proper CSRF protection
def frontend_log(request):
    """
    Endpoint to receive logs from the frontend
    """
    try:
        data = json.loads(request.body)
        logs = data.get('logs', [])
        
        for log_entry in logs:
            level = log_entry.get('level', 'INFO').upper()
            message = log_entry.get('message', '')
            context = log_entry.get('context', {})
            
            # Add request metadata
            meta = {
                'ip': request.META.get('REMOTE_ADDR'),
                'user_agent': log_entry.get('userAgent'),
                'url': log_entry.get('url'),
                'user': str(request.user) if request.user.is_authenticated else 'anonymous',
                'session_id': log_entry.get('sessionId'),
            }
            
            # Combine context with metadata
            extra = {'meta': meta, 'context': context}
            
            # Log with appropriate level
            if level == 'DEBUG':
                frontend_logger.debug(message, extra=extra)
            elif level == 'INFO':
                frontend_logger.info(message, extra=extra)
            elif level == 'WARNING':
                frontend_logger.warning(message, extra=extra)
            elif level == 'ERROR':
                frontend_logger.error(message, extra=extra)
            elif level == 'CRITICAL':
                frontend_logger.critical(message, extra=extra)
            else:
                frontend_logger.info(message, extra=extra)
        
        return JsonResponse({'success': True, 'count': len(logs)})
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)