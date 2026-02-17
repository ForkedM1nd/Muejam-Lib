"""Serializers for content moderation."""
from rest_framework import serializers


class ReportSerializer(serializers.Serializer):
    """
    Serializer for Report data.
    
    Returns: id, reporter_id, reported content IDs, reason, status, created_at
    
    Requirements:
        - 13.1: Report stories
        - 13.2: Report chapters
        - 13.3: Report whispers
        - 13.4: Report users
    """
    id = serializers.CharField(read_only=True)
    reporter_id = serializers.CharField(read_only=True)
    reported_user_id = serializers.CharField(read_only=True, allow_null=True)
    story_id = serializers.CharField(read_only=True, allow_null=True)
    chapter_id = serializers.CharField(read_only=True, allow_null=True)
    whisper_id = serializers.CharField(read_only=True, allow_null=True)
    reason = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)


class ReportCreateSerializer(serializers.Serializer):
    """
    Serializer for creating a report.
    
    Accepts: content_type, content_id, reason
    
    Requirements:
        - 13.1: Report stories
        - 13.2: Report chapters
        - 13.3: Report whispers
        - 13.4: Report users
        - 13.5: Store report with reason
        - 13.7: Validate reason text (max 500 characters)
    """
    content_type = serializers.ChoiceField(
        choices=['story', 'chapter', 'whisper', 'user'],
        required=True,
        help_text="Type of content being reported"
    )
    content_id = serializers.CharField(
        required=True,
        help_text="ID of the content being reported"
    )
    reason = serializers.CharField(
        required=True,
        max_length=500,
        help_text="Reason for reporting (max 500 characters)"
    )
    
    def validate_reason(self, value):
        """Validate reason is not empty after stripping."""
        if not value.strip():
            raise serializers.ValidationError("Reason cannot be empty.")
        return value.strip()
    
    def validate_content_id(self, value):
        """Validate content_id is not empty."""
        if not value.strip():
            raise serializers.ValidationError("Content ID cannot be empty.")
        return value.strip()
