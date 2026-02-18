"""
GDPR API Views

Endpoints for data export and account deletion.

Requirements:
- 10.1: Provide "Download My Data" feature
- 10.6: Provide "Delete My Account" feature
- 10.14: Allow cancellation of deletion request
"""

import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .data_export_service import DataExportService
from .account_deletion_service import AccountDeletionService
from .tasks import generate_data_export
from .email_service import send_deletion_confirmation_email

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def request_data_export(request):
    """
    Request a data export.
    
    POST /api/gdpr/export
    
    Returns:
        201: Export request created
        500: Server error
        
    Requirements: 10.1
    """
    try:
        user_id = request.clerk_user_id
        
        # Create export request
        service = DataExportService()
        export_request = await service.create_export_request(user_id)
        
        # Queue async task to generate export
        generate_data_export.delay(export_request['id'])
        
        return Response({
            'message': 'Data export request created',
            'export_request': export_request
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error creating export request: {str(e)}")
        return Response(
            {'error': 'Failed to create export request'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
async def get_export_status(request, export_id):
    """
    Get status of a data export request.
    
    GET /api/gdpr/export/{export_id}
    
    Returns:
        200: Export request details
        404: Export request not found
        403: User does not own this export request
        
    Requirements: 10.1
    """
    try:
        user_id = request.clerk_user_id
        
        # Get export request
        service = DataExportService()
        export_request = await service.get_export_request(export_id)
        
        if not export_request:
            return Response(
                {'error': 'Export request not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verify ownership
        if export_request['user_id'] != user_id:
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return Response(export_request, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error fetching export request: {str(e)}")
        return Response(
            {'error': 'Failed to fetch export request'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def request_account_deletion(request):
    """
    Request account deletion.
    
    POST /api/gdpr/delete
    
    Request body:
        {
            "password": "user_password"  // For confirmation
        }
    
    Returns:
        201: Deletion request created
        400: Invalid request
        500: Server error
        
    Requirements: 10.6, 10.7
    """
    try:
        user_id = request.clerk_user_id
        
        # TODO: Verify password with Clerk
        password = request.data.get('password')
        if not password:
            return Response(
                {'error': 'Password confirmation required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create deletion request
        service = AccountDeletionService()
        deletion_request = await service.create_deletion_request(user_id)
        
        # Generate cancellation URL
        cancellation_url = f"https://muejam.com/account/cancel-deletion/{deletion_request['id']}"
        
        # Send confirmation email
        await send_deletion_confirmation_email(
            user_id=user_id,
            cancellation_url=cancellation_url,
            scheduled_date=deletion_request['scheduled_deletion_at']
        )
        
        return Response({
            'message': 'Account deletion request created',
            'deletion_request': deletion_request
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error creating deletion request: {str(e)}")
        return Response(
            {'error': 'Failed to create deletion request'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def cancel_deletion_request(request, deletion_id):
    """
    Cancel a pending account deletion request.
    
    POST /api/gdpr/delete/{deletion_id}/cancel
    
    Returns:
        200: Deletion request cancelled
        404: Deletion request not found
        403: User does not own this deletion request
        400: Cannot cancel (already completed or cancelled)
        
    Requirements: 10.14
    """
    try:
        user_id = request.clerk_user_id
        
        # Cancel deletion request
        service = AccountDeletionService()
        deletion_request = await service.cancel_deletion_request(deletion_id, user_id)
        
        return Response({
            'message': 'Account deletion request cancelled',
            'deletion_request': deletion_request
        }, status=status.HTTP_200_OK)
        
    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except PermissionError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_403_FORBIDDEN
        )
    except Exception as e:
        logger.error(f"Error cancelling deletion request: {str(e)}")
        return Response(
            {'error': 'Failed to cancel deletion request'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
async def get_deletion_status(request, deletion_id):
    """
    Get status of an account deletion request.
    
    GET /api/gdpr/delete/{deletion_id}
    
    Returns:
        200: Deletion request details
        404: Deletion request not found
        403: User does not own this deletion request
        
    Requirements: 10.6
    """
    try:
        user_id = request.clerk_user_id
        
        # Get deletion request
        service = AccountDeletionService()
        deletion_request = await service.get_deletion_request(deletion_id)
        
        if not deletion_request:
            return Response(
                {'error': 'Deletion request not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verify ownership
        if deletion_request['user_id'] != user_id:
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return Response(deletion_request, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error fetching deletion request: {str(e)}")
        return Response(
            {'error': 'Failed to fetch deletion request'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



@api_view(['GET'])
@permission_classes([IsAuthenticated])
async def get_privacy_settings(request):
    """
    Get user's privacy settings.
    
    GET /api/privacy/settings
    
    Returns:
        200: Privacy settings
        500: Server error
        
    Requirements: 11.1
    """
    try:
        from .privacy_settings_service import PrivacySettingsService
        
        user_id = request.clerk_user_id
        
        # Get or create privacy settings
        service = PrivacySettingsService()
        settings = await service.get_or_create_settings(user_id)
        
        return Response(settings, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error fetching privacy settings: {str(e)}")
        return Response(
            {'error': 'Failed to fetch privacy settings'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
async def update_privacy_settings(request):
    """
    Update user's privacy settings.
    
    PUT /api/privacy/settings
    
    Request body:
        {
            "profile_visibility": "PUBLIC" | "FOLLOWERS_ONLY" | "PRIVATE",
            "reading_history_visibility": "PUBLIC" | "FOLLOWERS_ONLY" | "PRIVATE",
            "analytics_opt_out": boolean,
            "marketing_emails": boolean,
            "comment_permissions": "ANYONE" | "FOLLOWERS" | "DISABLED",
            "follower_approval_required": "ANYONE" | "APPROVAL_REQUIRED"
        }
    
    Returns:
        200: Updated privacy settings
        400: Invalid request
        500: Server error
        
    Requirements: 11.1-11.8, 11.10
    """
    try:
        from .privacy_settings_service import PrivacySettingsService
        
        user_id = request.clerk_user_id
        updates = request.data
        
        # Validate that at least one field is being updated
        if not updates:
            return Response(
                {'error': 'No updates provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update privacy settings
        service = PrivacySettingsService()
        settings = await service.update_settings(user_id, updates)
        
        return Response({
            'message': 'Privacy settings updated',
            'settings': settings
        }, status=status.HTTP_200_OK)
        
    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Error updating privacy settings: {str(e)}")
        return Response(
            {'error': 'Failed to update privacy settings'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
async def get_consent_history(request):
    """
    Get user's consent history.
    
    GET /api/consent/history
    
    Returns:
        200: List of consent records
        500: Server error
        
    Requirements: 11.11
    """
    try:
        from .privacy_settings_service import PrivacySettingsService
        
        user_id = request.clerk_user_id
        
        # Get consent history
        service = PrivacySettingsService()
        history = await service.get_consent_history(user_id)
        
        return Response({
            'consents': history
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error fetching consent history: {str(e)}")
        return Response(
            {'error': 'Failed to fetch consent history'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def withdraw_consent(request):
    """
    Withdraw consent for optional data processing.
    
    POST /api/consent/withdraw
    
    Request body:
        {
            "consent_type": "analytics" | "marketing"
        }
    
    Returns:
        200: Consent withdrawn, updated settings
        400: Invalid consent type
        500: Server error
        
    Requirements: 11.12, 11.13
    """
    try:
        from .privacy_settings_service import PrivacySettingsService
        
        user_id = request.clerk_user_id
        consent_type = request.data.get('consent_type')
        
        if not consent_type:
            return Response(
                {'error': 'consent_type is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Withdraw consent
        service = PrivacySettingsService()
        settings = await service.withdraw_consent(user_id, consent_type)
        
        return Response({
            'message': f'Consent withdrawn for {consent_type}',
            'settings': settings
        }, status=status.HTTP_200_OK)
        
    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Error withdrawing consent: {str(e)}")
        return Response(
            {'error': 'Failed to withdraw consent'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
