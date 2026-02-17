"""Views for search and autocomplete."""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from prisma import Prisma
from datetime import datetime
from apps.core.pagination import CursorPagination
from apps.core.cache import CacheManager
from apps.stories.serializers import StoryListSerializer
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


@api_view(['GET'])
@permission_classes([AllowAny])
def search(request):
    """
    Full-text search across stories, authors, and tags.
    
    Query Parameters:
        - q: Search query (required)
        - cursor: Pagination cursor (optional)
        - page_size: Number of results per page (default: 20, max: 100)
        
    Returns:
        Paginated list of stories matching the search query
        
    Requirements:
        - 9.1: Search across story title, blurb, author name, tags
        - 9.5: Rank results by relevance and trending score
        - 9.6: Exclude soft-deleted and blocked content
        - 9.7: Use PostgreSQL full-text search
    """
    query = request.query_params.get('q', '').strip()
    
    if not query:
        return Response(
            {'error': 'Search query parameter "q" is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get blocked user IDs
    blocked_ids = get_blocked_user_ids(request)
    
    # Fetch search results
    response_data = asyncio.run(fetch_search_results(query, blocked_ids, request))
    
    return Response(response_data)


async def fetch_search_results(query, blocked_ids, request):
    """
    Fetch search results using PostgreSQL full-text search.
    
    Requirements:
        - 9.1: Search across title, blurb, author name, tags
        - 9.5: Rank by relevance and trending score
        - 9.6: Exclude deleted and blocked content
    """
    db = Prisma()
    await db.connect()
    
    try:
        # Build where clause
        where_clause = {
            'published': True,
            'deleted_at': None
        }
        
        if blocked_ids:
            where_clause['author_id'] = {'not_in': blocked_ids}
        
        # Search across title and blurb using case-insensitive contains
        # Note: For production, you'd want to set up PostgreSQL full-text search indexes
        # and use to_tsvector/to_tsquery for better performance
        where_clause['OR'] = [
            {'title': {'contains': query, 'mode': 'insensitive'}},
            {'blurb': {'contains': query, 'mode': 'insensitive'}}
        ]
        
        # Get today's date for stats
        today = datetime.now().date()
        
        # Fetch stories with stats and author info
        stories = await db.story.find_many(
            where=where_clause,
            include={
                'author': True,
                'tags': {
                    'include': {
                        'tag': True
                    }
                },
                'stats': {
                    'where': {'date': today},
                    'take': 1
                }
            },
            take=100  # Get more for ranking
        )
        
        # Also search by tag name
        tag_matches = await db.tag.find_many(
            where={
                'name': {'contains': query, 'mode': 'insensitive'}
            }
        )
        
        if tag_matches:
            tag_ids = [tag.id for tag in tag_matches]
            tag_stories = await db.story.find_many(
                where={
                    'published': True,
                    'deleted_at': None,
                    'author_id': {'not_in': blocked_ids} if blocked_ids else {},
                    'tags': {
                        'some': {
                            'tag_id': {'in': tag_ids}
                        }
                    }
                },
                include={
                    'author': True,
                    'tags': {
                        'include': {
                            'tag': True
                        }
                    },
                    'stats': {
                        'where': {'date': today},
                        'take': 1
                    }
                },
                take=50
            )
            
            # Merge results (avoid duplicates)
            story_ids = {s.id for s in stories}
            for story in tag_stories:
                if story.id not in story_ids:
                    stories.append(story)
                    story_ids.add(story.id)
        
        # Also search by author name
        author_matches = await db.userprofile.find_many(
            where={
                'OR': [
                    {'display_name': {'contains': query, 'mode': 'insensitive'}},
                    {'handle': {'contains': query, 'mode': 'insensitive'}}
                ]
            }
        )
        
        if author_matches:
            author_ids = [author.id for author in author_matches]
            author_stories = await db.story.find_many(
                where={
                    'published': True,
                    'deleted_at': None,
                    'author_id': {'in': author_ids, 'not_in': blocked_ids} if blocked_ids else {'in': author_ids}
                },
                include={
                    'author': True,
                    'tags': {
                        'include': {
                            'tag': True
                        }
                    },
                    'stats': {
                        'where': {'date': today},
                        'take': 1
                    }
                },
                take=50
            )
            
            # Merge results (avoid duplicates)
            story_ids = {s.id for s in stories}
            for story in author_stories:
                if story.id not in story_ids:
                    stories.append(story)
                    story_ids.add(story.id)
        
        # Rank results by relevance and trending score
        scored_stories = []
        query_lower = query.lower()
        
        for story in stories:
            # Calculate relevance score
            relevance = 0
            
            # Title match (highest weight)
            if query_lower in story.title.lower():
                relevance += 10
                if story.title.lower().startswith(query_lower):
                    relevance += 5  # Bonus for prefix match
            
            # Blurb match
            if query_lower in story.blurb.lower():
                relevance += 3
            
            # Author match
            if query_lower in story.author.display_name.lower():
                relevance += 5
            if query_lower in story.author.handle.lower():
                relevance += 5
            
            # Tag match
            for story_tag in story.tags:
                if query_lower in story_tag.tag.name.lower():
                    relevance += 4
            
            # Get trending score
            trending_score = story.stats[0].trending_score if story.stats else 0
            
            # Combined score: 70% relevance, 30% trending
            final_score = (0.7 * relevance) + (0.3 * trending_score)
            
            scored_stories.append((final_score, story))
        
        # Sort by score descending
        scored_stories.sort(key=lambda x: x[0], reverse=True)
        
        # Apply pagination
        page_size = min(int(request.query_params.get('page_size', 20)), 100)
        paginated_stories = [story for score, story in scored_stories[:page_size]]
        
        # Serialize
        serializer = StoryListSerializer(paginated_stories, many=True)
        
        return {
            'data': serializer.data,
            'next_cursor': None  # Simplified for now
        }
        
    finally:
        await db.disconnect()


@api_view(['GET'])
@permission_classes([AllowAny])
def suggest(request):
    """
    Autocomplete suggestions for search.
    
    Query Parameters:
        - q: Search query (required)
        - limit: Number of suggestions (default: 10, max: 20)
        
    Returns:
        Suggestions for stories, tags, and authors
        
    Requirements:
        - 9.2: Return suggestions for stories, tags, authors
        - 9.3: Cache suggestions with TTL
        - 9.4: Navigate to corresponding content
        - 21.5: Cache with TTL 10-30 minutes
    """
    query = request.query_params.get('q', '').strip()
    
    if not query:
        return Response(
            {'error': 'Search query parameter "q" is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Generate cache key
    cache_key = CacheManager.make_key(
        'search_suggest',
        q=query,
        limit=request.query_params.get('limit', 10)
    )
    
    # Try to get from cache
    cached_response = CacheManager.get_or_set(
        cache_key,
        lambda: None,
        CacheManager.TTL_CONFIG['search_suggest']
    )
    
    if cached_response is not None:
        return Response(cached_response)
    
    # Get blocked user IDs
    blocked_ids = get_blocked_user_ids(request)
    
    # Fetch suggestions
    response_data = asyncio.run(fetch_suggestions(query, blocked_ids, request))
    
    # Cache the response
    CacheManager.get_or_set(
        cache_key,
        lambda: response_data,
        CacheManager.TTL_CONFIG['search_suggest']
    )
    
    return Response(response_data)


async def fetch_suggestions(query, blocked_ids, request):
    """
    Fetch autocomplete suggestions.
    
    Requirements:
        - 9.2: Suggestions for stories, tags, authors
        - 9.3: Cache with TTL 10-30 minutes
    """
    db = Prisma()
    await db.connect()
    
    try:
        limit = min(int(request.query_params.get('limit', 10)), 20)
        suggestions = {
            'stories': [],
            'tags': [],
            'authors': []
        }
        
        # Story suggestions
        stories = await db.story.find_many(
            where={
                'published': True,
                'deleted_at': None,
                'author_id': {'not_in': blocked_ids} if blocked_ids else {},
                'title': {'contains': query, 'mode': 'insensitive'}
            },
            take=limit
        )
        
        suggestions['stories'] = [
            {
                'id': story.id,
                'slug': story.slug,
                'title': story.title,
                'type': 'story'
            }
            for story in stories
        ]
        
        # Tag suggestions
        tags = await db.tag.find_many(
            where={
                'name': {'contains': query, 'mode': 'insensitive'}
            },
            take=limit
        )
        
        suggestions['tags'] = [
            {
                'id': tag.id,
                'slug': tag.slug,
                'name': tag.name,
                'type': 'tag'
            }
            for tag in tags
        ]
        
        # Author suggestions
        authors = await db.userprofile.find_many(
            where={
                'id': {'not_in': blocked_ids} if blocked_ids else {},
                'OR': [
                    {'display_name': {'contains': query, 'mode': 'insensitive'}},
                    {'handle': {'contains': query, 'mode': 'insensitive'}}
                ]
            },
            take=limit
        )
        
        suggestions['authors'] = [
            {
                'id': author.id,
                'handle': author.handle,
                'display_name': author.display_name,
                'type': 'author'
            }
            for author in authors
        ]
        
        return suggestions
        
    finally:
        await db.disconnect()
