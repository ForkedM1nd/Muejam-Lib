"""Permission decorators and utilities for moderation system."""
from functools import wraps
from rest_framework.response import Response
from rest_framework import status
from prisma import Prisma
import asyncio


async def get_user_moderator_role(user_id: str):
    """
    Get the moderator role for a user.
    
    Args:
        user_id: ID of the user
        
    Returns:
        ModeratorRole object or None if user is not a moderator
        
    Requirements:
        - 3.1: Support role types: ADMINISTRATOR, SENIOR_MODERATOR, MODERATOR
    """
    db = Prisma()
    await db.connect()
    
    try:
        moderator_role = await db.moderatorrole.find_first(
            where={
                'user_id': user_id,
                'is_active': True
            }
        )
        return moderator_role
    finally:
        await db.disconnect()


def require_moderator_role(allowed_roles=None):
    """
    Decorator to require specific moderator roles for an endpoint.
    
    Args:
        allowed_roles: List of allowed role types (e.g., ['ADMINISTRATOR', 'SENIOR_MODERATOR'])
                      If None, any active moderator role is allowed
                      
    Returns:
        Decorator function
        
    Requirements:
        - 3.2: Grant access to moderation dashboard when role is assigned
        - 3.6: Return 403 for unauthorized access
        
    Example:
        @require_moderator_role(['ADMINISTRATOR'])
        def admin_only_view(request):
            pass
            
        @require_moderator_role(['ADMINISTRATOR', 'SENIOR_MODERATOR'])
        def senior_mod_view(request):
            pass
            
        @require_moderator_role()  # Any moderator role
        def any_moderator_view(request):
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Check if user is authenticated
            if not hasattr(request, 'user_profile') or not request.user_profile:
                return Response(
                    {'error': 'Authentication required'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Get user's moderator role
            user_id = request.user_profile.id
            moderator_role = asyncio.run(get_user_moderator_role(user_id))
            
            # Check if user has a moderator role
            if not moderator_role:
                return Response(
                    {'error': 'Moderator access required'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Check if user's role is in allowed roles (if specified)
            if allowed_roles is not None and moderator_role.role not in allowed_roles:
                return Response(
                    {'error': f'Insufficient permissions. Required role: {", ".join(allowed_roles)}'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Store moderator role in request for use in view
            request.moderator_role = moderator_role
            
            # Call the view function
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def require_administrator(view_func):
    """
    Decorator to require administrator role for an endpoint.
    
    Convenience decorator for @require_moderator_role(['ADMINISTRATOR'])
    
    Requirements:
        - 3.5: Only Administrators can delete content, suspend users, and assign moderator roles
        - 3.6: Return 403 for unauthorized access
        
    Example:
        @require_administrator
        def admin_only_view(request):
            pass
    """
    return require_moderator_role(['ADMINISTRATOR'])(view_func)


async def can_perform_action(user_id: str, action_type: str, report_priority: str = None) -> tuple[bool, str]:
    """
    Check if a user can perform a specific moderation action.
    
    Args:
        user_id: ID of the user
        action_type: Type of action (DISMISS, WARN, HIDE, DELETE, SUSPEND)
        report_priority: Priority of the report (for DISMISS action)
        
    Returns:
        Tuple of (can_perform: bool, error_message: str)
        
    Requirements:
        - 3.3: Senior_Moderators can review reports, hide content, and warn users
        - 3.4: Moderators can review reports and dismiss low-priority reports only
        - 3.5: Only Administrators can delete content, suspend users, and assign moderator roles
    """
    moderator_role = await get_user_moderator_role(user_id)
    
    if not moderator_role:
        return False, "User does not have moderator permissions"
    
    role = moderator_role.role
    
    # Administrators can perform any action
    if role == 'ADMINISTRATOR':
        return True, ""
    
    # Senior Moderators can: review reports, hide content, warn users
    if role == 'SENIOR_MODERATOR':
        if action_type in ['DISMISS', 'WARN', 'HIDE']:
            return True, ""
        else:
            return False, f"Senior Moderators cannot perform {action_type} action. Only Administrators can delete content or suspend users."
    
    # Moderators can: review reports, dismiss low-priority reports only
    if role == 'MODERATOR':
        if action_type == 'DISMISS':
            # Check if report is low priority
            if report_priority and report_priority.lower() == 'low':
                return True, ""
            else:
                return False, "Moderators can only dismiss low-priority reports"
        else:
            return False, f"Moderators cannot perform {action_type} action. Only Senior Moderators and Administrators can perform this action."
    
    return False, "Invalid moderator role"


def check_action_permission(view_func):
    """
    Decorator to check if user has permission to perform a moderation action.
    
    This decorator should be used on views that take moderation actions.
    It checks the action_type in request.data and validates permissions.
    
    Requirements:
        - 3.3: Senior_Moderators can review reports, hide content, and warn users
        - 3.4: Moderators can review reports and dismiss low-priority reports only
        - 3.5: Only Administrators can delete content, suspend users, and assign moderator roles
        - 3.6: Return 403 for unauthorized access
        
    Example:
        @check_action_permission
        def take_moderation_action(request):
            # Action permission already validated
            pass
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Check if user is authenticated
        if not hasattr(request, 'user_profile') or not request.user_profile:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Get action type from request
        action_type = request.data.get('action_type')
        if not action_type:
            return Response(
                {'error': 'action_type is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # For DISMISS actions, we need to check report priority
        # This will be validated in the view function after fetching the report
        # For now, we'll do a basic permission check
        user_id = request.user_profile.id
        
        # Get report_id to check priority for DISMISS actions
        report_id = request.data.get('report_id')
        report_priority = None
        
        if action_type == 'DISMISS' and report_id:
            # Fetch report priority
            report_priority = asyncio.run(get_report_priority(report_id))
        
        # Check if user can perform this action
        can_perform, error_message = asyncio.run(
            can_perform_action(user_id, action_type, report_priority)
        )
        
        if not can_perform:
            return Response(
                {'error': error_message},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Call the view function
        return view_func(request, *args, **kwargs)
    
    return wrapper


async def get_report_priority(report_id: str) -> str:
    """
    Get the priority level of a report.
    
    Args:
        report_id: ID of the report
        
    Returns:
        Priority level ('low', 'medium', 'high') or None if not found
    """
    from .queue_service import ModerationQueueService
    
    db = Prisma()
    await db.connect()
    
    try:
        report = await db.report.find_unique(where={'id': report_id})
        if not report:
            return None
        
        # Calculate priority using the queue service
        async with ModerationQueueService() as queue_service:
            priority_score = await queue_service.calculate_priority(report)
            
            # Determine priority level based on score
            if priority_score >= 100:
                return 'high'
            elif priority_score >= 50:
                return 'medium'
            else:
                return 'low'
    finally:
        await db.disconnect()
