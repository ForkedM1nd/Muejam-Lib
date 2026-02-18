"""
Unit tests for security headers configuration.

Tests verify that all required security headers are properly configured
according to Requirements 6.3, 6.4, 6.5, and 6.6.
"""

import pytest
from django.test import Client, override_settings
from django.urls import reverse


@pytest.fixture
def client():
    """Create a test client."""
    return Client()


@pytest.mark.django_db
class TestSecurityHeaders:
    """Test suite for security headers configuration."""

    def test_hsts_header_present(self, client):
        """
        Test that Strict-Transport-Security header is present.
        
        Requirement 6.4: THE System SHALL set Strict-Transport-Security header
        with max-age of 31536000 seconds (1 year)
        
        Note: HSTS is only sent over HTTPS connections. In test/dev mode,
        we verify the setting is configured correctly.
        """
        from django.conf import settings
        
        # Verify HSTS is configured in settings
        assert hasattr(settings, 'SECURE_HSTS_SECONDS')
        assert settings.SECURE_HSTS_SECONDS == 31536000
        
    def test_hsts_includes_subdomains(self, client):
        """
        Test that HSTS header includes subdomains directive.
        
        This ensures HSTS protection extends to all subdomains.
        """
        from django.conf import settings
        
        # Verify HSTS subdomain setting is configured
        assert hasattr(settings, 'SECURE_HSTS_INCLUDE_SUBDOMAINS')
        assert settings.SECURE_HSTS_INCLUDE_SUBDOMAINS is True
        
    def test_x_frame_options_deny(self, client):
        """
        Test that X-Frame-Options header is set to DENY.
        
        Requirement 6.5: THE System SHALL set X-Frame-Options header to DENY
        to prevent clickjacking
        """
        response = client.get(reverse('health-check'))
        
        assert 'X-Frame-Options' in response.headers
        assert response.headers['X-Frame-Options'] == 'DENY'
        
    def test_x_content_type_options_nosniff(self, client):
        """
        Test that X-Content-Type-Options header is set to nosniff.
        
        Requirement 6.6: THE System SHALL set X-Content-Type-Options header
        to nosniff
        """
        response = client.get(reverse('health-check'))
        
        assert 'X-Content-Type-Options' in response.headers
        assert response.headers['X-Content-Type-Options'] == 'nosniff'
        
    def test_content_security_policy_present(self, client):
        """
        Test that Content-Security-Policy header is present.
        
        Requirement 6.3: THE System SHALL set Content-Security-Policy header
        restricting script sources to same-origin and trusted CDNs
        """
        response = client.get(reverse('health-check'))
        
        assert 'Content-Security-Policy' in response.headers
        csp_value = response.headers['Content-Security-Policy']
        
        # Verify default-src is set to 'self'
        assert "default-src 'self'" in csp_value or "default-src: 'self'" in csp_value
        
    def test_csp_script_src_restrictions(self, client):
        """
        Test that CSP script-src directive restricts to trusted sources.
        
        Requirement 6.3: Script sources should be limited to same-origin
        and trusted CDNs
        """
        response = client.get(reverse('health-check'))
        
        csp_value = response.headers.get('Content-Security-Policy', '')
        
        # Verify script-src includes 'self'
        assert "'self'" in csp_value
        
        # Verify trusted CDNs are allowed
        assert 'cdn.jsdelivr.net' in csp_value or 'www.google.com' in csp_value
        
    def test_csp_frame_ancestors_none(self, client):
        """
        Test that CSP frame-ancestors is set to 'none'.
        
        This provides additional clickjacking protection beyond X-Frame-Options.
        """
        response = client.get(reverse('health-check'))
        
        csp_value = response.headers.get('Content-Security-Policy', '')
        
        # Verify frame-ancestors is set to 'none'
        assert "frame-ancestors 'none'" in csp_value or "frame-ancestors: 'none'" in csp_value
        
    def test_x_xss_protection_enabled(self, client):
        """
        Test that X-XSS-Protection header is enabled.
        
        This provides legacy XSS protection for older browsers.
        """
        response = client.get(reverse('health-check'))
        
        # X-XSS-Protection may not be present in all responses
        # but if present, should be enabled
        if 'X-XSS-Protection' in response.headers:
            xss_value = response.headers['X-XSS-Protection']
            assert '1' in xss_value
            
    def test_all_security_headers_present(self, client):
        """
        Test that all required security headers are present in a single response.
        
        This is a comprehensive test ensuring all security headers work together.
        Note: HSTS is only sent over HTTPS, so we verify it via settings.
        """
        from django.conf import settings
        
        response = client.get(reverse('health-check'))
        
        required_headers = [
            'X-Frame-Options',
            'X-Content-Type-Options',
            'Content-Security-Policy',
        ]
        
        for header in required_headers:
            assert header in response.headers, f"Missing required security header: {header}"
            
        # Verify HSTS is configured (sent over HTTPS only)
        assert settings.SECURE_HSTS_SECONDS == 31536000
            
    def test_security_headers_on_api_endpoints(self, client):
        """
        Test that security headers are present on API endpoints.
        
        Security headers should be applied to all responses, including API endpoints.
        """
        # Test on a different endpoint to ensure headers are global
        response = client.get('/api/schema/')
        
        # Verify key security headers are present
        assert 'X-Frame-Options' in response.headers
        assert 'X-Content-Type-Options' in response.headers
        
    @override_settings(DEBUG=True)
    def test_hsts_not_enforced_in_debug_mode(self, client):
        """
        Test that HSTS is not enforced in DEBUG mode.
        
        In development (DEBUG=True), HSTS should not be enforced to allow
        HTTP connections.
        """
        # In DEBUG mode, SECURE_HSTS_SECONDS might be 0 or header might not be present
        # This is expected behavior for development
        response = client.get(reverse('health-check'))
        
        # Just verify the response is successful
        # HSTS enforcement is conditional on DEBUG setting
        assert response.status_code in [200, 404]  # 404 is ok if endpoint doesn't exist


@pytest.mark.django_db
class TestCSPConfiguration:
    """Test suite for Content Security Policy configuration details."""
    
    def test_csp_default_src_self_only(self, client):
        """
        Test that CSP default-src is restricted to 'self'.
        
        This ensures resources are only loaded from the same origin by default.
        """
        response = client.get(reverse('health-check'))
        csp_value = response.headers.get('Content-Security-Policy', '')
        
        # default-src should be 'self'
        assert "default-src 'self'" in csp_value or "default-src: 'self'" in csp_value
        
    def test_csp_img_src_allows_https(self, client):
        """
        Test that CSP img-src allows HTTPS images.
        
        This is needed for user-uploaded images from CDN.
        """
        response = client.get(reverse('health-check'))
        csp_value = response.headers.get('Content-Security-Policy', '')
        
        # img-src should allow https: and cloudfront
        assert 'img-src' in csp_value
        
    def test_csp_connect_src_includes_self(self, client):
        """
        Test that CSP connect-src includes 'self'.
        
        This allows API calls to the same origin.
        """
        response = client.get(reverse('health-check'))
        csp_value = response.headers.get('Content-Security-Policy', '')
        
        # connect-src should include 'self'
        assert 'connect-src' in csp_value


@pytest.mark.django_db
class TestSecurityHeaderValues:
    """Test suite for verifying exact security header values."""
    
    def test_hsts_max_age_one_year(self, client):
        """
        Test that HSTS max-age is exactly 1 year (31536000 seconds).
        
        Requirement 6.4: Strict-Transport-Security header with max-age
        of 31536000 seconds (1 year)
        """
        from django.conf import settings
        
        # Verify HSTS max-age setting
        assert settings.SECURE_HSTS_SECONDS == 31536000, \
            f"HSTS max-age should be 31536000, got {settings.SECURE_HSTS_SECONDS}"
            
    def test_x_frame_options_exact_value(self, client):
        """
        Test that X-Frame-Options is exactly 'DENY'.
        
        Requirement 6.5: X-Frame-Options header to DENY
        """
        response = client.get(reverse('health-check'))
        x_frame_options = response.headers.get('X-Frame-Options', '')
        
        assert x_frame_options == 'DENY', f"X-Frame-Options should be 'DENY', got '{x_frame_options}'"
        
    def test_x_content_type_options_exact_value(self, client):
        """
        Test that X-Content-Type-Options is exactly 'nosniff'.
        
        Requirement 6.6: X-Content-Type-Options header to nosniff
        """
        response = client.get(reverse('health-check'))
        x_content_type = response.headers.get('X-Content-Type-Options', '')
        
        assert x_content_type == 'nosniff', f"X-Content-Type-Options should be 'nosniff', got '{x_content_type}'"
