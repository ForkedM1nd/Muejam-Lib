"""
Structured Error Response Utilities for Mobile Backend Integration.

This module provides utilities for creating consistent, structured error responses
with mobile-friendly messages, error codes, retry guidance, and request tracking.

Implements Requirements 15.1, 15.2, 15.3, 15.4 from mobile-backend-integration spec.
"""

import uuid
import logging
from typing import Optional, Dict, Any, List
from enum import Enum
from django.http import JsonResponse
from django.utils.translation import gettext as _
from infrastructure.logging_config import get_logger


# Initialize logger
logger = get_logger(__name__)


class ErrorCode(str, Enum):
    """
    Standard error codes for API responses.
    
    Provides consistent error codes across the API for client handling.
    """
    # Client Errors (4xx)
    INVALID_REQUEST = "INVALID_REQUEST"
    MISSING_FIELD = "MISSING_FIELD"
    INVALID_FIELD_VALUE = "INVALID_FIELD_VALUE"
    TOKEN_MISSING = "TOKEN_MISSING"
    TOKEN_INVALID = "TOKEN_INVALID"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    RESOURCE_FORBIDDEN = "RESOURCE_FORBIDDEN"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    SYNC_CONFLICT = "SYNC_CONFLICT"
    VERSION_CONFLICT = "VERSION_CONFLICT"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    PAYLOAD_TOO_LARGE = "PAYLOAD_TOO_LARGE"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    INVALID_CLIENT_TYPE = "INVALID_CLIENT_TYPE"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    
    # Server Errors (5xx)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    PUSH_SERVICE_ERROR = "PUSH_SERVICE_ERROR"
    STORAGE_SERVICE_ERROR = "STORAGE_SERVICE_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    MAINTENANCE_MODE = "MAINTENANCE_MODE"
    EXTERNAL_SERVICE_TIMEOUT = "EXTERNAL_SERVICE_TIMEOUT"


class ErrorCategory(str, Enum):
    """Error categories for retry guidance."""
    CLIENT_ERROR = "client_error"
    AUTHENTICATION_ERROR = "authentication_error"
    AUTHORIZATION_ERROR = "authorization_error"
    VALIDATION_ERROR = "validation_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    SERVER_ERROR = "server_error"
    NETWORK_ERROR = "network_error"
    SERVICE_ERROR = "service_error"


# Error code to HTTP status code mapping
ERROR_CODE_TO_STATUS = {
    # 400 Bad Request
    ErrorCode.INVALID_REQUEST: 400,
    ErrorCode.MISSING_FIELD: 400,
    
    # 422 Unprocessable Entity
    ErrorCode.INVALID_FIELD_VALUE: 422,
    
    # 401 Unauthorized
    ErrorCode.TOKEN_MISSING: 401,
    ErrorCode.TOKEN_INVALID: 401,
    ErrorCode.TOKEN_EXPIRED: 401,
    
    # 403 Forbidden
    ErrorCode.INSUFFICIENT_PERMISSIONS: 403,
    ErrorCode.RESOURCE_FORBIDDEN: 403,
    
    # 404 Not Found
    ErrorCode.RESOURCE_NOT_FOUND: 404,
    
    # 409 Conflict
    ErrorCode.SYNC_CONFLICT: 409,
    ErrorCode.VERSION_CONFLICT: 409,
    
    # 413 Payload Too Large
    ErrorCode.FILE_TOO_LARGE: 413,
    ErrorCode.PAYLOAD_TOO_LARGE: 413,
    
    # 422 Unprocessable Entity
    ErrorCode.VALIDATION_FAILED: 422,
    ErrorCode.INVALID_CLIENT_TYPE: 422,
    
    # 429 Too Many Requests
    ErrorCode.RATE_LIMIT_EXCEEDED: 429,
    
    # 500 Internal Server Error
    ErrorCode.INTERNAL_ERROR: 500,
    ErrorCode.DATABASE_ERROR: 500,
    
    # 502 Bad Gateway
    ErrorCode.PUSH_SERVICE_ERROR: 502,
    ErrorCode.STORAGE_SERVICE_ERROR: 502,
    
    # 503 Service Unavailable
    ErrorCode.SERVICE_UNAVAILABLE: 503,
    ErrorCode.MAINTENANCE_MODE: 503,
    
    # 504 Gateway Timeout
    ErrorCode.EXTERNAL_SERVICE_TIMEOUT: 504,
}


# Error code to category mapping
ERROR_CODE_TO_CATEGORY = {
    ErrorCode.INVALID_REQUEST: ErrorCategory.CLIENT_ERROR,
    ErrorCode.MISSING_FIELD: ErrorCategory.VALIDATION_ERROR,
    ErrorCode.INVALID_FIELD_VALUE: ErrorCategory.VALIDATION_ERROR,
    ErrorCode.TOKEN_MISSING: ErrorCategory.AUTHENTICATION_ERROR,
    ErrorCode.TOKEN_INVALID: ErrorCategory.AUTHENTICATION_ERROR,
    ErrorCode.TOKEN_EXPIRED: ErrorCategory.AUTHENTICATION_ERROR,
    ErrorCode.INSUFFICIENT_PERMISSIONS: ErrorCategory.AUTHORIZATION_ERROR,
    ErrorCode.RESOURCE_FORBIDDEN: ErrorCategory.AUTHORIZATION_ERROR,
    ErrorCode.RESOURCE_NOT_FOUND: ErrorCategory.CLIENT_ERROR,
    ErrorCode.SYNC_CONFLICT: ErrorCategory.CLIENT_ERROR,
    ErrorCode.VERSION_CONFLICT: ErrorCategory.CLIENT_ERROR,
    ErrorCode.FILE_TOO_LARGE: ErrorCategory.VALIDATION_ERROR,
    ErrorCode.PAYLOAD_TOO_LARGE: ErrorCategory.VALIDATION_ERROR,
    ErrorCode.VALIDATION_FAILED: ErrorCategory.VALIDATION_ERROR,
    ErrorCode.INVALID_CLIENT_TYPE: ErrorCategory.VALIDATION_ERROR,
    ErrorCode.RATE_LIMIT_EXCEEDED: ErrorCategory.RATE_LIMIT_ERROR,
    ErrorCode.INTERNAL_ERROR: ErrorCategory.SERVER_ERROR,
    ErrorCode.DATABASE_ERROR: ErrorCategory.SERVER_ERROR,
    ErrorCode.PUSH_SERVICE_ERROR: ErrorCategory.SERVICE_ERROR,
    ErrorCode.STORAGE_SERVICE_ERROR: ErrorCategory.SERVICE_ERROR,
    ErrorCode.SERVICE_UNAVAILABLE: ErrorCategory.SERVICE_ERROR,
    ErrorCode.MAINTENANCE_MODE: ErrorCategory.SERVICE_ERROR,
    ErrorCode.EXTERNAL_SERVICE_TIMEOUT: ErrorCategory.NETWORK_ERROR,
}


class ErrorResponseBuilder:
    """
    Builder for creating structured error responses.
    
    Provides a fluent interface for constructing error responses with
    all required fields including error codes, messages, retry guidance,
    and request tracking.
    """
    
    def __init__(self, error_code: ErrorCode, user_message: str):
        """
        Initialize error response builder.
        
        Args:
            error_code: Standard error code
            user_message: User-friendly error message
        """
        self.error_code = error_code
        self.user_message = user_message
        self.technical_details = {}
        self.retry_after = None
        self.retry_guidance = None
        self.request_id = None
        self.status_code = ERROR_CODE_TO_STATUS.get(error_code, 500)
    
    def with_technical_details(self, **details) -> 'ErrorResponseBuilder':
        """
        Add technical details for debugging.
        
        Args:
            **details: Technical detail fields
            
        Returns:
            Self for chaining
        """
        self.technical_details.update(details)
        return self
    
    def with_retry_after(self, seconds: int) -> 'ErrorResponseBuilder':
        """
        Add retry-after guidance.
        
        Args:
            seconds: Seconds to wait before retry
            
        Returns:
            Self for chaining
        """
        self.retry_after = seconds
        return self
    
    def with_retry_guidance(self, guidance: str) -> 'ErrorResponseBuilder':
        """
        Add retry guidance message.
        
        Args:
            guidance: Retry guidance text
            
        Returns:
            Self for chaining
        """
        self.retry_guidance = guidance
        return self
    
    def with_request_id(self, request_id: str) -> 'ErrorResponseBuilder':
        """
        Add request ID for tracking.
        
        Args:
            request_id: Request identifier
            
        Returns:
            Self for chaining
        """
        self.request_id = request_id
        return self
    
    def with_status_code(self, status_code: int) -> 'ErrorResponseBuilder':
        """
        Override default status code.
        
        Args:
            status_code: HTTP status code
            
        Returns:
            Self for chaining
        """
        self.status_code = status_code
        return self
    
    def build(self) -> Dict[str, Any]:
        """
        Build error response dictionary.
        
        Returns:
            Structured error response dictionary
        """
        error_response = {
            "error": {
                "code": self.error_code.value,
                "message": self.user_message,
            }
        }
        
        # Add technical details if present
        if self.technical_details:
            error_response["error"]["details"] = self.technical_details
        
        # Add retry guidance if present
        if self.retry_after is not None:
            error_response["error"]["retry_after"] = self.retry_after
        
        if self.retry_guidance:
            error_response["error"]["retry_guidance"] = self.retry_guidance
        
        # Add request ID for tracking
        if self.request_id:
            error_response["error"]["request_id"] = self.request_id
        
        return error_response
    
    def build_response(self) -> JsonResponse:
        """
        Build Django JsonResponse with error data.
        
        Returns:
            JsonResponse with error data and appropriate status code
        """
        response_data = self.build()
        response = JsonResponse(response_data, status=self.status_code)
        
        # Add Retry-After header if specified
        if self.retry_after is not None:
            response['Retry-After'] = str(self.retry_after)
        
        # Add request ID header if specified
        if self.request_id:
            response['X-Request-ID'] = self.request_id
        
        return response


def create_error_response(
    error_code: ErrorCode,
    user_message: str,
    request=None,
    technical_details: Optional[Dict[str, Any]] = None,
    retry_after: Optional[int] = None,
    retry_guidance: Optional[str] = None,
) -> JsonResponse:
    """
    Create a structured error response.
    
    This is a convenience function for creating error responses with
    all standard fields populated.
    
    Args:
        error_code: Standard error code
        user_message: User-friendly error message
        request: Django request object (for request ID extraction)
        technical_details: Optional technical details for debugging
        retry_after: Optional retry delay in seconds
        retry_guidance: Optional retry guidance message
        
    Returns:
        JsonResponse with structured error data
    """
    # Extract request ID from request if available
    request_id = None
    if request and hasattr(request, 'request_id'):
        request_id = request.request_id
    else:
        request_id = str(uuid.uuid4())
    
    # Build error response
    builder = ErrorResponseBuilder(error_code, user_message)
    builder.with_request_id(request_id)
    
    if technical_details:
        builder.with_technical_details(**technical_details)
    
    if retry_after is not None:
        builder.with_retry_after(retry_after)
    
    if retry_guidance:
        builder.with_retry_guidance(retry_guidance)
    
    # Log error with context
    _log_error_response(
        error_code=error_code,
        user_message=user_message,
        request=request,
        request_id=request_id,
        technical_details=technical_details,
    )
    
    return builder.build_response()


def _log_error_response(
    error_code: ErrorCode,
    user_message: str,
    request,
    request_id: str,
    technical_details: Optional[Dict[str, Any]] = None,
):
    """
    Log error response with detailed context.
    
    Implements Requirement 15.4: Log detailed error context for debugging.
    
    Args:
        error_code: Error code
        user_message: User-friendly message
        request: Django request object
        request_id: Request ID
        technical_details: Technical details
    """
    # Determine log level based on error category
    category = ERROR_CODE_TO_CATEGORY.get(error_code, ErrorCategory.SERVER_ERROR)
    status_code = ERROR_CODE_TO_STATUS.get(error_code, 500)
    
    # Build log context
    log_context = {
        'error_code': error_code.value,
        'error_category': category.value,
        'status_code': status_code,
        'request_id': request_id,
        'user_message': user_message,
    }
    
    # Add request context if available
    if request:
        log_context.update({
            'method': request.method,
            'path': request.path,
            'client_type': getattr(request, 'client_type', 'unknown'),
            'user_id': getattr(request.user, 'id', None) if hasattr(request, 'user') else None,
            'ip_address': _get_client_ip(request),
        })
    
    # Add technical details
    if technical_details:
        log_context['technical_details'] = technical_details
    
    # Determine if this is a test request
    is_test_request = _is_test_request(request)
    if is_test_request:
        log_context['test_request'] = True
    
    # Log at appropriate level
    if status_code >= 500:
        logger.error(f"Server error: {error_code.value}", **log_context)
    elif status_code == 429:
        logger.warning(f"Rate limit exceeded: {error_code.value}", **log_context)
    else:
        logger.warning(f"Client error: {error_code.value}", **log_context)


def _get_client_ip(request) -> Optional[str]:
    """
    Extract client IP address from request.
    
    Args:
        request: Django request object
        
    Returns:
        Client IP address or None
    """
    if not request:
        return None
    
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def _is_test_request(request) -> bool:
    """
    Check if request is a test request.
    
    Implements Requirement 18.5: Separate test request logs from production.
    
    Args:
        request: Django request object
        
    Returns:
        True if test request, False otherwise
    """
    if not request:
        return False
    
    # Check for test mode header
    test_mode = request.META.get('HTTP_X_TEST_MODE', '').lower()
    if test_mode in ('true', '1', 'yes'):
        return True
    
    # Check for test mode attribute (set by middleware)
    if hasattr(request, 'test_mode') and request.test_mode:
        return True
    
    return False


# Export public API
__all__ = [
    'ErrorCode',
    'ErrorCategory',
    'ErrorResponseBuilder',
    'create_error_response',
    'ERROR_CODE_TO_STATUS',
    'ERROR_CODE_TO_CATEGORY',
]



# Import error messages for convenience
from infrastructure.error_messages import ErrorMessages, RetryGuidance, TechnicalDetails


def create_mobile_error_response(
    error_code: ErrorCode,
    request=None,
    custom_message: Optional[str] = None,
    technical_details: Optional[Dict[str, Any]] = None,
) -> JsonResponse:
    """
    Create a mobile-friendly error response with automatic retry guidance.
    
    This convenience function automatically adds user-friendly messages
    and retry guidance based on the error code.
    
    Args:
        error_code: Standard error code
        request: Django request object (for request ID extraction)
        custom_message: Optional custom user message (overrides default)
        technical_details: Optional technical details for debugging
        
    Returns:
        JsonResponse with mobile-friendly error data
    """
    # Get user-friendly message
    user_message = custom_message or ErrorMessages.get_message(error_code)
    
    # Get retry guidance
    retry_guidance = RetryGuidance.get_guidance(error_code)
    retry_delay = RetryGuidance.get_retry_delay(error_code)
    
    # Create error response
    return create_error_response(
        error_code=error_code,
        user_message=user_message,
        request=request,
        technical_details=technical_details,
        retry_after=retry_delay,
        retry_guidance=retry_guidance,
    )


def create_validation_error_response(
    field_name: str,
    reason: str,
    request=None,
) -> JsonResponse:
    """
    Create a validation error response for a specific field.
    
    Args:
        field_name: Name of the invalid field
        reason: Reason the field is invalid
        request: Django request object
        
    Returns:
        JsonResponse with validation error
    """
    technical_details = TechnicalDetails.for_invalid_field(field_name, reason)
    return create_mobile_error_response(
        error_code=ErrorCode.INVALID_FIELD_VALUE,
        request=request,
        technical_details=technical_details,
    )


def create_missing_field_error_response(
    field_name: str,
    request=None,
) -> JsonResponse:
    """
    Create a missing field error response.
    
    Args:
        field_name: Name of the missing field
        request: Django request object
        
    Returns:
        JsonResponse with missing field error
    """
    technical_details = TechnicalDetails.for_missing_field(field_name)
    return create_mobile_error_response(
        error_code=ErrorCode.MISSING_FIELD,
        request=request,
        technical_details=technical_details,
    )


def create_file_too_large_error_response(
    file_size: int,
    max_size: int,
    request=None,
) -> JsonResponse:
    """
    Create a file too large error response.
    
    Args:
        file_size: Actual file size in bytes
        max_size: Maximum allowed size in bytes
        request: Django request object
        
    Returns:
        JsonResponse with file size error
    """
    technical_details = TechnicalDetails.for_file_too_large(file_size, max_size)
    return create_mobile_error_response(
        error_code=ErrorCode.FILE_TOO_LARGE,
        request=request,
        technical_details=technical_details,
    )


def create_rate_limit_error_response(
    limit: int,
    window: str,
    reset_time: Optional[str] = None,
    request=None,
) -> JsonResponse:
    """
    Create a rate limit error response.
    
    Args:
        limit: Rate limit threshold
        window: Time window (e.g., "per minute")
        reset_time: When rate limit resets (ISO format)
        request: Django request object
        
    Returns:
        JsonResponse with rate limit error
    """
    technical_details = TechnicalDetails.for_rate_limit(limit, window, reset_time)
    return create_mobile_error_response(
        error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
        request=request,
        technical_details=technical_details,
    )


def create_sync_conflict_error_response(
    client_version: str,
    server_version: str,
    conflicting_fields: List[str],
    request=None,
) -> JsonResponse:
    """
    Create a sync conflict error response.
    
    Args:
        client_version: Client's version/timestamp
        server_version: Server's version/timestamp
        conflicting_fields: List of conflicting field names
        request: Django request object
        
    Returns:
        JsonResponse with sync conflict error
    """
    technical_details = TechnicalDetails.for_sync_conflict(
        client_version, server_version, conflicting_fields
    )
    return create_mobile_error_response(
        error_code=ErrorCode.SYNC_CONFLICT,
        request=request,
        technical_details=technical_details,
    )


def create_external_service_error_response(
    service_name: str,
    error_message: str,
    error_code: ErrorCode = ErrorCode.INTERNAL_ERROR,
    status_code: Optional[int] = None,
    request=None,
) -> JsonResponse:
    """
    Create an external service error response.
    
    Args:
        service_name: Name of external service
        error_message: Error message from service
        error_code: Specific error code (defaults to INTERNAL_ERROR)
        status_code: HTTP status code from service
        request: Django request object
        
    Returns:
        JsonResponse with external service error
    """
    technical_details = TechnicalDetails.for_external_service_error(
        service_name, error_message, status_code
    )
    return create_mobile_error_response(
        error_code=error_code,
        request=request,
        technical_details=technical_details,
    )


# Update exports
__all__.extend([
    'create_mobile_error_response',
    'create_validation_error_response',
    'create_missing_field_error_response',
    'create_file_too_large_error_response',
    'create_rate_limit_error_response',
    'create_sync_conflict_error_response',
    'create_external_service_error_response',
])
