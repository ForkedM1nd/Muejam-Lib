"""
Tests for client type middleware.

This test suite validates the client type extraction, validation,
and logging functionality.

Requirements: 2.1, 2.2, 2.3, 2.5
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

from infrastructure.client_type_middleware import ClientTypeMiddleware


class TestClientTypeMiddleware:
    """Test client type middleware functionality."""
    
    @pytest.fixture
    def factory(self):
        """Create request factory."""
        return RequestFactory()
    
    @pytest.fixture
    def middleware(self):
        """Create middleware instance."""
        def get_response(request):
            return HttpResponse("OK")
        return ClientTypeMiddleware(get_response)
    
    def test_extracts_web_client_type(self, factory, middleware):
        """Test that 'web' client type is correctly extracted."""
        request = factory.get('/v1/stories/', HTTP_X_CLIENT_TYPE='web')
        
        response = middleware(request)
        
        assert hasattr(request, 'client_type')
        assert request.client_type == 'web'
    
    def test_extracts_mobile_ios_client_type(self, factory, middleware):
        """Test that 'mobile-ios' client type is correctly extracted."""
        request = factory.get('/v1/stories/', HTTP_X_CLIENT_TYPE='mobile-ios')
        
        response = middleware(request)
        
        assert hasattr(request, 'client_type')
        assert request.client_type == 'mobile-ios'
    
    def test_extracts_mobile_android_client_type(self, factory, middleware):
        """Test that 'mobile-android' client type is correctly extracted."""
        request = factory.get('/v1/stories/', HTTP_X_CLIENT_TYPE='mobile-android')
        
        response = middleware(request)
        
        assert hasattr(request, 'client_type')
        assert request.client_type == 'mobile-android'
    
    def test_defaults_to_web_when_header_missing(self, factory, middleware):
        """Test that client type defaults to 'web' when header is missing."""
        request = factory.get('/v1/stories/')
        
        response = middleware(request)
        
        assert hasattr(request, 'client_type')
        assert request.client_type == 'web'
    
    def test_defaults_to_web_when_header_empty(self, factory, middleware):
        """Test that client type defaults to 'web' when header is empty."""
        request = factory.get('/v1/stories/', HTTP_X_CLIENT_TYPE='')
        
        response = middleware(request)
        
        assert hasattr(request, 'client_type')
        assert request.client_type == 'web'
    
    def test_defaults_to_web_when_header_whitespace(self, factory, middleware):
        """Test that client type defaults to 'web' when header is whitespace."""
        request = factory.get('/v1/stories/', HTTP_X_CLIENT_TYPE='   ')
        
        response = middleware(request)
        
        assert hasattr(request, 'client_type')
        assert request.client_type == 'web'
    
    def test_invalid_client_type_defaults_to_web(self, factory, middleware):
        """Test that invalid client type defaults to 'web'."""
        request = factory.get('/v1/stories/', HTTP_X_CLIENT_TYPE='invalid-type')
        
        response = middleware(request)
        
        assert hasattr(request, 'client_type')
        assert request.client_type == 'web'
    
    def test_case_insensitive_client_type(self, factory, middleware):
        """Test that client type header is case-insensitive."""
        request = factory.get('/v1/stories/', HTTP_X_CLIENT_TYPE='MOBILE-IOS')
        
        response = middleware(request)
        
        assert request.client_type == 'mobile-ios'
    
    def test_mixed_case_client_type(self, factory, middleware):
        """Test that mixed case client type is normalized."""
        request = factory.get('/v1/stories/', HTTP_X_CLIENT_TYPE='Mobile-Android')
        
        response = middleware(request)
        
        assert request.client_type == 'mobile-android'
    
    def test_client_type_with_extra_whitespace(self, factory, middleware):
        """Test that client type with extra whitespace is trimmed."""
        request = factory.get('/v1/stories/', HTTP_X_CLIENT_TYPE='  mobile-ios  ')
        
        response = middleware(request)
        
        assert request.client_type == 'mobile-ios'
    
    def test_client_type_available_in_request_context(self, factory, middleware):
        """Test that client_type is available in request context for views."""
        request = factory.get('/v1/stories/', HTTP_X_CLIENT_TYPE='mobile-ios')
        
        middleware(request)
        
        # Verify client_type attribute is set on request
        assert hasattr(request, 'client_type')
        assert request.client_type == 'mobile-ios'
    
    def test_post_request_client_type_extraction(self, factory, middleware):
        """Test client type extraction works for POST requests."""
        request = factory.post(
            '/v1/stories/',
            data={'title': 'Test'},
            HTTP_X_CLIENT_TYPE='mobile-android'
        )
        
        response = middleware(request)
        
        assert request.client_type == 'mobile-android'
    
    def test_put_request_client_type_extraction(self, factory, middleware):
        """Test client type extraction works for PUT requests."""
        request = factory.put(
            '/v1/stories/123/',
            data={'title': 'Updated'},
            HTTP_X_CLIENT_TYPE='mobile-ios'
        )
        
        response = middleware(request)
        
        assert request.client_type == 'mobile-ios'
    
    def test_delete_request_client_type_extraction(self, factory, middleware):
        """Test client type extraction works for DELETE requests."""
        request = factory.delete(
            '/v1/stories/123/',
            HTTP_X_CLIENT_TYPE='web'
        )
        
        response = middleware(request)
        
        assert request.client_type == 'web'
    
    def test_patch_request_client_type_extraction(self, factory, middleware):
        """Test client type extraction works for PATCH requests."""
        request = factory.patch(
            '/v1/stories/123/',
            data={'title': 'Patched'},
            HTTP_X_CLIENT_TYPE='mobile-android'
        )
        
        response = middleware(request)
        
        assert request.client_type == 'mobile-android'
    
    def test_client_type_with_query_parameters(self, factory, middleware):
        """Test client type extraction works with query parameters."""
        request = factory.get(
            '/v1/stories/?page=2&limit=10',
            HTTP_X_CLIENT_TYPE='mobile-ios'
        )
        
        response = middleware(request)
        
        assert request.client_type == 'mobile-ios'
    
    def test_client_type_with_nested_path(self, factory, middleware):
        """Test client type extraction works with nested paths."""
        request = factory.get(
            '/v1/stories/123/chapters/456/',
            HTTP_X_CLIENT_TYPE='mobile-android'
        )
        
        response = middleware(request)
        
        assert request.client_type == 'mobile-android'


class TestClientTypeMiddlewareHelpers:
    """Test helper methods of client type middleware."""
    
    @pytest.fixture
    def middleware(self):
        """Create middleware instance."""
        def get_response(request):
            return HttpResponse("OK")
        return ClientTypeMiddleware(get_response)
    
    @pytest.fixture
    def factory(self):
        """Create request factory."""
        return RequestFactory()
    
    def test_is_mobile_client_returns_true_for_ios(self, middleware):
        """Test _is_mobile_client returns True for mobile-ios."""
        assert middleware._is_mobile_client('mobile-ios') is True
    
    def test_is_mobile_client_returns_true_for_android(self, middleware):
        """Test _is_mobile_client returns True for mobile-android."""
        assert middleware._is_mobile_client('mobile-android') is True
    
    def test_is_mobile_client_returns_false_for_web(self, middleware):
        """Test _is_mobile_client returns False for web."""
        assert middleware._is_mobile_client('web') is False
    
    def test_extract_client_type_with_valid_web(self, middleware, factory):
        """Test _extract_client_type with valid 'web' header."""
        request = factory.get('/v1/stories/', HTTP_X_CLIENT_TYPE='web')
        
        client_type = middleware._extract_client_type(request)
        
        assert client_type == 'web'
    
    def test_extract_client_type_with_valid_mobile_ios(self, middleware, factory):
        """Test _extract_client_type with valid 'mobile-ios' header."""
        request = factory.get('/v1/stories/', HTTP_X_CLIENT_TYPE='mobile-ios')
        
        client_type = middleware._extract_client_type(request)
        
        assert client_type == 'mobile-ios'
    
    def test_extract_client_type_with_valid_mobile_android(self, middleware, factory):
        """Test _extract_client_type with valid 'mobile-android' header."""
        request = factory.get('/v1/stories/', HTTP_X_CLIENT_TYPE='mobile-android')
        
        client_type = middleware._extract_client_type(request)
        
        assert client_type == 'mobile-android'
    
    def test_extract_client_type_with_missing_header(self, middleware, factory):
        """Test _extract_client_type with missing header returns default."""
        request = factory.get('/v1/stories/')
        
        client_type = middleware._extract_client_type(request)
        
        assert client_type == middleware.DEFAULT_CLIENT_TYPE
    
    def test_extract_client_type_with_invalid_value(self, middleware, factory):
        """Test _extract_client_type with invalid value returns default."""
        request = factory.get('/v1/stories/', HTTP_X_CLIENT_TYPE='invalid-client')
        
        client_type = middleware._extract_client_type(request)
        
        assert client_type == middleware.DEFAULT_CLIENT_TYPE
    
    def test_extract_client_type_normalizes_case(self, middleware, factory):
        """Test _extract_client_type normalizes case to lowercase."""
        request = factory.get('/v1/stories/', HTTP_X_CLIENT_TYPE='MOBILE-IOS')
        
        client_type = middleware._extract_client_type(request)
        
        assert client_type == 'mobile-ios'
    
    def test_extract_client_type_strips_whitespace(self, middleware, factory):
        """Test _extract_client_type strips leading/trailing whitespace."""
        request = factory.get('/v1/stories/', HTTP_X_CLIENT_TYPE='  mobile-android  ')
        
        client_type = middleware._extract_client_type(request)
        
        assert client_type == 'mobile-android'
    
    def test_allowed_client_types_constant(self, middleware):
        """Test that ALLOWED_CLIENT_TYPES contains expected values."""
        assert 'web' in middleware.ALLOWED_CLIENT_TYPES
        assert 'mobile-ios' in middleware.ALLOWED_CLIENT_TYPES
        assert 'mobile-android' in middleware.ALLOWED_CLIENT_TYPES
        assert len(middleware.ALLOWED_CLIENT_TYPES) == 3
    
    def test_default_client_type_constant(self, middleware):
        """Test that DEFAULT_CLIENT_TYPE is 'web'."""
        assert middleware.DEFAULT_CLIENT_TYPE == 'web'


class TestClientTypeMiddlewareEdgeCases:
    """Test edge cases for client type middleware."""
    
    @pytest.fixture
    def factory(self):
        """Create request factory."""
        return RequestFactory()
    
    @pytest.fixture
    def middleware(self):
        """Create middleware instance."""
        def get_response(request):
            return HttpResponse("OK")
        return ClientTypeMiddleware(get_response)
    
    def test_special_characters_in_client_type(self, factory, middleware):
        """Test that special characters in client type are handled."""
        request = factory.get('/v1/stories/', HTTP_X_CLIENT_TYPE='mobile@ios')
        
        response = middleware(request)
        
        # Should default to web for invalid format
        assert request.client_type == 'web'
    
    def test_numeric_client_type(self, factory, middleware):
        """Test that numeric client type is handled."""
        request = factory.get('/v1/stories/', HTTP_X_CLIENT_TYPE='12345')
        
        response = middleware(request)
        
        # Should default to web for invalid format
        assert request.client_type == 'web'
    
    def test_very_long_client_type(self, factory, middleware):
        """Test that very long client type is handled."""
        long_type = 'a' * 1000
        request = factory.get('/v1/stories/', HTTP_X_CLIENT_TYPE=long_type)
        
        response = middleware(request)
        
        # Should default to web for invalid format
        assert request.client_type == 'web'
    
    def test_client_type_with_unicode_characters(self, factory, middleware):
        """Test that unicode characters in client type are handled."""
        request = factory.get('/v1/stories/', HTTP_X_CLIENT_TYPE='mobile-🍎')
        
        response = middleware(request)
        
        # Should default to web for invalid format
        assert request.client_type == 'web'
    
    def test_client_type_with_sql_injection_attempt(self, factory, middleware):
        """Test that SQL injection attempts in client type are handled."""
        request = factory.get('/v1/stories/', HTTP_X_CLIENT_TYPE="web'; DROP TABLE users; --")
        
        response = middleware(request)
        
        # Should default to web for invalid format
        assert request.client_type == 'web'
    
    def test_client_type_with_xss_attempt(self, factory, middleware):
        """Test that XSS attempts in client type are handled."""
        request = factory.get('/v1/stories/', HTTP_X_CLIENT_TYPE='<script>alert("xss")</script>')
        
        response = middleware(request)
        
        # Should default to web for invalid format
        assert request.client_type == 'web'
    
    def test_multiple_client_type_headers(self, factory, middleware):
        """Test behavior when multiple X-Client-Type headers are present."""
        # Django's test client doesn't support multiple headers with same name easily,
        # but we can test that the middleware handles the first value
        request = factory.get('/v1/stories/', HTTP_X_CLIENT_TYPE='mobile-ios')
        
        response = middleware(request)
        
        assert request.client_type == 'mobile-ios'
    
    def test_client_type_persists_through_middleware_chain(self, factory):
        """Test that client_type persists through middleware chain."""
        call_order = []
        
        def inner_middleware(request):
            call_order.append('inner')
            # Verify client_type is available in inner middleware
            assert hasattr(request, 'client_type')
            assert request.client_type == 'mobile-ios'
            return HttpResponse("OK")
        
        middleware = ClientTypeMiddleware(inner_middleware)
        request = factory.get('/v1/stories/', HTTP_X_CLIENT_TYPE='mobile-ios')
        
        response = middleware(request)
        
        assert 'inner' in call_order
        assert request.client_type == 'mobile-ios'
