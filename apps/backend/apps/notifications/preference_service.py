"""
Notification Preference Service.

Manages user notification preferences.
Implements Requirements 21.9, 21.10.
"""
import logging
from typing import Dict, Any, Optional
from prisma import Prisma
from datetime import datetime

logger = logging.getLogger(__name__)


class NotificationPreferenceService:
    """
    Service for managing notification preferences.
    
    Implements Requirements:
    - 21.9: Allow users to configure notification preferences
    - 21.10: Support notification frequency options
    """
    
    VALID_FREQUENCIES = ['immediate', 'daily_digest', 'weekly_digest', 'disabled']
    
    NOTIFICATION_TYPES = [
        'welcome_email',
        'new_comment',
        'new_like',
        'new_follower',
        'new_content',
        'content_takedown',
        'security_alert'
    ]
    
    @classmethod
    async def get_preferences(cls, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get notification preferences for a user.
        
        Implements Requirement 21.9: Retrieve user notification preferences.
        
        Args:
            user_id: User ID
        
        Returns:
            Dict containing preference settings or None if not found
        """
        db = Prisma()
        await db.connect()
        
        try:
            preferences = await db.notificationpreference.find_unique(
                where={'user_id': user_id}
            )
            
            await db.disconnect()
            
            if not preferences:
                return None
            
            return {
                'user_id': preferences.user_id,
                'welcome_email': preferences.welcome_email,
                'new_comment': preferences.new_comment,
                'new_like': preferences.new_like,
                'new_follower': preferences.new_follower,
                'new_content': preferences.new_content,
                'content_takedown': preferences.content_takedown,
                'security_alert': preferences.security_alert,
                'marketing_emails': preferences.marketing_emails,
                'updated_at': preferences.updated_at.isoformat()
            }
            
        except Exception as e:
            await db.disconnect()
            logger.error(f"Failed to get preferences for user {user_id}: {str(e)}")
            raise
    
    @classmethod
    async def create_default_preferences(cls, user_id: str) -> Dict[str, Any]:
        """
        Create default notification preferences for a new user.
        
        Implements Requirement 21.9: Initialize default preferences.
        
        Args:
            user_id: User ID
        
        Returns:
            Dict containing created preference settings
        """
        db = Prisma()
        await db.connect()
        
        try:
            preferences = await db.notificationpreference.create(
                data={
                    'user_id': user_id,
                    'welcome_email': 'immediate',
                    'new_comment': 'immediate',
                    'new_like': 'daily_digest',  # Reduce email volume
                    'new_follower': 'immediate',
                    'new_content': 'immediate',
                    'content_takedown': 'immediate',  # Always immediate for compliance
                    'security_alert': 'immediate',  # Always immediate for security
                    'marketing_emails': True
                }
            )
            
            await db.disconnect()
            
            logger.info(f"Created default preferences for user {user_id}")
            
            return {
                'user_id': preferences.user_id,
                'welcome_email': preferences.welcome_email,
                'new_comment': preferences.new_comment,
                'new_like': preferences.new_like,
                'new_follower': preferences.new_follower,
                'new_content': preferences.new_content,
                'content_takedown': preferences.content_takedown,
                'security_alert': preferences.security_alert,
                'marketing_emails': preferences.marketing_emails,
                'updated_at': preferences.updated_at.isoformat()
            }
            
        except Exception as e:
            await db.disconnect()
            logger.error(f"Failed to create preferences for user {user_id}: {str(e)}")
            raise
    
    @classmethod
    async def update_preferences(cls, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update notification preferences for a user.
        
        Implements Requirements:
        - 21.9: Allow users to configure notification preferences
        - 21.10: Support per-notification-type frequency settings
        
        Args:
            user_id: User ID
            updates: Dict of preference updates
        
        Returns:
            Dict containing updated preference settings
        """
        db = Prisma()
        await db.connect()
        
        try:
            # Validate frequency values
            for key, value in updates.items():
                if key in cls.NOTIFICATION_TYPES and value not in cls.VALID_FREQUENCIES:
                    raise ValueError(f"Invalid frequency '{value}' for {key}. Must be one of: {cls.VALID_FREQUENCIES}")
            
            # Ensure critical notifications remain immediate
            if 'content_takedown' in updates and updates['content_takedown'] != 'immediate':
                logger.warning(f"Attempted to change content_takedown frequency for user {user_id}. Keeping as immediate.")
                updates['content_takedown'] = 'immediate'
            
            if 'security_alert' in updates and updates['security_alert'] != 'immediate':
                logger.warning(f"Attempted to change security_alert frequency for user {user_id}. Keeping as immediate.")
                updates['security_alert'] = 'immediate'
            
            # Update preferences
            preferences = await db.notificationpreference.update(
                where={'user_id': user_id},
                data=updates
            )
            
            await db.disconnect()
            
            logger.info(f"Updated preferences for user {user_id}: {updates}")
            
            return {
                'user_id': preferences.user_id,
                'welcome_email': preferences.welcome_email,
                'new_comment': preferences.new_comment,
                'new_like': preferences.new_like,
                'new_follower': preferences.new_follower,
                'new_content': preferences.new_content,
                'content_takedown': preferences.content_takedown,
                'security_alert': preferences.security_alert,
                'marketing_emails': preferences.marketing_emails,
                'updated_at': preferences.updated_at.isoformat()
            }
            
        except Exception as e:
            await db.disconnect()
            logger.error(f"Failed to update preferences for user {user_id}: {str(e)}")
            raise
    
    @classmethod
    async def get_or_create_preferences(cls, user_id: str) -> Dict[str, Any]:
        """
        Get preferences for a user, creating defaults if they don't exist.
        
        Args:
            user_id: User ID
        
        Returns:
            Dict containing preference settings
        """
        preferences = await cls.get_preferences(user_id)
        
        if preferences is None:
            preferences = await cls.create_default_preferences(user_id)
        
        return preferences
    
    @classmethod
    async def should_send_notification(cls, user_id: str, notification_type: str) -> tuple[bool, str]:
        """
        Check if a notification should be sent based on user preferences.
        
        Implements Requirements:
        - 21.10: Respect user frequency preferences
        - 21.13: Respect unsubscribe preferences
        
        Args:
            user_id: User ID
            notification_type: Type of notification
        
        Returns:
            Tuple of (should_send, frequency)
            - should_send: True if notification should be sent
            - frequency: The frequency setting (immediate, daily_digest, weekly_digest, disabled)
        """
        preferences = await cls.get_or_create_preferences(user_id)
        
        # Get frequency for this notification type
        frequency = preferences.get(notification_type, 'immediate')
        
        # Check if disabled
        if frequency == 'disabled':
            return (False, frequency)
        
        # Check marketing email preference for non-transactional emails
        marketing_types = ['new_content', 'new_like']
        if notification_type in marketing_types and not preferences.get('marketing_emails', True):
            return (False, 'disabled')
        
        # Return True with the frequency setting
        return (True, frequency)
