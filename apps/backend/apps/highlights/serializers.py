"""Serializers for text highlighting system."""
from rest_framework import serializers


class HighlightSerializer(serializers.Serializer):
    """
    Serializer for Highlight data.
    
    Returns: id, user_id, chapter_id, start_offset, end_offset, created_at
    
    Requirements:
        - 8.1: Select text and capture offsets
        - 8.2: Save highlight with offsets
    """
    id = serializers.CharField(read_only=True)
    user_id = serializers.CharField(read_only=True)
    chapter_id = serializers.CharField(read_only=True)
    start_offset = serializers.IntegerField(read_only=True)
    end_offset = serializers.IntegerField(read_only=True)
    quote_text = serializers.CharField(read_only=True, required=False)
    chapter_title = serializers.CharField(read_only=True, required=False)
    story_title = serializers.CharField(read_only=True, required=False)
    story_id = serializers.CharField(read_only=True, required=False)
    created_at = serializers.DateTimeField(read_only=True)


class HighlightCreateSerializer(serializers.Serializer):
    """
    Serializer for creating a highlight.
    
    Accepts: start_offset, end_offset
    
    Requirements:
        - 8.1: Capture start and end offsets
        - 8.7: Validate start_offset < end_offset
        - 8.8: Validate offsets within chapter content length
    """
    start_offset = serializers.IntegerField(
        required=True,
        min_value=0,
        help_text="Starting character offset of the highlight"
    )
    end_offset = serializers.IntegerField(
        required=True,
        min_value=0,
        help_text="Ending character offset of the highlight"
    )
    quote_text = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Optional quoted text for client-side validation"
    )
    
    def validate(self, data):
        """
        Validate that start_offset is less than end_offset.
        
        Requirements:
            - 8.7: Validate start_offset < end_offset
        """
        if data['start_offset'] >= data['end_offset']:
            raise serializers.ValidationError(
                "start_offset must be less than end_offset"
            )
        return data
