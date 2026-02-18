"""Rate limiting decorators and utilities."""
from functools import wraps
from django.core.cache import cache
from rest_framework.response import Response
from rest_framework import status


def get_client_ip(request):
    """
    Extract client IP address from request.
    
    Checks X-Forwarded-For header first (for proxied requests),
    then falls back to REMOTE_ADDR.
    
    Args:
        request: Django request object
        
    Returns:
        Client IP address as string
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # X-Forwarded-For can contain multiple IPs, take the first one
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def require_captcha(view_func):
    """
    Decorator to require reCAPTCHA validation for a view.
    
    Expects 'recaptcha_token' in request data (POST/PUT/PATCH) or query params (GET).
    Validates the token and blocks the request if validation fails.
    
    Usage:
        @require_captcha
        def create_whisper(request):
            ...
    
    Requirements:
        - 5.4: Integrate reCAPTCHA v3 on signup, login, and content submission forms
        - 5.5: Block actions with reCAPTCHA score < 0.5
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        from apps.core.captcha import captcha_validator
        from apps.core.exceptions import CaptchaValidationError
        
        # Skip validation if reCAPTCHA is not configured
        if not captcha_validator.enabled:
            return view_func(request, *args, **kwargs)
        
        # Extract token from request
        if hasattr(request, 'data'):
            token = request.data.get('recaptcha_token')
        else:
            token = request.GET.get('recaptcha_token')
        
        # Get client IP
        remote_ip = get_client_ip(request)
        
        # Validate token
        try:
            captcha_validator.validate_or_raise(token, remote_ip)
        except CaptchaValidationError as e:
            return Response(
                {
                    'error': {
                        'code': 'CAPTCHA_VALIDATION_FAILED',
                        'message': str(e),
                        'details': {}
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Execute view
        return view_func(request, *args, **kwargs)
    
    return wrapper


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
