"""
Unit tests for ErrorFormatter.

Tests verify that all error types are formatted correctly according to the design document.
"""
import pytest
from apps.users.password_reset.error_formatter import ErrorFormatter


class TestErrorFormatter:
    """Test suite for ErrorFormatter."""
    
    def test_format_validation_error_basic(self):
        """Test basic validation error formatting."""
        result = ErrorFormatter.format_validation_error("Invalid input")
        
        assert result['success'] is False
        assert result['error']['code'] == 'VALIDATION_ERROR'
        assert result['error']['message'] == "Invalid input"
        assert 'details' not in result['error']
    
    def test_format_validation_error_with_details(self):
        """Test validation error formatting with details."""
        details = ["Email is required", "Password is too short"]
        result = ErrorFormatter.format_validation_error("Invalid input", details=details)
        
        assert result['success'] is False
        assert result['error']['code'] == 'VALIDATION_ERROR'
        assert result['error']['message'] == "Invalid input"
        assert result['error']['details'] == details
    
    def test_format_rate_limit_error_user(self):
        """Test rate limit error formatting for user limit."""
        result = ErrorFormatter.format_rate_limit_error(
            "Too many requests",
            retry_after=3600,
            limit_type='user'
        )
        
        assert result['success'] is False
        assert result['error']['code'] == 'RATE_LIMIT_EXCEEDED'
        assert result['error']['message'] == "Too many requests"
        assert result['error']['retry_after'] == 3600
        assert result['error']['limit_type'] == 'user'
    
    def test_format_rate_limit_error_ip(self):
        """Test rate limit error formatting for IP limit."""
        result = ErrorFormatter.format_rate_limit_error(
            "Too many requests from this IP",
            retry_after=1800,
            limit_type='ip'
        )
        
        assert result['success'] is False
        assert result['error']['code'] == 'RATE_LIMIT_EXCEEDED'
        assert result['error']['message'] == "Too many requests from this IP"
        assert result['error']['retry_after'] == 1800
        assert result['error']['limit_type'] == 'ip'
    
    def test_format_token_error_not_found(self):
        """Test token error formatting for token not found."""
        result = ErrorFormatter.format_token_error('token_not_found')
        
        assert result['success'] is False
        assert result['error']['code'] == 'INVALID_TOKEN'
        assert 'Invalid or expired reset token' in result['error']['message']
    
    def test_format_token_error_expired(self):
        """Test token error formatting for expired token."""
        result = ErrorFormatter.format_token_error('token_expired')
        
        assert result['success'] is False
        assert result['error']['code'] == 'INVALID_TOKEN'
        assert 'expired' in result['error']['message'].lower()
    
    def test_format_token_error_used(self):
        """Test token error formatting for used token."""
        result = ErrorFormatter.format_token_error('token_used')
        
        assert result['success'] is False
        assert result['error']['code'] == 'INVALID_TOKEN'
        assert 'already been used' in result['error']['message']
    
    def test_format_token_error_invalidated(self):
        """Test token error formatting for invalidated token."""
        result = ErrorFormatter.format_token_error('token_invalidated')
        
        assert result['success'] is False
        assert result['error']['code'] == 'INVALID_TOKEN'
        assert 'no longer valid' in result['error']['message']
    
    def test_format_token_error_unknown_reason(self):
        """Test token error formatting for unknown reason."""
        result = ErrorFormatter.format_token_error('unknown_reason')
        
        assert result['success'] is False
        assert result['error']['code'] == 'INVALID_TOKEN'
        assert 'Invalid reset token' in result['error']['message']
    
    def test_format_password_error(self):
        """Test password validation error formatting."""
        errors = [
            "Password must be at least 8 characters",
            "Password must contain at least one uppercase letter"
        ]
        result = ErrorFormatter.format_password_error(errors)
        
        assert result['success'] is False
        assert result['error']['code'] == 'PASSWORD_VALIDATION_ERROR'
        assert 'security requirements' in result['error']['message']
        assert result['error']['details'] == errors
    
    def test_format_internal_error_default(self):
        """Test internal error formatting with default message."""
        result = ErrorFormatter.format_internal_error()
        
        assert result['success'] is False
        assert result['error']['code'] == 'INTERNAL_ERROR'
        assert 'unexpected error' in result['error']['message'].lower()
    
    def test_format_internal_error_custom(self):
        """Test internal error formatting with custom message."""
        custom_message = "Database connection failed"
        result = ErrorFormatter.format_internal_error(custom_message)
        
        assert result['success'] is False
        assert result['error']['code'] == 'INTERNAL_ERROR'
        assert result['error']['message'] == custom_message
    
    def test_format_email_error(self):
        """Test email error formatting."""
        result = ErrorFormatter.format_email_error()
        
        assert result['success'] is False
        assert result['error']['code'] == 'EMAIL_ERROR'
        assert 'Failed to send email' in result['error']['message']
    
    def test_format_not_found_error_default(self):
        """Test not found error formatting with default resource."""
        result = ErrorFormatter.format_not_found_error()
        
        assert result['success'] is False
        assert result['error']['code'] == 'NOT_FOUND'
        assert result['error']['message'] == 'Resource not found'
    
    def test_format_not_found_error_custom(self):
        """Test not found error formatting with custom resource."""
        result = ErrorFormatter.format_not_found_error('User')
        
        assert result['success'] is False
        assert result['error']['code'] == 'NOT_FOUND'
        assert result['error']['message'] == 'User not found'
    
    def test_error_response_structure(self):
        """Test that all error responses follow the consistent structure."""
        # Test various error types to ensure they all have the required structure
        errors = [
            ErrorFormatter.format_validation_error("test"),
            ErrorFormatter.format_rate_limit_error("test", 60),
            ErrorFormatter.format_token_error("token_expired"),
            ErrorFormatter.format_password_error(["test"]),
            ErrorFormatter.format_internal_error(),
            ErrorFormatter.format_email_error(),
            ErrorFormatter.format_not_found_error(),
        ]
        
        for error in errors:
            # All errors must have success=False
            assert error['success'] is False
            
            # All errors must have an 'error' key
            assert 'error' in error
            
            # All errors must have code and message
            assert 'code' in error['error']
            assert 'message' in error['error']
            
            # Code must be a string
            assert isinstance(error['error']['code'], str)
            
            # Message must be a string
            assert isinstance(error['error']['message'], str)
