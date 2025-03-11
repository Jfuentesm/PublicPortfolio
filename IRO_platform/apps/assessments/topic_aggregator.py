"""
Topic Aggregator Service

This module provides functions for aggregating IROs into topics and calculating
topic-level materiality scores for the double materiality quadrants.
"""

from django.db.models import Avg, Count, Q, F
from django_tenants.utils import schema_context
from apps.assessments.models import Topic, IRO, ImpactAssessment, RiskOppAssessment, IROVersion
from tenants.models import TenantConfig
import logging

logger = logging.getLogger('apps')

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
                    logger.error(f"Error querying Topics in tenant schema {tenant.schema_name}: {str(inner_e)}", exc_info=True)
                    return []
        except Exception as schema_e:
            logger.error(f"Error switching to schema {tenant.schema_name}: {str(schema_e)}", exc_info=True)
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
                logger.error(f"Error querying Topics in current schema {current_schema}: {str(query_e)}", exc_info=True)
                return []
        else:
            # We're in the public schema, we can't get Topics directly
            logger.warning("Attempted to get topics while in public schema with no tenant specified")
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
    topics = []
    
    if tenant:
        # Always use schema context when accessing tenant data
        with schema_context(tenant.schema_name):
            # Ensure topics are synced before processing
            sync_topics_from_iro_versions(tenant)
            
            # Get topics with schema context
            topics = list(Topic.objects.filter(tenant=tenant))
            logger.debug(f"Found {len(topics)} topics for tenant {tenant.tenant_name}")
    else:
        # For cross-tenant operations
        topics = get_all_tenant_topics()
        logger.debug(f"Found {len(topics)} topics across all tenants")
    
    # Initialize result dictionary
    result = {
        'financially_material': [],
        'double_material': [],
        'not_material': [],
        'impact_material': []
    }
    
    # Group topics by quadrant
    for topic in topics:
        # Make sure to use schema context for topic operations
        with schema_context(topic.tenant.schema_name):
            try:
                quadrant = topic.get_materiality_quadrant()
                impact_score = topic.get_impact_materiality_score()
                financial_score = topic.get_financial_materiality_score()
                iro_count = topic.get_iro_count()
                
                # Log for debugging
                logger.debug(f"Topic '{topic.name}': quadrant={quadrant}, impact={impact_score}, financial={financial_score}, iros={iro_count}")
                
                result[quadrant].append({
                    'id': topic.topic_id,
                    'name': topic.name,
                    'level': topic.level,
                    'impact_score': impact_score,
                    'financial_score': financial_score,
                    'iro_count': iro_count
                })
            except Exception as e:
                logger.error(f"Error processing topic {topic.name} (ID: {topic.topic_id}): {str(e)}", exc_info=True)
    
    return result


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
    
    # Get IROs based on tenant context
    if tenant:
        try:
            # Add tenant to log context
            tenant_name = tenant.tenant_name if hasattr(tenant, 'tenant_name') else str(tenant)
            logger.debug(f"Fetching priority IROs for tenant: {tenant_name}")
            
            # Make sure we use schema context for tenant operations
            with schema_context(tenant.schema_name):
                iro_queryset = list(IRO.objects.filter(tenant=tenant))
        except Exception as e:
            tenant_name = tenant.tenant_name if hasattr(tenant, 'tenant_name') else "None"
            logger.error(f"Error fetching IROs for tenant {tenant_name}: {str(e)}", exc_info=True)
            return []
    else:
        try:
            # Default tenant for all-tenant operations
            logger.debug("Fetching priority IROs for all tenants")
            iro_queryset = get_all_tenant_iros()
        except Exception as e:
            logger.error(f"Error fetching IROs for all tenants: {str(e)}", exc_info=True)
            return []
    
    logger.debug(f"Found {len(iro_queryset) if iro_queryset else 0} IROs in queryset")
    
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
            tenant_to_use = tenant or iro.tenant
            
            # Always use schema context for tenant operations
            with schema_context(tenant_to_use.schema_name):
                impact_assessments = list(ImpactAssessment.objects.filter(iro=iro, tenant=tenant_to_use).order_by('-created_on'))
                risk_opp_assessments = list(RiskOppAssessment.objects.filter(iro=iro, tenant=tenant_to_use).order_by('-created_on'))
            
                impact_score = float(impact_assessments[0].impact_materiality_score or 0) if impact_assessments else 0.0
                financial_score = float(risk_opp_assessments[0].financial_materiality_score or 0) if risk_opp_assessments else 0.0
                
                # Get the topic information
                version = IROVersion.objects.filter(iro=iro, tenant=tenant_to_use).order_by('-version_number').first()
                
                topic_level1 = version.sust_topic_level1 if version else None
                
                # Ensure all values are JSON-serializable
                iro_data = {
                    'iro_id': iro.iro_id,
                    'title': str(iro.title) if hasattr(iro, 'title') else f"IRO #{iro.iro_id}",
                    'type': str(iro.type),
                    'topic': str(topic_level1) if topic_level1 else None,
                    'impact_score': impact_score,
                    'financial_score': financial_score,
                    'current_stage': str(iro.current_stage),
                }
                result.append(iro_data)
        except Exception as e:
            iro_id = getattr(iro, 'iro_id', 'unknown')
            logger.error(f"Error processing IRO {iro_id}: {str(e)}", exc_info=True)
    
    logger.debug(f"Returning {len(result)} priority IROs")
    return result


def sync_topics_from_iro_versions(tenant=None):
    """
    Synchronize Topics based on the topic fields in IROVersion objects.
    This ensures that all topics referenced in IROs have corresponding Topic objects.
    """
    from django.db import transaction
    
    if tenant is None:
        # If no tenant specified, log and return
        logger.warning("No tenant specified for sync_topics_from_iro_versions")
        return False
    
    logger.info(f"Syncing topics for tenant: {tenant.tenant_name}")
    
    # Always use schema context when working with tenant data
    with schema_context(tenant.schema_name):
        with transaction.atomic():
            try:
                # Get all unique topic values from IROVersion
                level1_topics = IROVersion.objects.filter(
                    tenant=tenant,
                    sust_topic_level1__isnull=False,
                    sust_topic_level1__gte=''  # Filter out empty strings
                ).values_list('sust_topic_level1', flat=True).distinct()
                
                level2_topics = IROVersion.objects.filter(
                    tenant=tenant,
                    sust_topic_level2__isnull=False,
                    sust_topic_level2__gte=''  # Filter out empty strings
                ).values_list('sust_topic_level2', 'sust_topic_level1').distinct()
                
                level3_topics = IROVersion.objects.filter(
                    tenant=tenant,
                    sust_topic_level3__isnull=False,
                    sust_topic_level3__gte=''  # Filter out empty strings
                ).values_list('sust_topic_level3', 'sust_topic_level2').distinct()
                
                # Log the counts for debugging
                logger.debug(f"Found {len(level1_topics)} level 1 topics, {len(level2_topics)} level 2 topics, {len(level3_topics)} level 3 topics")
                
                # Create level 1 topics if they don't exist
                for topic_name in level1_topics:
                    Topic.objects.get_or_create(
                        tenant=tenant,
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
                                tenant=tenant,
                                name=parent_name,
                                level=1
                            )
                        except Topic.DoesNotExist:
                            # Create parent topic if it doesn't exist
                            parent_topic = Topic.objects.create(
                                tenant=tenant,
                                name=parent_name,
                                level=1,
                                description=f"Level 1 topic: {parent_name}"
                            )
                    
                    # Create topic
                    Topic.objects.get_or_create(
                        tenant=tenant,
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
                                tenant=tenant,
                                name=parent_name,
                                level=2
                            )
                        except Topic.DoesNotExist:
                            # Skip if parent doesn't exist
                            continue
                    
                    # Create topic
                    Topic.objects.get_or_create(
                        tenant=tenant,
                        name=topic_name,
                        level=3,
                        defaults={
                            'description': f"Level 3 topic: {topic_name}",
                            'parent_topic': parent_topic
                        }
                    )
                
                # Count the final number of topics
                topic_count = Topic.objects.filter(tenant=tenant).count()
                logger.info(f"Successfully synced topics for tenant {tenant.tenant_name}. Total topics: {topic_count}")
                
                return True
                
            except Exception as e:
                logger.error(f"Error syncing topics for tenant {tenant.tenant_name}: {str(e)}", exc_info=True)
                return False