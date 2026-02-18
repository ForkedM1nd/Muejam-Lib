"""Tests for story and chapter management."""
import pytest
from django.test import RequestFactory
from apps.stories.serializers import generate_slug


class TestSlugGeneration:
    """Test slug generation from titles."""
    
    def test_basic_slug_generation(self):
        """Test basic slug generation."""
        assert generate_slug("My Story Title") == "my-story-title"
    
    def test_slug_with_special_characters(self):
        """Test slug generation with special characters."""
        assert generate_slug("My Story! Title?") == "my-story-title"
    
    def test_slug_with_multiple_spaces(self):
        """Test slug generation with multiple spaces."""
        assert generate_slug("My   Story   Title") == "my-story-title"
    
    def test_slug_with_leading_trailing_spaces(self):
        """Test slug generation with leading/trailing spaces."""
        assert generate_slug("  My Story Title  ") == "my-story-title"
    
    def test_slug_with_unicode(self):
        """Test slug generation with unicode characters."""
        result = generate_slug("My Café Story")
        # Unicode characters should be replaced with hyphens
        assert "my" in result and "story" in result


class TestMarkdownSanitization:
    """Test markdown sanitization."""
    
    def test_sanitize_removes_script_tags(self):
        """Test that script tags are removed."""
        from apps.stories.views import sanitize_markdown
        
        content = "<p>Hello</p><script>alert('xss')</script>"
        sanitized = sanitize_markdown(content)
        
        # Script tags should be removed (bleach strips tags but may keep text)
        assert "<script>" not in sanitized
        assert "</script>" not in sanitized
        assert "<p>Hello</p>" in sanitized
    
    def test_sanitize_allows_safe_tags(self):
        """Test that safe HTML tags are allowed."""
        from apps.stories.views import sanitize_markdown
        
        content = "<p>Hello <strong>world</strong></p>"
        sanitized = sanitize_markdown(content)
        
        assert "<p>" in sanitized
        assert "<strong>" in sanitized
        assert "Hello" in sanitized
        assert "world" in sanitized
    
    def test_sanitize_removes_javascript_urls(self):
        """Test that javascript: URLs are removed."""
        from apps.stories.views import sanitize_markdown
        
        content = '<a href="javascript:alert(\'xss\')">Click</a>'
        sanitized = sanitize_markdown(content)
        
        assert "javascript:" not in sanitized


# Note: Full integration tests would require database setup and authentication
# These are basic unit tests to verify core functionality



class TestReadingProgress:
    """Test reading progress tracking."""
    
    def test_reading_progress_update_validation(self):
        """Test reading progress update validation."""
        from apps.stories.serializers import ReadingProgressUpdateSerializer
        
        # Valid offset
        serializer = ReadingProgressUpdateSerializer(data={'offset': 100})
        assert serializer.is_valid()
        
        # Negative offset should fail
        serializer = ReadingProgressUpdateSerializer(data={'offset': -1})
        assert not serializer.is_valid()
        assert 'offset' in serializer.errors
        
        # Missing offset should fail
        serializer = ReadingProgressUpdateSerializer(data={})
        assert not serializer.is_valid()
        assert 'offset' in serializer.errors
    
    def test_reading_progress_zero_offset(self):
        """Test that zero offset is valid (start of chapter)."""
        from apps.stories.serializers import ReadingProgressUpdateSerializer
        
        serializer = ReadingProgressUpdateSerializer(data={'offset': 0})
        assert serializer.is_valid()


class TestBookmarks:
    """Test bookmark operations."""
    
    def test_bookmark_create_validation(self):
        """Test bookmark creation validation."""
        from apps.stories.serializers import BookmarkCreateSerializer
        
        # Valid offset
        serializer = BookmarkCreateSerializer(data={'offset': 250})
        assert serializer.is_valid()
        
        # Negative offset should fail
        serializer = BookmarkCreateSerializer(data={'offset': -10})
        assert not serializer.is_valid()
        assert 'offset' in serializer.errors
        
        # Missing offset should fail
        serializer = BookmarkCreateSerializer(data={})
        assert not serializer.is_valid()
        assert 'offset' in serializer.errors
    
    def test_bookmark_zero_offset(self):
        """Test that zero offset is valid for bookmarks."""
        from apps.stories.serializers import BookmarkCreateSerializer
        
        serializer = BookmarkCreateSerializer(data={'offset': 0})
        assert serializer.is_valid()


# Note: Full integration tests would require database setup and authentication
# These are basic unit tests to verify serializer validation
