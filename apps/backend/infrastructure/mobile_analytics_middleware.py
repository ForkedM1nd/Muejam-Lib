"""
Mobile Analytics Middleware for Mobile Backend Integration

This middleware tracks API response times per client type for mobile analytics.

Requirements: 14.2
"""

import time
import logging
from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin
from apps.analytics.mobile_analytics_service import get_mobile_analytics_service

logger = logging.getLogger(__name__)


class MobileAnalyticsMiddleware(MiddlewareMixin):
    """
    Middleware to track API response times per client type.
    
    Tracks response times for web, mobile-ios, and mobile-android clients
    separately for analytics purposes.
    
    Requirements: 14.2
    """
    
    def __init__(self, get_response):
        """
        Initialize middleware with next handler.
        
        Args:
            get_response: Next middleware or view in the chain
        """
        self.get_response = get_response
        self.analytics_service = get_mobile_analytics_service()
        super().__init__(get_response)
    
    def process_request(self, request: HttpRequest):
        """
        Record request start time.
        
        Args:
            request: Django request object
        """
        request._mobile_analytics_start_time = time.time()
        return None
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """
        Track API response time per client type.
        
        Args:
            request: Django request object
            response: Django response object
            
        Returns:
            Response object
        """
        # Calculate response time
        if hasattr(request, '_mobile_analytics_start_time'):
            response_time_ms = (time.time() - request._mobile_analytics_start_time) * 1000
            
            # Get client type (set by ClientTypeMiddleware)
            client_type = getattr(request, 'client_type', 'web')
            
            # Track the response time
            self.analytics_service.track_api_response_time(
                client_type=client_type,
                response_time_ms=response_time_ms,
                endpoint=request.path,
                method=request.method,
                status_code=response.status_code
            )
        
        return response
    
    def process_exception(self, request: HttpRequest, exception: Exception):
        """
        Track response time even when exceptions occur.
        
        Args:
            request: Django request object
            exception: Exception that occurred
        """
        # Calculate response time
        if hasattr(request, '_mobile_analytics_start_time'):
            response_time_ms = (time.time() - request._mobile_analytics_start_time) * 1000
            
            # Get client type
            client_type = getattr(request, 'client_type', 'web')
            
            # Track as error (500 status)
            self.analytics_service.track_api_response_time(
                client_type=client_type,
                response_time_ms=response_time_ms,
                endpoint=request.path,
                method=request.method,
                status_code=500
            )
        
        return None
