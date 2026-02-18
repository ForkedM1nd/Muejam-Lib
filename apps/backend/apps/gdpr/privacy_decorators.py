"""
Privacy Enforcement Decorators

Decorators for enforcing privacy settings in views.

Requirements:
- 11.8: Apply changes immediately
- 11.9: Respect privacy settings in all API responses
"""

import logging
from functools import wraps
from rest_framework.response import Response
from rest_framework import status
from .privacy_enforcement import PrivacyEnforcement

logger = logging.getLogger(__name__)


def require_profile_visibility(view_func):
    """
    Decorator to enforce profile visibility settings.
    
    Usage:
        @require_profile_visibility
        async def get_user_profile(request, user_id):
            ...
    
    Requirements: 11.2, 11.9
    """
    @wraps(view_func)
    async def wrapper(request, *args, **kwargs):
        # Get target user ID from kwargs or request
        target_user_id = kwargs.get('user_id') or kwargs.get('id')
        viewer_user_id = getattr(request, 'clerk_user_id', None)
        
        if target_user_id:
            can_view = await PrivacyEnforcement.can_view_profile(target_user_id, viewer_user_id)
            
            if not can_view:
                return Response(
                    {'error': 'This profile is private'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        return await view_func(request, *args, **kwargs)
    
    return wrapper


def require_reading_history_visibility(view_func):
    """
    Decorator to enforce reading history visibility settings.
    
    Usage:
        @require_reading_history_visibility
        async def get_reading_history(request, user_id):
            ...
    
    Requirements: 11.3, 11.9
    """
    @wraps(view_func)
    async def wrapper(request, *args, **kwargs):
        # Get target user ID from kwargs or request
        target_user_id = kwargs.get('user_id') or kwargs.get('id')
        viewer_user_id = getattr(request, 'clerk_user_id', None)
        
        if target_user_id:
            can_view = await PrivacyEnforcement.can_view_reading_history(target_user_id, viewer_user_id)
            
            if not can_view:
                return Response(
                    {'error': 'This user\'s reading history is private'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        return await view_func(request, *args, **kwargs)
    
    return wrapper


def require_comment_permission(view_func):
    """
    Decorator to enforce comment permission settings.
    
    Usage:
        @require_comment_permission
        async def create_comment(request, content_id):
            ...
    
    Requirements: 11.6, 11.9
    """
    @wraps(view_func)
    async def wrapper(request, *args, **kwargs):
        # Get content owner ID from request data or kwargs
        content_owner_id = request.data.get('content_owner_id') or kwargs.get('content_owner_id')
        commenter_id = getattr(request, 'clerk_user_id', None)
        
        if content_owner_id:
            can_comment = await PrivacyEnforcement.can_comment_on_content(content_owner_id, commenter_id)
            
            if not can_comment:
                return Response(
                    {'error': 'Comments are not allowed on this content'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        return await view_func(request, *args, **kwargs)
    
    return wrapper


def check_analytics_opt_out(view_func):
    """
    Decorator to check analytics opt-out before tracking.
    
    This decorator adds a flag to the request indicating whether
    analytics should be tracked for this user.
    
    Usage:
        @check_analytics_opt_out
        async def some_view(request):
            if request.should_track_analytics:
                # Track analytics
                pass
    
    Requirements: 11.4, 11.9
    """
    @wraps(view_func)
    async def wrapper(request, *args, **kwargs):
        user_id = getattr(request, 'clerk_user_id', None)
        
        if user_id:
            request.should_track_analytics = await PrivacyEnforcement.should_track_analytics(user_id)
        else:
            request.should_track_analytics = True
        
        return await view_func(request, *args, **kwargs)
    
    return wrapper
