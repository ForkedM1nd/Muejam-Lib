"""
Tests for secure configuration management.

Tests verify that:
1. SECRET_KEY is required (no default)
2. SECRET_KEY is validated for insecure patterns
3. SECRET_KEY length is validated (minimum 50 characters)
4. Production configuration is validated
5. Clear error messages are provided
"""

import os
import pytest
from unittest.mock import patch
from django.core.exceptions import ImproperlyConfigured
from config.secure_settings import SecureConfig


class TestSecureConfig:
    """Test SecureConfig class"""
    
    def test_get_required_with_value(self):
        """Test get_required returns value when set"""
        with patch.dict(os.environ, {'TEST_VAR': 'test_value'}):
            result = SecureConfig.get_required('TEST_VAR', 'Test variable')
            assert result == 'test_value'
    
    def test_get_required_without_value(self):
        """Test get_required raises error when not set"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ImproperlyConfigured) as exc_info:
                SecureConfig.get_required('MISSING_VAR', 'Missing variable')
            
            assert 'MISSING_VAR' in str(exc_info.value)
            assert 'Missing variable' in str(exc_info.value)


class TestGetSecretKey:
    """Test SECRET_KEY validation"""
    
    def test_missing_secret_key(self):
        """Test that missing SECRET_KEY raises error"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ImproperlyConfigured) as exc_info:
                SecureConfig.get_secret_key()
            
            assert 'SECRET_KEY environment variable must be set' in str(exc_info.value)
            assert 'get_random_secret_key' in str(exc_info.value)
    
    def test_insecure_secret_key_django_insecure(self):
        """Test that django-insecure pattern is rejected"""
        with patch.dict(os.environ, {'SECRET_KEY': 'django-insecure-test-key-1234567890123456789012345678901234567890'}):
            with pytest.raises(ImproperlyConfigured) as exc_info:
                SecureConfig.get_secret_key()
            
            assert 'appears to be an example value' in str(exc_info.value)
            assert 'django-insecure' in str(exc_info.value)
    
    def test_insecure_secret_key_change_this(self):
        """Test that change-this pattern is rejected"""
        with patch.dict(os.environ, {'SECRET_KEY': 'change-this-in-production-1234567890123456789012345678901234567890'}):
            with pytest.raises(ImproperlyConfigured) as exc_info:
                SecureConfig.get_secret_key()
            
            assert 'appears to be an example value' in str(exc_info.value)
    
    def test_insecure_secret_key_example(self):
        """Test that example pattern is rejected"""
        with patch.dict(os.environ, {'SECRET_KEY': 'example-secret-key-1234567890123456789012345678901234567890'}):
            with pytest.raises(ImproperlyConfigured) as exc_info:
                SecureConfig.get_secret_key()
            
            assert 'appears to be an example value' in str(exc_info.value)
    
    def test_short_secret_key(self):
        """Test that short SECRET_KEY is rejected"""
        with patch.dict(os.environ, {'SECRET_KEY': 'short-key-12345'}):
            with pytest.raises(ImproperlyConfigured) as exc_info:
                SecureConfig.get_secret_key()
            
            assert 'too short' in str(exc_info.value)
            assert 'at least 50 characters' in str(exc_info.value)
    
    def test_valid_secret_key(self):
        """Test that valid SECRET_KEY is accepted"""
        valid_key = 'a' * 50 + 'b' * 20  # 70 character key with no insecure patterns
        with patch.dict(os.environ, {'SECRET_KEY': valid_key}):
            result = SecureConfig.get_secret_key()
            assert result == valid_key
    
    def test_generated_secret_key(self):
        """Test that Django-generated key is accepted"""
        # Simulate a real Django-generated key
        generated_key = 'django-insecure-abc123!@#$%^&*()_+-=[]{}|;:,.<>?/~`1234567890abcdefghijklmnopqrstuvwxyz'
        # This should fail because it contains 'django-insecure'
        with patch.dict(os.environ, {'SECRET_KEY': generated_key}):
            with pytest.raises(ImproperlyConfigured):
                SecureConfig.get_secret_key()
        
        # Test with a proper production key (no insecure patterns)
        production_key = 'abc123!@#$%^&*()_+-=[]{}|;:,.<>?/~`1234567890abcdefghijklmnopqrstuvwxyz'
        with patch.dict(os.environ, {'SECRET_KEY': production_key}):
            result = SecureConfig.get_secret_key()
            assert result == production_key


class TestValidateProductionConfig:
    """Test production configuration validation"""
    
    def test_debug_true_in_production(self):
        """Test that DEBUG=True is rejected in production"""
        with patch.dict(os.environ, {
            'DEBUG': 'True',
            'SECURE_SSL_REDIRECT': 'True',
            'SENTRY_DSN': 'https://example.com',
            'ALLOWED_HOSTS': 'api.example.com',
            'DATABASE_URL': 'postgresql://localhost/db',
            'VALKEY_URL': 'redis://localhost:6379'
        }):
            with pytest.raises(ImproperlyConfigured) as exc_info:
                SecureConfig.validate_production_config()
            
            assert 'DEBUG must be False' in str(exc_info.value)
    
    def test_ssl_redirect_false_in_production(self):
        """Test that SECURE_SSL_REDIRECT=False is rejected"""
        with patch.dict(os.environ, {
            'DEBUG': 'False',
            'SECURE_SSL_REDIRECT': 'False',
            'SENTRY_DSN': 'https://example.com',
            'ALLOWED_HOSTS': 'api.example.com',
            'DATABASE_URL': 'postgresql://localhost/db',
            'VALKEY_URL': 'redis://localhost:6379'
        }):
            with pytest.raises(ImproperlyConfigured) as exc_info:
                SecureConfig.validate_production_config()
            
            assert 'SECURE_SSL_REDIRECT must be True' in str(exc_info.value)
    
    def test_missing_allowed_hosts(self):
        """Test that missing ALLOWED_HOSTS is rejected"""
        with patch.dict(os.environ, {
            'DEBUG': 'False',
            'SECURE_SSL_REDIRECT': 'True',
            'SENTRY_DSN': 'https://example.com',
            'DATABASE_URL': 'postgresql://localhost/db',
            'VALKEY_URL': 'redis://localhost:6379'
        }, clear=True):
            with pytest.raises(ImproperlyConfigured) as exc_info:
                SecureConfig.validate_production_config()
            
            assert 'ALLOWED_HOSTS must be properly configured' in str(exc_info.value)
    
    def test_missing_database_url(self):
        """Test that missing DATABASE_URL is rejected"""
        with patch.dict(os.environ, {
            'DEBUG': 'False',
            'SECURE_SSL_REDIRECT': 'True',
            'SENTRY_DSN': 'https://example.com',
            'ALLOWED_HOSTS': 'api.example.com',
            'VALKEY_URL': 'redis://localhost:6379'
        }, clear=True):
            with pytest.raises(ImproperlyConfigured) as exc_info:
                SecureConfig.validate_production_config()
            
            assert 'DATABASE_URL must be set' in str(exc_info.value)
    
    def test_missing_redis_url(self):
        """Test that missing Redis URL is rejected"""
        with patch.dict(os.environ, {
            'DEBUG': 'False',
            'SECURE_SSL_REDIRECT': 'True',
            'SENTRY_DSN': 'https://example.com',
            'ALLOWED_HOSTS': 'api.example.com',
            'DATABASE_URL': 'postgresql://localhost/db'
        }, clear=True):
            with pytest.raises(ImproperlyConfigured) as exc_info:
                SecureConfig.validate_production_config()
            
            assert 'VALKEY_URL or REDIS_URL must be set' in str(exc_info.value)
    
    def test_valid_production_config(self):
        """Test that valid production config passes"""
        with patch.dict(os.environ, {
            'DEBUG': 'False',
            'SECURE_SSL_REDIRECT': 'True',
            'SENTRY_DSN': 'https://example.com',
            'ALLOWED_HOSTS': 'api.example.com',
            'DATABASE_URL': 'postgresql://localhost/db',
            'VALKEY_URL': 'redis://localhost:6379'
        }):
            # Should not raise
            SecureConfig.validate_production_config()


class TestValidateClerkConfig:
    """Test Clerk configuration validation"""
    
    def test_missing_clerk_secret_key(self):
        """Test that missing CLERK_SECRET_KEY is rejected"""
        with patch.dict(os.environ, {'CLERK_PUBLISHABLE_KEY': 'pk_test_123'}, clear=True):
            with pytest.raises(ImproperlyConfigured) as exc_info:
                SecureConfig.validate_clerk_config()
            
            assert 'CLERK_SECRET_KEY must be set' in str(exc_info.value)
    
    def test_missing_clerk_publishable_key(self):
        """Test that missing CLERK_PUBLISHABLE_KEY is rejected"""
        with patch.dict(os.environ, {'CLERK_SECRET_KEY': 'sk_test_123'}, clear=True):
            with pytest.raises(ImproperlyConfigured) as exc_info:
                SecureConfig.validate_clerk_config()
            
            assert 'CLERK_PUBLISHABLE_KEY must be set' in str(exc_info.value)
    
    def test_valid_clerk_config(self):
        """Test that valid Clerk config passes"""
        with patch.dict(os.environ, {
            'CLERK_SECRET_KEY': 'sk_test_123',
            'CLERK_PUBLISHABLE_KEY': 'pk_test_123'
        }):
            # Should not raise
            SecureConfig.validate_clerk_config()


class TestValidateAll:
    """Test complete configuration validation"""
    
    def test_validate_all_development(self):
        """Test that development environment validation works"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'a' * 70,
            'CLERK_SECRET_KEY': 'sk_test_123',
            'CLERK_PUBLISHABLE_KEY': 'pk_test_123',
            'ENVIRONMENT': 'development'
        }):
            # Should not raise
            SecureConfig.validate_all()
    
    def test_validate_all_production(self):
        """Test that production environment validation works"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'a' * 70,
            'CLERK_SECRET_KEY': 'sk_test_123',
            'CLERK_PUBLISHABLE_KEY': 'pk_test_123',
            'ENVIRONMENT': 'production',
            'DEBUG': 'False',
            'SECURE_SSL_REDIRECT': 'True',
            'SENTRY_DSN': 'https://example.com',
            'ALLOWED_HOSTS': 'api.example.com',
            'DATABASE_URL': 'postgresql://localhost/db',
            'VALKEY_URL': 'redis://localhost:6379'
        }):
            # Should not raise
            SecureConfig.validate_all()
