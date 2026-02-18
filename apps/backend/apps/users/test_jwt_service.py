"""
Unit tests for JWT Verification Service

Tests JWKS fetching, caching, and token verification functionality.
"""

import pytest
from unittest.mock import patch, Mock
from django.core.cache import cache
from django.test import TestCase
import jwt as pyjwt

from .jwt_service import (
    JWTVerificationService,
    JWTVerificationError,
    TokenExpiredError,
    InvalidTokenError,
    get_jwt_service
)


class TestJWKSFetchingAndCaching(TestCase):
    """Test JWKS fetching and caching functionality"""
    
    def setUp(self):
        """Clear cache before each test"""
        cache.clear()
        JWTVerificationService.clear_jwks_cache()
    
    def tearDown(self):
        """Clear cache after each test"""
        cache.clear()
    
    @patch('apps.users.jwt_service.requests.get')
    def test_jwks_fetching_success(self, mock_get):
        """Test successful JWKS fetching from Clerk API"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.json.return_value = {
            'keys': [
                {
                    'kid': 'test-key-id',
                    'kty': 'RSA',
                    'use': 'sig',
                    'n': 'test-n',
                    'e': 'AQAB'
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Fetch JWKS
        jwks = JWTVerificationService.get_jwks()
        
        # Verify API was called
        mock_get.assert_called_once()
        assert mock_get.call_args[1]['timeout'] == 5
        
        # Verify JWKS structure
        assert 'keys' in jwks
        assert len(jwks['keys']) == 1
        assert jwks['keys'][0]['kid'] == 'test-key-id'
    
    @patch('apps.users.jwt_service.requests.get')
    def test_jwks_caching(self, mock_get):
        """Test that JWKS is cached and reused"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.json.return_value = {
            'keys': [{'kid': 'test-key-id'}]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # First call - should fetch from API
        jwks1 = JWTVerificationService.get_jwks()
        assert mock_get.call_count == 1
        
        # Second call - should use cache
        jwks2 = JWTVerificationService.get_jwks()
        assert mock_get.call_count == 1  # Still 1, not called again
        
        # Verify same data returned
        assert jwks1 == jwks2
    
    @patch('apps.users.jwt_service.requests.get')
    def test_jwks_cache_ttl(self, mock_get):
        """Test that JWKS cache respects TTL"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.json.return_value = {
            'keys': [{'kid': 'test-key-id'}]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Fetch JWKS
        JWTVerificationService.get_jwks()
        
        # Verify it's in cache
        cached_jwks = cache.get(JWTVerificationService.JWKS_CACHE_KEY)
        assert cached_jwks is not None
        
        # Verify TTL is set (1 hour = 3600 seconds)
        assert JWTVerificationService.JWKS_CACHE_TTL == 3600
    
    @patch('apps.users.jwt_service.requests.get')
    def test_jwks_fetch_failure_handling(self, mock_get):
        """Test graceful handling of JWKS fetch failures"""
        # Mock API failure
        mock_get.side_effect = Exception("Network error")
        
        # Should raise JWTVerificationError
        with pytest.raises(JWTVerificationError) as exc_info:
            JWTVerificationService.get_jwks()
        
        assert "Unexpected error" in str(exc_info.value)
    
    @patch('apps.users.jwt_service.requests.get')
    def test_jwks_timeout_handling(self, mock_get):
        """Test that JWKS fetch has timeout configured"""
        import requests
        
        # Mock timeout
        mock_get.side_effect = requests.Timeout("Request timeout")
        
        # Should raise JWTVerificationError
        with pytest.raises(JWTVerificationError) as exc_info:
            JWTVerificationService.get_jwks()
        
        assert "Failed to fetch JWKS" in str(exc_info.value)
    
    def test_clear_jwks_cache(self):
        """Test clearing JWKS cache"""
        # Set something in cache
        cache.set(JWTVerificationService.JWKS_CACHE_KEY, {'test': 'data'}, 3600)
        
        # Verify it's there
        assert cache.get(JWTVerificationService.JWKS_CACHE_KEY) is not None
        
        # Clear cache
        JWTVerificationService.clear_jwks_cache()
        
        # Verify it's gone
        assert cache.get(JWTVerificationService.JWKS_CACHE_KEY) is None
    
    def test_get_jwt_service_singleton(self):
        """Test that get_jwt_service returns singleton instance"""
        service1 = get_jwt_service()
        service2 = get_jwt_service()
        
        # Should be same instance
        assert service1 is service2
        assert isinstance(service1, JWTVerificationService)


class TestJWKSCacheConfiguration(TestCase):
    """Test Django cache framework integration"""
    
    def test_cache_backend_configured(self):
        """Test that Django cache is properly configured"""
        from django.conf import settings
        
        # Verify cache is configured
        assert 'default' in settings.CACHES
        
        # Verify Redis backend is used
        backend = settings.CACHES['default']['BACKEND']
        assert 'redis' in backend.lower() or 'valkey' in backend.lower()
    
    def test_cache_operations(self):
        """Test basic cache operations work"""
        # Test set
        cache.set('test_key', 'test_value', 60)
        
        # Test get
        value = cache.get('test_key')
        assert value == 'test_value'
        
        # Test delete
        cache.delete('test_key')
        assert cache.get('test_key') is None


class TestTokenVerification(TestCase):
    """Test JWT token verification functionality"""
    
    def setUp(self):
        """Clear cache before each test"""
        cache.clear()
        JWTVerificationService.clear_jwks_cache()
    
    def tearDown(self):
        """Clear cache after each test"""
        cache.clear()
    
    @patch('apps.users.jwt_service.requests.get')
    def test_verify_token_with_valid_token(self, mock_get):
        """Test token verification with a valid token"""
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.backends import default_backend
        import time
        
        # Generate RSA key pair for testing
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        public_key = private_key.public_key()
        
        # Get public key numbers for JWK
        public_numbers = public_key.public_numbers()
        
        # Convert to JWK format
        import base64
        def int_to_base64(num):
            num_bytes = num.to_bytes((num.bit_length() + 7) // 8, byteorder='big')
            return base64.urlsafe_b64encode(num_bytes).decode('utf-8').rstrip('=')
        
        jwk = {
            'kid': 'test-key-id',
            'kty': 'RSA',
            'use': 'sig',
            'alg': 'RS256',
            'n': int_to_base64(public_numbers.n),
            'e': int_to_base64(public_numbers.e)
        }
        
        # Mock JWKS response
        mock_response = Mock()
        mock_response.json.return_value = {'keys': [jwk]}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Create a valid token
        from django.conf import settings
        payload = {
            'sub': 'user_123',
            'exp': int(time.time()) + 3600,  # Expires in 1 hour
            'iat': int(time.time()),
            'aud': settings.CLERK_PUBLISHABLE_KEY
        }
        
        # Sign token with private key
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        token = pyjwt.encode(
            payload,
            private_pem,
            algorithm='RS256',
            headers={'kid': 'test-key-id'}
        )
        
        # Verify token
        decoded = JWTVerificationService.verify_token(token)
        
        # Verify decoded payload
        assert decoded['sub'] == 'user_123'
        assert 'exp' in decoded
        assert 'iat' in decoded
    
    @patch('apps.users.jwt_service.requests.get')
    def test_verify_token_with_expired_token(self, mock_get):
        """Test token verification with an expired token"""
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.backends import default_backend
        import time
        
        # Generate RSA key pair
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        public_key = private_key.public_key()
        public_numbers = public_key.public_numbers()
        
        # Convert to JWK format
        import base64
        def int_to_base64(num):
            num_bytes = num.to_bytes((num.bit_length() + 7) // 8, byteorder='big')
            return base64.urlsafe_b64encode(num_bytes).decode('utf-8').rstrip('=')
        
        jwk = {
            'kid': 'test-key-id',
            'kty': 'RSA',
            'use': 'sig',
            'alg': 'RS256',
            'n': int_to_base64(public_numbers.n),
            'e': int_to_base64(public_numbers.e)
        }
        
        # Mock JWKS response
        mock_response = Mock()
        mock_response.json.return_value = {'keys': [jwk]}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Create an expired token
        from django.conf import settings
        payload = {
            'sub': 'user_123',
            'exp': int(time.time()) - 3600,  # Expired 1 hour ago
            'iat': int(time.time()) - 7200,
            'aud': settings.CLERK_PUBLISHABLE_KEY
        }
        
        # Sign token
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        token = pyjwt.encode(
            payload,
            private_pem,
            algorithm='RS256',
            headers={'kid': 'test-key-id'}
        )
        
        # Should raise TokenExpiredError
        with pytest.raises(TokenExpiredError) as exc_info:
            JWTVerificationService.verify_token(token)
        
        assert "expired" in str(exc_info.value).lower()
    
    @patch('apps.users.jwt_service.requests.get')
    def test_verify_token_with_invalid_signature(self, mock_get):
        """Test token verification with invalid signature"""
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.backends import default_backend
        import time
        
        # Generate two different RSA key pairs
        private_key_1 = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        private_key_2 = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        # Use public key from key 1 in JWKS
        public_key_1 = private_key_1.public_key()
        public_numbers = public_key_1.public_numbers()
        
        import base64
        def int_to_base64(num):
            num_bytes = num.to_bytes((num.bit_length() + 7) // 8, byteorder='big')
            return base64.urlsafe_b64encode(num_bytes).decode('utf-8').rstrip('=')
        
        jwk = {
            'kid': 'test-key-id',
            'kty': 'RSA',
            'use': 'sig',
            'alg': 'RS256',
            'n': int_to_base64(public_numbers.n),
            'e': int_to_base64(public_numbers.e)
        }
        
        # Mock JWKS response
        mock_response = Mock()
        mock_response.json.return_value = {'keys': [jwk]}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Create token signed with key 2 (different key)
        from django.conf import settings
        payload = {
            'sub': 'user_123',
            'exp': int(time.time()) + 3600,
            'iat': int(time.time()),
            'aud': settings.CLERK_PUBLISHABLE_KEY
        }
        
        # Sign with private key 2
        private_pem_2 = private_key_2.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        token = pyjwt.encode(
            payload,
            private_pem_2,
            algorithm='RS256',
            headers={'kid': 'test-key-id'}
        )
        
        # Should raise InvalidTokenError due to signature mismatch
        with pytest.raises(InvalidTokenError) as exc_info:
            JWTVerificationService.verify_token(token)
        
        assert "invalid" in str(exc_info.value).lower()
    
    @patch('apps.users.jwt_service.requests.get')
    def test_verify_token_with_missing_kid(self, mock_get):
        """Test token verification with missing kid in header"""
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.backends import default_backend
        import time
        
        # Generate RSA key pair
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        # Mock JWKS response
        mock_response = Mock()
        mock_response.json.return_value = {'keys': []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Create token without kid in header
        from django.conf import settings
        payload = {
            'sub': 'user_123',
            'exp': int(time.time()) + 3600,
            'iat': int(time.time()),
            'aud': settings.CLERK_PUBLISHABLE_KEY
        }
        
        # Sign token without kid header
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        token = pyjwt.encode(
            payload,
            private_pem,
            algorithm='RS256'
            # No headers parameter - no kid
        )
        
        # Should raise InvalidTokenError
        with pytest.raises(InvalidTokenError) as exc_info:
            JWTVerificationService.verify_token(token)
        
        assert "kid" in str(exc_info.value).lower()
    
    @patch('apps.users.jwt_service.requests.get')
    def test_verify_token_with_wrong_kid(self, mock_get):
        """Test token verification when kid doesn't match any key in JWKS"""
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.backends import default_backend
        import time
        
        # Generate RSA key pair
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        public_key = private_key.public_key()
        public_numbers = public_key.public_numbers()
        
        import base64
        def int_to_base64(num):
            num_bytes = num.to_bytes((num.bit_length() + 7) // 8, byteorder='big')
            return base64.urlsafe_b64encode(num_bytes).decode('utf-8').rstrip('=')
        
        # JWKS has key with kid='key-1'
        jwk = {
            'kid': 'key-1',
            'kty': 'RSA',
            'use': 'sig',
            'alg': 'RS256',
            'n': int_to_base64(public_numbers.n),
            'e': int_to_base64(public_numbers.e)
        }
        
        # Mock JWKS response
        mock_response = Mock()
        mock_response.json.return_value = {'keys': [jwk]}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Create token with kid='key-2' (doesn't exist in JWKS)
        from django.conf import settings
        payload = {
            'sub': 'user_123',
            'exp': int(time.time()) + 3600,
            'iat': int(time.time()),
            'aud': settings.CLERK_PUBLISHABLE_KEY
        }
        
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        token = pyjwt.encode(
            payload,
            private_pem,
            algorithm='RS256',
            headers={'kid': 'key-2'}  # Different kid
        )
        
        # Should raise InvalidTokenError
        with pytest.raises(InvalidTokenError) as exc_info:
            JWTVerificationService.verify_token(token)
        
        assert "no matching key" in str(exc_info.value).lower()
    
    @patch('apps.users.jwt_service.requests.get')
    def test_verify_token_with_malformed_token(self, mock_get):
        """Test token verification with malformed token"""
        # Mock JWKS response (won't be used but needed to avoid real API call)
        mock_response = Mock()
        mock_response.json.return_value = {'keys': []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Test with completely invalid token
        with pytest.raises(InvalidTokenError) as exc_info:
            JWTVerificationService.verify_token("not.a.valid.token")
        
        assert "malformed" in str(exc_info.value).lower() or "invalid" in str(exc_info.value).lower()
    
    @patch('apps.users.jwt_service.requests.get')
    def test_verify_token_with_wrong_audience(self, mock_get):
        """Test token verification with wrong audience"""
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.backends import default_backend
        import time
        
        # Generate RSA key pair
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        public_key = private_key.public_key()
        public_numbers = public_key.public_numbers()
        
        import base64
        def int_to_base64(num):
            num_bytes = num.to_bytes((num.bit_length() + 7) // 8, byteorder='big')
            return base64.urlsafe_b64encode(num_bytes).decode('utf-8').rstrip('=')
        
        jwk = {
            'kid': 'test-key-id',
            'kty': 'RSA',
            'use': 'sig',
            'alg': 'RS256',
            'n': int_to_base64(public_numbers.n),
            'e': int_to_base64(public_numbers.e)
        }
        
        # Mock JWKS response
        mock_response = Mock()
        mock_response.json.return_value = {'keys': [jwk]}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Create token with wrong audience
        payload = {
            'sub': 'user_123',
            'exp': int(time.time()) + 3600,
            'iat': int(time.time()),
            'aud': 'wrong_audience'  # Wrong audience
        }
        
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        token = pyjwt.encode(
            payload,
            private_pem,
            algorithm='RS256',
            headers={'kid': 'test-key-id'}
        )
        
        # Should raise InvalidTokenError
        with pytest.raises(InvalidTokenError) as exc_info:
            JWTVerificationService.verify_token(token)
        
        assert "audience" in str(exc_info.value).lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
