"""Serializers for story and chapter management."""
import re
from rest_framework import serializers
from prisma import Prisma
from datetime import datetime
from apps.core.deep_link_service import DeepLinkService


def generate_slug(title: str) -> str:
    """
    Generate a URL-friendly slug from a title.
    
    Args:
        title: The story title
        
    Returns:
        A slug suitable for URLs
        
    Requirements:
        - 5.1: Add slug generation from title
    """
    # Convert to lowercase and replace spaces with hyphens
    slug = title.lower().strip()
    # Replace non-alphanumeric characters (except hyphens) with hyphens
    slug = re.sub(r'[^a-z0-9-]+', '-', slug)
    # Remove multiple consecutive hyphens
    slug = re.sub(r'-+', '-', slug)
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    return slug


class StoryListSerializer(serializers.Serializer):
    """
    Serializer for listing stories (minimal fields).
    
    Returns: id, slug, title, blurb, cover_key, author info, published status, timestamps
    
    Requirements:
        - 5.1: List stories with basic information
    """
    id = serializers.CharField(read_only=True)
    slug = serializers.CharField(read_only=True)
    title = serializers.CharField(read_only=True)
    blurb = serializers.CharField(read_only=True)
    cover_key = serializers.CharField(read_only=True, allow_null=True)
    author_id = serializers.CharField(read_only=True)
    published = serializers.BooleanField(read_only=True)
    published_at = serializers.DateTimeField(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class StoryDetailSerializer(serializers.Serializer):
    """
    Serializer for story detail view (all fields including relations).
    
    Returns: All story fields plus author info, tags, chapter count
    
    Requirements:
        - 5.1: Get story by slug with full details
        - 6.1, 6.3: Include deep links for mobile clients
    """
    id = serializers.CharField(read_only=True)
    slug = serializers.CharField(read_only=True)
    title = serializers.CharField(read_only=True)
    blurb = serializers.CharField(read_only=True)
    cover_key = serializers.CharField(read_only=True, allow_null=True)
    author_id = serializers.CharField(read_only=True)
    published = serializers.BooleanField(read_only=True)
    published_at = serializers.DateTimeField(read_only=True, allow_null=True)
    deleted_at = serializers.DateTimeField(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    
    def to_representation(self, instance):
        """Add deep link for mobile clients."""
        data = super().to_representation(instance)
        
        # Add deep link for mobile clients
        request = self.context.get('request')
        if request and hasattr(request, 'client_type'):
            if request.client_type.startswith('mobile'):
                platform = 'ios' if 'ios' in request.client_type else 'android'
                data['deep_link'] = DeepLinkService.generate_story_link(
                    instance.id,
                    platform
                )
        
        return data


class StoryCreateSerializer(serializers.Serializer):
    """
    Serializer for creating a story draft.
    
    Accepts: title, blurb, cover_key (optional), mark_as_nsfw (optional)
    
    Requirements:
        - 5.1: Create story draft with title, blurb, cover_key
        - 8.3: Allow content creators to manually mark their content as NSFW
    """
    title = serializers.CharField(
        required=True,
        max_length=200,
        help_text="Story title (max 200 characters)"
    )
    blurb = serializers.CharField(
        required=True,
        max_length=1000,
        help_text="Story description/blurb (max 1000 characters)"
    )
    cover_key = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=255,
        help_text="S3 object key for cover image"
    )
    mark_as_nsfw = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Mark this story as NSFW (Not Safe For Work)"
    )
    
    def validate_title(self, value):
        """Validate title is not empty after stripping."""
        if not value.strip():
            raise serializers.ValidationError("Title cannot be empty.")
        return value.strip()
    
    def validate_blurb(self, value):
        """Validate blurb is not empty after stripping."""
        if not value.strip():
            raise serializers.ValidationError("Blurb cannot be empty.")
        return value.strip()


class StoryUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating a story draft.
    
    Accepts: title, blurb, cover_key, mark_as_nsfw (all optional)
    
    Requirements:
        - 5.5: Update draft without affecting publication status
        - 8.3: Allow content creators to manually mark their content as NSFW
    """
    title = serializers.CharField(
        required=False,
        max_length=200,
        help_text="Story title (max 200 characters)"
    )
    blurb = serializers.CharField(
        required=False,
        max_length=1000,
        help_text="Story description/blurb (max 1000 characters)"
    )
    cover_key = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=255,
        help_text="S3 object key for cover image"
    )
    mark_as_nsfw = serializers.BooleanField(
        required=False,
        help_text="Mark this story as NSFW (Not Safe For Work)"
    )
    
    def validate_title(self, value):
        """Validate title is not empty after stripping."""
        if value is not None and not value.strip():
            raise serializers.ValidationError("Title cannot be empty.")
        return value.strip() if value else value
    
    def validate_blurb(self, value):
        """Validate blurb is not empty after stripping."""
        if value is not None and not value.strip():
            raise serializers.ValidationError("Blurb cannot be empty.")
        return value.strip() if value else value


class ChapterListSerializer(serializers.Serializer):
    """
    Serializer for listing chapters (minimal fields).
    
    Returns: id, story_id, chapter_number, title, published status, timestamps
    
    Requirements:
        - 5.2: List chapters for a story
    """
    id = serializers.CharField(read_only=True)
    story_id = serializers.CharField(read_only=True)
    chapter_number = serializers.IntegerField(read_only=True)
    title = serializers.CharField(read_only=True)
    published = serializers.BooleanField(read_only=True)
    published_at = serializers.DateTimeField(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class ChapterDetailSerializer(serializers.Serializer):
    """
    Serializer for chapter detail view (includes content).
    
    Returns: All chapter fields including full content
    
    Requirements:
        - 5.2: Get chapter content
        - 6.1, 6.3: Include deep links for mobile clients
    """
    id = serializers.CharField(read_only=True)
    story_id = serializers.CharField(read_only=True)
    chapter_number = serializers.IntegerField(read_only=True)
    title = serializers.CharField(read_only=True)
    content = serializers.CharField(read_only=True)
    published = serializers.BooleanField(read_only=True)
    published_at = serializers.DateTimeField(read_only=True, allow_null=True)
    deleted_at = serializers.DateTimeField(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    
    def to_representation(self, instance):
        """Add deep link for mobile clients."""
        data = super().to_representation(instance)
        
        # Add deep link for mobile clients
        request = self.context.get('request')
        if request and hasattr(request, 'client_type'):
            if request.client_type.startswith('mobile'):
                platform = 'ios' if 'ios' in request.client_type else 'android'
                data['deep_link'] = DeepLinkService.generate_chapter_link(
                    instance.id,
                    platform
                )
        
        return data


class ChapterCreateSerializer(serializers.Serializer):
    """
    Serializer for creating a chapter draft.
    
    Accepts: title, content, chapter_number, mark_as_nsfw (optional)
    
    Requirements:
        - 5.2: Create chapter draft with title, content, chapter_number
        - 8.3: Allow content creators to manually mark their content as NSFW
    """
    title = serializers.CharField(
        required=True,
        max_length=200,
        help_text="Chapter title (max 200 characters)"
    )
    content = serializers.CharField(
        required=True,
        help_text="Chapter content in markdown format"
    )
    chapter_number = serializers.IntegerField(
        required=True,
        min_value=1,
        help_text="Chapter number (must be positive)"
    )
    mark_as_nsfw = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Mark this chapter as NSFW (Not Safe For Work)"
    )
    
    def validate_title(self, value):
        """Validate title is not empty after stripping."""
        if not value.strip():
            raise serializers.ValidationError("Title cannot be empty.")
        return value.strip()
    
    def validate_content(self, value):
        """Validate content is not empty after stripping."""
        if not value.strip():
            raise serializers.ValidationError("Content cannot be empty.")
        return value.strip()


class ChapterUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating a chapter draft.
    
    Accepts: title, content, mark_as_nsfw (all optional)
    
    Requirements:
        - 5.4: Update draft without affecting publication status
        - 8.3: Allow content creators to manually mark their content as NSFW
    """
    title = serializers.CharField(
        required=False,
        max_length=200,
        help_text="Chapter title (max 200 characters)"
    )
    content = serializers.CharField(
        required=False,
        help_text="Chapter content in markdown format"
    )
    mark_as_nsfw = serializers.BooleanField(
        required=False,
        help_text="Mark this chapter as NSFW (Not Safe For Work)"
    )
    
    def validate_title(self, value):
        """Validate title is not empty after stripping."""
        if value is not None and not value.strip():
            raise serializers.ValidationError("Title cannot be empty.")
        return value.strip() if value else value
    
    def validate_content(self, value):
        """Validate content is not empty after stripping."""
        if value is not None and not value.strip():
            raise serializers.ValidationError("Content cannot be empty.")
        return value.strip() if value else value



class ReadingProgressSerializer(serializers.Serializer):
    """
    Serializer for ReadingProgress data.
    
    Returns: id, user_id, chapter_id, offset, updated_at
    
    Requirements:
        - 3.4: Track reading progress as character offset
        - 3.5: Restore last reading progress position
    """
    id = serializers.CharField(read_only=True)
    user_id = serializers.CharField(read_only=True)
    chapter_id = serializers.CharField(read_only=True)
    offset = serializers.IntegerField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class ReadingProgressUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating reading progress.
    
    Accepts: offset
    
    Requirements:
        - 3.4: Update reading progress with character offset
    """
    offset = serializers.IntegerField(
        required=True,
        min_value=0,
        help_text="Character offset in the chapter content"
    )


class BookmarkSerializer(serializers.Serializer):
    """
    Serializer for Bookmark data.
    
    Returns: id, user_id, chapter_id, offset, created_at
    
    Requirements:
        - 3.6: Save bookmark with character offset
    """
    id = serializers.CharField(read_only=True)
    user_id = serializers.CharField(read_only=True)
    chapter_id = serializers.CharField(read_only=True)
    offset = serializers.IntegerField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)


class BookmarkCreateSerializer(serializers.Serializer):
    """
    Serializer for creating a bookmark.
    
    Accepts: offset
    
    Requirements:
        - 3.6: Create bookmark at current position
    """
    offset = serializers.IntegerField(
        required=True,
        min_value=0,
        help_text="Character offset in the chapter content"
    )
