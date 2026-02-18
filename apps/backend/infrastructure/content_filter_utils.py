"""
Content Filter Utilities for applying shadowban filtering to content queries.

This module provides utilities to filter content from shadowbanned users
across different content types (stories, whispers, etc.).

Requirements: 5.12
"""
import logging
from typing import List, Dict, Any, Optional
from apps.moderation.shadowban import ShadowbanService

logger = logging.getLogger(__name__)


class ContentFilterUtils:
    """
    Utility class for applying shadowban filtering to content.
    
    Provides methods to filter various content types based on shadowban status.
    """
    
    def __init__(self):
        """Initialize content filter utilities."""
        self.shadowban_service = ShadowbanService()
    
    async def filter_whispers(
        self,
        whispers: List[Dict[str, Any]],
        requesting_user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter whispers from shadowbanned users.
        
        Args:
            whispers: List of whisper dictionaries
            requesting_user_id: ID of user requesting content
            
        Returns:
            Filtered whisper list
            
        Requirements: 5.12
        """
        return await self.shadowban_service.filter_shadowbanned_content(
            whispers,
            requesting_user_id
        )
    
    async def filter_stories(
        self,
        stories: List[Dict[str, Any]],
        requesting_user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter stories from shadowbanned authors.
        
        Args:
            stories: List of story dictionaries
            requesting_user_id: ID of user requesting content
            
        Returns:
            Filtered story list
            
        Requirements: 5.12
        """
        return await self.shadowban_service.filter_shadowbanned_content(
            stories,
            requesting_user_id
        )
    
    async def should_show_content(
        self,
        content_user_id: str,
        requesting_user_id: Optional[str] = None
    ) -> bool:
        """
        Check if content from a user should be shown to the requesting user.
        
        Args:
            content_user_id: ID of user who created the content
            requesting_user_id: ID of user requesting to view content
            
        Returns:
            True if content should be shown, False if it should be hidden
            
        Requirements: 5.12
        """
        # Check if content author is shadowbanned
        is_shadowbanned = await self.shadowban_service.is_shadowbanned(content_user_id)
        
        if not is_shadowbanned:
            # Not shadowbanned, show content
            return True
        
        # Content author is shadowbanned
        # Show content if:
        # 1. Requesting user is the shadowbanned user themselves
        if content_user_id == requesting_user_id:
            return True
        
        # 2. Requesting user is a moderator (checked in shadowban service)
        # For now, we'll use the filter method which handles this
        test_content = [{'user_id': content_user_id}]
        filtered = await self.shadowban_service.filter_shadowbanned_content(
            test_content,
            requesting_user_id
        )
        
        return len(filtered) > 0


# Global instance for easy access
content_filter_utils = ContentFilterUtils()
