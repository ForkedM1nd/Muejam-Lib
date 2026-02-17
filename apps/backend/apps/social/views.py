"""Views for social features (follow/block)."""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from prisma import Prisma
from apps.core.pagination import CursorPagination
from .serializers import (
    FollowSerializer,
    FollowerListSerializer,
    FollowingListSerializer,
    BlockSerializer
)
from apps.notifications.views import sync_create_notification


def sync_follow_user(follower_id: str, following_id: str):
    """Synchronous wrapper for follow_user."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(follow_user(follower_id, following_id))


def sync_unfollow_user(follower_id: str, following_id: str):
    """Synchronous wrapper for unfollow_user."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(unfollow_user(follower_id, following_id))


def sync_get_followers(user_id: str, cursor: str = None, page_size: int = 20):
    """Synchronous wrapper for get_followers."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(get_followers(user_id, cursor, page_size))


def sync_get_following(user_id: str, cursor: str = None, page_size: int = 20):
    """Synchronous wrapper for get_following."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(get_following(user_id, cursor, page_size))


def sync_block_user(blocker_id: str, blocked_id: str):
    """Synchronous wrapper for block_user."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(block_user(blocker_id, blocked_id))


def sync_unblock_user(blocker_id: str, blocked_id: str):
    """Synchronous wrapper for unblock_user."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(unblock_user(blocker_id, blocked_id))


@api_view(['POST', 'DELETE'])
def follow(request, id):
    """
    POST /v1/users/{id}/follow - Follow a user
    DELETE /v1/users/{id}/follow - Unfollow a user
    
    Requirements:
        - 11.1: Follow user creates Follow record
        - 11.2: Unfollow user deletes Follow record
        - 11.8: Prevent duplicate follow relationships
    """
    # Check authentication
    if not request.clerk_user_id or not request.user_profile:
        return Response(
            {'error': {'code': 'UNAUTHORIZED', 'message': 'Authentication required'}},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Prevent following self
    if request.user_profile.id == id:
        return Response(
            {'error': {'code': 'INVALID_OPERATION', 'message': 'Cannot follow yourself'}},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if request.method == 'POST':
        # Follow user
        result = sync_follow_user(request.user_profile.id, id)
        
        if result is None:
            return Response(
                {'error': {'code': 'NOT_FOUND', 'message': 'User not found'}},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if result == 'blocked':
            return Response(
                {'error': {'code': 'BLOCKED', 'message': 'Cannot follow a blocked user'}},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if result == 'duplicate':
            return Response(
                {'error': {'code': 'DUPLICATE', 'message': 'Already following this user'}},
                status=status.HTTP_409_CONFLICT
            )
        
        serializer = FollowSerializer(result)
        
        # Create notification for the followed user
        sync_create_notification(
            user_id=id,
            notification_type='FOLLOW',
            actor_id=request.user_profile.id,
            whisper_id=None
        )
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    elif request.method == 'DELETE':
        # Unfollow user
        success = sync_unfollow_user(request.user_profile.id, id)
        
        if not success:
            return Response(
                {'error': {'code': 'NOT_FOUND', 'message': 'Follow relationship not found'}},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
def followers(request, id):
    """
    GET /v1/users/{id}/followers - List followers for a user
    
    Requirements:
        - 11.1: List followers with pagination
    """
    cursor = request.query_params.get('cursor')
    page_size = min(int(request.query_params.get('page_size', 20)), 100)
    
    result = sync_get_followers(id, cursor, page_size)
    
    if result is None:
        return Response(
            {'error': {'code': 'NOT_FOUND', 'message': 'User not found'}},
            status=status.HTTP_404_NOT_FOUND
        )
    
    followers_list, next_cursor = result
    serializer = FollowerListSerializer(followers_list, many=True)
    
    return Response({
        'data': serializer.data,
        'next_cursor': next_cursor
    })


@api_view(['GET'])
def following(request, id):
    """
    GET /v1/users/{id}/following - List users that a user is following
    
    Requirements:
        - 11.1: List following with pagination
    """
    cursor = request.query_params.get('cursor')
    page_size = min(int(request.query_params.get('page_size', 20)), 100)
    
    result = sync_get_following(id, cursor, page_size)
    
    if result is None:
        return Response(
            {'error': {'code': 'NOT_FOUND', 'message': 'User not found'}},
            status=status.HTTP_404_NOT_FOUND
        )
    
    following_list, next_cursor = result
    serializer = FollowingListSerializer(following_list, many=True)
    
    return Response({
        'data': serializer.data,
        'next_cursor': next_cursor
    })


@api_view(['POST', 'DELETE'])
def block(request, id):
    """
    POST /v1/users/{id}/block - Block a user
    DELETE /v1/users/{id}/block - Unblock a user
    
    Requirements:
        - 11.3: Block user creates Block record
        - 11.4: Unblock user deletes Block record
        - 11.7: Prevent following blocked users
        - 11.9: Remove follow relationship on block
    """
    # Check authentication
    if not request.clerk_user_id or not request.user_profile:
        return Response(
            {'error': {'code': 'UNAUTHORIZED', 'message': 'Authentication required'}},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Prevent blocking self
    if request.user_profile.id == id:
        return Response(
            {'error': {'code': 'INVALID_OPERATION', 'message': 'Cannot block yourself'}},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if request.method == 'POST':
        # Block user
        result = sync_block_user(request.user_profile.id, id)
        
        if result is None:
            return Response(
                {'error': {'code': 'NOT_FOUND', 'message': 'User not found'}},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if result == 'duplicate':
            return Response(
                {'error': {'code': 'DUPLICATE', 'message': 'User is already blocked'}},
                status=status.HTTP_409_CONFLICT
            )
        
        serializer = BlockSerializer(result)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    elif request.method == 'DELETE':
        # Unblock user
        success = sync_unblock_user(request.user_profile.id, id)
        
        if not success:
            return Response(
                {'error': {'code': 'NOT_FOUND', 'message': 'Block relationship not found'}},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(status=status.HTTP_204_NO_CONTENT)


async def follow_user(follower_id: str, following_id: str):
    """
    Create a follow relationship between two users.
    
    Args:
        follower_id: ID of the user who is following
        following_id: ID of the user being followed
        
    Returns:
        Follow record, None if user not found, 'blocked' if blocked, 'duplicate' if already following
        
    Requirements:
        - 11.1: Create Follow record
        - 11.7: Prevent following blocked users
        - 11.8: Prevent duplicate follows
    """
    db = Prisma()
    await db.connect()
    
    try:
        # Check if following user exists
        following_user = await db.userprofile.find_unique(
            where={'id': following_id}
        )
        
        if not following_user:
            await db.disconnect()
            return None
        
        # Check if user is blocked
        block = await db.block.find_first(
            where={
                'blocker_id': follower_id,
                'blocked_id': following_id
            }
        )
        
        if block:
            await db.disconnect()
            return 'blocked'
        
        # Check for duplicate follow
        existing_follow = await db.follow.find_first(
            where={
                'follower_id': follower_id,
                'following_id': following_id
            }
        )
        
        if existing_follow:
            await db.disconnect()
            return 'duplicate'
        
        # Create follow relationship
        follow = await db.follow.create(
            data={
                'follower_id': follower_id,
                'following_id': following_id
            }
        )
        
        await db.disconnect()
        return follow
        
    except Exception as e:
        await db.disconnect()
        raise e


async def unfollow_user(follower_id: str, following_id: str):
    """
    Remove a follow relationship between two users.
    
    Args:
        follower_id: ID of the user who is unfollowing
        following_id: ID of the user being unfollowed
        
    Returns:
        True if successful, False if relationship not found
        
    Requirements:
        - 11.2: Delete Follow record
    """
    db = Prisma()
    await db.connect()
    
    try:
        # Find and delete follow relationship
        follow = await db.follow.find_first(
            where={
                'follower_id': follower_id,
                'following_id': following_id
            }
        )
        
        if not follow:
            await db.disconnect()
            return False
        
        await db.follow.delete(
            where={'id': follow.id}
        )
        
        await db.disconnect()
        return True
        
    except Exception:
        await db.disconnect()
        return False


async def get_followers(user_id: str, cursor: str = None, page_size: int = 20):
    """
    Get list of followers for a user with cursor pagination.
    
    Args:
        user_id: ID of the user
        cursor: Pagination cursor
        page_size: Number of results per page
        
    Returns:
        Tuple of (followers list, next_cursor) or None if user not found
        
    Requirements:
        - 11.1: List followers with pagination
    """
    db = Prisma()
    await db.connect()
    
    try:
        # Check if user exists
        user = await db.userprofile.find_unique(
            where={'id': user_id}
        )
        
        if not user:
            await db.disconnect()
            return None
        
        # Build query
        where_clause = {'following_id': user_id}
        
        # Apply cursor if provided
        if cursor:
            import json
            import base64
            decoded = json.loads(base64.b64decode(cursor))
            where_clause['id'] = {'lt': decoded['id']}
        
        # Fetch followers with one extra to check if there are more
        follows = await db.follow.find_many(
            where=where_clause,
            include={'follower': True},
            order={'id': 'desc'},
            take=page_size + 1
        )
        
        # Check if there are more results
        has_next = len(follows) > page_size
        if has_next:
            follows = follows[:-1]
        
        # Extract follower profiles
        followers = [f.follower for f in follows]
        
        # Generate next cursor
        next_cursor = None
        if has_next and follows:
            import json
            import base64
            last_follow = follows[-1]
            next_cursor = base64.b64encode(
                json.dumps({'id': last_follow.id}).encode()
            ).decode()
        
        await db.disconnect()
        return (followers, next_cursor)
        
    except Exception as e:
        await db.disconnect()
        raise e


async def get_following(user_id: str, cursor: str = None, page_size: int = 20):
    """
    Get list of users that a user is following with cursor pagination.
    
    Args:
        user_id: ID of the user
        cursor: Pagination cursor
        page_size: Number of results per page
        
    Returns:
        Tuple of (following list, next_cursor) or None if user not found
        
    Requirements:
        - 11.1: List following with pagination
    """
    db = Prisma()
    await db.connect()
    
    try:
        # Check if user exists
        user = await db.userprofile.find_unique(
            where={'id': user_id}
        )
        
        if not user:
            await db.disconnect()
            return None
        
        # Build query
        where_clause = {'follower_id': user_id}
        
        # Apply cursor if provided
        if cursor:
            import json
            import base64
            decoded = json.loads(base64.b64decode(cursor))
            where_clause['id'] = {'lt': decoded['id']}
        
        # Fetch following with one extra to check if there are more
        follows = await db.follow.find_many(
            where=where_clause,
            include={'following': True},
            order={'id': 'desc'},
            take=page_size + 1
        )
        
        # Check if there are more results
        has_next = len(follows) > page_size
        if has_next:
            follows = follows[:-1]
        
        # Extract following profiles
        following = [f.following for f in follows]
        
        # Generate next cursor
        next_cursor = None
        if has_next and follows:
            import json
            import base64
            last_follow = follows[-1]
            next_cursor = base64.b64encode(
                json.dumps({'id': last_follow.id}).encode()
            ).decode()
        
        await db.disconnect()
        return (following, next_cursor)
        
    except Exception as e:
        await db.disconnect()
        raise e


async def block_user(blocker_id: str, blocked_id: str):
    """
    Create a block relationship and remove any follow relationships.
    
    Args:
        blocker_id: ID of the user who is blocking
        blocked_id: ID of the user being blocked
        
    Returns:
        Block record, None if user not found, 'duplicate' if already blocked
        
    Requirements:
        - 11.3: Create Block record
        - 11.9: Remove follow relationship on block
    """
    db = Prisma()
    await db.connect()
    
    try:
        # Check if blocked user exists
        blocked_user = await db.userprofile.find_unique(
            where={'id': blocked_id}
        )
        
        if not blocked_user:
            await db.disconnect()
            return None
        
        # Check for duplicate block
        existing_block = await db.block.find_first(
            where={
                'blocker_id': blocker_id,
                'blocked_id': blocked_id
            }
        )
        
        if existing_block:
            await db.disconnect()
            return 'duplicate'
        
        # Remove any existing follow relationships (both directions)
        await db.follow.delete_many(
            where={
                'OR': [
                    {'follower_id': blocker_id, 'following_id': blocked_id},
                    {'follower_id': blocked_id, 'following_id': blocker_id}
                ]
            }
        )
        
        # Create block relationship
        block = await db.block.create(
            data={
                'blocker_id': blocker_id,
                'blocked_id': blocked_id
            }
        )
        
        await db.disconnect()
        return block
        
    except Exception as e:
        await db.disconnect()
        raise e


async def unblock_user(blocker_id: str, blocked_id: str):
    """
    Remove a block relationship between two users.
    
    Args:
        blocker_id: ID of the user who is unblocking
        blocked_id: ID of the user being unblocked
        
    Returns:
        True if successful, False if relationship not found
        
    Requirements:
        - 11.4: Delete Block record
    """
    db = Prisma()
    await db.connect()
    
    try:
        # Find and delete block relationship
        block = await db.block.find_first(
            where={
                'blocker_id': blocker_id,
                'blocked_id': blocked_id
            }
        )
        
        if not block:
            await db.disconnect()
            return False
        
        await db.block.delete(
            where={'id': block.id}
        )
        
        await db.disconnect()
        return True
        
    except Exception:
        await db.disconnect()
        return False
