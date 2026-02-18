"""
Privacy Settings Enforcement

Utilities for enforcing privacy settings across the application.

Requirements:
- 11.2: Apply profile visibility
- 11.3: Apply reading history visibility
- 11.4: Respect analytics opt-out
- 11.5: Respect marketing email preferences
- 11.6: Apply comment permissions
- 11.7: Apply follower approval requirements
- 11.9: Respect privacy settings in all API responses
"""

import logging
from prisma import Prisma
from prisma.enums import VisibilityLevel, CommentPermission, FollowerApproval

logger = logging.getLogger(__name__)


class PrivacyEnforcement:
    """Utility class for enforcing privacy settings."""
    
    @staticmethod
    async def get_user_privacy_settings(user_id: str) -> dict:
        """
        Get user's privacy settings.
        
        Args:
            user_id: User ID
            
        Returns:
            Privacy settings dictionary or None if not found
        """
        db = Prisma()
        await db.connect()
        
        try:
            settings = await db.privacysettings.find_unique(
                where={'user_id': user_id}
            )
            
            if not settings:
                return None
            
            return {
                'profile_visibility': settings.profile_visibility,
                'reading_history_visibility': settings.reading_history_visibility,
                'analytics_opt_out': settings.analytics_opt_out,
                'marketing_emails': settings.marketing_emails,
                'comment_permissions': settings.comment_permissions,
                'follower_approval_required': settings.follower_approval_required
            }
            
        finally:
            await db.disconnect()
    
    @staticmethod
    async def can_view_profile(target_user_id: str, viewer_user_id: str = None) -> bool:
        """
        Check if viewer can see target user's profile.
        
        Args:
            target_user_id: User whose profile is being viewed
            viewer_user_id: User viewing the profile (None for anonymous)
            
        Returns:
            True if profile can be viewed, False otherwise
            
        Requirements: 11.2, 11.9
        """
        settings = await PrivacyEnforcement.get_user_privacy_settings(target_user_id)
        
        if not settings:
            # Default to public if no settings exist
            return True
        
        visibility = settings['profile_visibility']
        
        if visibility == VisibilityLevel.PUBLIC:
            return True
        
        if visibility == VisibilityLevel.PRIVATE:
            # Only the user themselves can view
            return viewer_user_id == target_user_id
        
        if visibility == VisibilityLevel.FOLLOWERS_ONLY:
            if viewer_user_id == target_user_id:
                return True
            
            if viewer_user_id:
                # Check if viewer follows target user
                return await PrivacyEnforcement._is_following(viewer_user_id, target_user_id)
            
            return False
        
        return False
    
    @staticmethod
    async def can_view_reading_history(target_user_id: str, viewer_user_id: str = None) -> bool:
        """
        Check if viewer can see target user's reading history.
        
        Args:
            target_user_id: User whose reading history is being viewed
            viewer_user_id: User viewing the history (None for anonymous)
            
        Returns:
            True if reading history can be viewed, False otherwise
            
        Requirements: 11.3, 11.9
        """
        settings = await PrivacyEnforcement.get_user_privacy_settings(target_user_id)
        
        if not settings:
            # Default to private if no settings exist
            return viewer_user_id == target_user_id
        
        visibility = settings['reading_history_visibility']
        
        if visibility == VisibilityLevel.PUBLIC:
            return True
        
        if visibility == VisibilityLevel.PRIVATE:
            # Only the user themselves can view
            return viewer_user_id == target_user_id
        
        if visibility == VisibilityLevel.FOLLOWERS_ONLY:
            if viewer_user_id == target_user_id:
                return True
            
            if viewer_user_id:
                # Check if viewer follows target user
                return await PrivacyEnforcement._is_following(viewer_user_id, target_user_id)
            
            return False
        
        return False
    
    @staticmethod
    async def should_track_analytics(user_id: str) -> bool:
        """
        Check if analytics should be tracked for user.
        
        Args:
            user_id: User ID
            
        Returns:
            True if analytics should be tracked, False if opted out
            
        Requirements: 11.4, 11.9
        """
        settings = await PrivacyEnforcement.get_user_privacy_settings(user_id)
        
        if not settings:
            # Default to tracking if no settings exist
            return True
        
        # Return opposite of opt_out (if opted out, don't track)
        return not settings['analytics_opt_out']
    
    @staticmethod
    async def can_send_marketing_email(user_id: str) -> bool:
        """
        Check if marketing emails can be sent to user.
        
        Args:
            user_id: User ID
            
        Returns:
            True if marketing emails are allowed, False otherwise
            
        Requirements: 11.5, 11.9
        """
        settings = await PrivacyEnforcement.get_user_privacy_settings(user_id)
        
        if not settings:
            # Default to allowing marketing emails
            return True
        
        return settings['marketing_emails']
    
    @staticmethod
    async def can_comment_on_content(content_owner_id: str, commenter_id: str = None) -> bool:
        """
        Check if user can comment on content.
        
        Args:
            content_owner_id: Owner of the content
            commenter_id: User trying to comment (None for anonymous)
            
        Returns:
            True if commenting is allowed, False otherwise
            
        Requirements: 11.6, 11.9
        """
        settings = await PrivacyEnforcement.get_user_privacy_settings(content_owner_id)
        
        if not settings:
            # Default to allowing anyone to comment
            return True
        
        permission = settings['comment_permissions']
        
        if permission == CommentPermission.DISABLED:
            return False
        
        if permission == CommentPermission.ANYONE:
            return True
        
        if permission == CommentPermission.FOLLOWERS:
            if not commenter_id:
                return False
            
            if commenter_id == content_owner_id:
                return True
            
            # Check if commenter follows content owner
            return await PrivacyEnforcement._is_following(commenter_id, content_owner_id)
        
        return False
    
    @staticmethod
    async def requires_follower_approval(user_id: str) -> bool:
        """
        Check if user requires approval for new followers.
        
        Args:
            user_id: User ID
            
        Returns:
            True if approval is required, False otherwise
            
        Requirements: 11.7, 11.9
        """
        settings = await PrivacyEnforcement.get_user_privacy_settings(user_id)
        
        if not settings:
            # Default to not requiring approval
            return False
        
        return settings['follower_approval_required'] == FollowerApproval.APPROVAL_REQUIRED
    
    @staticmethod
    async def _is_following(follower_id: str, following_id: str) -> bool:
        """
        Check if one user follows another.
        
        Args:
            follower_id: User who might be following
            following_id: User who might be followed
            
        Returns:
            True if following relationship exists, False otherwise
        """
        db = Prisma()
        await db.connect()
        
        try:
            follow = await db.follow.find_first(
                where={
                    'follower_id': follower_id,
                    'following_id': following_id
                }
            )
            
            return follow is not None
            
        finally:
            await db.disconnect()
    
    @staticmethod
    async def filter_profile_data(profile_data: dict, target_user_id: str, viewer_user_id: str = None) -> dict:
        """
        Filter profile data based on privacy settings.
        
        Args:
            profile_data: Full profile data
            target_user_id: User whose profile this is
            viewer_user_id: User viewing the profile
            
        Returns:
            Filtered profile data
            
        Requirements: 11.2, 11.9
        """
        can_view = await PrivacyEnforcement.can_view_profile(target_user_id, viewer_user_id)
        
        if not can_view:
            # Return minimal public info
            return {
                'id': profile_data.get('id'),
                'handle': profile_data.get('handle'),
                'display_name': profile_data.get('display_name'),
                'is_private': True
            }
        
        # Check reading history visibility
        can_view_history = await PrivacyEnforcement.can_view_reading_history(target_user_id, viewer_user_id)
        
        if not can_view_history and 'reading_history' in profile_data:
            # Remove reading history from response
            profile_data = profile_data.copy()
            del profile_data['reading_history']
        
        return profile_data
