"""
Unit Tests for Deep Link Service

Tests the deep link generation functionality for mobile app navigation.
"""

import pytest
from apps.core.deep_link_service import DeepLinkService


class TestDeepLinkService:
    """Unit tests for DeepLinkService"""
    
    def test_generate_story_link_ios(self):
        """Test story link generation for iOS platform"""
        link = DeepLinkService.generate_story_link('story123', 'ios')
        assert link == 'muejam://story/story123'
    
    def test_generate_story_link_android(self):
        """Test story link generation for Android platform"""
        link = DeepLinkService.generate_story_link('story456', 'android')
        assert link == 'muejam://story/story456'
    
    def test_generate_story_link_no_platform(self):
        """Test story link generation without platform specification"""
        link = DeepLinkService.generate_story_link('story789')
        assert link == 'muejam://story/story789'
    
    def test_generate_chapter_link_ios(self):
        """Test chapter link generation for iOS platform"""
        link = DeepLinkService.generate_chapter_link('chapter123', 'ios')
        assert link == 'muejam://chapter/chapter123'
    
    def test_generate_chapter_link_android(self):
        """Test chapter link generation for Android platform"""
        link = DeepLinkService.generate_chapter_link('chapter456', 'android')
        assert link == 'muejam://chapter/chapter456'
    
    def test_generate_whisper_link_ios(self):
        """Test whisper link generation for iOS platform"""
        link = DeepLinkService.generate_whisper_link('whisper123', 'ios')
        assert link == 'muejam://whisper/whisper123'
    
    def test_generate_whisper_link_android(self):
        """Test whisper link generation for Android platform"""
        link = DeepLinkService.generate_whisper_link('whisper456', 'android')
        assert link == 'muejam://whisper/whisper456'
    
    def test_generate_profile_link_ios(self):
        """Test profile link generation for iOS platform"""
        link = DeepLinkService.generate_profile_link('user123', 'ios')
        assert link == 'muejam://profile/user123'
    
    def test_generate_profile_link_android(self):
        """Test profile link generation for Android platform"""
        link = DeepLinkService.generate_profile_link('user456', 'android')
        assert link == 'muejam://profile/user456'
    
    def test_url_encoding_special_characters(self):
        """Test that special characters in IDs are properly URL encoded"""
        link = DeepLinkService.generate_story_link('story with spaces')
        assert 'story%20with%20spaces' in link
        
        link = DeepLinkService.generate_chapter_link('chapter/with/slashes')
        assert 'chapter%2Fwith%2Fslashes' in link
    
    def test_empty_story_id_raises_error(self):
        """Test that empty story ID raises ValueError"""
        with pytest.raises(ValueError, match="story_id cannot be empty"):
            DeepLinkService.generate_story_link('')
    
    def test_empty_chapter_id_raises_error(self):
        """Test that empty chapter ID raises ValueError"""
        with pytest.raises(ValueError, match="chapter_id cannot be empty"):
            DeepLinkService.generate_chapter_link('')
    
    def test_empty_whisper_id_raises_error(self):
        """Test that empty whisper ID raises ValueError"""
        with pytest.raises(ValueError, match="whisper_id cannot be empty"):
            DeepLinkService.generate_whisper_link('')
    
    def test_empty_user_id_raises_error(self):
        """Test that empty user ID raises ValueError"""
        with pytest.raises(ValueError, match="user_id cannot be empty"):
            DeepLinkService.generate_profile_link('')
    
    def test_invalid_platform_raises_error(self):
        """Test that invalid platform raises ValueError"""
        with pytest.raises(ValueError, match="Invalid platform"):
            DeepLinkService.generate_story_link('story123', 'windows')
    
    def test_numeric_ids(self):
        """Test that numeric IDs are handled correctly"""
        link = DeepLinkService.generate_story_link('12345', 'ios')
        assert link == 'muejam://story/12345'
    
    def test_uuid_ids(self):
        """Test that UUID-style IDs are handled correctly"""
        uuid = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'
        link = DeepLinkService.generate_story_link(uuid, 'android')
        assert link == f'muejam://story/{uuid}'
    
    def test_deep_link_format_consistency(self):
        """Test that all deep links follow consistent format"""
        story_link = DeepLinkService.generate_story_link('id1', 'ios')
        chapter_link = DeepLinkService.generate_chapter_link('id2', 'ios')
        whisper_link = DeepLinkService.generate_whisper_link('id3', 'ios')
        profile_link = DeepLinkService.generate_profile_link('id4', 'ios')
        
        # All should start with the same scheme
        assert story_link.startswith('muejam://')
        assert chapter_link.startswith('muejam://')
        assert whisper_link.startswith('muejam://')
        assert profile_link.startswith('muejam://')
    
    def test_path_without_leading_slash(self):
        """Test that paths don't have leading slashes"""
        link = DeepLinkService.generate_story_link('story123', 'ios')
        # Should be muejam://story/... not muejam:///story/...
        assert '///' not in link
