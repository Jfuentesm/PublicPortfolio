"""
Topic Aggregator Service

This module provides functions for aggregating IROs into topics and calculating
topic-level materiality scores for the double materiality quadrants.
"""

from django.db.models import Avg, Count, Q, F
from django_tenants.utils import schema_context
from apps.assessments.models import Topic, IRO, ImpactAssessment, RiskOppAssessment, IROVersion
from tenants.models import TenantConfig


def get_topics_for_tenant(tenant=None):
    """
    Get all topics for a specific tenant or use the current schema if no tenant specified.
    Returns a list of Topic objects to ensure they're fully loaded before exiting schema context.
    """
    if tenant and hasattr(tenant, 'schema_name') and tenant.schema_name:
        # If a tenant is specified, use its schema
        try:
            with schema_context(tenant.schema_name):
                try:
                    # Try to get all Topics for this tenant
                    topics = list(Topic.objects.filter(tenant=tenant))
                    return topics
                except Exception as inner_e:
                    print(f"Error querying Topics in tenant schema {tenant.schema_name}: {str(inner_e)}")
                    return []
        except Exception as schema_e:
            print(f"Error switching to schema {tenant.schema_name}: {str(schema_e)}")
            return []
    else:
        # If no valid tenant, use the current schema but be careful about filtering
        from django.db import connection
        current_schema = connection.schema_name
        if current_schema and current_schema.startswith('tenant_'):
            # We're in a tenant schema, get all Topics for this schema
            try:
                return list(Topic.objects.all())
            except Exception as query_e:
                print(f"Error querying Topics in current schema {current_schema}: {str(query_e)}")
                return []
        else:
            # We're in the public schema, we can't get Topics directly
            return []


def get_all_tenant_topics():
    """
    Get Topics from all tenant schemas.
    This is useful for admin views or aggregate dashboards.
    """
    all_topics = []
    
    for tenant in TenantConfig.objects.all():
        with schema_context(tenant.schema_name):
            # Convert QuerySet to list to ensure objects are fully loaded
            tenant_topics = list(Topic.objects.filter(tenant=tenant))
            all_topics.extend(tenant_topics)
    
    return all_topics


def get_topics_by_materiality_quadrant(tenant=None):
    """
    Group topics by their materiality quadrant.
    
    Returns a dictionary with four keys:
    - 'financially_material': Topics that are financially material but not impact material
    - 'double_material': Topics that are both financially and impact material
    - 'not_material': Topics that are neither financially nor impact material
    - 'impact_material': Topics that are impact material but not financially material
    """
    # Get topics for the tenant
    if tenant:
        topics = get_topics_for_tenant(tenant)
    else:
        topics = get_all_tenant_topics()
    
    # Initialize result dictionary
    result = {
        'financially_material': [],
        'double_material': [],
        'not_material': [],
        'impact_material': []
    }
    
    # Group topics by quadrant
    for topic in topics:
        quadrant = topic.get_materiality_quadrant()
        result[quadrant].append({
            'id': topic.topic_id,
            'name': topic.name,
            'level': topic.level,
            'impact_score': topic.get_impact_materiality_score(),
            'financial_score': topic.get_financial_materiality_score(),
            'iro_count': topic.get_iro_count()
        })
    
    return result


# apps/assessments/topic_aggregator.py - update the get_priority_iros function

def get_priority_iros(tenant=None, limit=10):
    """
    Get high-priority IROs for quick editing.
    
    Priority is determined by:
    1. High materiality score (impact or financial)
    2. Recently created or updated
    3. Incomplete assessments
    
    Returns a list of IRO objects with their latest assessment scores.
    """
    from apps.assessments.utils import get_iros_for_tenant, get_all_tenant_iros
    import logging
    
    logger = logging.getLogger('apps')
    
    # Get IROs based on tenant context
    if tenant:
        try:
            logger.debug("Fetching priority IROs for tenant: %s", tenant.tenant_name)
            iro_queryset = get_iros_for_tenant(tenant)
        except Exception as e:
            logger.error("Error fetching IROs for tenant %s: %s", 
                         tenant.tenant_name if tenant else "None", str(e), exc_info=True)
            return []
    else:
        try:
            logger.debug("Fetching priority IROs for all tenants")
            iro_queryset = get_all_tenant_iros()
        except Exception as e:
            logger.error("Error fetching IROs for all tenants: %s", str(e), exc_info=True)
            return []
    
    logger.debug("Found %d IROs in queryset", len(iro_queryset) if iro_queryset else 0)
    
    # Filter IROs with assessment scores
    scored_iros = []
    for iro in iro_queryset:
        if hasattr(iro, 'last_assessment_score') and iro.last_assessment_score:
            scored_iros.append(iro)
    
    # Sort IROs by last_assessment_score (if available)
    sorted_iros = sorted(
        scored_iros,
        key=lambda x: float(x.last_assessment_score) if x.last_assessment_score else 0, 
        reverse=True
    )
    
    # Prepare result with assessment scores
    result = []
    for iro in sorted_iros[:limit]:
        try:
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
            
            # Get the topic information
            if tenant:
                with schema_context(tenant.schema_name):
                    version = IROVersion.objects.filter(iro=iro).order_by('-version_number').first()
            else:
                tenant_obj = iro.tenant
                with schema_context(tenant_obj.schema_name):
                    version = IROVersion.objects.filter(iro=iro).order_by('-version_number').first()
            
            topic_level1 = version.sust_topic_level1 if version else None
            
            # Ensure all values are JSON-serializable
            iro_data = {
                'iro_id': iro.iro_id,
                'title': str(iro.title) if hasattr(iro, 'title') else f"IRO #{iro.iro_id}",
                'type': str(iro.type),
                'topic': str(topic_level1) if topic_level1 else None,
                'impact_score': float(impact_score) if impact_score else 0.0,
                'financial_score': float(financial_score) if financial_score else 0.0,
                'current_stage': str(iro.current_stage),
            }
            result.append(iro_data)
        except Exception as e:
            logger.error("Error processing IRO %s: %s", iro.iro_id, str(e), exc_info=True)
    
    logger.debug("Returning %d priority IROs", len(result))
    return result


def sync_topics_from_iro_versions(tenant=None):
    """
    Synchronize Topics based on the topic fields in IROVersion objects.
    This ensures that all topics referenced in IROs have corresponding Topic objects.
    """
    from django.db import transaction
    
    if tenant:
        tenants = [tenant]
    else:
        tenants = TenantConfig.objects.all()
    
    for tenant_obj in tenants:
        with schema_context(tenant_obj.schema_name):
            with transaction.atomic():
                # Get all unique topic values from IROVersion
                level1_topics = IROVersion.objects.filter(
                    sust_topic_level1__isnull=False
                ).values_list('sust_topic_level1', flat=True).distinct()
                
                level2_topics = IROVersion.objects.filter(
                    sust_topic_level2__isnull=False
                ).values_list('sust_topic_level2', 'sust_topic_level1').distinct()
                
                level3_topics = IROVersion.objects.filter(
                    sust_topic_level3__isnull=False
                ).values_list('sust_topic_level3', 'sust_topic_level2').distinct()
                
                # Create level 1 topics if they don't exist
                for topic_name in level1_topics:
                    Topic.objects.get_or_create(
                        tenant=tenant_obj,
                        name=topic_name,
                        level=1,
                        defaults={'description': f"Level 1 topic: {topic_name}"}
                    )
                
                # Create level 2 topics if they don't exist
                for topic_name, parent_name in level2_topics:
                    if not topic_name:
                        continue
                        
                    # Get parent topic
                    parent_topic = None
                    if parent_name:
                        try:
                            parent_topic = Topic.objects.get(
                                tenant=tenant_obj,
                                name=parent_name,
                                level=1
                            )
                        except Topic.DoesNotExist:
                            # Create parent topic if it doesn't exist
                            parent_topic = Topic.objects.create(
                                tenant=tenant_obj,
                                name=parent_name,
                                level=1,
                                description=f"Level 1 topic: {parent_name}"
                            )
                    
                    # Create topic
                    Topic.objects.get_or_create(
                        tenant=tenant_obj,
                        name=topic_name,
                        level=2,
                        defaults={
                            'description': f"Level 2 topic: {topic_name}",
                            'parent_topic': parent_topic
                        }
                    )
                
                # Create level 3 topics if they don't exist
                for topic_name, parent_name in level3_topics:
                    if not topic_name:
                        continue
                        
                    # Get parent topic
                    parent_topic = None
                    if parent_name:
                        try:
                            parent_topic = Topic.objects.get(
                                tenant=tenant_obj,
                                name=parent_name,
                                level=2
                            )
                        except Topic.DoesNotExist:
                            # Skip if parent doesn't exist
                            continue
                    
                    # Create topic
                    Topic.objects.get_or_create(
                        tenant=tenant_obj,
                        name=topic_name,
                        level=3,
                        defaults={
                            'description': f"Level 3 topic: {topic_name}",
                            'parent_topic': parent_topic
                        }
                    )
    
    return True
