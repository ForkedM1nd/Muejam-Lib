"""
Logging Middleware

This middleware automatically logs all API requests with structured logging.
Implements Requirement 15.3: Log all API requests.
"""

import time
import uuid
from django.utils.deprecation import MiddlewareMixin
from infrastructure.logging_config import get_logger, log_api_request


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log all API requests with structured logging.
    
    Implements Requirement 15.3: Log all API requests with method, path,
    status code, response time, and user agent.
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.logger = get_logger(__name__)
    
    def process_request(self, request):
        """
        Process incoming request.
        
        Adds request ID and start time to request object.
        """
        # Generate unique request ID
        request.request_id = str(uuid.uuid4())
        
        # Record request start time
        request.start_time = time.time()
        
        # Detect test mode (Requirement 18.5)
        test_mode_header = request.headers.get('X-Test-Mode', '').lower()
        request.is_test_mode = test_mode_header in ['true', '1', 'yes']
        
        # Set request context in logger
        context = {
            'request_id': request.request_id,
            'ip_address': self.get_client_ip(request),
        }
        
        # Add test mode flag to logging context (Requirement 18.5)
        if request.is_test_mode:
            context['test_mode'] = True
        
        self.logger.set_context(**context)
        
        # Add user ID if authenticated
        if hasattr(request, 'user') and request.user and hasattr(request.user, 'id'):
            self.logger.set_context(user_id=str(request.user.id))
        
        return None
    
    def process_response(self, request, response):
        """
        Process outgoing response.
        
        Logs the API request with all relevant details.
        """
        # Calculate response time
        if hasattr(request, 'start_time'):
            response_time_ms = (time.time() - request.start_time) * 1000
        else:
            response_time_ms = 0
        
        # Get user ID if authenticated
        user_id = None
        if hasattr(request, 'user') and request.user and hasattr(request.user, 'id'):
            user_id = str(request.user.id)
        
        # Check if this is a test mode request (Requirement 18.5)
        is_test_mode = getattr(request, 'is_test_mode', False)
        
        # Log the request with test mode flag
        log_api_request(
            logger=self.logger,
            method=request.method,
            path=request.path,
            status_code=response.status_code,
            response_time_ms=response_time_ms,
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            user_id=user_id,
            test_mode=is_test_mode
        )
        
        # Add request ID to response headers
        if hasattr(request, 'request_id'):
            response['X-Request-ID'] = request.request_id
        
        # Clear logger context
        self.logger.clear_context()
        
        return response
    
    @staticmethod
    def get_client_ip(request):
        """
        Get client IP address from request.
        
        Args:
            request: Django request object
            
        Returns:
            Client IP address
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


# Export public API
__all__ = ['RequestLoggingMiddleware']
