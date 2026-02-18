"""
APM Middleware for Django

This middleware tracks API endpoint performance and integrates with APM providers.
Implements Requirement 14.2: Track API endpoint performance.
"""

import time
from django.utils.deprecation import MiddlewareMixin
from infrastructure.apm_config import PerformanceMonitor, APMConfig


class APMMiddleware(MiddlewareMixin):
    """
    Middleware to track API endpoint performance.
    
    Tracks:
    - Request duration
    - Response status codes
    - Endpoint paths
    - HTTP methods
    """
    
    def process_request(self, request):
        """Record request start time."""
        request._apm_start_time = time.time()
        return None
    
    def process_response(self, request, response):
        """Track API endpoint performance."""
        if not APMConfig.is_enabled():
            return response
        
        # Calculate request duration
        if hasattr(request, '_apm_start_time'):
            duration_ms = (time.time() - request._apm_start_time) * 1000
            
            # Get endpoint information
            endpoint = request.path
            method = request.method
            status_code = response.status_code
            
            # Track performance
            PerformanceMonitor.track_api_endpoint(
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                duration_ms=duration_ms
            )
        
        return response
    
    def process_exception(self, request, exception):
        """Track exceptions in API endpoints."""
        if not APMConfig.is_enabled():
            return None
        
        # Calculate request duration
        if hasattr(request, '_apm_start_time'):
            duration_ms = (time.time() - request._apm_start_time) * 1000
            
            # Track as error
            PerformanceMonitor.track_api_endpoint(
                endpoint=request.path,
                method=request.method,
                status_code=500,
                duration_ms=duration_ms
            )
        
        return None
