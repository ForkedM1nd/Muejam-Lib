"""
Session Manager Implementation

Manages user sessions and invalidation.
"""
from django.contrib.sessions.models import Session
from django.utils import timezone
from asgiref.sync import sync_to_async
from ..interfaces import ISessionManager


class SessionManager(ISessionManager):
    """
    Service for managing user sessions.
    
    Implements session invalidation on password reset to ensure
    security by terminating all active sessions.
    """
    
    async def invalidate_all_sessions(self, user_id: str) -> None:
        """
        Invalidate all active sessions for a user.
        
        This method removes all session tokens from the database for the given user,
        effectively logging them out from all devices and browsers.
        
        Args:
            user_id: The user ID whose sessions should be invalidated
            
        Implementation:
            Django stores sessions in the django_session table with session data
            encoded. We need to:
            1. Iterate through all active sessions
            2. Decode session data to check if it belongs to the user
            3. Delete matching sessions
            
        Note:
            Django's session framework is synchronous, so we wrap it in sync_to_async.
        """
        await sync_to_async(self._invalidate_sessions_sync)(user_id)
    
    def _invalidate_sessions_sync(self, user_id: str) -> None:
        """Synchronous implementation of session invalidation."""
        # Get all non-expired sessions using the default database
        current_time = timezone.now()
        active_sessions = Session.objects.using('default').filter(expire_date__gte=current_time)
        
        # Check each session to see if it belongs to the user
        sessions_to_delete = []
        for session in active_sessions:
            session_data = session.get_decoded()
            # Check if this session belongs to the user
            # Django stores user_id in session data under '_auth_user_id' key
            if session_data.get('_auth_user_id') == user_id or session_data.get('user_id') == user_id:
                sessions_to_delete.append(session.session_key)
        
        # Delete all matching sessions
        if sessions_to_delete:
            Session.objects.using('default').filter(session_key__in=sessions_to_delete).delete()
