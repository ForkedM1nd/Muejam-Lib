"""
Mobile-Friendly Error Message Templates.

This module provides user-friendly error messages with retry guidance
for mobile clients. Messages are designed to be clear, actionable, and
appropriate for display to end users.

Implements Requirements 15.2, 15.3 from mobile-backend-integration spec.
"""

from typing import Dict, Optional
from infrastructure.error_responses import ErrorCode


class ErrorMessages:
    """
    User-friendly error message templates for mobile clients.
    
    Provides clear, actionable messages that can be displayed to users,
    along with retry guidance for recoverable errors.
    """
    
    # Client Error Messages (4xx)
    INVALID_REQUEST = "We couldn't process your request. Please check your input and try again."
    MISSING_FIELD = "Some required information is missing. Please fill in all required fields."
    INVALID_FIELD_VALUE = "Some information you provided is invalid. Please check and try again."
    
    # Authentication Error Messages (401)
    TOKEN_MISSING = "You need to sign in to access this content."
    TOKEN_INVALID = "Your session is invalid. Please sign in again."
    TOKEN_EXPIRED = "Your session has expired. Please sign in again to continue."
    
    # Authorization Error Messages (403)
    INSUFFICIENT_PERMISSIONS = "You don't have permission to perform this action."
    RESOURCE_FORBIDDEN = "You don't have access to this content."
    
    # Not Found Error Messages (404)
    RESOURCE_NOT_FOUND = "We couldn't find what you're looking for. It may have been removed or doesn't exist."
    
    # Conflict Error Messages (409)
    SYNC_CONFLICT = "Your changes conflict with recent updates. Please refresh and try again."
    VERSION_CONFLICT = "This content has been updated by someone else. Please refresh to see the latest version."
    
    # Payload Error Messages (413)
    FILE_TOO_LARGE = "The file you're trying to upload is too large. Please choose a smaller file."
    PAYLOAD_TOO_LARGE = "The data you're sending is too large. Please try sending less data at once."
    
    # Validation Error Messages (422)
    VALIDATION_FAILED = "Some information you provided is invalid. Please check and try again."
    INVALID_CLIENT_TYPE = "Your app version may be outdated. Please update to the latest version."
    
    # Rate Limit Error Messages (429)
    RATE_LIMIT_EXCEEDED = "You're making requests too quickly. Please wait a moment and try again."
    
    # Server Error Messages (5xx)
    INTERNAL_ERROR = "Something went wrong on our end. Please try again in a moment."
    DATABASE_ERROR = "We're having trouble accessing your data. Please try again in a moment."
    
    # External Service Error Messages (502)
    PUSH_SERVICE_ERROR = "We're having trouble sending notifications right now. We'll keep trying."
    STORAGE_SERVICE_ERROR = "We're having trouble saving your files right now. Please try again in a moment."
    
    # Service Unavailable Messages (503)
    SERVICE_UNAVAILABLE = "Our service is temporarily unavailable. Please try again in a few minutes."
    MAINTENANCE_MODE = "We're performing maintenance. Please check back soon."
    
    # Timeout Error Messages (504)
    EXTERNAL_SERVICE_TIMEOUT = "The request took too long to complete. Please try again."
    
    @classmethod
    def get_message(cls, error_code: ErrorCode) -> str:
        """
        Get user-friendly message for error code.
        
        Args:
            error_code: Error code
            
        Returns:
            User-friendly error message
        """
        message_map = {
            ErrorCode.INVALID_REQUEST: cls.INVALID_REQUEST,
            ErrorCode.MISSING_FIELD: cls.MISSING_FIELD,
            ErrorCode.INVALID_FIELD_VALUE: cls.INVALID_FIELD_VALUE,
            ErrorCode.TOKEN_MISSING: cls.TOKEN_MISSING,
            ErrorCode.TOKEN_INVALID: cls.TOKEN_INVALID,
            ErrorCode.TOKEN_EXPIRED: cls.TOKEN_EXPIRED,
            ErrorCode.INSUFFICIENT_PERMISSIONS: cls.INSUFFICIENT_PERMISSIONS,
            ErrorCode.RESOURCE_FORBIDDEN: cls.RESOURCE_FORBIDDEN,
            ErrorCode.RESOURCE_NOT_FOUND: cls.RESOURCE_NOT_FOUND,
            ErrorCode.SYNC_CONFLICT: cls.SYNC_CONFLICT,
            ErrorCode.VERSION_CONFLICT: cls.VERSION_CONFLICT,
            ErrorCode.FILE_TOO_LARGE: cls.FILE_TOO_LARGE,
            ErrorCode.PAYLOAD_TOO_LARGE: cls.PAYLOAD_TOO_LARGE,
            ErrorCode.VALIDATION_FAILED: cls.VALIDATION_FAILED,
            ErrorCode.INVALID_CLIENT_TYPE: cls.INVALID_CLIENT_TYPE,
            ErrorCode.RATE_LIMIT_EXCEEDED: cls.RATE_LIMIT_EXCEEDED,
            ErrorCode.INTERNAL_ERROR: cls.INTERNAL_ERROR,
            ErrorCode.DATABASE_ERROR: cls.DATABASE_ERROR,
            ErrorCode.PUSH_SERVICE_ERROR: cls.PUSH_SERVICE_ERROR,
            ErrorCode.STORAGE_SERVICE_ERROR: cls.STORAGE_SERVICE_ERROR,
            ErrorCode.SERVICE_UNAVAILABLE: cls.SERVICE_UNAVAILABLE,
            ErrorCode.MAINTENANCE_MODE: cls.MAINTENANCE_MODE,
            ErrorCode.EXTERNAL_SERVICE_TIMEOUT: cls.EXTERNAL_SERVICE_TIMEOUT,
        }
        
        return message_map.get(error_code, cls.INTERNAL_ERROR)


class RetryGuidance:
    """
    Retry guidance for recoverable errors.
    
    Provides specific guidance on when and how to retry failed requests,
    particularly for network and service errors.
    """
    
    # Retry guidance templates
    IMMEDIATE_RETRY = "Please try again immediately."
    SHORT_DELAY_RETRY = "Please wait a few seconds and try again."
    MEDIUM_DELAY_RETRY = "Please wait a minute and try again."
    LONG_DELAY_RETRY = "Please wait a few minutes and try again."
    REFRESH_AND_RETRY = "Please refresh the page and try again."
    SIGN_IN_AND_RETRY = "Please sign in again and try your request."
    UPDATE_APP_AND_RETRY = "Please update your app to the latest version and try again."
    CHECK_CONNECTION_AND_RETRY = "Please check your internet connection and try again."
    REDUCE_SIZE_AND_RETRY = "Please reduce the file size and try again."
    NO_RETRY = "This action cannot be retried. Please contact support if the problem persists."
    
    @classmethod
    def get_guidance(cls, error_code: ErrorCode) -> Optional[str]:
        """
        Get retry guidance for error code.
        
        Args:
            error_code: Error code
            
        Returns:
            Retry guidance message or None if not retryable
        """
        guidance_map = {
            # Client errors - generally not retryable without changes
            ErrorCode.INVALID_REQUEST: None,
            ErrorCode.MISSING_FIELD: None,
            ErrorCode.INVALID_FIELD_VALUE: None,
            
            # Authentication errors - need re-authentication
            ErrorCode.TOKEN_MISSING: cls.SIGN_IN_AND_RETRY,
            ErrorCode.TOKEN_INVALID: cls.SIGN_IN_AND_RETRY,
            ErrorCode.TOKEN_EXPIRED: cls.SIGN_IN_AND_RETRY,
            
            # Authorization errors - not retryable
            ErrorCode.INSUFFICIENT_PERMISSIONS: None,
            ErrorCode.RESOURCE_FORBIDDEN: None,
            
            # Not found - not retryable
            ErrorCode.RESOURCE_NOT_FOUND: None,
            
            # Conflicts - need refresh
            ErrorCode.SYNC_CONFLICT: cls.REFRESH_AND_RETRY,
            ErrorCode.VERSION_CONFLICT: cls.REFRESH_AND_RETRY,
            
            # Payload errors - need size reduction
            ErrorCode.FILE_TOO_LARGE: cls.REDUCE_SIZE_AND_RETRY,
            ErrorCode.PAYLOAD_TOO_LARGE: cls.REDUCE_SIZE_AND_RETRY,
            
            # Validation errors - not retryable without changes
            ErrorCode.VALIDATION_FAILED: None,
            ErrorCode.INVALID_CLIENT_TYPE: cls.UPDATE_APP_AND_RETRY,
            
            # Rate limit - retry after delay
            ErrorCode.RATE_LIMIT_EXCEEDED: cls.SHORT_DELAY_RETRY,
            
            # Server errors - retry with delay
            ErrorCode.INTERNAL_ERROR: cls.SHORT_DELAY_RETRY,
            ErrorCode.DATABASE_ERROR: cls.SHORT_DELAY_RETRY,
            
            # External service errors - retry with delay
            ErrorCode.PUSH_SERVICE_ERROR: cls.MEDIUM_DELAY_RETRY,
            ErrorCode.STORAGE_SERVICE_ERROR: cls.SHORT_DELAY_RETRY,
            
            # Service unavailable - retry with longer delay
            ErrorCode.SERVICE_UNAVAILABLE: cls.LONG_DELAY_RETRY,
            ErrorCode.MAINTENANCE_MODE: cls.LONG_DELAY_RETRY,
            
            # Timeout errors - check connection and retry
            ErrorCode.EXTERNAL_SERVICE_TIMEOUT: cls.CHECK_CONNECTION_AND_RETRY,
        }
        
        return guidance_map.get(error_code)
    
    @classmethod
    def get_retry_delay(cls, error_code: ErrorCode) -> Optional[int]:
        """
        Get recommended retry delay in seconds.
        
        Args:
            error_code: Error code
            
        Returns:
            Retry delay in seconds or None if not retryable
        """
        delay_map = {
            # Rate limit - wait before retry
            ErrorCode.RATE_LIMIT_EXCEEDED: 30,
            
            # Server errors - short delay
            ErrorCode.INTERNAL_ERROR: 5,
            ErrorCode.DATABASE_ERROR: 5,
            
            # External service errors - medium delay
            ErrorCode.PUSH_SERVICE_ERROR: 60,
            ErrorCode.STORAGE_SERVICE_ERROR: 10,
            
            # Service unavailable - longer delay
            ErrorCode.SERVICE_UNAVAILABLE: 300,  # 5 minutes
            ErrorCode.MAINTENANCE_MODE: 600,  # 10 minutes
            
            # Timeout errors - short delay
            ErrorCode.EXTERNAL_SERVICE_TIMEOUT: 10,
        }
        
        return delay_map.get(error_code)


class TechnicalDetails:
    """
    Technical details for debugging.
    
    Provides additional technical information that can help developers
    debug issues while keeping user-facing messages simple.
    """
    
    @staticmethod
    def for_missing_field(field_name: str) -> Dict[str, str]:
        """
        Technical details for missing field error.
        
        Args:
            field_name: Name of missing field
            
        Returns:
            Technical details dictionary
        """
        return {
            "field": field_name,
            "technical_message": f"Required field '{field_name}' is missing from request"
        }
    
    @staticmethod
    def for_invalid_field(field_name: str, reason: str) -> Dict[str, str]:
        """
        Technical details for invalid field error.
        
        Args:
            field_name: Name of invalid field
            reason: Reason field is invalid
            
        Returns:
            Technical details dictionary
        """
        return {
            "field": field_name,
            "technical_message": f"Field '{field_name}' is invalid: {reason}"
        }
    
    @staticmethod
    def for_file_too_large(file_size: int, max_size: int) -> Dict[str, any]:
        """
        Technical details for file too large error.
        
        Args:
            file_size: Actual file size in bytes
            max_size: Maximum allowed size in bytes
            
        Returns:
            Technical details dictionary
        """
        return {
            "file_size_bytes": file_size,
            "max_size_bytes": max_size,
            "file_size_mb": round(file_size / (1024 * 1024), 2),
            "max_size_mb": round(max_size / (1024 * 1024), 2),
            "technical_message": f"File size {file_size} bytes exceeds maximum {max_size} bytes"
        }
    
    @staticmethod
    def for_rate_limit(limit: int, window: str, reset_time: Optional[str] = None) -> Dict[str, any]:
        """
        Technical details for rate limit error.
        
        Args:
            limit: Rate limit threshold
            window: Time window (e.g., "per minute")
            reset_time: When rate limit resets (ISO format)
            
        Returns:
            Technical details dictionary
        """
        details = {
            "rate_limit": limit,
            "window": window,
            "technical_message": f"Rate limit of {limit} requests {window} exceeded"
        }
        
        if reset_time:
            details["reset_time"] = reset_time
        
        return details
    
    @staticmethod
    def for_sync_conflict(
        client_version: str,
        server_version: str,
        conflicting_fields: list
    ) -> Dict[str, any]:
        """
        Technical details for sync conflict error.
        
        Args:
            client_version: Client's version/timestamp
            server_version: Server's version/timestamp
            conflicting_fields: List of conflicting field names
            
        Returns:
            Technical details dictionary
        """
        return {
            "client_version": client_version,
            "server_version": server_version,
            "conflicting_fields": conflicting_fields,
            "technical_message": f"Client version {client_version} conflicts with server version {server_version}"
        }
    
    @staticmethod
    def for_external_service_error(
        service_name: str,
        error_message: str,
        status_code: Optional[int] = None
    ) -> Dict[str, any]:
        """
        Technical details for external service error.
        
        Args:
            service_name: Name of external service
            error_message: Error message from service
            status_code: HTTP status code from service
            
        Returns:
            Technical details dictionary
        """
        details = {
            "service": service_name,
            "service_error": error_message,
            "technical_message": f"External service '{service_name}' error: {error_message}"
        }
        
        if status_code:
            details["service_status_code"] = status_code
        
        return details


# Export public API
__all__ = [
    'ErrorMessages',
    'RetryGuidance',
    'TechnicalDetails',
]
