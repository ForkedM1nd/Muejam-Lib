"""Views for notification system."""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from prisma import Prisma
from datetime import datetime
from .serializers import NotificationSerializer


def sync_get_notifications(user_id: str, cursor: str = None, page_size: int = 20):
    """Synchronous wrapper for get_notifications."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(get_notifications(user_id, cursor, page_size))


def sync_mark_notification_read(notification_id: str, user_id: str):
    """Synchronous wrapper for mark_notification_read."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(mark_notification_read(notification_id, user_id))


def sync_mark_all_notifications_read(user_id: str):
    """Synchronous wrapper for mark_all_notifications_read."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(mark_all_notifications_read(user_id))


def sync_create_notification(user_id: str, notification_type: str, actor_id: str, whisper_id: str = None):
    """Synchronous wrapper for create_notification."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(create_notification(user_id, notification_type, actor_id, whisper_id))


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
