"""Rate limiting decorators and utilities."""
from functools import wraps
from django.core.cache import cache
from rest_framework.response import Response
from rest_framework import status


def rate_limit(key_prefix, max_requests, window_seconds):
    """
    Rate limiting decorator using Valkey with sliding window algorithm.
    
    Args:
        key_prefix: Prefix for cache key (e.g., 'whisper_create')
        max_requests: Maximum number of requests allowed in window
        window_seconds: Time window in seconds
        
    Returns:
        Decorator function
        
    Usage:
        @rate_limit('whisper_create', 10, 60)
        def create_whisper(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Get user ID from request
            user_id = getattr(request, 'clerk_user_id', None)
            if not user_id:
                # No user ID, skip rate limiting
                return view_func(request, *args, **kwargs)
            
            # Generate cache key
            cache_key = f"rate_limit:{key_prefix}:{user_id}"
            
            # Get current count
            current = cache.get(cache_key, 0)
            
            # Check if limit exceeded
            if current >= max_requests:
                return Response(
                    {
                        'error': {
                            'code': 'RATE_LIMIT_EXCEEDED',
                            'message': 'Rate limit exceeded. Please try again later.',
                            'details': {
                                'limit': max_requests,
                                'window': window_seconds
                            }
                        }
                    },
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                    headers={'Retry-After': str(window_seconds)}
                )
            
            # Increment counter
            if current == 0:
                # First request in window, set with expiry
                cache.set(cache_key, 1, window_seconds)
            else:
                # Increment existing counter
                cache.incr(cache_key)
            
            # Execute view
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator
