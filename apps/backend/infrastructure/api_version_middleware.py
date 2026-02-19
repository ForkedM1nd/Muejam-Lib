"""
API Version Middleware for Mobile Backend Integration.

This middleware extracts API version information from request paths and adds
version headers to responses. It also implements deprecation warning logic
for old API versions.

Requirements: 1.4
"""

import re
import logging
from typing import Optional
from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class APIVersionMiddleware(MiddlewareMixin):
    """
    Middleware to add API version information and deprecation warnings.
    
    Extracts API version from request path and adds appropriate headers
    to responses. Implements deprecation warning logic for old versions.
    """
    
    # API version configuration
    CURRENT_VERSION = 'v1'
    DEPRECATED_VERSIONS = []  # List of deprecated versions, e.g., ['v0']
    VERSION_PATTERN = re.compile(r'^/v(\d+)/')
    
    # Deprecation configuration
    DEPRECATION_MESSAGES = {
        # Example: 'v0': 'API v0 is deprecated. Please migrate to v1 by 2024-12-31.'
    }
    
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
        Process request and add version headers to response.
        
        Args:
            request: Django request object
            
        Returns:
            Response with version headers added
        """
        # Extract API version from request path
        api_version = self._get_api_version(request)
        
        # Store version in request for use by views
        request.api_version = api_version
        
        # Process request through the rest of the middleware chain
        response = self.get_response(request)
        
        # Add version information to response headers
        if api_version:
            response['X-API-Version'] = api_version
            
            # Add deprecation warning if version is deprecated
            if self._is_deprecated(api_version):
                deprecation_message = self._get_deprecation_message(api_version)
                response['X-API-Deprecation'] = deprecation_message
                response['Warning'] = f'299 - "Deprecated API version: {api_version}"'
                
                # Log deprecation usage for monitoring
                logger.warning(
                    f"Deprecated API version accessed: {api_version} "
                    f"from {request.path} by {self._get_client_identifier(request)}"
                )
        
        return response
    
    def _get_api_version(self, request: HttpRequest) -> Optional[str]:
        """
        Extract API version from request path.
        
        Args:
            request: Django request object
            
        Returns:
            API version string (e.g., 'v1') or None if no version in path
        """
        match = self.VERSION_PATTERN.match(request.path)
        if match:
            version_number = match.group(1)
            return f'v{version_number}'
        return None
    
    def _is_deprecated(self, version: str) -> bool:
        """
        Check if API version is deprecated.
        
        Args:
            version: API version string (e.g., 'v1')
            
        Returns:
            True if version is deprecated, False otherwise
        """
        return version in self.DEPRECATED_VERSIONS
    
    def _get_deprecation_message(self, version: str) -> str:
        """
        Get deprecation message for a specific API version.
        
        Args:
            version: API version string (e.g., 'v1')
            
        Returns:
            Deprecation message string
        """
        return self.DEPRECATION_MESSAGES.get(
            version,
            f'API {version} is deprecated. Please migrate to {self.CURRENT_VERSION}.'
        )
    
    def _get_client_identifier(self, request: HttpRequest) -> str:
        """
        Get client identifier for logging purposes.
        
        Args:
            request: Django request object
            
        Returns:
            Client identifier string (user ID, IP, or 'anonymous')
        """
        # Try to get user ID if authenticated
        if hasattr(request, 'user') and request.user.is_authenticated:
            return f'user:{request.user.id}'
        
        # Fall back to IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        
        return f'ip:{ip}'
