"""
Authentication Error Response Utilities

Provides utilities for returning clear, structured error responses for
authentication failures, including token expiration with refresh guidance.

Requirements: 17.3
"""

from rest_framework.response import Response
from rest_framework import status


def get_auth_error_response(request):
    """
    Get a structured error response based on request authentication error.
    
    This function checks the request.auth_error and request.auth_error_details
    attributes set by the ClerkAuthMiddleware and returns an appropriate
    error response with clear messaging and guidance.
    
    Args:
        request: Django request object with auth_error and auth_error_details
        
    Returns:
        Response object with structured error, or None if no auth error
        
    Validates: Requirement 17.3
    """
    if not hasattr(request, 'auth_error') or not request.auth_error:
        return None
    
    # Check if we have detailed error information
    if hasattr(request, 'auth_error_details') and request.auth_error_details:
        return Response(
            {'error': request.auth_error_details},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Fallback to basic error responses
    error_responses = {
        'expired_token': {
            'code': 'TOKEN_EXPIRED',
            'message': 'Your authentication token has expired',
            'details': {
                'technical_message': 'JWT token has expired and needs to be refreshed',
                'refresh_guidance': 'Please use the /v1/sessions/refresh endpoint with your refresh token to obtain a new access token'
            }
        },
        'invalid_token': {
            'code': 'TOKEN_INVALID',
            'message': 'Your authentication token is invalid',
            'details': {
                'technical_message': 'JWT token signature verification failed or token is malformed'
            }
        },
        'profile_error': {
            'code': 'PROFILE_ERROR',
            'message': 'Failed to retrieve user profile',
            'details': {
                'technical_message': 'User profile could not be loaded from database'
            }
        },
        'authentication_failed': {
            'code': 'AUTHENTICATION_FAILED',
            'message': 'Authentication failed',
            'details': {
                'technical_message': 'Token verification failed due to an unexpected error'
            }
        }
    }
    
    error_data = error_responses.get(
        request.auth_error,
        {
            'code': 'AUTHENTICATION_REQUIRED',
            'message': 'Authentication is required to access this resource'
        }
    )
    
    return Response(
        {'error': error_data},
        status=status.HTTP_401_UNAUTHORIZED
    )


def require_authentication(view_func):
    """
    Decorator to require authentication and return clear error responses.
    
    This decorator checks if the request is authenticated and returns
    a structured error response with token refresh guidance if authentication
    failed due to token expiration.
    
    Usage:
        @require_authentication
        @api_view(['GET'])
        def my_view(request):
            # request.user_profile is guaranteed to exist here
            ...
    
    Args:
        view_func: View function to wrap
        
    Returns:
        Wrapped view function that checks authentication
        
    Validates: Requirement 17.3
    """
    def wrapper(request, *args, **kwargs):
        # Check for authentication errors first
        error_response = get_auth_error_response(request)
        if error_response:
            return error_response
        
        # Check if user is authenticated
        if not request.clerk_user_id or not request.user_profile:
            return Response(
                {
                    'error': {
                        'code': 'AUTHENTICATION_REQUIRED',
                        'message': 'Authentication is required to access this resource',
                        'details': {
                            'technical_message': 'No valid authentication token provided'
                        }
                    }
                },
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Call the original view
        return view_func(request, *args, **kwargs)
    
    return wrapper
