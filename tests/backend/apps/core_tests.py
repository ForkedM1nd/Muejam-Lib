"""Unit tests for core utilities."""
import base64
import json
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, override_settings
from django.core.cache import cache
from rest_framework.test import APIRequestFactory
from rest_framework.response import Response
from rest_framework import status

from apps.core.pagination import CursorPagination
from apps.core.rate_limiting import rate_limit
from apps.core.cache import CacheManager, CacheInvalidator
from apps.core.exceptions import (
    RateLimitExceeded,
    InvalidCursor,
    ContentDeleted,
    UserBlocked,
    DuplicateResource,
    InvalidOffset,
    custom_exception_handler
)


# Use local memory cache for testing
@override_settings(CACHES={
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-test-cache',
    }
})
class CursorPaginationTests(TestCase):
    """Test cursor-based pagination."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.factory = APIRequestFactory()
        self.paginator = CursorPagination()
        
    def test_default_page_size(self):
        """Test default page size is 20."""
        self.assertEqual(self.paginator.page_size, 20)
        
    def test_max_page_size_enforced(self):
        """Test maximum page size is enforced."""
        request = self.factory.get('/', {'page_size': 200})
        
        # Create mock queryset
        mock_queryset = MagicMock()
        mock_queryset.order_by.return_value = mock_queryset
        mock_queryset.__getitem__.return_value = []
        
        self.paginator.paginate_queryset(mock_queryset, request)
        self.assertEqual(self.paginator.page_size, 100)
        
    def test_pagination_without_cursor(self):
        """Test pagination from beginning without cursor."""
        request = self.factory.get('/')
        
        # Create mock items
        mock_items = [Mock(id=i) for i in range(25)]
        mock_queryset = MagicMock()
        mock_queryset.order_by.return_value = mock_queryset
        mock_queryset.__getitem__.return_value = mock_items[:21]
        
        results = self.paginator.paginate_queryset(mock_queryset, request)
        
        # Should return 20 items (page_size)
        self.assertEqual(len(results), 20)
        # Should have next cursor
        self.assertIsNotNone(self.paginator.next_cursor)
        
    def test_pagination_with_cursor(self):
        """Test pagination with cursor."""
        # Create cursor
        cursor_data = {'id': 10}
        cursor = base64.b64encode(json.dumps(cursor_data).encode('utf-8')).decode('utf-8')
        
        request = self.factory.get('/', {'cursor': cursor})
        
        mock_queryset = MagicMock()
        mock_queryset.order_by.return_value = mock_queryset
        mock_queryset.filter.return_value = mock_queryset
        mock_queryset.__getitem__.return_value = []
        
        self.paginator.paginate_queryset(mock_queryset, request)
        
        # Should apply filter
        mock_queryset.filter.assert_called_once()
        
    def test_pagination_last_page(self):
        """Test pagination on last page (no next cursor)."""
        request = self.factory.get('/')
        
        # Create mock items (less than page_size)
        mock_items = [Mock(id=i) for i in range(15)]
        mock_queryset = MagicMock()
        mock_queryset.order_by.return_value = mock_queryset
        mock_queryset.__getitem__.return_value = mock_items
        
        results = self.paginator.paginate_queryset(mock_queryset, request)
        
        # Should return all items
        self.assertEqual(len(results), 15)
        # Should not have next cursor
        self.assertIsNone(self.paginator.next_cursor)
        
    def test_paginated_response_format(self):
        """Test paginated response format."""
        self.paginator.next_cursor = 'test_cursor'
        data = [{'id': 1}, {'id': 2}]
        
        response = self.paginator.get_paginated_response(data)
        
        self.assertIn('data', response.data)
        self.assertIn('next_cursor', response.data)
        self.assertEqual(response.data['data'], data)
        self.assertEqual(response.data['next_cursor'], 'test_cursor')
        
    def test_invalid_cursor_ignored(self):
        """Test invalid cursor is ignored and pagination starts from beginning."""
        request = self.factory.get('/', {'cursor': 'invalid_cursor'})
        
        mock_queryset = MagicMock()
        mock_queryset.order_by.return_value = mock_queryset
        mock_queryset.__getitem__.return_value = []
        
        # Should not raise exception
        self.paginator.paginate_queryset(mock_queryset, request)


@override_settings(CACHES={
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-test-cache',
    }
})
class RateLimitingTests(TestCase):
    """Test rate limiting decorator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.factory = APIRequestFactory()
        cache.clear()
        
    def tearDown(self):
        """Clean up after tests."""
        cache.clear()
        
    def test_rate_limit_allows_within_limit(self):
        """Test requests within limit are allowed."""
        @rate_limit('test', 5, 60)
        def test_view(request):
            return Response({'success': True})
        
        request = self.factory.get('/')
        request.clerk_user_id = 'user_123'
        
        # First request should succeed
        response = test_view(request)
        self.assertEqual(response.status_code, 200)
        
    def test_rate_limit_blocks_over_limit(self):
        """Test requests over limit are blocked."""
        @rate_limit('test', 3, 60)
        def test_view(request):
            return Response({'success': True})
        
        request = self.factory.get('/')
        request.clerk_user_id = 'user_123'
        
        # Make 3 requests (at limit)
        for _ in range(3):
            response = test_view(request)
            self.assertEqual(response.status_code, 200)
        
        # 4th request should be blocked
        response = test_view(request)
        self.assertEqual(response.status_code, 429)
        self.assertIn('error', response.data)
        
    def test_rate_limit_includes_retry_after_header(self):
        """Test rate limit response includes Retry-After header."""
        @rate_limit('test', 1, 60)
        def test_view(request):
            return Response({'success': True})
        
        request = self.factory.get('/')
        request.clerk_user_id = 'user_123'
        
        # First request
        test_view(request)
        
        # Second request should be blocked
        response = test_view(request)
        self.assertEqual(response.status_code, 429)
        self.assertIn('Retry-After', response)
        self.assertEqual(response['Retry-After'], '60')
        
    def test_rate_limit_skips_unauthenticated(self):
        """Test rate limiting is skipped for unauthenticated requests."""
        @rate_limit('test', 1, 60)
        def test_view(request):
            return Response({'success': True})
        
        request = self.factory.get('/')
        # No clerk_user_id
        
        # Multiple requests should succeed
        for _ in range(5):
            response = test_view(request)
            self.assertEqual(response.status_code, 200)
            
    def test_rate_limit_per_user(self):
        """Test rate limits are per user."""
        @rate_limit('test', 2, 60)
        def test_view(request):
            return Response({'success': True})
        
        request1 = self.factory.get('/')
        request1.clerk_user_id = 'user_1'
        
        request2 = self.factory.get('/')
        request2.clerk_user_id = 'user_2'
        
        # User 1 makes 2 requests
        for _ in range(2):
            response = test_view(request1)
            self.assertEqual(response.status_code, 200)
        
        # User 1's 3rd request should be blocked
        response = test_view(request1)
        self.assertEqual(response.status_code, 429)
        
        # User 2's request should still succeed
        response = test_view(request2)
        self.assertEqual(response.status_code, 200)


@override_settings(CACHES={
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-test-cache',
    }
})
class CacheManagerTests(TestCase):
    """Test cache manager utilities."""
    
    def setUp(self):
        """Set up test fixtures."""
        cache.clear()
        
    def tearDown(self):
        """Clean up after tests."""
        cache.clear()
        
    def test_make_key_generates_consistent_keys(self):
        """Test make_key generates consistent keys for same params."""
        key1 = CacheManager.make_key('test', param1='value1', param2='value2')
        key2 = CacheManager.make_key('test', param1='value1', param2='value2')
        
        self.assertEqual(key1, key2)
        
    def test_make_key_different_for_different_params(self):
        """Test make_key generates different keys for different params."""
        key1 = CacheManager.make_key('test', param='value1')
        key2 = CacheManager.make_key('test', param='value2')
        
        self.assertNotEqual(key1, key2)
        
    def test_get_or_set_returns_cached_value(self):
        """Test get_or_set returns cached value if exists."""
        key = 'test_key'
        cached_value = {'data': 'cached'}
        cache.set(key, cached_value, 60)
        
        fetch_func = Mock(return_value={'data': 'fresh'})
        
        result = CacheManager.get_or_set(key, fetch_func, 60)
        
        # Should return cached value
        self.assertEqual(result, cached_value)
        # Should not call fetch function
        fetch_func.assert_not_called()
        
    def test_get_or_set_fetches_on_cache_miss(self):
        """Test get_or_set fetches and caches on cache miss."""
        key = 'test_key'
        fresh_value = {'data': 'fresh'}
        fetch_func = Mock(return_value=fresh_value)
        
        result = CacheManager.get_or_set(key, fetch_func, 60)
        
        # Should return fresh value
        self.assertEqual(result, fresh_value)
        # Should call fetch function
        fetch_func.assert_called_once()
        # Should cache the value
        self.assertEqual(cache.get(key), fresh_value)
        
    def test_invalidate_removes_key(self):
        """Test invalidate removes cache key."""
        key = 'test_key'
        cache.set(key, 'value', 60)
        
        CacheManager.invalidate(key)
        
        self.assertIsNone(cache.get(key))
        
    def test_ttl_config_values(self):
        """Test TTL configuration has expected values."""
        self.assertEqual(CacheManager.TTL_CONFIG['discover_feed'], 180)
        self.assertEqual(CacheManager.TTL_CONFIG['trending_feed'], 300)
        self.assertEqual(CacheManager.TTL_CONFIG['whispers_feed'], 60)
        self.assertEqual(CacheManager.TTL_CONFIG['story_metadata'], 600)
        self.assertEqual(CacheManager.TTL_CONFIG['search_suggest'], 1200)
        self.assertEqual(CacheManager.TTL_CONFIG['for_you_feed'], 7200)
        self.assertEqual(CacheManager.TTL_CONFIG['user_profile'], 300)


@override_settings(CACHES={
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-test-cache',
    }
})
class CacheInvalidatorTests(TestCase):
    """Test cache invalidation logic."""
    
    def setUp(self):
        """Set up test fixtures."""
        cache.clear()
        
    def tearDown(self):
        """Clean up after tests."""
        cache.clear()
        
    @patch.object(CacheManager, 'invalidate_pattern')
    @patch.object(CacheManager, 'invalidate')
    def test_on_story_published_invalidates_caches(self, mock_invalidate, mock_invalidate_pattern):
        """Test story publication invalidates relevant caches."""
        story_id = 'story_123'
        
        CacheInvalidator.on_story_published(story_id)
        
        # Should invalidate discover feeds
        mock_invalidate_pattern.assert_called_with('discover_feed:*')
        # Should invalidate story metadata
        mock_invalidate.assert_called_with(f'story:{story_id}')
        
    @patch.object(CacheManager, 'invalidate_pattern')
    def test_on_whisper_created_global(self, mock_invalidate_pattern):
        """Test global whisper creation invalidates global feed."""
        CacheInvalidator.on_whisper_created('whisper_123', 'GLOBAL')
        
        mock_invalidate_pattern.assert_called_with('whispers_feed:global:*')
        
    @patch.object(CacheManager, 'invalidate_pattern')
    def test_on_whisper_created_story(self, mock_invalidate_pattern):
        """Test story whisper creation invalidates story feed."""
        story_id = 'story_123'
        CacheInvalidator.on_whisper_created('whisper_123', 'STORY', story_id)
        
        mock_invalidate_pattern.assert_called_with(f'whispers_feed:story:{story_id}:*')
        
    @patch.object(CacheManager, 'invalidate')
    def test_on_user_profile_updated(self, mock_invalidate):
        """Test profile update invalidates user cache."""
        user_id = 'user_123'
        
        CacheInvalidator.on_user_profile_updated(user_id)
        
        mock_invalidate.assert_called_with(f'user_profile:{user_id}')


class CustomExceptionsTests(TestCase):
    """Test custom exception classes."""
    
    def test_rate_limit_exceeded_exception(self):
        """Test RateLimitExceeded exception."""
        exc = RateLimitExceeded()
        self.assertEqual(exc.status_code, 429)
        self.assertIn('rate limit', str(exc.detail).lower())
        
    def test_invalid_cursor_exception(self):
        """Test InvalidCursor exception."""
        exc = InvalidCursor()
        self.assertEqual(exc.status_code, 400)
        self.assertIn('cursor', str(exc.detail).lower())
        
    def test_content_deleted_exception(self):
        """Test ContentDeleted exception."""
        exc = ContentDeleted()
        self.assertEqual(exc.status_code, 404)
        self.assertIn('deleted', str(exc.detail).lower())
        
    def test_user_blocked_exception(self):
        """Test UserBlocked exception."""
        exc = UserBlocked()
        self.assertEqual(exc.status_code, 403)
        self.assertIn('blocked', str(exc.detail).lower())
        
    def test_duplicate_resource_exception(self):
        """Test DuplicateResource exception."""
        exc = DuplicateResource()
        self.assertEqual(exc.status_code, 409)
        self.assertIn('exists', str(exc.detail).lower())
        
    def test_invalid_offset_exception(self):
        """Test InvalidOffset exception."""
        exc = InvalidOffset()
        self.assertEqual(exc.status_code, 400)
        self.assertIn('offset', str(exc.detail).lower())


class CustomExceptionHandlerTests(TestCase):
    """Test custom exception handler."""
    
    def test_exception_handler_formats_response(self):
        """Test exception handler formats error response correctly."""
        exc = RateLimitExceeded()
        context = {}
        
        response = custom_exception_handler(exc, context)
        
        self.assertIsNotNone(response)
        self.assertIn('error', response.data)
        self.assertIn('code', response.data['error'])
        self.assertIn('message', response.data['error'])
        self.assertIn('details', response.data['error'])
        
    def test_exception_handler_includes_error_code(self):
        """Test exception handler includes error code."""
        exc = RateLimitExceeded()
        context = {}
        
        response = custom_exception_handler(exc, context)
        
        self.assertEqual(response.data['error']['code'], 'RATE_LIMIT_EXCEEDED')
        
    def test_exception_handler_returns_none_for_non_api_exceptions(self):
        """Test exception handler returns None for non-API exceptions."""
        exc = ValueError("Test error")
        context = {}
        
        response = custom_exception_handler(exc, context)
        
        # Should return None for non-DRF exceptions
        self.assertIsNone(response)



class HealthCheckTests(TestCase):
    """
    Tests for health check endpoint.
    
    Requirements:
        - 22.1: Health check endpoint exists
        - 22.2: Check PostgreSQL connectivity
        - 22.3: Check Valkey connectivity
        - 22.4: Return HTTP 200 when healthy
        - 22.5: Return HTTP 503 when unhealthy
    """
    
    def setUp(self):
        """Set up test client."""
        from rest_framework.test import APIClient
        self.client = APIClient()
    
    def test_health_check_endpoint_exists(self):
        """
        Test that health check endpoint is accessible.
        
        Requirements:
            - 22.1: GET /v1/health endpoint exists
        """
        response = self.client.get('/v1/health/')
        # Should return 200 or 503, not 404
        self.assertIn(response.status_code, [200, 503])
    
    def test_health_check_no_auth_required(self):
        """
        Test that health check does not require authentication.
        
        Requirements:
            - 22.7: No authentication required
        """
        response = self.client.get('/v1/health/')
        # Should not return 401 (unauthorized)
        self.assertNotEqual(response.status_code, 401)
    
    def test_health_check_response_structure(self):
        """
        Test that health check response has correct structure.
        
        Requirements:
            - 22.6: Include response time and timestamp
        """
        response = self.client.get('/v1/health/')
        data = response.json()
        
        # Verify response structure
        self.assertIn('status', data)
        self.assertIn('timestamp', data)
        self.assertIn('checks', data)
        
        # Verify checks structure
        self.assertIsInstance(data['checks'], dict)
    
    def test_health_check_includes_database_check(self):
        """
        Test that health check includes database connectivity check.
        
        Requirements:
            - 22.2: Check PostgreSQL connectivity
        """
        response = self.client.get('/v1/health/')
        data = response.json()
        
        self.assertIn('database', data['checks'])
    
    def test_health_check_includes_cache_check(self):
        """
        Test that health check includes cache connectivity check.
        
        Requirements:
            - 22.3: Check Valkey connectivity
        """
        response = self.client.get('/v1/health/')
        data = response.json()
        
        self.assertIn('cache', data['checks'])
    
    def test_health_check_healthy_status(self):
        """
        Test that health check returns 200 when all dependencies are healthy.
        
        Requirements:
            - 22.4: Return HTTP 200 with "healthy" status
        """
        response = self.client.get('/v1/health/')
        
        # If all dependencies are up, should return 200
        if response.status_code == 200:
            data = response.json()
            self.assertEqual(data['status'], 'healthy')
            self.assertEqual(data['checks']['database'], 'healthy')
            self.assertEqual(data['checks']['cache'], 'healthy')
    
    @patch('django.db.connection.ensure_connection')
    def test_health_check_unhealthy_database(self, mock_ensure_connection):
        """
        Test that health check returns 503 when database is down.
        
        Requirements:
            - 22.2: Check PostgreSQL connectivity
            - 22.5: Return HTTP 503 when unhealthy
        """
        # Simulate database connection failure
        mock_ensure_connection.side_effect = Exception('Database connection failed')
        
        response = self.client.get('/v1/health/')
        
        # Should return 503
        self.assertEqual(response.status_code, 503)
        
        data = response.json()
        self.assertEqual(data['status'], 'unhealthy')
        self.assertIn('unhealthy', data['checks']['database'])
    
    @patch('django.core.cache.cache.set')
    def test_health_check_unhealthy_cache(self, mock_cache_set):
        """
        Test that health check returns 503 when cache is down.
        
        Requirements:
            - 22.3: Check Valkey connectivity
            - 22.5: Return HTTP 503 when unhealthy
        """
        # Simulate cache connection failure
        mock_cache_set.side_effect = Exception('Cache connection failed')
        
        response = self.client.get('/v1/health/')
        
        # Should return 503
        self.assertEqual(response.status_code, 503)
        
        data = response.json()
        self.assertEqual(data['status'], 'unhealthy')
        self.assertIn('unhealthy', data['checks']['cache'])
    
    def test_health_check_timestamp_format(self):
        """
        Test that health check timestamp is in ISO format.
        
        Requirements:
            - 22.6: Include timestamp
        """
        response = self.client.get('/v1/health/')
        data = response.json()
        
        # Verify timestamp is present and in ISO format
        self.assertIn('timestamp', data)
        timestamp = data['timestamp']
        
        # Should be able to parse as ISO format
        from datetime import datetime
        try:
            datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            self.fail(f"Timestamp '{timestamp}' is not in valid ISO format")
    
    def test_health_check_status_values(self):
        """
        Test that health check status is either 'healthy' or 'unhealthy'.
        
        Requirements:
            - 22.4: Return "healthy" status
            - 22.5: Return "unhealthy" status
        """
        response = self.client.get('/v1/health/')
        data = response.json()
        
        self.assertIn(data['status'], ['healthy', 'unhealthy'])
    
    @patch('django.db.connection.ensure_connection')
    @patch('django.core.cache.cache.set')
    def test_health_check_multiple_failures(self, mock_cache_set, mock_ensure_connection):
        """
        Test that health check reports all failures when multiple dependencies are down.
        
        Requirements:
            - 22.2: Check PostgreSQL connectivity
            - 22.3: Check Valkey connectivity
            - 22.5: Return HTTP 503 when unhealthy
        """
        # Simulate both database and cache failures
        mock_ensure_connection.side_effect = Exception('Database failed')
        mock_cache_set.side_effect = Exception('Cache failed')
        
        response = self.client.get('/v1/health/')
        
        # Should return 503
        self.assertEqual(response.status_code, 503)
        
        data = response.json()
        self.assertEqual(data['status'], 'unhealthy')
        self.assertIn('unhealthy', data['checks']['database'])
        self.assertIn('unhealthy', data['checks']['cache'])
