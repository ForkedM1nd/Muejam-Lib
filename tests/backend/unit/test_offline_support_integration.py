"""
Unit tests for offline support integration in views.

Tests cache headers, conditional requests, and 304 Not Modified responses
for list and detail views across stories, discovery, and user endpoints.

Requirements: 9.1, 9.2, 9.3, 9.4
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from django.test import RequestFactory
from django.http import HttpResponse
from rest_framework.response import Response
from apps.core.offline_support_service import OfflineSupportService


class TestOfflineSupportService:
    """Test the OfflineSupportService methods."""
    
    def test_generate_etag(self):
        """Test ETag generation produces consistent hashes."""
        content = "test content"
        etag1 = OfflineSupportService.generate_etag(content)
        etag2 = OfflineSupportService.generate_etag(content)
        
        # Same content should produce same ETag
        assert etag1 == etag2
        assert etag1.startswith('"')
        assert etag1.endswith('"')
    
    def test_generate_etag_different_content(self):
        """Test different content produces different ETags."""
        etag1 = OfflineSupportService.generate_etag("content1")
        etag2 = OfflineSupportService.generate_etag("content2")
        
        assert etag1 != etag2
    
    def test_add_cache_headers(self):
        """Test cache headers are added correctly."""
        response = HttpResponse()
        last_modified = datetime(2024, 1, 15, 10, 0, 0)
        etag = '"abc123"'
        
        OfflineSupportService.add_cache_headers(response, last_modified, etag)
        
        assert 'Last-Modified' in response
        assert 'ETag' in response
        assert 'Cache-Control' in response
        assert response['ETag'] == etag
        assert 'private' in response['Cache-Control']
        assert 'must-revalidate' in response['Cache-Control']
    
    def test_check_conditional_request_with_matching_etag(self):
        """Test conditional request returns True when ETag matches."""
        factory = RequestFactory()
        request = factory.get('/', HTTP_IF_NONE_MATCH='"abc123"')
        
        last_modified = datetime(2024, 1, 15, 10, 0, 0)
        etag = '"abc123"'
        
        result = OfflineSupportService.check_conditional_request(request, last_modified, etag)
        
        assert result is True
    
    def test_check_conditional_request_with_non_matching_etag(self):
        """Test conditional request returns False when ETag doesn't match."""
        factory = RequestFactory()
        request = factory.get('/', HTTP_IF_NONE_MATCH='"xyz789"')
        
        last_modified = datetime(2024, 1, 15, 10, 0, 0)
        etag = '"abc123"'
        
        result = OfflineSupportService.check_conditional_request(request, last_modified, etag)
        
        assert result is False
    
    def test_check_conditional_request_with_if_modified_since(self):
        """Test conditional request with If-Modified-Since header."""
        factory = RequestFactory()
        # Client has content from Jan 15, 2024
        request = factory.get('/', HTTP_IF_MODIFIED_SINCE='Mon, 15 Jan 2024 10:00:00 GMT')
        
        # Content was last modified on Jan 15, 2024 (same time)
        last_modified = datetime(2024, 1, 15, 10, 0, 0)
        etag = '"abc123"'
        
        result = OfflineSupportService.check_conditional_request(request, last_modified, etag)
        
        # Should return True because content hasn't changed
        assert result is True
    
    def test_check_conditional_request_with_newer_content(self):
        """Test conditional request returns False when content is newer."""
        factory = RequestFactory()
        # Client has content from Jan 15, 2024
        request = factory.get('/', HTTP_IF_MODIFIED_SINCE='Mon, 15 Jan 2024 10:00:00 GMT')
        
        # Content was last modified on Jan 16, 2024 (newer)
        last_modified = datetime(2024, 1, 16, 10, 0, 0)
        etag = '"abc123"'
        
        result = OfflineSupportService.check_conditional_request(request, last_modified, etag)
        
        # Should return False because content has changed
        assert result is False
    
    def test_check_conditional_request_no_headers(self):
        """Test conditional request returns False when no conditional headers present."""
        factory = RequestFactory()
        request = factory.get('/')
        
        last_modified = datetime(2024, 1, 15, 10, 0, 0)
        etag = '"abc123"'
        
        result = OfflineSupportService.check_conditional_request(request, last_modified, etag)
        
        assert result is False
    
    def test_create_not_modified_response(self):
        """Test 304 Not Modified response creation."""
        response = OfflineSupportService.create_not_modified_response()
        
        assert response.status_code == 304
        assert not response.content


class TestViewsOfflineSupport:
    """Test offline support integration in views."""
    
    @patch('apps.stories.views.Prisma')
    def test_story_list_includes_cache_headers(self, mock_prisma):
        """Test story list view includes cache headers."""
        from apps.stories.views import _list_stories
        
        # Mock database response
        mock_db = MagicMock()
        mock_prisma.return_value = mock_db
        
        mock_story = MagicMock()
        mock_story.id = 'story-1'
        mock_story.title = 'Test Story'
        mock_story.updated_at = datetime(2024, 1, 15, 10, 0, 0)
        mock_story.deleted_at = None
        
        mock_db.story.find_many.return_value = [mock_story]
        
        # Create request
        factory = RequestFactory()
        request = factory.get('/v1/stories')
        request.query_params = {}
        
        # Call view
        response = _list_stories(request)
        
        # Check cache headers are present
        assert 'Last-Modified' in response
        assert 'ETag' in response
        assert 'Cache-Control' in response
    
    @patch('apps.stories.views.Prisma')
    def test_story_detail_returns_304_when_not_modified(self, mock_prisma):
        """Test story detail view returns 304 when content hasn't changed."""
        from apps.stories.views import get_story_by_slug
        
        # Mock database response
        mock_db = MagicMock()
        mock_prisma.return_value = mock_db
        
        mock_story = MagicMock()
        mock_story.id = 'story-1'
        mock_story.title = 'Test Story'
        mock_story.updated_at = datetime(2024, 1, 15, 10, 0, 0)
        mock_story.deleted_at = None
        mock_story.author_id = 'author-1'
        
        mock_db.story.find_unique.return_value = mock_story
        
        # Create request with If-Modified-Since header
        factory = RequestFactory()
        request = factory.get('/v1/stories/test-story', HTTP_IF_MODIFIED_SINCE='Mon, 15 Jan 2024 10:00:00 GMT')
        
        # Mock cache manager
        with patch('apps.stories.views.cache_manager.get', return_value=None):
            response = get_story_by_slug(request, 'test-story')
        
        # Should return 304 Not Modified
        assert response.status_code == 304
    
    @patch('apps.discovery.views.asyncio.run')
    @patch('apps.discovery.views.CacheManager')
    def test_discovery_feed_includes_cache_headers(self, mock_cache_manager, mock_asyncio_run):
        """Test discovery feed includes cache headers."""
        from apps.discovery.views import discover_feed
        
        # Mock cache miss
        mock_cache_manager.get_or_set.side_effect = lambda key, func, ttl: func()
        mock_cache_manager.make_key.return_value = 'cache_key'
        mock_cache_manager.TTL_CONFIG = {'discover_feed': 300}
        
        # Mock async function return
        mock_asyncio_run.return_value = {
            'data': [
                {
                    'id': 'story-1',
                    'title': 'Test Story',
                    'published_at': '2024-01-15T10:00:00Z'
                }
            ],
            'next_cursor': None
        }
        
        # Create request
        factory = RequestFactory()
        request = factory.get('/v1/discovery/feed?tab=trending')
        request.query_params = {'tab': 'trending'}
        
        # Call view
        response = discover_feed(request)
        
        # Check cache headers are present
        assert 'Last-Modified' in response
        assert 'ETag' in response
        assert 'Cache-Control' in response
    
    @patch('apps.users.views.sync_get_profile_by_handle')
    def test_user_profile_returns_304_when_not_modified(self, mock_get_profile):
        """Test user profile view returns 304 when content hasn't changed."""
        from apps.users.views import user_by_handle
        
        # Mock profile
        mock_profile = MagicMock()
        mock_profile.id = 'user-1'
        mock_profile.handle = 'testuser'
        mock_profile.updated_at = datetime(2024, 1, 15, 10, 0, 0)
        
        mock_get_profile.return_value = mock_profile
        
        # Create request with If-Modified-Since header
        factory = RequestFactory()
        request = factory.get('/v1/users/testuser', HTTP_IF_MODIFIED_SINCE='Mon, 15 Jan 2024 10:00:00 GMT')
        
        response = user_by_handle(request, 'testuser')
        
        # Should return 304 Not Modified
        assert response.status_code == 304


class TestCacheControlHeaders:
    """Test cache-control headers for mobile clients."""
    
    def test_cache_control_includes_private_directive(self):
        """Test cache-control includes private directive for user-specific content."""
        response = HttpResponse()
        last_modified = datetime(2024, 1, 15, 10, 0, 0)
        etag = '"abc123"'
        
        OfflineSupportService.add_cache_headers(response, last_modified, etag)
        
        assert 'private' in response['Cache-Control']
    
    def test_cache_control_includes_must_revalidate(self):
        """Test cache-control includes must-revalidate directive."""
        response = HttpResponse()
        last_modified = datetime(2024, 1, 15, 10, 0, 0)
        etag = '"abc123"'
        
        OfflineSupportService.add_cache_headers(response, last_modified, etag)
        
        assert 'must-revalidate' in response['Cache-Control']
    
    def test_cache_control_includes_max_age(self):
        """Test cache-control includes max-age directive."""
        response = HttpResponse()
        last_modified = datetime(2024, 1, 15, 10, 0, 0)
        etag = '"abc123"'
        
        OfflineSupportService.add_cache_headers(response, last_modified, etag)
        
        assert 'max-age' in response['Cache-Control']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
