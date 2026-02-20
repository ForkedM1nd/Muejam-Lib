"""Views for notification system."""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from prisma import Prisma
from datetime import datetime
from .serializers import NotificationSerializer


def _run_async(coro):
    """Run an async coroutine in an isolated event loop."""
    import asyncio

    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def sync_get_notifications(user_id: str, cursor: str = None, page_size: int = 20):
    """Synchronous wrapper for get_notifications."""
    return _run_async(get_notifications(user_id, cursor, page_size))


def sync_mark_notification_read(notification_id: str, user_id: str):
    """Synchronous wrapper for mark_notification_read."""
    return _run_async(mark_notification_read(notification_id, user_id))


def sync_mark_all_notifications_read(user_id: str):
    """Synchronous wrapper for mark_all_notifications_read."""
    return _run_async(mark_all_notifications_read(user_id))


def sync_create_notification(user_id: str, notification_type: str, actor_id: str, whisper_id: str = None):
    """Synchronous wrapper for create_notification."""
    return _run_async(create_notification(user_id, notification_type, actor_id, whisper_id))


@api_view(['GET'])
def notifications(request):
    """
    GET /v1/notifications - List notifications for current user
    
    Query parameters:
        - cursor: Pagination cursor
        - page_size: Number of results (default 20, max 100)
        
    Returns:
        - 200: List of notifications
        - 401: Not authenticated
        
    Requirements:
        - 12.3: List notifications ordered by creation time descending
    """
    # Check authentication
    if not request.clerk_user_id or not request.user_profile:
        return Response(
            {'error': {'code': 'UNAUTHORIZED', 'message': 'Authentication required'}},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    cursor = request.query_params.get('cursor')
    page_size = min(int(request.query_params.get('page_size', 20)), 100)
    
    result = sync_get_notifications(request.user_profile.id, cursor, page_size)
    
    notifications_list, next_cursor = result
    serializer = NotificationSerializer(notifications_list, many=True)
    
    return Response({
        'data': serializer.data,
        'next_cursor': next_cursor
    })


@api_view(['POST'])
def mark_read(request, id):
    """
    POST /v1/notifications/{id}/read - Mark notification as read
    
    Returns:
        - 200: Notification marked as read
        - 401: Not authenticated
        - 404: Notification not found
        
    Requirements:
        - 12.4: Mark notification as read
    """
    # Check authentication
    if not request.clerk_user_id or not request.user_profile:
        return Response(
            {'error': {'code': 'UNAUTHORIZED', 'message': 'Authentication required'}},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    notification = sync_mark_notification_read(id, request.user_profile.id)
    
    if notification is None:
        return Response(
            {'error': {'code': 'NOT_FOUND', 'message': 'Notification not found'}},
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = NotificationSerializer(notification)
    return Response(serializer.data)


@api_view(['POST'])
def mark_all_read(request):
    """
    POST /v1/notifications/read-all - Mark all notifications as read
    
    Returns:
        - 200: All notifications marked as read
        - 401: Not authenticated
        
    Requirements:
        - 12.4: Mark all notifications as read
    """
    # Check authentication
    if not request.clerk_user_id or not request.user_profile:
        return Response(
            {'error': {'code': 'UNAUTHORIZED', 'message': 'Authentication required'}},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    count = sync_mark_all_notifications_read(request.user_profile.id)
    
    return Response({
        'message': f'{count} notifications marked as read',
        'count': count
    })


async def get_notifications(user_id: str, cursor: str = None, page_size: int = 20):
    """
    Get list of notifications for a user with cursor pagination.
    
    Args:
        user_id: ID of the user
        cursor: Pagination cursor
        page_size: Number of results per page
        
    Returns:
        Tuple of (notifications list, next_cursor)
        
    Requirements:
        - 12.3: List notifications ordered by creation time descending
    """
    db = Prisma()
    await db.connect()
    
    try:
        # Build query
        where_clause = {'user_id': user_id}
        
        # Apply cursor if provided
        if cursor:
            import json
            import base64
            decoded = json.loads(base64.b64decode(cursor))
            where_clause['id'] = {'lt': decoded['id']}
        
        # Fetch notifications with one extra to check if there are more
        notifications = await db.notification.find_many(
            where=where_clause,
            order={'created_at': 'desc'},
            take=page_size + 1
        )
        
        # Check if there are more results
        has_next = len(notifications) > page_size
        if has_next:
            notifications = notifications[:-1]
        
        # Generate next cursor
        next_cursor = None
        if has_next and notifications:
            import json
            import base64
            last_notification = notifications[-1]
            next_cursor = base64.b64encode(
                json.dumps({'id': last_notification.id}).encode()
            ).decode()
        
        await db.disconnect()
        return (notifications, next_cursor)
        
    except Exception as e:
        await db.disconnect()
        raise e


async def mark_notification_read(notification_id: str, user_id: str):
    """
    Mark a notification as read.
    
    Args:
        notification_id: ID of the notification
        user_id: ID of the user (for authorization)
        
    Returns:
        Updated notification or None if not found
        
    Requirements:
        - 12.4: Update read_at timestamp
    """
    db = Prisma()
    await db.connect()
    
    try:
        # Find notification and verify ownership
        notification = await db.notification.find_unique(
            where={'id': notification_id}
        )
        
        if not notification or notification.user_id != user_id:
            await db.disconnect()
            return None
        
        # Update read_at timestamp
        updated_notification = await db.notification.update(
            where={'id': notification_id},
            data={'read_at': datetime.now()}
        )
        
        await db.disconnect()
        return updated_notification
        
    except Exception as e:
        await db.disconnect()
        raise e


async def mark_all_notifications_read(user_id: str):
    """
    Mark all unread notifications as read for a user.
    
    Args:
        user_id: ID of the user
        
    Returns:
        Number of notifications marked as read
        
    Requirements:
        - 12.4: Mark all notifications as read
    """
    db = Prisma()
    await db.connect()
    
    try:
        # Update all unread notifications
        result = await db.notification.update_many(
            where={
                'user_id': user_id,
                'read_at': None
            },
            data={'read_at': datetime.now()}
        )
        
        await db.disconnect()
        return result
        
    except Exception as e:
        await db.disconnect()
        raise e


async def create_notification(user_id: str, notification_type: str, actor_id: str, whisper_id: str = None):
    """
    Create a new notification.
    
    Args:
        user_id: ID of the user receiving the notification
        notification_type: Type of notification (REPLY or FOLLOW)
        actor_id: ID of the user who triggered the notification
        whisper_id: ID of the whisper (for REPLY notifications)
        
    Returns:
        Created notification
        
    Requirements:
        - 12.1: Create notification on reply
        - 12.2: Create notification on follow
    """
    db = Prisma()
    await db.connect()
    
    try:
        notification = await db.notification.create(
            data={
                'user_id': user_id,
                'type': notification_type,
                'actor_id': actor_id,
                'whisper_id': whisper_id
            }
        )
        
        await db.disconnect()
        return notification
        
    except Exception as e:
        await db.disconnect()
        raise e



# Notification Preference Views

def sync_get_preferences(user_id: str):
    """Synchronous wrapper for get_preferences."""
    from .preference_service import NotificationPreferenceService
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(NotificationPreferenceService.get_or_create_preferences(user_id))


def sync_update_preferences(user_id: str, updates: dict):
    """Synchronous wrapper for update_preferences."""
    from .preference_service import NotificationPreferenceService
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(NotificationPreferenceService.update_preferences(user_id, updates))


@api_view(['GET'])
def notification_preferences(request):
    """
    GET /api/notifications/preferences - Get notification preferences
    
    Returns:
        - 200: Notification preferences
        - 401: Not authenticated
        
    Requirements:
        - 21.9: Retrieve user notification preferences
    """
    # Check authentication
    if not request.clerk_user_id or not request.user_profile:
        return Response(
            {'error': {'code': 'UNAUTHORIZED', 'message': 'Authentication required'}},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    preferences = sync_get_preferences(request.user_profile.id)
    
    return Response({
        'data': preferences
    })


@api_view(['PUT'])
def update_notification_preferences(request):
    """
    PUT /api/notifications/preferences - Update notification preferences
    
    Body:
        {
            "new_comment": "immediate" | "daily_digest" | "weekly_digest" | "disabled",
            "new_like": "immediate" | "daily_digest" | "weekly_digest" | "disabled",
            "new_follower": "immediate" | "daily_digest" | "weekly_digest" | "disabled",
            "new_content": "immediate" | "daily_digest" | "weekly_digest" | "disabled",
            "marketing_emails": true | false
        }
    
    Returns:
        - 200: Updated preferences
        - 400: Invalid request
        - 401: Not authenticated
        
    Requirements:
        - 21.9: Allow users to configure notification preferences
        - 21.10: Support per-notification-type frequency settings
    """
    # Check authentication
    if not request.clerk_user_id or not request.user_profile:
        return Response(
            {'error': {'code': 'UNAUTHORIZED', 'message': 'Authentication required'}},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    updates = request.data
    
    # Validate updates
    valid_fields = [
        'welcome_email', 'new_comment', 'new_like', 'new_follower',
        'new_content', 'content_takedown', 'security_alert', 'marketing_emails'
    ]
    
    invalid_fields = [key for key in updates.keys() if key not in valid_fields]
    if invalid_fields:
        return Response(
            {'error': {'code': 'INVALID_REQUEST', 'message': f'Invalid fields: {invalid_fields}'}},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        preferences = sync_update_preferences(request.user_profile.id, updates)
        
        return Response({
            'data': preferences,
            'message': 'Notification preferences updated successfully'
        })
        
    except ValueError as e:
        return Response(
            {'error': {'code': 'INVALID_REQUEST', 'message': str(e)}},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': {'code': 'INTERNAL_ERROR', 'message': 'Failed to update preferences'}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



# Device Token Management Views

def sync_register_device(user_id: str, token: str, platform: str, app_version: str = None):
    """Synchronous wrapper for register_device."""
    from .push_service import PushNotificationService
    loop = asyncio.get_event_loop()
    service = PushNotificationService()
    return loop.run_until_complete(service.register_device(user_id, token, platform, app_version))


def sync_unregister_device(token: str):
    """Synchronous wrapper for unregister_device."""
    from .push_service import PushNotificationService
    loop = asyncio.get_event_loop()
    service = PushNotificationService()
    return loop.run_until_complete(service.unregister_device(token))


def sync_get_user_devices(user_id: str):
    """Synchronous wrapper for get_user_devices."""
    from .push_service import PushNotificationService
    loop = asyncio.get_event_loop()
    service = PushNotificationService()
    return loop.run_until_complete(service.get_user_devices(user_id))


@api_view(['POST'])
def register_device(request):
    """
    POST /v1/devices/register - Register device token for push notifications
    
    Body:
        {
            "token": "device_token_from_fcm_or_apns",
            "platform": "ios" | "android",
            "app_version": "1.0.0" (optional)
        }
    
    Returns:
        - 200: Device token registered successfully
        - 400: Invalid request
        - 401: Not authenticated
        
    Requirements:
        - 4.1: Register device token for push notifications
        - 4.2: Store token with user and platform information
    """
    from .serializers import DeviceTokenRegisterSerializer, DeviceTokenResponseSerializer
    
    # Check authentication
    if not request.clerk_user_id or not request.user_profile:
        return Response(
            {'error': {'code': 'UNAUTHORIZED', 'message': 'Authentication required'}},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Validate request data
    serializer = DeviceTokenRegisterSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'error': {'code': 'INVALID_REQUEST', 'message': 'Invalid request data', 'details': serializer.errors}},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        device_token = sync_register_device(
            user_id=request.user_profile.id,
            token=serializer.validated_data['token'],
            platform=serializer.validated_data['platform'],
            app_version=serializer.validated_data.get('app_version')
        )
        
        response_serializer = DeviceTokenResponseSerializer(device_token)
        
        return Response({
            'data': response_serializer.data,
            'message': 'Device registered successfully'
        }, status=status.HTTP_200_OK)
        
    except ValueError as e:
        return Response(
            {'error': {'code': 'INVALID_REQUEST', 'message': str(e)}},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': {'code': 'INTERNAL_ERROR', 'message': 'Failed to register device'}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
def unregister_device(request):
    """
    DELETE /v1/devices/unregister - Unregister device token
    
    Body:
        {
            "token": "device_token_to_unregister"
        }
    
    Returns:
        - 200: Device token unregistered successfully
        - 400: Invalid request
        - 401: Not authenticated
        - 404: Device token not found
        
    Requirements:
        - 4.4: Handle device token deregistration
    """
    from .serializers import DeviceTokenUnregisterSerializer
    
    # Check authentication
    if not request.clerk_user_id or not request.user_profile:
        return Response(
            {'error': {'code': 'UNAUTHORIZED', 'message': 'Authentication required'}},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Validate request data
    serializer = DeviceTokenUnregisterSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'error': {'code': 'INVALID_REQUEST', 'message': 'Invalid request data', 'details': serializer.errors}},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        success = sync_unregister_device(serializer.validated_data['token'])
        
        if not success:
            return Response(
                {'error': {'code': 'NOT_FOUND', 'message': 'Device token not found'}},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response({
            'message': 'Device unregistered successfully'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': {'code': 'INTERNAL_ERROR', 'message': 'Failed to unregister device'}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT'])
def update_device_preferences(request):
    """
    PUT /v1/devices/preferences - Update device notification preferences
    
    Body:
        {
            "token": "device_token",
            "enabled": true | false,
            "notification_types": ["reply", "follow", "like"] (optional)
        }
    
    Returns:
        - 200: Preferences updated successfully
        - 400: Invalid request
        - 401: Not authenticated
        - 404: Device token not found
        
    Requirements:
        - 4.3: Update notification preferences per device
    """
    from .serializers import DevicePreferencesSerializer
    
    # Check authentication
    if not request.clerk_user_id or not request.user_profile:
        return Response(
            {'error': {'code': 'UNAUTHORIZED', 'message': 'Authentication required'}},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Validate request data
    serializer = DevicePreferencesSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'error': {'code': 'INVALID_REQUEST', 'message': 'Invalid request data', 'details': serializer.errors}},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # For now, we'll use the enabled flag to activate/deactivate the device token
        # In a full implementation, you would store notification_types preferences separately
        token = serializer.validated_data['token']
        enabled = serializer.validated_data.get('enabled', True)
        
        if not enabled:
            # Deactivate the device token
            success = sync_unregister_device(token)
            if not success:
                return Response(
                    {'error': {'code': 'NOT_FOUND', 'message': 'Device token not found'}},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Verify the device token exists and belongs to the user
            devices = sync_get_user_devices(request.user_profile.id)
            device_found = any(d['token'] == token for d in devices)
            
            if not device_found:
                return Response(
                    {'error': {'code': 'NOT_FOUND', 'message': 'Device token not found for this user'}},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        return Response({
            'message': 'Device preferences updated successfully',
            'data': {
                'token': token,
                'enabled': enabled,
                'notification_types': serializer.validated_data.get('notification_types', [])
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': {'code': 'INTERNAL_ERROR', 'message': 'Failed to update device preferences'}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
