"""Service for managing NSFW flags and content preferences."""
from prisma import Prisma
from prisma.enums import NSFWContentType, NSFWDetectionMethod, NSFWPreference
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


class NSFWService:
    """Service for managing NSFW flags and user content preferences."""
    
    def __init__(self):
        """Initialize the NSFW service."""
        self.db = Prisma()
    
    async def create_nsfw_flag(
        self,
        content_type: NSFWContentType,
        content_id: str,
        is_nsfw: bool,
        detection_method: NSFWDetectionMethod,
        confidence: Optional[float] = None,
        labels: Optional[List[Dict]] = None,
        flagged_by: Optional[str] = None
    ) -> Dict:
        """
        Create an NSFW flag for content.
        
        Args:
            content_type: Type of content (STORY, CHAPTER, WHISPER, IMAGE)
            content_id: ID of the content
            is_nsfw: Whether content is flagged as NSFW
            detection_method: How NSFW was detected (AUTOMATIC, MANUAL, USER_MARKED)
            confidence: Confidence score from detection (0-100)
            labels: List of detected labels
            flagged_by: User ID who flagged (for MANUAL/USER_MARKED)
            
        Returns:
            Created NSFWFlag record
        """
        try:
            # Check if flag already exists
            existing_flag = await self.db.nsfwflag.find_first(
                where={
                    'content_type': content_type,
                    'content_id': content_id
                }
            )
            
            if existing_flag:
                # Update existing flag
                logger.info(
                    f"Updating existing NSFW flag for {content_type} {content_id}"
                )
                flag = await self.db.nsfwflag.update(
                    where={'id': existing_flag.id},
                    data={
                        'is_nsfw': is_nsfw,
                        'confidence': confidence,
                        'labels': labels,
                        'detection_method': detection_method,
                        'flagged_by': flagged_by,
                        'reviewed': False  # Reset reviewed status on update
                    }
                )
            else:
                # Create new flag
                logger.info(
                    f"Creating new NSFW flag for {content_type} {content_id}"
                )
                flag = await self.db.nsfwflag.create(
                    data={
                        'content_type': content_type,
                        'content_id': content_id,
                        'is_nsfw': is_nsfw,
                        'confidence': confidence,
                        'labels': labels,
                        'detection_method': detection_method,
                        'flagged_by': flagged_by,
                        'reviewed': False
                    }
                )
            
            return flag.model_dump()
            
        except Exception as e:
            logger.error(f"Error creating NSFW flag: {e}")
            raise
    
    async def get_nsfw_flag(
        self,
        content_type: NSFWContentType,
        content_id: str
    ) -> Optional[Dict]:
        """
        Get NSFW flag for content.
        
        Args:
            content_type: Type of content
            content_id: ID of the content
            
        Returns:
            NSFWFlag record or None if not found
        """
        try:
            flag = await self.db.nsfwflag.find_first(
                where={
                    'content_type': content_type,
                    'content_id': content_id
                }
            )
            return flag.model_dump() if flag else None
            
        except Exception as e:
            logger.error(f"Error getting NSFW flag: {e}")
            return None
    
    async def is_content_nsfw(
        self,
        content_type: NSFWContentType,
        content_id: str
    ) -> bool:
        """
        Check if content is flagged as NSFW.
        
        Args:
            content_type: Type of content
            content_id: ID of the content
            
        Returns:
            True if content is NSFW, False otherwise
        """
        flag = await self.get_nsfw_flag(content_type, content_id)
        return flag['is_nsfw'] if flag else False
    
    async def mark_content_as_nsfw(
        self,
        content_type: NSFWContentType,
        content_id: str,
        user_id: str,
        is_manual: bool = True
    ) -> Dict:
        """
        Manually mark content as NSFW.
        
        Args:
            content_type: Type of content
            content_id: ID of the content
            user_id: ID of user marking content
            is_manual: Whether this is a manual flag (vs user-marked)
            
        Returns:
            Created/updated NSFWFlag record
        """
        detection_method = (
            NSFWDetectionMethod.MANUAL if is_manual 
            else NSFWDetectionMethod.USER_MARKED
        )
        
        return await self.create_nsfw_flag(
            content_type=content_type,
            content_id=content_id,
            is_nsfw=True,
            detection_method=detection_method,
            flagged_by=user_id
        )
    
    async def override_nsfw_flag(
        self,
        content_type: NSFWContentType,
        content_id: str,
        is_nsfw: bool,
        moderator_id: str
    ) -> Dict:
        """
        Override NSFW classification (moderator action).
        
        Args:
            content_type: Type of content
            content_id: ID of the content
            is_nsfw: New NSFW status
            moderator_id: ID of moderator making override
            
        Returns:
            Updated NSFWFlag record
        """
        logger.info(
            f"Moderator {moderator_id} overriding NSFW flag for "
            f"{content_type} {content_id} to {is_nsfw}"
        )
        
        flag = await self.create_nsfw_flag(
            content_type=content_type,
            content_id=content_id,
            is_nsfw=is_nsfw,
            detection_method=NSFWDetectionMethod.MANUAL,
            flagged_by=moderator_id
        )
        
        # Mark as reviewed
        await self.db.nsfwflag.update(
            where={'id': flag['id']},
            data={'reviewed': True}
        )
        
        return flag
    
    async def get_user_nsfw_preference(self, user_id: str) -> NSFWPreference:
        """
        Get user's NSFW content preference.
        
        Args:
            user_id: ID of the user
            
        Returns:
            User's NSFW preference (defaults to BLUR_NSFW)
        """
        try:
            preference = await self.db.contentpreference.find_unique(
                where={'user_id': user_id}
            )
            
            if preference:
                return preference.nsfw_preference
            else:
                # Create default preference
                await self.create_user_nsfw_preference(
                    user_id, NSFWPreference.BLUR_NSFW
                )
                return NSFWPreference.BLUR_NSFW
                
        except Exception as e:
            logger.error(f"Error getting user NSFW preference: {e}")
            return NSFWPreference.BLUR_NSFW
    
    async def create_user_nsfw_preference(
        self,
        user_id: str,
        preference: NSFWPreference
    ) -> Dict:
        """
        Create or update user's NSFW content preference.
        
        Args:
            user_id: ID of the user
            preference: NSFW preference (SHOW_ALL, BLUR_NSFW, HIDE_NSFW)
            
        Returns:
            Created/updated ContentPreference record
        """
        try:
            # Check if preference exists
            existing = await self.db.contentpreference.find_unique(
                where={'user_id': user_id}
            )
            
            if existing:
                # Update existing preference
                pref = await self.db.contentpreference.update(
                    where={'user_id': user_id},
                    data={'nsfw_preference': preference}
                )
            else:
                # Create new preference
                pref = await self.db.contentpreference.create(
                    data={
                        'user_id': user_id,
                        'nsfw_preference': preference
                    }
                )
            
            logger.info(f"Set NSFW preference for user {user_id} to {preference}")
            return pref.model_dump()
            
        except Exception as e:
            logger.error(f"Error creating user NSFW preference: {e}")
            raise
    
    async def get_nsfw_flags_for_review(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """
        Get NSFW flags that need review.
        
        Args:
            limit: Maximum number of flags to return
            offset: Number of flags to skip
            
        Returns:
            List of unreviewed NSFW flags
        """
        try:
            flags = await self.db.nsfwflag.find_many(
                where={'reviewed': False},
                order={'flagged_at': 'desc'},
                take=limit,
                skip=offset
            )
            
            return [flag.model_dump() for flag in flags]
            
        except Exception as e:
            logger.error(f"Error getting NSFW flags for review: {e}")
            return []


# Singleton instance
_nsfw_service_instance: Optional[NSFWService] = None


def get_nsfw_service() -> NSFWService:
    """Get or create the singleton NSFWService instance."""
    global _nsfw_service_instance
    if _nsfw_service_instance is None:
        _nsfw_service_instance = NSFWService()
    return _nsfw_service_instance
