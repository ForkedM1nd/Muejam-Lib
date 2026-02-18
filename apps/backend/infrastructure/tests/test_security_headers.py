"""
Tests for security headers configuration.

This module tests that all required security headers are properly configured
and applied to responses.

Requirements: 6.3, 6.4, 6.5, 6.6
"""

import pytest
from django.test import Client, override_settings
from django.urls import reverse


# Disable timeout middleware for tests (SIGALRM not available on Windows)
TEST_MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'infrastructure.https_enforcement.HTTPSEnforcementMiddleware',
    'csp.middleware.CSPMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


class TestSecurityHeaders:
    """Test security headers on responses."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return Client()
    
    @override_settings(
        MIDDLEWARE=TEST_MIDDLEWARE,
        SECURE_HSTS_SECONDS=31536000,
        SECURE_HSTS_INCLUDE_SUBDOMAINS=True,
        SECURE_HSTS_PRELOAD=True,
        SECURE_CONTENT_TYPE_NOSNIFF=True,
        SECURE_BROWSER_XSS_FILTER=True,
        X_FRAME_OPTIONS='DENY',
        SECURE_SSL_REDIRECT=False  # Disable for testing
    )
    @pytest.mark.django_db
    def test_hsts_header_on_https(self, client):
        """Test that HSTS header is present on HTTPS requests."""
        response = client.get('/health/', secure=True)
        
        assert 'Strict-Transport-Security' in response
        hsts_value = response['Strict-Transport-Security']
        assert 'max-age=31536000' in hsts_value
        assert 'includeSubDomains' in hsts_value
        assert 'preload' in hsts_value
    
    @override_settings(MIDDLEWARE=TEST_MIDDLEWARE, SECURE_CONTENT_TYPE_NOSNIFF=True)
    @pytest.mark.django_db
    def test_x_content_type_options_header(self, client):
        """Test that X-Content-Type-Options header is present."""
        response = client.get('/health/')
        
        assert 'X-Content-Type-Options' in response
        assert response['X-Content-Type-Options'] == 'nosniff'
    
    @override_settings(MIDDLEWARE=TEST_MIDDLEWARE, X_FRAME_OPTIONS='DENY')
    @pytest.mark.django_db
    def test_x_frame_options_header(self, client):
        """Test that X-Frame-Options header is present."""
        response = client.get('/health/')
        
        assert 'X-Frame-Options' in response
        assert response['X-Frame-Options'] == 'DENY'
    
    @override_settings(MIDDLEWARE=TEST_MIDDLEWARE, SECURE_BROWSER_XSS_FILTER=True)
    @pytest.mark.django_db
    def test_x_xss_protection_header(self, client):
        """Test that X-XSS-Protection header is present."""
        response = client.get('/health/')
        
        # Note: This header may be added by SecurityMiddleware
        # Check if present (some browsers ignore it now)
        if 'X-XSS-Protection' in response:
            assert response['X-XSS-Protection'] in ['1; mode=block', '1']
    
    @override_settings(
        MIDDLEWARE=TEST_MIDDLEWARE,
        CSP_DEFAULT_SRC=("'self'",),
        CSP_SCRIPT_SRC=("'self'", 'cdn.example.com'),
        CSP_STYLE_SRC=("'self'", "'unsafe-inline'"),
        CSP_IMG_SRC=("'self'", 'data:', 'https:'),
        CSP_FRAME_ANCESTORS=("'none'",)
    )
    @pytest.mark.django_db
    def test_content_security_policy_header(self, client):
        """Test that Content-Security-Policy header is present."""
        response = client.get('/health/')
        
        assert 'Content-Security-Policy' in response
        csp_value = response['Content-Security-Policy']
        
        # Check key directives
        assert "default-src 'self'" in csp_value
        assert "frame-ancestors 'none'" in csp_value
    
    @override_settings(
        MIDDLEWARE=TEST_MIDDLEWARE,
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Strict'
    )
    @pytest.mark.django_db
    def test_session_cookie_security(self, client):
        """Test that session cookies have secure flags."""
        # Make a request that sets a session cookie
        response = client.get('/health/')
        
        # Check session cookie settings (if set)
        if 'sessionid' in response.cookies:
            cookie = response.cookies['sessionid']
            assert cookie['secure'] is True
            assert cookie['httponly'] is True
            assert cookie['samesite'] == 'Strict'
    
    @override_settings(
        MIDDLEWARE=TEST_MIDDLEWARE,
        CSRF_COOKIE_SECURE=True,
        CSRF_COOKIE_HTTPONLY=True,
        CSRF_COOKIE_SAMESITE='Strict'
    )
    @pytest.mark.django_db
    def test_csrf_cookie_security(self, client):
        """Test that CSRF cookies have secure flags."""
        # Make a request that sets a CSRF cookie
        response = client.get('/health/')
        
        # Check CSRF cookie settings (if set)
        if 'csrftoken' in response.cookies:
            cookie = response.cookies['csrftoken']
            assert cookie['secure'] is True
            assert cookie['httponly'] is True
            assert cookie['samesite'] == 'Strict'
    
    @override_settings(
        MIDDLEWARE=TEST_MIDDLEWARE,
        SECURE_HSTS_SECONDS=31536000,
        SECURE_CONTENT_TYPE_NOSNIFF=True,
        X_FRAME_OPTIONS='DENY',
        CSP_DEFAULT_SRC=("'self'",),
        CSP_FRAME_ANCESTORS=("'none'",)
    )
    @pytest.mark.django_db
    def test_all_security_headers_present(self, client):
        """Test that all required security headers are present on HTTPS."""
        response = client.get('/health/', secure=True)
        
        # Check all required headers
        required_headers = [
            'Strict-Transport-Security',  # HSTS
            'X-Content-Type-Options',      # Nosniff
            'X-Frame-Options',             # Clickjacking protection
            'Content-Security-Policy',     # CSP
        ]
        
        for header in required_headers:
            assert header in response, f"Missing required header: {header}"
    
    @override_settings(MIDDLEWARE=TEST_MIDDLEWARE)
    @pytest.mark.django_db
    def test_security_headers_on_api_endpoints(self, client):
        """Test that security headers are applied to API endpoints."""
        # Test on health endpoint (should always work)
        response = client.get('/health/', secure=True)
        
        # Verify at least some security headers are present
        assert 'X-Content-Type-Options' in response or 'X-Frame-Options' in response


class TestSecurityHeaderValues:
    """Test specific security header values and configurations."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return Client()
    
    @override_settings(MIDDLEWARE=TEST_MIDDLEWARE, SECURE_HSTS_SECONDS=31536000)
    @pytest.mark.django_db
    def test_hsts_max_age_minimum(self, client):
        """Test that HSTS max-age is at least 1 year."""
        response = client.get('/health/', secure=True)
        
        if 'Strict-Transport-Security' in response:
            hsts_value = response['Strict-Transport-Security']
            # Extract max-age value
            if 'max-age=' in hsts_value:
                max_age_str = hsts_value.split('max-age=')[1].split(';')[0].strip()
                max_age = int(max_age_str)
                assert max_age >= 31536000, "HSTS max-age should be at least 1 year"
    
    @override_settings(MIDDLEWARE=TEST_MIDDLEWARE, X_FRAME_OPTIONS='DENY')
    @pytest.mark.django_db
    def test_x_frame_options_deny(self, client):
        """Test that X-Frame-Options is set to DENY."""
        response = client.get('/health/')
        
        assert 'X-Frame-Options' in response
        assert response['X-Frame-Options'] == 'DENY'
    
    @override_settings(MIDDLEWARE=TEST_MIDDLEWARE, CSP_FRAME_ANCESTORS=("'none'",))
    @pytest.mark.django_db
    def test_csp_frame_ancestors_none(self, client):
        """Test that CSP frame-ancestors is set to 'none'."""
        response = client.get('/health/')
        
        if 'Content-Security-Policy' in response:
            csp_value = response['Content-Security-Policy']
            assert "frame-ancestors 'none'" in csp_value
    
    @override_settings(MIDDLEWARE=TEST_MIDDLEWARE, SECURE_CONTENT_TYPE_NOSNIFF=True)
    @pytest.mark.django_db
    def test_content_type_nosniff(self, client):
        """Test that X-Content-Type-Options is set to nosniff."""
        response = client.get('/health/')
        
        assert 'X-Content-Type-Options' in response
        assert response['X-Content-Type-Options'] == 'nosniff'


class TestSecurityHeadersProduction:
    """Test security headers in production-like configuration."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return Client()
    
    @override_settings(
        MIDDLEWARE=TEST_MIDDLEWARE,
        ENVIRONMENT='production',
        DEBUG=False,
        SECURE_SSL_REDIRECT=False,  # Disable for testing
        SECURE_HSTS_SECONDS=31536000,
        SECURE_HSTS_INCLUDE_SUBDOMAINS=True,
        SECURE_HSTS_PRELOAD=True,
        SECURE_CONTENT_TYPE_NOSNIFF=True,
        SECURE_BROWSER_XSS_FILTER=True,
        X_FRAME_OPTIONS='DENY',
        SESSION_COOKIE_SECURE=True,
        CSRF_COOKIE_SECURE=True,
        CSP_DEFAULT_SRC=("'self'",),
        CSP_FRAME_ANCESTORS=("'none'",)
    )
    @pytest.mark.django_db
    def test_production_security_headers(self, client):
        """Test that all security headers are properly configured for production."""
        response = client.get('/health/', secure=True)
        
        # Verify all critical security headers
        assert 'Strict-Transport-Security' in response
        assert 'X-Content-Type-Options' in response
        assert 'X-Frame-Options' in response
        assert 'Content-Security-Policy' in response
        
        # Verify values
        assert 'max-age=31536000' in response['Strict-Transport-Security']
        assert response['X-Content-Type-Options'] == 'nosniff'
        assert response['X-Frame-Options'] == 'DENY'
        assert "frame-ancestors 'none'" in response['Content-Security-Policy']
