"""
Rate limiting middleware for enforcing request rate limits.

This middleware integrates with the RateLimiter infrastructure to enforce
rate limits on all incoming requests. It provides:
- Per-user rate limiting (authenticated users)
- Per-IP rate limiting (anonymous users)
- Client-type-specific rate limits (mobile vs web)
- Admin bypass capability
- Health check endpoint exemption
- Standard rate limit headers (X-RateLimit-*)
- 429 status with Retry-After header when limit exceeded

The middleware uses the MobileRateLimiter class which implements
a sliding window algorithm with Redis for distributed rate limiting
and supports client-type-specific rate limits.

Requirements: 8.1, 8.2, 8.3, 8.4
"""

import logging
from django.http import JsonResponse
from infrastructure.rate_limiter import MobileRateLimiter

logger = logging.getLogger(__name__)


class RateLimitMiddleware:
    """
    Middleware to enforce rate limiting on all requests.
    
    This middleware:
    1. Skips rate limiting for health check endpoints
    2. Identifies users by user_profile.id (authenticated) or IP (anonymous)
    3. Checks if user is admin and bypasses rate limits if configured
    4. Enforces rate limits using the RateLimiter infrastructure
    5. Returns 429 with Retry-After header when limit exceeded
    6. Adds rate limit headers to all responses
    
    Rate limit headers added to responses:
    - X-RateLimit-Limit: Maximum requests allowed in window
    - X-RateLimit-Remaining: Requests remaining in current window
    - X-RateLimit-Reset: ISO timestamp when the rate limit resets
    
    When rate limit is exceeded:
    - Returns 429 Too Many Requests
    - Includes Retry-After header (seconds until retry allowed)
    - Includes error message with limit details
    """
    
    def __init__(self, get_response):
        """
        Initialize rate limit middleware.
        
        Args:
            get_response: Next middleware or view in the chain
        """
        self.get_response = get_response
        self.rate_limiter = MobileRateLimiter()
        
        # Paths to skip rate limiting
        self.skip_paths = ['/health', '/metrics']
    
    def __call__(self, request):
        """
        Process request and enforce rate limiting.
        
        Args:
            request: Django request object
            
        Returns:
            Django response object (429 if rate limited, otherwise normal response)
        """
        # Skip rate limiting for health checks and metrics
        if request.path in self.skip_paths:
            return self.get_response(request)
        
        # Get user identifier (user ID for authenticated, IP for anonymous)
        user_id = self._get_user_identifier(request)
        
        # Check if user is admin (bypass rate limiting)
        is_admin = self._is_admin_user(request)
        
        # Get client type from request (set by ClientTypeMiddleware)
        client_type = getattr(request, 'client_type', 'web')
        
        # Check rate limit with client type
        if not self.rate_limiter.allow_request(user_id, is_admin, client_type):
            # Rate limit exceeded - get details for response
            user_result = self.rate_limiter.check_user_limit(user_id, client_type)
            
            logger.warning(
                f"Rate limit exceeded for {user_id}",
                extra={
                    'user_id': user_id,
                    'client_type': client_type,
                    'path': request.path,
                    'method': request.method,
                    'limit': user_result.limit,
                    'retry_after': user_result.retry_after
                }
            )
            
            # Return 429 response with rate limit details
            response = JsonResponse(
                {
                    'error': 'Rate limit exceeded',
                    'message': f'Too many requests. Limit: {user_result.limit} requests per minute.',
                    'limit': user_result.limit,
                    'retry_after': user_result.retry_after
                },
                status=429
            )
            
            # Add rate limit headers
            response['Retry-After'] = str(user_result.retry_after)
            response['X-RateLimit-Limit'] = str(user_result.limit)
            response['X-RateLimit-Remaining'] = '0'
            response['X-RateLimit-Reset'] = user_result.reset_at.isoformat()
            
            return response
        
        # Process request normally
        response = self.get_response(request)
        
        # Add rate limit headers to response
        user_result = self.rate_limiter.check_user_limit(user_id, client_type)
        response['X-RateLimit-Limit'] = str(user_result.limit)
        response['X-RateLimit-Remaining'] = str(user_result.remaining)
        response['X-RateLimit-Reset'] = user_result.reset_at.isoformat()
        
        return response
    
    @staticmethod
    def _get_user_identifier(request) -> str:
        """
        Get user identifier for rate limiting.
        
        Uses user_profile.id for authenticated users, IP address for anonymous users.
        
        Args:
            request: Django request object
            
        Returns:
            User identifier string
        """
        # Use user profile ID if authenticated
        if hasattr(request, 'user_profile') and request.user_profile:
            return f"user:{request.user_profile.id}"
        
        # Fall back to IP address for anonymous users
        return f"ip:{RateLimitMiddleware._get_client_ip(request)}"
    
    @staticmethod
    def _get_client_ip(request) -> str:
        """
        Get client IP address from request.
        
        Handles X-Forwarded-For header for requests behind proxies/load balancers.
        
        Args:
            request: Django request object
            
        Returns:
            Client IP address
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # X-Forwarded-For can contain multiple IPs, take the first (client IP)
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        return ip
    
    @staticmethod
    def _is_admin_user(request) -> bool:
        """
        Check if user has admin/moderator privileges.
        
        Checks if the user has an active ModeratorRole in the database.
        Uses Django ORM instead of Prisma to avoid async/sync issues.
        
        Args:
            request: Django request object
            
        Returns:
            True if user is admin, False otherwise
        """
        if not hasattr(request, 'user_profile') or not request.user_profile:
            return False
        
        try:
            # Use Django ORM to check moderator role
            # This avoids async/sync issues with Prisma
            from django.db import connection
            
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT COUNT(*) 
                    FROM "ModeratorRole" 
                    WHERE user_id = %s AND is_active = TRUE
                    """,
                    [request.user_profile.id]
                )
                count = cursor.fetchone()[0]
                return count > 0
                
        except Exception as e:
            logger.error(f"Error checking admin status: {e}")
            return False
