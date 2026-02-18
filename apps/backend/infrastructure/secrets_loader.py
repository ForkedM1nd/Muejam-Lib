"""
Secrets Loader Utility

This module provides helper functions to load secrets from AWS Secrets Manager
and inject them into the application configuration.

Requirements: 30.2 - Store sensitive configuration in Secrets Manager
"""

import logging
import os
from typing import Any, Dict, Optional

from infrastructure.secrets_manager import get_secrets_manager, SecretsManagerError

logger = logging.getLogger(__name__)


def load_secret_or_env(secret_name: str, env_var: str, 
                       secret_key: Optional[str] = None,
                       default: Any = None,
                       use_cache: bool = True) -> Any:
    """
    Load a value from AWS Secrets Manager or fall back to environment variable.
    
    This function tries to load from Secrets Manager first, then falls back to
    environment variables. This allows for local development without AWS access.
    
    Args:
        secret_name: Name of the secret in Secrets Manager
        env_var: Environment variable name to use as fallback
        secret_key: Key within the secret (if secret is a JSON object)
        default: Default value if neither source is available
        use_cache: Whether to use cached secret value
    
    Returns:
        The secret value, environment variable value, or default
    
    Example:
        # Load database password
        db_password = load_secret_or_env(
            secret_name='database/primary',
            env_var='DATABASE_PASSWORD',
            secret_key='password'
        )
    """
    # Try loading from Secrets Manager first
    if os.getenv('USE_SECRETS_MANAGER', 'False') == 'True':
        try:
            secrets_manager = get_secrets_manager()
            secret_data = secrets_manager.get_secret(secret_name, use_cache=use_cache)
            
            if secret_key:
                value = secret_data.get(secret_key)
            else:
                value = secret_data
            
            if value is not None:
                logger.debug(f"Loaded '{env_var}' from Secrets Manager")
                return value
        
        except SecretsManagerError as e:
            logger.warning(
                f"Failed to load secret '{secret_name}' from Secrets Manager: {e}. "
                f"Falling back to environment variable."
            )
    
    # Fall back to environment variable
    env_value = os.getenv(env_var)
    if env_value is not None:
        logger.debug(f"Loaded '{env_var}' from environment variable")
        return env_value
    
    # Use default if provided
    if default is not None:
        logger.debug(f"Using default value for '{env_var}'")
        return default
    
    # No value found
    logger.warning(f"No value found for '{env_var}' in Secrets Manager or environment")
    return None


def load_database_config(database_name: str = 'primary') -> Dict[str, str]:
    """
    Load database configuration from Secrets Manager.
    
    Args:
        database_name: Name of the database (e.g., 'primary', 'replica')
    
    Returns:
        Dictionary with database configuration
    
    Example:
        db_config = load_database_config('primary')
        # Returns: {
        #     'host': 'db.example.com',
        #     'port': '5432',
        #     'name': 'muejam',
        #     'user': 'muejam_user',
        #     'password': 'secure_password'
        # }
    """
    secret_name = f'database/{database_name}'
    
    return {
        'host': load_secret_or_env(
            secret_name, f'DATABASE_{database_name.upper()}_HOST',
            secret_key='host', default='localhost'
        ),
        'port': load_secret_or_env(
            secret_name, f'DATABASE_{database_name.upper()}_PORT',
            secret_key='port', default='5432'
        ),
        'name': load_secret_or_env(
            secret_name, f'DATABASE_{database_name.upper()}_NAME',
            secret_key='name', default='muejam'
        ),
        'user': load_secret_or_env(
            secret_name, f'DATABASE_{database_name.upper()}_USER',
            secret_key='user', default='muejam_user'
        ),
        'password': load_secret_or_env(
            secret_name, f'DATABASE_{database_name.upper()}_PASSWORD',
            secret_key='password', default='muejam_password'
        ),
    }


def load_api_key(service_name: str) -> Optional[str]:
    """
    Load API key for external service from Secrets Manager.
    
    Args:
        service_name: Name of the service (e.g., 'resend', 'aws', 'clerk')
    
    Returns:
        API key string or None
    
    Example:
        resend_key = load_api_key('resend')
    """
    secret_name = f'api-keys/{service_name}'
    env_var = f'{service_name.upper()}_API_KEY'
    
    return load_secret_or_env(
        secret_name, env_var,
        secret_key='api_key'
    )


def sync_secrets_to_env():
    """
    Sync secrets from AWS Secrets Manager to environment variables.
    
    This is useful for applications that expect configuration in environment
    variables but you want to store secrets in Secrets Manager.
    
    Call this early in application startup before other modules load config.
    """
    if os.getenv('USE_SECRETS_MANAGER', 'False') != 'True':
        logger.info("Secrets Manager not enabled, skipping sync")
        return
    
    logger.info("Syncing secrets from AWS Secrets Manager to environment variables")
    
    # Define secrets to sync
    secrets_to_sync = [
        # Database
        ('database/primary', 'DATABASE_PASSWORD', 'password'),
        
        # API Keys
        ('api-keys/resend', 'RESEND_API_KEY', 'api_key'),
        ('api-keys/clerk', 'CLERK_SECRET_KEY', 'api_key'),
        ('api-keys/aws', 'AWS_SECRET_ACCESS_KEY', 'api_key'),
        
        # Other sensitive config
        ('django/secret-key', 'SECRET_KEY', 'value'),
    ]
    
    synced_count = 0
    
    for secret_name, env_var, secret_key in secrets_to_sync:
        try:
            value = load_secret_or_env(secret_name, env_var, secret_key)
            if value:
                os.environ[env_var] = str(value)
                synced_count += 1
                logger.debug(f"Synced {env_var} from Secrets Manager")
        except Exception as e:
            logger.warning(f"Failed to sync {env_var}: {e}")
    
    logger.info(f"Successfully synced {synced_count} secrets to environment variables")
