"""
Views for password reset API endpoints.

These views implement the password reset flow:
1. POST /api/forgot-password - Request password reset
2. GET /api/reset-password/:token - Validate token
3. POST /api/reset-password - Complete password reset
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from .serializers import (
    ForgotPasswordRequestSerializer,
    ForgotPasswordResponseSerializer,
    ValidateTokenResponseSerializer,
    ResetPasswordRequestSerializer,
    ResetPasswordResponseSerializer,
    ErrorResponseSerializer,
)
from .error_formatter import ErrorFormatter
from .services.password_reset_service import PasswordResetService
from .services.token_service import TokenService
from .services.rate_limit_service import RateLimitService
from .services.email_service import EmailService
from .services.audit_logger import AuditLogger
from .services.password_validator import PasswordValidator
from .services.session_manager import SessionManager
from .repositories.token_repository import TokenRepository
from .repositories.user_repository import UserRepository


def get_client_ip(request):
    """Extract client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
    return ip


def get_password_reset_service():
    """
    Factory function to create PasswordResetService with all dependencies.
    
    This creates a fully configured service instance with all required dependencies.
    """
    # Create repositories
    token_repository = TokenRepository()
    user_repository = UserRepository()
    
    # Create services
    token_service = TokenService(token_repository)
    rate_limit_service = RateLimitService()
    email_service = EmailService()
    audit_logger = AuditLogger()
    password_validator = PasswordValidator(user_repository)
    session_manager = SessionManager()
    
    # Create and return the main service
    return PasswordResetService(
        token_service=token_service,
        rate_limit_service=rate_limit_service,
        email_service=email_service,
        audit_logger=audit_logger,
        user_repository=user_repository,
        password_validator=password_validator,
        session_manager=session_manager,
    )


@extend_schema(
    tags=['Password Reset'],
    summary='Request password reset',
    description='''
    Initiates a password reset request for the given email address.
    
    **Security Features:**
    - Returns consistent response regardless of whether email exists (prevents email enumeration)
    - Rate limited per user (3 requests/hour) and per IP (10 requests/hour)
    - Generates cryptographically secure token
    - Sends email with reset link
    
    **Requirements:**
    - 1.1: Accept email address
    - 1.2: Generate secure token
    - 1.3: Send reset email
    - 1.4: Prevent email enumeration
    - 1.5: Validate email format
    ''',
    request=ForgotPasswordRequestSerializer,
    responses={
        200: ForgotPasswordResponseSerializer,
        400: ErrorResponseSerializer,
        429: ErrorResponseSerializer,
    },
    examples=[
        OpenApiExample(
            'Request Example',
            value={'email': 'user@example.com'},
            request_only=True,
        ),
        OpenApiExample(
            'Success Response',
            value={
                'success': True,
                'message': 'If an account exists with this email, you will receive a password reset link.'
            },
            response_only=True,
        ),
    ]
)
@api_view(['POST'])
def forgot_password(request):
    """
    POST /api/forgot-password - Request password reset
    
    Requirements:
        - 1.1: Accept email and IP address
        - 1.2: Call PasswordResetService.requestPasswordReset
        - 1.3: Return consistent success response
        - 1.4: Handle errors with appropriate error responses
    """
    # Validate request data
    serializer = ForgotPasswordRequestSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(
            ErrorFormatter.format_validation_error(
                'Invalid input data',
                details=[str(e) for e in serializer.errors.values()]
            ),
            status=status.HTTP_400_BAD_REQUEST
        )
    
    email = serializer.validated_data['email']
    ip_address = get_client_ip(request)
    
    # Get service instance
    service = get_password_reset_service()
    
    # Request password reset (async operation)
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(
            service.request_password_reset(email, ip_address)
        )
        
        # Always return success response (Requirement 1.4)
        return Response(
            {
                'success': True,
                'message': 'If an account exists with this email, you will receive a password reset link.'
            },
            status=status.HTTP_200_OK
        )
    
    except Exception as e:
        # Log error and return generic error response
        return Response(
            ErrorFormatter.format_internal_error(),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    tags=['Password Reset'],
    summary='Validate reset token',
    description='''
    Validates a password reset token from the email link.
    
    **Returns:**
    - Valid token: Returns success with valid=true
    - Invalid/expired token: Returns error with valid=false and reason
    
    **Requirements:**
    - 4.1: Validate token
    - 4.2: Return form display or error
    - 4.3: Handle invalid tokens
    ''',
    responses={
        200: ValidateTokenResponseSerializer,
        400: ErrorResponseSerializer,
    },
    examples=[
        OpenApiExample(
            'Valid Token Response',
            value={
                'valid': True,
                'message': 'Token is valid'
            },
            response_only=True,
        ),
        OpenApiExample(
            'Invalid Token Response',
            value={
                'valid': False,
                'message': 'Token is invalid or expired'
            },
            response_only=True,
        ),
    ]
)
@api_view(['GET'])
def validate_token(request, token):
    """
    GET /api/reset-password/:token - Validate token
    
    Requirements:
        - 4.1: Validate token
        - 4.2: Return form display or error response
    """
    # Get service instance
    service = get_password_reset_service()
    
    # Validate token (async operation)
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        validation_result = loop.run_until_complete(
            service.validate_token(token)
        )
        
        if validation_result.valid:
            return Response(
                {
                    'valid': True,
                    'message': 'Token is valid'
                },
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {
                    'valid': False,
                    'message': validation_result.reason or 'Token is invalid or expired'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    except Exception as e:
        return Response(
            ErrorFormatter.format_internal_error('An error occurred validating the token'),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    tags=['Password Reset'],
    summary='Complete password reset',
    description='''
    Completes the password reset process with a valid token and new password.
    
    **Validation:**
    - Token must be valid and not expired
    - Password must match confirmation
    - Password must meet security requirements:
      - Minimum 8 characters
      - At least one uppercase letter
      - At least one lowercase letter
      - At least one number
      - At least one special character
      - Cannot match previous password
      - Cannot be a common/weak password
    
    **Side Effects:**
    - Updates user password
    - Invalidates all user sessions
    - Sends confirmation email
    
    **Requirements:**
    - 5.1: Validate password requirements
    - 5.2: Update password
    - 5.3: Validate password confirmation
    - 5.4: Invalidate token and sessions
    - 5.5: Send confirmation email
    ''',
    request=ResetPasswordRequestSerializer,
    responses={
        200: ResetPasswordResponseSerializer,
        400: ErrorResponseSerializer,
    },
    examples=[
        OpenApiExample(
            'Request Example',
            value={
                'token': 'abc123def456...',
                'password': 'NewSecure123!',
                'confirm_password': 'NewSecure123!'
            },
            request_only=True,
        ),
        OpenApiExample(
            'Success Response',
            value={
                'success': True,
                'message': 'Password has been reset successfully'
            },
            response_only=True,
        ),
        OpenApiExample(
            'Error Response',
            value={
                'success': False,
                'message': 'Password reset failed',
                'errors': ['Password must contain at least one uppercase letter']
            },
            response_only=True,
        ),
    ]
)
@api_view(['POST'])
def reset_password(request):
    """
    POST /api/reset-password - Complete password reset
    
    Requirements:
        - 5.1: Accept token, password, confirmPassword, and IP address
        - 5.2: Call PasswordResetService.resetPassword
        - 5.3: Return success or error response
    """
    # Validate request data
    serializer = ResetPasswordRequestSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(
            ErrorFormatter.format_validation_error(
                'Invalid input data',
                details=[str(e) for e in serializer.errors.values()]
            ),
            status=status.HTTP_400_BAD_REQUEST
        )
    
    token = serializer.validated_data['token']
    password = serializer.validated_data['password']
    confirm_password = serializer.validated_data['confirm_password']
    ip_address = get_client_ip(request)
    
    # Get service instance
    service = get_password_reset_service()
    
    # Reset password (async operation)
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(
            service.reset_password(token, password, confirm_password, ip_address)
        )
        
        if result.success:
            return Response(
                {
                    'success': True,
                    'message': 'Password has been reset successfully'
                },
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {
                    'success': False,
                    'message': 'Password reset failed',
                    'errors': result.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    except Exception as e:
        return Response(
            ErrorFormatter.format_internal_error('An error occurred resetting the password'),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
