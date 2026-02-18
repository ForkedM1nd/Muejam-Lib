"""
Views for Two-Factor Authentication API endpoints.

Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.7, 7.8
"""
import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
from clerk_backend_api import Clerk

from .service import TwoFactorAuthService
from .email_service import TwoFactorEmailService
from .serializers import (
    Setup2FAResponseSerializer,
    VerifySetup2FASerializer,
    VerifySetup2FAResponseSerializer,
    Verify2FASerializer,
    Verify2FAResponseSerializer,
    VerifyBackupCodeSerializer,
    VerifyBackupCodeResponseSerializer,
    Disable2FAResponseSerializer,
    RegenerateBackupCodesResponseSerializer,
)

logger = logging.getLogger(__name__)

# Initialize Clerk client
clerk = Clerk(bearer_auth=settings.CLERK_SECRET_KEY)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def setup_2fa(request):
    """
    Initialize 2FA setup for the authenticated user.
    
    POST /api/auth/2fa/setup
    
    Returns:
        {
            "secret": "TOTP secret key",
            "qr_code": "base64-encoded QR code image",
            "backup_codes": ["code1", "code2", ...],
            "message": "2FA setup initialized"
        }
    
    Requirements: 7.1, 7.2
    """
    user_id = request.clerk_user_id  # From authentication middleware
    
    try:
        # Get user email from Clerk
        clerk_user = clerk.users.get(user_id)
        
        # Get primary email
        user_email = None
        for email_obj in clerk_user.email_addresses:
            if email_obj.id == clerk_user.primary_email_address_id:
                user_email = email_obj.email_address
                break
        
        if not user_email:
            return Response(
                {'error': 'User email not found'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if 2FA is already enabled
        service = TwoFactorAuthService()
        if await service.has_2fa_enabled(user_id):
            return Response(
                {'error': '2FA is already enabled for this account'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Setup 2FA
        result = await service.setup_2fa(user_id, user_email)
        
        # Add success message
        result['message'] = '2FA setup initialized. Please scan the QR code with your authenticator app and verify with a code.'
        
        # Validate response
        serializer = Setup2FAResponseSerializer(data=result)
        serializer.is_valid(raise_exception=True)
        
        logger.info(f"2FA setup initialized for user {user_id}")
        
        return Response(
            serializer.validated_data,
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Error setting up 2FA for user {user_id}: {str(e)}")
        return Response(
            {'error': 'Failed to initialize 2FA setup'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def verify_setup_2fa(request):
    """
    Verify and confirm 2FA setup with a TOTP code.
    
    POST /api/auth/2fa/verify-setup
    
    Request body:
        {
            "token": "123456"
        }
    
    Returns:
        {
            "message": "2FA enabled successfully",
            "enabled": true
        }
    
    Requirements: 7.3, 7.9
    """
    user_id = request.clerk_user_id  # From authentication middleware
    
    serializer = VerifySetup2FASerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(
            {'error': 'Invalid request data', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    token = serializer.validated_data['token']
    
    try:
        service = TwoFactorAuthService()
        
        # Verify the setup token
        verified = await service.verify_2fa_setup(user_id, token)
        
        if verified:
            # Get user email from Clerk for notification
            try:
                clerk_user = clerk.users.get(user_id)
                user_email = None
                for email_obj in clerk_user.email_addresses:
                    if email_obj.id == clerk_user.primary_email_address_id:
                        user_email = email_obj.email_address
                        break
                
                # Send email notification (Requirement 7.9)
                if user_email:
                    email_service = TwoFactorEmailService()
                    await email_service.send_2fa_enabled_notification(user_email)
            except Exception as e:
                logger.error(f"Failed to send 2FA enabled notification: {str(e)}")
                # Don't fail the request if email fails
            
            response_data = {
                'message': '2FA enabled successfully',
                'enabled': True
            }
            
            response_serializer = VerifySetup2FAResponseSerializer(data=response_data)
            response_serializer.is_valid(raise_exception=True)
            
            logger.info(f"2FA enabled for user {user_id}")
            
            return Response(
                response_serializer.validated_data,
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {'error': 'Invalid verification code'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
    except Exception as e:
        logger.error(f"Error verifying 2FA setup for user {user_id}: {str(e)}")
        return Response(
            {'error': 'Failed to verify 2FA setup'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def verify_2fa(request):
    """
    Verify 2FA TOTP code during login.
    
    POST /api/auth/2fa/verify
    
    Request body:
        {
            "token": "123456"
        }
    
    Returns:
        {
            "message": "2FA verification successful",
            "verified": true
        }
    
    Requirements: 7.4
    """
    user_id = request.clerk_user_id  # From authentication middleware
    
    serializer = Verify2FASerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(
            {'error': 'Invalid request data', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    token = serializer.validated_data['token']
    
    try:
        service = TwoFactorAuthService()
        
        # Check if 2FA is enabled
        if not await service.has_2fa_enabled(user_id):
            return Response(
                {'error': '2FA is not enabled for this account'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify the TOTP token
        verified = await service.verify_totp(user_id, token)
        
        if verified:
            # Set session flag to indicate 2FA is verified (Requirement 7.4)
            request.session['2fa_verified'] = True
            request.session['2fa_user_id'] = user_id
            request.session.save()
            
            response_data = {
                'message': '2FA verification successful',
                'verified': True
            }
            
            response_serializer = Verify2FAResponseSerializer(data=response_data)
            response_serializer.is_valid(raise_exception=True)
            
            logger.info(f"2FA verification successful for user {user_id}")
            
            return Response(
                response_serializer.validated_data,
                status=status.HTTP_200_OK
            )
        else:
            logger.warning(f"Invalid 2FA token for user {user_id}")
            return Response(
                {'error': 'Invalid verification code'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
    except Exception as e:
        logger.error(f"Error verifying 2FA for user {user_id}: {str(e)}")
        return Response(
            {'error': 'Failed to verify 2FA code'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def verify_backup_code(request):
    """
    Verify a backup code for 2FA.
    
    POST /api/auth/2fa/backup-code
    
    Request body:
        {
            "code": "ABCD1234"
        }
    
    Returns:
        {
            "message": "Backup code verified successfully",
            "verified": true,
            "remaining_codes": 9
        }
    
    Requirements: 7.5
    """
    user_id = request.clerk_user_id  # From authentication middleware
    
    serializer = VerifyBackupCodeSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(
            {'error': 'Invalid request data', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    code = serializer.validated_data['code']
    
    try:
        service = TwoFactorAuthService()
        
        # Check if 2FA is enabled
        if not await service.has_2fa_enabled(user_id):
            return Response(
                {'error': '2FA is not enabled for this account'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify the backup code
        verified, remaining_codes = await service.verify_backup_code(user_id, code)
        
        if verified:
            # Set session flag to indicate 2FA is verified (Requirement 7.4)
            request.session['2fa_verified'] = True
            request.session['2fa_user_id'] = user_id
            request.session.save()
            
            response_data = {
                'message': 'Backup code verified successfully',
                'verified': True,
                'remaining_codes': remaining_codes or 0
            }
            
            response_serializer = VerifyBackupCodeResponseSerializer(data=response_data)
            response_serializer.is_valid(raise_exception=True)
            
            logger.info(f"Backup code verified for user {user_id}, {remaining_codes} codes remaining")
            
            return Response(
                response_serializer.validated_data,
                status=status.HTTP_200_OK
            )
        else:
            logger.warning(f"Invalid backup code for user {user_id}")
            return Response(
                {'error': 'Invalid or already used backup code'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
    except Exception as e:
        logger.error(f"Error verifying backup code for user {user_id}: {str(e)}")
        return Response(
            {'error': 'Failed to verify backup code'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
async def disable_2fa(request):
    """
    Disable 2FA for the authenticated user.
    
    DELETE /api/auth/2fa
    
    Returns:
        {
            "message": "2FA disabled successfully",
            "disabled": true
        }
    
    Requirements: 7.7, 7.9
    """
    user_id = request.clerk_user_id  # From authentication middleware
    
    try:
        service = TwoFactorAuthService()
        
        # Check if 2FA is enabled
        if not await service.has_2fa_enabled(user_id):
            return Response(
                {'error': '2FA is not enabled for this account'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Disable 2FA
        disabled = await service.disable_2fa(user_id)
        
        if disabled:
            # Get user email from Clerk for notification
            try:
                clerk_user = clerk.users.get(user_id)
                user_email = None
                for email_obj in clerk_user.email_addresses:
                    if email_obj.id == clerk_user.primary_email_address_id:
                        user_email = email_obj.email_address
                        break
                
                # Send email notification (Requirement 7.9)
                if user_email:
                    email_service = TwoFactorEmailService()
                    await email_service.send_2fa_disabled_notification(user_email)
            except Exception as e:
                logger.error(f"Failed to send 2FA disabled notification: {str(e)}")
                # Don't fail the request if email fails
            
            response_data = {
                'message': '2FA disabled successfully',
                'disabled': True
            }
            
            response_serializer = Disable2FAResponseSerializer(data=response_data)
            response_serializer.is_valid(raise_exception=True)
            
            logger.info(f"2FA disabled for user {user_id}")
            
            return Response(
                response_serializer.validated_data,
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {'error': 'Failed to disable 2FA'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    except Exception as e:
        logger.error(f"Error disabling 2FA for user {user_id}: {str(e)}")
        return Response(
            {'error': 'Failed to disable 2FA'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def regenerate_backup_codes(request):
    """
    Regenerate backup codes for the authenticated user.
    
    POST /api/auth/2fa/regenerate-backup-codes
    
    Returns:
        {
            "message": "Backup codes regenerated successfully",
            "backup_codes": ["code1", "code2", ...]
        }
    
    Requirements: 7.8
    """
    user_id = request.clerk_user_id  # From authentication middleware
    
    try:
        service = TwoFactorAuthService()
        
        # Check if 2FA is enabled
        if not await service.has_2fa_enabled(user_id):
            return Response(
                {'error': '2FA is not enabled for this account'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Regenerate backup codes
        backup_codes = await service.regenerate_backup_codes(user_id)
        
        response_data = {
            'message': 'Backup codes regenerated successfully. Store these codes in a safe place.',
            'backup_codes': backup_codes
        }
        
        response_serializer = RegenerateBackupCodesResponseSerializer(data=response_data)
        response_serializer.is_valid(raise_exception=True)
        
        logger.info(f"Backup codes regenerated for user {user_id}")
        
        return Response(
            response_serializer.validated_data,
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Error regenerating backup codes for user {user_id}: {str(e)}")
        return Response(
            {'error': 'Failed to regenerate backup codes'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
async def check_2fa_status(request):
    """
    Check if the user has 2FA enabled and if it's verified in the current session.
    
    GET /api/auth/2fa/status
    
    Returns:
        {
            "enabled": true/false,
            "verified": true/false
        }
    
    Requirements: 7.4
    """
    user_id = request.clerk_user_id  # From authentication middleware
    
    try:
        service = TwoFactorAuthService()
        
        # Check if 2FA is enabled
        has_2fa = await service.has_2fa_enabled(user_id)
        
        # Check if 2FA is verified in the current session
        is_verified = False
        if has_2fa:
            is_verified = request.session.get('2fa_verified', False)
            user_id_in_session = request.session.get('2fa_user_id')
            
            # Verify that the session 2FA verification matches the current user
            if user_id_in_session != user_id:
                is_verified = False
        
        return Response(
            {
                'enabled': has_2fa,
                'verified': is_verified
            },
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Error checking 2FA status for user {user_id}: {str(e)}")
        return Response(
            {'error': 'Failed to check 2FA status'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
