"""Decorators for authentication and authorization."""
from functools import wraps
from rest_framework.response import Response
from rest_framework import status
from .exceptions import AuthenticationRequired, InvalidToken, InsufficientPermissions


def require_authentication(view_func):
    """
    Decorator to require authentication for a view.
    
    Checks if request.clerk_user_id and request.user_profile are set.
    If not, raises AuthenticationRequired or InvalidToken exception.
    
    Requirements:
        - 17.7: Return HTTP 401 for missing/invalid tokens
    
    Usage:
        @require_authentication
        def my_view(request):
            # request.clerk_user_id and request.user_profile are guaranteed to exist
            pass
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Check if authentication was attempted but failed
        if hasattr(request, 'auth_error') and request.auth_error:
            if request.auth_error in ['expired_token', 'invalid_token']:
                raise InvalidToken()
            else:
                raise AuthenticationRequired()
        
        # Check if user is authenticated
        if not request.clerk_user_id or not request.user_profile:
            raise AuthenticationRequired()
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def require_ownership(get_owner_id):
    """
    Decorator to require that the authenticated user owns the resource.
    
    Args:
        get_owner_id: Function that takes (request, *args, **kwargs) and returns the owner's user_id
    
    Requirements:
        - 17.8: Return HTTP 403 for authorization failures
    
    Usage:
        def get_story_owner(request, story_id):
            # Fetch story and return author_id
            return story.author_id
        
        @require_authentication
        @require_ownership(get_story_owner)
        def update_story(request, story_id):
            # User is guaranteed to own the story
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Get the owner ID
            owner_id = get_owner_id(request, *args, **kwargs)
            
            # Check if current user is the owner
            if request.user_profile.id != owner_id:
                raise InsufficientPermissions(
                    detail="You do not have permission to modify this resource."
                )
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    
    return decorator


def check_not_blocked(get_target_user_id):
    """
    Decorator to check that the target user is not blocked by the current user.
    
    Args:
        get_target_user_id: Function that takes (request, *args, **kwargs) and returns the target user_id
    
    Requirements:
        - 11.5: Exclude blocked user content from feeds
        - 11.6: Exclude blocked user content from search
    
    Usage:
        def get_author_id(request, story_id):
            # Fetch story and return author_id
            return story.author_id
        
        @require_authentication
        @check_not_blocked(get_author_id)
        def view_story(request, story_id):
            # User has not blocked the story author
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        async def wrapper(request, *args, **kwargs):
            from prisma import Prisma
            
            # Get the target user ID
            target_user_id = get_target_user_id(request, *args, **kwargs)
            
            # Check if current user has blocked the target user
            db = Prisma()
            await db.connect()
            
            try:
                block = await db.block.find_first(
                    where={
                        'blocker_id': request.user_profile.id,
                        'blocked_id': target_user_id
                    }
                )
                
                if block:
                    from .exceptions import UserBlocked
                    raise UserBlocked(
                        detail="You have blocked this user and cannot access their content."
                    )
                
            finally:
                await db.disconnect()
            
            return await view_func(request, *args, **kwargs)
        
        return wrapper
    
    return decorator



def async_api_view(view_func):
    """
    Decorator to handle async view functions with DRF.
    
    Wraps an async view function to make it compatible with Django REST Framework.
    Handles async execution and ensures proper response handling.
    
    Usage:
        @api_view(['GET'])
        @async_api_view
        async def my_async_view(request):
            result = await some_async_operation()
            return Response(result)
    """
    import asyncio
    from asgiref.sync import sync_to_async
    
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Run the async view function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(view_func(request, *args, **kwargs))
        finally:
            loop.close()
    
    return wrapper
