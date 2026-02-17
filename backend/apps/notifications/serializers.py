"""Serializers for notification system."""
from rest_framework import serializers


class NotificationSerializer(serializers.Serializer):
    """
    Serializer for Notification data.
    
    Returns: id, user_id, type, actor_id, whisper_id, read_at, created_at
    
    Requirements:
        - 12.1: Create notification on reply
        - 12.2: Create notification on follow
        - 12.3: List notifications
    """
    id = serializers.CharField(read_only=True)
    user_id = serializers.CharField(read_only=True)
    type = serializers.CharField(read_only=True)
    actor_id = serializers.CharField(read_only=True)
    whisper_id = serializers.CharField(read_only=True, allow_null=True)
    read_at = serializers.DateTimeField(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
