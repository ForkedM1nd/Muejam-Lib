"""
Unit tests for deep link integration in serializers.

Tests that serializers correctly add deep links for mobile clients
and omit them for web clients.

Requirements: 6.1, 6.3
"""
import pytest
from unittest.mock import Mock
from apps.stories.serializers import StoryDetailSerializer, ChapterDetailSerializer
from apps.whispers.serializers import WhisperSerializer
from apps.users.serializers import UserProfileReadSerializer, PublicUserProfileSerializer


class TestStorySerializerDeepLinks:
    """Test deep link integration in StoryDetailSerializer."""
    
    def test_story_includes_deep_link_for_mobile_ios(self):
        """Story serializer should include deep link for mobile-ios clients."""
        # Create mock story instance
        story = Mock()
        story.id = 'story123'
        story.slug = 'test-story'
        story.title = 'Test Story'
        story.blurb = 'Test blurb'
        story.cover_key = None
        story.author_id = 'author123'
        story.published = True
        story.published_at = None
        story.deleted_at = None
        story.created_at = None
        story.updated_at = None
        
        # Create mock request with mobile-ios client type
        request = Mock()
        request.client_type = 'mobile-ios'
        
        # Serialize with request context
        serializer = StoryDetailSerializer(story, context={'request': request})
        data = serializer.data
        
        # Verify deep link is present and correct
        assert 'deep_link' in data
        assert data['deep_link'] == 'muejam://story/story123'
    
    def test_story_includes_deep_link_for_mobile_android(self):
        """Story serializer should include deep link for mobile-android clients."""
        story = Mock()
        story.id = 'story456'
        story.slug = 'another-story'
        story.title = 'Another Story'
        story.blurb = 'Another blurb'
        story.cover_key = None
        story.author_id = 'author456'
        story.published = True
        story.published_at = None
        story.deleted_at = None
        story.created_at = None
        story.updated_at = None
        
        request = Mock()
        request.client_type = 'mobile-android'
        
        serializer = StoryDetailSerializer(story, context={'request': request})
        data = serializer.data
        
        assert 'deep_link' in data
        assert data['deep_link'] == 'muejam://story/story456'
    
    def test_story_no_deep_link_for_web_client(self):
        """Story serializer should NOT include deep link for web clients."""
        story = Mock()
        story.id = 'story789'
        story.slug = 'web-story'
        story.title = 'Web Story'
        story.blurb = 'Web blurb'
        story.cover_key = None
        story.author_id = 'author789'
        story.published = True
        story.published_at = None
        story.deleted_at = None
        story.created_at = None
        story.updated_at = None
        
        request = Mock()
        request.client_type = 'web'
        
        serializer = StoryDetailSerializer(story, context={'request': request})
        data = serializer.data
        
        assert 'deep_link' not in data
    
    def test_story_no_deep_link_without_request(self):
        """Story serializer should NOT include deep link without request context."""
        story = Mock()
        story.id = 'story999'
        story.slug = 'no-request-story'
        story.title = 'No Request Story'
        story.blurb = 'No request blurb'
        story.cover_key = None
        story.author_id = 'author999'
        story.published = True
        story.published_at = None
        story.deleted_at = None
        story.created_at = None
        story.updated_at = None
        
        serializer = StoryDetailSerializer(story)
        data = serializer.data
        
        assert 'deep_link' not in data


class TestChapterSerializerDeepLinks:
    """Test deep link integration in ChapterDetailSerializer."""
    
    def test_chapter_includes_deep_link_for_mobile_ios(self):
        """Chapter serializer should include deep link for mobile-ios clients."""
        chapter = Mock()
        chapter.id = 'chapter123'
        chapter.story_id = 'story123'
        chapter.chapter_number = 1
        chapter.title = 'Chapter 1'
        chapter.content = 'Chapter content'
        chapter.published = True
        chapter.published_at = None
        chapter.deleted_at = None
        chapter.created_at = None
        chapter.updated_at = None
        
        request = Mock()
        request.client_type = 'mobile-ios'
        
        serializer = ChapterDetailSerializer(chapter, context={'request': request})
        data = serializer.data
        
        assert 'deep_link' in data
        assert data['deep_link'] == 'muejam://chapter/chapter123'
    
    def test_chapter_includes_deep_link_for_mobile_android(self):
        """Chapter serializer should include deep link for mobile-android clients."""
        chapter = Mock()
        chapter.id = 'chapter456'
        chapter.story_id = 'story456'
        chapter.chapter_number = 2
        chapter.title = 'Chapter 2'
        chapter.content = 'More content'
        chapter.published = True
        chapter.published_at = None
        chapter.deleted_at = None
        chapter.created_at = None
        chapter.updated_at = None
        
        request = Mock()
        request.client_type = 'mobile-android'
        
        serializer = ChapterDetailSerializer(chapter, context={'request': request})
        data = serializer.data
        
        assert 'deep_link' in data
        assert data['deep_link'] == 'muejam://chapter/chapter456'
    
    def test_chapter_no_deep_link_for_web_client(self):
        """Chapter serializer should NOT include deep link for web clients."""
        chapter = Mock()
        chapter.id = 'chapter789'
        chapter.story_id = 'story789'
        chapter.chapter_number = 3
        chapter.title = 'Chapter 3'
        chapter.content = 'Web content'
        chapter.published = True
        chapter.published_at = None
        chapter.deleted_at = None
        chapter.created_at = None
        chapter.updated_at = None
        
        request = Mock()
        request.client_type = 'web'
        
        serializer = ChapterDetailSerializer(chapter, context={'request': request})
        data = serializer.data
        
        assert 'deep_link' not in data


class TestWhisperSerializerDeepLinks:
    """Test deep link integration in WhisperSerializer."""
    
    def test_whisper_includes_deep_link_for_mobile_ios(self):
        """Whisper serializer should include deep link for mobile-ios clients."""
        whisper = Mock()
        whisper.id = 'whisper123'
        whisper.user_id = 'user123'
        whisper.content = 'Test whisper'
        whisper.media_key = None
        whisper.scope = 'GLOBAL'
        whisper.story_id = None
        whisper.highlight_id = None
        whisper.parent_id = None
        whisper.deleted_at = None
        whisper.created_at = None
        whisper.reply_count = 0
        whisper.like_count = 0
        
        request = Mock()
        request.client_type = 'mobile-ios'
        
        serializer = WhisperSerializer(whisper, context={'request': request})
        data = serializer.data
        
        assert 'deep_link' in data
        assert data['deep_link'] == 'muejam://whisper/whisper123'
    
    def test_whisper_includes_deep_link_for_mobile_android(self):
        """Whisper serializer should include deep link for mobile-android clients."""
        whisper = Mock()
        whisper.id = 'whisper456'
        whisper.user_id = 'user456'
        whisper.content = 'Another whisper'
        whisper.media_key = None
        whisper.scope = 'STORY'
        whisper.story_id = 'story123'
        whisper.highlight_id = None
        whisper.parent_id = None
        whisper.deleted_at = None
        whisper.created_at = None
        whisper.reply_count = 5
        whisper.like_count = 10
        
        request = Mock()
        request.client_type = 'mobile-android'
        
        serializer = WhisperSerializer(whisper, context={'request': request})
        data = serializer.data
        
        assert 'deep_link' in data
        assert data['deep_link'] == 'muejam://whisper/whisper456'
    
    def test_whisper_no_deep_link_for_web_client(self):
        """Whisper serializer should NOT include deep link for web clients."""
        whisper = Mock()
        whisper.id = 'whisper789'
        whisper.user_id = 'user789'
        whisper.content = 'Web whisper'
        whisper.media_key = None
        whisper.scope = 'GLOBAL'
        whisper.story_id = None
        whisper.highlight_id = None
        whisper.parent_id = None
        whisper.deleted_at = None
        whisper.created_at = None
        whisper.reply_count = 2
        whisper.like_count = 3
        
        request = Mock()
        request.client_type = 'web'
        
        serializer = WhisperSerializer(whisper, context={'request': request})
        data = serializer.data
        
        assert 'deep_link' not in data


class TestUserProfileSerializerDeepLinks:
    """Test deep link integration in UserProfile serializers."""
    
    def test_user_profile_includes_deep_link_for_mobile_ios(self):
        """UserProfileReadSerializer should include deep link for mobile-ios clients."""
        profile = Mock()
        profile.id = 'user123'
        profile.clerk_user_id = 'clerk123'
        profile.handle = 'testuser'
        profile.display_name = 'Test User'
        profile.bio = 'Test bio'
        profile.avatar_key = None
        profile.age_verified = True
        profile.age_verified_at = None
        profile.created_at = None
        profile.banner_key = None
        profile.theme_color = None
        profile.twitter_url = None
        profile.instagram_url = None
        profile.website_url = None
        profile.pinned_story_1 = None
        profile.pinned_story_2 = None
        profile.pinned_story_3 = None
        
        request = Mock()
        request.client_type = 'mobile-ios'
        
        serializer = UserProfileReadSerializer(profile, context={'request': request})
        data = serializer.data
        
        assert 'deep_link' in data
        assert data['deep_link'] == 'muejam://profile/user123'
    
    def test_public_profile_includes_deep_link_for_mobile_android(self):
        """PublicUserProfileSerializer should include deep link for mobile-android clients."""
        profile = Mock()
        profile.id = 'user456'
        profile.handle = 'publicuser'
        profile.display_name = 'Public User'
        profile.bio = 'Public bio'
        profile.avatar_key = None
        profile.created_at = None
        profile.banner_key = None
        profile.theme_color = None
        profile.twitter_url = None
        profile.instagram_url = None
        profile.website_url = None
        profile.pinned_story_1 = None
        profile.pinned_story_2 = None
        profile.pinned_story_3 = None
        
        request = Mock()
        request.client_type = 'mobile-android'
        
        serializer = PublicUserProfileSerializer(profile, context={'request': request})
        data = serializer.data
        
        assert 'deep_link' in data
        assert data['deep_link'] == 'muejam://profile/user456'
    
    def test_user_profile_no_deep_link_for_web_client(self):
        """UserProfileReadSerializer should NOT include deep link for web clients."""
        profile = Mock()
        profile.id = 'user789'
        profile.clerk_user_id = 'clerk789'
        profile.handle = 'webuser'
        profile.display_name = 'Web User'
        profile.bio = 'Web bio'
        profile.avatar_key = None
        profile.age_verified = True
        profile.age_verified_at = None
        profile.created_at = None
        profile.banner_key = None
        profile.theme_color = None
        profile.twitter_url = None
        profile.instagram_url = None
        profile.website_url = None
        profile.pinned_story_1 = None
        profile.pinned_story_2 = None
        profile.pinned_story_3 = None
        
        request = Mock()
        request.client_type = 'web'
        
        serializer = UserProfileReadSerializer(profile, context={'request': request})
        data = serializer.data
        
        assert 'deep_link' not in data
