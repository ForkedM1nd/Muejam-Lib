"""
Request Timeout Middleware

This middleware enforces request timeouts to prevent long-running requests
from exhausting worker threads and causing resource exhaustion.

Fixes critical reliability issue where requests could run indefinitely.
"""

import signal
import logging
from django.conf import settings
from django.http import JsonResponse

logger = logging.getLogger(__name__)


class TimeoutMiddleware:
    """
    Middleware to enforce request timeouts.
    
    This middleware:
    1. Sets an alarm for the configured timeout
    2. Processes the request
    3. Cancels the alarm if request completes
    4. Returns 504 Gateway Timeout if timeout exceeded
    
    Reliability improvements:
    - Prevents worker thread exhaustion
    - Prevents resource exhaustion attacks
    - Provides clear timeout errors
    - Protects against slow database queries
    """
    
    # Paths to skip timeout (admin interface needs longer timeouts)
    SKIP_PATHS = [
        '/django-admin/',
        '/admin/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.timeout = getattr(settings, 'REQUEST_TIMEOUT', 30)
        logger.info(f"Timeout middleware initialized with {self.timeout}s timeout")
    
    def __call__(self, request):
        # Skip timeout for admin paths
        if self.should_skip_timeout(request):
            return self.get_response(request)
        
        # Set alarm for timeout
        old_handler = signal.signal(signal.SIGALRM, self.timeout_handler)
        signal.alarm(self.timeout)
        
        try:
            response = self.get_response(request)
            return response
            
        except TimeoutError as e:
            # Request exceeded timeout
            return self.handle_timeout(request, e)
            
        finally:
            # Cancel alarm
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
    
    def should_skip_timeout(self, request) -> bool:
        """
        Check if timeout should be skipped for this request.
        
        Args:
            request: Django request object
            
        Returns:
            True if timeout should be skipped
        """
        for skip_path in self.SKIP_PATHS:
            if request.path.startswith(skip_path):
                return True
        return False
    
    def timeout_handler(self, signum, frame):
        """
        Signal handler for timeout alarm.
        
        Raises TimeoutError when alarm fires.
        """
        raise TimeoutError(f"Request exceeded {self.timeout}s timeout")
    
    def handle_timeout(self, request, error: TimeoutError) -> JsonResponse:
        """
        Handle request timeout.
        
        Args:
            request: Django request object
            error: TimeoutError exception
            
        Returns:
            504 Gateway Timeout response
        """
        logger.error(
            f"Request timeout",
            extra={
                'path': request.path,
                'method': request.method,
                'timeout': self.timeout,
                'user': getattr(request, 'user_profile', None)
            }
        )
        
        return JsonResponse(
            {
                'error': 'Request timeout',
                'message': f'Request exceeded {self.timeout} second timeout',
                'timeout': self.timeout
            },
            status=504
        )
