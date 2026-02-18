"""Service for filtering NSFW content based on user preferences."""
from prisma import Prisma
from prisma.enums import NSFWContentType, NSFWPreference
from typing import List, Dict, Any, Optional
import logging

from apps.moderation.nsfw_service import get_nsfw_service

logger = logging.getLogger(__name__)


class NSFWContentFilter:
    """Service for filtering content based on user NSFW preferences."""
    
    def __init__(self):
        """Initialize the NSFW content filter."""
        self.db = Prisma()
        self.nsfw_service = get_nsfw_service()
    
    async def filter_stories(
        self,
        stories: List[Any],
        user_id: Optional[str] = None
    ) -> List[Any]:
        """
        Filter stories based on user's NSFW preference.
        
        Args:
            stories: List of story objects
            user_id: ID of the user (None for anonymous users)
            
        Returns:
            Filtered list of stories with NSFW flags applied
        """
        if not user_id:
            # Anonymous users default to BLUR_NSFW
            preference = NSFWPreference.BLUR_NSFW
        else:
            preference = await self.nsfw_service.get_user_nsfw_preference(user_id)
        
        # If user wants to see all content, return as-is
        if preference == NSFWPreference.SHOW_ALL:
            return stories
        
        filtered_stories = []
        for story in stories:
            # Check if story is flagged as NSFW
            is_nsfw = await self.nsfw_service.is_content_nsfw(
                NSFWContentType.STORY,
                story.id
            )
            
            if is_nsfw:
                if preference == NSFWPreference.HIDE_NSFW:
                    # Skip NSFW content
                    continue
                elif preference == NSFWPreference.BLUR_NSFW:
                    # Mark for blurring
                    story.is_nsfw = True
                    story.is_blurred = True
            
            filtered_stories.append(story)
        
        return filtered_stories
    
    async def filter_chapters(
        self,
        chapters: List[Any],
        user_id: Optional[str] = None
    ) -> List[Any]:
        """
        Filter chapters based on user's NSFW preference.
        
        Args:
            chapters: List of chapter objects
            user_id: ID of the user (None for anonymous users)
            
        Returns:
            Filtered list of chapters with NSFW flags applied
        """
        if not user_id:
            preference = NSFWPreference.BLUR_NSFW
        else:
            preference = await self.nsfw_service.get_user_nsfw_preference(user_id)
        
        if preference == NSFWPreference.SHOW_ALL:
            return chapters
        
        filtered_chapters = []
        for chapter in chapters:
            is_nsfw = await self.nsfw_service.is_content_nsfw(
                NSFWContentType.CHAPTER,
                chapter.id
            )
            
            if is_nsfw:
                if preference == NSFWPreference.HIDE_NSFW:
                    continue
                elif preference == NSFWPreference.BLUR_NSFW:
                    chapter.is_nsfw = True
                    chapter.is_blurred = True
            
            filtered_chapters.append(chapter)
        
        return filtered_chapters
    
    async def filter_whispers(
        self,
        whispers: List[Any],
        user_id: Optional[str] = None
    ) -> List[Any]:
        """
        Filter whispers based on user's NSFW preference.
        
        Args:
            whispers: List of whisper objects
            user_id: ID of the user (None for anonymous users)
            
        Returns:
            Filtered list of whispers with NSFW flags applied
        """
        if not user_id:
            preference = NSFWPreference.BLUR_NSFW
        else:
            preference = await self.nsfw_service.get_user_nsfw_preference(user_id)
        
        if preference == NSFWPreference.SHOW_ALL:
            return whispers
        
        filtered_whispers = []
        for whisper in whispers:
            is_nsfw = await self.nsfw_service.is_content_nsfw(
                NSFWContentType.WHISPER,
                whisper.id
            )
            
            if is_nsfw:
                if preference == NSFWPreference.HIDE_NSFW:
                    continue
                elif preference == NSFWPreference.BLUR_NSFW:
                    whisper.is_nsfw = True
                    whisper.is_blurred = True
            
            filtered_whispers.append(whisper)
        
        return filtered_whispers
    
    async def filter_content_list(
        self,
        content_list: List[Dict[str, Any]],
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter a mixed list of content based on user's NSFW preference.
        
        This is useful for feeds that contain multiple content types.
        
        Args:
            content_list: List of content dictionaries with 'type' and 'id' keys
            user_id: ID of the user (None for anonymous users)
            
        Returns:
            Filtered list of content with NSFW flags applied
        """
        if not user_id:
            preference = NSFWPreference.BLUR_NSFW
        else:
            preference = await self.nsfw_service.get_user_nsfw_preference(user_id)
        
        if preference == NSFWPreference.SHOW_ALL:
            return content_list
        
        filtered_content = []
        for content in content_list:
            # Determine content type
            content_type_str = content.get('type', '').upper()
            try:
                content_type = NSFWContentType[content_type_str]
            except KeyError:
                # Unknown content type, include it
                filtered_content.append(content)
                continue
            
            # Check if content is NSFW
            is_nsfw = await self.nsfw_service.is_content_nsfw(
                content_type,
                content['id']
            )
            
            if is_nsfw:
                if preference == NSFWPreference.HIDE_NSFW:
                    continue
                elif preference == NSFWPreference.BLUR_NSFW:
                    content['is_nsfw'] = True
                    content['is_blurred'] = True
            
            filtered_content.append(content)
        
        return filtered_content
    
    async def should_blur_image(
        self,
        image_id: str,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Check if an image should be blurred for the user.
        
        Args:
            image_id: ID of the image
            user_id: ID of the user (None for anonymous users)
            
        Returns:
            True if image should be blurred, False otherwise
        """
        # Check if image is NSFW
        is_nsfw = await self.nsfw_service.is_content_nsfw(
            NSFWContentType.IMAGE,
            image_id
        )
        
        if not is_nsfw:
            return False
        
        # Get user preference
        if not user_id:
            preference = NSFWPreference.BLUR_NSFW
        else:
            preference = await self.nsfw_service.get_user_nsfw_preference(user_id)
        
        # Blur if preference is BLUR_NSFW or HIDE_NSFW
        return preference in [NSFWPreference.BLUR_NSFW, NSFWPreference.HIDE_NSFW]
    
    async def should_hide_content(
        self,
        content_type: NSFWContentType,
        content_id: str,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Check if content should be completely hidden from the user.
        
        Args:
            content_type: Type of content
            content_id: ID of the content
            user_id: ID of the user (None for anonymous users)
            
        Returns:
            True if content should be hidden, False otherwise
        """
        # Check if content is NSFW
        is_nsfw = await self.nsfw_service.is_content_nsfw(
            content_type,
            content_id
        )
        
        if not is_nsfw:
            return False
        
        # Get user preference
        if not user_id:
            preference = NSFWPreference.BLUR_NSFW
        else:
            preference = await self.nsfw_service.get_user_nsfw_preference(user_id)
        
        # Hide only if preference is HIDE_NSFW
        return preference == NSFWPreference.HIDE_NSFW
    
    async def add_nsfw_metadata(
        self,
        content: Any,
        content_type: NSFWContentType
    ) -> Any:
        """
        Add NSFW metadata to a content object.
        
        This adds is_nsfw flag and nsfw_labels to the content object.
        
        Args:
            content: Content object
            content_type: Type of content
            
        Returns:
            Content object with NSFW metadata added
        """
        nsfw_flag = await self.nsfw_service.get_nsfw_flag(
            content_type,
            content.id
        )
        
        if nsfw_flag:
            content.is_nsfw = nsfw_flag['is_nsfw']
            content.nsfw_confidence = nsfw_flag.get('confidence')
            content.nsfw_labels = nsfw_flag.get('labels', [])
            content.nsfw_detection_method = nsfw_flag.get('detection_method')
        else:
            content.is_nsfw = False
            content.nsfw_confidence = None
            content.nsfw_labels = []
            content.nsfw_detection_method = None
        
        return content


# Singleton instance
_nsfw_content_filter_instance: Optional[NSFWContentFilter] = None


def get_nsfw_content_filter() -> NSFWContentFilter:
    """Get or create the singleton NSFWContentFilter instance."""
    global _nsfw_content_filter_instance
    if _nsfw_content_filter_instance is None:
        _nsfw_content_filter_instance = NSFWContentFilter()
    return _nsfw_content_filter_instance
