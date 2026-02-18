"""
Serializers for email verification endpoints.
"""
from rest_framework import serializers


class SendVerificationEmailSerializer(serializers.Serializer):
    """Serializer for sending verification email."""
    email = serializers.EmailField(required=True)


class VerifyEmailSerializer(serializers.Serializer):
    """Serializer for verifying email with token."""
    token = serializers.CharField(required=True, min_length=32)


class EmailVerificationStatusSerializer(serializers.Serializer):
    """Serializer for email verification status response."""
    is_verified = serializers.BooleanField()
    message = serializers.CharField()
