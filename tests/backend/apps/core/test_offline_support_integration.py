"""
Integration tests for offline support in views.

Tests that list and detail views properly integrate the OfflineSupportService
to add cache headers and handle conditional requests.

Validates Requirements: 9.1, 9.2, 9.3, 9.4
"""

import pytest
import json
from datetime import datetime
from django.test import RequestFactory
from django.http import HttpRequest
from rest_framework.test import APIClient
from apps.core.offline_support_service import OfflineSupportService


@pytest.mark.django_db
class TestOfflineSupportIntegration:
    """Integration tests for offline support in views."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        self.client = APIClient()
    
    def test_story_list_includes_cache_headers(self):
        """
        Test that story list endpoint includes cache headers.
        
        Validates: Requirement 9.1, 9.4
        """
        # Make request to story list endpoint
        response = self.client.get('/v1/stories/')
        
        # Verify cache headers are present
        assert 'Last-Modified' in response
        assert 'ETag' in response
        assert 'Cache-Control' in response
        
        # Verify cache control has appropriate directives
        cache_control = response['Cache-Control']
        assert 'private' in cache_control
        assert 'must-revalidate' in cache_control
        assert 'max-age' in cache_control
    
    def test_story_detail_includes_cache_headers(self, db):
        """
        Test that story detail endpoint includes cache headers.
        
        Validates: Requirement 9.1, 9.4
        """
        from prisma import Prisma
        
        # Create a test story
        prisma_db = Prisma()
        prisma_db.connect()
        
        # Create test user profile first
        profile = prisma_db.userprofile.create(
            data={
                'clerk_user_id': 'test_user_123',
                'handle': 'testuser',
                'display_name': 'Test User',
            }
        )
        
        story = prisma_db.story.create(
            data={
                'title': 'Test Story',
                'blurb': 'Test blurb',
                'slug': 'test-story',
                'author_id': profile.id,
                'published': True,
            }
        )
        
        prisma_db.disconnect()
        
        # Make request to story detail endpoint
        response = self.client.get(f'/v1/stories/{story.slug}')
        
        # Verify cache headers are present
        assert 'Last-Modified' in response
        assert 'ETag' in response
        assert 'Cache-Control' in response
    
    def test_story_detail_conditional_request_returns_304(self, db):
        """
        Test that story detail endpoint returns 304 for conditional requests.
        
        Validates: Requirement 9.2, 9.3
        """
        from prisma import Prisma
        
        # Create a test story
        prisma_db = Prisma()
        prisma_db.connect()
        
        # Create test user profile first
        profile = prisma_db.userprofile.create(
            data={
                'clerk_user_id': 'test_user_456',
                'handle': 'testuser2',
                'display_name': 'Test User 2',
            }
        )
        
        story = prisma_db.story.create(
            data={
                'title': 'Test Story 2',
                'blurb': 'Test blurb 2',
                'slug': 'test-story-2',
                'author_id': profile.id,
                'published': True,
            }
        )
        
        prisma_db.disconnect()
        
        # First request to get ETag
        response1 = self.client.get(f'/v1/stories/{story.slug}')
        assert response1.status_code == 200
        etag = response1['ETag']
        
        # Second request with If-None-Match header
        response2 = self.client.get(
            f'/v1/stories/{story.slug}',
            HTTP_IF_NONE_MATCH=etag
        )
        
        # Should return 304 Not Modified
        assert response2.status_code == 304
        assert len(response2.content) == 0  # No body
        assert 'ETag' in response2  # Headers still present
    
    def test_chapter_list_includes_cache_headers(self, db):
        """
        Test that chapter list endpoint includes cache headers.
        
        Validates: Requirement 9.1, 9.4
        """
        from prisma import Prisma
        
        # Create a test story with chapters
        prisma_db = Prisma()
        prisma_db.connect()
        
        # Create test user profile
        profile = prisma_db.userprofile.create(
            data={
                'clerk_user_id': 'test_user_789',
                'handle': 'testuser3',
                'display_name': 'Test User 3',
            }
        )
        
        story = prisma_db.story.create(
            data={
                'title': 'Test Story 3',
                'blurb': 'Test blurb 3',
                'slug': 'test-story-3',
                'author_id': profile.id,
                'published': True,
            }
        )
        
        prisma_db.disconnect()
        
        # Make request to chapter list endpoint
        response = self.client.get(f'/v1/stories/{story.id}/chapters')
        
        # Verify cache headers are present
        assert 'Last-Modified' in response
        assert 'ETag' in response
        assert 'Cache-Control' in response
    
    def test_chapter_detail_conditional_request_returns_304(self, db):
        """
        Test that chapter detail endpoint returns 304 for conditional requests.
        
        Validates: Requirement 9.2, 9.3
        """
        from prisma import Prisma
        
        # Create a test chapter
        prisma_db = Prisma()
        prisma_db.connect()
        
        # Create test user profile
        profile = prisma_db.userprofile.create(
            data={
                'clerk_user_id': 'test_user_101',
                'handle': 'testuser4',
                'display_name': 'Test User 4',
            }
        )
        
        story = prisma_db.story.create(
            data={
                'title': 'Test Story 4',
                'blurb': 'Test blurb 4',
                'slug': 'test-story-4',
                'author_id': profile.id,
                'published': True,
            }
        )
        
        chapter = prisma_db.chapter.create(
            data={
                'story_id': story.id,
                'title': 'Test Chapter',
                'content': 'Test content',
                'chapter_number': 1,
            }
        )
        
        prisma_db.disconnect()
        
        # First request to get ETag
        response1 = self.client.get(f'/v1/chapters/{chapter.id}')
        assert response1.status_code == 200
        etag = response1['ETag']
        
        # Second request with If-None-Match header
        response2 = self.client.get(
            f'/v1/chapters/{chapter.id}',
            HTTP_IF_NONE_MATCH=etag
        )
        
        # Should return 304 Not Modified
        assert response2.status_code == 304
        assert len(response2.content) == 0
        assert 'ETag' in response2
    
    def test_whisper_list_includes_cache_headers(self):
        """
        Test that whisper list endpoint includes cache headers.
        
        Validates: Requirement 9.1, 9.4
        """
        # Make request to whisper list endpoint
        response = self.client.get('/v1/whispers/')
        
        # Verify cache headers are present
        assert 'Last-Modified' in response
        assert 'ETag' in response
        assert 'Cache-Control' in response
    
    def test_user_profile_conditional_request_returns_304(self, db):
        """
        Test that user profile endpoint returns 304 for conditional requests.
        
        Validates: Requirement 9.2, 9.3
        """
        from prisma import Prisma
        
        # Create a test user profile
        prisma_db = Prisma()
        prisma_db.connect()
        
        profile = prisma_db.userprofile.create(
            data={
                'clerk_user_id': 'test_user_202',
                'handle': 'testuser5',
                'display_name': 'Test User 5',
            }
        )
        
        prisma_db.disconnect()
        
        # First request to get ETag
        response1 = self.client.get(f'/v1/users/{profile.handle}')
        assert response1.status_code == 200
        etag = response1['ETag']
        
        # Second request with If-None-Match header
        response2 = self.client.get(
            f'/v1/users/{profile.handle}',
            HTTP_IF_NONE_MATCH=etag
        )
        
        # Should return 304 Not Modified
        assert response2.status_code == 304
        assert len(response2.content) == 0
        assert 'ETag' in response2
    
    def test_conditional_request_with_if_modified_since(self, db):
        """
        Test conditional request using If-Modified-Since header.
        
        Validates: Requirement 9.2, 9.3
        """
        from prisma import Prisma
        from django.utils.http import http_date
        
        # Create a test story
        prisma_db = Prisma()
        prisma_db.connect()
        
        profile = prisma_db.userprofile.create(
            data={
                'clerk_user_id': 'test_user_303',
                'handle': 'testuser6',
                'display_name': 'Test User 6',
            }
        )
        
        story = prisma_db.story.create(
            data={
                'title': 'Test Story 5',
                'blurb': 'Test blurb 5',
                'slug': 'test-story-5',
                'author_id': profile.id,
                'published': True,
            }
        )
        
        prisma_db.disconnect()
        
        # First request to get Last-Modified
        response1 = self.client.get(f'/v1/stories/{story.slug}')
        assert response1.status_code == 200
        last_modified = response1['Last-Modified']
        
        # Second request with If-Modified-Since header
        response2 = self.client.get(
            f'/v1/stories/{story.slug}',
            HTTP_IF_MODIFIED_SINCE=last_modified
        )
        
        # Should return 304 Not Modified
        assert response2.status_code == 304
        assert len(response2.content) == 0
