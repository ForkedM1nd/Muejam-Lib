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


class DeviceTokenRegisterSerializer(serializers.Serializer):
    """
    Serializer for device token registration.
    
    Requirements:
        - 4.1: Register device token for push notifications
    """
    token = serializers.CharField(required=True, min_length=1, max_length=512)
    platform = serializers.ChoiceField(choices=['ios', 'android'], required=True)
    app_version = serializers.CharField(required=False, allow_null=True, max_length=50)


class DeviceTokenResponseSerializer(serializers.Serializer):
    """
    Serializer for device token response data.
    
    Requirements:
        - 4.2: Return device token information
    """
    id = serializers.CharField(read_only=True)
    user_id = serializers.CharField(read_only=True)
    platform = serializers.CharField(read_only=True)
    app_version = serializers.CharField(read_only=True, allow_null=True)
    is_active = serializers.BooleanField(read_only=True)
    created_at = serializers.CharField(read_only=True)
    last_used_at = serializers.CharField(read_only=True)


class DeviceTokenUnregisterSerializer(serializers.Serializer):
    """
    Serializer for device token unregistration.
    
    Requirements:
        - 4.4: Unregister device token
    """
    token = serializers.CharField(required=True, min_length=1, max_length=512)


class DevicePreferencesSerializer(serializers.Serializer):
    """
    Serializer for device notification preferences.
    
    Requirements:
        - 4.3: Update notification preferences per device
    """
    token = serializers.CharField(required=True, min_length=1, max_length=512)
    enabled = serializers.BooleanField(required=False)
    notification_types = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True
    )
