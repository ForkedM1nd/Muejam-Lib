"""Views for whispers micro-posting system."""
import logging
from datetime import datetime
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from prisma import Prisma
import bleach
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from .serializers import (
    WhisperSerializer,
    WhisperCreateSerializer,
    WhisperReplySerializer,
    WhisperLikeSerializer,
)
from apps.core.rate_limiting import rate_limit
from apps.social.utils import sync_get_blocked_user_ids
from apps.notifications.views import sync_create_notification

logger = logging.getLogger(__name__)


def sanitize_whisper_content(content: str) -> str:
    """
    Sanitize whisper content to prevent XSS attacks.
    
    Args:
        content: Raw whisper content
        
    Returns:
        Sanitized content safe for rendering
        
    Requirements:
        - 6.10: Sanitize whisper content for XSS prevention
    """
    # Define allowed tags and attributes (more restrictive than story content)
    allowed_tags = ['p', 'br', 'strong', 'em', 'a']
    allowed_attributes = {
        'a': ['href', 'title'],
    }
    
    # Sanitize content
    sanitized = bleach.clean(
        content,
        tags=allowed_tags,
        attributes=allowed_attributes,
        strip=True
    )
    
    return sanitized


@extend_schema(
    tags=['Whispers'],
    summary='List whispers or create new whisper',
    description='''
    **GET**: List whispers with optional scope filtering (global, story-specific, or highlight-specific).
    Supports cursor-based pagination.
    
    **POST**: Create a new whisper. Rate limited to 10 whispers per minute.
    Whispers can be global, linked to a story, or linked to a highlight.
    ''',
    parameters=[
        OpenApiParameter(
            name='scope',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Filter by scope: GLOBAL, STORY, or HIGHLIGHT',
            required=False,
            enum=['GLOBAL', 'STORY', 'HIGHLIGHT'],
        ),
        OpenApiParameter(
            name='story_id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.QUERY,
            description='Filter whispers by story ID (when scope=STORY)',
            required=False,
        ),
        OpenApiParameter(
            name='highlight_id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.QUERY,
            description='Filter whispers by highlight ID (when scope=HIGHLIGHT)',
            required=False,
        ),
        OpenApiParameter(
            name='cursor',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Pagination cursor for next page',
            required=False,
        ),
    ],
    request=WhisperCreateSerializer,
    responses={
        200: WhisperSerializer(many=True),
        201: WhisperSerializer,
        400: OpenApiTypes.OBJECT,
        401: OpenApiTypes.OBJECT,
        429: OpenApiTypes.OBJECT,
    },
    examples=[
        OpenApiExample(
            'Create Global Whisper',
            value={
                'content': 'Just finished reading an amazing chapter!',
                'scope': 'GLOBAL'
            },
            request_only=True,
        ),
        OpenApiExample(
            'Create Story Whisper',
            value={
                'content': 'This story keeps getting better!',
                'scope': 'STORY',
                'story_id': '123e4567-e89b-12d3-a456-426614174000'
            },
            request_only=True,
        ),
    ]
)
@api_view(['GET', 'POST'])
@rate_limit('whisper_create', 10, 60)  # 10 whispers per minute
def whispers(request):
    """
    List whispers or create a new whisper.
    
    GET /v1/whispers - List whispers with scope filter
    POST /v1/whispers - Create whisper
    """
    if request.method == 'POST':
        return _create_whisper(request)
    else:
        return _list_whispers(request)


def _create_whisper(request):
    """
    Create a new whisper.
    
    POST /v1/whispers
    
    Request body:
        - content: Whisper content (required, max 280 chars)
        - media_key: S3 object key for media (optional)
        - scope: GLOBAL, STORY, or HIGHLIGHT (required)
        - story_id: Story ID (required if scope is STORY)
        - highlight_id: Highlight ID (required if scope is HIGHLIGHT)
        
    Returns:
        - 201: Whisper created successfully
        - 400: Invalid input
        - 401: Not authenticated
        - 404: Referenced story or highlight not found
        - 429: Rate limit exceeded
        
    Requirements:
        - 6.1: Create global whisper
        - 6.2: Create story-linked whisper
        - 6.3: Create highlight-linked whisper
        - 6.4: Enforce rate limit (10 per minute)
        - 6.10: Sanitize content for XSS prevention
    """
    # Check authentication
    user_id = getattr(request, 'clerk_user_id', None)
    user_profile = getattr(request, 'user_profile', None)
    
    if not user_id or not user_profile:
        return Response(
            {
                'error': {
                    'code': 'UNAUTHORIZED',
                    'message': 'Authentication required',
                }
            },
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Validate input
    serializer = WhisperCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Invalid input',
                    'details': serializer.errors
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    validated_data = serializer.validated_data
    
    # Sanitize content
    sanitized_content = sanitize_whisper_content(validated_data['content'])
    
    # Query database
    db = Prisma()
    
    try:
        db.connect()
        
        # Validate story_id if provided
        if validated_data.get('story_id'):
            story = db.story.find_unique(where={'id': validated_data['story_id']})
            if not story or story.deleted_at:
                db.disconnect()
                return Response(
                    {
                        'error': {
                            'code': 'NOT_FOUND',
                            'message': 'Story not found',
                        }
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Validate highlight_id if provided
        if validated_data.get('highlight_id'):
            highlight = db.highlight.find_unique(where={'id': validated_data['highlight_id']})
            if not highlight:
                db.disconnect()
                return Response(
                    {
                        'error': {
                            'code': 'NOT_FOUND',
                            'message': 'Highlight not found',
                        }
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Create whisper
        whisper = db.whisper.create(
            data={
                'user_id': user_profile.id,
                'content': sanitized_content,
                'media_key': validated_data.get('media_key'),
                'scope': validated_data['scope'],
                'story_id': validated_data.get('story_id'),
                'highlight_id': validated_data.get('highlight_id'),
            }
        )
        
        db.disconnect()
        
        # Serialize response
        response_serializer = WhisperSerializer(whisper)
        
        return Response(
            {'data': response_serializer.data},
            status=status.HTTP_201_CREATED
        )
        
    except Exception as e:
        logger.error(f"Error creating whisper: {e}")
        db.disconnect()
        return Response(
            {
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to create whisper',
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def _list_whispers(request):
    """
    List whispers with optional scope filter.
    
    GET /v1/whispers?scope=GLOBAL&story_id=xxx
    
    Query parameters:
        - scope: Filter by scope (GLOBAL, STORY, HIGHLIGHT)
        - story_id: Filter by story (for STORY scope)
        - cursor: Pagination cursor
        - page_size: Number of results (default 20, max 100)
        
    Returns:
        - 200: List of whispers
        
    Requirements:
        - 6.6: List global whispers
        - 6.7: List story-specific whispers
        - 6.11: Exclude blocked users from whisper feeds
    """
    # Parse query parameters
    scope_filter = request.query_params.get('scope')
    story_id = request.query_params.get('story_id')
    cursor = request.query_params.get('cursor')
    page_size = min(int(request.query_params.get('page_size', 20)), 100)
    
    # Build where clause
    where = {'deleted_at': None}  # Exclude soft-deleted whispers
    
    if scope_filter:
        where['scope'] = scope_filter
    
    if story_id:
        where['story_id'] = story_id
    
    # Exclude blocked users if authenticated
    user_profile = getattr(request, 'user_profile', None)
    if user_profile:
        blocked_ids = sync_get_blocked_user_ids(user_profile.id)
        if blocked_ids:
            where['user_id'] = {'notIn': blocked_ids}
    
    # Query database
    db = Prisma()
    
    try:
        db.connect()
        
        # Apply cursor pagination
        query_args = {
            'where': where,
            'order': {'created_at': 'desc'},
            'take': page_size + 1,
            'include': {
                'likes': True,
                'replies': {'where': {'deleted_at': None}}
            }
        }
        
        if cursor:
            query_args['cursor'] = {'id': cursor}
            query_args['skip'] = 1
        
        whispers = db.whisper.find_many(**query_args)
        
        # Check if there are more results
        has_next = len(whispers) > page_size
        if has_next:
            whispers = whispers[:page_size]
        
        # Generate next cursor
        next_cursor = whispers[-1].id if has_next and whispers else None
        
        db.disconnect()
        
        # Add counts to whispers
        whispers_data = []
        for whisper in whispers:
            whisper_dict = {
                'id': whisper.id,
                'user_id': whisper.user_id,
                'content': whisper.content,
                'media_key': whisper.media_key,
                'scope': whisper.scope,
                'story_id': whisper.story_id,
                'highlight_id': whisper.highlight_id,
                'parent_id': whisper.parent_id,
                'deleted_at': whisper.deleted_at,
                'created_at': whisper.created_at,
                'reply_count': len(whisper.replies) if hasattr(whisper, 'replies') else 0,
                'like_count': len(whisper.likes) if hasattr(whisper, 'likes') else 0,
            }
            whispers_data.append(whisper_dict)
        
        return Response({
            'data': whispers_data,
            'next_cursor': next_cursor
        })
        
    except Exception as e:
        logger.error(f"Error listing whispers: {e}")
        db.disconnect()
        return Response(
            {
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to list whispers',
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
def delete_whisper(request, whisper_id):
    """
    Soft delete a whisper.
    
    DELETE /v1/whispers/{id}
    
    Returns:
        - 204: Whisper deleted successfully
        - 401: Not authenticated
        - 403: Not authorized (not the whisper author)
        - 404: Whisper not found
        
    Requirements:
        - 6.5: Soft delete whisper
    """
    # Check authentication
    user_id = getattr(request, 'clerk_user_id', None)
    user_profile = getattr(request, 'user_profile', None)
    
    if not user_id or not user_profile:
        return Response(
            {
                'error': {
                    'code': 'UNAUTHORIZED',
                    'message': 'Authentication required',
                }
            },
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Query database
    db = Prisma()
    
    try:
        db.connect()
        
        # Get whisper
        whisper = db.whisper.find_unique(where={'id': whisper_id})
        
        if not whisper or whisper.deleted_at:
            db.disconnect()
            return Response(
                {
                    'error': {
                        'code': 'NOT_FOUND',
                        'message': 'Whisper not found',
                    }
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check authorization
        if whisper.user_id != user_profile.id:
            db.disconnect()
            return Response(
                {
                    'error': {
                        'code': 'FORBIDDEN',
                        'message': 'You are not authorized to delete this whisper',
                    }
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Soft delete whisper
        db.whisper.update(
            where={'id': whisper_id},
            data={'deleted_at': datetime.now()}
        )
        
        db.disconnect()
        
        return Response(status=status.HTTP_204_NO_CONTENT)
        
    except Exception as e:
        logger.error(f"Error deleting whisper: {e}")
        db.disconnect()
        return Response(
            {
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to delete whisper',
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



# Whisper Replies

@api_view(['GET', 'POST'])
@rate_limit('whisper_reply', 20, 60)  # 20 replies per minute
def whisper_replies(request, whisper_id):
    """
    List replies or create a reply to a whisper.
    
    GET /v1/whispers/{id}/replies - List replies
    POST /v1/whispers/{id}/replies - Create reply
    """
    if request.method == 'POST':
        return _create_reply(request, whisper_id)
    else:
        return _list_replies(request, whisper_id)


def _create_reply(request, whisper_id):
    """
    Create a reply to a whisper.
    
    POST /v1/whispers/{id}/replies
    
    Request body:
        - content: Reply content (required, max 280 chars)
        - media_key: S3 object key for media (optional)
        
    Returns:
        - 201: Reply created successfully
        - 400: Invalid input
        - 401: Not authenticated
        - 404: Parent whisper not found
        - 429: Rate limit exceeded
        
    Requirements:
        - 7.1: Create reply with parent_whisper_id
        - 7.6: Enforce rate limit (20 per minute)
    """
    # Check authentication
    user_id = getattr(request, 'clerk_user_id', None)
    user_profile = getattr(request, 'user_profile', None)
    
    if not user_id or not user_profile:
        return Response(
            {
                'error': {
                    'code': 'UNAUTHORIZED',
                    'message': 'Authentication required',
                }
            },
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Validate input
    serializer = WhisperReplySerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Invalid input',
                    'details': serializer.errors
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    validated_data = serializer.validated_data
    
    # Sanitize content
    sanitized_content = sanitize_whisper_content(validated_data['content'])
    
    # Query database
    db = Prisma()
    
    try:
        db.connect()
        
        # Check if parent whisper exists
        parent_whisper = db.whisper.find_unique(where={'id': whisper_id})
        
        if not parent_whisper:
            db.disconnect()
            return Response(
                {
                    'error': {
                        'code': 'NOT_FOUND',
                        'message': 'Parent whisper not found',
                    }
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Create reply (inherit scope from parent)
        reply = db.whisper.create(
            data={
                'user_id': user_profile.id,
                'content': sanitized_content,
                'media_key': validated_data.get('media_key'),
                'scope': parent_whisper.scope,
                'story_id': parent_whisper.story_id,
                'highlight_id': parent_whisper.highlight_id,
                'parent_id': whisper_id,
            }
        )
        
        db.disconnect()
        
        # Create notification for parent whisper author (if not replying to self)
        if parent_whisper.user_id != user_profile.id:
            sync_create_notification(
                user_id=parent_whisper.user_id,
                notification_type='REPLY',
                actor_id=user_profile.id,
                whisper_id=reply.id
            )
        
        # Serialize response
        response_serializer = WhisperSerializer(reply)
        
        return Response(
            {'data': response_serializer.data},
            status=status.HTTP_201_CREATED
        )
        
    except Exception as e:
        logger.error(f"Error creating reply: {e}")
        db.disconnect()
        return Response(
            {
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to create reply',
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def _list_replies(request, whisper_id):
    """
    List replies to a whisper.
    
    GET /v1/whispers/{id}/replies
    
    Query parameters:
        - cursor: Pagination cursor
        - page_size: Number of results (default 20, max 100)
        
    Returns:
        - 200: List of replies
        - 404: Parent whisper not found
        
    Requirements:
        - 7.2: List replies ordered by creation time
    """
    # Parse query parameters
    cursor = request.query_params.get('cursor')
    page_size = min(int(request.query_params.get('page_size', 20)), 100)
    
    # Query database
    db = Prisma()
    
    try:
        db.connect()
        
        # Check if parent whisper exists
        parent_whisper = db.whisper.find_unique(where={'id': whisper_id})
        
        if not parent_whisper:
            db.disconnect()
            return Response(
                {
                    'error': {
                        'code': 'NOT_FOUND',
                        'message': 'Parent whisper not found',
                    }
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get replies
        query_args = {
            'where': {
                'parent_id': whisper_id,
                'deleted_at': None
            },
            'order': {'created_at': 'asc'},  # Chronological order for replies
            'take': page_size + 1,
            'include': {
                'likes': True,
                'replies': {'where': {'deleted_at': None}}
            }
        }
        
        if cursor:
            query_args['cursor'] = {'id': cursor}
            query_args['skip'] = 1
        
        replies = db.whisper.find_many(**query_args)
        
        # Check if there are more results
        has_next = len(replies) > page_size
        if has_next:
            replies = replies[:page_size]
        
        # Generate next cursor
        next_cursor = replies[-1].id if has_next and replies else None
        
        db.disconnect()
        
        # Add counts to replies
        replies_data = []
        for reply in replies:
            reply_dict = {
                'id': reply.id,
                'user_id': reply.user_id,
                'content': reply.content,
                'media_key': reply.media_key,
                'scope': reply.scope,
                'story_id': reply.story_id,
                'highlight_id': reply.highlight_id,
                'parent_id': reply.parent_id,
                'deleted_at': reply.deleted_at,
                'created_at': reply.created_at,
                'reply_count': len(reply.replies) if hasattr(reply, 'replies') else 0,
                'like_count': len(reply.likes) if hasattr(reply, 'likes') else 0,
            }
            replies_data.append(reply_dict)
        
        return Response({
            'data': replies_data,
            'next_cursor': next_cursor
        })
        
    except Exception as e:
        logger.error(f"Error listing replies: {e}")
        db.disconnect()
        return Response(
            {
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to list replies',
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Whisper Likes

@api_view(['POST'])
def like_whisper(request, whisper_id):
    """
    Like a whisper.
    
    POST /v1/whispers/{id}/like
    
    Returns:
        - 201: Whisper liked successfully
        - 401: Not authenticated
        - 404: Whisper not found
        - 409: Already liked
        
    Requirements:
        - 7.3: Like whisper
        - 7.7: Prevent duplicate likes
    """
    # Check authentication
    user_id = getattr(request, 'clerk_user_id', None)
    user_profile = getattr(request, 'user_profile', None)
    
    if not user_id or not user_profile:
        return Response(
            {
                'error': {
                    'code': 'UNAUTHORIZED',
                    'message': 'Authentication required',
                }
            },
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Query database
    db = Prisma()
    
    try:
        db.connect()
        
        # Check if whisper exists
        whisper = db.whisper.find_unique(where={'id': whisper_id})
        
        if not whisper or whisper.deleted_at:
            db.disconnect()
            return Response(
                {
                    'error': {
                        'code': 'NOT_FOUND',
                        'message': 'Whisper not found',
                    }
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if already liked
        existing_like = db.whisperlike.find_unique(
            where={
                'user_id_whisper_id': {
                    'user_id': user_profile.id,
                    'whisper_id': whisper_id
                }
            }
        )
        
        if existing_like:
            db.disconnect()
            return Response(
                {
                    'error': {
                        'code': 'CONFLICT',
                        'message': 'You have already liked this whisper',
                    }
                },
                status=status.HTTP_409_CONFLICT
            )
        
        # Create like
        like = db.whisperlike.create(
            data={
                'user_id': user_profile.id,
                'whisper_id': whisper_id
            }
        )
        
        db.disconnect()
        
        # Serialize response
        serializer = WhisperLikeSerializer(like)
        
        return Response(
            {'data': serializer.data},
            status=status.HTTP_201_CREATED
        )
        
    except Exception as e:
        logger.error(f"Error liking whisper: {e}")
        db.disconnect()
        return Response(
            {
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to like whisper',
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
def unlike_whisper(request, whisper_id):
    """
    Unlike a whisper.
    
    DELETE /v1/whispers/{id}/like
    
    Returns:
        - 204: Whisper unliked successfully
        - 401: Not authenticated
        - 404: Whisper or like not found
        
    Requirements:
        - 7.4: Unlike whisper
    """
    # Check authentication
    user_id = getattr(request, 'clerk_user_id', None)
    user_profile = getattr(request, 'user_profile', None)
    
    if not user_id or not user_profile:
        return Response(
            {
                'error': {
                    'code': 'UNAUTHORIZED',
                    'message': 'Authentication required',
                }
            },
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Query database
    db = Prisma()
    
    try:
        db.connect()
        
        # Check if whisper exists
        whisper = db.whisper.find_unique(where={'id': whisper_id})
        
        if not whisper or whisper.deleted_at:
            db.disconnect()
            return Response(
                {
                    'error': {
                        'code': 'NOT_FOUND',
                        'message': 'Whisper not found',
                    }
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Find like
        like = db.whisperlike.find_unique(
            where={
                'user_id_whisper_id': {
                    'user_id': user_profile.id,
                    'whisper_id': whisper_id
                }
            }
        )
        
        if not like:
            db.disconnect()
            return Response(
                {
                    'error': {
                        'code': 'NOT_FOUND',
                        'message': 'Like not found',
                    }
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Delete like
        db.whisperlike.delete(where={'id': like.id})
        
        db.disconnect()
        
        return Response(status=status.HTTP_204_NO_CONTENT)
        
    except Exception as e:
        logger.error(f"Error unliking whisper: {e}")
        db.disconnect()
        return Response(
            {
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to unlike whisper',
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
