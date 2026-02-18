"""Serializers for discovery endpoints."""
from rest_framework import serializers


class DiscoverFeedQuerySerializer(serializers.Serializer):
    """
    Serializer for discover feed query parameters.
    
    Validates tab, tag, search query, cursor, and page size.
    """
    
    VALID_TABS = ['trending', 'new', 'for-you']
    
    tab = serializers.ChoiceField(
        choices=VALID_TABS,
        default='trending',
        required=False,
        error_messages={
            'invalid_choice': f'Tab must be one of: {", ".join(VALID_TABS)}'
        }
    )
    
    tag = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=100,
        help_text='Filter by tag slug'
    )
    
    q = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=200,
        help_text='Search query'
    )
    
    cursor = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text='Pagination cursor'
    )
    
    page_size = serializers.IntegerField(
        default=20,
        min_value=1,
        max_value=100,
        required=False,
        help_text='Number of results per page'
    )


class GenreQuerySerializer(serializers.Serializer):
    """Serializer for genre-based story queries."""
    
    cursor = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text='Pagination cursor'
    )
    
    page_size = serializers.IntegerField(
        default=20,
        min_value=1,
        max_value=100,
        required=False,
        help_text='Number of results per page'
    )


class SimilarStoriesQuerySerializer(serializers.Serializer):
    """Serializer for similar stories query parameters."""
    
    limit = serializers.IntegerField(
        default=10,
        min_value=1,
        max_value=50,
        required=False,
        help_text='Number of similar stories to return'
    )
