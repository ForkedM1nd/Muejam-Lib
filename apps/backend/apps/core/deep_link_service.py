"""
Deep Link Service for Mobile Backend Integration

This service generates platform-specific deep links for mobile app navigation.
Supports iOS and Android platforms with custom URL schemes.

Requirements: 6.1, 6.2, 6.3
"""

from urllib.parse import quote as url_quote


def quote(text: str) -> str:
    """URL encode text, including slashes"""
    return url_quote(str(text), safe='')


class DeepLinkService:
    """
    Service for generating deep links for mobile app navigation.
    
    Generates platform-specific URLs that open content in the mobile app.
    Supports stories, chapters, whispers, and user profiles.
    """
    
    # URL scheme configuration
    IOS_SCHEME = 'muejam://'
    ANDROID_SCHEME = 'muejam://'
    WEB_BASE_URL = 'https://muejam.com'
    
    @staticmethod
    def generate_story_link(story_id: str, platform: str = None) -> str:
        """
        Generate deep link to a story.
        
        Args:
            story_id: Story ID
            platform: 'ios', 'android', or None for universal
            
        Returns:
            Deep link URL
            
        Example:
            >>> DeepLinkService.generate_story_link('story123', 'ios')
            'muejam://story/story123'
        """
        if not story_id:
            raise ValueError("story_id cannot be empty")
        
        path = f'story/{quote(str(story_id))}'
        return DeepLinkService._build_deep_link(path, platform)
    
    @staticmethod
    def generate_chapter_link(chapter_id: str, platform: str = None) -> str:
        """
        Generate deep link to a chapter.
        
        Args:
            chapter_id: Chapter ID
            platform: 'ios', 'android', or None for universal
            
        Returns:
            Deep link URL
            
        Example:
            >>> DeepLinkService.generate_chapter_link('chapter456', 'android')
            'muejam://chapter/chapter456'
        """
        if not chapter_id:
            raise ValueError("chapter_id cannot be empty")
        
        path = f'chapter/{quote(str(chapter_id))}'
        return DeepLinkService._build_deep_link(path, platform)
    
    @staticmethod
    def generate_whisper_link(whisper_id: str, platform: str = None) -> str:
        """
        Generate deep link to a whisper.
        
        Args:
            whisper_id: Whisper ID
            platform: 'ios', 'android', or None for universal
            
        Returns:
            Deep link URL
            
        Example:
            >>> DeepLinkService.generate_whisper_link('whisper789', 'ios')
            'muejam://whisper/whisper789'
        """
        if not whisper_id:
            raise ValueError("whisper_id cannot be empty")
        
        path = f'whisper/{quote(str(whisper_id))}'
        return DeepLinkService._build_deep_link(path, platform)
    
    @staticmethod
    def generate_profile_link(user_id: str, platform: str = None) -> str:
        """
        Generate deep link to a user profile.
        
        Args:
            user_id: User ID
            platform: 'ios', 'android', or None for universal
            
        Returns:
            Deep link URL
            
        Example:
            >>> DeepLinkService.generate_profile_link('user123', 'android')
            'muejam://profile/user123'
        """
        if not user_id:
            raise ValueError("user_id cannot be empty")
        
        path = f'profile/{quote(str(user_id))}'
        return DeepLinkService._build_deep_link(path, platform)
    
    @staticmethod
    def _build_deep_link(path: str, platform: str = None) -> str:
        """
        Build deep link URL with appropriate scheme.
        
        Args:
            path: Path component (e.g., 'story/123')
            platform: Target platform ('ios', 'android', or None)
            
        Returns:
            Complete deep link URL
            
        Raises:
            ValueError: If platform is invalid
        """
        if platform is not None and platform not in ['ios', 'android']:
            raise ValueError(f"Invalid platform: {platform}. Must be 'ios' or 'android'")
        
        # Both iOS and Android use the same scheme for this app
        scheme = DeepLinkService.IOS_SCHEME if platform == 'ios' else DeepLinkService.ANDROID_SCHEME
        
        # Ensure path doesn't start with /
        if path.startswith('/'):
            path = path[1:]
        
        return f'{scheme}{path}'
