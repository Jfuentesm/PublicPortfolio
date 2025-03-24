"""
Unit tests for the Topic model and topic aggregator service.
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django_tenants.test.cases import TenantTestCase
from django_tenants.utils import schema_context

from apps.assessments.models import IRO, Topic, ImpactAssessment, RiskOppAssessment
from apps.assessments.topic_aggregator import (
    get_topics_by_materiality_quadrant,
    get_priority_iros,
    sync_topics_from_iro_versions
)
from apps.tenants.models import TenantConfig


class TopicModelTestCase(TenantTestCase):
    """Test case for the Topic model."""

    def setUp(self):
        """Set up test data."""
        # Create a test tenant
        self.tenant = TenantConfig.objects.create(
            schema_name='test',
            name='Test Tenant',
            paid_until='2025-12-31',
            on_trial=False
        )
        
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        # Create test topics
        with schema_context(self.tenant.schema_name):
            # Create topics
            self.topic1 = Topic.objects.create(
                tenant=self.tenant,
                name='Climate Change',
                level=1,
                description='Climate change and related impacts'
            )
            
            self.topic2 = Topic.objects.create(
                tenant=self.tenant,
                name='Human Rights',
                level=1,
                description='Human rights and labor practices'
            )
            
            # Create IROs for each topic
            self.iro1 = IRO.objects.create(
                tenant=self.tenant,
                title='Carbon Emissions',
                type='Risk',
                sust_topic_level1='Climate Change',
                current_stage='Approved'
            )
            
            self.iro2 = IRO.objects.create(
                tenant=self.tenant,
                title='Renewable Energy',
                type='Opportunity',
                sust_topic_level1='Climate Change',
                current_stage='Approved'
            )
            
            self.iro3 = IRO.objects.create(
                tenant=self.tenant,
                title='Labor Rights',
                type='Risk',
                sust_topic_level1='Human Rights',
                current_stage='Approved'
            )
            
            # Create assessments for each IRO
            self.impact_assessment1 = ImpactAssessment.objects.create(
                iro=self.iro1,
                tenant=self.tenant,
                created_by=self.user,
                impact_materiality_score=4.5
            )
            
            self.risk_opp_assessment1 = RiskOppAssessment.objects.create(
                iro=self.iro1,
                tenant=self.tenant,
                created_by=self.user,
                financial_materiality_score=4.0
            )
            
            self.impact_assessment2 = ImpactAssessment.objects.create(
                iro=self.iro2,
                tenant=self.tenant,
                created_by=self.user,
                impact_materiality_score=3.5
            )
            
            self.risk_opp_assessment2 = RiskOppAssessment.objects.create(
                iro=self.iro2,
                tenant=self.tenant,
                created_by=self.user,
                financial_materiality_score=4.2
            )
            
            self.impact_assessment3 = ImpactAssessment.objects.create(
                iro=self.iro3,
                tenant=self.tenant,
                created_by=self.user,
                impact_materiality_score=4.0
            )
            
            self.risk_opp_assessment3 = RiskOppAssessment.objects.create(
                iro=self.iro3,
                tenant=self.tenant,
                created_by=self.user,
                financial_materiality_score=2.0
            )

    def test_topic_materiality_calculation(self):
        """Test topic materiality calculation."""
        with schema_context(self.tenant.schema_name):
            # Sync topics from IRO versions
            sync_topics_from_iro_versions(self.tenant)
            
            # Get the topics
            topic1 = Topic.objects.get(name='Climate Change')
            topic2 = Topic.objects.get(name='Human Rights')
            
            # Test impact score calculation
            self.assertAlmostEqual(topic1.calculate_impact_score(), 4.0, places=1)
            self.assertAlmostEqual(topic2.calculate_impact_score(), 4.0, places=1)
            
            # Test financial score calculation
            self.assertAlmostEqual(topic1.calculate_financial_score(), 4.1, places=1)
            self.assertAlmostEqual(topic2.calculate_financial_score(), 2.0, places=1)
            
            # Test materiality quadrant determination
            self.assertEqual(topic1.get_materiality_quadrant(), 'double_material')
            self.assertEqual(topic2.get_materiality_quadrant(), 'impact_material')

    def test_topics_by_materiality_quadrant(self):
        """Test getting topics by materiality quadrant."""
        with schema_context(self.tenant.schema_name):
            # Sync topics from IRO versions
            sync_topics_from_iro_versions(self.tenant)
            
            # Get topics by materiality quadrant
            quadrants = get_topics_by_materiality_quadrant(self.tenant)
            
            # Test that topics are in the correct quadrants
            self.assertEqual(len(quadrants['double_material']), 1)
            self.assertEqual(quadrants['double_material'][0]['name'], 'Climate Change')
            
            self.assertEqual(len(quadrants['impact_material']), 1)
            self.assertEqual(quadrants['impact_material'][0]['name'], 'Human Rights')
            
            self.assertEqual(len(quadrants['financially_material']), 0)
            self.assertEqual(len(quadrants['not_material']), 0)

    def test_priority_iros(self):
        """Test getting priority IROs."""
        with schema_context(self.tenant.schema_name):
            # Get priority IROs
            priority_iros = get_priority_iros(self.tenant)
            
            # Test that IROs are returned in the correct order (by materiality score)
            self.assertEqual(len(priority_iros), 3)
            self.assertEqual(priority_iros[0]['iro_id'], self.iro1.iro_id)
            self.assertEqual(priority_iros[1]['iro_id'], self.iro2.iro_id)
            self.assertEqual(priority_iros[2]['iro_id'], self.iro3.iro_id)
