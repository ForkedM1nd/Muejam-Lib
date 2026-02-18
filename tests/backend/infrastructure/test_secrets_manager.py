"""
Unit tests for Secrets Manager

Tests the AWS Secrets Manager integration including:
- Secret retrieval
- Secret creation and updates
- Caching behavior
- Error handling
- Audit logging
"""

import os
import sys
import django
from pathlib import Path

# Configure Django settings before importing Django modules
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ['SKIP_CONFIG_VALIDATION'] = 'True'  # Skip validation for tests

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent.parent / 'apps' / 'backend'
sys.path.insert(0, str(backend_dir))

# Setup Django
django.setup()

import json
from unittest.mock import Mock, patch, MagicMock
import pytest
from botocore.exceptions import ClientError

from infrastructure.secrets_manager import (
    SecretsManager,
    SecretsManagerError,
    SecretNotFoundError,
    SecretAccessDeniedError,
    get_secrets_manager
)


@pytest.fixture
def secrets_manager():
    """Create a SecretsManager instance for testing"""
    with patch('infrastructure.secrets_manager.boto3.client'):
        sm = SecretsManager()
        sm.client = Mock()
        return sm


@pytest.fixture
def mock_secret_data():
    """Sample secret data for testing"""
    return {
        'username': 'test_user',
        'password': 'test_password',
        'host': 'localhost',
        'port': '5432'
    }


class TestSecretsManagerRetrieval:
    """Test secret retrieval functionality"""
    
    def test_get_secret_success(self, secrets_manager, mock_secret_data):
        """Test successful secret retrieval"""
        # Mock AWS response
        secrets_manager.client.get_secret_value.return_value = {
            'SecretString': json.dumps(mock_secret_data)
        }
        
        # Retrieve secret
        result = secrets_manager.get_secret('test-secret', use_cache=False)
        
        # Verify
        assert result == mock_secret_data
        secrets_manager.client.get_secret_value.assert_called_once()
    
    def test_get_secret_with_environment_prefix(self, secrets_manager, mock_secret_data):
        """Test that environment prefix is added to secret name"""
        secrets_manager.environment = 'production'
        secrets_manager.client.get_secret_value.return_value = {
            'SecretString': json.dumps(mock_secret_data)
        }
        
        secrets_manager.get_secret('database/primary', use_cache=False)
        
        # Verify full secret name includes environment
        call_args = secrets_manager.client.get_secret_value.call_args
        assert call_args[1]['SecretId'] == 'production/database/primary'
    
    def test_get_secret_not_found(self, secrets_manager):
        """Test handling of non-existent secret"""
        # Mock AWS error
        error_response = {'Error': {'Code': 'ResourceNotFoundException'}}
        secrets_manager.client.get_secret_value.side_effect = ClientError(
            error_response, 'GetSecretValue'
        )
        
        # Verify exception is raised
        with pytest.raises(SecretNotFoundError):
            secrets_manager.get_secret('nonexistent-secret', use_cache=False)
    
    def test_get_secret_access_denied(self, secrets_manager):
        """Test handling of access denied error"""
        # Mock AWS error
        error_response = {'Error': {'Code': 'AccessDeniedException'}}
        secrets_manager.client.get_secret_value.side_effect = ClientError(
            error_response, 'GetSecretValue'
        )
        
        # Verify exception is raised
        with pytest.raises(SecretAccessDeniedError):
            secrets_manager.get_secret('restricted-secret', use_cache=False)
    
    @patch('infrastructure.secrets_manager.cache')
    def test_get_secret_uses_cache(self, mock_cache, secrets_manager, mock_secret_data):
        """Test that caching is used when enabled"""
        # Setup cache to return data
        mock_cache.get.return_value = mock_secret_data
        
        # Retrieve secret with caching
        result = secrets_manager.get_secret('test-secret', use_cache=True)
        
        # Verify cache was checked
        mock_cache.get.assert_called_once()
        assert result == mock_secret_data
        
        # Verify AWS was not called
        secrets_manager.client.get_secret_value.assert_not_called()
    
    @patch('infrastructure.secrets_manager.cache')
    def test_get_secret_cache_miss(self, mock_cache, secrets_manager, mock_secret_data):
        """Test behavior when cache misses"""
        # Setup cache to return None (miss)
        mock_cache.get.return_value = None
        
        # Setup AWS to return data
        secrets_manager.client.get_secret_value.return_value = {
            'SecretString': json.dumps(mock_secret_data)
        }
        
        # Retrieve secret
        result = secrets_manager.get_secret('test-secret', use_cache=True)
        
        # Verify AWS was called
        secrets_manager.client.get_secret_value.assert_called_once()
        
        # Verify result was cached
        mock_cache.set.assert_called_once()
        assert result == mock_secret_data


class TestSecretsManagerCreation:
    """Test secret creation and update functionality"""
    
    def test_create_secret_success(self, secrets_manager, mock_secret_data):
        """Test successful secret creation"""
        secrets_manager.client.create_secret.return_value = {
            'ARN': 'arn:aws:secretsmanager:us-east-1:123456789012:secret:test-secret',
            'Name': 'test-secret'
        }
        
        result = secrets_manager.create_secret(
            'test-secret',
            mock_secret_data,
            description='Test secret'
        )
        
        assert result is True
        secrets_manager.client.create_secret.assert_called_once()
    
    def test_update_secret_success(self, secrets_manager, mock_secret_data):
        """Test successful secret update"""
        secrets_manager.client.update_secret.return_value = {
            'ARN': 'arn:aws:secretsmanager:us-east-1:123456789012:secret:test-secret',
            'Name': 'test-secret'
        }
        
        result = secrets_manager.update_secret('test-secret', mock_secret_data)
        
        assert result is True
        secrets_manager.client.update_secret.assert_called_once()
    
    @patch('infrastructure.secrets_manager.cache')
    def test_update_secret_invalidates_cache(self, mock_cache, secrets_manager, mock_secret_data):
        """Test that updating a secret invalidates the cache"""
        secrets_manager.client.update_secret.return_value = {}
        
        secrets_manager.update_secret('test-secret', mock_secret_data)
        
        # Verify cache was invalidated
        mock_cache.delete.assert_called_once()


class TestSecretsRotation:
    """Test secret rotation functionality"""
    
    @patch('secrets.choice')
    def test_rotate_database_password(self, mock_choice, secrets_manager):
        """Test database password rotation"""
        # Mock password generation
        mock_choice.return_value = 'a'
        
        # Mock get_secret to return current secret
        current_secret = {
            'host': 'localhost',
            'password': 'old_password'
        }
        secrets_manager.get_secret = Mock(return_value=current_secret)
        secrets_manager.update_secret = Mock(return_value=True)
        
        # Rotate password
        new_password = secrets_manager.rotate_database_password('primary')
        
        # Verify new password was generated
        assert len(new_password) == 32
        
        # Verify secret was updated
        secrets_manager.update_secret.assert_called_once()
        update_call = secrets_manager.update_secret.call_args
        assert 'password' in update_call[0][1]
        assert 'rotated_at' in update_call[0][1]
    
    @patch('secrets.token_urlsafe')
    def test_rotate_api_key(self, mock_token, secrets_manager):
        """Test API key rotation"""
        # Mock token generation
        mock_token.return_value = 'random_token_string'
        
        # Mock get_secret to return current secret
        current_secret = {
            'api_key': 'old_api_key'
        }
        secrets_manager.get_secret = Mock(return_value=current_secret)
        secrets_manager.update_secret = Mock(return_value=True)
        
        # Rotate API key
        new_api_key = secrets_manager.rotate_api_key('resend')
        
        # Verify new API key format
        assert new_api_key.startswith('RESE_')
        
        # Verify secret was updated with previous key stored
        secrets_manager.update_secret.assert_called_once()
        update_call = secrets_manager.update_secret.call_args
        updated_secret = update_call[0][1]
        assert 'api_key' in updated_secret
        assert 'previous_key' in updated_secret
        assert 'rotated_at' in updated_secret


class TestAuditLogging:
    """Test audit logging functionality"""
    
    @patch('infrastructure.secrets_manager.logger')
    def test_audit_successful_retrieval(self, mock_logger, secrets_manager, mock_secret_data):
        """Test that successful secret retrieval is logged"""
        secrets_manager.client.get_secret_value.return_value = {
            'SecretString': json.dumps(mock_secret_data)
        }
        
        secrets_manager.get_secret('test-secret', use_cache=False)
        
        # Verify info log was created
        assert mock_logger.info.called
    
    @patch('infrastructure.secrets_manager.logger')
    def test_audit_failed_retrieval(self, mock_logger, secrets_manager):
        """Test that failed secret retrieval is logged"""
        error_response = {'Error': {'Code': 'ResourceNotFoundException'}}
        secrets_manager.client.get_secret_value.side_effect = ClientError(
            error_response, 'GetSecretValue'
        )
        
        with pytest.raises(SecretNotFoundError):
            secrets_manager.get_secret('nonexistent-secret', use_cache=False)
        
        # Verify error log was created
        assert mock_logger.error.called


class TestAlerting:
    """Test alerting functionality"""
    
    @patch('infrastructure.secrets_manager.logger')
    def test_alert_on_unauthorized_access(self, mock_logger, secrets_manager):
        """Test that unauthorized access is logged critically"""
        error_response = {'Error': {'Code': 'AccessDeniedException'}}
        secrets_manager.client.get_secret_value.side_effect = ClientError(
            error_response, 'GetSecretValue'
        )
        
        with pytest.raises(SecretAccessDeniedError):
            secrets_manager.get_secret('restricted-secret', use_cache=False)
        
        # Verify critical log was created
        assert mock_logger.critical.called


class TestSingleton:
    """Test singleton pattern"""
    
    @patch('infrastructure.secrets_manager.boto3.client')
    def test_get_secrets_manager_singleton(self, mock_boto_client):
        """Test that get_secrets_manager returns singleton instance"""
        # Reset singleton
        import infrastructure.secrets_manager
        infrastructure.secrets_manager._secrets_manager = None
        
        # Get instance twice
        sm1 = get_secrets_manager()
        sm2 = get_secrets_manager()
        
        # Verify same instance
        assert sm1 is sm2
        
        # Verify boto3 client was only created once
        assert mock_boto_client.call_count == 1
