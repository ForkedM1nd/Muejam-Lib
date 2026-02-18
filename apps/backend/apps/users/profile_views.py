"""Views for enhanced profile features."""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from apps.core.decorators import async_api_view
from .profile_service import ProfileService


@api_view(['GET'])
@async_api_view
async def user_statistics(request, handle):
    """
    GET /v1/users/{handle}/statistics - Get user statistics
    
    Requirements:
        - 24.4: Display user statistics
        - 24.8, 24.9: Respect privacy settings
    
    Returns:
        - total_stories: Total published stories
        - total_chapters: Total published chapters
        - total_whispers: Total whispers posted
        - total_likes_received: Total likes on all content
        - follower_count: Number of followers
        - following_count: Number of users following
    """
    from .views import get_profile_by_handle
    from apps.gdpr.privacy_enforcement import PrivacyEnforcement
    
    # Get user profile
    profile = await get_profile_by_handle(handle)
    
    if not profile:
        return Response(
            {'error': {'code': 'NOT_FOUND', 'message': 'User not found'}},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check privacy settings
    viewer_id = getattr(request, 'user_profile_id', None)
    can_view = await PrivacyEnforcement.can_view_profile(profile.id, viewer_id)
    
    if not can_view:
        return Response(
            {'error': {'code': 'FORBIDDEN', 'message': 'Profile is private'}},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get statistics
    stats = await ProfileService.get_user_statistics(profile.id)
    
    return Response(stats)


@api_view(['GET'])
@async_api_view
async def user_pinned_stories(request, handle):
    """
    GET /v1/users/{handle}/pinned - Get user's pinned stories
    
    Requirements:
        - 24.5: Display pinned stories
    
    Returns:
        List of up to 3 pinned stories
    """
    from .views import get_profile_by_handle
    from apps.stories.serializers import StoryListSerializer
    
    # Get user profile
    profile = await get_profile_by_handle(handle)
    
    if not profile:
        return Response(
            {'error': {'code': 'NOT_FOUND', 'message': 'User not found'}},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Get pinned stories
    stories = await ProfileService.get_pinned_stories(profile.id)
    
    # Serialize stories
    serializer = StorySerializer(stories, many=True)
    
    return Response(serializer.data)


@api_view(['GET'])
@async_api_view
async def user_badges(request, handle):
    """
    GET /v1/users/{handle}/badges - Get user's badges
    
    Requirements:
        - 24.6: Display user badges
    
    Returns:
        List of badges earned by the user
    """
    from .views import get_profile_by_handle
    
    # Get user profile
    profile = await get_profile_by_handle(handle)
    
    if not profile:
        return Response(
            {'error': {'code': 'NOT_FOUND', 'message': 'User not found'}},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Get badges
    badges = await ProfileService.get_user_badges(profile.id)
    
    # Format badge data
    badge_data = [
        {
            'id': badge.id,
            'badge_type': badge.badge_type,
            'earned_at': badge.earned_at,
            'metadata': badge.metadata
        }
        for badge in badges
    ]
    
    return Response(badge_data)


@api_view(['POST'])
@async_api_view
async def pin_story(request):
    """
    POST /v1/me/pin-story - Pin a story to profile
    
    Requirements:
        - 24.5: Allow pinning up to 3 stories
    
    Request body:
        - story_id: ID of story to pin
        - position: Position (1, 2, or 3)
    """
    if not request.user_profile:
        return Response(
            {'error': {'code': 'UNAUTHORIZED', 'message': 'Authentication required'}},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    story_id = request.data.get('story_id')
    position = request.data.get('position', 1)
    
    if not story_id:
        return Response(
            {'error': {'code': 'VALIDATION_ERROR', 'message': 'story_id is required'}},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if position not in [1, 2, 3]:
        return Response(
            {'error': {'code': 'VALIDATION_ERROR', 'message': 'position must be 1, 2, or 3'}},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Update profile with pinned story
    from .views import update_profile
    
    field_name = f'pinned_story_{position}'
    updated_profile = await update_profile(
        request.user_profile.id,
        {field_name: story_id}
    )
    
    return Response({'message': 'Story pinned successfully'})


@api_view(['DELETE'])
@async_api_view
async def unpin_story(request, position):
    """
    DELETE /v1/me/pin-story/{position} - Unpin a story from profile
    
    Requirements:
        - 24.5: Allow unpinning stories
    """
    if not request.user_profile:
        return Response(
            {'error': {'code': 'UNAUTHORIZED', 'message': 'Authentication required'}},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    if int(position) not in [1, 2, 3]:
        return Response(
            {'error': {'code': 'VALIDATION_ERROR', 'message': 'position must be 1, 2, or 3'}},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Update profile to remove pinned story
    from .views import update_profile
    
    field_name = f'pinned_story_{position}'
    updated_profile = await update_profile(
        request.user_profile.id,
        {field_name: None}
    )
    
    return Response({'message': 'Story unpinned successfully'})
