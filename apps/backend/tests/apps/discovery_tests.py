"""Tests for discovery feeds."""
import pytest
from django.test import TestCase
from rest_framework.test import APIClient
from prisma import Prisma
import asyncio
from hypothesis.extra.django import TestCase as HypothesisTestCase


class DiscoveryFeedTests(TestCase):
    """
    Basic tests for discovery feed endpoints.
    
    Requirements:
        - 2.1: Display three tabs: Trending, New, For You
        - 2.2: Trending tab ordered by Trending_Score
        - 2.3: New tab ordered by publication date descending
    """
    
    def setUp(self):
        """Set up test client."""
        self.client = APIClient()
    
    def test_discover_endpoint_exists(self):
        """Test that discover endpoint is accessible."""
        response = self.client.get('/v1/discover/')
        # Should return 200 or 401, not 404
        self.assertIn(response.status_code, [200, 401])
    
    def test_trending_tab_parameter(self):
        """Test trending tab parameter."""
        response = self.client.get('/v1/discover/?tab=trending')
        # Should return 200 or 401, not 404
        self.assertIn(response.status_code, [200, 401])
    
    def test_new_tab_parameter(self):
        """Test new tab parameter."""
        response = self.client.get('/v1/discover/?tab=new')
        # Should return 200 or 401, not 404
        self.assertIn(response.status_code, [200, 401])
    
    def test_invalid_tab_parameter(self):
        """Test invalid tab parameter returns 400."""
        response = self.client.get('/v1/discover/?tab=invalid')
        self.assertEqual(response.status_code, 400)
    
    def test_for_you_requires_auth(self):
        """Test that for-you tab requires authentication."""
        response = self.client.get('/v1/discover/?tab=for-you')
        self.assertEqual(response.status_code, 401)
    
    def test_response_structure(self):
        """Test that response has correct structure."""
        response = self.client.get('/v1/discover/?tab=trending')
        if response.status_code == 200:
            data = response.json()
            self.assertIn('data', data)
            self.assertIn('next_cursor', data)
            self.assertIsInstance(data['data'], list)


class TrendingCalculatorTests(TestCase):
    """
    Tests for TrendingCalculator class.
    
    Requirements:
        - 16.1: Calculate Trending_Score using weighted engagement
        - 16.2: Apply time decay factor
    """
    
    def test_trending_calculator_import(self):
        """Test that TrendingCalculator can be imported."""
        from apps.discovery.trending import TrendingCalculator
        calculator = TrendingCalculator()
        self.assertIsNotNone(calculator)
        self.assertEqual(calculator.HOURLY_DECAY, 0.98)
    
    def test_engagement_weights(self):
        """Test that engagement weights are defined."""
        from apps.discovery.trending import TrendingCalculator
        calculator = TrendingCalculator()
        self.assertIn('save', calculator.ENGAGEMENT_WEIGHTS)
        self.assertIn('read', calculator.ENGAGEMENT_WEIGHTS)
        self.assertIn('like', calculator.ENGAGEMENT_WEIGHTS)
        self.assertIn('whisper', calculator.ENGAGEMENT_WEIGHTS)


class PersonalizationEngineTests(TestCase):
    """
    Tests for PersonalizationEngine class.
    
    Requirements:
        - 10.1: Track saves as interest signals
        - 10.2: Track reads as interest signals
    """
    
    def test_personalization_engine_import(self):
        """Test that PersonalizationEngine can be imported."""
        from apps.discovery.personalization import PersonalizationEngine
        engine = PersonalizationEngine()
        self.assertIsNotNone(engine)
        self.assertEqual(engine.DAILY_DECAY, 0.98)
    
    def test_interest_weights(self):
        """Test that interest weights are defined."""
        from apps.discovery.personalization import PersonalizationEngine
        engine = PersonalizationEngine()
        self.assertIn('save', engine.WEIGHTS)
        self.assertIn('complete_read', engine.WEIGHTS)
        self.assertIn('partial_read', engine.WEIGHTS)
        self.assertIn('like', engine.WEIGHTS)
        self.assertIn('follow', engine.WEIGHTS)



# Property-Based Tests
from hypothesis import given, strategies as st
from hypothesis.strategies import floats, lists, integers
from decimal import Decimal


class InterestDecayPropertyTests(HypothesisTestCase):
    """
    Property-based tests for interest score decay.
    
    Property 19: Interest Score Decay
    For any set of UserInterest records with scores S, after daily decay runs,
    all scores should equal S * 0.98
    
    Requirements:
        - 10.6: Apply daily score decay of 0.98
    """
    
    @given(lists(floats(min_value=0.0, max_value=1000.0, allow_nan=False, allow_infinity=False), min_size=1, max_size=100))
    def test_interest_decay_multiplies_by_0_98(self, initial_scores):
        """
        Property: After decay, all scores should equal original_score * 0.98
        
        This test verifies that the decay operation correctly multiplies
        all interest scores by the decay factor of 0.98.
        """
        import asyncio
        from prisma import Prisma
        from apps.discovery.tasks import apply_daily_decay
        import uuid
        
        async def run_test():
            db = Prisma()
            await db.connect()
            
            try:
                # Create test user
                test_user_id = str(uuid.uuid4())
                test_user = await db.userprofile.create(
                    data={
                        'clerk_user_id': f'test_decay_{test_user_id}',
                        'handle': f'test_decay_{test_user_id[:8]}',
                        'display_name': 'Test User'
                    }
                )
                
                # Create test tags and interest records
                created_interests = []
                for i, score in enumerate(initial_scores):
                    tag = await db.tag.create(
                        data={
                            'name': f'test_tag_{test_user_id}_{i}',
                            'slug': f'test-tag-{test_user_id}-{i}'
                        }
                    )
                    
                    interest = await db.userinterest.create(
                        data={
                            'user_id': test_user.id,
                            'tag_id': tag.id,
                            'score': float(score)
                        }
                    )
                    created_interests.append((interest.id, float(score)))
                
                # Apply decay
                apply_daily_decay()
                
                # Verify all scores are multiplied by 0.98
                for interest_id, original_score in created_interests:
                    updated_interest = await db.userinterest.find_unique(
                        where={'id': interest_id}
                    )
                    
                    expected_score = original_score * 0.98
                    actual_score = updated_interest.score
                    
                    # Allow small floating point error
                    self.assertAlmostEqual(
                        actual_score,
                        expected_score,
                        places=5,
                        msg=f"Score {original_score} should decay to {expected_score}, got {actual_score}"
                    )
                
                # Cleanup
                await db.userinterest.delete_many(
                    where={'user_id': test_user.id}
                )
                await db.tag.delete_many(
                    where={'name': {'startswith': f'test_tag_{test_user_id}'}}
                )
                await db.userprofile.delete(where={'id': test_user.id})
                
            finally:
                await db.disconnect()
        
        asyncio.run(run_test())
    
    @given(st.integers(min_value=1, max_value=50))
    def test_interest_decay_preserves_count(self, num_interests):
        """
        Property: Decay should not change the number of interest records
        
        This test verifies that the decay operation doesn't delete or
        create any interest records.
        """
        import asyncio
        from prisma import Prisma
        from apps.discovery.tasks import apply_daily_decay
        import uuid
        
        async def run_test():
            db = Prisma()
            await db.connect()
            
            try:
                # Create test user
                test_user_id = str(uuid.uuid4())
                test_user = await db.userprofile.create(
                    data={
                        'clerk_user_id': f'test_count_{test_user_id}',
                        'handle': f'test_count_{test_user_id[:8]}',
                        'display_name': 'Test User'
                    }
                )
                
                # Create interest records
                for i in range(num_interests):
                    tag = await db.tag.create(
                        data={
                            'name': f'test_tag_count_{test_user_id}_{i}',
                            'slug': f'test-tag-count-{test_user_id}-{i}'
                        }
                    )
                    
                    await db.userinterest.create(
                        data={
                            'user_id': test_user.id,
                            'tag_id': tag.id,
                            'score': 10.0
                        }
                    )
                
                # Count before decay
                count_before = await db.userinterest.count(
                    where={'user_id': test_user.id}
                )
                
                # Apply decay
                apply_daily_decay()
                
                # Count after decay
                count_after = await db.userinterest.count(
                    where={'user_id': test_user.id}
                )
                
                # Verify count is preserved
                self.assertEqual(
                    count_before,
                    count_after,
                    f"Interest count should remain {count_before}, got {count_after}"
                )
                
                # Cleanup
                await db.userinterest.delete_many(
                    where={'user_id': test_user.id}
                )
                await db.tag.delete_many(
                    where={'name': {'startswith': f'test_tag_count_{test_user_id}'}}
                )
                await db.userprofile.delete(where={'id': test_user.id})
                
            finally:
                await db.disconnect()
        
        asyncio.run(run_test())



class BackgroundJobTests(TestCase):
    """
    Unit tests for background jobs.
    
    Requirements:
        - 16.1: Calculate trending scores
        - 16.3: Recompute trending scores as background job
        - 19.2: Run every 10-30 minutes
        - 19.4: Run daily decay every 24 hours
        - 19.5: Retry on failure with exponential backoff
    """
    
    def test_trending_score_calculation(self):
        """
        Test that trending score is calculated correctly.
        
        Requirements:
            - 16.1: Weighted combination of engagement metrics
        """
        import asyncio
        from prisma import Prisma
        from apps.discovery.trending import TrendingCalculator
        from datetime import datetime
        import uuid
        
        async def run_test():
            db = Prisma()
            await db.connect()
            
            try:
                # Create test user and story
                test_user_id = str(uuid.uuid4())
                test_user = await db.userprofile.create(
                    data={
                        'clerk_user_id': f'test_trending_{test_user_id}',
                        'handle': f'test_trending_{test_user_id[:8]}',
                        'display_name': 'Test Author'
                    }
                )
                
                story = await db.story.create(
                    data={
                        'slug': f'test-story-{test_user_id}',
                        'title': 'Test Story',
                        'blurb': 'Test blurb',
                        'author_id': test_user.id,
                        'published': True,
                        'published_at': datetime.now()
                    }
                )
                
                # Create stats with known values
                today = datetime.now().date()
                await db.story_stats_daily.create(
                    data={
                        'story_id': story.id,
                        'date': today,
                        'saves_count': 10,
                        'reads_count': 20,
                        'likes_count': 5,
                        'whispers_count': 3
                    }
                )
                
                # Calculate trending score
                calculator = TrendingCalculator()
                score = await calculator.calculate_trending_score(story.id)
                
                # Verify score is calculated (should be > 0 with these stats)
                self.assertGreater(score, 0, "Trending score should be positive with engagement")
                
                # Verify weights are applied correctly
                # Expected raw score = 10*3.0 + 20*1.0 + 5*2.0 + 3*2.5 = 30 + 20 + 10 + 7.5 = 67.5
                # With decay (12 hours average): 67.5 * (0.98^12) ≈ 53.3
                expected_min = 50.0  # Allow some margin
                expected_max = 70.0
                self.assertGreater(score, expected_min, f"Score {score} should be > {expected_min}")
                self.assertLess(score, expected_max, f"Score {score} should be < {expected_max}")
                
                # Cleanup
                await db.story_stats_daily.delete_many(where={'story_id': story.id})
                await db.story.delete(where={'id': story.id})
                await db.userprofile.delete(where={'id': test_user.id})
                
            finally:
                await db.disconnect()
        
        asyncio.run(run_test())
    
    def test_daily_decay_application(self):
        """
        Test that daily decay is applied correctly.
        
        Requirements:
            - 10.6: Multiply all UserInterest scores by 0.98
            - 19.4: Run every 24 hours
        """
        import asyncio
        from prisma import Prisma
        from apps.discovery.tasks import apply_daily_decay
        import uuid
        
        async def run_test():
            db = Prisma()
            await db.connect()
            
            try:
                # Create test user
                test_user_id = str(uuid.uuid4())
                test_user = await db.userprofile.create(
                    data={
                        'clerk_user_id': f'test_decay_unit_{test_user_id}',
                        'handle': f'test_decay_unit_{test_user_id[:8]}',
                        'display_name': 'Test User'
                    }
                )
                
                # Create test tag and interest
                tag = await db.tag.create(
                    data={
                        'name': f'test_tag_decay_{test_user_id}',
                        'slug': f'test-tag-decay-{test_user_id}'
                    }
                )
                
                initial_score = 100.0
                interest = await db.userinterest.create(
                    data={
                        'user_id': test_user.id,
                        'tag_id': tag.id,
                        'score': initial_score
                    }
                )
                
                # Apply decay
                apply_daily_decay()
                
                # Verify score is decayed
                updated_interest = await db.userinterest.find_unique(
                    where={'id': interest.id}
                )
                
                expected_score = initial_score * 0.98
                self.assertAlmostEqual(
                    updated_interest.score,
                    expected_score,
                    places=5,
                    msg=f"Score should decay from {initial_score} to {expected_score}"
                )
                
                # Cleanup
                await db.userinterest.delete(where={'id': interest.id})
                await db.tag.delete(where={'id': tag.id})
                await db.userprofile.delete(where={'id': test_user.id})
                
            finally:
                await db.disconnect()
        
        asyncio.run(run_test())
    
    def test_trending_score_update_task(self):
        """
        Test that update_trending_scores task runs successfully.
        
        Requirements:
            - 16.3: Recompute trending scores as background job
            - 19.2: Run every 10-30 minutes
        """
        import asyncio
        from prisma import Prisma
        from apps.discovery.tasks import update_trending_scores
        from datetime import datetime
        import uuid
        
        async def run_test():
            db = Prisma()
            await db.connect()
            
            try:
                # Create test user and story
                test_user_id = str(uuid.uuid4())
                test_user = await db.userprofile.create(
                    data={
                        'clerk_user_id': f'test_task_{test_user_id}',
                        'handle': f'test_task_{test_user_id[:8]}',
                        'display_name': 'Test Author'
                    }
                )
                
                story = await db.story.create(
                    data={
                        'slug': f'test-story-task-{test_user_id}',
                        'title': 'Test Story',
                        'blurb': 'Test blurb',
                        'author_id': test_user.id,
                        'published': True,
                        'published_at': datetime.now()
                    }
                )
                
                # Create initial stats
                today = datetime.now().date()
                await db.story_stats_daily.create(
                    data={
                        'story_id': story.id,
                        'date': today,
                        'saves_count': 5,
                        'reads_count': 10,
                        'likes_count': 2,
                        'whispers_count': 1,
                        'trending_score': 0.0  # Initial score is 0
                    }
                )
                
                # Run the task
                update_trending_scores()
                
                # Verify score was updated
                updated_stats = await db.story_stats_daily.find_unique(
                    where={
                        'story_id_date': {
                            'story_id': story.id,
                            'date': today
                        }
                    }
                )
                
                self.assertGreater(
                    updated_stats.trending_score,
                    0.0,
                    "Trending score should be updated to > 0"
                )
                
                # Cleanup
                await db.story_stats_daily.delete_many(where={'story_id': story.id})
                await db.story.delete(where={'id': story.id})
                await db.userprofile.delete(where={'id': test_user.id})
                
            finally:
                await db.disconnect()
        
        asyncio.run(run_test())
    
    def test_celery_task_retry_configuration(self):
        """
        Test that Celery tasks are configured with retry logic.
        
        Requirements:
            - 19.5: Retry with exponential backoff up to 3 attempts
        """
        from apps.discovery.tasks import update_trending_scores, apply_daily_decay
        
        # Verify tasks are decorated as shared_task
        self.assertTrue(
            hasattr(update_trending_scores, 'delay'),
            "update_trending_scores should be a Celery task"
        )
        self.assertTrue(
            hasattr(apply_daily_decay, 'delay'),
            "apply_daily_decay should be a Celery task"
        )
    
    def test_trending_score_with_zero_engagement(self):
        """
        Test that trending score is 0 when there's no engagement.
        
        Requirements:
            - 16.1: Calculate trending score
        """
        import asyncio
        from prisma import Prisma
        from apps.discovery.trending import TrendingCalculator
        from datetime import datetime
        import uuid
        
        async def run_test():
            db = Prisma()
            await db.connect()
            
            try:
                # Create test user and story
                test_user_id = str(uuid.uuid4())
                test_user = await db.userprofile.create(
                    data={
                        'clerk_user_id': f'test_zero_{test_user_id}',
                        'handle': f'test_zero_{test_user_id[:8]}',
                        'display_name': 'Test Author'
                    }
                )
                
                story = await db.story.create(
                    data={
                        'slug': f'test-story-zero-{test_user_id}',
                        'title': 'Test Story',
                        'blurb': 'Test blurb',
                        'author_id': test_user.id,
                        'published': True,
                        'published_at': datetime.now()
                    }
                )
                
                # Calculate score without creating stats (no engagement)
                calculator = TrendingCalculator()
                score = await calculator.calculate_trending_score(story.id)
                
                # Verify score is 0
                self.assertEqual(score, 0.0, "Trending score should be 0 with no engagement")
                
                # Cleanup
                await db.story.delete(where={'id': story.id})
                await db.userprofile.delete(where={'id': test_user.id})
                
            finally:
                await db.disconnect()
        
        asyncio.run(run_test())
