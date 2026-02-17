"""Serializers for whispers micro-posting system."""
from rest_framework import serializers


class WhisperSerializer(serializers.Serializer):
    """
    Serializer for Whisper data.
    
    Returns: id, user_id, content, media_key, scope, story_id, highlight_id, 
             parent_id, deleted_at, created_at, reply_count, like_count
    
    Requirements:
        - 6.1: Create whisper with content and scope
        - 7.5: Include reply count and like count
    """
    id = serializers.CharField(read_only=True)
    user_id = serializers.CharField(read_only=True)
    content = serializers.CharField(read_only=True)
    media_key = serializers.CharField(read_only=True, allow_null=True)
    scope = serializers.CharField(read_only=True)
    story_id = serializers.CharField(read_only=True, allow_null=True)
    highlight_id = serializers.CharField(read_only=True, allow_null=True)
    parent_id = serializers.CharField(read_only=True, allow_null=True)
    deleted_at = serializers.DateTimeField(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    # These will be added dynamically in views
    reply_count = serializers.IntegerField(read_only=True, required=False)
    like_count = serializers.IntegerField(read_only=True, required=False)


class WhisperCreateSerializer(serializers.Serializer):
    """
    Serializer for creating a whisper.
    
    Accepts: content, media_key (optional), scope, story_id (optional), highlight_id (optional)
    
    Requirements:
        - 6.1: Create global whisper
        - 6.2: Create story-linked whisper
        - 6.3: Create highlight-linked whisper
    """
    content = serializers.CharField(
        required=True,
        max_length=280,
        help_text="Whisper content (max 280 characters)"
    )
    media_key = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=255,
        help_text="S3 object key for media attachment"
    )
    scope = serializers.ChoiceField(
        required=True,
        choices=['GLOBAL', 'STORY', 'HIGHLIGHT'],
        help_text="Whisper scope (GLOBAL, STORY, or HIGHLIGHT)"
    )
    story_id = serializers.CharField(
        required=False,
        allow_null=True,
        help_text="Story ID (required if scope is STORY)"
    )
    highlight_id = serializers.CharField(
        required=False,
        allow_null=True,
        help_text="Highlight ID (required if scope is HIGHLIGHT)"
    )
    
    def validate_content(self, value):
        """Validate content is not empty after stripping."""
        if not value.strip():
            raise serializers.ValidationError("Content cannot be empty.")
        return value.strip()
    
    def validate(self, data):
        """
        Validate scope-specific requirements.
        
        Requirements:
            - 6.2: STORY scope requires story_id
            - 6.3: HIGHLIGHT scope requires highlight_id
        """
        scope = data.get('scope')
        
        if scope == 'STORY' and not data.get('story_id'):
            raise serializers.ValidationError({
                'story_id': 'story_id is required when scope is STORY'
            })
        
        if scope == 'HIGHLIGHT' and not data.get('highlight_id'):
            raise serializers.ValidationError({
                'highlight_id': 'highlight_id is required when scope is HIGHLIGHT'
            })
        
        return data


class WhisperReplySerializer(serializers.Serializer):
    """
    Serializer for creating a reply to a whisper.
    
    Accepts: content, media_key (optional)
    
    Requirements:
        - 7.1: Create reply with parent_whisper_id
    """
    content = serializers.CharField(
        required=True,
        max_length=280,
        help_text="Reply content (max 280 characters)"
    )
    media_key = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=255,
        help_text="S3 object key for media attachment"
    )
    
    def validate_content(self, value):
        """Validate content is not empty after stripping."""
        if not value.strip():
            raise serializers.ValidationError("Content cannot be empty.")
        return value.strip()


class WhisperLikeSerializer(serializers.Serializer):
    """
    Serializer for WhisperLike data.
    
    Returns: id, user_id, whisper_id, created_at
    
    Requirements:
        - 7.3: Like whisper
    """
    id = serializers.CharField(read_only=True)
    user_id = serializers.CharField(read_only=True)
    whisper_id = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
