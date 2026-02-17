"""
Serializers for password reset API endpoints.

These serializers handle request/response validation for the password reset flow.
"""
from rest_framework import serializers


class ForgotPasswordRequestSerializer(serializers.Serializer):
    """
    Serializer for POST /api/forgot-password request.
    
    Requirements:
        - 1.1: Accept email address for password reset request
    """
    email = serializers.EmailField(
        required=True,
        help_text="Email address of the account to reset"
    )


class ForgotPasswordResponseSerializer(serializers.Serializer):
    """
    Serializer for POST /api/forgot-password response.
    
    Requirements:
        - 1.4: Return consistent success response
    """
    success = serializers.BooleanField(default=True)
    message = serializers.CharField(
        default="If an account exists with this email, you will receive a password reset link."
    )


class ValidateTokenResponseSerializer(serializers.Serializer):
    """
    Serializer for GET /api/reset-password/:token response.
    
    Requirements:
        - 4.1: Return validation result for token
    """
    valid = serializers.BooleanField()
    message = serializers.CharField(required=False, allow_null=True)


class ResetPasswordRequestSerializer(serializers.Serializer):
    """
    Serializer for POST /api/reset-password request.
    
    Requirements:
        - 5.1: Accept token, password, and confirmation
    """
    token = serializers.CharField(
        required=True,
        help_text="Password reset token from email"
    )
    password = serializers.CharField(
        required=True,
        write_only=True,
        help_text="New password"
    )
    confirm_password = serializers.CharField(
        required=True,
        write_only=True,
        help_text="Password confirmation"
    )


class ResetPasswordResponseSerializer(serializers.Serializer):
    """
    Serializer for POST /api/reset-password response.
    
    Requirements:
        - 5.2: Return success or error response
    """
    success = serializers.BooleanField()
    message = serializers.CharField(required=False, allow_null=True)
    errors = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_null=True
    )


class ErrorResponseSerializer(serializers.Serializer):
    """
    Standard error response format.
    
    Requirements:
        - 3.2: Consistent error response format
    """
    success = serializers.BooleanField(default=False)
    error = serializers.DictField(
        child=serializers.CharField(),
        help_text="Error details including code, message, and optional retry_after"
    )
