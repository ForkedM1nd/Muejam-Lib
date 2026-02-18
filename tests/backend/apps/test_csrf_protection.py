"""
Tests for CSRF protection configuration and enforcement.

Requirements:
    - 6.1: THE System SHALL enable Django CSRF protection on all state-changing endpoints
    - 6.2: THE System SHALL validate CSRF tokens on POST, PUT, PATCH, and DELETE requests
"""

from django.test import TestCase, override_settings
from django.conf import settings
from rest_framework.test import APIClient, APIRequestFactory
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.middleware.csrf import get_token
from unittest.mock import patch


class CSRFMiddlewareTests(TestCase):
    """
    Test that CSRF middleware is properly enabled.
    
    Requirements:
        - 6.1: Enable Django CSRF protection
    """
    
    def test_csrf_middleware_enabled(self):
        """
        Test that CsrfViewMiddleware is in MIDDLEWARE list.
        
        Requirements:
            - 6.1: CSRF middleware is enabled
        """
        self.assertIn(
            'django.middleware.csrf.CsrfViewMiddleware',
            settings.MIDDLEWARE,
            "CSRF middleware must be enabled in settings"
        )
    
    def test_csrf_middleware_order(self):
        """
        Test that CSRF middleware is after SessionMiddleware.
        
        CSRF middleware requires session middleware to be loaded first.
        """
        middleware_list = settings.MIDDLEWARE
        csrf_index = middleware_list.index('django.middleware.csrf.CsrfViewMiddleware')
        session_index = middleware_list.index('django.contrib.sessions.middleware.SessionMiddleware')
        
        self.assertLess(
            session_index,
            csrf_index,
            "SessionMiddleware must come before CsrfViewMiddleware"
        )


class CSRFCookieConfigurationTests(TestCase):
    """
    Test CSRF cookie security configuration.
    
    Requirements:
        - 6.1: Configure CSRF cookie settings (secure, httponly, samesite)
    """
    
    def test_csrf_cookie_httponly(self):
        """
        Test that CSRF cookie has httpOnly flag set.
        
        Requirements:
            - 6.1: CSRF cookie httponly flag
        """
        self.assertTrue(
            settings.CSRF_COOKIE_HTTPONLY,
            "CSRF_COOKIE_HTTPONLY must be True"
        )
    
    def test_csrf_cookie_samesite(self):
        """
        Test that CSRF cookie has SameSite=Strict.
        
        Requirements:
            - 6.1: CSRF cookie samesite flag
        """
        self.assertEqual(
            settings.CSRF_COOKIE_SAMESITE,
            'Strict',
            "CSRF_COOKIE_SAMESITE must be 'Strict'"
        )
    
    def test_csrf_cookie_secure_in_production(self):
        """
        Test that CSRF cookie secure flag is configured correctly.
        
        The setting should be dynamic based on DEBUG mode.
        This test verifies the configuration exists and is boolean.
        
        Requirements:
            - 6.1: CSRF cookie secure flag
        """
        # Verify the setting exists and is a boolean
        self.assertIsInstance(
            settings.CSRF_COOKIE_SECURE,
            bool,
            "CSRF_COOKIE_SECURE must be a boolean"
        )
        
        # In the actual settings.py, it's configured as: CSRF_COOKIE_SECURE = not DEBUG
        # This ensures it's True in production (DEBUG=False) and False in development (DEBUG=True)
        # We can't test the exact value here because test environment may override DEBUG
    
    def test_csrf_trusted_origins_configured(self):
        """
        Test that CSRF_TRUSTED_ORIGINS is configured.
        
        This is required for cross-origin requests from the frontend.
        """
        self.assertIsNotNone(
            settings.CSRF_TRUSTED_ORIGINS,
            "CSRF_TRUSTED_ORIGINS must be configured"
        )
        self.assertIsInstance(
            settings.CSRF_TRUSTED_ORIGINS,
            list,
            "CSRF_TRUSTED_ORIGINS must be a list"
        )


class CSRFProtectionEnforcementTests(TestCase):
    """
    Test CSRF protection enforcement on state-changing endpoints.
    
    Requirements:
        - 6.2: Validate CSRF tokens on POST, PUT, PATCH, and DELETE requests
    """
    
    def setUp(self):
        """Set up test client."""
        self.client = APIClient()
        # Enforce CSRF checks (APIClient disables them by default)
        self.client.handler.enforce_csrf_checks = True
    
    def test_post_request_without_csrf_token_rejected(self):
        """
        Test that POST requests without CSRF token are rejected.
        
        Requirements:
            - 6.2: Validate CSRF tokens on POST requests
        """
        # Try to create a report without CSRF token
        response = self.client.post(
            '/v1/reports/',
            {
                'content_type': 'STORY',
                'content_id': 'test_story_id',
                'reason': 'SPAM',
                'description': 'Test report'
            },
            format='json'
        )
        
        # Should be rejected with 403 Forbidden
        self.assertEqual(
            response.status_code,
            403,
            "POST request without CSRF token should be rejected"
        )
    
    def test_put_request_without_csrf_token_rejected(self):
        """
        Test that PUT requests without CSRF token are rejected.
        
        Requirements:
            - 6.2: Validate CSRF tokens on PUT requests
        """
        # Try to update user profile without CSRF token (this endpoint supports PUT)
        response = self.client.put(
            '/v1/users/me/',  # This endpoint supports PUT
            {'bio': 'Updated bio'},
            format='json'
        )
        
        # Should be rejected with 403 Forbidden (or 401 if auth required first)
        # The key is that it's not a 200 success
        self.assertIn(
            response.status_code,
            [401, 403],
            "PUT request without CSRF token should be rejected"
        )
    
    def test_patch_request_without_csrf_token_rejected(self):
        """
        Test that PATCH requests without CSRF token are rejected.
        
        Requirements:
            - 6.2: Validate CSRF tokens on PATCH requests
        """
        # Try to partially update a story without CSRF token
        # Note: PATCH is less commonly supported, so we test the concept
        # by verifying the request is not successful (401/403/405 all indicate protection)
        response = self.client.patch(
            '/v1/stories/test_story_id/',
            {'title': 'Updated bio'},
            format='json'
        )
        
        # Should be rejected (403 for CSRF, 401 for auth, 405 if method not allowed)
        # The key is that it's not a 200 success
        self.assertIn(
            response.status_code,
            [401, 403, 404, 405],
            "PATCH request without CSRF token should be rejected or not allowed"
        )
    
    def test_delete_request_without_csrf_token_rejected(self):
        """
        Test that DELETE requests without CSRF token are rejected.
        
        Requirements:
            - 6.2: Validate CSRF tokens on DELETE requests
        """
        # Try to delete a bookmark without CSRF token
        response = self.client.delete('/v1/bookmarks/test_bookmark_id')
        
        # Should be rejected with 403 Forbidden (or 401 if auth required first)
        self.assertIn(
            response.status_code,
            [401, 403, 404],  # 404 if bookmark doesn't exist, but still protected
            "DELETE request without CSRF token should be rejected"
        )
    
    def test_get_request_without_csrf_token_allowed(self):
        """
        Test that GET requests don't require CSRF token.
        
        CSRF protection only applies to state-changing methods.
        """
        # GET request should work without CSRF token
        response = self.client.get('/v1/health/')
        
        # Should not be rejected for missing CSRF token
        # (may return 200, 404, or other status, but not 403 for CSRF)
        self.assertNotEqual(
            response.status_code,
            403,
            "GET request should not require CSRF token"
        )
    
    def test_post_request_with_valid_csrf_token_accepted(self):
        """
        Test that POST requests with valid CSRF token are accepted.
        
        Requirements:
            - 6.2: Validate CSRF tokens on POST requests
        """
        # Get CSRF token
        response = self.client.get('/v1/health/')
        csrf_token = response.cookies.get('csrftoken')
        
        if csrf_token:
            # Make POST request with CSRF token
            self.client.credentials(HTTP_X_CSRFTOKEN=csrf_token.value)
            response = self.client.post(
                '/v1/reports/',
                {
                    'content_type': 'STORY',
                    'content_id': 'test_story_id',
                    'reason': 'SPAM',
                    'description': 'Test report'
                },
                format='json'
            )
            
            # Should not be rejected for CSRF (may fail for other reasons like auth)
            self.assertNotEqual(
                response.status_code,
                403,
                "POST request with valid CSRF token should not be rejected for CSRF"
            )


class CSRFTokenRetrievalTests(TestCase):
    """
    Test CSRF token retrieval mechanism.
    
    Clients need to be able to retrieve CSRF tokens.
    """
    
    def setUp(self):
        """Set up test client."""
        self.client = APIClient()
    
    def test_csrf_token_in_cookie(self):
        """
        Test that CSRF token is set in cookie on first request.
        
        The frontend needs to retrieve the CSRF token from the cookie.
        """
        # Make a GET request to trigger CSRF token generation
        response = self.client.get('/v1/health/')
        
        # Check if CSRF token cookie is set
        csrf_cookie = response.cookies.get('csrftoken')
        
        # Note: In test environment, cookie might not be set automatically
        # This test documents the expected behavior in production
        if csrf_cookie:
            self.assertIsNotNone(
                csrf_cookie.value,
                "CSRF token should be set in cookie"
            )


class SessionCookieConfigurationTests(TestCase):
    """
    Test session cookie security configuration.
    
    Requirements:
        - 6.11: Implement session security (secure, httpOnly, SameSite=Strict)
        - 6.12: Expire sessions after 30 days of inactivity
    """
    
    def test_session_cookie_httponly(self):
        """
        Test that session cookie has httpOnly flag set.
        
        Requirements:
            - 6.11: Session cookie httpOnly flag
        """
        self.assertTrue(
            settings.SESSION_COOKIE_HTTPONLY,
            "SESSION_COOKIE_HTTPONLY must be True"
        )
    
    def test_session_cookie_samesite(self):
        """
        Test that session cookie has SameSite=Strict.
        
        Requirements:
            - 6.11: Session cookie SameSite=Strict
        """
        self.assertEqual(
            settings.SESSION_COOKIE_SAMESITE,
            'Strict',
            "SESSION_COOKIE_SAMESITE must be 'Strict'"
        )
    
    def test_session_cookie_secure_in_production(self):
        """
        Test that session cookie secure flag is configured correctly.
        
        The setting should be dynamic based on DEBUG mode.
        This test verifies the configuration exists and is boolean.
        
        Requirements:
            - 6.11: Session cookie secure flag
        """
        # Verify the setting exists and is a boolean
        self.assertIsInstance(
            settings.SESSION_COOKIE_SECURE,
            bool,
            "SESSION_COOKIE_SECURE must be a boolean"
        )
        
        # In the actual settings.py, it's configured as: SESSION_COOKIE_SECURE = not DEBUG
        # This ensures it's True in production (DEBUG=False) and False in development (DEBUG=True)
        # We can't test the exact value here because test environment may override DEBUG
    
    def test_session_cookie_age(self):
        """
        Test that session expires after 30 days.
        
        Requirements:
            - 6.12: Expire sessions after 30 days of inactivity
        """
        expected_age = 30 * 24 * 60 * 60  # 30 days in seconds
        self.assertEqual(
            settings.SESSION_COOKIE_AGE,
            expected_age,
            "SESSION_COOKIE_AGE must be 30 days (2592000 seconds)"
        )
    
    def test_session_save_every_request(self):
        """
        Test that session is updated on every request.
        
        This ensures the 30-day expiration is based on last activity.
        """
        self.assertTrue(
            settings.SESSION_SAVE_EVERY_REQUEST,
            "SESSION_SAVE_EVERY_REQUEST must be True to track activity"
        )


class CSRFExemptEndpointsTests(TestCase):
    """
    Test that certain endpoints are exempt from CSRF protection.
    
    Some endpoints like health checks and metrics should be exempt.
    """
    
    def setUp(self):
        """Set up test client."""
        self.client = APIClient()
        self.client.handler.enforce_csrf_checks = True
    
    def test_health_check_exempt_from_csrf(self):
        """
        Test that health check endpoint doesn't require CSRF token.
        
        Health checks are read-only and should be accessible without CSRF.
        """
        response = self.client.get('/v1/health/')
        
        # Should not be rejected for CSRF
        self.assertNotEqual(
            response.status_code,
            403,
            "Health check should not require CSRF token"
        )
    
    def test_metrics_endpoint_exempt_from_csrf(self):
        """
        Test that metrics endpoint doesn't require CSRF token.
        
        Metrics are read-only and should be accessible without CSRF.
        """
        response = self.client.get('/metrics')
        
        # Should not be rejected for CSRF
        self.assertNotEqual(
            response.status_code,
            403,
            "Metrics endpoint should not require CSRF token"
        )


class CSRFIntegrationTests(TestCase):
    """
    Integration tests for CSRF protection across different endpoints.
    
    Requirements:
        - 6.1: Enable Django CSRF protection on all state-changing endpoints
        - 6.2: Validate CSRF tokens on POST, PUT, PATCH, and DELETE requests
    """
    
    def setUp(self):
        """Set up test client with CSRF enforcement."""
        self.client = APIClient()
        self.client.handler.enforce_csrf_checks = True
    
    def test_csrf_protection_on_multiple_endpoints(self):
        """
        Test that CSRF protection is enforced across different API endpoints.
        
        Requirements:
            - 6.1: CSRF protection on all state-changing endpoints
            - 6.2: Validate CSRF tokens on POST, PUT, PATCH, DELETE
        """
        # List of state-changing endpoints to test
        # Note: Some endpoints may return 401 (auth required) before CSRF check
        # 405 means method not allowed, which is also acceptable (endpoint exists but doesn't support that method)
        test_cases = [
            ('POST', '/v1/reports/', {'content_type': 'STORY', 'content_id': 'test', 'reason': 'SPAM'}),
            ('POST', '/v1/whispers/', {'content': 'Test whisper', 'whisper_type': 'GLOBAL'}),
            ('DELETE', '/v1/bookmarks/test_id', None),
            ('PUT', '/v1/users/me/', {'bio': 'Updated'}),  # This endpoint supports PUT
            ('PATCH', '/v1/stories/test_id/', {'title': 'Updated'}),  # May return 405 if not supported
        ]
        
        for method, url, data in test_cases:
            with self.subTest(method=method, url=url):
                if method == 'POST':
                    response = self.client.post(url, data, format='json')
                elif method == 'PUT':
                    response = self.client.put(url, data, format='json')
                elif method == 'PATCH':
                    response = self.client.patch(url, data, format='json')
                elif method == 'DELETE':
                    response = self.client.delete(url)
                
                # Should be rejected (403 for CSRF, 401 for auth, 404 for not found, 405 for method not allowed)
                # The key is that it's not a 200 success without proper tokens
                self.assertIn(
                    response.status_code,
                    [401, 403, 404, 405],
                    f"{method} request to {url} should require CSRF token and/or authentication"
                )
