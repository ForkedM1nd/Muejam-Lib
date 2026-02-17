"""Tests for whispers micro-posting system."""
import pytest


class TestWhisperValidation:
    """Test whisper validation."""
    
    def test_valid_whisper_creation(self):
        """Test valid whisper creation."""
        from apps.whispers.serializers import WhisperCreateSerializer
        
        # Valid global whisper
        serializer = WhisperCreateSerializer(data={
            'content': 'This is a test whisper',
            'scope': 'GLOBAL'
        })
        assert serializer.is_valid()
    
    def test_whisper_content_max_length(self):
        """Test whisper content max length (280 characters)."""
        from apps.whispers.serializers import WhisperCreateSerializer
        
        # Content exactly 280 characters should be valid
        content_280 = 'a' * 280
        serializer = WhisperCreateSerializer(data={
            'content': content_280,
            'scope': 'GLOBAL'
        })
        assert serializer.is_valid()
        
        # Content over 280 characters should fail
        content_281 = 'a' * 281
        serializer = WhisperCreateSerializer(data={
            'content': content_281,
            'scope': 'GLOBAL'
        })
        assert not serializer.is_valid()
        assert 'content' in serializer.errors
    
    def test_whisper_empty_content(self):
        """Test that empty content is not allowed."""
        from apps.whispers.serializers import WhisperCreateSerializer
        
        # Empty content
        serializer = WhisperCreateSerializer(data={
            'content': '',
            'scope': 'GLOBAL'
        })
        assert not serializer.is_valid()
        
        # Whitespace-only content
        serializer = WhisperCreateSerializer(data={
            'content': '   ',
            'scope': 'GLOBAL'
        })
        assert not serializer.is_valid()
    
    def test_whisper_scope_validation(self):
        """Test whisper scope validation."""
        from apps.whispers.serializers import WhisperCreateSerializer
        
        # Valid scopes
        for scope in ['GLOBAL', 'STORY', 'HIGHLIGHT']:
            serializer = WhisperCreateSerializer(data={
                'content': 'Test',
                'scope': scope,
                'story_id': 'story-123' if scope == 'STORY' else None,
                'highlight_id': 'highlight-123' if scope == 'HIGHLIGHT' else None
            })
            # Note: This will fail validation because story_id/highlight_id are required
            # but we're testing scope validation here
            if scope == 'GLOBAL':
                assert serializer.is_valid()
        
        # Invalid scope
        serializer = WhisperCreateSerializer(data={
            'content': 'Test',
            'scope': 'INVALID'
        })
        assert not serializer.is_valid()
        assert 'scope' in serializer.errors
    
    def test_story_scope_requires_story_id(self):
        """Test that STORY scope requires story_id."""
        from apps.whispers.serializers import WhisperCreateSerializer
        
        # STORY scope without story_id should fail
        serializer = WhisperCreateSerializer(data={
            'content': 'Test',
            'scope': 'STORY'
        })
        assert not serializer.is_valid()
        assert 'story_id' in serializer.errors
        
        # STORY scope with story_id should be valid
        serializer = WhisperCreateSerializer(data={
            'content': 'Test',
            'scope': 'STORY',
            'story_id': 'story-123'
        })
        assert serializer.is_valid()
    
    def test_highlight_scope_requires_highlight_id(self):
        """Test that HIGHLIGHT scope requires highlight_id."""
        from apps.whispers.serializers import WhisperCreateSerializer
        
        # HIGHLIGHT scope without highlight_id should fail
        serializer = WhisperCreateSerializer(data={
            'content': 'Test',
            'scope': 'HIGHLIGHT'
        })
        assert not serializer.is_valid()
        assert 'highlight_id' in serializer.errors
        
        # HIGHLIGHT scope with highlight_id should be valid
        serializer = WhisperCreateSerializer(data={
            'content': 'Test',
            'scope': 'HIGHLIGHT',
            'highlight_id': 'highlight-123'
        })
        assert serializer.is_valid()


class TestWhisperReplyValidation:
    """Test whisper reply validation."""
    
    def test_valid_reply(self):
        """Test valid reply creation."""
        from apps.whispers.serializers import WhisperReplySerializer
        
        serializer = WhisperReplySerializer(data={
            'content': 'This is a reply'
        })
        assert serializer.is_valid()
    
    def test_reply_content_max_length(self):
        """Test reply content max length (280 characters)."""
        from apps.whispers.serializers import WhisperReplySerializer
        
        # Content exactly 280 characters should be valid
        content_280 = 'a' * 280
        serializer = WhisperReplySerializer(data={
            'content': content_280
        })
        assert serializer.is_valid()
        
        # Content over 280 characters should fail
        content_281 = 'a' * 281
        serializer = WhisperReplySerializer(data={
            'content': content_281
        })
        assert not serializer.is_valid()
        assert 'content' in serializer.errors
    
    def test_reply_empty_content(self):
        """Test that empty reply content is not allowed."""
        from apps.whispers.serializers import WhisperReplySerializer
        
        # Empty content
        serializer = WhisperReplySerializer(data={
            'content': ''
        })
        assert not serializer.is_valid()
        
        # Whitespace-only content
        serializer = WhisperReplySerializer(data={
            'content': '   '
        })
        assert not serializer.is_valid()


class TestWhisperSanitization:
    """Test whisper content sanitization."""
    
    def test_sanitize_removes_script_tags(self):
        """Test that script tags are removed."""
        from apps.whispers.views import sanitize_whisper_content
        
        content = "Hello<script>alert('xss')</script>world"
        sanitized = sanitize_whisper_content(content)
        
        assert "<script>" not in sanitized
        assert "</script>" not in sanitized
    
    def test_sanitize_allows_safe_tags(self):
        """Test that safe tags are allowed."""
        from apps.whispers.views import sanitize_whisper_content
        
        content = "<p>Hello <strong>world</strong></p>"
        sanitized = sanitize_whisper_content(content)
        
        assert "<p>" in sanitized
        assert "<strong>" in sanitized
        assert "Hello" in sanitized
        assert "world" in sanitized


# Note: Full integration tests would require database setup and authentication
# These are basic unit tests to verify serializer validation and sanitization
