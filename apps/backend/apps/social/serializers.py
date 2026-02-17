"""Serializers for social features (follow/block)."""
from rest_framework import serializers


class FollowSerializer(serializers.Serializer):
    """
    Serializer for Follow relationship data.
    
    Returns: id, follower_id, following_id, created_at
    
    Requirements:
        - 11.1: Follow user creates Follow record
        - 11.2: Unfollow user deletes Follow record
    """
    id = serializers.CharField(read_only=True)
    follower_id = serializers.CharField(read_only=True)
    following_id = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)


class FollowerListSerializer(serializers.Serializer):
    """
    Serializer for listing followers (returns user profile info).
    
    Returns: User profile information for each follower
    
    Requirements:
        - 11.1: List followers for a user
    """
    id = serializers.CharField(read_only=True)
    handle = serializers.CharField(read_only=True)
    display_name = serializers.CharField(read_only=True)
    avatar_key = serializers.CharField(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)


class FollowingListSerializer(serializers.Serializer):
    """
    Serializer for listing following (returns user profile info).
    
    Returns: User profile information for each followed user
    
    Requirements:
        - 11.1: List following for a user
    """
    id = serializers.CharField(read_only=True)
    handle = serializers.CharField(read_only=True)
    display_name = serializers.CharField(read_only=True)
    avatar_key = serializers.CharField(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)


class BlockSerializer(serializers.Serializer):
    """
    Serializer for Block relationship data.
    
    Returns: id, blocker_id, blocked_id, created_at
    
    Requirements:
        - 11.3: Block user creates Block record
        - 11.4: Unblock user deletes Block record
    """
    id = serializers.CharField(read_only=True)
    blocker_id = serializers.CharField(read_only=True)
    blocked_id = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
