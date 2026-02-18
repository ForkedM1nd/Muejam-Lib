"""Views for story and chapter management."""
import logging
import asyncio
from datetime import datetime
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from prisma import Prisma
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from .serializers import (
    StoryListSerializer,
    StoryDetailSerializer,
    StoryCreateSerializer,
    StoryUpdateSerializer,
    ChapterListSerializer,
    ChapterDetailSerializer,
    ChapterCreateSerializer,
    ChapterUpdateSerializer,
    generate_slug,
)
from apps.core.rate_limiting import rate_limit, require_captcha
from apps.core.content_sanitizer import ContentSanitizer
from apps.core.pii_middleware import detect_pii_in_content
from apps.social.utils import sync_get_blocked_user_ids
from apps.moderation.content_filter_integration import ContentFilterIntegration

logger = logging.getLogger(__name__)


@extend_schema(
    tags=['Stories'],
    summary='List stories or create new story',
    description='''
    **GET**: List published stories with optional filters (tag, author, search query).
    Supports cursor-based pagination for infinite scroll.
    
    **POST**: Create a new story draft. Requires authentication.
    Story will be created in draft state (published=false).
    ''',
    parameters=[
        OpenApiParameter(
            name='tag',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Filter stories by tag slug',
            required=False,
        ),
        OpenApiParameter(
            name='author_id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.QUERY,
            description='Filter stories by author ID',
            required=False,
        ),
        OpenApiParameter(
            name='search',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Search stories by title, blurb, or author name',
            required=False,
        ),
        OpenApiParameter(
            name='cursor',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Pagination cursor for next page',
            required=False,
        ),
        OpenApiParameter(
            name='page_size',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='Number of items per page (max 100, default 20)',
            required=False,
        ),
    ],
    request=StoryCreateSerializer,
    responses={
        200: StoryListSerializer(many=True),
        201: StoryDetailSerializer,
        400: OpenApiTypes.OBJECT,
        401: OpenApiTypes.OBJECT,
    },
    examples=[
        OpenApiExample(
            'Create Story Request',
            value={
                'title': 'The Chronicles of Aether',
                'blurb': 'A fantasy epic about magic and destiny',
                'cover_key': 'covers/uuid-here.jpg'
            },
            request_only=True,
        ),
    ]
)
@api_view(['GET', 'POST'])
@require_captcha  # Validate reCAPTCHA token for POST requests (Requirement 5.4)
@detect_pii_in_content(content_fields=['title', 'blurb'])  # Detect PII in story content (Requirements 9.1, 9.2, 9.3, 9.4)
def stories_list_create(request):
    """
    List stories or create a new story draft.
    
    GET /v1/stories - List stories with filters
    POST /v1/stories - Create new story
    """
    if request.method == 'POST':
        return _create_story(request)
    else:
        return _list_stories(request)


def _create_story(request):
    """
    Create a new story draft.
    
    POST /v1/stories
    
    Request body:
        - title: Story title (required)
        - blurb: Story description (required)
        - cover_key: S3 object key for cover image (optional)
        
    Returns:
        - 201: Story created successfully
        - 400: Invalid input or content blocked by filters
        - 401: Not authenticated
        - 409: Slug already exists
        
    Requirements:
        - 5.1: Create story draft with published=false
        - 4.1: Filter profanity
        - 4.2: Block spam patterns
        - 4.3: Return appropriate errors for blocked content
        - 4.4: Create high-priority reports for hate speech
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
    serializer = StoryCreateSerializer(data=request.data)
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
    
    # Sanitize blurb using centralized ContentSanitizer (Requirement 6.8)
    sanitized_blurb = ContentSanitizer.sanitize_rich_content(validated_data['blurb'])
    
    # Generate slug from title
    base_slug = generate_slug(validated_data['title'])
    slug = base_slug
    
    # Create story in database
    db = Prisma()
    
    try:
        db.connect()
        
        # Run content filters on title and blurb (Requirement 4.1, 4.2, 4.3, 4.4)
        filter_integration = ContentFilterIntegration(db)
        
        # Filter title
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            title_filter_result = loop.run_until_complete(
                filter_integration.filter_and_validate_content(
                    content=validated_data['title'],
                    content_type='story'
                )
            )
        finally:
            loop.close()
        
        # Block if title is problematic
        if title_filter_result['blocked']:
            db.disconnect()
            return Response(
                {
                    'error': {
                        'code': 'CONTENT_BLOCKED',
                        'message': f"Story title blocked: {title_filter_result['error_message']}",
                        'flags': title_filter_result['flags']
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Filter blurb
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            blurb_filter_result = loop.run_until_complete(
                filter_integration.filter_and_validate_content(
                    content=sanitized_blurb,
                    content_type='story'
                )
            )
        finally:
            loop.close()
        
        # Block if blurb is problematic
        if blurb_filter_result['blocked']:
            db.disconnect()
            return Response(
                {
                    'error': {
                        'code': 'CONTENT_BLOCKED',
                        'message': f"Story description blocked: {blurb_filter_result['error_message']}",
                        'flags': blurb_filter_result['flags']
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Ensure slug uniqueness by appending numbers if needed
        counter = 1
        while True:
            existing = db.story.find_unique(where={'slug': slug})
            if not existing:
                break
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        # Create story
        story = db.story.create(
            data={
                'title': validated_data['title'],
                'blurb': sanitized_blurb,
                'cover_key': validated_data.get('cover_key'),
                'slug': slug,
                'author_id': user_profile.id,
                'published': False,
            }
        )
        
        # Handle manual NSFW marking (Requirement 8.3)
        if validated_data.get('mark_as_nsfw', False):
            from apps.moderation.nsfw_service import get_nsfw_service
            from prisma.enums import NSFWContentType
            
            nsfw_service = get_nsfw_service()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(
                    nsfw_service.mark_content_as_nsfw(
                        content_type=NSFWContentType.STORY,
                        content_id=story.id,
                        user_id=user_profile.id,
                        is_manual=False  # USER_MARKED
                    )
                )
            finally:
                loop.close()
        
        # Handle automated actions for title
        if title_filter_result.get('auto_actions'):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(
                    filter_integration.handle_auto_actions(
                        content_type='story',
                        content_id=story.id,
                        auto_actions=title_filter_result['auto_actions'],
                        filter_details=title_filter_result['details']
                    )
                )
            finally:
                loop.close()
        
        # Handle automated actions for blurb
        if blurb_filter_result.get('auto_actions'):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(
                    filter_integration.handle_auto_actions(
                        content_type='story',
                        content_id=story.id,
                        auto_actions=blurb_filter_result['auto_actions'],
                        filter_details=blurb_filter_result['details']
                    )
                )
            finally:
                loop.close()
        
        db.disconnect()
        
        # Serialize response
        response_serializer = StoryDetailSerializer(story)
        
        return Response(
            {'data': response_serializer.data},
            status=status.HTTP_201_CREATED
        )
        
    except Exception as e:
        logger.error(f"Error creating story: {e}")
        db.disconnect()
        return Response(
            {
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to create story',
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def _list_stories(request):
    """
    List stories with optional filters.
    
    GET /v1/stories?published=true&author_id=xxx
    
    Query parameters:
        - published: Filter by published status (optional)
        - author_id: Filter by author (optional)
        - cursor: Pagination cursor (optional)
        - page_size: Number of results (default 20, max 100)
        
    Returns:
        - 200: List of stories
        
    Requirements:
        - 5.1: List stories with filters
        - 11.5: Exclude blocked users from content feeds
    """
    # Parse query parameters
    published_filter = request.query_params.get('published')
    author_id = request.query_params.get('author_id')
    cursor = request.query_params.get('cursor')
    page_size = min(int(request.query_params.get('page_size', 20)), 100)
    
    # Build where clause
    where = {'deleted_at': None}  # Exclude soft-deleted stories
    
    if published_filter is not None:
        where['published'] = published_filter.lower() == 'true'
    
    if author_id:
        where['author_id'] = author_id
    
    # Exclude blocked users if authenticated
    user_profile = getattr(request, 'user_profile', None)
    if user_profile:
        blocked_ids = sync_get_blocked_user_ids(user_profile.id)
        if blocked_ids:
            where['author_id'] = {'notIn': blocked_ids}
    
    # Query database
    db = Prisma()
    
    try:
        db.connect()
        
        # Apply cursor pagination
        query_args = {
            'where': where,
            'order': {'created_at': 'desc'},
            'take': page_size + 1,  # Fetch one extra to check if there's more
        }
        
        if cursor:
            query_args['cursor'] = {'id': cursor}
            query_args['skip'] = 1  # Skip the cursor item itself
        
        stories = db.story.find_many(**query_args)
        
        # Check if there are more results
        has_next = len(stories) > page_size
        if has_next:
            stories = stories[:page_size]
        
        # Generate next cursor
        next_cursor = stories[-1].id if has_next and stories else None
        
        db.disconnect()
        
        # Serialize response
        serializer = StoryListSerializer(stories, many=True)
        
        return Response({
            'data': serializer.data,
            'next_cursor': next_cursor
        })
        
    except Exception as e:
        logger.error(f"Error listing stories: {e}")
        db.disconnect()
        return Response(
            {
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to list stories',
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_story_by_slug(request, slug):
    """
    Get a story by its slug.
    
    GET /v1/stories/{slug}
    
    Returns:
        - 200: Story details
        - 404: Story not found or deleted
        - 403: Access denied (blocked author)
        
    Requirements:
        - 5.1: Get story by slug
        - 3.9: Hide content from blocked authors
    """
    db = Prisma()
    
    try:
        db.connect()
        
        story = db.story.find_unique(
            where={'slug': slug},
            include={'author': True}
        )
        
        db.disconnect()
        
        if not story or story.deleted_at:
            return Response(
                {
                    'error': {
                        'code': 'NOT_FOUND',
                        'message': 'Story not found',
                    }
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if author is blocked by current user
        user_profile = getattr(request, 'user_profile', None)
        if user_profile:
            blocked_ids = sync_get_blocked_user_ids(user_profile.id)
            if story.author_id in blocked_ids:
                return Response(
                    {
                        'error': {
                            'code': 'FORBIDDEN',
                            'message': 'Access denied',
                        }
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Serialize response
        serializer = StoryDetailSerializer(story)
        
        return Response({'data': serializer.data})
        
    except Exception as e:
        logger.error(f"Error getting story: {e}")
        db.disconnect()
        return Response(
            {
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to get story',
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT'])
@require_captcha  # Validate reCAPTCHA token (Requirement 5.4)
@detect_pii_in_content(content_fields=['title', 'blurb'])  # Detect PII in story content (Requirements 9.1, 9.2, 9.3, 9.4)
def update_story(request, story_id):
    """
    Update a story draft.
    
    PUT /v1/stories/{id}
    
    Request body:
        - title: Story title (optional)
        - blurb: Story description (optional)
        - cover_key: S3 object key for cover image (optional)
        
    Returns:
        - 200: Story updated successfully
        - 400: Invalid input or PII detected
        - 401: Not authenticated
        - 403: Not authorized (not the author)
        - 404: Story not found
        
    Requirements:
        - 5.5: Update draft without affecting publication status
        - 9.1-9.4: PII detection and protection
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
    serializer = StoryUpdateSerializer(data=request.data)
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
    
    # Query database
    db = Prisma()
    
    try:
        db.connect()
        
        # Get story
        story = db.story.find_unique(where={'id': story_id})
        
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
        
        # Check authorization
        if story.author_id != user_profile.id:
            db.disconnect()
            return Response(
                {
                    'error': {
                        'code': 'FORBIDDEN',
                        'message': 'You are not authorized to update this story',
                    }
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Prepare update data
        update_data = {}
        
        if 'title' in validated_data:
            update_data['title'] = validated_data['title']
            # Regenerate slug if title changed
            base_slug = generate_slug(validated_data['title'])
            slug = base_slug
            counter = 1
            while True:
                existing = db.story.find_unique(where={'slug': slug})
                if not existing or existing.id == story_id:
                    break
                slug = f"{base_slug}-{counter}"
                counter += 1
            update_data['slug'] = slug
        
        if 'blurb' in validated_data:
            update_data['blurb'] = ContentSanitizer.sanitize_rich_content(validated_data['blurb'])
        
        if 'cover_key' in validated_data:
            update_data['cover_key'] = validated_data['cover_key']
        
        # Update story
        updated_story = db.story.update(
            where={'id': story_id},
            data=update_data
        )
        
        # Handle manual NSFW marking (Requirement 8.3)
        if 'mark_as_nsfw' in validated_data:
            from apps.moderation.nsfw_service import get_nsfw_service
            from prisma.enums import NSFWContentType
            
            nsfw_service = get_nsfw_service()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                if validated_data['mark_as_nsfw']:
                    # Mark as NSFW
                    loop.run_until_complete(
                        nsfw_service.mark_content_as_nsfw(
                            content_type=NSFWContentType.STORY,
                            content_id=story_id,
                            user_id=user_profile.id,
                            is_manual=False  # USER_MARKED
                        )
                    )
                else:
                    # Remove NSFW flag if user unmarked it
                    loop.run_until_complete(
                        nsfw_service.create_nsfw_flag(
                            content_type=NSFWContentType.STORY,
                            content_id=story_id,
                            is_nsfw=False,
                            detection_method='USER_MARKED',
                            flagged_by=user_profile.id
                        )
                    )
            finally:
                loop.close()
        
        db.disconnect()
        
        # Serialize response
        response_serializer = StoryDetailSerializer(updated_story)
        
        return Response({'data': response_serializer.data})
        
    except Exception as e:
        logger.error(f"Error updating story: {e}")
        db.disconnect()
        return Response(
            {
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to update story',
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
def delete_story(request, story_id):
    """
    Soft delete a story.
    
    DELETE /v1/stories/{id}
    
    Returns:
        - 204: Story deleted successfully
        - 401: Not authenticated
        - 403: Not authorized (not the author)
        - 404: Story not found
        
    Requirements:
        - 5.6: Soft delete by setting deleted_at timestamp
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
        
        # Get story
        story = db.story.find_unique(where={'id': story_id})
        
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
        
        # Check authorization
        if story.author_id != user_profile.id:
            db.disconnect()
            return Response(
                {
                    'error': {
                        'code': 'FORBIDDEN',
                        'message': 'You are not authorized to delete this story',
                    }
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Soft delete story
        db.story.update(
            where={'id': story_id},
            data={'deleted_at': datetime.now()}
        )
        
        db.disconnect()
        
        return Response(status=status.HTTP_204_NO_CONTENT)
        
    except Exception as e:
        logger.error(f"Error deleting story: {e}")
        db.disconnect()
        return Response(
            {
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to delete story',
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@require_captcha  # Validate reCAPTCHA token (Requirement 5.4)
@rate_limit('story_publish', 5, 3600)  # 5 publishes per hour
def publish_story(request, story_id):
    """
    Publish a story.
    
    POST /v1/stories/{id}/publish
    
    Returns:
        - 200: Story published successfully
        - 401: Not authenticated
        - 403: Not authorized (not the author)
        - 404: Story not found
        - 429: Rate limit exceeded
        
    Requirements:
        - 5.3: Set published=true and record publication timestamp
        - 5.8: Enforce rate limit of 5 publish operations per hour
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
        
        # Get story
        story = db.story.find_unique(where={'id': story_id})
        
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
        
        # Check authorization
        if story.author_id != user_profile.id:
            db.disconnect()
            return Response(
                {
                    'error': {
                        'code': 'FORBIDDEN',
                        'message': 'You are not authorized to publish this story',
                    }
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Publish story
        updated_story = db.story.update(
            where={'id': story_id},
            data={
                'published': True,
                'published_at': datetime.now() if not story.published else story.published_at
            }
        )
        
        db.disconnect()
        
        # Serialize response
        serializer = StoryDetailSerializer(updated_story)
        
        return Response({'data': serializer.data})
        
    except Exception as e:
        logger.error(f"Error publishing story: {e}")
        db.disconnect()
        return Response(
            {
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to publish story',
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



@api_view(['GET'])
def list_chapters(request, story_id):
    """
    List chapters for a story.
    
    GET /v1/stories/{id}/chapters
    
    Query parameters:
        - cursor: Pagination cursor (optional)
        - page_size: Number of results (default 20, max 100)
        
    Returns:
        - 200: List of chapters
        - 404: Story not found
        
    Requirements:
        - 5.2: List chapters for a story
    """
    # Parse query parameters
    cursor = request.query_params.get('cursor')
    page_size = min(int(request.query_params.get('page_size', 20)), 100)
    
    # Query database
    db = Prisma()
    
    try:
        db.connect()
        
        # Check if story exists
        story = db.story.find_unique(where={'id': story_id})
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
        
        # Build where clause
        where = {
            'story_id': story_id,
            'deleted_at': None  # Exclude soft-deleted chapters
        }
        
        # Apply cursor pagination
        query_args = {
            'where': where,
            'order': {'chapter_number': 'asc'},
            'take': page_size + 1,
        }
        
        if cursor:
            query_args['cursor'] = {'id': cursor}
            query_args['skip'] = 1
        
        chapters = db.chapter.find_many(**query_args)
        
        # Check if there are more results
        has_next = len(chapters) > page_size
        if has_next:
            chapters = chapters[:page_size]
        
        # Generate next cursor
        next_cursor = chapters[-1].id if has_next and chapters else None
        
        db.disconnect()
        
        # Serialize response
        serializer = ChapterListSerializer(chapters, many=True)
        
        return Response({
            'data': serializer.data,
            'next_cursor': next_cursor
        })
        
    except Exception as e:
        logger.error(f"Error listing chapters: {e}")
        db.disconnect()
        return Response(
            {
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to list chapters',
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_chapter(request, chapter_id):
    """
    Get a chapter by ID.
    
    GET /v1/chapters/{id}
    
    Returns:
        - 200: Chapter details with content
        - 404: Chapter not found or deleted
        
    Requirements:
        - 5.2: Get chapter content
    """
    db = Prisma()
    
    try:
        db.connect()
        
        chapter = db.chapter.find_unique(
            where={'id': chapter_id},
            include={'story': True}
        )
        
        db.disconnect()
        
        if not chapter or chapter.deleted_at:
            return Response(
                {
                    'error': {
                        'code': 'NOT_FOUND',
                        'message': 'Chapter not found',
                    }
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Serialize response
        serializer = ChapterDetailSerializer(chapter)
        
        return Response({'data': serializer.data})
        
    except Exception as e:
        logger.error(f"Error getting chapter: {e}")
        db.disconnect()
        return Response(
            {
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to get chapter',
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@require_captcha  # Validate reCAPTCHA token (Requirement 5.4)
@detect_pii_in_content(content_fields=['title', 'content'])  # Detect PII in chapter content (Requirements 9.1, 9.2, 9.3, 9.4)
def create_chapter(request, story_id):
    """
    Create a new chapter draft.
    
    POST /v1/stories/{id}/chapters
    
    Request body:
        - title: Chapter title (required)
        - content: Chapter content in markdown (required)
        - chapter_number: Chapter number (required)
        
    Returns:
        - 201: Chapter created successfully
        - 400: Invalid input, PII detected, or content blocked by filters
        - 401: Not authenticated
        - 403: Not authorized (not the story author)
        - 404: Story not found
        - 409: Chapter number already exists
        
    Requirements:
        - 5.2: Create chapter draft with published=false
        - 4.1: Filter profanity
        - 4.2: Block spam patterns
        - 4.3: Return appropriate errors for blocked content
        - 4.4: Create high-priority reports for hate speech
        - 9.1-9.4: PII detection and protection
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
    serializer = ChapterCreateSerializer(data=request.data)
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
    
    # Sanitize content using centralized ContentSanitizer (Requirement 6.8)
    sanitized_content = ContentSanitizer.sanitize_rich_content(validated_data['content'])
    
    # Query database
    db = Prisma()
    
    try:
        db.connect()
        
        # Get story
        story = db.story.find_unique(where={'id': story_id})
        
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
        
        # Check authorization
        if story.author_id != user_profile.id:
            db.disconnect()
            return Response(
                {
                    'error': {
                        'code': 'FORBIDDEN',
                        'message': 'You are not authorized to create chapters for this story',
                    }
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if chapter number already exists
        existing_chapter = db.chapter.find_first(
            where={
                'story_id': story_id,
                'chapter_number': validated_data['chapter_number'],
                'deleted_at': None
            }
        )
        
        if existing_chapter:
            db.disconnect()
            return Response(
                {
                    'error': {
                        'code': 'CONFLICT',
                        'message': f"Chapter number {validated_data['chapter_number']} already exists for this story",
                    }
                },
                status=status.HTTP_409_CONFLICT
            )
        
        # Run content filters on title and content (Requirement 4.1, 4.2, 4.3, 4.4)
        filter_integration = ContentFilterIntegration(db)
        
        # Filter title
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            title_filter_result = loop.run_until_complete(
                filter_integration.filter_and_validate_content(
                    content=validated_data['title'],
                    content_type='chapter'
                )
            )
        finally:
            loop.close()
        
        # Block if title is problematic
        if title_filter_result['blocked']:
            db.disconnect()
            return Response(
                {
                    'error': {
                        'code': 'CONTENT_BLOCKED',
                        'message': f"Chapter title blocked: {title_filter_result['error_message']}",
                        'flags': title_filter_result['flags']
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Filter content
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            content_filter_result = loop.run_until_complete(
                filter_integration.filter_and_validate_content(
                    content=sanitized_content,
                    content_type='chapter'
                )
            )
        finally:
            loop.close()
        
        # Block if content is problematic
        if content_filter_result['blocked']:
            db.disconnect()
            return Response(
                {
                    'error': {
                        'code': 'CONTENT_BLOCKED',
                        'message': f"Chapter content blocked: {content_filter_result['error_message']}",
                        'flags': content_filter_result['flags']
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create chapter
        chapter = db.chapter.create(
            data={
                'story_id': story_id,
                'title': validated_data['title'],
                'content': sanitized_content,
                'chapter_number': validated_data['chapter_number'],
                'published': False,
            }
        )
        
        # Handle manual NSFW marking (Requirement 8.3)
        if validated_data.get('mark_as_nsfw', False):
            from apps.moderation.nsfw_service import get_nsfw_service
            from prisma.enums import NSFWContentType
            
            nsfw_service = get_nsfw_service()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(
                    nsfw_service.mark_content_as_nsfw(
                        content_type=NSFWContentType.CHAPTER,
                        content_id=chapter.id,
                        user_id=user_profile.id,
                        is_manual=False  # USER_MARKED
                    )
                )
            finally:
                loop.close()
        
        # Handle automated actions for title
        if title_filter_result.get('auto_actions'):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(
                    filter_integration.handle_auto_actions(
                        content_type='chapter',
                        content_id=chapter.id,
                        auto_actions=title_filter_result['auto_actions'],
                        filter_details=title_filter_result['details']
                    )
                )
            finally:
                loop.close()
        
        # Handle automated actions for content
        if content_filter_result.get('auto_actions'):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(
                    filter_integration.handle_auto_actions(
                        content_type='chapter',
                        content_id=chapter.id,
                        auto_actions=content_filter_result['auto_actions'],
                        filter_details=content_filter_result['details']
                    )
                )
            finally:
                loop.close()
        
        db.disconnect()
        
        # Serialize response
        response_serializer = ChapterDetailSerializer(chapter)
        
        return Response(
            {'data': response_serializer.data},
            status=status.HTTP_201_CREATED
        )
        
    except Exception as e:
        logger.error(f"Error creating chapter: {e}")
        db.disconnect()
        return Response(
            {
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to create chapter',
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT'])
@require_captcha  # Validate reCAPTCHA token (Requirement 5.4)
@detect_pii_in_content(content_fields=['title', 'content'])  # Detect PII in chapter content (Requirements 9.1, 9.2, 9.3, 9.4)
def update_chapter(request, chapter_id):
    """
    Update a chapter draft.
    
    PUT /v1/chapters/{id}
    
    Request body:
        - title: Chapter title (optional)
        - content: Chapter content in markdown (optional)
        
    Returns:
        - 200: Chapter updated successfully
        - 400: Invalid input or PII detected
        - 401: Not authenticated
        - 403: Not authorized (not the story author)
        - 404: Chapter not found
        
    Requirements:
        - 5.4: Update draft without affecting publication status
        - 9.1-9.4: PII detection and protection
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
    serializer = ChapterUpdateSerializer(data=request.data)
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
    
    # Query database
    db = Prisma()
    
    try:
        db.connect()
        
        # Get chapter with story
        chapter = db.chapter.find_unique(
            where={'id': chapter_id},
            include={'story': True}
        )
        
        if not chapter or chapter.deleted_at:
            db.disconnect()
            return Response(
                {
                    'error': {
                        'code': 'NOT_FOUND',
                        'message': 'Chapter not found',
                    }
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check authorization
        if chapter.story.author_id != user_profile.id:
            db.disconnect()
            return Response(
                {
                    'error': {
                        'code': 'FORBIDDEN',
                        'message': 'You are not authorized to update this chapter',
                    }
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Prepare update data
        update_data = {}
        
        if 'title' in validated_data:
            update_data['title'] = validated_data['title']
        
        if 'content' in validated_data:
            update_data['content'] = ContentSanitizer.sanitize_rich_content(validated_data['content'])
        
        # Update chapter
        updated_chapter = db.chapter.update(
            where={'id': chapter_id},
            data=update_data
        )
        
        # Handle manual NSFW marking (Requirement 8.3)
        if 'mark_as_nsfw' in validated_data:
            from apps.moderation.nsfw_service import get_nsfw_service
            from prisma.enums import NSFWContentType
            
            nsfw_service = get_nsfw_service()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                if validated_data['mark_as_nsfw']:
                    # Mark as NSFW
                    loop.run_until_complete(
                        nsfw_service.mark_content_as_nsfw(
                            content_type=NSFWContentType.CHAPTER,
                            content_id=chapter_id,
                            user_id=user_profile.id,
                            is_manual=False  # USER_MARKED
                        )
                    )
                else:
                    # Remove NSFW flag if user unmarked it
                    loop.run_until_complete(
                        nsfw_service.create_nsfw_flag(
                            content_type=NSFWContentType.CHAPTER,
                            content_id=chapter_id,
                            is_nsfw=False,
                            detection_method='USER_MARKED',
                            flagged_by=user_profile.id
                        )
                    )
            finally:
                loop.close()
        
        db.disconnect()
        
        # Serialize response
        response_serializer = ChapterDetailSerializer(updated_chapter)
        
        return Response({'data': response_serializer.data})
        
    except Exception as e:
        logger.error(f"Error updating chapter: {e}")
        db.disconnect()
        return Response(
            {
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to update chapter',
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
def delete_chapter(request, chapter_id):
    """
    Soft delete a chapter.
    
    DELETE /v1/chapters/{id}
    
    Returns:
        - 204: Chapter deleted successfully
        - 401: Not authenticated
        - 403: Not authorized (not the story author)
        - 404: Chapter not found
        
    Requirements:
        - 5.7: Soft delete by setting deleted_at timestamp
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
        
        # Get chapter with story
        chapter = db.chapter.find_unique(
            where={'id': chapter_id},
            include={'story': True}
        )
        
        if not chapter or chapter.deleted_at:
            db.disconnect()
            return Response(
                {
                    'error': {
                        'code': 'NOT_FOUND',
                        'message': 'Chapter not found',
                    }
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check authorization
        if chapter.story.author_id != user_profile.id:
            db.disconnect()
            return Response(
                {
                    'error': {
                        'code': 'FORBIDDEN',
                        'message': 'You are not authorized to delete this chapter',
                    }
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Soft delete chapter
        db.chapter.update(
            where={'id': chapter_id},
            data={'deleted_at': datetime.now()}
        )
        
        db.disconnect()
        
        return Response(status=status.HTTP_204_NO_CONTENT)
        
    except Exception as e:
        logger.error(f"Error deleting chapter: {e}")
        db.disconnect()
        return Response(
            {
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to delete chapter',
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@require_captcha  # Validate reCAPTCHA token (Requirement 5.4)
@rate_limit('chapter_publish', 5, 3600)  # 5 publishes per hour
def publish_chapter(request, chapter_id):
    """
    Publish a chapter.
    
    POST /v1/chapters/{id}/publish
    
    Returns:
        - 200: Chapter published successfully
        - 401: Not authenticated
        - 403: Not authorized (not the story author)
        - 404: Chapter not found
        - 429: Rate limit exceeded
        
    Requirements:
        - 5.4: Set published=true and record publication timestamp
        - 5.8: Enforce rate limit of 5 publish operations per hour
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
        
        # Get chapter with story
        chapter = db.chapter.find_unique(
            where={'id': chapter_id},
            include={'story': True}
        )
        
        if not chapter or chapter.deleted_at:
            db.disconnect()
            return Response(
                {
                    'error': {
                        'code': 'NOT_FOUND',
                        'message': 'Chapter not found',
                    }
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check authorization
        if chapter.story.author_id != user_profile.id:
            db.disconnect()
            return Response(
                {
                    'error': {
                        'code': 'FORBIDDEN',
                        'message': 'You are not authorized to publish this chapter',
                    }
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Publish chapter
        updated_chapter = db.chapter.update(
            where={'id': chapter_id},
            data={
                'published': True,
                'published_at': datetime.now() if not chapter.published else chapter.published_at
            }
        )
        
        db.disconnect()
        
        # Serialize response
        serializer = ChapterDetailSerializer(updated_chapter)
        
        return Response({'data': serializer.data})
        
    except Exception as e:
        logger.error(f"Error publishing chapter: {e}")
        db.disconnect()
        return Response(
            {
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to publish chapter',
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



# Reading Progress and Bookmarks

@api_view(['GET', 'POST'])
def reading_progress(request, chapter_id):
    """
    Get or update reading progress for a chapter.
    
    GET /v1/chapters/{id}/progress - Get reading progress
    POST /v1/chapters/{id}/progress - Update reading progress
    """
    if request.method == 'POST':
        return _update_reading_progress(request, chapter_id)
    else:
        return _get_reading_progress(request, chapter_id)


def _update_reading_progress(request, chapter_id):
    """
    Update reading progress for a chapter.
    
    POST /v1/chapters/{id}/progress
    
    Request body:
        - offset: Character offset in the chapter (required)
        
    Returns:
        - 200: Progress updated successfully
        - 400: Invalid input
        - 401: Not authenticated
        - 404: Chapter not found
        
    Requirements:
        - 3.4: Track reading progress as character offset
        - 3.5: Allow retrieval of last position
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
    from .serializers import ReadingProgressUpdateSerializer
    serializer = ReadingProgressUpdateSerializer(data=request.data)
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
    
    # Query database
    db = Prisma()
    
    try:
        db.connect()
        
        # Check if chapter exists
        chapter = db.chapter.find_unique(where={'id': chapter_id})
        
        if not chapter or chapter.deleted_at:
            db.disconnect()
            return Response(
                {
                    'error': {
                        'code': 'NOT_FOUND',
                        'message': 'Chapter not found',
                    }
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Upsert reading progress (create or update)
        progress = db.readingprogress.upsert(
            where={
                'user_id_chapter_id': {
                    'user_id': user_profile.id,
                    'chapter_id': chapter_id
                }
            },
            data={
                'create': {
                    'user_id': user_profile.id,
                    'chapter_id': chapter_id,
                    'offset': validated_data['offset']
                },
                'update': {
                    'offset': validated_data['offset']
                }
            }
        )
        
        db.disconnect()
        
        # Serialize response
        from .serializers import ReadingProgressSerializer
        response_serializer = ReadingProgressSerializer(progress)
        
        return Response({'data': response_serializer.data})
        
    except Exception as e:
        logger.error(f"Error updating reading progress: {e}")
        db.disconnect()
        return Response(
            {
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to update reading progress',
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def _get_reading_progress(request, chapter_id):
    """
    Get reading progress for a chapter.
    
    GET /v1/chapters/{id}/progress
    
    Returns:
        - 200: Progress retrieved successfully
        - 401: Not authenticated
        - 404: Chapter or progress not found
        
    Requirements:
        - 3.5: Restore last reading progress position
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
        
        # Check if chapter exists
        chapter = db.chapter.find_unique(where={'id': chapter_id})
        
        if not chapter or chapter.deleted_at:
            db.disconnect()
            return Response(
                {
                    'error': {
                        'code': 'NOT_FOUND',
                        'message': 'Chapter not found',
                    }
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get reading progress
        progress = db.readingprogress.find_unique(
            where={
                'user_id_chapter_id': {
                    'user_id': user_profile.id,
                    'chapter_id': chapter_id
                }
            }
        )
        
        db.disconnect()
        
        if not progress:
            return Response(
                {
                    'error': {
                        'code': 'NOT_FOUND',
                        'message': 'No reading progress found for this chapter',
                    }
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Serialize response
        from .serializers import ReadingProgressSerializer
        serializer = ReadingProgressSerializer(progress)
        
        return Response({'data': serializer.data})
        
    except Exception as e:
        logger.error(f"Error getting reading progress: {e}")
        db.disconnect()
        return Response(
            {
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to get reading progress',
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET', 'POST'])
def bookmarks(request, chapter_id):
    """
    List bookmarks or create a new bookmark for a chapter.
    
    GET /v1/chapters/{id}/bookmarks - List bookmarks
    POST /v1/chapters/{id}/bookmarks - Create bookmark
    """
    if request.method == 'POST':
        return _create_bookmark(request, chapter_id)
    else:
        return _list_bookmarks(request, chapter_id)


def _create_bookmark(request, chapter_id):
    """
    Update reading progress for a chapter.
    
    POST /v1/chapters/{id}/progress
    
    Request body:
        - offset: Character offset in the chapter (required)
        
    Returns:
        - 200: Progress updated successfully
        - 400: Invalid input
        - 401: Not authenticated
        - 404: Chapter not found
        
    Requirements:
        - 3.4: Track reading progress as character offset
        - 3.5: Allow retrieval of last position
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
    from .serializers import ReadingProgressUpdateSerializer
    serializer = ReadingProgressUpdateSerializer(data=request.data)
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
    
    # Query database
    db = Prisma()
    
    try:
        db.connect()
        
        # Check if chapter exists
        chapter = db.chapter.find_unique(where={'id': chapter_id})
        
        if not chapter or chapter.deleted_at:
            db.disconnect()
            return Response(
                {
                    'error': {
                        'code': 'NOT_FOUND',
                        'message': 'Chapter not found',
                    }
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Upsert reading progress (create or update)
        progress = db.readingprogress.upsert(
            where={
                'user_id_chapter_id': {
                    'user_id': user_profile.id,
                    'chapter_id': chapter_id
                }
            },
            data={
                'create': {
                    'user_id': user_profile.id,
                    'chapter_id': chapter_id,
                    'offset': validated_data['offset']
                },
                'update': {
                    'offset': validated_data['offset']
                }
            }
        )
        
        db.disconnect()
        
        # Serialize response
        from .serializers import ReadingProgressSerializer
        response_serializer = ReadingProgressSerializer(progress)
        
        return Response({'data': response_serializer.data})
        
    except Exception as e:
        logger.error(f"Error updating reading progress: {e}")
        db.disconnect()
        return Response(
            {
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to update reading progress',
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_reading_progress(request, chapter_id):
    """
    Get reading progress for a chapter.
    
    GET /v1/chapters/{id}/progress
    
    Returns:
        - 200: Progress retrieved successfully
        - 401: Not authenticated
        - 404: Chapter or progress not found
        
    Requirements:
        - 3.5: Restore last reading progress position
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
        
        # Check if chapter exists
        chapter = db.chapter.find_unique(where={'id': chapter_id})
        
        if not chapter or chapter.deleted_at:
            db.disconnect()
            return Response(
                {
                    'error': {
                        'code': 'NOT_FOUND',
                        'message': 'Chapter not found',
                    }
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get reading progress
        progress = db.readingprogress.find_unique(
            where={
                'user_id_chapter_id': {
                    'user_id': user_profile.id,
                    'chapter_id': chapter_id
                }
            }
        )
        
        db.disconnect()
        
        if not progress:
            return Response(
                {
                    'error': {
                        'code': 'NOT_FOUND',
                        'message': 'No reading progress found for this chapter',
                    }
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Serialize response
        from .serializers import ReadingProgressSerializer
        serializer = ReadingProgressSerializer(progress)
        
        return Response({'data': serializer.data})
        
    except Exception as e:
        logger.error(f"Error getting reading progress: {e}")
        db.disconnect()
        return Response(
            {
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to get reading progress',
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def _create_bookmark(request, chapter_id):
    """
    Create a bookmark in a chapter.
    
    POST /v1/chapters/{id}/bookmarks
    
    Request body:
        - offset: Character offset in the chapter (required)
        
    Returns:
        - 201: Bookmark created successfully
        - 400: Invalid input
        - 401: Not authenticated
        - 404: Chapter not found
        
    Requirements:
        - 3.6: Create bookmark at current position
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
    from .serializers import BookmarkCreateSerializer
    serializer = BookmarkCreateSerializer(data=request.data)
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
    
    # Query database
    db = Prisma()
    
    try:
        db.connect()
        
        # Check if chapter exists
        chapter = db.chapter.find_unique(where={'id': chapter_id})
        
        if not chapter or chapter.deleted_at:
            db.disconnect()
            return Response(
                {
                    'error': {
                        'code': 'NOT_FOUND',
                        'message': 'Chapter not found',
                    }
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Create bookmark
        bookmark = db.bookmark.create(
            data={
                'user_id': user_profile.id,
                'chapter_id': chapter_id,
                'offset': validated_data['offset']
            }
        )
        
        db.disconnect()
        
        # Serialize response
        from .serializers import BookmarkSerializer
        response_serializer = BookmarkSerializer(bookmark)
        
        return Response(
            {'data': response_serializer.data},
            status=status.HTTP_201_CREATED
        )
        
    except Exception as e:
        logger.error(f"Error creating bookmark: {e}")
        db.disconnect()
        return Response(
            {
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to create bookmark',
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def _list_bookmarks(request, chapter_id):
    """
    List all bookmarks for a chapter.
    
    GET /v1/chapters/{id}/bookmarks
    
    Returns:
        - 200: List of bookmarks
        - 401: Not authenticated
        - 404: Chapter not found
        
    Requirements:
        - 3.6: List bookmarks for a chapter
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
        
        # Check if chapter exists
        chapter = db.chapter.find_unique(where={'id': chapter_id})
        
        if not chapter or chapter.deleted_at:
            db.disconnect()
            return Response(
                {
                    'error': {
                        'code': 'NOT_FOUND',
                        'message': 'Chapter not found',
                    }
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get bookmarks
        bookmarks = db.bookmark.find_many(
            where={
                'user_id': user_profile.id,
                'chapter_id': chapter_id
            },
            order={'created_at': 'desc'}
        )
        
        db.disconnect()
        
        # Serialize response
        from .serializers import BookmarkSerializer
        serializer = BookmarkSerializer(bookmarks, many=True)
        
        return Response({'data': serializer.data})
        
    except Exception as e:
        logger.error(f"Error listing bookmarks: {e}")
        db.disconnect()
        return Response(
            {
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to list bookmarks',
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
def delete_bookmark(request, bookmark_id):
    """
    Delete a bookmark.
    
    DELETE /v1/bookmarks/{id}
    
    Returns:
        - 204: Bookmark deleted successfully
        - 401: Not authenticated
        - 403: Not authorized (not the bookmark owner)
        - 404: Bookmark not found
        
    Requirements:
        - 3.6: Delete bookmark
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
        
        # Get bookmark
        bookmark = db.bookmark.find_unique(where={'id': bookmark_id})
        
        if not bookmark:
            db.disconnect()
            return Response(
                {
                    'error': {
                        'code': 'NOT_FOUND',
                        'message': 'Bookmark not found',
                    }
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check authorization
        if bookmark.user_id != user_profile.id:
            db.disconnect()
            return Response(
                {
                    'error': {
                        'code': 'FORBIDDEN',
                        'message': 'You are not authorized to delete this bookmark',
                    }
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Delete bookmark
        db.bookmark.delete(where={'id': bookmark_id})
        
        db.disconnect()
        
        return Response(status=status.HTTP_204_NO_CONTENT)
        
    except Exception as e:
        logger.error(f"Error deleting bookmark: {e}")
        db.disconnect()
        return Response(
            {
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to delete bookmark',
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
