"""
API views for topic-level data.

This module provides API views for topic-level data, including:
- Topic-level materiality data for quadrants
- High-priority IROs for quick editing
- Recent activity data
"""

import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from apps.assessments.models import Topic, IRO, AuditTrail
from apps.assessments.serializers import (
    TopicSerializer, PriorityIROSerializer,
    RecentActivitySerializer, TopicMaterialityQuadrantSerializer
)
from apps.assessments.topic_aggregator import (
    get_topics_by_materiality_quadrant,
    get_priority_iros,
    sync_topics_from_iro_versions
)
from django_tenants.utils import schema_context
from rest_framework.permissions import IsAuthenticated

logger = logging.getLogger(__name__)

class TopicMaterialityView(APIView):
    """
    API view for topic-level materiality data for quadrants.
    """
    def get(self, request):
        # Get tenant from context middleware
        tenant = request.context.get('tenant')
        
        if not tenant:
            logger.warning("No tenant context found in TopicMaterialityView")
            return Response({"error": "No tenant context found"}, status=status.HTTP_400_BAD_REQUEST)
            
        logger.debug(f"TopicMaterialityView: Getting materiality data for tenant {tenant.tenant_name}")
        
        # Sync topics from IRO versions to ensure all topics exist
        # This should be done within the tenant's schema
        with schema_context(tenant.schema_name):
            sync_topics_from_iro_versions(tenant)
            
        # Get topics grouped by materiality quadrant
        # This function already handles schema context properly
        quadrant_data = get_topics_by_materiality_quadrant(tenant)
        
        # Log the returned data for debugging
        logger.debug(f"TopicMaterialityView: Returning data with {len(quadrant_data['financially_material'])} financially material, " +
                    f"{len(quadrant_data['double_material'])} double material, " +
                    f"{len(quadrant_data['not_material'])} not material, " +
                    f"{len(quadrant_data['impact_material'])} impact material topics")
        
        # Return the data
        return Response(quadrant_data)


class PriorityIROsView(APIView):
    """
    API view for high-priority IROs for quick editing.
    """
    def get(self, request):
        # Get tenant from context middleware
        tenant = request.context.get('tenant')
        
        if not tenant:
            logger.warning("No tenant context found in PriorityIROsView")
            return Response({"error": "No tenant context found"}, status=status.HTTP_400_BAD_REQUEST)
            
        # Get limit parameter (default to 10)
        limit = int(request.query_params.get('limit', 10))
        
        logger.debug(f"PriorityIROsView: Getting priority IROs for tenant {tenant.tenant_name}, limit {limit}")
        
        # Get priority IROs
        priority_iros = get_priority_iros(tenant, limit)
        
        # Added debug logging to see exactly which IROs are fetched
        logger.debug(f"Priority IROs fetched: {priority_iros}")
        
        # Return the data
        return Response(priority_iros)
    
    def patch(self, request):
        """
        Update multiple IROs at once.
        
        Expected request format:
        {
            "iros": [
                {"iro_id": 1, "current_stage": "In Review"},
                {"iro_id": 2, "current_stage": "Approved"}
            ]
        }
        """
        # Get tenant from context middleware
        tenant = request.context.get('tenant')
        
        if not tenant:
            logger.warning("No tenant context found in PriorityIROsView.patch")
            return Response({"error": "No tenant context found"}, status=status.HTTP_400_BAD_REQUEST)
            
        # Get IROs to update
        iros_data = request.data.get('iros', [])
        
        logger.debug(f"PriorityIROsView.patch: Updating {len(iros_data)} IROs for tenant {tenant.tenant_name}")
        
        updated_iros = []
        errors = []
        
        # Always use schema context for tenant operations
        with schema_context(tenant.schema_name):
            for iro_data in iros_data:
                iro_id = iro_data.get('iro_id')
                try:
                    iro = IRO.objects.get(iro_id=iro_id, tenant=tenant)
                    
                    # Update fields
                    if 'current_stage' in iro_data:
                        iro.current_stage = iro_data['current_stage']
                    
                    # Save changes
                    iro.save()
                    
                    # Create audit trail entry
                    AuditTrail.objects.create(
                        tenant=tenant,
                        entity_type='IRO',
                        entity_id=iro.iro_id,
                        action='updated',
                        user_id=request.user.id if (hasattr(request, 'user') and request.user.is_authenticated) else 0,
                        data_diff={'current_stage': iro.current_stage}
                    )
                    
                    updated_iros.append(iro)
                except IRO.DoesNotExist:
                    errors.append(f"IRO with ID {iro_id} not found")
                except Exception as e:
                    errors.append(f"Error updating IRO {iro_id}: {str(e)}")
        
        if errors:
            logger.error(f"PriorityIROsView.patch: Errors encountered: {errors}")
            return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)
            
        logger.debug(f"PriorityIROsView.patch: Successfully updated {len(updated_iros)} IROs")
        serializer = PriorityIROSerializer(updated_iros, many=True)
        return Response(serializer.data)


class BatchUpdateIROsView(APIView):
    """
    API view to update multiple IROs at once.
    Used by the quick-edit table on the dashboard.
    """
    permission_classes = [IsAuthenticated]
    
    def patch(self, request, *args, **kwargs):
        tenant = request.context.get('tenant')
        if not tenant:
            logger.warning("No tenant context found in BatchUpdateIROsView")
            return Response({"error": "No tenant selected"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the list of IROs to update
        iros_data = request.data.get('iros', [])
        if not iros_data:
            return Response({"error": "No IROs provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        logger.debug(f"BatchUpdateIROsView: Updating {len(iros_data)} IROs for tenant {tenant.tenant_name}")
        
        updated_iros = []
        errors = []
        
        # Always use schema context for tenant operations
        with schema_context(tenant.schema_name):
            for iro_data in iros_data:
                iro_id = iro_data.get('iro_id')
                if not iro_id:
                    errors.append({"error": "IRO ID is required", "data": iro_data})
                    continue
                
                try:
                    iro = IRO.objects.get(iro_id=iro_id, tenant=tenant)
                except IRO.DoesNotExist:
                    errors.append({"error": f"IRO with ID {iro_id} does not exist", "data": iro_data})
                    continue
                
                # Update the IRO fields
                if 'current_stage' in iro_data:
                    iro.current_stage = iro_data['current_stage']
                
                # Save the IRO
                try:
                    iro.save()
                    
                    # Create audit trail entry
                    AuditTrail.objects.create(
                        tenant=tenant,
                        user=request.user,
                        entity_type='IRO',
                        entity_id=iro.iro_id,
                        action='updated',
                        details=f"Updated via quick-edit: {', '.join(iro_data.keys())}"
                    )
                    
                    updated_iros.append({
                        'iro_id': iro.iro_id,
                        'title': iro.title,
                        'current_stage': iro.current_stage
                    })
                except Exception as e:
                    errors.append({"error": str(e), "data": iro_data})
        
        logger.debug(f"BatchUpdateIROsView: Updated {len(updated_iros)} IROs, encountered {len(errors)} errors")
        return Response({
            'updated_iros': updated_iros,
            'errors': errors
        }, status=status.HTTP_200_OK if not errors else status.HTTP_207_MULTI_STATUS)


class RecentActivityView(APIView):
    """
    API view for recent activity data.
    """
    def get(self, request):
        # Get tenant from context middleware
        tenant = request.context.get('tenant')
        
        # Get limit parameter (default to 5)
        limit = int(request.query_params.get('limit', 5))
        
        logger.debug(f"RecentActivityView: Getting recent activity for tenant {tenant.tenant_name if tenant else 'all'}, limit {limit}")
        
        recent_activities = []
        if tenant:
            # Always use schema context for tenant operations
            with schema_context(tenant.schema_name):
                recent_activities = list(AuditTrail.objects.filter(tenant=tenant).order_by('-timestamp')[:limit])
        else:
            # Aggregate across all tenants
            from tenants.models import TenantConfig
            for t in TenantConfig.objects.all():
                # Always use schema context for tenant operations
                with schema_context(t.schema_name):
                    tenant_activities = list(AuditTrail.objects.filter(tenant=t).order_by('-timestamp')[:limit])
                    recent_activities.extend(tenant_activities)
            recent_activities.sort(key=lambda x: x.timestamp, reverse=True)
            recent_activities = recent_activities[:limit]
        
        activity_data = []
        for activity in recent_activities:
            activity_info = {
                'timestamp': activity.timestamp,
                'action': activity.action,
                'description': f"{activity.entity_type} #{activity.entity_id} {activity.action}",
            }
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
        
        logger.debug(f"RecentActivityView: Returning {len(activity_data)} activities")
        return Response(activity_data)