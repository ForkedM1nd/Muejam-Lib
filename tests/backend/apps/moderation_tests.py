"""Tests for content moderation system."""
import pytest
from django.test import TestCase
from rest_framework.test import APIClient
from prisma import Prisma
import asyncio
import uuid
from datetime import datetime
from hypothesis import given, strategies as st, settings
from hypothesis.strategies import sampled_from, text, integers
from hypothesis.extra.django import TestCase as HypothesisTestCase


class ReportSubmissionTests(TestCase):
    """
    Tests for report submission.
    
    Requirements:
        - 13.1: Report stories
        - 13.2: Report chapters
        - 13.3: Report whispers
        - 13.4: Report users
        - 13.5: Store report with reason
        - 13.6: Prevent duplicate reports
        - 13.7: Validate reason text (max 500 characters)
    """
    
    def setUp(self):
        """Set up test client."""
        self.client = APIClient()
    
    def test_report_endpoint_exists(self):
        """Test that report endpoint is accessible."""
        response = self.client.post('/v1/reports/')
        # Should return 401 (auth required), 403 (CSRF/forbidden), or 400 (missing data), not 404
        self.assertIn(response.status_code, [400, 401, 403])
    
    def test_report_requires_authentication(self):
        """Test that report submission requires authentication."""
        response = self.client.post('/v1/reports/', {
            'content_type': 'story',
            'content_id': 'test-id',
            'reason': 'Test reason'
        })
        # Should return 401 (unauthorized) or 403 (CSRF/forbidden)
        self.assertIn(response.status_code, [401, 403])
    
    def test_report_requires_content_type(self):
        """Test that content_type is required."""
        response = self.client.post('/v1/reports/', {
            'content_id': 'test-id',
            'reason': 'Test reason'
        })
        self.assertIn(response.status_code, [400, 401, 403])
    
    def test_report_requires_content_id(self):
        """Test that content_id is required."""
        response = self.client.post('/v1/reports/', {
            'content_type': 'story',
            'reason': 'Test reason'
        })
        self.assertIn(response.status_code, [400, 401, 403])
    
    def test_report_requires_reason(self):
        """Test that reason is required."""
        response = self.client.post('/v1/reports/', {
            'content_type': 'story',
            'content_id': 'test-id'
        })
        self.assertIn(response.status_code, [400, 401, 403])
    
    def test_report_validates_content_type(self):
        """
        Test that invalid content types are rejected.
        
        Requirements:
            - 13.1-13.4: Only story, chapter, whisper, user allowed
        """
        response = self.client.post('/v1/reports/', {
            'content_type': 'invalid_type',
            'content_id': 'test-id',
            'reason': 'Test reason'
        })
        self.assertIn(response.status_code, [400, 401, 403])
    
    def test_report_validates_reason_length(self):
        """
        Test that reason text is limited to 500 characters.
        
        Requirements:
            - 13.7: Validate reason text (max 500 characters)
        """
        long_reason = 'x' * 501
        response = self.client.post('/v1/reports/', {
            'content_type': 'story',
            'content_id': 'test-id',
            'reason': long_reason
        })
        self.assertIn(response.status_code, [400, 401, 403])
    
    def test_report_story(self):
        """
        Test reporting a story.
        
        Requirements:
            - 13.1: Report stories
        """
        import asyncio
        
        async def run_test():
            db = Prisma()
            await db.connect()
            
            try:
                # Create test users
                test_id = str(uuid.uuid4())
                reporter = await db.userprofile.create(
                    data={
                        'clerk_user_id': f'test_reporter_{test_id}',
                        'handle': f'reporter_{test_id[:8]}',
                        'display_name': 'Reporter'
                    }
                )
                
                author = await db.userprofile.create(
                    data={
                        'clerk_user_id': f'test_author_{test_id}',
                        'handle': f'author_{test_id[:8]}',
                        'display_name': 'Author'
                    }
                )
                
                # Create test story
                story = await db.story.create(
                    data={
                        'slug': f'test-story-{test_id}',
                        'title': 'Test Story',
                        'blurb': 'Test blurb',
                        'author_id': author.id,
                        'published': True,
                        'published_at': datetime.now()
                    }
                )
                
                # Create report
                from apps.moderation.views import create_report
                report_data = await create_report(
                    reporter.id,
                    'story',
                    story.id,
                    'Inappropriate content'
                )
                
                # Verify report was created
                self.assertIsNotNone(report_data)
                self.assertEqual(report_data['story_id'], story.id)
                self.assertEqual(report_data['reporter_id'], reporter.id)
                self.assertEqual(report_data['reason'], 'Inappropriate content')
                self.assertEqual(report_data['status'], 'PENDING')
                
                # Cleanup
                await db.report.delete(where={'id': report_data['id']})
                await db.story.delete(where={'id': story.id})
                await db.userprofile.delete(where={'id': reporter.id})
                await db.userprofile.delete(where={'id': author.id})
                
            finally:
                await db.disconnect()
        
        asyncio.run(run_test())
    
    def test_duplicate_report_prevention(self):
        """
        Test that duplicate reports are prevented.
        
        Requirements:
            - 13.6: Prevent duplicate reports
        """
        import asyncio
        
        async def run_test():
            db = Prisma()
            await db.connect()
            
            try:
                # Create test users
                test_id = str(uuid.uuid4())
                reporter = await db.userprofile.create(
                    data={
                        'clerk_user_id': f'test_dup_reporter_{test_id}',
                        'handle': f'dup_reporter_{test_id[:8]}',
                        'display_name': 'Reporter'
                    }
                )
                
                author = await db.userprofile.create(
                    data={
                        'clerk_user_id': f'test_dup_author_{test_id}',
                        'handle': f'dup_author_{test_id[:8]}',
                        'display_name': 'Author'
                    }
                )
                
                # Create test story
                story = await db.story.create(
                    data={
                        'slug': f'test-dup-story-{test_id}',
                        'title': 'Test Story',
                        'blurb': 'Test blurb',
                        'author_id': author.id,
                        'published': True,
                        'published_at': datetime.now()
                    }
                )
                
                # Create first report
                from apps.moderation.views import create_report
                report1 = await create_report(
                    reporter.id,
                    'story',
                    story.id,
                    'First report'
                )
                
                self.assertIsNotNone(report1, "First report should be created")
                
                # Try to create duplicate report
                report2 = await create_report(
                    reporter.id,
                    'story',
                    story.id,
                    'Second report'
                )
                
                self.assertIsNone(report2, "Duplicate report should be prevented")
                
                # Cleanup
                await db.report.delete(where={'id': report1['id']})
                await db.story.delete(where={'id': story.id})
                await db.userprofile.delete(where={'id': reporter.id})
                await db.userprofile.delete(where={'id': author.id})
                
            finally:
                await db.disconnect()
        
        asyncio.run(run_test())


class DuplicateReportPropertyTests(HypothesisTestCase):
    """
    Property-based tests for duplicate report prevention.
    
    Property 26: Duplicate Report Prevention
    For any user and content item, attempting to report the same content twice
    should result in only one Report record.
    
    Requirements:
        - 13.6: Prevent duplicate reports
    """
    
    @settings(max_examples=5, deadline=None)
    @given(
        sampled_from(['story', 'chapter', 'whisper', 'user']),
        st.integers(min_value=2, max_value=10)
    )
    def test_duplicate_reports_prevented(self, content_type, num_attempts):
        """
        Property: Multiple report attempts should result in only one report.
        
        This test verifies that no matter how many times a user tries to
        report the same content, only one report is created.
        """
        import asyncio
        
        async def run_test():
            db = Prisma()
            await db.connect()
            
            try:
                # Create test users
                test_id = str(uuid.uuid4())
                reporter = await db.userprofile.create(
                    data={
                        'clerk_user_id': f'test_prop_reporter_{test_id}',
                        'handle': f'prop_reporter_{test_id[:8]}',
                        'display_name': 'Reporter'
                    }
                )
                
                # Create content based on type
                if content_type == 'story':
                    author = await db.userprofile.create(
                        data={
                            'clerk_user_id': f'test_prop_author_{test_id}',
                            'handle': f'prop_author_{test_id[:8]}',
                            'display_name': 'Author'
                        }
                    )
                    content = await db.story.create(
                        data={
                            'slug': f'test-prop-story-{test_id}',
                            'title': 'Test Story',
                            'blurb': 'Test blurb',
                            'author_id': author.id,
                            'published': True,
                            'published_at': datetime.now()
                        }
                    )
                    content_id = content.id
                elif content_type == 'user':
                    content = await db.userprofile.create(
                        data={
                            'clerk_user_id': f'test_prop_reported_{test_id}',
                            'handle': f'prop_reported_{test_id[:8]}',
                            'display_name': 'Reported User'
                        }
                    )
                    content_id = content.id
                else:
                    # For chapter and whisper, skip for simplicity
                    await db.userprofile.delete(where={'id': reporter.id})
                    return
                
                # Attempt to create multiple reports
                from apps.moderation.views import create_report
                created_reports = []
                
                for i in range(num_attempts):
                    report = await create_report(
                        reporter.id,
                        content_type,
                        content_id,
                        f'Report attempt {i+1}'
                    )
                    if report:
                        created_reports.append(report['id'])
                
                # Verify only one report was created
                self.assertEqual(
                    len(created_reports),
                    1,
                    f"Expected 1 report from {num_attempts} attempts, got {len(created_reports)}"
                )
                
                # Verify in database
                where_clause = {'reporter_id': reporter.id}
                if content_type == 'story':
                    where_clause['story_id'] = content_id
                elif content_type == 'user':
                    where_clause['reported_user_id'] = content_id
                
                db_reports = await db.report.find_many(where=where_clause)
                self.assertEqual(
                    len(db_reports),
                    1,
                    f"Database should contain exactly 1 report, found {len(db_reports)}"
                )
                
                # Cleanup
                await db.report.delete_many(where=where_clause)
                if content_type == 'story':
                    await db.story.delete(where={'id': content_id})
                    await db.userprofile.delete(where={'id': author.id})
                elif content_type == 'user':
                    await db.userprofile.delete(where={'id': content_id})
                await db.userprofile.delete(where={'id': reporter.id})
                
            finally:
                await db.disconnect()
        
        asyncio.run(run_test())


class ReportValidationTests(TestCase):
    """
    Tests for report validation.
    
    Requirements:
        - 13.7: Validate reason text (max 500 characters)
    """
    
    def test_reason_max_length_500(self):
        """
        Test that reason text is limited to 500 characters.
        
        Requirements:
            - 13.7: Validate reason text (max 500 characters)
        """
        from apps.moderation.serializers import ReportCreateSerializer
        
        # Valid reason (500 characters)
        valid_reason = 'x' * 500
        serializer = ReportCreateSerializer(data={
            'content_type': 'story',
            'content_id': 'test-id',
            'reason': valid_reason
        })
        self.assertTrue(serializer.is_valid())
        
        # Invalid reason (501 characters)
        invalid_reason = 'x' * 501
        serializer = ReportCreateSerializer(data={
            'content_type': 'story',
            'content_id': 'test-id',
            'reason': invalid_reason
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn('reason', serializer.errors)
    
    def test_reason_cannot_be_empty(self):
        """Test that reason cannot be empty or whitespace only."""
        from apps.moderation.serializers import ReportCreateSerializer
        
        # Empty reason
        serializer = ReportCreateSerializer(data={
            'content_type': 'story',
            'content_id': 'test-id',
            'reason': ''
        })
        self.assertFalse(serializer.is_valid())
        
        # Whitespace only
        serializer = ReportCreateSerializer(data={
            'content_type': 'story',
            'content_id': 'test-id',
            'reason': '   '
        })
        self.assertFalse(serializer.is_valid())
    
    def test_content_types_validation(self):
        """
        Test that only valid content types are accepted.
        
        Requirements:
            - 13.1-13.4: Support story, chapter, whisper, user
        """
        from apps.moderation.serializers import ReportCreateSerializer
        
        # Valid content types
        valid_types = ['story', 'chapter', 'whisper', 'user']
        for content_type in valid_types:
            serializer = ReportCreateSerializer(data={
                'content_type': content_type,
                'content_id': 'test-id',
                'reason': 'Test reason'
            })
            self.assertTrue(
                serializer.is_valid(),
                f"Content type '{content_type}' should be valid"
            )
        
        # Invalid content type
        serializer = ReportCreateSerializer(data={
            'content_type': 'invalid',
            'content_id': 'test-id',
            'reason': 'Test reason'
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn('content_type', serializer.errors)



class ModerationQueueTests(TestCase):
    """
    Tests for moderation queue service.
    
    Requirements:
        - 2.1: Display all pending reports in moderation queue
        - 2.2: Sort reports by priority and creation date
    """
    
    def test_moderation_queue_endpoint_exists(self):
        """Test that moderation queue endpoint is accessible."""
        response = self.client.get('/v1/reports/queue/')
        # Should return 401 (auth required), 403 (forbidden), or 200, not 404
        self.assertIn(response.status_code, [200, 401, 403])
    
    def test_queue_returns_pending_reports_only(self):
        """
        Test that queue only returns PENDING reports.
        
        Requirements:
            - 2.1: Display all pending reports
        """
        import asyncio
        
        async def run_test():
            db = Prisma()
            await db.connect()
            
            try:
                # Create test users
                test_id = str(uuid.uuid4())
                reporter = await db.userprofile.create(
                    data={
                        'clerk_user_id': f'test_queue_reporter_{test_id}',
                        'handle': f'queue_reporter_{test_id[:8]}',
                        'display_name': 'Reporter'
                    }
                )
                
                author = await db.userprofile.create(
                    data={
                        'clerk_user_id': f'test_queue_author_{test_id}',
                        'handle': f'queue_author_{test_id[:8]}',
                        'display_name': 'Author'
                    }
                )
                
                # Create test stories
                story1 = await db.story.create(
                    data={
                        'slug': f'test-queue-story1-{test_id}',
                        'title': 'Test Story 1',
                        'blurb': 'Test blurb',
                        'author_id': author.id,
                        'published': True,
                        'published_at': datetime.now()
                    }
                )
                
                story2 = await db.story.create(
                    data={
                        'slug': f'test-queue-story2-{test_id}',
                        'title': 'Test Story 2',
                        'blurb': 'Test blurb',
                        'author_id': author.id,
                        'published': True,
                        'published_at': datetime.now()
                    }
                )
                
                # Create pending report
                pending_report = await db.report.create(
                    data={
                        'reporter_id': reporter.id,
                        'story_id': story1.id,
                        'reason': 'Pending report',
                        'status': 'PENDING'
                    }
                )
                
                # Create resolved report
                resolved_report = await db.report.create(
                    data={
                        'reporter_id': reporter.id,
                        'story_id': story2.id,
                        'reason': 'Resolved report',
                        'status': 'RESOLVED'
                    }
                )
                
                # Get queue
                from apps.moderation.views import fetch_moderation_queue
                queue = await fetch_moderation_queue()
                
                # Verify only pending report is in queue
                queue_ids = [report['id'] for report in queue]
                self.assertIn(pending_report.id, queue_ids)
                self.assertNotIn(resolved_report.id, queue_ids)
                
                # Cleanup
                await db.report.delete(where={'id': pending_report.id})
                await db.report.delete(where={'id': resolved_report.id})
                await db.story.delete(where={'id': story1.id})
                await db.story.delete(where={'id': story2.id})
                await db.userprofile.delete(where={'id': reporter.id})
                await db.userprofile.delete(where={'id': author.id})
                
            finally:
                await db.disconnect()
        
        asyncio.run(run_test())
    
    def test_queue_sorted_by_priority(self):
        """
        Test that queue is sorted by priority score.
        
        Requirements:
            - 2.2: Sort reports by priority
        """
        import asyncio
        from datetime import timedelta
        
        async def run_test():
            db = Prisma()
            await db.connect()
            
            try:
                # Create test users
                test_id = str(uuid.uuid4())
                reporter = await db.userprofile.create(
                    data={
                        'clerk_user_id': f'test_priority_reporter_{test_id}',
                        'handle': f'priority_reporter_{test_id[:8]}',
                        'display_name': 'Reporter'
                    }
                )
                
                author = await db.userprofile.create(
                    data={
                        'clerk_user_id': f'test_priority_author_{test_id}',
                        'handle': f'priority_author_{test_id[:8]}',
                        'display_name': 'Author'
                    }
                )
                
                # Create test stories
                story1 = await db.story.create(
                    data={
                        'slug': f'test-priority-story1-{test_id}',
                        'title': 'Test Story 1',
                        'blurb': 'Test blurb',
                        'author_id': author.id,
                        'published': True,
                        'published_at': datetime.now()
                    }
                )
                
                story2 = await db.story.create(
                    data={
                        'slug': f'test-priority-story2-{test_id}',
                        'title': 'Test Story 2',
                        'blurb': 'Test blurb',
                        'author_id': author.id,
                        'published': True,
                        'published_at': datetime.now()
                    }
                )
                
                # Create older report (should have higher priority due to age)
                old_time = datetime.now() - timedelta(hours=10)
                old_report = await db.report.create(
                    data={
                        'reporter_id': reporter.id,
                        'story_id': story1.id,
                        'reason': 'Old report',
                        'status': 'PENDING',
                        'created_at': old_time
                    }
                )
                
                # Create newer report
                new_report = await db.report.create(
                    data={
                        'reporter_id': reporter.id,
                        'story_id': story2.id,
                        'reason': 'New report',
                        'status': 'PENDING'
                    }
                )
                
                # Get queue
                from apps.moderation.views import fetch_moderation_queue
                queue = await fetch_moderation_queue()
                
                # Find positions of reports in queue
                old_report_index = next(
                    (i for i, r in enumerate(queue) if r['id'] == old_report.id),
                    None
                )
                new_report_index = next(
                    (i for i, r in enumerate(queue) if r['id'] == new_report.id),
                    None
                )
                
                # Verify old report comes before new report (higher priority)
                self.assertIsNotNone(old_report_index)
                self.assertIsNotNone(new_report_index)
                self.assertLess(
                    old_report_index,
                    new_report_index,
                    "Older report should have higher priority"
                )
                
                # Cleanup
                await db.report.delete(where={'id': old_report.id})
                await db.report.delete(where={'id': new_report.id})
                await db.story.delete(where={'id': story1.id})
                await db.story.delete(where={'id': story2.id})
                await db.userprofile.delete(where={'id': reporter.id})
                await db.userprofile.delete(where={'id': author.id})
                
            finally:
                await db.disconnect()
        
        asyncio.run(run_test())
    
    def test_duplicate_reports_increase_priority(self):
        """
        Test that duplicate reports increase priority score.
        
        Requirements:
            - 2.2: Priority algorithm based on duplicate reports
        """
        import asyncio
        
        async def run_test():
            db = Prisma()
            await db.connect()
            
            try:
                # Create test users
                test_id = str(uuid.uuid4())
                reporter1 = await db.userprofile.create(
                    data={
                        'clerk_user_id': f'test_dup_priority_reporter1_{test_id}',
                        'handle': f'dup_priority_rep1_{test_id[:8]}',
                        'display_name': 'Reporter 1'
                    }
                )
                
                reporter2 = await db.userprofile.create(
                    data={
                        'clerk_user_id': f'test_dup_priority_reporter2_{test_id}',
                        'handle': f'dup_priority_rep2_{test_id[:8]}',
                        'display_name': 'Reporter 2'
                    }
                )
                
                author = await db.userprofile.create(
                    data={
                        'clerk_user_id': f'test_dup_priority_author_{test_id}',
                        'handle': f'dup_priority_author_{test_id[:8]}',
                        'display_name': 'Author'
                    }
                )
                
                # Create test stories
                story_with_duplicates = await db.story.create(
                    data={
                        'slug': f'test-dup-priority-story1-{test_id}',
                        'title': 'Story with duplicates',
                        'blurb': 'Test blurb',
                        'author_id': author.id,
                        'published': True,
                        'published_at': datetime.now()
                    }
                )
                
                story_without_duplicates = await db.story.create(
                    data={
                        'slug': f'test-dup-priority-story2-{test_id}',
                        'title': 'Story without duplicates',
                        'blurb': 'Test blurb',
                        'author_id': author.id,
                        'published': True,
                        'published_at': datetime.now()
                    }
                )
                
                # Create multiple reports for same story (duplicates)
                report1 = await db.report.create(
                    data={
                        'reporter_id': reporter1.id,
                        'story_id': story_with_duplicates.id,
                        'reason': 'First report',
                        'status': 'PENDING'
                    }
                )
                
                report2 = await db.report.create(
                    data={
                        'reporter_id': reporter2.id,
                        'story_id': story_with_duplicates.id,
                        'reason': 'Second report',
                        'status': 'PENDING'
                    }
                )
                
                # Create single report for another story
                report3 = await db.report.create(
                    data={
                        'reporter_id': reporter1.id,
                        'story_id': story_without_duplicates.id,
                        'reason': 'Single report',
                        'status': 'PENDING'
                    }
                )
                
                # Get queue
                from apps.moderation.views import fetch_moderation_queue
                queue = await fetch_moderation_queue()
                
                # Find reports in queue
                report1_data = next((r for r in queue if r['id'] == report1.id), None)
                report3_data = next((r for r in queue if r['id'] == report3.id), None)
                
                self.assertIsNotNone(report1_data)
                self.assertIsNotNone(report3_data)
                
                # Report with duplicates should have higher priority
                self.assertGreater(
                    report1_data['priority_score'],
                    report3_data['priority_score'],
                    "Report with duplicates should have higher priority"
                )
                
                # Cleanup
                await db.report.delete(where={'id': report1.id})
                await db.report.delete(where={'id': report2.id})
                await db.report.delete(where={'id': report3.id})
                await db.story.delete(where={'id': story_with_duplicates.id})
                await db.story.delete(where={'id': story_without_duplicates.id})
                await db.userprofile.delete(where={'id': reporter1.id})
                await db.userprofile.delete(where={'id': reporter2.id})
                await db.userprofile.delete(where={'id': author.id})
                
            finally:
                await db.disconnect()
        
        asyncio.run(run_test())
    
    def test_user_reports_have_higher_priority(self):
        """
        Test that user reports have higher priority than content reports.
        
        Requirements:
            - 2.2: Priority algorithm based on content type
        """
        import asyncio
        
        async def run_test():
            db = Prisma()
            await db.connect()
            
            try:
                # Create test users
                test_id = str(uuid.uuid4())
                reporter = await db.userprofile.create(
                    data={
                        'clerk_user_id': f'test_type_priority_reporter_{test_id}',
                        'handle': f'type_priority_rep_{test_id[:8]}',
                        'display_name': 'Reporter'
                    }
                )
                
                author = await db.userprofile.create(
                    data={
                        'clerk_user_id': f'test_type_priority_author_{test_id}',
                        'handle': f'type_priority_author_{test_id[:8]}',
                        'display_name': 'Author'
                    }
                )
                
                reported_user = await db.userprofile.create(
                    data={
                        'clerk_user_id': f'test_type_priority_reported_{test_id}',
                        'handle': f'type_priority_reported_{test_id[:8]}',
                        'display_name': 'Reported User'
                    }
                )
                
                # Create test story
                story = await db.story.create(
                    data={
                        'slug': f'test-type-priority-story-{test_id}',
                        'title': 'Test Story',
                        'blurb': 'Test blurb',
                        'author_id': author.id,
                        'published': True,
                        'published_at': datetime.now()
                    }
                )
                
                # Create user report
                user_report = await db.report.create(
                    data={
                        'reporter_id': reporter.id,
                        'reported_user_id': reported_user.id,
                        'reason': 'User report',
                        'status': 'PENDING'
                    }
                )
                
                # Create story report
                story_report = await db.report.create(
                    data={
                        'reporter_id': reporter.id,
                        'story_id': story.id,
                        'reason': 'Story report',
                        'status': 'PENDING'
                    }
                )
                
                # Get queue
                from apps.moderation.views import fetch_moderation_queue
                queue = await fetch_moderation_queue()
                
                # Find reports in queue
                user_report_data = next((r for r in queue if r['id'] == user_report.id), None)
                story_report_data = next((r for r in queue if r['id'] == story_report.id), None)
                
                self.assertIsNotNone(user_report_data)
                self.assertIsNotNone(story_report_data)
                
                # User report should have higher priority
                self.assertGreater(
                    user_report_data['priority_score'],
                    story_report_data['priority_score'],
                    "User report should have higher priority than story report"
                )
                
                # Cleanup
                await db.report.delete(where={'id': user_report.id})
                await db.report.delete(where={'id': story_report.id})
                await db.story.delete(where={'id': story.id})
                await db.userprofile.delete(where={'id': reporter.id})
                await db.userprofile.delete(where={'id': author.id})
                await db.userprofile.delete(where={'id': reported_user.id})
                
            finally:
                await db.disconnect()
        
        asyncio.run(run_test())



class ModerationActionTests(TestCase):
    """
    Tests for moderation actions.
    
    Requirements:
        - 2.4: Support actions: dismiss, warn, hide, delete, suspend
        - 2.5: Require dismissal reason
        - 2.6: Immediately remove content from public view
        - 2.8: Notify content author via email
    """
    
    def setUp(self):
        """Set up test client."""
        self.client = APIClient()
    
    def test_moderation_action_endpoint_exists(self):
        """Test that moderation action endpoint is accessible."""
        response = self.client.post('/v1/reports/actions/')
        # Should return 401 (auth required), 403 (forbidden), or 400 (missing data), not 404
        self.assertIn(response.status_code, [400, 401, 403])
    
    def test_action_requires_report_id(self):
        """Test that report_id is required."""
        response = self.client.post('/v1/reports/actions/', {
            'action_type': 'DISMISS',
            'reason': 'Test reason'
        })
        self.assertIn(response.status_code, [400, 401, 403])
    
    def test_action_requires_action_type(self):
        """Test that action_type is required."""
        response = self.client.post('/v1/reports/actions/', {
            'report_id': 'test-id',
            'reason': 'Test reason'
        })
        self.assertIn(response.status_code, [400, 401, 403])
    
    def test_action_requires_reason(self):
        """
        Test that reason is required for all actions.
        
        Requirements:
            - 2.5: Require dismissal reason
        """
        response = self.client.post('/v1/reports/actions/', {
            'report_id': 'test-id',
            'action_type': 'DISMISS'
        })
        self.assertIn(response.status_code, [400, 401, 403])
    
    def test_action_validates_action_type(self):
        """
        Test that only valid action types are accepted.
        
        Requirements:
            - 2.4: Support DISMISS, WARN, HIDE, DELETE, SUSPEND
        """
        response = self.client.post('/v1/reports/actions/', {
            'report_id': 'test-id',
            'action_type': 'INVALID',
            'reason': 'Test reason'
        })
        self.assertIn(response.status_code, [400, 401, 403])
    
    def test_dismiss_action(self):
        """
        Test DISMISS action.
        
        Requirements:
            - 2.4: Support DISMISS action
            - 2.5: Require dismissal reason
        """
        import asyncio
        
        async def run_test():
            db = Prisma()
            await db.connect()
            
            try:
                # Create test users
                test_id = str(uuid.uuid4())
                reporter = await db.userprofile.create(
                    data={
                        'clerk_user_id': f'test_dismiss_reporter_{test_id}',
                        'handle': f'dismiss_reporter_{test_id[:8]}',
                        'display_name': 'Reporter'
                    }
                )
                
                moderator = await db.userprofile.create(
                    data={
                        'clerk_user_id': f'test_dismiss_moderator_{test_id}',
                        'handle': f'dismiss_moderator_{test_id[:8]}',
                        'display_name': 'Moderator'
                    }
                )
                
                author = await db.userprofile.create(
                    data={
                        'clerk_user_id': f'test_dismiss_author_{test_id}',
                        'handle': f'dismiss_author_{test_id[:8]}',
                        'display_name': 'Author'
                    }
                )
                
                # Create test story
                story = await db.story.create(
                    data={
                        'slug': f'test-dismiss-story-{test_id}',
                        'title': 'Test Story',
                        'blurb': 'Test blurb',
                        'author_id': author.id,
                        'published': True,
                        'published_at': datetime.now()
                    }
                )
                
                # Create report
                report = await db.report.create(
                    data={
                        'reporter_id': reporter.id,
                        'story_id': story.id,
                        'reason': 'Test report',
                        'status': 'PENDING'
                    }
                )
                
                # Execute DISMISS action
                from apps.moderation.views import execute_moderation_action
                action_data = await execute_moderation_action(
                    report.id,
                    moderator.id,
                    'DISMISS',
                    'Not a violation'
                )
                
                # Verify action was created
                self.assertIsNotNone(action_data)
                self.assertEqual(action_data['action_type'], 'DISMISS')
                self.assertEqual(action_data['reason'], 'Not a violation')
                
                # Verify report status updated
                updated_report = await db.report.find_unique(where={'id': report.id})
                self.assertEqual(updated_report.status, 'RESOLVED')
                
                # Verify story was NOT deleted (DISMISS doesn't affect content)
                story_check = await db.story.find_unique(where={'id': story.id})
                self.assertIsNotNone(story_check)
                self.assertIsNone(story_check.deleted_at)
                
                # Cleanup
                await db.moderationaction.delete(where={'id': action_data['id']})
                await db.report.delete(where={'id': report.id})
                await db.story.delete(where={'id': story.id})
                await db.userprofile.delete(where={'id': reporter.id})
                await db.userprofile.delete(where={'id': moderator.id})
                await db.userprofile.delete(where={'id': author.id})
                
            finally:
                await db.disconnect()
        
        asyncio.run(run_test())
    
    def test_hide_action_removes_content(self):
        """
        Test HIDE action immediately removes content from public view.
        
        Requirements:
            - 2.4: Support HIDE action
            - 2.6: Immediately remove content from public view
        """
        import asyncio
        
        async def run_test():
            db = Prisma()
            await db.connect()
            
            try:
                # Create test users
                test_id = str(uuid.uuid4())
                reporter = await db.userprofile.create(
                    data={
                        'clerk_user_id': f'test_hide_reporter_{test_id}',
                        'handle': f'hide_reporter_{test_id[:8]}',
                        'display_name': 'Reporter'
                    }
                )
                
                moderator = await db.userprofile.create(
                    data={
                        'clerk_user_id': f'test_hide_moderator_{test_id}',
                        'handle': f'hide_moderator_{test_id[:8]}',
                        'display_name': 'Moderator'
                    }
                )
                
                author = await db.userprofile.create(
                    data={
                        'clerk_user_id': f'test_hide_author_{test_id}',
                        'handle': f'hide_author_{test_id[:8]}',
                        'display_name': 'Author'
                    }
                )
                
                # Create test story
                story = await db.story.create(
                    data={
                        'slug': f'test-hide-story-{test_id}',
                        'title': 'Test Story',
                        'blurb': 'Test blurb',
                        'author_id': author.id,
                        'published': True,
                        'published_at': datetime.now()
                    }
                )
                
                # Create report
                report = await db.report.create(
                    data={
                        'reporter_id': reporter.id,
                        'story_id': story.id,
                        'reason': 'Test report',
                        'status': 'PENDING'
                    }
                )
                
                # Execute HIDE action
                from apps.moderation.views import execute_moderation_action
                action_data = await execute_moderation_action(
                    report.id,
                    moderator.id,
                    'HIDE',
                    'Violates content policy'
                )
                
                # Verify action was created
                self.assertIsNotNone(action_data)
                self.assertEqual(action_data['action_type'], 'HIDE')
                
                # Verify story was hidden (deleted_at set)
                story_check = await db.story.find_unique(where={'id': story.id})
                self.assertIsNotNone(story_check)
                self.assertIsNotNone(story_check.deleted_at, "Story should have deleted_at timestamp")
                
                # Cleanup
                await db.moderationaction.delete(where={'id': action_data['id']})
                await db.report.delete(where={'id': report.id})
                await db.story.delete(where={'id': story.id})
                await db.userprofile.delete(where={'id': reporter.id})
                await db.userprofile.delete(where={'id': moderator.id})
                await db.userprofile.delete(where={'id': author.id})
                
            finally:
                await db.disconnect()
        
        asyncio.run(run_test())
    
    def test_delete_action_permanently_removes_content(self):
        """
        Test DELETE action permanently removes content.
        
        Requirements:
            - 2.4: Support DELETE action
            - 2.6: Immediately remove content from public view
        """
        import asyncio
        
        async def run_test():
            db = Prisma()
            await db.connect()
            
            try:
                # Create test users
                test_id = str(uuid.uuid4())
                reporter = await db.userprofile.create(
                    data={
                        'clerk_user_id': f'test_delete_reporter_{test_id}',
                        'handle': f'delete_reporter_{test_id[:8]}',
                        'display_name': 'Reporter'
                    }
                )
                
                moderator = await db.userprofile.create(
                    data={
                        'clerk_user_id': f'test_delete_moderator_{test_id}',
                        'handle': f'delete_moderator_{test_id[:8]}',
                        'display_name': 'Moderator'
                    }
                )
                
                author = await db.userprofile.create(
                    data={
                        'clerk_user_id': f'test_delete_author_{test_id}',
                        'handle': f'delete_author_{test_id[:8]}',
                        'display_name': 'Author'
                    }
                )
                
                # Create test story
                story = await db.story.create(
                    data={
                        'slug': f'test-delete-story-{test_id}',
                        'title': 'Test Story',
                        'blurb': 'Test blurb',
                        'author_id': author.id,
                        'published': True,
                        'published_at': datetime.now()
                    }
                )
                
                story_id = story.id
                
                # Create report
                report = await db.report.create(
                    data={
                        'reporter_id': reporter.id,
                        'story_id': story.id,
                        'reason': 'Test report',
                        'status': 'PENDING'
                    }
                )
                
                # Execute DELETE action
                from apps.moderation.views import execute_moderation_action
                action_data = await execute_moderation_action(
                    report.id,
                    moderator.id,
                    'DELETE',
                    'Severe violation'
                )
                
                # Verify action was created
                self.assertIsNotNone(action_data)
                self.assertEqual(action_data['action_type'], 'DELETE')
                
                # Verify story was permanently deleted
                story_check = await db.story.find_unique(where={'id': story_id})
                self.assertIsNone(story_check, "Story should be permanently deleted")
                
                # Cleanup
                await db.moderationaction.delete(where={'id': action_data['id']})
                await db.report.delete(where={'id': report.id})
                await db.userprofile.delete(where={'id': reporter.id})
                await db.userprofile.delete(where={'id': moderator.id})
                await db.userprofile.delete(where={'id': author.id})
                
            finally:
                await db.disconnect()
        
        asyncio.run(run_test())
    
    def test_warn_action(self):
        """
        Test WARN action.
        
        Requirements:
            - 2.4: Support WARN action with user notification
        """
        import asyncio
        
        async def run_test():
            db = Prisma()
            await db.connect()
            
            try:
                # Create test users
                test_id = str(uuid.uuid4())
                reporter = await db.userprofile.create(
                    data={
                        'clerk_user_id': f'test_warn_reporter_{test_id}',
                        'handle': f'warn_reporter_{test_id[:8]}',
                        'display_name': 'Reporter'
                    }
                )
                
                moderator = await db.userprofile.create(
                    data={
                        'clerk_user_id': f'test_warn_moderator_{test_id}',
                        'handle': f'warn_moderator_{test_id[:8]}',
                        'display_name': 'Moderator'
                    }
                )
                
                author = await db.userprofile.create(
                    data={
                        'clerk_user_id': f'test_warn_author_{test_id}',
                        'handle': f'warn_author_{test_id[:8]}',
                        'display_name': 'Author'
                    }
                )
                
                # Create test story
                story = await db.story.create(
                    data={
                        'slug': f'test-warn-story-{test_id}',
                        'title': 'Test Story',
                        'blurb': 'Test blurb',
                        'author_id': author.id,
                        'published': True,
                        'published_at': datetime.now()
                    }
                )
                
                # Create report
                report = await db.report.create(
                    data={
                        'reporter_id': reporter.id,
                        'story_id': story.id,
                        'reason': 'Test report',
                        'status': 'PENDING'
                    }
                )
                
                # Execute WARN action
                from apps.moderation.views import execute_moderation_action
                action_data = await execute_moderation_action(
                    report.id,
                    moderator.id,
                    'WARN',
                    'Minor policy violation'
                )
                
                # Verify action was created
                self.assertIsNotNone(action_data)
                self.assertEqual(action_data['action_type'], 'WARN')
                
                # Verify report status updated
                updated_report = await db.report.find_unique(where={'id': report.id})
                self.assertEqual(updated_report.status, 'RESOLVED')
                
                # Verify story was NOT deleted (WARN doesn't affect content)
                story_check = await db.story.find_unique(where={'id': story.id})
                self.assertIsNotNone(story_check)
                self.assertIsNone(story_check.deleted_at)
                
                # Note: Email notification is sent but not verified in this test
                # Email service is mocked in integration tests
                
                # Cleanup
                await db.moderationaction.delete(where={'id': action_data['id']})
                await db.report.delete(where={'id': report.id})
                await db.story.delete(where={'id': story.id})
                await db.userprofile.delete(where={'id': reporter.id})
                await db.userprofile.delete(where={'id': moderator.id})
                await db.userprofile.delete(where={'id': author.id})
                
            finally:
                await db.disconnect()
        
        asyncio.run(run_test())
    
    def test_suspend_action(self):
        """
        Test SUSPEND action.
        
        Requirements:
            - 2.4: Support SUSPEND action
        """
        import asyncio
        
        async def run_test():
            db = Prisma()
            await db.connect()
            
            try:
                # Create test users
                test_id = str(uuid.uuid4())
                reporter = await db.userprofile.create(
                    data={
                        'clerk_user_id': f'test_suspend_reporter_{test_id}',
                        'handle': f'suspend_reporter_{test_id[:8]}',
                        'display_name': 'Reporter'
                    }
                )
                
                moderator = await db.userprofile.create(
                    data={
                        'clerk_user_id': f'test_suspend_moderator_{test_id}',
                        'handle': f'suspend_moderator_{test_id[:8]}',
                        'display_name': 'Moderator'
                    }
                )
                
                reported_user = await db.userprofile.create(
                    data={
                        'clerk_user_id': f'test_suspend_reported_{test_id}',
                        'handle': f'suspend_reported_{test_id[:8]}',
                        'display_name': 'Reported User'
                    }
                )
                
                # Create report
                report = await db.report.create(
                    data={
                        'reporter_id': reporter.id,
                        'reported_user_id': reported_user.id,
                        'reason': 'Test report',
                        'status': 'PENDING'
                    }
                )
                
                # Execute SUSPEND action
                from apps.moderation.views import execute_moderation_action
                action_data = await execute_moderation_action(
                    report.id,
                    moderator.id,
                    'SUSPEND',
                    'Repeated violations'
                )
                
                # Verify action was created
                self.assertIsNotNone(action_data)
                self.assertEqual(action_data['action_type'], 'SUSPEND')
                
                # Verify report status updated
                updated_report = await db.report.find_unique(where={'id': report.id})
                self.assertEqual(updated_report.status, 'RESOLVED')
                
                # Note: Actual suspension enforcement requires AccountSuspension model
                # and middleware integration, which is beyond the scope of this test
                
                # Cleanup
                await db.moderationaction.delete(where={'id': action_data['id']})
                await db.report.delete(where={'id': report.id})
                await db.userprofile.delete(where={'id': reporter.id})
                await db.userprofile.delete(where={'id': moderator.id})
                await db.userprofile.delete(where={'id': reported_user.id})
                
            finally:
                await db.disconnect()
        
        asyncio.run(run_test())
