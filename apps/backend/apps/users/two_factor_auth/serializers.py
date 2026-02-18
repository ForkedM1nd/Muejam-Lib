"""
Serializers for Two-Factor Authentication API endpoints.

Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.7, 7.8
"""
from rest_framework import serializers


class Setup2FAResponseSerializer(serializers.Serializer):
    """Response serializer for 2FA setup initialization."""
    secret = serializers.CharField(
        help_text="TOTP secret key (for manual entry)"
    )
    qr_code = serializers.CharField(
        help_text="Base64-encoded QR code image"
    )
    backup_codes = serializers.ListField(
        child=serializers.CharField(),
        help_text="List of backup codes (display once)"
    )
    message = serializers.CharField(
        help_text="Success message"
    )


class VerifySetup2FASerializer(serializers.Serializer):
    """Request serializer for verifying 2FA setup."""
    token = serializers.CharField(
        required=True,
        min_length=6,
        max_length=6,
        help_text="6-digit TOTP code from authenticator app"
    )


class VerifySetup2FAResponseSerializer(serializers.Serializer):
    """Response serializer for 2FA setup verification."""
    message = serializers.CharField()
    enabled = serializers.BooleanField()


class Verify2FASerializer(serializers.Serializer):
    """Request serializer for verifying 2FA during login."""
    token = serializers.CharField(
        required=True,
        min_length=6,
        max_length=6,
        help_text="6-digit TOTP code from authenticator app"
    )


class Verify2FAResponseSerializer(serializers.Serializer):
    """Response serializer for 2FA verification."""
    message = serializers.CharField()
    verified = serializers.BooleanField()


class VerifyBackupCodeSerializer(serializers.Serializer):
    """Request serializer for verifying backup code."""
    code = serializers.CharField(
        required=True,
        min_length=8,
        max_length=8,
        help_text="8-character backup code"
    )


class VerifyBackupCodeResponseSerializer(serializers.Serializer):
    """Response serializer for backup code verification."""
    message = serializers.CharField()
    verified = serializers.BooleanField()
    remaining_codes = serializers.IntegerField(
        help_text="Number of remaining backup codes"
    )


class Disable2FAResponseSerializer(serializers.Serializer):
    """Response serializer for disabling 2FA."""
    message = serializers.CharField()
    disabled = serializers.BooleanField()


class RegenerateBackupCodesResponseSerializer(serializers.Serializer):
    """Response serializer for regenerating backup codes."""
    message = serializers.CharField()
    backup_codes = serializers.ListField(
        child=serializers.CharField(),
        help_text="List of new backup codes (display once)"
    )
