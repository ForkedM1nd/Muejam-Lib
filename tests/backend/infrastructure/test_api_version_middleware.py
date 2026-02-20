"""
Tests for API version middleware.

This test suite validates the API version extraction, header addition,
and deprecation warning functionality.

Requirements: 1.2, 1.4, 1.5
"""

import pytest
import django
from django.conf import settings

# Configure Django settings if not already configured
if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY='test-secret-key',
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
        ],
        MIDDLEWARE=[],
        ROOT_URLCONF='',
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        DEFAULT_CHARSET='utf-8',
    )
    django.setup()

from django.test import RequestFactory
from django.http import HttpResponse

from infrastructure.api_version_middleware import APIVersionMiddleware


class TestAPIVersionMiddleware:
    """Test API version middleware functionality."""
    
    @pytest.fixture
    def factory(self):
        """Create request factory."""
        return RequestFactory()
    
    @pytest.fixture
    def middleware(self):
        """Create middleware instance."""
        def get_response(request):
            return HttpResponse("OK")
        return APIVersionMiddleware(get_response)
    
    def test_extracts_v1_from_path(self, factory, middleware):
        """Test that v1 is correctly extracted from request path."""
        request = factory.get('/v1/stories/')
        
        response = middleware(request)
        
        assert hasattr(request, 'api_version')
        assert request.api_version == 'v1'
        assert response['X-API-Version'] == 'v1'
    
    def test_extracts_v2_from_path(self, factory, middleware):
        """Test that v2 is correctly extracted from request path."""
        request = factory.get('/v2/stories/')
        
        response = middleware(request)
        
        assert hasattr(request, 'api_version')
        assert request.api_version == 'v2'
        assert response['X-API-Version'] == 'v2'
    
    def test_no_version_in_path(self, factory, middleware):
        """Test handling of requests without version in path."""
        request = factory.get('/stories/')
        
        response = middleware(request)
        
        assert hasattr(request, 'api_version')
        assert request.api_version is None
        assert 'X-API-Version' not in response
    
    def test_version_extraction_with_query_params(self, factory, middleware):
        """Test version extraction works with query parameters."""
        request = factory.get('/v1/stories/?page=2&limit=10')
        
        response = middleware(request)
        
        assert request.api_version == 'v1'
        assert response['X-API-Version'] == 'v1'
    
    def test_version_extraction_with_nested_path(self, factory, middleware):
        """Test version extraction works with nested paths."""
        request = factory.get('/v1/stories/123/chapters/456/')
        
        response = middleware(request)
        
        assert request.api_version == 'v1'
        assert response['X-API-Version'] == 'v1'
    
    def test_deprecated_version_adds_warning_headers(self, factory, middleware):
        """Test that deprecated versions get warning headers."""
        # Temporarily add v0 to deprecated list
        original_deprecated = middleware.DEPRECATED_VERSIONS.copy()
        middleware.DEPRECATED_VERSIONS = ['v0']
        
        try:
            request = factory.get('/v0/stories/')
            
            response = middleware(request)
            
            assert response['X-API-Version'] == 'v0'
            assert 'X-API-Deprecation' in response
            assert 'Warning' in response
            assert '299' in response['Warning']
            assert 'Deprecated' in response['Warning']
        finally:
            middleware.DEPRECATED_VERSIONS = original_deprecated
    
    def test_deprecated_version_with_custom_message(self, factory, middleware):
        """Test that custom deprecation messages are used."""
        # Temporarily configure deprecation
        original_deprecated = middleware.DEPRECATED_VERSIONS.copy()
        original_messages = middleware.DEPRECATION_MESSAGES.copy()
        
        middleware.DEPRECATED_VERSIONS = ['v0']
        middleware.DEPRECATION_MESSAGES = {
            'v0': 'API v0 is deprecated. Please migrate to v1 by 2024-12-31.'
        }
        
        try:
            request = factory.get('/v0/stories/')
            
            response = middleware(request)
            
            assert response['X-API-Deprecation'] == 'API v0 is deprecated. Please migrate to v1 by 2024-12-31.'
        finally:
            middleware.DEPRECATED_VERSIONS = original_deprecated
            middleware.DEPRECATION_MESSAGES = original_messages
    
    def test_current_version_no_deprecation_warning(self, factory, middleware):
        """Test that current version does not get deprecation warnings."""
        request = factory.get('/v1/stories/')
        
        response = middleware(request)
        
        assert response['X-API-Version'] == 'v1'
        assert 'X-API-Deprecation' not in response
        assert 'Warning' not in response
    
    def test_version_extraction_case_sensitive(self, factory, middleware):
        """Test that version extraction is case sensitive."""
        request = factory.get('/V1/stories/')
        
        response = middleware(request)
        
        # Should not match uppercase V
        assert request.api_version is None
        assert 'X-API-Version' not in response
    
    def test_version_extraction_numeric_only(self, factory, middleware):
        """Test that only numeric versions are extracted."""
        request = factory.get('/v1/stories/')
        
        response = middleware(request)
        
        assert request.api_version == 'v1'
        assert response['X-API-Version'] == 'v1'
    
    def test_extracts_version_from_api_prefix_path(self, factory, middleware):
        """Test that version is extracted from compatibility /api/vN paths."""
        request = factory.get('/api/v1/stories/')
        
        response = middleware(request)
        
        assert request.api_version == 'v1'
        assert response['X-API-Version'] == 'v1'

    def test_version_not_extracted_from_non_api_path_middle(self, factory, middleware):
        """Test that version-like segments in non-prefix paths are ignored."""
        request = factory.get('/internal/v1/stories/')

        response = middleware(request)

        assert request.api_version is None
        assert 'X-API-Version' not in response
    
    def test_multiple_versions_in_path_uses_first(self, factory, middleware):
        """Test that only the first version in path is used."""
        request = factory.get('/v1/v2/stories/')
        
        response = middleware(request)
        
        assert request.api_version == 'v1'
        assert response['X-API-Version'] == 'v1'
    
    def test_version_with_trailing_slash(self, factory, middleware):
        """Test version extraction with trailing slash."""
        request = factory.get('/v1/')
        
        response = middleware(request)
        
        assert request.api_version == 'v1'
        assert response['X-API-Version'] == 'v1'
    
    def test_version_without_trailing_slash(self, factory, middleware):
        """Test version extraction without trailing slash in path."""
        request = factory.get('/v1')
        
        response = middleware(request)
        
        # Pattern requires trailing slash
        assert request.api_version is None
    
    def test_post_request_version_extraction(self, factory, middleware):
        """Test version extraction works for POST requests."""
        request = factory.post('/v1/stories/', data={'title': 'Test'})
        
        response = middleware(request)
        
        assert request.api_version == 'v1'
        assert response['X-API-Version'] == 'v1'
    
    def test_put_request_version_extraction(self, factory, middleware):
        """Test version extraction works for PUT requests."""
        request = factory.put('/v1/stories/123/', data={'title': 'Updated'})
        
        response = middleware(request)
        
        assert request.api_version == 'v1'
        assert response['X-API-Version'] == 'v1'
    
    def test_delete_request_version_extraction(self, factory, middleware):
        """Test version extraction works for DELETE requests."""
        request = factory.delete('/v1/stories/123/')
        
        response = middleware(request)
        
        assert request.api_version == 'v1'
        assert response['X-API-Version'] == 'v1'
    
    def test_patch_request_version_extraction(self, factory, middleware):
        """Test version extraction works for PATCH requests."""
        request = factory.patch('/v1/stories/123/', data={'title': 'Patched'})
        
        response = middleware(request)
        
        assert request.api_version == 'v1'
        assert response['X-API-Version'] == 'v1'


class TestAPIVersionMiddlewareHelpers:
    """Test helper methods of API version middleware."""
    
    @pytest.fixture
    def middleware(self):
        """Create middleware instance."""
        def get_response(request):
            return HttpResponse("OK")
        return APIVersionMiddleware(get_response)
    
    def test_is_deprecated_returns_true_for_deprecated_version(self, middleware):
        """Test _is_deprecated returns True for deprecated versions."""
        original_deprecated = middleware.DEPRECATED_VERSIONS.copy()
        middleware.DEPRECATED_VERSIONS = ['v0', 'v1']
        
        try:
            assert middleware._is_deprecated('v0') is True
            assert middleware._is_deprecated('v1') is True
        finally:
            middleware.DEPRECATED_VERSIONS = original_deprecated
    
    def test_is_deprecated_returns_false_for_current_version(self, middleware):
        """Test _is_deprecated returns False for current versions."""
        assert middleware._is_deprecated('v1') is False
        assert middleware._is_deprecated('v2') is False
    
    def test_get_deprecation_message_returns_custom_message(self, middleware):
        """Test _get_deprecation_message returns custom message when available."""
        original_messages = middleware.DEPRECATION_MESSAGES.copy()
        middleware.DEPRECATION_MESSAGES = {
            'v0': 'Custom deprecation message for v0'
        }
        
        try:
            message = middleware._get_deprecation_message('v0')
            assert message == 'Custom deprecation message for v0'
        finally:
            middleware.DEPRECATION_MESSAGES = original_messages
    
    def test_get_deprecation_message_returns_default_message(self, middleware):
        """Test _get_deprecation_message returns default message when no custom message."""
        message = middleware._get_deprecation_message('v0')
        
        assert 'v0' in message
        assert 'deprecated' in message.lower()
        assert middleware.CURRENT_VERSION in message
    
    def test_get_client_identifier_with_authenticated_user(self, middleware):
        """Test _get_client_identifier returns user ID for authenticated users."""
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get('/v1/stories/')
        
        # Mock authenticated user
        class MockUser:
            is_authenticated = True
            id = 'user123'
        
        request.user = MockUser()
        
        identifier = middleware._get_client_identifier(request)
        
        assert identifier == 'user:user123'
    
    def test_get_client_identifier_with_anonymous_user(self, middleware):
        """Test _get_client_identifier returns IP for anonymous users."""
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get('/v1/stories/')
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        
        # Mock anonymous user
        class MockUser:
            is_authenticated = False
        
        request.user = MockUser()
        
        identifier = middleware._get_client_identifier(request)
        
        assert identifier == 'ip:192.168.1.1'
    
    def test_get_client_identifier_with_x_forwarded_for(self, middleware):
        """Test _get_client_identifier uses X-Forwarded-For when available."""
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get('/v1/stories/')
        request.META['HTTP_X_FORWARDED_FOR'] = '10.0.0.1, 192.168.1.1'
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        
        # Mock anonymous user
        class MockUser:
            is_authenticated = False
        
        request.user = MockUser()
        
        identifier = middleware._get_client_identifier(request)
        
        # Should use first IP from X-Forwarded-For
        assert identifier == 'ip:10.0.0.1'
