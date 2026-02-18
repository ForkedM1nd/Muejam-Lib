"""
Shadowban Service for managing user shadowbans.

A shadowban restricts a user's content visibility without their knowledge.
Shadowbanned users can post content, but it's hidden from other users.

This service handles:
- Creating and removing shadowbans
- Checking shadowban status
- Filtering content from shadowbanned users

Requirements: 5.12
"""
import logging
from typing import Optional, Dict, Any, List
from prisma import Prisma

logger = logging.getLogger(__name__)


class ShadowbanService:
    """
    Service for managing shadowbans.
    
    Implements:
    - Shadowban creation and removal
    - Shadowban status checking
    - Content filtering for shadowbanned users
    """
    
    async def apply_shadowban(
        self,
        user_id: str,
        applied_by: str,
        reason: str
    ) -> Dict[str, Any]:
        """
        Apply a shadowban to a user account.
        
        Args:
            user_id: ID of user to shadowban
            applied_by: ID of administrator applying shadowban
            reason: Reason for shadowban
            
        Returns:
            Dictionary with shadowban details
            
        Requirements: 5.12
        """
        db = Prisma()
        await db.connect()
        
        try:
            # Deactivate any existing active shadowbans
            await db.shadowban.update_many(
                where={
                    'user_id': user_id,
                    'is_active': True
                },
                data={'is_active': False}
            )
            
            # Create new shadowban
            shadowban = await db.shadowban.create(
                data={
                    'user_id': user_id,
                    'applied_by': applied_by,
                    'reason': reason,
                    'is_active': True
                }
            )
            
            logger.info(
                f"Shadowban applied: user_id={user_id}, "
                f"applied_by={applied_by}, "
                f"reason={reason[:50]}"
            )
            
            return {
                'id': shadowban.id,
                'user_id': shadowban.user_id,
                'applied_by': shadowban.applied_by,
                'reason': shadowban.reason,
                'applied_at': shadowban.applied_at,
                'is_active': shadowban.is_active
            }
            
        finally:
            await db.disconnect()
    
    async def check_shadowban(
        self,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Check if a user is currently shadowbanned.
        
        Args:
            user_id: ID of user to check
            
        Returns:
            Shadowban details if shadowbanned, None if not shadowbanned
            
        Requirements: 5.12
        """
        db = Prisma()
        await db.connect()
        
        try:
            # Get active shadowban
            shadowban = await db.shadowban.find_first(
                where={
                    'user_id': user_id,
                    'is_active': True
                },
                order_by={'applied_at': 'desc'}
            )
            
            if not shadowban:
                return None
            
            return {
                'id': shadowban.id,
                'user_id': shadowban.user_id,
                'applied_by': shadowban.applied_by,
                'reason': shadowban.reason,
                'applied_at': shadowban.applied_at,
                'is_active': shadowban.is_active
            }
            
        finally:
            await db.disconnect()
    
    async def is_shadowbanned(
        self,
        user_id: str
    ) -> bool:
        """
        Quick check if a user is shadowbanned.
        
        Args:
            user_id: ID of user to check
            
        Returns:
            True if shadowbanned, False otherwise
        """
        shadowban = await self.check_shadowban(user_id)
        return shadowban is not None
    
    async def remove_shadowban(
        self,
        user_id: str,
        removed_by: str
    ) -> bool:
        """
        Remove an active shadowban.
        
        Args:
            user_id: ID of user to unshadowban
            removed_by: ID of administrator removing shadowban
            
        Returns:
            True if shadowban was removed, False if no active shadowban
        """
        db = Prisma()
        await db.connect()
        
        try:
            # Deactivate active shadowbans
            result = await db.shadowban.update_many(
                where={
                    'user_id': user_id,
                    'is_active': True
                },
                data={'is_active': False}
            )
            
            if result > 0:
                logger.info(
                    f"Shadowban removed for user {user_id} by {removed_by}"
                )
                return True
            
            return False
            
        finally:
            await db.disconnect()
    
    async def filter_shadowbanned_content(
        self,
        content_list: List[Dict[str, Any]],
        requesting_user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter out content from shadowbanned users.
        
        Content from shadowbanned users is visible to:
        - The shadowbanned user themselves
        - Administrators and moderators
        
        Args:
            content_list: List of content items with 'user_id' or 'author_id' field
            requesting_user_id: ID of user requesting content (None for anonymous)
            
        Returns:
            Filtered content list
            
        Requirements: 5.12
        """
        if not content_list:
            return []
        
        db = Prisma()
        await db.connect()
        
        try:
            # Get all unique user IDs from content
            user_ids = set()
            for item in content_list:
                # Handle different field names for user ID
                user_id = item.get('user_id') or item.get('author_id')
                if user_id:
                    user_ids.add(user_id)
            
            if not user_ids:
                return content_list
            
            # Get all active shadowbans for these users
            shadowbans = await db.shadowban.find_many(
                where={
                    'user_id': {'in': list(user_ids)},
                    'is_active': True
                }
            )
            
            shadowbanned_user_ids = {sb.user_id for sb in shadowbans}
            
            if not shadowbanned_user_ids:
                # No shadowbanned users in content
                return content_list
            
            # Check if requesting user is admin/moderator
            is_moderator = False
            if requesting_user_id:
                moderator_role = await db.moderatorrole.find_first(
                    where={
                        'user_id': requesting_user_id,
                        'is_active': True
                    }
                )
                is_moderator = moderator_role is not None
            
            # Filter content
            filtered_content = []
            for item in content_list:
                user_id = item.get('user_id') or item.get('author_id')
                
                # Include content if:
                # 1. User is not shadowbanned
                # 2. Requesting user is the shadowbanned user themselves
                # 3. Requesting user is a moderator
                if (
                    user_id not in shadowbanned_user_ids or
                    user_id == requesting_user_id or
                    is_moderator
                ):
                    filtered_content.append(item)
            
            logger.debug(
                f"Filtered {len(content_list) - len(filtered_content)} "
                f"shadowbanned content items"
            )
            
            return filtered_content
            
        finally:
            await db.disconnect()
    
    async def get_shadowban_history(
        self,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get shadowban history for a user.
        
        Args:
            user_id: ID of user
            
        Returns:
            List of shadowban records
        """
        db = Prisma()
        await db.connect()
        
        try:
            shadowbans = await db.shadowban.find_many(
                where={'user_id': user_id},
                order_by={'applied_at': 'desc'}
            )
            
            return [
                {
                    'id': sb.id,
                    'applied_by': sb.applied_by,
                    'reason': sb.reason,
                    'applied_at': sb.applied_at,
                    'is_active': sb.is_active
                }
                for sb in shadowbans
            ]
            
        finally:
            await db.disconnect()
