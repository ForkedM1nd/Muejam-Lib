"""Serializers for library and shelf management."""
from rest_framework import serializers


class ShelfSerializer(serializers.Serializer):
    """
    Serializer for Shelf data.
    
    Returns: id, user_id, name, created_at, updated_at
    
    Requirements:
        - 4.1: Create and manage shelves
    """
    id = serializers.CharField(read_only=True)
    user_id = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class ShelfCreateSerializer(serializers.Serializer):
    """
    Serializer for creating a shelf.
    
    Accepts: name
    
    Requirements:
        - 4.1: Create shelf with name
    """
    name = serializers.CharField(
        required=True,
        max_length=100,
        help_text="Shelf name (max 100 characters)"
    )
    
    def validate_name(self, value):
        """Validate name is not empty after stripping."""
        if not value.strip():
            raise serializers.ValidationError("Shelf name cannot be empty.")
        return value.strip()


class ShelfUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating a shelf (rename).
    
    Accepts: name
    
    Requirements:
        - 4.7: Rename shelf
    """
    name = serializers.CharField(
        required=True,
        max_length=100,
        help_text="New shelf name (max 100 characters)"
    )
    
    def validate_name(self, value):
        """Validate name is not empty after stripping."""
        if not value.strip():
            raise serializers.ValidationError("Shelf name cannot be empty.")
        return value.strip()


class ShelfItemSerializer(serializers.Serializer):
    """
    Serializer for ShelfItem data.
    
    Returns: id, shelf_id, story_id, added_at
    
    Requirements:
        - 4.2: Add story to shelf
    """
    id = serializers.CharField(read_only=True)
    shelf_id = serializers.CharField(read_only=True)
    story_id = serializers.CharField(read_only=True)
    added_at = serializers.DateTimeField(read_only=True)


class ShelfItemCreateSerializer(serializers.Serializer):
    """
    Serializer for adding a story to a shelf.
    
    Accepts: story_id
    
    Requirements:
        - 4.2: Add story to shelf
    """
    story_id = serializers.CharField(
        required=True,
        help_text="ID of the story to add to shelf"
    )


class ShelfWithStoriesSerializer(serializers.Serializer):
    """
    Serializer for shelf with associated stories.
    
    Returns: Shelf data with list of stories
    
    Requirements:
        - 4.4: Get all shelves with stories
    """
    id = serializers.CharField(read_only=True)
    user_id = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    story_count = serializers.IntegerField(read_only=True)
    # stories will be added dynamically in the view
