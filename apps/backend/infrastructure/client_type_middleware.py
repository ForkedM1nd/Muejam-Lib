"""
Client Type Middleware for Mobile Backend Integration.

This middleware detects and validates client type from request headers,
making it available throughout the request lifecycle. It extracts the
X-Client-Type header, validates it against allowed types, and sets
request.client_type for use by views and other middleware.

Requirements: 2.1, 2.2, 2.3, 2.5
"""

import logging
from typing import Optional
from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class ClientTypeMiddleware(MiddlewareMixin):
    """
    Middleware to detect and validate client type from request headers.
    
    Extracts X-Client-Type header and validates against allowed types.
    Sets request.client_type for use by views and other middleware.
    Logs client type for analytics purposes.
    """
    
    # Allowed client types
    ALLOWED_CLIENT_TYPES = ['web', 'mobile-ios', 'mobile-android']
    DEFAULT_CLIENT_TYPE = 'web'
    
    def __init__(self, get_response):
        """
        Initialize middleware with next handler.
        
        Args:
            get_response: Next middleware or view in the chain
        """
        self.get_response = get_response
        super().__init__(get_response)
    
    def __call__(self, request: HttpRequest) -> HttpResponse:
        """
        Process request and set client type.
        
        Args:
            request: Django request object
            
        Returns:
            Response from next middleware/view
        """
        # Extract and validate client type from request headers
        client_type = self._extract_client_type(request)
        
        # Set client_type attribute on request for use by views and middleware
        request.client_type = client_type
        
        # Log client type for analytics
        logger.info(
            f"Request from client type: {client_type}",
            extra={
                'client_type': client_type,
                'path': request.path,
                'method': request.method,
                'user_agent': request.META.get('HTTP_USER_AGENT', 'unknown'),
                'is_mobile': self._is_mobile_client(client_type)
            }
        )
        
        # Continue to next middleware/view
        response = self.get_response(request)
        
        return response
    
    def _extract_client_type(self, request: HttpRequest) -> str:
        """
        Extract and validate client type from request headers.
        
        Reads the X-Client-Type header, validates it against allowed types,
        and returns the validated client type or default if missing/invalid.
        
        Args:
            request: Django request object
            
        Returns:
            Validated client type string
        """
        # Get X-Client-Type header (case-insensitive)
        client_type = request.META.get('HTTP_X_CLIENT_TYPE', '').strip().lower()
        
        # If header is missing or empty, use default
        if not client_type:
            return self.DEFAULT_CLIENT_TYPE
        
        # Validate against allowed types
        if client_type in self.ALLOWED_CLIENT_TYPES:
            return client_type
        
        # Invalid client type - log warning and use default
        logger.warning(
            f"Invalid client type received: {client_type}",
            extra={
                'invalid_client_type': client_type,
                'path': request.path,
                'method': request.method,
                'allowed_types': self.ALLOWED_CLIENT_TYPES
            }
        )
        
        return self.DEFAULT_CLIENT_TYPE
    
    def _is_mobile_client(self, client_type: str) -> bool:
        """
        Check if client type is mobile.
        
        Args:
            client_type: Client type string
            
        Returns:
            True if client type is mobile (iOS or Android), False otherwise
        """
        return client_type.startswith('mobile-')
