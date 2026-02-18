"""
Tests for HTTPS enforcement middleware and configuration.

Requirements: 6.4, 6.11, 6.12
"""

import pytest
from django.test import RequestFactory, override_settings
from django.http import HttpResponse

from infrastructure.https_enforcement import (
    HTTPSEnforcementMiddleware,
    validate_https_configuration,
    get_https_status
)


class TestHTTPSEnforcementMiddleware:
    """Test HTTPS enforcement middleware."""
    
    @pytest.fixture
    def factory(self):
        """Create request factory."""
        return RequestFactory()
    
    @pytest.fixture
    def middleware(self):
        """Create middleware instance."""
        def get_response(request):
            return HttpResponse("OK")
        return HTTPSEnforcementMiddleware(get_response)
    
    @override_settings(SECURE_SSL_REDIRECT=True, ALLOWED_HOSTS=['example.com'])
    def test_http_redirects_to_https(self, factory, middleware):
        """Test that HTTP requests are redirected to HTTPS."""
        request = factory.get('/api/stories/')
        request.META['HTTP_HOST'] = 'example.com'
        
        response = middleware.process_request(request)
        
        assert response is not None
        assert response.status_code == 301
        assert response['Location'] == 'https://example.com/api/stories/'
    
    @override_settings(SECURE_SSL_REDIRECT=True)
    def test_https_not_redirected(self, factory, middleware):
        """Test that HTTPS requests are not redirected."""
        request = factory.get('/api/stories/', secure=True)
        
        response = middleware.process_request(request)
        
        assert response is None
    
    @override_settings(SECURE_SSL_REDIRECT=True)
    def test_x_forwarded_proto_https(self, factory, middleware):
        """Test that X-Forwarded-Proto: https is recognized."""
        request = factory.get('/api/stories/')
        request.META['HTTP_X_FORWARDED_PROTO'] = 'https'
        
        response = middleware.process_request(request)
        
        assert response is None
    
    @override_settings(SECURE_SSL_REDIRECT=True, HTTPS_EXEMPT_PATHS=['/health'])
    def test_exempt_paths_not_redirected(self, factory, middleware):
        """Test that exempt paths are not redirected."""
        request = factory.get('/health')
        
        response = middleware.process_request(request)
        
        assert response is None
    
    @override_settings(
        SECURE_SSL_REDIRECT=True,
        SECURE_HSTS_SECONDS=31536000,
        SECURE_HSTS_INCLUDE_SUBDOMAINS=True,
        SECURE_HSTS_PRELOAD=True
    )
    def test_hsts_headers_added(self, factory, middleware):
        """Test that HSTS headers are added to HTTPS responses."""
        request = factory.get('/api/stories/', secure=True)
        response = HttpResponse("OK")
        
        response = middleware.process_response(request, response)
        
        assert 'Strict-Transport-Security' in response
        hsts_value = response['Strict-Transport-Security']
        assert 'max-age=31536000' in hsts_value
        assert 'includeSubDomains' in hsts_value
        assert 'preload' in hsts_value
    
    @override_settings(SECURE_SSL_REDIRECT=True)
    def test_hsts_not_added_to_http(self, factory, middleware):
        """Test that HSTS headers are not added to HTTP responses."""
        request = factory.get('/api/stories/')
        response = HttpResponse("OK")
        
        response = middleware.process_response(request, response)
        
        assert 'Strict-Transport-Security' not in response
    
    @override_settings(SECURE_SSL_REDIRECT=True, ALLOWED_HOSTS=['example.com'])
    def test_redirect_preserves_query_string(self, factory, middleware):
        """Test that query strings are preserved in redirects."""
        request = factory.get('/api/stories/?page=2&limit=10')
        request.META['HTTP_HOST'] = 'example.com'
        
        response = middleware.process_request(request)
        
        assert response is not None
        assert response['Location'] == 'https://example.com/api/stories/?page=2&limit=10'
    
    @override_settings(SECURE_SSL_REDIRECT=True, ALLOWED_HOSTS=['example.com'])
    def test_redirect_removes_port_80(self, factory, middleware):
        """Test that port 80 is removed from redirect URL."""
        request = factory.get('/api/stories/')
        request.META['HTTP_HOST'] = 'example.com:80'
        
        response = middleware.process_request(request)
        
        assert response is not None
        assert response['Location'] == 'https://example.com/api/stories/'


class TestHTTPSConfiguration:
    """Test HTTPS configuration validation."""
    
    @override_settings(
        ENVIRONMENT='production',
        SECURE_SSL_REDIRECT=True,
        SECURE_HSTS_SECONDS=31536000,
        SESSION_COOKIE_SECURE=True,
        CSRF_COOKIE_SECURE=True
    )
    def test_valid_production_configuration(self):
        """Test that valid production configuration passes validation."""
        # Should not raise exception
        validate_https_configuration()
    
    @override_settings(
        ENVIRONMENT='production',
        SECURE_SSL_REDIRECT=False
    )
    def test_missing_ssl_redirect_fails(self):
        """Test that missing SSL redirect fails validation."""
        from django.core.exceptions import ImproperlyConfigured
        
        with pytest.raises(ImproperlyConfigured, match="SECURE_SSL_REDIRECT"):
            validate_https_configuration()
    
    @override_settings(
        ENVIRONMENT='production',
        SECURE_SSL_REDIRECT=True,
        SESSION_COOKIE_SECURE=False
    )
    def test_insecure_session_cookie_fails(self):
        """Test that insecure session cookie fails validation."""
        from django.core.exceptions import ImproperlyConfigured
        
        with pytest.raises(ImproperlyConfigured, match="SESSION_COOKIE_SECURE"):
            validate_https_configuration()
    
    @override_settings(
        ENVIRONMENT='production',
        SECURE_SSL_REDIRECT=True,
        SESSION_COOKIE_SECURE=True,
        CSRF_COOKIE_SECURE=False
    )
    def test_insecure_csrf_cookie_fails(self):
        """Test that insecure CSRF cookie fails validation."""
        from django.core.exceptions import ImproperlyConfigured
        
        with pytest.raises(ImproperlyConfigured, match="CSRF_COOKIE_SECURE"):
            validate_https_configuration()
    
    @override_settings(ENVIRONMENT='development')
    def test_development_skips_validation(self):
        """Test that development environment skips validation."""
        # Should not raise exception even with invalid config
        validate_https_configuration()
    
    @override_settings(
        SECURE_SSL_REDIRECT=True,
        SECURE_HSTS_SECONDS=31536000,
        SECURE_HSTS_INCLUDE_SUBDOMAINS=True,
        SECURE_HSTS_PRELOAD=True,
        SESSION_COOKIE_SECURE=True,
        CSRF_COOKIE_SECURE=True,
        ENVIRONMENT='production'
    )
    def test_get_https_status(self):
        """Test getting HTTPS configuration status."""
        status = get_https_status()
        
        assert status['enforce_https'] is True
        assert status['hsts_enabled'] is True
        assert status['hsts_seconds'] == 31536000
        assert status['hsts_include_subdomains'] is True
        assert status['hsts_preload'] is True
        assert status['session_cookie_secure'] is True
        assert status['csrf_cookie_secure'] is True
        assert status['environment'] == 'production'
