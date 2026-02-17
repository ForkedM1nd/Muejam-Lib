"""Views for user profile management."""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from prisma import Prisma
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from apps.core.exceptions import DuplicateResource
from .serializers import (
    UserProfileReadSerializer,
    UserProfileWriteSerializer,
    PublicUserProfileSerializer
)


def sync_update_profile(user_id: str, update_data: dict):
    """Synchronous wrapper for update_profile."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is running, we need to use a different approach
            import nest_asyncio
            nest_asyncio.apply()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(update_profile(user_id, update_data))


def sync_get_profile_by_handle(handle: str):
    """Synchronous wrapper for get_profile_by_handle."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is running, we need to use a different approach
            import nest_asyncio
            nest_asyncio.apply()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(get_profile_by_handle(handle))


@api_view(['GET'])
def test_auth(request):
    """
    Test endpoint to verify Clerk authentication middleware.
    
    Returns the clerk_user_id and user_profile information if authenticated.
    """
    return Response({
        'authenticated': request.clerk_user_id is not None,
        'clerk_user_id': request.clerk_user_id,
        'user_profile': {
            'id': request.user_profile.id if request.user_profile else None,
            'handle': request.user_profile.handle if request.user_profile else None,
            'display_name': request.user_profile.display_name if request.user_profile else None,
        } if request.user_profile else None
    })


@extend_schema(
    tags=['Authentication'],
    summary='Get or update current user profile',
    description='''
    Retrieve or update the authenticated user's profile information.
    
    **GET**: Returns the current user's profile with all fields.
    
    **PUT**: Updates the current user's profile. Handle must be unique and follow format rules:
    - Alphanumeric characters and underscores only
    - 3-30 characters in length
    ''',
    request=UserProfileWriteSerializer,
    responses={
        200: UserProfileReadSerializer,
        400: OpenApiTypes.OBJECT,
        401: OpenApiTypes.OBJECT,
        409: OpenApiTypes.OBJECT,
    },
    examples=[
        OpenApiExample(
            'Update Profile Example',
            value={
                'handle': 'john_doe',
                'display_name': 'John Doe',
                'bio': 'Writer and reader of serial fiction',
                'avatar_key': 'avatars/uuid-here.jpg'
            },
            request_only=True,
        ),
        OpenApiExample(
            'Profile Response',
            value={
                'id': '123e4567-e89b-12d3-a456-426614174000',
                'clerk_user_id': 'user_2abc123def456',
                'handle': 'john_doe',
                'display_name': 'John Doe',
                'bio': 'Writer and reader of serial fiction',
                'avatar_key': 'avatars/uuid-here.jpg',
                'created_at': '2024-01-15T10:30:00Z',
                'updated_at': '2024-01-20T14:45:00Z'
            },
            response_only=True,
        ),
    ]
)
@api_view(['GET', 'PUT'])
def me(request):
    """
    GET /v1/me - Retrieve current user's profile
    PUT /v1/me - Update current user's profile
    
    Requirements:
        - 1.3: Validate handle uniqueness and update profile
        - 1.4: Return user profile with all fields
        - 1.5: Enforce handle format validation
    """
    # Check authentication
    if not request.clerk_user_id or not request.user_profile:
        return Response(
            {'error': {'code': 'UNAUTHORIZED', 'message': 'Authentication required'}},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    if request.method == 'GET':
        # Return current user's profile
        serializer = UserProfileReadSerializer(request.user_profile)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        # Update current user's profile
        serializer = UserProfileWriteSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {
                    'error': {
                        'code': 'VALIDATION_ERROR',
                        'message': 'Invalid input data',
                        'details': serializer.errors
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update profile
        updated_profile = sync_update_profile(
            request.user_profile.id, serializer.validated_data
        )
        
        if updated_profile is None:
            return Response(
                {
                    'error': {
                        'code': 'DUPLICATE_HANDLE',
                        'message': 'Handle is already taken by another user'
                    }
                },
                status=status.HTTP_409_CONFLICT
            )
        
        # Return updated profile
        response_serializer = UserProfileReadSerializer(updated_profile)
        return Response(response_serializer.data)


@extend_schema(
    tags=['Authentication'],
    summary='Get public user profile by handle',
    description='Retrieve a user\'s public profile information using their unique handle.',
    parameters=[
        OpenApiParameter(
            name='handle',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.PATH,
            description='Unique user handle (3-30 alphanumeric characters and underscores)',
            required=True,
        ),
    ],
    responses={
        200: PublicUserProfileSerializer,
        404: OpenApiTypes.OBJECT,
    },
    examples=[
        OpenApiExample(
            'Public Profile Response',
            value={
                'id': '123e4567-e89b-12d3-a456-426614174000',
                'handle': 'jane_writer',
                'display_name': 'Jane Writer',
                'bio': 'Fantasy and sci-fi author',
                'avatar_key': 'avatars/uuid-here.jpg',
                'created_at': '2024-01-10T08:00:00Z'
            },
            response_only=True,
        ),
    ]
)
@api_view(['GET'])
def user_by_handle(request, handle):
    """
    GET /v1/users/{handle} - Get public user profile by handle
    
    Requirements:
        - 1.4: Return public profile when accessed by handle
    """
    # Fetch profile by handle
    profile = sync_get_profile_by_handle(handle)
    
    if profile is None:
        return Response(
            {
                'error': {
                    'code': 'NOT_FOUND',
                    'message': 'User not found'
                }
            },
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Return public profile
    serializer = PublicUserProfileSerializer(profile)
    return Response(serializer.data)


async def update_profile(user_id: str, update_data: dict):
    """
    Update user profile with validated data.
    
    Args:
        user_id: ID of the user profile to update
        update_data: Dictionary of fields to update
        
    Returns:
        Updated UserProfile or None if handle is taken
        
    Requirements:
        - 1.3: Validate handle uniqueness before update
    """
    db = Prisma()
    await db.connect()
    
    try:
        # Check handle uniqueness if handle is being updated
        if 'handle' in update_data:
            existing = await db.userprofile.find_unique(
                where={'handle': update_data['handle']}
            )
            
            # If handle exists and belongs to different user, reject
            if existing and existing.id != user_id:
                await db.disconnect()
                return None
        
        # Update profile
        updated_profile = await db.userprofile.update(
            where={'id': user_id},
            data=update_data
        )
        
        await db.disconnect()
        return updated_profile
        
    except Exception as e:
        await db.disconnect()
        raise e


async def get_profile_by_handle(handle: str):
    """
    Fetch user profile by handle.
    
    Args:
        handle: User handle to search for
        
    Returns:
        UserProfile or None if not found
    """
    db = Prisma()
    await db.connect()
    
    try:
        profile = await db.userprofile.find_unique(
            where={'handle': handle}
        )
        
        await db.disconnect()
        return profile
        
    except Exception:
        await db.disconnect()
        return None
