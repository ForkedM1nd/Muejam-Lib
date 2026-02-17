"""Serializers for user profile management."""
import re
from rest_framework import serializers
from prisma import Prisma


class UserProfileReadSerializer(serializers.Serializer):
    """
    Serializer for reading UserProfile data.
    
    Returns all public profile fields including:
    - id, clerk_user_id, handle, display_name, bio, avatar_key, created_at
    
    Requirements:
        - 1.4: Return profile fields when user requests their profile
    """
    id = serializers.CharField(read_only=True)
    clerk_user_id = serializers.CharField(read_only=True)
    handle = serializers.CharField(read_only=True)
    display_name = serializers.CharField(read_only=True)
    bio = serializers.CharField(read_only=True, allow_null=True)
    avatar_key = serializers.CharField(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)


class UserProfileWriteSerializer(serializers.Serializer):
    """
    Serializer for updating UserProfile data.
    
    Allows updating: handle, display_name, bio, avatar_key
    
    Requirements:
        - 1.3: Validate handle uniqueness and update profile fields
        - 1.5: Enforce handle format (alphanumeric + underscore, 3-30 chars)
    """
    handle = serializers.CharField(
        required=False,
        min_length=3,
        max_length=30,
        help_text="Alphanumeric characters and underscores only, 3-30 characters"
    )
    display_name = serializers.CharField(
        required=False,
        max_length=100,
        help_text="Display name for the user"
    )
    bio = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=500,
        help_text="User bio (max 500 characters)"
    )
    avatar_key = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=255,
        help_text="S3 object key for avatar image"
    )
    
    def validate_handle(self, value):
        """
        Validate handle format: alphanumeric + underscore, 3-30 chars.
        
        Requirements:
            - 1.5: Enforce handle format validation
        """
        if not re.match(r'^[a-zA-Z0-9_]{3,30}$', value):
            raise serializers.ValidationError(
                "Handle must contain only alphanumeric characters and underscores, "
                "and be between 3-30 characters long."
            )
        return value
    
    async def validate_handle_uniqueness(self, handle, current_user_id):
        """
        Check if handle is already taken by another user.
        
        Args:
            handle: The handle to check
            current_user_id: The ID of the current user (to exclude from check)
            
        Returns:
            True if handle is available, False otherwise
            
        Requirements:
            - 1.3: Validate handle uniqueness
        """
        db = Prisma()
        await db.connect()
        
        try:
            existing = await db.userprofile.find_unique(
                where={'handle': handle}
            )
            
            # Handle is available if it doesn't exist or belongs to current user
            is_available = existing is None or existing.id == current_user_id
            
            await db.disconnect()
            return is_available
            
        except Exception:
            await db.disconnect()
            return False


class PublicUserProfileSerializer(serializers.Serializer):
    """
    Serializer for public user profile data (accessed via handle).
    
    Returns public profile fields only (excludes clerk_user_id).
    
    Requirements:
        - 1.4: Return public profile when accessed by handle
    """
    id = serializers.CharField(read_only=True)
    handle = serializers.CharField(read_only=True)
    display_name = serializers.CharField(read_only=True)
    bio = serializers.CharField(read_only=True, allow_null=True)
    avatar_key = serializers.CharField(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
