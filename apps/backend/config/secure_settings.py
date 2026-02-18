"""
Secure Configuration Management

This module enforces secure configuration practices by:
1. Requiring all critical environment variables
2. Validating SECRET_KEY is not a default/example value
3. Enforcing production security requirements
4. Providing clear error messages for misconfiguration

Fixes critical security vulnerability where SECRET_KEY had an insecure default.
"""

import os
import logging
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)


class SecureConfig:
    """
    Secure configuration management with validation.
    
    This class ensures that:
    - Required environment variables are set
    - SECRET_KEY is secure (not a default/example value)
    - Production environments have proper security configuration
    - Clear error messages guide developers to fix issues
    """
    
    @staticmethod
    def get_required(key: str, description: str = "", example: str = "") -> str:
        """
        Get required environment variable or raise error.
        
        Args:
            key: Environment variable name
            description: Human-readable description
            example: Example value (for error message)
            
        Returns:
            Environment variable value
            
        Raises:
            ImproperlyConfigured: If variable is not set
        """
        value = os.getenv(key)
        if not value:
            error_msg = f"Required environment variable '{key}' is not set."
            if description:
                error_msg += f"\nDescription: {description}"
            if example:
                error_msg += f"\nExample: {example}"
            error_msg += f"\nSet it in your environment or .env file."
            
            logger.error(error_msg)
            raise ImproperlyConfigured(error_msg)
        
        return value
    
    @staticmethod
    def get_secret_key() -> str:
        """
        Get Django SECRET_KEY with validation.
        
        This method:
        1. Requires SECRET_KEY to be set (no default)
        2. Validates it's not an example/insecure value
        3. Validates minimum length (50 characters)
        4. Provides clear error messages
        
        Returns:
            Validated SECRET_KEY
            
        Raises:
            ImproperlyConfigured: If SECRET_KEY is missing or insecure
        """
        key = os.getenv('SECRET_KEY')
        
        # Require SECRET_KEY to be set
        if not key:
            raise ImproperlyConfigured(
                "SECRET_KEY environment variable must be set.\n"
                "Generate a secure key with:\n"
                "  python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'\n"
                "Then set it in your .env file or environment:\n"
                "  SECRET_KEY=<generated_key>"
            )
        
        # Validate it's not a default/example value
        insecure_patterns = [
            'django-insecure',
            'change-this',
            'your-secret-key',
            'example',
            'test-key',
            'secret-key-here',
            'replace-me',
            'changeme'
        ]
        
        key_lower = key.lower()
        for pattern in insecure_patterns:
            if pattern in key_lower:
                raise ImproperlyConfigured(
                    f"SECRET_KEY appears to be an example value (contains '{pattern}').\n"
                    f"Generate a secure key with:\n"
                    f"  python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'\n"
                    f"Current value: {key[:20]}..."
                )
        
        # Validate minimum length
        if len(key) < 50:
            raise ImproperlyConfigured(
                f"SECRET_KEY is too short ({len(key)} characters).\n"
                f"It should be at least 50 characters for security.\n"
                f"Generate a secure key with:\n"
                f"  python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'"
            )
        
        logger.info("SECRET_KEY validated successfully")
        return key
    
    @staticmethod
    def validate_production_config():
        """
        Validate all production-required configuration.
        
        This method ensures that production environments have:
        - DEBUG = False
        - HTTPS enforcement enabled
        - Monitoring configured (Sentry)
        - Proper ALLOWED_HOSTS
        - Secure cookie settings
        
        Raises:
            ImproperlyConfigured: If production requirements not met
        """
        logger.info("Validating production configuration")
        
        # Ensure DEBUG is False
        debug = os.getenv('DEBUG', 'False')
        if debug.lower() not in ['false', '0', 'no']:
            raise ImproperlyConfigured(
                "DEBUG must be False in production.\n"
                "Set DEBUG=False in your environment."
            )
        
        # Ensure HTTPS is enforced
        ssl_redirect = os.getenv('SECURE_SSL_REDIRECT', 'True')
        if ssl_redirect.lower() not in ['true', '1', 'yes']:
            raise ImproperlyConfigured(
                "SECURE_SSL_REDIRECT must be True in production.\n"
                "Set SECURE_SSL_REDIRECT=True in your environment."
            )
        
        # Ensure monitoring is configured
        if not os.getenv('SENTRY_DSN'):
            logger.warning(
                "SENTRY_DSN is not set. Error monitoring will not work.\n"
                "Set SENTRY_DSN in your environment for production monitoring."
            )
        
        # Ensure ALLOWED_HOSTS is properly configured
        allowed_hosts = os.getenv('ALLOWED_HOSTS', '')
        if not allowed_hosts or allowed_hosts == 'localhost,127.0.0.1':
            raise ImproperlyConfigured(
                "ALLOWED_HOSTS must be properly configured in production.\n"
                "Set ALLOWED_HOSTS to your production domain(s).\n"
                "Example: ALLOWED_HOSTS=api.example.com,www.example.com"
            )
        
        # Ensure database is configured
        if not os.getenv('DATABASE_URL'):
            raise ImproperlyConfigured(
                "DATABASE_URL must be set in production.\n"
                "Set DATABASE_URL to your production database connection string."
            )
        
        # Ensure Redis is configured
        if not os.getenv('VALKEY_URL') and not os.getenv('REDIS_URL'):
            raise ImproperlyConfigured(
                "VALKEY_URL or REDIS_URL must be set in production.\n"
                "Set VALKEY_URL to your Redis connection string."
            )
        
        logger.info("Production configuration validated successfully")
    
    @staticmethod
    def validate_clerk_config():
        """
        Validate Clerk authentication configuration.
        
        Raises:
            ImproperlyConfigured: If Clerk configuration is missing
        """
        if not os.getenv('CLERK_SECRET_KEY'):
            raise ImproperlyConfigured(
                "CLERK_SECRET_KEY must be set.\n"
                "Get your secret key from: https://dashboard.clerk.com/\n"
                "Set CLERK_SECRET_KEY in your environment."
            )
        
        if not os.getenv('CLERK_PUBLISHABLE_KEY'):
            raise ImproperlyConfigured(
                "CLERK_PUBLISHABLE_KEY must be set.\n"
                "Get your publishable key from: https://dashboard.clerk.com/\n"
                "Set CLERK_PUBLISHABLE_KEY in your environment."
            )
        
        logger.info("Clerk configuration validated successfully")
    
    @staticmethod
    def validate_aws_config():
        """
        Validate AWS configuration.
        
        Raises:
            ImproperlyConfigured: If AWS configuration is missing
        """
        if not os.getenv('AWS_ACCESS_KEY_ID'):
            logger.warning("AWS_ACCESS_KEY_ID not set. AWS services will not work.")
        
        if not os.getenv('AWS_SECRET_ACCESS_KEY'):
            logger.warning("AWS_SECRET_ACCESS_KEY not set. AWS services will not work.")
        
        if not os.getenv('AWS_S3_BUCKET'):
            logger.warning("AWS_S3_BUCKET not set. File uploads will not work.")
    
    @staticmethod
    def validate_all():
        """
        Validate all configuration.
        
        This is the main entry point for configuration validation.
        Call this at application startup to ensure proper configuration.
        """
        logger.info("Starting configuration validation")
        
        # Always validate SECRET_KEY
        SecureConfig.get_secret_key()
        
        # Always validate Clerk config
        SecureConfig.validate_clerk_config()
        
        # Validate production-specific config
        environment = os.getenv('ENVIRONMENT', 'development')
        if environment == 'production':
            SecureConfig.validate_production_config()
        
        # Validate AWS config (warnings only)
        SecureConfig.validate_aws_config()
        
        logger.info("Configuration validation completed successfully")


def validate_config_on_startup():
    """
    Validate configuration on application startup.
    
    This function is called from settings.py to ensure
    proper configuration before the application starts.
    """
    try:
        SecureConfig.validate_all()
    except ImproperlyConfigured as e:
        logger.error(f"Configuration validation failed: {e}")
        raise
