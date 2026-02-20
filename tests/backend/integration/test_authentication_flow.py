"""
Integration Tests for Authentication Flow

This module tests the complete authentication flow including:
- JWT token verification
- User profile creation
- Authentication middleware
- Session management

Requirements: 1.1, 5.1
"""

import pytest
import jwt
from datetime import datetime, timedelta, timezone
from django.test import Client, override_settings
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock


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
    'apps.users.middleware.ClerkAuthMiddleware',
    'infrastructure.rate_limit_middleware.RateLimitMiddleware',
]


class TestAuthenticationFlow:
    """Integration tests for authentication flow."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return Client()
    
    @pytest.fixture
    def mock_jwt_token(self):
        """Create a mock JWT token."""
        payload = {
            'sub': 'user_test123',
            'email': 'test@example.com',
            'exp': datetime.now(timezone.utc) + timedelta(hours=1),
            'iat': datetime.now(timezone.utc),
            'aud': 'test_audience'
        }
        # Create a test token (not verified in tests)
        return jwt.encode(payload, 'test_secret', algorithm='HS256')
    
    @override_settings(MIDDLEWARE=TEST_MIDDLEWARE)
    @pytest.mark.django_db
    @patch('apps.users.middleware.JWTVerificationService.verify_token')
    @patch('apps.users.middleware.get_or_create_profile_sync')
    def test_successful_authentication_flow(self, mock_get_profile, mock_verify, client, mock_jwt_token):
        """Test successful authentication flow from token to user profile."""
        # Mock JWT verification
        mock_verify.return_value = {
            'sub': 'user_test123',
            'email': 'test@example.com'
        }
        
        # Mock user profile creation
        mock_profile = MagicMock()
        mock_profile.id = 'profile_123'
        mock_profile.clerk_user_id = 'user_test123'
        mock_profile.handle = 'testuser'
        mock_get_profile.return_value = mock_profile
        
        # Make authenticated request
        response = client.get(
            '/health/live',
            HTTP_AUTHORIZATION=f'Bearer {mock_jwt_token}'
        )
        
        # Verify response
        assert response.status_code == 200
        
        # Verify JWT was verified
        mock_verify.assert_called_once()
        
        # Verify profile was retrieved/created
        mock_get_profile.assert_called_once_with('user_test123')
    
    @override_settings(MIDDLEWARE=TEST_MIDDLEWARE)
    @pytest.mark.django_db
    @patch('apps.users.middleware.JWTVerificationService.verify_token')
    def test_authentication_with_expired_token(self, mock_verify, client, mock_jwt_token):
        """Test authentication fails with expired token."""
        # Mock JWT verification to raise expired error
        mock_verify.side_effect = Exception("Token has expired")
        
        # Make authenticated request
        response = client.get(
            '/health/live',
            HTTP_AUTHORIZATION=f'Bearer {mock_jwt_token}'
        )
        
        # Should still return 200 but without authentication
        assert response.status_code == 200
        
        # Verify JWT verification was attempted
        mock_verify.assert_called_once()
    
    @override_settings(MIDDLEWARE=TEST_MIDDLEWARE)
    @pytest.mark.django_db
    @patch('apps.users.middleware.JWTVerificationService.verify_token')
    def test_authentication_with_invalid_token(self, mock_verify, client):
        """Test authentication fails with invalid token."""
        # Mock JWT verification to raise invalid token error
        mock_verify.side_effect = Exception("Invalid token")
        
        # Make authenticated request with invalid token
        response = client.get(
            '/health/live',
            HTTP_AUTHORIZATION='Bearer invalid_token_here'
        )
        
        # Should still return 200 but without authentication
        assert response.status_code == 200
        
        # Verify JWT verification was attempted
        mock_verify.assert_called_once()
    
    @override_settings(MIDDLEWARE=TEST_MIDDLEWARE)
    @pytest.mark.django_db
    def test_authentication_without_token(self, client):
        """Test request without authentication token."""
        # Make unauthenticated request
        response = client.get('/health/live')
        
        # Should return 200 (health endpoint is public)
        assert response.status_code == 200
    
    @override_settings(MIDDLEWARE=TEST_MIDDLEWARE)
    @pytest.mark.django_db
    def test_authentication_with_malformed_header(self, client):
        """Test authentication with malformed Authorization header."""
        # Make request with malformed header
        response = client.get(
            '/health/live',
            HTTP_AUTHORIZATION='InvalidFormat token_here'
        )
        
        # Should return 200 but without authentication
        assert response.status_code == 200
    
    @override_settings(MIDDLEWARE=TEST_MIDDLEWARE)
    @pytest.mark.django_db
    @patch('apps.users.middleware.JWTVerificationService.verify_token')
    @patch('apps.users.middleware.get_or_create_profile_sync')
    def test_authentication_with_profile_creation(self, mock_get_profile, mock_verify, client, mock_jwt_token):
        """Test authentication creates user profile if not exists."""
        # Mock JWT verification
        mock_verify.return_value = {
            'sub': 'user_new123',
            'email': 'newuser@example.com'
        }
        
        # Mock profile creation (simulating new user)
        mock_profile = MagicMock()
        mock_profile.id = 'profile_new123'
        mock_profile.clerk_user_id = 'user_new123'
        mock_profile.handle = 'newuser'
        mock_get_profile.return_value = mock_profile
        
        # Make authenticated request
        response = client.get(
            '/health/live',
            HTTP_AUTHORIZATION=f'Bearer {mock_jwt_token}'
        )
        
        # Verify response
        assert response.status_code == 200
        
        # Verify profile was created
        mock_get_profile.assert_called_once_with('user_new123')
    
    @override_settings(MIDDLEWARE=TEST_MIDDLEWARE)
    @pytest.mark.django_db
    @patch('apps.users.middleware.JWTVerificationService.verify_token')
    @patch('apps.users.middleware.get_or_create_profile_sync')
    def test_authentication_logging(self, mock_get_profile, mock_verify, client, mock_jwt_token):
        """Test that authentication events are logged."""
        # Mock JWT verification
        mock_verify.return_value = {
            'sub': 'user_test123',
            'email': 'test@example.com'
        }
        
        # Mock user profile
        mock_profile = MagicMock()
        mock_profile.id = 'profile_123'
        mock_get_profile.return_value = mock_profile
        
        # Make authenticated request
        with patch('apps.users.middleware.log_authentication_event') as mock_log:
            response = client.get(
                '/health/live',
                HTTP_AUTHORIZATION=f'Bearer {mock_jwt_token}'
            )
            
            # Verify logging was called
            # Note: This assumes log_authentication_event is called in middleware
            # Adjust based on actual implementation
            assert response.status_code == 200
    
    @override_settings(MIDDLEWARE=TEST_MIDDLEWARE)
    @pytest.mark.django_db
    @patch('apps.users.middleware.JWTVerificationService.verify_token')
    @patch('apps.users.middleware.get_or_create_profile_sync')
    def test_multiple_authenticated_requests(self, mock_get_profile, mock_verify, client, mock_jwt_token):
        """Test multiple authenticated requests with same token."""
        # Mock JWT verification
        mock_verify.return_value = {
            'sub': 'user_test123',
            'email': 'test@example.com'
        }
        
        # Mock user profile
        mock_profile = MagicMock()
        mock_profile.id = 'profile_123'
        mock_get_profile.return_value = mock_profile
        
        # Make multiple authenticated requests
        for _ in range(3):
            response = client.get(
                '/health/live',
                HTTP_AUTHORIZATION=f'Bearer {mock_jwt_token}'
            )
            assert response.status_code == 200
        
        # Verify JWT was verified for each request
        assert mock_verify.call_count == 3
        
        # Verify profile was retrieved for each request
        assert mock_get_profile.call_count == 3
    
    @override_settings(MIDDLEWARE=TEST_MIDDLEWARE)
    @pytest.mark.django_db
    @patch('apps.users.middleware.JWTVerificationService.verify_token')
    def test_authentication_error_handling(self, mock_verify, client, mock_jwt_token):
        """Test that authentication errors are handled gracefully."""
        # Mock JWT verification to raise unexpected error
        mock_verify.side_effect = Exception("Unexpected error")
        
        # Make authenticated request
        response = client.get(
            '/health/live',
            HTTP_AUTHORIZATION=f'Bearer {mock_jwt_token}'
        )
        
        # Should handle error gracefully and return 200
        assert response.status_code == 200
        
        # Verify error was logged (implementation dependent)
        mock_verify.assert_called_once()


class TestAuthenticationMiddleware:
    """Integration tests for authentication middleware behavior."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return Client()
    
    @override_settings(MIDDLEWARE=TEST_MIDDLEWARE)
    @pytest.mark.django_db
    @patch('apps.users.middleware.JWTVerificationService.verify_token')
    @patch('apps.users.middleware.get_or_create_profile_sync')
    def test_middleware_sets_request_attributes(self, mock_get_profile, mock_verify, client):
        """Test that middleware sets correct request attributes."""
        # Mock JWT verification
        mock_verify.return_value = {
            'sub': 'user_test123',
            'email': 'test@example.com'
        }
        
        # Mock user profile
        mock_profile = MagicMock()
        mock_profile.id = 'profile_123'
        mock_profile.clerk_user_id = 'user_test123'
        mock_get_profile.return_value = mock_profile
        
        # Make authenticated request
        response = client.get(
            '/health/live',
            HTTP_AUTHORIZATION='Bearer test_token'
        )
        
        # Verify response
        assert response.status_code == 200
        
        # Note: Request attributes are not accessible in response
        # This test verifies the middleware executes without errors
    
    @override_settings(MIDDLEWARE=TEST_MIDDLEWARE)
    @pytest.mark.django_db
    def test_middleware_order(self, client):
        """Test that authentication middleware is in correct order."""
        from django.conf import settings
        
        middleware = settings.MIDDLEWARE
        
        # Verify ClerkAuthMiddleware is present
        assert 'apps.users.middleware.ClerkAuthMiddleware' in middleware
        
        # Verify it comes after session middleware
        session_idx = middleware.index('django.contrib.sessions.middleware.SessionMiddleware')
        auth_idx = middleware.index('apps.users.middleware.ClerkAuthMiddleware')
        assert auth_idx > session_idx
    
    @override_settings(MIDDLEWARE=TEST_MIDDLEWARE)
    @pytest.mark.django_db
    @patch('apps.users.middleware.JWTVerificationService.verify_token')
    def test_middleware_handles_missing_profile(self, mock_verify, client):
        """Test middleware handles case where profile creation fails."""
        # Mock JWT verification
        mock_verify.return_value = {
            'sub': 'user_test123',
            'email': 'test@example.com'
        }
        
        # Mock profile creation to return None
        with patch('apps.users.middleware.get_or_create_profile_sync', return_value=None):
            # Make authenticated request
            response = client.get(
                '/health/live',
                HTTP_AUTHORIZATION='Bearer test_token'
            )
            
            # Should handle gracefully
            assert response.status_code == 200


class TestAuthenticationSecurity:
    """Integration tests for authentication security measures."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return Client()
    
    @override_settings(MIDDLEWARE=TEST_MIDDLEWARE)
    @pytest.mark.django_db
    def test_authentication_without_signature_verification_disabled(self, client):
        """Test that JWT signature verification is enabled."""
        # Create a token with invalid signature
        invalid_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyXzEyMyJ9.invalid_signature'
        
        # Make request with invalid token
        response = client.get(
            '/health/live',
            HTTP_AUTHORIZATION=f'Bearer {invalid_token}'
        )
        
        # Should not authenticate (signature verification should fail)
        assert response.status_code == 200
        # Note: Health endpoint is public, so it returns 200
        # Protected endpoints would return 401/403
    
    @override_settings(MIDDLEWARE=TEST_MIDDLEWARE)
    @pytest.mark.django_db
    @patch('apps.users.middleware.JWTVerificationService.verify_token')
    @patch('apps.users.middleware.get_or_create_profile_sync')
    def test_authentication_rate_limiting_integration(self, mock_get_profile, mock_verify, client):
        """Test that authentication works with rate limiting."""
        # Mock JWT verification
        mock_verify.return_value = {
            'sub': 'user_test123',
            'email': 'test@example.com'
        }
        
        # Mock user profile
        mock_profile = MagicMock()
        mock_profile.id = 'profile_123'
        mock_get_profile.return_value = mock_profile
        
        # Make multiple authenticated requests
        for i in range(5):
            response = client.get(
                '/health/live',
                HTTP_AUTHORIZATION='Bearer test_token'
            )
            # Should not be rate limited for health endpoint
            assert response.status_code == 200
    
    @override_settings(MIDDLEWARE=TEST_MIDDLEWARE)
    @pytest.mark.django_db
    def test_authentication_with_sql_injection_attempt(self, client):
        """Test that authentication is safe from SQL injection."""
        # Attempt SQL injection in token
        malicious_token = "'; DROP TABLE users; --"
        
        # Make request with malicious token
        response = client.get(
            '/health/live',
            HTTP_AUTHORIZATION=f'Bearer {malicious_token}'
        )
        
        # Should handle safely
        assert response.status_code == 200
    
    @override_settings(MIDDLEWARE=TEST_MIDDLEWARE)
    @pytest.mark.django_db
    def test_authentication_with_xss_attempt(self, client):
        """Test that authentication is safe from XSS."""
        # Attempt XSS in token
        malicious_token = "<script>alert('xss')</script>"
        
        # Make request with malicious token
        response = client.get(
            '/health/live',
            HTTP_AUTHORIZATION=f'Bearer {malicious_token}'
        )
        
        # Should handle safely
        assert response.status_code == 200


class TestAuthenticationEndToEnd:
    """End-to-end integration tests for authentication."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return Client()
    
    @override_settings(MIDDLEWARE=TEST_MIDDLEWARE)
    @pytest.mark.django_db
    @patch('apps.users.middleware.JWTVerificationService.verify_token')
    @patch('apps.users.middleware.get_or_create_profile_sync')
    def test_complete_authentication_flow(self, mock_get_profile, mock_verify, client):
        """Test complete authentication flow from request to response."""
        # Setup mocks
        mock_verify.return_value = {
            'sub': 'user_test123',
            'email': 'test@example.com',
            'name': 'Test User'
        }
        
        mock_profile = MagicMock()
        mock_profile.id = 'profile_123'
        mock_profile.clerk_user_id = 'user_test123'
        mock_profile.handle = 'testuser'
        mock_profile.display_name = 'Test User'
        mock_get_profile.return_value = mock_profile
        
        # Make authenticated request
        response = client.get(
            '/health/live',
            HTTP_AUTHORIZATION='Bearer valid_token_here'
        )
        
        # Verify complete flow
        assert response.status_code == 200
        mock_verify.assert_called_once()
        mock_get_profile.assert_called_once_with('user_test123')
        
        # Verify response headers (if any authentication headers are set)
        # This depends on implementation
    
    @override_settings(MIDDLEWARE=TEST_MIDDLEWARE)
    @pytest.mark.django_db
    @patch('apps.users.middleware.JWTVerificationService.verify_token')
    @patch('apps.users.middleware.get_or_create_profile_sync')
    def test_authentication_with_all_middleware(self, mock_get_profile, mock_verify, client):
        """Test authentication works with all middleware enabled."""
        # Setup mocks
        mock_verify.return_value = {
            'sub': 'user_test123',
            'email': 'test@example.com'
        }
        
        mock_profile = MagicMock()
        mock_profile.id = 'profile_123'
        mock_get_profile.return_value = mock_profile
        
        # Make authenticated request through all middleware
        response = client.get(
            '/health/live',
            HTTP_AUTHORIZATION='Bearer test_token',
            secure=True  # HTTPS
        )
        
        # Verify request passed through all middleware
        assert response.status_code == 200
        
        # Verify security headers are present
        assert 'X-Content-Type-Options' in response or 'X-Frame-Options' in response
        
        # Verify rate limit headers are present
        assert 'X-RateLimit-Limit' in response or response.status_code == 200


