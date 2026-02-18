"""
HTTPS Enforcement Middleware and Configuration.

This module provides comprehensive HTTPS enforcement including:
- Automatic HTTP to HTTPS redirection
- HSTS (HTTP Strict Transport Security) headers
- Secure cookie configuration
- SSL/TLS validation

Requirements: 6.4, 6.11, 6.12
"""

import logging
from typing import Callable

from django.conf import settings
from django.http import HttpRequest, HttpResponse, HttpResponsePermanentRedirect
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class HTTPSEnforcementMiddleware(MiddlewareMixin):
    """
    Middleware to enforce HTTPS connections in production.
    
    This middleware:
    - Redirects all HTTP requests to HTTPS (301 Permanent Redirect)
    - Adds HSTS headers to enforce HTTPS for future requests
    - Validates SSL/TLS configuration
    - Logs security events
    
    Requirements: 6.4
    """
    
    def __init__(self, get_response: Callable):
        """Initialize middleware."""
        super().__init__(get_response)
        self.get_response = get_response
    
    def _get_config(self):
        """Get current configuration from settings (allows for test overrides)."""
        return {
            'enforce_https': getattr(settings, 'SECURE_SSL_REDIRECT', False),
            'hsts_seconds': getattr(settings, 'SECURE_HSTS_SECONDS', 31536000),
            'hsts_include_subdomains': getattr(settings, 'SECURE_HSTS_INCLUDE_SUBDOMAINS', True),
            'hsts_preload': getattr(settings, 'SECURE_HSTS_PRELOAD', True),
            'exempt_paths': getattr(settings, 'HTTPS_EXEMPT_PATHS', ['/health'])
        }
    
    def process_request(self, request: HttpRequest) -> HttpResponse:
        """
        Process incoming request and enforce HTTPS.
        
        Args:
            request: Django HTTP request
            
        Returns:
            None to continue processing, or redirect response for HTTP requests
        """
        # Get current configuration (allows for test overrides)
        config = self._get_config()
        
        # Skip enforcement in development or for exempt paths
        if not config['enforce_https'] or request.path in config['exempt_paths']:
            return None
        
        # Check if request is already HTTPS
        if self._is_secure_request(request):
            return None
        
        # Redirect HTTP to HTTPS
        https_url = self._build_https_url(request)
        
        logger.info(
            f"Redirecting HTTP to HTTPS: {request.path}",
            extra={
                'path': request.path,
                'method': request.method,
                'client_ip': self._get_client_ip(request),
                'redirect_url': https_url
            }
        )
        
        return HttpResponsePermanentRedirect(https_url)
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """
        Process outgoing response and add HSTS headers.
        
        Args:
            request: Django HTTP request
            response: Django HTTP response
            
        Returns:
            Modified response with HSTS headers
        """
        # Get current configuration (allows for test overrides)
        config = self._get_config()
        
        # Only add HSTS headers for HTTPS requests
        if self._is_secure_request(request):
            # Build HSTS header value
            hsts_value = f'max-age={config["hsts_seconds"]}'
            
            if config['hsts_include_subdomains']:
                hsts_value += '; includeSubDomains'
            
            if config['hsts_preload']:
                hsts_value += '; preload'
            
            response['Strict-Transport-Security'] = hsts_value
        
        return response
    
    def _is_secure_request(self, request: HttpRequest) -> bool:
        """
        Check if request is using HTTPS.
        
        Handles both direct HTTPS and proxied requests (X-Forwarded-Proto).
        
        Args:
            request: Django HTTP request
            
        Returns:
            True if request is secure, False otherwise
        """
        # Check X-Forwarded-Proto header (for load balancers/proxies)
        forwarded_proto = request.META.get('HTTP_X_FORWARDED_PROTO', '')
        if forwarded_proto.lower() == 'https':
            return True
        
        # Check Django's is_secure() method
        if request.is_secure():
            return True
        
        # Check if running on standard HTTPS port
        if request.META.get('SERVER_PORT') == '443':
            return True
        
        return False
    
    def _build_https_url(self, request: HttpRequest) -> str:
        """
        Build HTTPS URL from HTTP request.
        
        Args:
            request: Django HTTP request
            
        Returns:
            HTTPS URL string
        """
        # Get host from request
        host = request.get_host()
        
        # Remove port if it's the default HTTP port
        if ':80' in host:
            host = host.replace(':80', '')
        
        # Build HTTPS URL
        https_url = f'https://{host}{request.get_full_path()}'
        
        return https_url
    
    @staticmethod
    def _get_client_ip(request: HttpRequest) -> str:
        """
        Get client IP address from request.
        
        Args:
            request: Django HTTP request
            
        Returns:
            Client IP address
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        return ip


def validate_https_configuration():
    """
    Validate HTTPS configuration on application startup.
    
    Checks that all required HTTPS settings are properly configured
    for production environments.
    
    Raises:
        ImproperlyConfigured: If HTTPS configuration is invalid
    """
    from django.core.exceptions import ImproperlyConfigured
    
    environment = getattr(settings, 'ENVIRONMENT', 'development')
    
    if environment == 'production':
        # Check that HTTPS enforcement is enabled
        if not getattr(settings, 'SECURE_SSL_REDIRECT', False):
            raise ImproperlyConfigured(
                "SECURE_SSL_REDIRECT must be True in production. "
                "Set SECURE_SSL_REDIRECT=True in settings.py"
            )
        
        # Check that HSTS is configured
        hsts_seconds = getattr(settings, 'SECURE_HSTS_SECONDS', 0)
        if hsts_seconds < 31536000:  # 1 year
            logger.warning(
                f"SECURE_HSTS_SECONDS is {hsts_seconds}, "
                f"recommended minimum is 31536000 (1 year)"
            )
        
        # Check that secure cookies are enabled
        if not getattr(settings, 'SESSION_COOKIE_SECURE', False):
            raise ImproperlyConfigured(
                "SESSION_COOKIE_SECURE must be True in production. "
                "Set SESSION_COOKIE_SECURE=True in settings.py"
            )
        
        if not getattr(settings, 'CSRF_COOKIE_SECURE', False):
            raise ImproperlyConfigured(
                "CSRF_COOKIE_SECURE must be True in production. "
                "Set CSRF_COOKIE_SECURE=True in settings.py"
            )
        
        logger.info("HTTPS configuration validated successfully")
    else:
        logger.info(f"Skipping HTTPS validation in {environment} environment")


def get_https_status() -> dict:
    """
    Get current HTTPS configuration status.
    
    Returns:
        Dictionary with HTTPS configuration details
    """
    return {
        'enforce_https': getattr(settings, 'SECURE_SSL_REDIRECT', False),
        'hsts_enabled': getattr(settings, 'SECURE_HSTS_SECONDS', 0) > 0,
        'hsts_seconds': getattr(settings, 'SECURE_HSTS_SECONDS', 0),
        'hsts_include_subdomains': getattr(settings, 'SECURE_HSTS_INCLUDE_SUBDOMAINS', False),
        'hsts_preload': getattr(settings, 'SECURE_HSTS_PRELOAD', False),
        'session_cookie_secure': getattr(settings, 'SESSION_COOKIE_SECURE', False),
        'csrf_cookie_secure': getattr(settings, 'CSRF_COOKIE_SECURE', False),
        'environment': getattr(settings, 'ENVIRONMENT', 'development')
    }
