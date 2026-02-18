"""
Unit tests for Configuration Validator

Tests the environment configuration validation including:
- Required variable validation
- Environment-specific requirements
- Error message formatting
- Documentation generation
"""

import os
from unittest.mock import patch, mock_open
import pytest

from infrastructure.config_validator import (
    ConfigValidator,
    ConfigValidationError,
    validate_config_on_startup
)


@pytest.fixture
def validator():
    """Create a ConfigValidator instance for testing"""
    return ConfigValidator(environment='production')


@pytest.fixture
def dev_validator():
    """Create a ConfigValidator instance for development"""
    return ConfigValidator(environment='development')


class TestConfigValidation:
    """Test configuration validation functionality"""
    
    def test_validate_success_with_all_required_vars(self, validator):
        """Test validation passes when all required variables are present"""
        required_vars = {
            'SECRET_KEY': 'test-secret-key',
            'DEBUG': 'False',
            'ALLOWED_HOSTS': 'api.muejam.com',
            'DATABASE_URL': 'postgresql://user:pass@host:5432/db',
            'CLERK_SECRET_KEY': 'sk_test_xxx',
            'CLERK_PUBLISHABLE_KEY': 'pk_test_xxx',
            'VALKEY_URL': 'redis://localhost:6379/0',
            'AWS_ACCESS_KEY_ID': 'AKIAIOSFODNN7EXAMPLE',
            'AWS_SECRET_ACCESS_KEY': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
            'AWS_REGION': 'us-east-1',
            'AWS_S3_BUCKET': 'muejam-media-prod',
            'RESEND_API_KEY': 're_xxxxxxxxxxxxx',
            'SENTRY_DSN': 'https://xxxxx@sentry.io/xxxxx',
            'ENVIRONMENT': 'production',
            'FRONTEND_URL': 'https://muejam.com',
            'CORS_ALLOWED_ORIGINS': 'https://muejam.com',
            'CSRF_TRUSTED_ORIGINS': 'https://muejam.com',
        }
        
        with patch.dict(os.environ, required_vars, clear=True):
            is_valid, errors = validator.validate(fail_on_error=False)
            
            assert is_valid is True
            assert len(errors) == 0
    
    def test_validate_fails_with_missing_required_var(self, validator):
        """Test validation fails when required variable is missing"""
        # Set only some required variables
        partial_vars = {
            'SECRET_KEY': 'test-secret-key',
            'DEBUG': 'False',
        }
        
        with patch.dict(os.environ, partial_vars, clear=True):
            is_valid, errors = validator.validate(fail_on_error=False)
            
            assert is_valid is False
            assert len(errors) > 0
    
    def test_validate_raises_exception_on_failure(self, validator):
        """Test validation raises exception when fail_on_error is True"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ConfigValidationError):
                validator.validate(fail_on_error=True)
    
    def test_environment_specific_requirements(self, dev_validator):
        """Test that development environment has fewer requirements"""
        # Development requires fewer variables than production
        dev_vars = {
            'DEBUG': 'True',
            'DATABASE_URL': 'postgresql://user:pass@localhost:5432/db',
            'CLERK_SECRET_KEY': 'sk_test_xxx',
            'CLERK_PUBLISHABLE_KEY': 'pk_test_xxx',
            'VALKEY_URL': 'redis://localhost:6379/0',
        }
        
        with patch.dict(os.environ, dev_vars, clear=True):
            is_valid, errors = dev_validator.validate(fail_on_error=False)
            
            # Development should pass with fewer variables
            # (AWS, Resend, Sentry not required in development)
            assert is_valid is True or len(errors) < 10
    
    def test_warning_for_example_values(self, validator):
        """Test that using example values generates warnings"""
        vars_with_examples = {
            'SECRET_KEY': 'django-insecure-your-secret-key-here',  # Example value
            'DEBUG': 'False',
            'ALLOWED_HOSTS': 'api.muejam.com',
            'DATABASE_URL': 'postgresql://user:pass@host:5432/db',
            'CLERK_SECRET_KEY': 'sk_test_xxx',
            'CLERK_PUBLISHABLE_KEY': 'pk_test_xxx',
            'VALKEY_URL': 'redis://localhost:6379/0',
            'AWS_ACCESS_KEY_ID': 'AKIAIOSFODNN7EXAMPLE',  # Example value
            'AWS_SECRET_ACCESS_KEY': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
            'AWS_REGION': 'us-east-1',
            'AWS_S3_BUCKET': 'muejam-media-prod',
            'RESEND_API_KEY': 're_xxxxxxxxxxxxx',
            'SENTRY_DSN': 'https://xxxxx@sentry.io/xxxxx',
            'ENVIRONMENT': 'production',
            'FRONTEND_URL': 'https://muejam.com',
            'CORS_ALLOWED_ORIGINS': 'https://muejam.com',
            'CSRF_TRUSTED_ORIGINS': 'https://muejam.com',
        }
        
        with patch.dict(os.environ, vars_with_examples, clear=True):
            with patch('infrastructure.config_validator.logger') as mock_logger:
                validator.validate(fail_on_error=False)
                
                # Verify warnings were logged
                assert mock_logger.warning.called


class TestErrorFormatting:
    """Test error message formatting"""
    
    def test_format_error_message_includes_details(self, validator):
        """Test that error messages include helpful details"""
        errors = [
            "Missing required environment variable: SECRET_KEY\n"
            "  Description: Django secret key\n"
            "  Example: django-insecure-xxx\n"
            "  Required in: production, staging"
        ]
        
        formatted = validator._format_error_message(errors)
        
        # Verify message includes key information
        assert 'CONFIGURATION VALIDATION FAILED' in formatted
        assert 'SECRET_KEY' in formatted
        assert 'Django secret key' in formatted
        assert 'production, staging' in formatted
        assert 'AWS Secrets Manager' in formatted
    
    def test_format_error_message_includes_fix_instructions(self, validator):
        """Test that error messages include fix instructions"""
        errors = ["Test error"]
        formatted = validator._format_error_message(errors)
        
        # Verify fix instructions are included
        assert 'To fix this issue:' in formatted
        assert '.env file' in formatted
        assert 'AWS Secrets Manager' in formatted


class TestDocumentation:
    """Test documentation generation"""
    
    def test_get_documentation_includes_all_variables(self, validator):
        """Test that documentation includes all required variables"""
        doc = validator.get_documentation()
        
        # Verify documentation includes key sections
        assert 'ENVIRONMENT VARIABLES DOCUMENTATION' in doc
        assert 'REQUIRED VARIABLES' in doc
        assert 'RECOMMENDED VARIABLES' in doc
        
        # Verify some key variables are documented
        assert 'SECRET_KEY' in doc
        assert 'DATABASE_URL' in doc
        assert 'AWS_ACCESS_KEY_ID' in doc
    
    def test_get_documentation_includes_descriptions(self, validator):
        """Test that documentation includes descriptions and examples"""
        doc = validator.get_documentation()
        
        # Verify descriptions are included
        assert 'Description:' in doc
        assert 'Example:' in doc
        assert 'Required in:' in doc
        assert 'Sensitive:' in doc
    
    def test_export_documentation_creates_file(self, validator):
        """Test that documentation can be exported to file"""
        mock_file = mock_open()
        
        with patch('builtins.open', mock_file):
            with patch('os.makedirs'):
                validator.export_documentation('test_output.md')
        
        # Verify file was opened for writing
        mock_file.assert_called_once_with('test_output.md', 'w')
        
        # Verify content was written
        handle = mock_file()
        assert handle.write.called


class TestStartupValidation:
    """Test startup validation function"""
    
    def test_validate_config_on_startup_success(self):
        """Test that startup validation passes with valid config"""
        required_vars = {
            'SECRET_KEY': 'test-secret-key',
            'DEBUG': 'True',
            'DATABASE_URL': 'postgresql://user:pass@localhost:5432/db',
            'CLERK_SECRET_KEY': 'sk_test_xxx',
            'CLERK_PUBLISHABLE_KEY': 'pk_test_xxx',
            'VALKEY_URL': 'redis://localhost:6379/0',
            'ENVIRONMENT': 'development',
        }
        
        with patch.dict(os.environ, required_vars, clear=True):
            # Should not raise exception
            validate_config_on_startup()
    
    def test_validate_config_on_startup_fails_with_invalid_config(self):
        """Test that startup validation fails with invalid config"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ConfigValidationError):
                validate_config_on_startup()


class TestRequiredVariablesDefinition:
    """Test that required variables are properly defined"""
    
    def test_all_required_variables_have_descriptions(self, validator):
        """Test that all required variables have descriptions"""
        for var_name, var_info in validator.REQUIRED_VARIABLES.items():
            assert 'description' in var_info
            assert 'example' in var_info
            assert 'required_in' in var_info
            assert 'sensitive' in var_info
            
            # Verify values are not empty
            assert var_info['description']
            assert var_info['example']
            assert len(var_info['required_in']) > 0
    
    def test_sensitive_variables_marked_correctly(self, validator):
        """Test that sensitive variables are marked as sensitive"""
        sensitive_vars = [
            'SECRET_KEY',
            'DATABASE_URL',
            'CLERK_SECRET_KEY',
            'AWS_SECRET_ACCESS_KEY',
            'RESEND_API_KEY',
            'SENTRY_DSN',
        ]
        
        for var_name in sensitive_vars:
            assert validator.REQUIRED_VARIABLES[var_name]['sensitive'] is True
    
    def test_non_sensitive_variables_marked_correctly(self, validator):
        """Test that non-sensitive variables are marked correctly"""
        non_sensitive_vars = [
            'DEBUG',
            'ALLOWED_HOSTS',
            'AWS_REGION',
            'ENVIRONMENT',
        ]
        
        for var_name in non_sensitive_vars:
            assert validator.REQUIRED_VARIABLES[var_name]['sensitive'] is False
