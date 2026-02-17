"""
Error response formatter for password reset feature.

Provides consistent error response formatting across all password reset endpoints.
"""
from typing import Optional, List, Dict, Any
from .types import ErrorResponse


class ErrorFormatter:
    """
    Formats errors into consistent ErrorResponse format.
    
    Requirements:
        - 3.2: Consistent error response format with retry-after for rate limiting
    """
    
    @staticmethod
    def format_validation_error(message: str, details: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Format a validation error response.
        
        Args:
            message: User-friendly error message
            details: Optional list of detailed error messages
            
        Returns:
            Formatted error response dictionary
        """
        error_dict = {
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': message,
            }
        }
        
        if details:
            error_dict['error']['details'] = details
        
        return error_dict
    
    @staticmethod
    def format_rate_limit_error(
        message: str,
        retry_after: int,
        limit_type: str = 'user'
    ) -> Dict[str, Any]:
        """
        Format a rate limit error response.
        
        Args:
            message: User-friendly error message
            retry_after: Seconds until retry is allowed
            limit_type: Type of rate limit ('user' or 'ip')
            
        Returns:
            Formatted error response dictionary
            
        Requirements:
            - 3.2: Include retry-after for rate limiting
        """
        return {
            'success': False,
            'error': {
                'code': 'RATE_LIMIT_EXCEEDED',
                'message': message,
                'retry_after': retry_after,
                'limit_type': limit_type
            }
        }
    
    @staticmethod
    def format_token_error(reason: str) -> Dict[str, Any]:
        """
        Format a token validation error response.
        
        Args:
            reason: Reason for token invalidity
            
        Returns:
            Formatted error response dictionary
        """
        # Map internal reasons to user-friendly messages
        message_map = {
            'token_not_found': 'Invalid or expired reset token. Please request a new password reset.',
            'token_expired': 'This reset link has expired. Please request a new password reset.',
            'token_used': 'This reset link has already been used. Please request a new password reset.',
            'token_invalidated': 'This reset link is no longer valid. Please request a new password reset.',
        }
        
        message = message_map.get(reason, 'Invalid reset token. Please request a new password reset.')
        
        return {
            'success': False,
            'error': {
                'code': 'INVALID_TOKEN',
                'message': message,
            }
        }
    
    @staticmethod
    def format_password_error(errors: List[str]) -> Dict[str, Any]:
        """
        Format a password validation error response.
        
        Args:
            errors: List of password validation errors
            
        Returns:
            Formatted error response dictionary
        """
        return {
            'success': False,
            'error': {
                'code': 'PASSWORD_VALIDATION_ERROR',
                'message': 'Password does not meet security requirements',
                'details': errors
            }
        }
    
    @staticmethod
    def format_internal_error(message: Optional[str] = None) -> Dict[str, Any]:
        """
        Format an internal server error response.
        
        Args:
            message: Optional custom error message
            
        Returns:
            Formatted error response dictionary
        """
        return {
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': message or 'An unexpected error occurred. Please try again later.',
            }
        }
    
    @staticmethod
    def format_email_error() -> Dict[str, Any]:
        """
        Format an email sending error response.
        
        Returns:
            Formatted error response dictionary
        """
        return {
            'success': False,
            'error': {
                'code': 'EMAIL_ERROR',
                'message': 'Failed to send email. Please try again later.',
            }
        }
    
    @staticmethod
    def format_not_found_error(resource: str = 'Resource') -> Dict[str, Any]:
        """
        Format a not found error response.
        
        Args:
            resource: Name of the resource that was not found
            
        Returns:
            Formatted error response dictionary
        """
        return {
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': f'{resource} not found',
            }
        }
