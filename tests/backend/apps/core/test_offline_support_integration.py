"""
Integration tests for offline support in views.

Tests that list and detail views properly integrate the OfflineSupportService
to add cache headers and handle conditional requests.

Validates Requirements: 9.1, 9.2, 9.3, 9.4
"""

import pytest
import json
import asyncio
import threading
import uuid
from datetime import datetime
from django.test import RequestFactory
from django.http import HttpRequest
from rest_framework.test import APIClient
from apps.core.offline_support_service import OfflineSupportService


def _run_async(coro):
    """Run async Prisma operations from sync tests."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    result = {}
    error = {}

    def _runner():
        try:
            result['value'] = asyncio.run(coro)
        except Exception as exc:
            error['value'] = exc

    thread = threading.Thread(target=_runner)
    thread.start()
    thread.join()

    if 'value' in error:
        raise error['value']

    return result.get('value')


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
        unique = uuid.uuid4().hex[:8]
        
        # Create a test story
        prisma_db = Prisma()

        async def _setup_story():
            await prisma_db.connect()
            try:
                profile = await prisma_db.userprofile.create(
                    data={
                        'clerk_user_id': f'test_user_123_{unique}',
                        'handle': f'testuser_{unique}',
                        'display_name': 'Test User',
                    }
                )
                return await prisma_db.story.create(
                    data={
                        'title': 'Test Story',
                        'blurb': 'Test blurb',
                        'slug': f'test-story-{unique}',
                        'author_id': profile.id,
                        'published': True,
                    }
                )
            finally:
                await prisma_db.disconnect()

        story = _run_async(_setup_story())
        
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
        unique = uuid.uuid4().hex[:8]
        
        # Create a test story
        prisma_db = Prisma()

        async def _setup_story():
            await prisma_db.connect()
            try:
                profile = await prisma_db.userprofile.create(
                    data={
                        'clerk_user_id': f'test_user_456_{unique}',
                        'handle': f'testuser2_{unique}',
                        'display_name': 'Test User 2',
                    }
                )
                return await prisma_db.story.create(
                    data={
                        'title': 'Test Story 2',
                        'blurb': 'Test blurb 2',
                        'slug': f'test-story-2-{unique}',
                        'author_id': profile.id,
                        'published': True,
                    }
                )
            finally:
                await prisma_db.disconnect()

        story = _run_async(_setup_story())
        
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
        unique = uuid.uuid4().hex[:8]
        
        # Create a test story with chapters
        prisma_db = Prisma()

        async def _setup_story():
            await prisma_db.connect()
            try:
                profile = await prisma_db.userprofile.create(
                    data={
                        'clerk_user_id': f'test_user_789_{unique}',
                        'handle': f'testuser3_{unique}',
                        'display_name': 'Test User 3',
                    }
                )
                return await prisma_db.story.create(
                    data={
                        'title': 'Test Story 3',
                        'blurb': 'Test blurb 3',
                        'slug': f'test-story-3-{unique}',
                        'author_id': profile.id,
                        'published': True,
                    }
                )
            finally:
                await prisma_db.disconnect()

        story = _run_async(_setup_story())
        
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
        unique = uuid.uuid4().hex[:8]
        
        # Create a test chapter
        prisma_db = Prisma()

        async def _setup_chapter():
            await prisma_db.connect()
            try:
                profile = await prisma_db.userprofile.create(
                    data={
                        'clerk_user_id': f'test_user_101_{unique}',
                        'handle': f'testuser4_{unique}',
                        'display_name': 'Test User 4',
                    }
                )
                story = await prisma_db.story.create(
                    data={
                        'title': 'Test Story 4',
                        'blurb': 'Test blurb 4',
                        'slug': f'test-story-4-{unique}',
                        'author_id': profile.id,
                        'published': True,
                    }
                )
                return await prisma_db.chapter.create(
                    data={
                        'story_id': story.id,
                        'title': 'Test Chapter',
                        'content': 'Test content',
                        'chapter_number': 1,
                    }
                )
            finally:
                await prisma_db.disconnect()

        chapter = _run_async(_setup_chapter())
        
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
        unique = uuid.uuid4().hex[:8]
        
        # Create a test user profile
        prisma_db = Prisma()

        async def _setup_profile():
            await prisma_db.connect()
            try:
                return await prisma_db.userprofile.create(
                    data={
                        'clerk_user_id': f'test_user_202_{unique}',
                        'handle': f'testuser5_{unique}',
                        'display_name': 'Test User 5',
                    }
                )
            finally:
                await prisma_db.disconnect()

        profile = _run_async(_setup_profile())
        
        # First request to get ETag
        response1 = self.client.get(f'/v1/users/{profile.handle}/')
        assert response1.status_code == 200
        etag = response1['ETag']
        
        # Second request with If-None-Match header
        response2 = self.client.get(
            f'/v1/users/{profile.handle}/',
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
        unique = uuid.uuid4().hex[:8]
        
        # Create a test story
        prisma_db = Prisma()

        async def _setup_story():
            await prisma_db.connect()
            try:
                profile = await prisma_db.userprofile.create(
                    data={
                        'clerk_user_id': f'test_user_303_{unique}',
                        'handle': f'testuser6_{unique}',
                        'display_name': 'Test User 6',
                    }
                )
                return await prisma_db.story.create(
                    data={
                        'title': 'Test Story 5',
                        'blurb': 'Test blurb 5',
                        'slug': f'test-story-5-{unique}',
                        'author_id': profile.id,
                        'published': True,
                    }
                )
            finally:
                await prisma_db.disconnect()

        story = _run_async(_setup_story())
        
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
