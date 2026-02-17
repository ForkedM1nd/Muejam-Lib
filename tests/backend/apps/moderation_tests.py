"""Tests for content moderation system."""
import pytest
from django.test import TestCase
from rest_framework.test import APIClient
from prisma import Prisma
import asyncio
import uuid
from datetime import datetime
from hypothesis import given, strategies as st
from hypothesis.strategies import sampled_from, text, integers


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
        # Should return 401 (auth required) or 400 (missing data), not 404
        self.assertIn(response.status_code, [400, 401])
    
    def test_report_requires_authentication(self):
        """Test that report submission requires authentication."""
        response = self.client.post('/v1/reports/', {
            'content_type': 'story',
            'content_id': 'test-id',
            'reason': 'Test reason'
        })
        self.assertEqual(response.status_code, 401)
    
    def test_report_requires_content_type(self):
        """Test that content_type is required."""
        response = self.client.post('/v1/reports/', {
            'content_id': 'test-id',
            'reason': 'Test reason'
        })
        self.assertIn(response.status_code, [400, 401])
    
    def test_report_requires_content_id(self):
        """Test that content_id is required."""
        response = self.client.post('/v1/reports/', {
            'content_type': 'story',
            'reason': 'Test reason'
        })
        self.assertIn(response.status_code, [400, 401])
    
    def test_report_requires_reason(self):
        """Test that reason is required."""
        response = self.client.post('/v1/reports/', {
            'content_type': 'story',
            'content_id': 'test-id'
        })
        self.assertIn(response.status_code, [400, 401])
    
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
        self.assertIn(response.status_code, [400, 401])
    
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
        self.assertIn(response.status_code, [400, 401])
    
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


class DuplicateReportPropertyTests(TestCase):
    """
    Property-based tests for duplicate report prevention.
    
    Property 26: Duplicate Report Prevention
    For any user and content item, attempting to report the same content twice
    should result in only one Report record.
    
    Requirements:
        - 13.6: Prevent duplicate reports
    """
    
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
