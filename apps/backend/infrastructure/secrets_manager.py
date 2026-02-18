"""
AWS Secrets Manager Integration

This module provides secure secrets management using AWS Secrets Manager.
Implements Requirements 30.2, 30.4, 30.5, 30.7, 30.8 from the production readiness spec.

Features:
- Secure storage and retrieval of sensitive configuration
- Automatic secret rotation for database passwords and API keys
- Access control and audit logging
- Caching to reduce API calls and improve performance
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import boto3
from botocore.exceptions import ClientError, BotoCoreError
from django.core.cache import cache

logger = logging.getLogger(__name__)


class SecretsManagerError(Exception):
    """Base exception for secrets manager errors"""
    pass


class SecretNotFoundError(SecretsManagerError):
    """Raised when a secret is not found"""
    pass


class SecretAccessDeniedError(SecretsManagerError):
    """Raised when access to a secret is denied"""
    pass


class SecretsManager:
    """
    AWS Secrets Manager client for secure configuration management.
    
    Provides methods to:
    - Retrieve secrets from AWS Secrets Manager
    - Cache secrets to reduce API calls
    - Rotate database passwords and API keys
    - Audit secret access
    """
    
    def __init__(self):
        """Initialize AWS Secrets Manager client"""
        self.region = os.getenv('AWS_REGION', 'us-east-1')
        self.environment = os.getenv('ENVIRONMENT', 'development')
        self.cache_ttl = int(os.getenv('SECRETS_CACHE_TTL', '300'))  # 5 minutes default
        
        try:
            self.client = boto3.client(
                'secretsmanager',
                region_name=self.region
            )
        except Exception as e:
            logger.error(f"Failed to initialize Secrets Manager client: {e}")
            raise SecretsManagerError(f"Failed to initialize Secrets Manager: {e}")
    
    def get_secret(self, secret_name: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Retrieve a secret from AWS Secrets Manager.
        
        Args:
            secret_name: Name of the secret to retrieve
            use_cache: Whether to use cached value if available
        
        Returns:
            Dictionary containing secret key-value pairs
        
        Raises:
            SecretNotFoundError: If secret doesn't exist
            SecretAccessDeniedError: If access is denied
            SecretsManagerError: For other errors
        
        Requirements: 30.2 - Store sensitive configuration in Secrets Manager
        """
        # Build full secret name with environment prefix
        full_secret_name = self._build_secret_name(secret_name)
        
        # Check cache first
        if use_cache:
            cached_secret = self._get_from_cache(full_secret_name)
            if cached_secret is not None:
                logger.debug(f"Retrieved secret '{secret_name}' from cache")
                return cached_secret
        
        try:
            # Retrieve secret from AWS
            response = self.client.get_secret_value(SecretId=full_secret_name)
            
            # Parse secret value
            if 'SecretString' in response:
                secret_data = json.loads(response['SecretString'])
            else:
                # Binary secrets not supported in this implementation
                raise SecretsManagerError(f"Binary secrets not supported: {secret_name}")
            
            # Audit secret access (Requirement 30.8)
            self._audit_secret_access(full_secret_name, 'retrieve', success=True)
            
            # Cache the secret
            if use_cache:
                self._save_to_cache(full_secret_name, secret_data)
            
            logger.info(f"Successfully retrieved secret '{secret_name}'")
            return secret_data
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            
            if error_code == 'ResourceNotFoundException':
                self._audit_secret_access(full_secret_name, 'retrieve', success=False, error='not_found')
                raise SecretNotFoundError(f"Secret not found: {secret_name}")
            
            elif error_code == 'AccessDeniedException':
                # Alert on unauthorized access (Requirement 30.8)
                self._alert_unauthorized_access(full_secret_name)
                self._audit_secret_access(full_secret_name, 'retrieve', success=False, error='access_denied')
                raise SecretAccessDeniedError(f"Access denied to secret: {secret_name}")
            
            else:
                self._audit_secret_access(full_secret_name, 'retrieve', success=False, error=error_code)
                raise SecretsManagerError(f"Failed to retrieve secret '{secret_name}': {e}")
        
        except (BotoCoreError, Exception) as e:
            self._audit_secret_access(full_secret_name, 'retrieve', success=False, error=str(e))
            raise SecretsManagerError(f"Unexpected error retrieving secret '{secret_name}': {e}")
    
    def create_secret(self, secret_name: str, secret_value: Dict[str, Any], 
                     description: str = "") -> bool:
        """
        Create a new secret in AWS Secrets Manager.
        
        Args:
            secret_name: Name of the secret
            secret_value: Dictionary of secret key-value pairs
            description: Optional description of the secret
        
        Returns:
            True if successful
        
        Raises:
            SecretsManagerError: If creation fails
        """
        full_secret_name = self._build_secret_name(secret_name)
        
        try:
            self.client.create_secret(
                Name=full_secret_name,
                Description=description,
                SecretString=json.dumps(secret_value)
            )
            
            self._audit_secret_access(full_secret_name, 'create', success=True)
            logger.info(f"Successfully created secret '{secret_name}'")
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            self._audit_secret_access(full_secret_name, 'create', success=False, error=error_code)
            raise SecretsManagerError(f"Failed to create secret '{secret_name}': {e}")
    
    def update_secret(self, secret_name: str, secret_value: Dict[str, Any]) -> bool:
        """
        Update an existing secret in AWS Secrets Manager.
        
        Args:
            secret_name: Name of the secret
            secret_value: New dictionary of secret key-value pairs
        
        Returns:
            True if successful
        
        Raises:
            SecretsManagerError: If update fails
        """
        full_secret_name = self._build_secret_name(secret_name)
        
        try:
            self.client.update_secret(
                SecretId=full_secret_name,
                SecretString=json.dumps(secret_value)
            )
            
            # Invalidate cache
            self._invalidate_cache(full_secret_name)
            
            self._audit_secret_access(full_secret_name, 'update', success=True)
            logger.info(f"Successfully updated secret '{secret_name}'")
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            self._audit_secret_access(full_secret_name, 'update', success=False, error=error_code)
            raise SecretsManagerError(f"Failed to update secret '{secret_name}': {e}")
    
    def rotate_database_password(self, database_name: str) -> str:
        """
        Rotate database password and update in Secrets Manager.
        
        Args:
            database_name: Name of the database (e.g., 'primary', 'replica')
        
        Returns:
            New password
        
        Requirements: 30.4 - Automatic secret rotation for database passwords
        """
        import secrets
        import string
        
        # Generate strong password
        alphabet = string.ascii_letters + string.digits + string.punctuation
        new_password = ''.join(secrets.choice(alphabet) for _ in range(32))
        
        secret_name = f"database/{database_name}"
        
        try:
            # Get current secret
            current_secret = self.get_secret(secret_name, use_cache=False)
            
            # Update password in secret
            current_secret['password'] = new_password
            current_secret['rotated_at'] = datetime.utcnow().isoformat()
            
            # Save updated secret
            self.update_secret(secret_name, current_secret)
            
            logger.info(f"Successfully rotated password for database '{database_name}'")
            return new_password
            
        except Exception as e:
            logger.error(f"Failed to rotate database password for '{database_name}': {e}")
            raise SecretsManagerError(f"Password rotation failed: {e}")
    
    def rotate_api_key(self, service_name: str) -> str:
        """
        Rotate API key for external service and update in Secrets Manager.
        
        Args:
            service_name: Name of the service (e.g., 'resend', 'aws', 'clerk')
        
        Returns:
            New API key
        
        Requirements: 30.5 - API key rotation
        """
        import secrets
        
        # Generate new API key (format: prefix_randomstring)
        prefix = service_name[:4].upper()
        random_part = secrets.token_urlsafe(32)
        new_api_key = f"{prefix}_{random_part}"
        
        secret_name = f"api-keys/{service_name}"
        
        try:
            # Get current secret
            current_secret = self.get_secret(secret_name, use_cache=False)
            
            # Store old key for rollback
            current_secret['previous_key'] = current_secret.get('api_key', '')
            current_secret['api_key'] = new_api_key
            current_secret['rotated_at'] = datetime.utcnow().isoformat()
            
            # Save updated secret
            self.update_secret(secret_name, current_secret)
            
            logger.info(f"Successfully rotated API key for service '{service_name}'")
            return new_api_key
            
        except Exception as e:
            logger.error(f"Failed to rotate API key for '{service_name}': {e}")
            raise SecretsManagerError(f"API key rotation failed: {e}")
    
    def _build_secret_name(self, secret_name: str) -> str:
        """Build full secret name with environment prefix"""
        return f"{self.environment}/{secret_name}"
    
    def _get_from_cache(self, secret_name: str) -> Optional[Dict[str, Any]]:
        """Retrieve secret from cache"""
        cache_key = f"secret:{secret_name}"
        return cache.get(cache_key)
    
    def _save_to_cache(self, secret_name: str, secret_data: Dict[str, Any]) -> None:
        """Save secret to cache"""
        cache_key = f"secret:{secret_name}"
        cache.set(cache_key, secret_data, self.cache_ttl)
    
    def _invalidate_cache(self, secret_name: str) -> None:
        """Invalidate cached secret"""
        cache_key = f"secret:{secret_name}"
        cache.delete(cache_key)
    
    def _audit_secret_access(self, secret_name: str, action: str, 
                            success: bool, error: Optional[str] = None) -> None:
        """
        Audit secret access for compliance and security monitoring.
        
        Requirements: 30.8 - Audit all secret access
        """
        from apps.admin.audit_log_service import AuditLogService
        
        try:
            audit_service = AuditLogService()
            audit_service.log_action(
                user_id=None,  # System action
                action_type=f'secret_{action}',
                resource_type='secret',
                resource_id=secret_name,
                result='success' if success else 'failure',
                metadata={
                    'secret_name': secret_name,
                    'action': action,
                    'error': error,
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
        except Exception as e:
            # Don't fail the operation if audit logging fails
            logger.error(f"Failed to audit secret access: {e}")
    
    def _alert_unauthorized_access(self, secret_name: str) -> None:
        """
        Alert administrators on unauthorized secret access attempts.
        
        Requirements: 30.8 - Alert on unauthorized access attempts
        """
        try:
            # Log critical alert
            logger.critical(
                f"SECURITY ALERT: Unauthorized access attempt to secret '{secret_name}'",
                extra={
                    'alert_type': 'unauthorized_secret_access',
                    'secret_name': secret_name,
                    'environment': self.environment,
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            
            # Send alert via configured channels (email, Slack, PagerDuty)
            from infrastructure.alerting_service import AlertingService
            
            alerting = AlertingService()
            alerting.trigger_alert(
                severity='critical',
                title='Unauthorized Secret Access Attempt',
                description=f"Unauthorized access attempt to secret: {secret_name}",
                details={
                    'secret_name': secret_name,
                    'environment': self.environment,
                    'action': 'immediate_investigation_required'
                }
            )
        except Exception as e:
            # Don't fail the operation if alerting fails
            logger.error(f"Failed to send unauthorized access alert: {e}")


# Singleton instance
_secrets_manager = None


def get_secrets_manager() -> SecretsManager:
    """Get or create SecretsManager singleton instance"""
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = SecretsManager()
    return _secrets_manager
