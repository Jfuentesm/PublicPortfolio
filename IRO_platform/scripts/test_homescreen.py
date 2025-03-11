#!/usr/bin/env python
"""
Test script for the new homescreen implementation.
This script populates test data and verifies the functionality of the new features.
"""
import os
import sys
import random
import django
from django.utils import timezone
from datetime import timedelta

# Set up Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'iro_platform.settings')
django.setup()

from django.contrib.auth.models import User
from django_tenants.utils import schema_context
from apps.tenants.models import TenantConfig
from apps.assessments.models import IRO, Topic, ImpactAssessment, RiskOppAssessment, AuditTrail
from apps.assessments.topic_aggregator import sync_topics_from_iro_versions


def create_test_data(tenant, user):
    """Create test data for the homescreen."""
    print(f"Creating test data for tenant: {tenant.tenant_name}")
    
    # Define test topics
    topics = [
        {
            'name': 'Climate Change',
            'level': 1,
            'description': 'Climate change and related impacts'
        },
        {
            'name': 'Human Rights',
            'level': 1,
            'description': 'Human rights and labor practices'
        },
        {
            'name': 'Governance',
            'level': 1,
            'description': 'Corporate governance and ethics'
        },
        {
            'name': 'Water Management',
            'level': 1,
            'description': 'Water usage, conservation, and pollution'
        },
        {
            'name': 'Waste Management',
            'level': 1,
            'description': 'Waste reduction, recycling, and disposal'
        },
        {
            'name': 'Biodiversity',
            'level': 1,
            'description': 'Protection of ecosystems and biodiversity'
        },
        {
            'name': 'Supply Chain',
            'level': 1,
            'description': 'Supply chain management and sustainability'
        },
        {
            'name': 'Product Safety',
            'level': 1,
            'description': 'Product safety and quality'
        }
    ]
    
    # Define IROs for each topic
    iros_by_topic = {
        'Climate Change': [
            {
                'title': 'Carbon Emissions',
                'type': 'Risk',
                'impact_score': 4.5,
                'financial_score': 4.0
            },
            {
                'title': 'Renewable Energy',
                'type': 'Opportunity',
                'impact_score': 3.5,
                'financial_score': 4.2
            },
            {
                'title': 'Climate Adaptation',
                'type': 'Risk',
                'impact_score': 4.0,
                'financial_score': 3.8
            }
        ],
        'Human Rights': [
            {
                'title': 'Labor Rights',
                'type': 'Risk',
                'impact_score': 4.0,
                'financial_score': 2.0
            },
            {
                'title': 'Diversity and Inclusion',
                'type': 'Opportunity',
                'impact_score': 3.8,
                'financial_score': 2.5
            }
        ],
        'Governance': [
            {
                'title': 'Anti-corruption',
                'type': 'Risk',
                'impact_score': 3.5,
                'financial_score': 3.8
            },
            {
                'title': 'Board Diversity',
                'type': 'Opportunity',
                'impact_score': 2.8,
                'financial_score': 3.2
            }
        ],
        'Water Management': [
            {
                'title': 'Water Scarcity',
                'type': 'Risk',
                'impact_score': 4.2,
                'financial_score': 2.8
            },
            {
                'title': 'Water Recycling',
                'type': 'Opportunity',
                'impact_score': 3.5,
                'financial_score': 2.2
            }
        ],
        'Waste Management': [
            {
                'title': 'Hazardous Waste',
                'type': 'Risk',
                'impact_score': 3.8,
                'financial_score': 2.5
            },
            {
                'title': 'Circular Economy',
                'type': 'Opportunity',
                'impact_score': 3.2,
                'financial_score': 3.0
            }
        ],
        'Biodiversity': [
            {
                'title': 'Habitat Destruction',
                'type': 'Risk',
                'impact_score': 4.0,
                'financial_score': 1.8
            }
        ],
        'Supply Chain': [
            {
                'title': 'Supplier Compliance',
                'type': 'Risk',
                'impact_score': 3.5,
                'financial_score': 3.2
            },
            {
                'title': 'Sustainable Sourcing',
                'type': 'Opportunity',
                'impact_score': 3.0,
                'financial_score': 3.5
            }
        ],
        'Product Safety': [
            {
                'title': 'Product Recalls',
                'type': 'Risk',
                'impact_score': 2.5,
                'financial_score': 4.5
            },
            {
                'title': 'Quality Improvement',
                'type': 'Opportunity',
                'impact_score': 2.0,
                'financial_score': 4.0
            }
        ]
    }
    
    with schema_context(tenant.schema_name):
        # Create topics
        for topic_data in topics:
            Topic.objects.get_or_create(
                tenant=tenant,
                name=topic_data['name'],
                defaults={
                    'level': topic_data['level'],
                    'description': topic_data['description']
                }
            )
        
        # Create IROs and assessments
        for topic_name, iros in iros_by_topic.items():
            for iro_data in iros:
                # Create IRO
                iro, created = IRO.objects.get_or_create(
                    tenant=tenant,
                    title=iro_data['title'],
                    defaults={
                        'type': iro_data['type'],
                        'sust_topic_level1': topic_name,
                        'current_stage': random.choice(['Draft', 'In Review', 'Approved'])
                    }
                )
                
                if created:
                    # Create impact assessment
                    impact_assessment = ImpactAssessment.objects.create(
                        iro=iro,
                        tenant=tenant,
                        created_by=user,
                        impact_materiality_score=iro_data['impact_score']
                    )
                    
                    # Create risk/opportunity assessment
                    risk_opp_assessment = RiskOppAssessment.objects.create(
                        iro=iro,
                        tenant=tenant,
                        created_by=user,
                        financial_materiality_score=iro_data['financial_score']
                    )
                    
                    # Create audit trail entry
                    AuditTrail.objects.create(
                        tenant=tenant,
                        user=user,
                        entity_type='IRO',
                        entity_id=iro.iro_id,
                        action='created',
                        timestamp=timezone.now() - timedelta(days=random.randint(0, 30))
                    )
        
        # Sync topics from IRO versions
        sync_topics_from_iro_versions(tenant)
        
        print(f"Created {IRO.objects.filter(tenant=tenant).count()} IROs for {Topic.objects.filter(tenant=tenant).count()} topics")


def test_homescreen_data(tenant):
    """Test the homescreen data for a tenant."""
    print(f"Testing homescreen data for tenant: {tenant.tenant_name}")
    
    with schema_context(tenant.schema_name):
        # Test topic materiality quadrants
        topics = Topic.objects.filter(tenant=tenant)
        
        quadrant_counts = {
            'double_material': 0,
            'impact_material': 0,
            'financially_material': 0,
            'not_material': 0
        }
        
        for topic in topics:
            quadrant = topic.get_materiality_quadrant()
            quadrant_counts[quadrant] += 1
        
        print("Topic materiality quadrants:")
        for quadrant, count in quadrant_counts.items():
            print(f"  {quadrant}: {count} topics")
        
        # Test priority IROs
        from apps.assessments.topic_aggregator import get_priority_iros
        priority_iros = get_priority_iros(tenant)
        
        print(f"Priority IROs: {len(priority_iros)}")
        for i, iro in enumerate(priority_iros[:5]):
            print(f"  {i+1}. {iro['title']} (Impact: {iro['impact_score']}, Financial: {iro['financial_score']})")


def main():
    """Main function."""
    # Get or create test tenant
    tenant, created = TenantConfig.objects.get_or_create(
        schema_name='test',
        defaults={
            'tenant_name': 'Test Tenant',
            'paid_until': '2025-12-31',
            'on_trial': False
        }
    )
    
    # Get or create test user
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'test@example.com',
            'is_staff': True
        }
    )
    
    if created:
        user.set_password('testpassword')
        user.save()
    
    # Create test data
    create_test_data(tenant, user)
    
    # Test homescreen data
    test_homescreen_data(tenant)
    
    print("\nTest completed successfully!")


if __name__ == '__main__':
    main()
