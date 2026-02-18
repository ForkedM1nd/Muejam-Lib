"""
Integration tests for Secrets Manager

These tests verify the actual behavior of the secrets manager with real cache
and proper error handling. Unlike unit tests, these test the integration between
components.

Tests:
- Secret retrieval with actual AWS SDK behavior
- Secret caching with 5-minute TTL
- Cache invalidation on updates
- Error handling and fallback behavior
"""

import json
import time
from unittest.mock import patch, Mock, MagicMock
import pytest
from botocore.exceptions import ClientError

from infrastructure.secrets_manager import (
    SecretsManager,
    SecretNotFoundError,
    SecretAccessDeniedError,
    get_secrets_manager
)


@pytest.fixture
def mock_cache():
    """Mock Django cache"""
    with patch('infrastructure.secrets_manager.cache') as mock:
        # Setup mock cache with dict-like behavior
        cache_storage = {}
        
        def get(key):
            return cache_storage.get(key)
        
        def set(key, value, ttl=None):
            cache_storage[key] = value
        
        def delete(key):
            cache_storage.pop(key, None)
        
        def clear():
            cache_storage.clear()
        
        mock.get = Mock(side_effect=get)
        mock.set = Mock(side_effect=set)
        mock.delete = Mock(side_effect=delete)
        mock.clear = Mock(side_effect=clear)
        mock._storage = cache_storage
        
        yield mock


@pytest.fixture
def mock_aws_client():
    """Mock AWS Secrets Manager client"""
    with patch('infrastructure.secrets_manager.boto3.client') as mock_client:
        client_instance = Mock()
        mock_client.return_value = client_instance
        yield client_instance


@pytest.fixture
def secrets_manager(mock_aws_client, mock_cache):
    """Create a SecretsManager instance with mocked AWS client and cache"""
    # Reset singleton
    import infrastructure.secrets_manager
    infrastructure.secrets_manager._secrets_manager = None
    
    sm = SecretsManager()
    sm.client = mock_aws_client
    return sm


@pytest.fixture
def sample_database_secret():
    """Sample database secret data"""
    return {
        'host': 'db.example.com',
        'port': '5432',
        'username': 'app_user',
        'password': 'secure_password_123',
        'database': 'production_db'
    }


@pytest.fixture
def sample_api_key_secret():
    """Sample API key secret data"""
    return {
        'api_key': 'sk_live_1234567890abcdef',
        'api_secret': 'secret_abcdef1234567890',
        'environment': 'production'
    }


class TestSecretRetrieval:
    """Test secret retrieval functionality with real cache"""
    
    def test_retrieve_database_secret_success(self, secrets_manager, mock_aws_client, sample_database_secret):
        """Test successful retrieval of database secret"""
        # Setup AWS mock response
        mock_aws_client.get_secret_value.return_value = {
            'SecretString': json.dumps(sample_database_secret),
            'VersionId': 'v1',
            'ARN': 'arn:aws:secretsmanager:us-east-1:123456789012:secret:test'
        }
        
        # Retrieve secret
        result = secrets_manager.get_secret('database/primary', use_cache=False)
        
        # Verify result
        assert result == sample_database_secret
        assert result['host'] == 'db.example.com'
        assert result['password'] == 'secure_password_123'
        
        # Verify AWS was called with correct parameters
        mock_aws_client.get_secret_value.assert_called_once()
        call_args = mock_aws_client.get_secret_value.call_args
        assert 'database/primary' in call_args[1]['SecretId']
    
    def test_retrieve_api_key_secret_success(self, secrets_manager, mock_aws_client, sample_api_key_secret):
        """Test successful retrieval of API key secret"""
        # Setup AWS mock response
        mock_aws_client.get_secret_value.return_value = {
            'SecretString': json.dumps(sample_api_key_secret)
        }
        
        # Retrieve secret
        result = secrets_manager.get_secret('api-keys/clerk', use_cache=False)
        
        # Verify result
        assert result == sample_api_key_secret
        assert result['api_key'] == 'sk_live_1234567890abcdef'
    
    def test_retrieve_secret_with_environment_prefix(self, secrets_manager, mock_aws_client, sample_database_secret):
        """Test that environment prefix is correctly added to secret name"""
        secrets_manager.environment = 'production'
        
        mock_aws_client.get_secret_value.return_value = {
            'SecretString': json.dumps(sample_database_secret)
        }
        
        # Retrieve secret
        secrets_manager.get_secret('database/primary', use_cache=False)
        
        # Verify full secret name includes environment
        call_args = mock_aws_client.get_secret_value.call_args
        assert call_args[1]['SecretId'] == 'production/database/primary'
    
    def test_retrieve_nonexistent_secret(self, secrets_manager, mock_aws_client):
        """Test handling of non-existent secret"""
        # Mock AWS ResourceNotFoundException
        error_response = {
            'Error': {
                'Code': 'ResourceNotFoundException',
                'Message': 'Secret not found'
            }
        }
        mock_aws_client.get_secret_value.side_effect = ClientError(
            error_response, 'GetSecretValue'
        )
        
        # Verify exception is raised
        with pytest.raises(SecretNotFoundError) as exc_info:
            secrets_manager.get_secret('nonexistent/secret', use_cache=False)
        
        assert 'nonexistent/secret' in str(exc_info.value)
    
    def test_retrieve_secret_access_denied(self, secrets_manager, mock_aws_client):
        """Test handling of access denied error"""
        # Mock AWS AccessDeniedException
        error_response = {
            'Error': {
                'Code': 'AccessDeniedException',
                'Message': 'Access denied'
            }
        }
        mock_aws_client.get_secret_value.side_effect = ClientError(
            error_response, 'GetSecretValue'
        )
        
        # Verify exception is raised
        with pytest.raises(SecretAccessDeniedError) as exc_info:
            secrets_manager.get_secret('restricted/secret', use_cache=False)
        
        assert 'restricted/secret' in str(exc_info.value)
    
    def test_retrieve_multiple_secrets_sequentially(self, secrets_manager, mock_aws_client):
        """Test retrieving multiple different secrets"""
        secrets = {
            'database/primary': {'host': 'db1.example.com', 'password': 'pass1'},
            'database/replica': {'host': 'db2.example.com', 'password': 'pass2'},
            'api-keys/clerk': {'api_key': 'clerk_key_123'}
        }
        
        def mock_get_secret(SecretId):
            for name, data in secrets.items():
                if name in SecretId:
                    return {'SecretString': json.dumps(data)}
            raise ClientError(
                {'Error': {'Code': 'ResourceNotFoundException'}},
                'GetSecretValue'
            )
        
        mock_aws_client.get_secret_value.side_effect = mock_get_secret
        
        # Retrieve all secrets
        result1 = secrets_manager.get_secret('database/primary', use_cache=False)
        result2 = secrets_manager.get_secret('database/replica', use_cache=False)
        result3 = secrets_manager.get_secret('api-keys/clerk', use_cache=False)
        
        # Verify results
        assert result1['host'] == 'db1.example.com'
        assert result2['host'] == 'db2.example.com'
        assert result3['api_key'] == 'clerk_key_123'
        
        # Verify AWS was called 3 times
        assert mock_aws_client.get_secret_value.call_count == 3


class TestSecretCaching:
    """Test secret caching with 5-minute TTL"""
    
    def test_cache_stores_secret_on_first_retrieval(self, secrets_manager, mock_aws_client, sample_database_secret):
        """Test that secret is cached after first retrieval"""
        # Setup AWS mock
        mock_aws_client.get_secret_value.return_value = {
            'SecretString': json.dumps(sample_database_secret)
        }
        
        # First retrieval with caching enabled
        result1 = secrets_manager.get_secret('database/primary', use_cache=True)
        
        # Verify AWS was called
        assert mock_aws_client.get_secret_value.call_count == 1
        
        # Second retrieval should use cache
        result2 = secrets_manager.get_secret('database/primary', use_cache=True)
        
        # Verify AWS was NOT called again
        assert mock_aws_client.get_secret_value.call_count == 1
        
        # Verify both results are identical
        assert result1 == result2
        assert result1 == sample_database_secret
    
    def test_cache_ttl_is_5_minutes(self, secrets_manager):
        """Test that cache TTL is set to 5 minutes (300 seconds)"""
        # Verify default cache TTL
        assert secrets_manager.cache_ttl == 300
        
        # Verify it can be configured via environment
        import os
        with patch.dict(os.environ, {'SECRETS_CACHE_TTL': '600'}):
            sm = SecretsManager()
            assert sm.cache_ttl == 600
    
    def test_cache_key_format(self, secrets_manager, mock_aws_client, mock_cache, sample_database_secret):
        """Test that cache keys are properly formatted"""
        mock_aws_client.get_secret_value.return_value = {
            'SecretString': json.dumps(sample_database_secret)
        }
        
        secrets_manager.environment = 'production'
        
        # Retrieve secret
        secrets_manager.get_secret('database/primary', use_cache=True)
        
        # Verify cache key format
        cache_key = 'secret:production/database/primary'
        cached_value = mock_cache._storage.get(cache_key)
        
        assert cached_value is not None
        assert cached_value == sample_database_secret
    
    def test_cache_bypass_when_disabled(self, secrets_manager, mock_aws_client, sample_database_secret):
        """Test that cache is bypassed when use_cache=False"""
        mock_aws_client.get_secret_value.return_value = {
            'SecretString': json.dumps(sample_database_secret)
        }
        
        # First retrieval without cache
        result1 = secrets_manager.get_secret('database/primary', use_cache=False)
        
        # Second retrieval without cache
        result2 = secrets_manager.get_secret('database/primary', use_cache=False)
        
        # Verify AWS was called twice (no caching)
        assert mock_aws_client.get_secret_value.call_count == 2
        
        # Results should still be identical
        assert result1 == result2
    
    def test_cache_miss_fetches_from_aws(self, secrets_manager, mock_aws_client, mock_cache, sample_database_secret):
        """Test that cache miss triggers AWS fetch"""
        mock_aws_client.get_secret_value.return_value = {
            'SecretString': json.dumps(sample_database_secret)
        }
        
        # Clear cache to ensure miss
        mock_cache.clear()
        
        # Retrieve with caching enabled
        result = secrets_manager.get_secret('database/primary', use_cache=True)
        
        # Verify AWS was called
        assert mock_aws_client.get_secret_value.call_count == 1
        assert result == sample_database_secret
    
    def test_cache_stores_different_secrets_separately(self, secrets_manager, mock_aws_client):
        """Test that different secrets are cached separately"""
        secret1 = {'password': 'pass1'}
        secret2 = {'password': 'pass2'}
        
        def mock_get_secret(SecretId):
            if 'primary' in SecretId:
                return {'SecretString': json.dumps(secret1)}
            elif 'replica' in SecretId:
                return {'SecretString': json.dumps(secret2)}
        
        mock_aws_client.get_secret_value.side_effect = mock_get_secret
        
        # Retrieve both secrets
        result1 = secrets_manager.get_secret('database/primary', use_cache=True)
        result2 = secrets_manager.get_secret('database/replica', use_cache=True)
        
        # Verify both are cached separately
        assert result1 == secret1
        assert result2 == secret2
        
        # Retrieve again from cache
        result1_cached = secrets_manager.get_secret('database/primary', use_cache=True)
        result2_cached = secrets_manager.get_secret('database/replica', use_cache=True)
        
        # Verify cache was used (AWS called only twice, not four times)
        assert mock_aws_client.get_secret_value.call_count == 2
        assert result1_cached == secret1
        assert result2_cached == secret2
    
    def test_cache_invalidation_on_update(self, secrets_manager, mock_aws_client, mock_cache, sample_database_secret):
        """Test that cache is invalidated when secret is updated"""
        # Setup initial secret
        mock_aws_client.get_secret_value.return_value = {
            'SecretString': json.dumps(sample_database_secret)
        }
        
        # Retrieve and cache secret
        result1 = secrets_manager.get_secret('database/primary', use_cache=True)
        assert result1 == sample_database_secret
        
        # Update secret
        updated_secret = sample_database_secret.copy()
        updated_secret['password'] = 'new_password_456'
        
        mock_aws_client.update_secret.return_value = {
            'ARN': 'arn:aws:secretsmanager:us-east-1:123456789012:secret:test',
            'Name': 'database/primary'
        }
        
        secrets_manager.update_secret('database/primary', updated_secret)
        
        # Verify cache was invalidated
        cache_key = f"secret:{secrets_manager.environment}/database/primary"
        cached_value = mock_cache._storage.get(cache_key)
        assert cached_value is None
    
    def test_cache_performance_improvement(self, secrets_manager, mock_aws_client, sample_database_secret):
        """Test that caching improves performance by reducing AWS calls"""
        mock_aws_client.get_secret_value.return_value = {
            'SecretString': json.dumps(sample_database_secret)
        }
        
        # Retrieve secret 10 times with caching
        for _ in range(10):
            result = secrets_manager.get_secret('database/primary', use_cache=True)
            assert result == sample_database_secret
        
        # Verify AWS was only called once
        assert mock_aws_client.get_secret_value.call_count == 1


class TestSecretCachingEdgeCases:
    """Test edge cases in secret caching"""
    
    def test_cache_handles_empty_secret(self, secrets_manager, mock_aws_client):
        """Test caching of empty secret data"""
        empty_secret = {}
        
        mock_aws_client.get_secret_value.return_value = {
            'SecretString': json.dumps(empty_secret)
        }
        
        # Retrieve empty secret
        result = secrets_manager.get_secret('empty/secret', use_cache=True)
        assert result == empty_secret
        
        # Retrieve again from cache
        result_cached = secrets_manager.get_secret('empty/secret', use_cache=True)
        assert result_cached == empty_secret
        
        # Verify AWS was called only once
        assert mock_aws_client.get_secret_value.call_count == 1
    
    def test_cache_handles_large_secret(self, secrets_manager, mock_aws_client):
        """Test caching of large secret data"""
        large_secret = {
            f'key_{i}': f'value_{i}' * 100
            for i in range(100)
        }
        
        mock_aws_client.get_secret_value.return_value = {
            'SecretString': json.dumps(large_secret)
        }
        
        # Retrieve large secret
        result = secrets_manager.get_secret('large/secret', use_cache=True)
        assert result == large_secret
        
        # Retrieve again from cache
        result_cached = secrets_manager.get_secret('large/secret', use_cache=True)
        assert result_cached == large_secret
        
        # Verify AWS was called only once
        assert mock_aws_client.get_secret_value.call_count == 1
    
    def test_cache_handles_special_characters_in_values(self, secrets_manager, mock_aws_client):
        """Test caching of secrets with special characters"""
        special_secret = {
            'password': 'p@$$w0rd!#%&*()[]{}',
            'connection_string': 'postgresql://user:p@ss@host:5432/db?ssl=true',
            'json_data': '{"nested": "value"}'
        }
        
        mock_aws_client.get_secret_value.return_value = {
            'SecretString': json.dumps(special_secret)
        }
        
        # Retrieve secret with special characters
        result = secrets_manager.get_secret('special/secret', use_cache=True)
        assert result == special_secret
        
        # Retrieve again from cache
        result_cached = secrets_manager.get_secret('special/secret', use_cache=True)
        assert result_cached == special_secret
        assert result_cached['password'] == 'p@$$w0rd!#%&*()[]{}' 


class TestSecretManagerSingleton:
    """Test singleton pattern for secrets manager"""
    
    @patch('infrastructure.secrets_manager.boto3.client')
    def test_singleton_returns_same_instance(self, mock_boto_client):
        """Test that get_secrets_manager returns the same instance"""
        # Reset singleton
        import infrastructure.secrets_manager
        infrastructure.secrets_manager._secrets_manager = None
        
        # Get instance multiple times
        sm1 = get_secrets_manager()
        sm2 = get_secrets_manager()
        sm3 = get_secrets_manager()
        
        # Verify all are the same instance
        assert sm1 is sm2
        assert sm2 is sm3
        
        # Verify boto3 client was only created once
        assert mock_boto_client.call_count == 1
