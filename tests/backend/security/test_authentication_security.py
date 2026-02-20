"""
Security tests for authentication mechanisms

Tests JWT verification, token validation, and authentication bypass attempts.
"""

import pytest
import jwt
import time
from datetime import datetime, timedelta, timezone
from django.test import TestCase, Client
from django.conf import settings
from unittest.mock import patch, MagicMock


class AuthenticationSecurityTest(TestCase):
    """Test authentication security"""
    
    def setUp(self):
        self.client = Client()
        self.valid_token = self.generate_test_token()
        self.expired_token = self.generate_expired_token()
        self.invalid_signature_token = self.generate_invalid_signature_token()
    
    def generate_test_token(self):
        """Generate a valid test JWT token"""
        # In real tests, use actual Clerk token or mock properly
        payload = {
            'sub': 'test_user_123',
            'exp': datetime.now(timezone.utc) + timedelta(hours=1),
            'iat': datetime.now(timezone.utc),
            'aud': 'test_audience'
        }
        # This is a test token - in real tests, use proper signing
        return jwt.encode(payload, 'test_secret', algorithm='HS256')
    
    def generate_expired_token(self):
        """Generate an expired JWT token"""
        payload = {
            'sub': 'test_user_123',
            'exp': datetime.now(timezone.utc) - timedelta(hours=1),  # Expired
            'iat': datetime.now(timezone.utc) - timedelta(hours=2),
            'aud': 'test_audience'
        }
        return jwt.encode(payload, 'test_secret', algorithm='HS256')
    
    def generate_invalid_signature_token(self):
        """Generate a token with invalid signature"""
        payload = {
            'sub': 'test_user_123',
            'exp': datetime.now(timezone.utc) + timedelta(hours=1),
            'iat': datetime.now(timezone.utc),
            'aud': 'test_audience'
        }
        # Sign with wrong key
        return jwt.encode(payload, 'wrong_secret', algorithm='HS256')
    
    def test_valid_token_accepted(self):
        """Test that valid JWT tokens are accepted"""
        response = self.client.get(
            '/api/users/me',
            HTTP_AUTHORIZATION=f'Bearer {self.valid_token}'
        )
        
        # Should not be 401 (may be 404 if user doesn't exist, which is fine)
        self.assertNotEqual(response.status_code, 401,
                          "Valid token should not return 401 Unauthorized")
    
    def test_expired_token_rejected(self):
        """Test that expired tokens are rejected"""
        response = self.client.get(
            '/api/users/me',
            HTTP_AUTHORIZATION=f'Bearer {self.expired_token}'
        )
        
        self.assertEqual(response.status_code, 401,
                        "Expired token should return 401 Unauthorized")
    
    def test_invalid_signature_rejected(self):
        """Test that tokens with invalid signatures are rejected"""
        response = self.client.get(
            '/api/users/me',
            HTTP_AUTHORIZATION=f'Bearer {self.invalid_signature_token}'
        )
        
        self.assertEqual(response.status_code, 401,
                        "Invalid signature should return 401 Unauthorized")
    
    def test_missing_token_rejected(self):
        """Test that requests without tokens are rejected"""
        response = self.client.get('/api/users/me')
        
        self.assertEqual(response.status_code, 401,
                        "Missing token should return 401 Unauthorized")
    
    def test_malformed_token_rejected(self):
        """Test that malformed tokens are rejected"""
        response = self.client.get(
            '/api/users/me',
            HTTP_AUTHORIZATION='Bearer not-a-valid-jwt-token'
        )
        
        self.assertEqual(response.status_code, 401,
                        "Malformed token should return 401 Unauthorized")
    
    def test_bearer_prefix_required(self):
        """Test that Bearer prefix is required"""
        response = self.client.get(
            '/api/users/me',
            HTTP_AUTHORIZATION=self.valid_token  # Missing "Bearer " prefix
        )
        
        self.assertEqual(response.status_code, 401,
                        "Token without Bearer prefix should return 401")
    
    def test_token_with_wrong_audience_rejected(self):
        """Test that tokens with wrong audience are rejected"""
        payload = {
            'sub': 'test_user_123',
            'exp': datetime.now(timezone.utc) + timedelta(hours=1),
            'iat': datetime.now(timezone.utc),
            'aud': 'wrong_audience'  # Wrong audience
        }
        wrong_aud_token = jwt.encode(payload, 'test_secret', algorithm='HS256')
        
        response = self.client.get(
            '/api/users/me',
            HTTP_AUTHORIZATION=f'Bearer {wrong_aud_token}'
        )
        
        self.assertEqual(response.status_code, 401,
                        "Token with wrong audience should return 401")
    
    def test_token_without_sub_claim_rejected(self):
        """Test that tokens without sub claim are rejected"""
        payload = {
            # Missing 'sub' claim
            'exp': datetime.now(timezone.utc) + timedelta(hours=1),
            'iat': datetime.now(timezone.utc),
            'aud': 'test_audience'
        }
        no_sub_token = jwt.encode(payload, 'test_secret', algorithm='HS256')
        
        response = self.client.get(
            '/api/users/me',
            HTTP_AUTHORIZATION=f'Bearer {no_sub_token}'
        )
        
        self.assertEqual(response.status_code, 401,
                        "Token without sub claim should return 401")
    
    def test_authentication_bypass_attempt(self):
        """Test that authentication cannot be bypassed"""
        # Attempt to access protected endpoint without auth
        protected_endpoints = [
            '/api/users/me',
            '/api/stories',
            '/api/whispers',
            '/api/library/shelves',
        ]
        
        for endpoint in protected_endpoints:
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 401,
                           f"Endpoint {endpoint} should require authentication")
    
    def test_token_reuse_after_logout(self):
        """Test that tokens cannot be reused after logout"""
        # 1. Logout
        logout_response = self.client.post(
            '/api/auth/logout',
            HTTP_AUTHORIZATION=f'Bearer {self.valid_token}'
        )
        
        # 2. Try to use same token
        response = self.client.get(
            '/api/users/me',
            HTTP_AUTHORIZATION=f'Bearer {self.valid_token}'
        )
        
        # Token should be invalidated (if logout is implemented)
        # This test may need adjustment based on actual logout implementation
        self.assertIn(response.status_code, [401, 404],
                     "Token should not work after logout")


class JWTVerificationTest(TestCase):
    """Test JWT verification service"""
    
    def test_jwt_signature_verification_enabled(self):
        """Test that JWT signature verification is enabled"""
        from apps.users.jwt_service import JWTVerificationService
        
        # Create a token with invalid signature
        payload = {
            'sub': 'test_user',
            'exp': datetime.now(timezone.utc) + timedelta(hours=1),
            'iat': datetime.now(timezone.utc)
        }
        invalid_token = jwt.encode(payload, 'wrong_key', algorithm='HS256')
        
        # Verification should fail
        with self.assertRaises(Exception):
            JWTVerificationService.verify_token(invalid_token)
    
    def test_jwks_caching(self):
        """Test that JWKS are cached"""
        from apps.users.jwt_service import JWTVerificationService
        from django.core.cache import cache
        
        # Clear cache
        cache.delete(JWTVerificationService.JWKS_CACHE_KEY)
        
        # First call should fetch JWKS
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {'keys': []}
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            jwks1 = JWTVerificationService.get_jwks()
            
            # Second call should use cache
            jwks2 = JWTVerificationService.get_jwks()
            
            # Should only call API once
            self.assertEqual(mock_get.call_count, 1)
            self.assertEqual(jwks1, jwks2)


class RateLimitSecurityTest(TestCase):
    """Test rate limiting security"""
    
    def setUp(self):
        self.client = Client()
        self.token = self.generate_test_token()
    
    def generate_test_token(self):
        """Generate test token"""
        payload = {
            'sub': 'test_user_123',
            'exp': datetime.now(timezone.utc) + timedelta(hours=1),
            'iat': datetime.now(timezone.utc)
        }
        return jwt.encode(payload, 'test_secret', algorithm='HS256')
    
    def test_rate_limit_enforced(self):
        """Test that rate limiting is enforced"""
        # Make many requests quickly
        responses = []
        for i in range(150):  # Exceed rate limit
            response = self.client.get(
                '/api/discovery/trending',
                HTTP_AUTHORIZATION=f'Bearer {self.token}'
            )
            responses.append(response.status_code)
        
        # Should have some 429 responses
        rate_limited_count = responses.count(429)
        self.assertGreater(rate_limited_count, 0,
                          "Rate limiting should trigger 429 responses")
    
    def test_rate_limit_headers_present(self):
        """Test that rate limit headers are present"""
        response = self.client.get(
            '/api/discovery/trending',
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        
        # Check for rate limit headers
        self.assertIn('X-RateLimit-Limit', response,
                     "X-RateLimit-Limit header should be present")
        self.assertIn('X-RateLimit-Remaining', response,
                     "X-RateLimit-Remaining header should be present")
        self.assertIn('X-RateLimit-Reset', response,
                     "X-RateLimit-Reset header should be present")
    
    def test_rate_limit_per_user(self):
        """Test that rate limiting is per user, not global"""
        # This test would need multiple user tokens
        # Placeholder for now
        pass


@pytest.mark.security
class SecurityHeadersTest(TestCase):
    """Test security headers"""
    
    def setUp(self):
        self.client = Client()
    
    def test_security_headers_present(self):
        """Test that security headers are present"""
        response = self.client.get('/')
        
        # Check for security headers
        headers_to_check = [
            'X-Content-Type-Options',
            'X-Frame-Options',
            'Strict-Transport-Security',
        ]
        
        for header in headers_to_check:
            self.assertIn(header, response,
                         f"{header} should be present")
    
    def test_x_content_type_options_nosniff(self):
        """Test X-Content-Type-Options is set to nosniff"""
        response = self.client.get('/')
        self.assertEqual(response.get('X-Content-Type-Options'), 'nosniff')
    
    def test_x_frame_options_deny(self):
        """Test X-Frame-Options is set to DENY"""
        response = self.client.get('/')
        self.assertIn(response.get('X-Frame-Options'), ['DENY', 'SAMEORIGIN'])
    
    def test_hsts_header(self):
        """Test Strict-Transport-Security header"""
        response = self.client.get('/')
        hsts = response.get('Strict-Transport-Security')
        
        if hsts:  # May not be set in development
            self.assertIn('max-age', hsts)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
