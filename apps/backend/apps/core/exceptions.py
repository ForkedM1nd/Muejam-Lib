"""Custom exception handlers and exception classes."""
from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException, ValidationError
from rest_framework import status


class RateLimitExceeded(APIException):
    """Exception raised when rate limit is exceeded."""
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = 'Rate limit exceeded. Please try again later.'
    default_code = 'rate_limit_exceeded'


class InvalidCursor(APIException):
    """Exception raised when pagination cursor is invalid."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Invalid pagination cursor.'
    default_code = 'invalid_cursor'


class ContentDeleted(APIException):
    """Exception raised when accessing soft-deleted content."""
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Content has been deleted.'
    default_code = 'content_deleted'


class UserBlocked(APIException):
    """Exception raised when accessing blocked user's content."""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'You have blocked this user.'
    default_code = 'user_blocked'


class DuplicateResource(APIException):
    """Exception raised when attempting to create duplicate resource."""
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'Resource already exists.'
    default_code = 'duplicate_resource'


class InvalidOffset(APIException):
    """Exception raised when highlight offsets are invalid."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Invalid offset values.'
    default_code = 'invalid_offset'


class AuthenticationRequired(APIException):
    """Exception raised when authentication is required but not provided."""
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = 'Authentication credentials were not provided.'
    default_code = 'authentication_required'


class InvalidToken(APIException):
    """Exception raised when authentication token is invalid."""
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = 'Invalid or expired authentication token.'
    default_code = 'invalid_token'


class InsufficientPermissions(APIException):
    """Exception raised when user lacks required permissions."""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'You do not have permission to perform this action.'
    default_code = 'insufficient_permissions'


class CaptchaValidationError(APIException):
    """Exception raised when reCAPTCHA validation fails."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'CAPTCHA validation failed. Please try again.'
    default_code = 'captcha_validation_failed'


def custom_exception_handler(exc, context):
    """
    Custom exception handler for consistent error responses.
    
    Maps Django/DRF exceptions to appropriate HTTP status codes and returns
    error responses in the format:
    {
        "error": {
            "code": "ERROR_CODE",
            "message": "Human-readable error message",
            "details": {...}
        }
    }
    
    Requirements:
        - 17.2: Return JSON with error code, message, and details
        - 17.3: Map Django/DRF exceptions to appropriate HTTP status codes
    """
    # Call DRF's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Get error code from exception or use generic code
        error_code = getattr(exc, 'default_code', 'error')
        
        # Map common Django/DRF exceptions to appropriate codes
        from rest_framework.exceptions import (
            ValidationError, AuthenticationFailed, NotAuthenticated,
            PermissionDenied, NotFound, MethodNotAllowed, NotAcceptable,
            UnsupportedMediaType, Throttled, ParseError
        )
        from django.core.exceptions import ObjectDoesNotExist, PermissionDenied as DjangoPermissionDenied
        
        # Map exception types to error codes
        if isinstance(exc, ValidationError):
            error_code = 'validation_error'
        elif isinstance(exc, (NotAuthenticated, AuthenticationFailed)):
            error_code = 'authentication_failed'
        elif isinstance(exc, (PermissionDenied, DjangoPermissionDenied)):
            error_code = 'permission_denied'
        elif isinstance(exc, (NotFound, ObjectDoesNotExist)):
            error_code = 'not_found'
        elif isinstance(exc, MethodNotAllowed):
            error_code = 'method_not_allowed'
        elif isinstance(exc, Throttled):
            error_code = 'rate_limit_exceeded'
        elif isinstance(exc, ParseError):
            error_code = 'parse_error'
        elif isinstance(exc, (NotAcceptable, UnsupportedMediaType)):
            error_code = 'invalid_media_type'
        
        # Extract error message and details
        if hasattr(exc, 'detail'):
            if isinstance(exc.detail, dict):
                # For dict details, extract message if present
                message = exc.detail.get('message', exc.detail.get('detail', str(exc)))
                details = {k: v for k, v in exc.detail.items() if k not in ['message', 'detail']}
            elif isinstance(exc.detail, list):
                # For list details (validation errors), use first item as message
                message = 'Validation failed'
                details = {'errors': exc.detail}
            else:
                # For string details
                message = str(exc.detail)
                details = {}
        else:
            message = str(exc)
            details = {}
        
        # Build consistent error response
        response.data = {
            'error': {
                'code': error_code.upper() if isinstance(error_code, str) else str(error_code).upper(),
                'message': message,
                'details': details if details else {}
            }
        }
    
    return response



def validate_serializer(serializer, raise_exception=True):
    """
    Validate a serializer and optionally raise ValidationError.
    
    This helper ensures consistent validation error handling across all views.
    When raise_exception=True, validation errors will be caught by the custom
    exception handler and formatted consistently.
    
    Args:
        serializer: DRF serializer instance
        raise_exception: If True, raises ValidationError on validation failure
        
    Returns:
        True if valid, False otherwise (when raise_exception=False)
        
    Raises:
        ValidationError: When validation fails and raise_exception=True
        
    Requirements:
        - 17.5: Add DRF serializer validation for all endpoints
        - 17.6: Return HTTP 400 with detailed validation errors
    """
    return serializer.is_valid(raise_exception=raise_exception)
