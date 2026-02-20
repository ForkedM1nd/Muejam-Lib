"""Views for user profile management."""
import asyncio
import threading
from datetime import datetime
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from prisma import Prisma
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from apps.core.exceptions import DuplicateResource
from apps.core.content_sanitizer import ContentSanitizer
from apps.core.pii_middleware import check_profile_pii
from infrastructure.cache_manager import CacheManager
from .serializers import (
    UserProfileReadSerializer,
    UserProfileWriteSerializer,
    PublicUserProfileSerializer
)

# Initialize cache manager
cache_manager = CacheManager()


def _run_async(coro):
    """Run async Prisma operations safely from sync views."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    result = {}
    error = {}

    def _runner():
        try:
            result['value'] = asyncio.run(coro)
        except Exception as exc:
            error['value'] = exc

    thread = threading.Thread(target=_runner)
    thread.start()
    thread.join()

    if 'value' in error:
        raise error['value']

    return result.get('value')


def sync_update_profile(user_id: str, update_data: dict):
    """
    Synchronous version of update_profile.
    
    This replaces the async version to avoid the nest_asyncio anti-pattern
    that was causing performance issues and potential deadlocks.
    """
    async def _update_profile():
        db = Prisma()
        await db.connect()

        try:
            if 'handle' in update_data:
                existing = await db.userprofile.find_unique(
                    where={'handle': update_data['handle']}
                )

                if existing and existing.id != user_id:
                    return None

            updated_profile = await db.userprofile.update(
                where={'id': user_id},
                data=update_data
            )

            cache_manager.invalidate(f'user_profile:{user_id}')
            cache_manager.invalidate(f'user_profile_by_handle:{updated_profile.handle}')

            return updated_profile
        finally:
            await db.disconnect()

    return _run_async(_update_profile())


def sync_get_profile_by_handle(handle: str):
    """
    Synchronous version of get_profile_by_handle.
    
    This replaces the async version to avoid the nest_asyncio anti-pattern
    that was causing performance issues and potential deadlocks.
    """
    # Check cache first
    cache_key = f'user_profile_by_handle:{handle}'
    cached_profile = cache_manager.get(cache_key)
    
    if cached_profile is not None:
        # Return cached profile (need to convert dict back to Prisma model)
        return type('UserProfile', (), cached_profile)
    
    async def _get_profile():
        db = Prisma()
        await db.connect()

        try:
            profile = await db.userprofile.find_unique(
                where={'handle': handle}
            )

            if profile:
                profile_dict = {
                    'id': profile.id,
                    'clerk_user_id': profile.clerk_user_id,
                    'handle': profile.handle,
                    'display_name': profile.display_name,
                    'bio': profile.bio,
                    'avatar_key': profile.avatar_key,
                    'created_at': profile.created_at.isoformat() if profile.created_at else None,
                    'updated_at': profile.updated_at.isoformat() if profile.updated_at else None,
                }

                ttl = cache_manager.get_ttl_for_type('user_profile')
                cache_manager.set(cache_key, profile_dict, ttl=ttl, tags=[f'user:{profile.id}'])

            return profile
        except Exception:
            return None
        finally:
            await db.disconnect()

    return _run_async(_get_profile())


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
        profile_data = serializer.data
        
        # Add cache headers for offline support (Requirements 9.1, 9.4)
        from apps.core.offline_support_service import OfflineSupportService
        import json
        
        last_modified = request.user_profile.updated_at
        etag = OfflineSupportService.generate_etag(json.dumps(profile_data, default=str))
        
        # Check conditional request
        if OfflineSupportService.check_conditional_request(request, last_modified, etag):
            response = OfflineSupportService.create_not_modified_response()
            OfflineSupportService.add_cache_headers(response, last_modified, etag)
            return response
        
        response = Response(profile_data)
        OfflineSupportService.add_cache_headers(response, last_modified, etag)
        return response
    
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
        
        # Check for PII in profile fields (Requirement 9.7)
        has_pii, pii_error = check_profile_pii(
            request.data,
            fields=['bio', 'display_name']
        )
        
        if has_pii:
            return pii_error
        
        # Sanitize bio field if present (Requirement 6.8)
        validated_data = serializer.validated_data
        if 'bio' in validated_data and validated_data['bio']:
            validated_data['bio'] = ContentSanitizer.sanitize_plain_text(validated_data['bio'])
        
        # Update profile
        updated_profile = sync_update_profile(
            request.user_profile.id, validated_data
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
        - 9.2: Support conditional requests
        - 9.3: Return 304 Not Modified when appropriate
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
    
    # Serialize profile
    serializer = PublicUserProfileSerializer(profile)
    profile_data = serializer.data
    
    # Check conditional request headers (Requirements 9.2, 9.3)
    from apps.core.offline_support_service import OfflineSupportService
    import json
    
    last_modified = profile.updated_at
    if isinstance(last_modified, str):
        try:
            last_modified = datetime.fromisoformat(last_modified.replace('Z', '+00:00'))
        except ValueError:
            last_modified = datetime.now()

    if not isinstance(last_modified, datetime):
        last_modified = datetime.now()

    stable_etag_payload = f"{profile_data.get('id')}:{int(last_modified.timestamp())}"
    etag = OfflineSupportService.generate_etag(stable_etag_payload)
    
    # Check if client has fresh cached content
    if OfflineSupportService.check_conditional_request(request, last_modified, etag):
        # Return 304 Not Modified
        response = OfflineSupportService.create_not_modified_response()
        OfflineSupportService.add_cache_headers(response, last_modified, etag)
        return response
    
    # Create response with cache headers
    response = Response(profile_data)
    OfflineSupportService.add_cache_headers(response, last_modified, etag)
    
    return response



