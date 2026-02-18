"""
Views for email verification endpoints.

Requirements: 5.1, 5.2, 5.3
"""
import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.conf import settings
from clerk_backend_api import Clerk

from .service import EmailVerificationService
from .serializers import (
    SendVerificationEmailSerializer,
    VerifyEmailSerializer,
    EmailVerificationStatusSerializer
)

logger = logging.getLogger(__name__)

# Initialize Clerk client
clerk = Clerk(bearer_auth=settings.CLERK_SECRET_KEY)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def send_verification_email(request):
    """
    Send or resend email verification.
    
    POST /api/users/email-verification/send
    
    Request body:
        {
            "email": "user@example.com"
        }
    
    Requirements: 5.2
    """
    serializer = SendVerificationEmailSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(
            {'error': 'Invalid request data', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    email = serializer.validated_data['email']
    user_id = request.user_id  # From authentication middleware
    
    try:
        # Get user from Clerk to verify email matches
        clerk_user = clerk.users.get(user_id)
        
        # Check if email matches user's primary email
        primary_email = None
        for email_obj in clerk_user.email_addresses:
            if email_obj.id == clerk_user.primary_email_address_id:
                primary_email = email_obj.email_address
                break
        
        if primary_email != email:
            return Response(
                {'error': 'Email does not match your account'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create and send verification
        service = EmailVerificationService()
        await service.create_verification(user_id, email)
        
        return Response(
            {
                'message': 'Verification email sent successfully',
                'email': email
            },
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Error sending verification email: {str(e)}")
        return Response(
            {'error': 'Failed to send verification email'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
async def verify_email(request):
    """
    Verify email with token.
    
    POST /api/users/email-verification/verify
    
    Request body:
        {
            "token": "verification_token_here"
        }
    
    Requirements: 5.1
    """
    serializer = VerifyEmailSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(
            {'error': 'Invalid request data', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    token = serializer.validated_data['token']
    
    try:
        service = EmailVerificationService()
        user_id = await service.verify_token(token)
        
        if user_id:
            return Response(
                {
                    'message': 'Email verified successfully',
                    'user_id': user_id
                },
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {'error': 'Invalid or expired verification token'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
    except Exception as e:
        logger.error(f"Error verifying email: {str(e)}")
        return Response(
            {'error': 'Failed to verify email'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
async def check_verification_status(request):
    """
    Check if user's email is verified.
    
    GET /api/users/email-verification/status
    
    Requirements: 5.3
    """
    user_id = request.user_id  # From authentication middleware
    
    try:
        service = EmailVerificationService()
        is_verified = await service.is_email_verified(user_id)
        
        serializer = EmailVerificationStatusSerializer(data={
            'is_verified': is_verified,
            'message': 'Email is verified' if is_verified else 'Email is not verified'
        })
        serializer.is_valid(raise_exception=True)
        
        return Response(
            serializer.validated_data,
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Error checking verification status: {str(e)}")
        return Response(
            {'error': 'Failed to check verification status'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def resend_verification(request):
    """
    Resend verification email.
    
    POST /api/users/email-verification/resend
    
    Request body:
        {
            "email": "user@example.com"
        }
    
    Requirements: 5.2
    """
    serializer = SendVerificationEmailSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(
            {'error': 'Invalid request data', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    email = serializer.validated_data['email']
    user_id = request.user_id  # From authentication middleware
    
    try:
        # Get user from Clerk to verify email matches
        clerk_user = clerk.users.get(user_id)
        
        # Check if email matches user's primary email
        primary_email = None
        for email_obj in clerk_user.email_addresses:
            if email_obj.id == clerk_user.primary_email_address_id:
                primary_email = email_obj.email_address
                break
        
        if primary_email != email:
            return Response(
                {'error': 'Email does not match your account'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Resend verification
        service = EmailVerificationService()
        success = await service.resend_verification(user_id, email)
        
        if success:
            return Response(
                {
                    'message': 'Verification email resent successfully',
                    'email': email
                },
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {'error': 'Email is already verified or failed to resend'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
    except Exception as e:
        logger.error(f"Error resending verification email: {str(e)}")
        return Response(
            {'error': 'Failed to resend verification email'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
