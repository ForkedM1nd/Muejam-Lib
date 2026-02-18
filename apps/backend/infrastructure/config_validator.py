"""
Environment Configuration Validator

This module validates required environment variables on application startup.
Implements Requirements 30.9, 30.10, 30.11 from the production readiness spec.

Features:
- Validates required environment variables are present
- Fails startup with clear error messages if variables are missing
- Documents all required variables with descriptions
"""

import logging
import os
import sys
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ConfigValidationError(Exception):
    """Raised when configuration validation fails"""
    pass


class ConfigValidator:
    """
    Validates environment configuration on application startup.
    
    Requirements:
    - 30.9: Validate required environment variables on startup
    - 30.10: Fail with clear error if variables missing
    - 30.11: Document all required variables
    """
    
    # Required environment variables with descriptions and example values
    REQUIRED_VARIABLES = {
        # Core Django Settings
        'SECRET_KEY': {
            'description': 'Django secret key for cryptographic signing',
            'example': 'django-insecure-your-secret-key-here',
            'required_in': ['production', 'staging'],
            'sensitive': True
        },
        'DEBUG': {
            'description': 'Django debug mode (True/False)',
            'example': 'False',
            'required_in': ['production', 'staging', 'development'],
            'sensitive': False
        },
        'ALLOWED_HOSTS': {
            'description': 'Comma-separated list of allowed hosts',
            'example': 'api.muejam.com,localhost',
            'required_in': ['production', 'staging'],
            'sensitive': False
        },
        
        # Database Configuration
        'DATABASE_URL': {
            'description': 'PostgreSQL database connection URL',
            'example': 'postgresql://user:password@host:5432/dbname',
            'required_in': ['production', 'staging', 'development'],
            'sensitive': True
        },
        
        # Authentication
        'CLERK_SECRET_KEY': {
            'description': 'Clerk authentication secret key',
            'example': 'sk_test_xxxxxxxxxxxxx',
            'required_in': ['production', 'staging', 'development'],
            'sensitive': True
        },
        'CLERK_PUBLISHABLE_KEY': {
            'description': 'Clerk authentication publishable key',
            'example': 'pk_test_xxxxxxxxxxxxx',
            'required_in': ['production', 'staging', 'development'],
            'sensitive': False
        },
        
        # Cache/Redis
        'VALKEY_URL': {
            'description': 'Redis/Valkey connection URL',
            'example': 'redis://localhost:6379/0',
            'required_in': ['production', 'staging', 'development'],
            'sensitive': True
        },
        
        # AWS Services
        'AWS_ACCESS_KEY_ID': {
            'description': 'AWS access key ID for S3 and other services',
            'example': 'AKIAIOSFODNN7EXAMPLE',
            'required_in': ['production', 'staging'],
            'sensitive': True
        },
        'AWS_SECRET_ACCESS_KEY': {
            'description': 'AWS secret access key',
            'example': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
            'required_in': ['production', 'staging'],
            'sensitive': True
        },
        'AWS_REGION': {
            'description': 'AWS region for services',
            'example': 'us-east-1',
            'required_in': ['production', 'staging'],
            'sensitive': False
        },
        'AWS_S3_BUCKET': {
            'description': 'S3 bucket name for file storage',
            'example': 'muejam-media-prod',
            'required_in': ['production', 'staging'],
            'sensitive': False
        },
        
        # Email Service
        'RESEND_API_KEY': {
            'description': 'Resend email service API key',
            'example': 're_xxxxxxxxxxxxx',
            'required_in': ['production', 'staging'],
            'sensitive': True
        },
        
        # Error Tracking
        'SENTRY_DSN': {
            'description': 'Sentry error tracking DSN',
            'example': 'https://xxxxx@sentry.io/xxxxx',
            'required_in': ['production', 'staging'],
            'sensitive': True
        },
        
        # Environment Identification
        'ENVIRONMENT': {
            'description': 'Environment name (production/staging/development)',
            'example': 'production',
            'required_in': ['production', 'staging'],
            'sensitive': False
        },
        
        # Frontend URL
        'FRONTEND_URL': {
            'description': 'Frontend application URL',
            'example': 'https://muejam.com',
            'required_in': ['production', 'staging'],
            'sensitive': False
        },
        
        # CORS Configuration
        'CORS_ALLOWED_ORIGINS': {
            'description': 'Comma-separated list of allowed CORS origins',
            'example': 'https://muejam.com,https://www.muejam.com',
            'required_in': ['production', 'staging'],
            'sensitive': False
        },
        'CSRF_TRUSTED_ORIGINS': {
            'description': 'Comma-separated list of trusted CSRF origins',
            'example': 'https://muejam.com,https://www.muejam.com',
            'required_in': ['production', 'staging'],
            'sensitive': False
        },
    }
    
    # Optional but recommended variables
    RECOMMENDED_VARIABLES = {
        'CELERY_BROKER_URL': {
            'description': 'Celery message broker URL',
            'example': 'redis://localhost:6379/0',
            'sensitive': True
        },
        'CELERY_RESULT_BACKEND': {
            'description': 'Celery result backend URL',
            'example': 'redis://localhost:6379/0',
            'sensitive': True
        },
        'GOOGLE_SAFE_BROWSING_API_KEY': {
            'description': 'Google Safe Browsing API key for URL validation',
            'example': 'AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX',
            'sensitive': True
        },
        'RECAPTCHA_SECRET_KEY': {
            'description': 'Google reCAPTCHA v3 secret key',
            'example': '6LeXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX',
            'sensitive': True
        },
        'NEW_RELIC_LICENSE_KEY': {
            'description': 'New Relic APM license key',
            'example': 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
            'sensitive': True
        },
        'DATADOG_API_KEY': {
            'description': 'DataDog APM API key',
            'example': 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
            'sensitive': True
        },
    }
    
    def __init__(self, environment: Optional[str] = None):
        """
        Initialize configuration validator.
        
        Args:
            environment: Environment name (production/staging/development)
                        If None, reads from ENVIRONMENT env var
        """
        self.environment = environment or os.getenv('ENVIRONMENT', 'development')
    
    def validate(self, fail_on_error: bool = True) -> Tuple[bool, List[str]]:
        """
        Validate all required environment variables are present.
        
        Args:
            fail_on_error: If True, raises exception on validation failure
        
        Returns:
            Tuple of (is_valid, list of error messages)
        
        Raises:
            ConfigValidationError: If validation fails and fail_on_error is True
        
        Requirements:
        - 30.9: Validate required environment variables on startup
        - 30.10: Fail with clear error if variables missing
        """
        errors = []
        warnings = []
        
        # Validate required variables
        for var_name, var_info in self.REQUIRED_VARIABLES.items():
            if self.environment in var_info['required_in']:
                value = os.getenv(var_name)
                
                if not value:
                    errors.append(
                        f"Missing required environment variable: {var_name}\n"
                        f"  Description: {var_info['description']}\n"
                        f"  Example: {var_info['example']}\n"
                        f"  Required in: {', '.join(var_info['required_in'])}"
                    )
                elif value == var_info['example']:
                    warnings.append(
                        f"Environment variable '{var_name}' is using example value. "
                        f"Please set a proper value."
                    )
        
        # Check recommended variables
        for var_name, var_info in self.RECOMMENDED_VARIABLES.items():
            value = os.getenv(var_name)
            if not value:
                warnings.append(
                    f"Recommended environment variable not set: {var_name}\n"
                    f"  Description: {var_info['description']}\n"
                    f"  Example: {var_info['example']}"
                )
        
        # Log warnings
        for warning in warnings:
            logger.warning(warning)
        
        # Handle errors
        if errors:
            error_message = self._format_error_message(errors)
            
            if fail_on_error:
                logger.critical(error_message)
                raise ConfigValidationError(error_message)
            else:
                logger.error(error_message)
                return False, errors
        
        logger.info(f"Configuration validation passed for environment: {self.environment}")
        return True, []
    
    def _format_error_message(self, errors: List[str]) -> str:
        """
        Format validation errors into a clear, actionable message.
        
        Requirements: 30.10 - Clear error message when variables missing
        """
        message = [
            "\n" + "=" * 80,
            "CONFIGURATION VALIDATION FAILED",
            "=" * 80,
            f"\nEnvironment: {self.environment}",
            f"\nThe following required environment variables are missing or invalid:\n",
        ]
        
        for i, error in enumerate(errors, 1):
            message.append(f"\n{i}. {error}\n")
        
        message.extend([
            "\n" + "-" * 80,
            "\nTo fix this issue:",
            "1. Create or update your .env file with the required variables",
            "2. Ensure all sensitive values are stored in AWS Secrets Manager",
            "3. Verify environment-specific configuration is correct",
            "\nFor production deployments:",
            "- Use AWS Secrets Manager for sensitive configuration",
            "- Never commit secrets to version control",
            "- Ensure different credentials for each environment",
            "\n" + "=" * 80 + "\n"
        ])
        
        return "\n".join(message)
    
    def get_documentation(self) -> str:
        """
        Generate documentation for all required environment variables.
        
        Requirements: 30.11 - Document all required variables
        """
        doc = [
            "=" * 80,
            "ENVIRONMENT VARIABLES DOCUMENTATION",
            "=" * 80,
            "\nThis document lists all environment variables used by the application.",
            "\n## REQUIRED VARIABLES\n"
        ]
        
        for var_name, var_info in sorted(self.REQUIRED_VARIABLES.items()):
            doc.append(f"\n### {var_name}")
            doc.append(f"Description: {var_info['description']}")
            doc.append(f"Example: {var_info['example']}")
            doc.append(f"Required in: {', '.join(var_info['required_in'])}")
            doc.append(f"Sensitive: {'Yes' if var_info['sensitive'] else 'No'}")
            doc.append("")
        
        doc.append("\n## RECOMMENDED VARIABLES\n")
        
        for var_name, var_info in sorted(self.RECOMMENDED_VARIABLES.items()):
            doc.append(f"\n### {var_name}")
            doc.append(f"Description: {var_info['description']}")
            doc.append(f"Example: {var_info['example']}")
            doc.append(f"Sensitive: {'Yes' if var_info['sensitive'] else 'No'}")
            doc.append("")
        
        doc.append("=" * 80)
        
        return "\n".join(doc)
    
    def export_documentation(self, output_path: str = 'docs/ENVIRONMENT_VARIABLES.md') -> None:
        """
        Export environment variables documentation to a file.
        
        Args:
            output_path: Path to output file
        """
        import os
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Write documentation
        with open(output_path, 'w') as f:
            f.write(self.get_documentation())
        
        logger.info(f"Environment variables documentation exported to: {output_path}")


def validate_config_on_startup():
    """
    Validate configuration on application startup.
    
    This function should be called early in the application startup process.
    It will fail with a clear error message if required variables are missing.
    
    Requirements:
    - 30.9: Validate required environment variables on startup
    - 30.10: Fail with clear error if variables missing
    """
    validator = ConfigValidator()
    validator.validate(fail_on_error=True)
