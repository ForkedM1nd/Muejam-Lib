"""Views for discovery feeds."""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from prisma import Prisma
from datetime import datetime
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from apps.core.pagination import CursorPagination
from apps.core.cache import CacheManager
from apps.stories.serializers import StoryListSerializer
from .trending import TrendingCalculator
from .personalization import PersonalizationEngine
from .serializers import DiscoverFeedQuerySerializer, GenreQuerySerializer, SimilarStoriesQuerySerializer
import asyncio


def get_blocked_user_ids(request):
    """
    Get list of blocked user IDs for the current user.
    
    Args:
        request: DRF request object
        
    Returns:
        List of blocked user IDs
    """
    if not hasattr(request, 'user_profile') or not request.user_profile:
        return []
    
    async def fetch_blocked():
        db = Prisma()
        await db.connect()
        try:
            blocks = await db.block.find_many(
                where={'blocker_id': request.user_profile.id},
                select={'blocked_id': True}
            )
            return [b.blocked_id for b in blocks]
        finally:
            await db.disconnect()
    
    return asyncio.run(fetch_blocked())


@extend_schema(
    tags=['Discovery'],
    summary='Get discovery feed',
    description='''
    Retrieve stories from one of three discovery feeds:
    
    - **Trending**: Stories with high recent engagement (saves, reads, likes, whispers)
    - **New**: Recently published stories ordered by publication date
    - **For You**: Personalized recommendations based on user interests (requires authentication)
    
    All feeds support filtering by tag and search query. Results are cached for performance.
    ''',
    parameters=[
        OpenApiParameter(
            name='tab',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Feed type: trending, new, or for-you',
            required=False,
            enum=['trending', 'new', 'for-you'],
        ),
        OpenApiParameter(
            name='tag',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Filter by tag slug',
            required=False,
        ),
        OpenApiParameter(
            name='q',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Search query for title, blurb, or author',
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
    responses={
        200: OpenApiTypes.OBJECT,
        400: OpenApiTypes.OBJECT,
    },
    examples=[
        OpenApiExample(
            'Discovery Feed Response',
            value={
                'data': [
                    {
                        'id': '123e4567-e89b-12d3-a456-426614174000',
                        'slug': 'the-chronicles-of-aether',
                        'title': 'The Chronicles of Aether',
                        'blurb': 'A fantasy epic about magic and destiny',
                        'cover_key': 'covers/uuid-here.jpg',
                        'author': {
                            'id': '456e7890-e89b-12d3-a456-426614174000',
                            'handle': 'fantasy_writer',
                            'display_name': 'Fantasy Writer'
                        },
                        'tags': ['fantasy', 'magic', 'adventure'],
                        'published_at': '2024-01-15T10:00:00Z'
                    }
                ],
                'next_cursor': 'eyJpZCI6IjEyM2U0NTY3LWU4OWItMTJkMy1hNDU2LTQyNjYxNDE3NDAwMCJ9'
            },
            response_only=True,
        ),
    ]
)
@api_view(['GET'])
@permission_classes([AllowAny])
def discover_feed(request):
    """
    Get discovery feed based on tab parameter.
    
    Query Parameters:
        - tab: 'trending', 'new', or 'for-you' (default: 'trending')
        - cursor: Pagination cursor (optional)
        - page_size: Number of results per page (default: 20, max: 100)
        - tag: Filter by tag slug (optional)
        - q: Search query (optional)
        
    Returns:
        Paginated list of stories
        
    Requirements:
        - 2.1: Display three tabs: Trending, New, For You
        - 2.2: Trending tab ordered by Trending_Score
        - 2.3: New tab ordered by publication date descending
        - 2.4: For You tab with personalized recommendations
        - 2.10: Filter by tag
        - 2.11: Search with query text
        - 21.2: Cache with TTL 3-5 minutes
    """
    # Validate query parameters with serializer
    serializer = DiscoverFeedQuerySerializer(data=request.query_params)
    if not serializer.is_valid():
        return Response(
            {
                'error': 'Invalid query parameters',
                'details': serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    validated_data = serializer.validated_data
    tab = validated_data.get('tab', 'trending')
    tag_slug = validated_data.get('tag')
    search_query = validated_data.get('q')
    cursor = validated_data.get('cursor')
    
    # For You feed requires authentication
    if tab == 'for-you':
        if not hasattr(request, 'user_profile') or not request.user_profile:
            return Response(
                {'error': 'Authentication required for For You feed'},
                status=status.HTTP_401_UNAUTHORIZED
            )
    
    # Generate cache key
    cache_key = CacheManager.make_key(
        'discover_feed',
        tab=tab,
        tag=tag_slug or '',
        q=search_query or '',
        cursor=cursor or ''
    )
    
    # Try to get from cache
    cached_response = CacheManager.get_or_set(
        cache_key,
        lambda: None,  # Will be replaced with actual fetch
        CacheManager.TTL_CONFIG['discover_feed']
    )
    
    if cached_response is not None:
        return Response(cached_response)
    
    # Fetch data based on tab
    if tab == 'trending':
        response_data = asyncio.run(fetch_trending_feed(request, tag_slug, search_query))
    elif tab == 'new':
        response_data = asyncio.run(fetch_new_feed(request, tag_slug, search_query))
    elif tab == 'for-you':
        response_data = asyncio.run(fetch_for_you_feed(request, tag_slug, search_query))
    
    # Cache the response
    CacheManager.get_or_set(
        cache_key,
        lambda: response_data,
        CacheManager.TTL_CONFIG['discover_feed']
    )
    
    return Response(response_data)


async def fetch_trending_feed(request, tag_slug=None, search_query=None):
    """
    Fetch trending feed stories.
    
    Requirements:
        - 2.2: Order by Trending_Score within last 24 hours
        - 16.7: Exclude soft-deleted stories
    """
    db = Prisma()
    await db.connect()
    
    try:
        # Get blocked user IDs
        blocked_ids = get_blocked_user_ids(request)
        
        # Build where clause
        where_clause = {
            'published': True,
            'deleted_at': None
        }
        
        if blocked_ids:
            where_clause['author_id'] = {'not_in': blocked_ids}
        
        # Add tag filter
        if tag_slug:
            tag = await db.tag.find_unique(where={'slug': tag_slug})
            if tag:
                where_clause['tags'] = {
                    'some': {
                        'tag_id': tag.id
                    }
                }
        
        # Add search filter
        if search_query:
            where_clause['OR'] = [
                {'title': {'contains': search_query, 'mode': 'insensitive'}},
                {'blurb': {'contains': search_query, 'mode': 'insensitive'}}
            ]
        
        # Get today's date for stats (convert to datetime for Prisma)
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Fetch stories with stats
        stories = await db.story.find_many(
            where=where_clause,
            include={
                'stats': {
                    'where': {'date': today},
                    'take': 1
                },
                'tags': {
                    'include': {
                        'tag': True
                    }
                }
            },
            take=100  # Get more for sorting
        )
        
        # Sort by trending score
        stories_with_scores = [
            (story.stats[0].trending_score if story.stats else 0, story)
            for story in stories
        ]
        stories_with_scores.sort(key=lambda x: x[0], reverse=True)
        
        # Apply pagination manually
        page_size = min(int(request.query_params.get('page_size', 20)), 100)
        cursor = request.query_params.get('cursor')
        
        # Simple pagination without cursor for now
        sorted_stories = [story for score, story in stories_with_scores]
        paginated_stories = sorted_stories[:page_size]
        
        # Serialize
        serializer = StoryListSerializer(paginated_stories, many=True)
        
        return {
            'data': serializer.data,
            'next_cursor': None  # Simplified for now
        }
        
    finally:
        await db.disconnect()


async def fetch_new_feed(request, tag_slug=None, search_query=None):
    """
    Fetch new feed stories.
    
    Requirements:
        - 2.3: Order by published_at descending
        - 21.1: Cache with TTL 3-5 minutes
    """
    db = Prisma()
    await db.connect()
    
    try:
        # Get blocked user IDs
        blocked_ids = get_blocked_user_ids(request)
        
        # Build where clause
        where_clause = {
            'published': True,
            'deleted_at': None
        }
        
        if blocked_ids:
            where_clause['author_id'] = {'not_in': blocked_ids}
        
        # Add tag filter
        if tag_slug:
            tag = await db.tag.find_unique(where={'slug': tag_slug})
            if tag:
                where_clause['tags'] = {
                    'some': {
                        'tag_id': tag.id
                    }
                }
        
        # Add search filter
        if search_query:
            where_clause['OR'] = [
                {'title': {'contains': search_query, 'mode': 'insensitive'}},
                {'blurb': {'contains': search_query, 'mode': 'insensitive'}}
            ]
        
        # Fetch stories ordered by published_at
        page_size = min(int(request.query_params.get('page_size', 20)), 100)
        
        stories = await db.story.find_many(
            where=where_clause,
            include={
                'tags': {
                    'include': {
                        'tag': True
                    }
                }
            },
            order={'published_at': 'desc'},
            take=page_size
        )
        
        # Serialize
        serializer = StoryListSerializer(stories, many=True)
        
        return {
            'data': serializer.data,
            'next_cursor': None  # Simplified for now
        }
        
    finally:
        await db.disconnect()


async def fetch_for_you_feed(request, tag_slug=None, search_query=None):
    """
    Fetch personalized For You feed.
    
    Requirements:
        - 2.4: Personalized recommendations based on Interest_Score
        - 2.5: Cold start fallback to trending
        - 10.7: Exclude blocked authors
        - 21.6: Cache with TTL 1-6 hours
    """
    user_id = request.user_profile.id
    blocked_ids = get_blocked_user_ids(request)
    
    # Get personalized feed
    engine = PersonalizationEngine()
    stories = await engine.get_for_you_feed(user_id, blocked_ids, limit=20)
    
    # Cold start: fallback to trending
    if stories is None:
        return await fetch_trending_feed(request, tag_slug, search_query)
    
    # Apply tag filter if provided
    if tag_slug:
        db = Prisma()
        await db.connect()
        try:
            tag = await db.tag.find_unique(where={'slug': tag_slug})
            if tag:
                stories = [
                    s for s in stories
                    if any(t['tag_id'] == tag.id for t in s.get('tags', []))
                ]
        finally:
            await db.disconnect()
    
    # Apply search filter if provided
    if search_query:
        query_lower = search_query.lower()
        stories = [
            s for s in stories
            if query_lower in s['title'].lower() or query_lower in s['blurb'].lower()
        ]
    
    return {
        'data': stories,
        'next_cursor': None  # Simplified for now
    }



# New discovery endpoints for Task 67

@api_view(['GET'])
@permission_classes([AllowAny])
def trending_stories_v2(request):
    """
    GET /v1/discovery/trending - Get trending stories
    
    Requirements:
        - 25.1, 25.2: Trending feed based on engagement and recency
    
    Query params:
        - limit: Number of stories to return (default: 20)
        - days: Number of days to consider (default: 7)
    """
    from .discovery_service import DiscoveryService
    from apps.stories.serializers import StoryListSerializer
    
    limit = int(request.query_params.get('limit', 20))
    days = int(request.query_params.get('days', 7))
    
    stories = asyncio.run(DiscoveryService.get_trending_stories(limit=limit, days=days))
    
    serializer = StoryListSerializer(stories, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def stories_by_genre(request, genre):
    """
    GET /v1/discovery/genre/{genre} - Get stories by genre with filters
    
    Requirements:
        - 25.3: Genre-based browsing
        - 25.4: Filtering by status, word count, update frequency
    """
    from .discovery_service import DiscoveryService
    from apps.stories.serializers import StoryListSerializer
    
    limit = int(request.query_params.get('limit', 20))
    offset = int(request.query_params.get('offset', 0))
    
    filters = {}
    if 'status' in request.query_params:
        filters['status'] = request.query_params['status']
    
    stories, total = asyncio.run(DiscoveryService.get_stories_by_genre(
        genre=genre,
        limit=limit,
        offset=offset,
        filters=filters
    ))
    
    serializer = StoryListSerializer(stories, many=True)
    return Response({
        'results': serializer.data,
        'total': total,
        'limit': limit,
        'offset': offset
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recommended_stories(request):
    """
    GET /v1/discovery/recommended - Get recommended stories for current user
    
    Requirements:
        - 25.5: Recommendations based on reading history and followed authors
    """
    from .discovery_service import DiscoveryService
    from apps.stories.serializers import StoryListSerializer
    
    if not request.user_profile:
        return Response(
            {'error': {'code': 'UNAUTHORIZED', 'message': 'Authentication required'}},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    limit = int(request.query_params.get('limit', 10))
    
    stories = asyncio.run(DiscoveryService.get_recommended_stories(
        user_id=request.user_profile.id,
        limit=limit
    ))
    
    serializer = StoryListSerializer(stories, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def similar_stories(request, story_id):
    """
    GET /v1/discovery/similar/{story_id} - Get similar stories
    
    Requirements:
        - 25.6: Similar stories based on genre, tags, and reader overlap
    """
    from .discovery_service import DiscoveryService
    from apps.stories.serializers import StoryListSerializer
    
    limit = int(request.query_params.get('limit', 5))
    
    stories = asyncio.run(DiscoveryService.get_similar_stories(
        story_id=story_id,
        limit=limit
    ))
    
    serializer = StoryListSerializer(stories, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def new_and_noteworthy(request):
    """
    GET /v1/discovery/new-and-noteworthy - Get new and noteworthy stories
    
    Requirements:
        - 25.7: New and noteworthy featuring recent stories with quality signals
    """
    from .discovery_service import DiscoveryService
    from apps.stories.serializers import StoryListSerializer
    
    limit = int(request.query_params.get('limit', 10))
    days = int(request.query_params.get('days', 30))
    
    stories = asyncio.run(DiscoveryService.get_new_and_noteworthy(limit=limit, days=days))
    
    serializer = StoryListSerializer(stories, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def staff_picks(request):
    """
    GET /v1/discovery/staff-picks - Get staff-curated stories
    
    Requirements:
        - 25.10: Staff picks curated by moderators
    """
    from .discovery_service import DiscoveryService
    from apps.stories.serializers import StoryListSerializer
    
    limit = int(request.query_params.get('limit', 10))
    
    stories = asyncio.run(DiscoveryService.get_staff_picks(limit=limit))
    
    serializer = StoryListSerializer(stories, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def rising_authors(request):
    """
    GET /v1/discovery/rising-authors - Get rising authors
    
    Requirements:
        - 25.12: Rising authors featuring new authors with growing followings
    """
    from .discovery_service import DiscoveryService
    
    limit = int(request.query_params.get('limit', 10))
    days = int(request.query_params.get('days', 30))
    
    authors = asyncio.run(DiscoveryService.get_rising_authors(limit=limit, days=days))
    
    # Format response
    author_data = [
        {
            'id': item['author'].id,
            'handle': item['author'].handle,
            'display_name': item['author'].display_name,
            'bio': item['author'].bio,
            'avatar_key': item['author'].avatar_key,
            'follower_count': item['follower_count'],
            'story_count': item['story_count'],
            'created_at': item['author'].created_at
        }
        for item in authors
    ]
    
    return Response(author_data)
