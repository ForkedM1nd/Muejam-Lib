"""
Search API Views

This module provides REST API endpoints for full-text search functionality.

Requirements: 35.3, 35.4, 35.5, 35.6, 35.8, 35.10
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from datetime import datetime
import asyncio
from prisma import Prisma

from infrastructure.search_service import search_service, SearchFilters
from apps.core.rate_limiting import rate_limit


def _run_async(coro):
    """Run async code from sync views, even with active event loop."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    result = {}
    error = {}

    def _runner():
        try:
            result['value'] = asyncio.run(coro)
        except Exception as exc:
            error['value'] = exc

    import threading

    thread = threading.Thread(target=_runner)
    thread.start()
    thread.join()

    if 'value' in error:
        raise error['value']

    return result.get('value')


class LegacySearchView(APIView):
    """Backward-compatible search endpoint for /v1/search/."""

    permission_classes = [AllowAny]
    RESULTS_PER_PAGE = 20

    async def _search_stories(self, query: str, page: int):
        db = Prisma()
        await db.connect()

        where = {
            'published': True,
            'deleted_at': None,
            'OR': [
                {'title': {'contains': query, 'mode': 'insensitive'}},
                {'blurb': {'contains': query, 'mode': 'insensitive'}},
            ],
        }

        try:
            stories = await db.story.find_many(
                where=where,
                order={'updated_at': 'desc'},
                skip=(page - 1) * self.RESULTS_PER_PAGE,
                take=self.RESULTS_PER_PAGE,
            )
            total = await db.story.count(where=where)
            return stories, total
        finally:
            await db.disconnect()

    @rate_limit('search_stories', 100, 60)
    def get(self, request):
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response(
                {'error': 'Query parameter "q" is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            page = int(request.query_params.get('page', 1))
            if page < 1:
                page = 1
        except ValueError:
            page = 1

        try:
            stories, total = _run_async(self._search_stories(query, page))

            formatted = []
            for story in stories:
                title = story.title or ''
                blurb = story.blurb or ''
                rank = 2.0 if query.lower() in title.lower() else 1.0
                formatted.append(
                    {
                        'id': story.id,
                        'type': 'story',
                        'title': title,
                        'description': blurb,
                        'snippet': blurb[:200],
                        'rank': rank,
                        'metadata': {
                            'author_id': story.author_id,
                            'updated_at': story.updated_at.isoformat() if story.updated_at else None,
                        },
                    }
                )

            formatted.sort(
                key=lambda item: (
                    0 if query.lower() in (item.get('title') or '').lower() else 1,
                    -(item.get('rank') or 0),
                )
            )

            has_next = page * self.RESULTS_PER_PAGE < total
            next_cursor = str(page + 1) if has_next else None
            return Response({'data': formatted, 'next_cursor': next_cursor}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': f'Search failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LegacySuggestView(APIView):
    """Backward-compatible suggest endpoint for /v1/search/suggest."""

    permission_classes = [AllowAny]

    async def _fetch_suggestions(self, query: str, limit: int):
        db = Prisma()
        await db.connect()

        try:
            stories = await db.story.find_many(
                where={
                    'published': True,
                    'deleted_at': None,
                    'title': {'contains': query, 'mode': 'insensitive'},
                },
                order={'updated_at': 'desc'},
                take=limit,
            )

            tags = await db.tag.find_many(
                where={'name': {'contains': query, 'mode': 'insensitive'}},
                order={'name': 'asc'},
                take=limit,
            )

            authors = await db.userprofile.find_many(
                where={
                    'OR': [
                        {'display_name': {'contains': query, 'mode': 'insensitive'}},
                        {'handle': {'contains': query, 'mode': 'insensitive'}},
                    ]
                },
                order={'display_name': 'asc'},
                take=limit,
            )

            return {
                'stories': [
                    {'id': story.id, 'title': story.title, 'slug': story.slug}
                    for story in stories
                ],
                'tags': [
                    {'id': tag.id, 'name': tag.name, 'slug': tag.slug}
                    for tag in tags
                ],
                'authors': [
                    {
                        'id': author.id,
                        'display_name': author.display_name,
                        'handle': author.handle,
                    }
                    for author in authors
                ],
            }
        finally:
            await db.disconnect()

    @rate_limit('autocomplete', 200, 60)
    def get(self, request):
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response(
                {'error': 'Query parameter "q" is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            limit = int(request.query_params.get('limit', 10))
        except ValueError:
            limit = 10

        if limit < 1:
            limit = 10
        if limit > 50:
            limit = 50

        try:
            suggestions = _run_async(self._fetch_suggestions(query, limit))
            return Response(suggestions, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': f'Autocomplete failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SearchStoriesView(APIView):
    """
    Search stories with full-text search and filters.
    
    GET /api/search/stories?q=query&genre=Fantasy&page=1
    
    Query Parameters:
    - q: Search query (required)
    - genre: Filter by genre (optional)
    - completion_status: Filter by completion status (optional)
    - min_word_count: Minimum word count (optional)
    - max_word_count: Maximum word count (optional)
    - updated_after: Filter by update date (ISO format, optional)
    - updated_before: Filter by update date (ISO format, optional)
    - page: Page number (default: 1)
    
    Requirements: 35.3, 35.4, 35.5, 35.8
    """
    
    permission_classes = [AllowAny]
    
    @rate_limit('search_stories', 100, 60)
    def get(self, request):
        # Get query parameter
        query = request.query_params.get('q', '').strip()
        
        if not query:
            return Response(
                {'error': 'Query parameter "q" is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get page number
        try:
            page = int(request.query_params.get('page', 1))
            if page < 1:
                page = 1
        except ValueError:
            page = 1
        
        # Build filters
        filters = SearchFilters()
        
        if request.query_params.get('genre'):
            filters.genre = request.query_params.get('genre')
        
        if request.query_params.get('completion_status'):
            filters.completion_status = request.query_params.get('completion_status')
        
        if request.query_params.get('min_word_count'):
            try:
                filters.min_word_count = int(request.query_params.get('min_word_count'))
            except ValueError:
                pass
        
        if request.query_params.get('max_word_count'):
            try:
                filters.max_word_count = int(request.query_params.get('max_word_count'))
            except ValueError:
                pass
        
        if request.query_params.get('updated_after'):
            try:
                filters.updated_after = datetime.fromisoformat(
                    request.query_params.get('updated_after')
                )
            except ValueError:
                pass
        
        if request.query_params.get('updated_before'):
            try:
                filters.updated_before = datetime.fromisoformat(
                    request.query_params.get('updated_before')
                )
            except ValueError:
                pass
        
        # Get user ID if authenticated
        user_id = request.user.id if request.user.is_authenticated else None
        
        # Perform search
        try:
            results = search_service.search_stories(
                query=query,
                filters=filters,
                page=page,
                user_id=user_id
            )
            
            return Response(results, status=status.HTTP_200_OK)
            
        except Exception as e:
            import traceback
            traceback.print_exc()  # Print full traceback to console
            return Response(
                {'error': f'Search failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SearchAuthorsView(APIView):
    """
    Search authors with full-text search.
    
    GET /api/search/authors?q=query&page=1
    
    Query Parameters:
    - q: Search query (required)
    - page: Page number (default: 1)
    
    Requirements: 35.3, 35.4, 35.8
    """
    
    permission_classes = [AllowAny]
    
    @rate_limit('search_authors', 100, 60)
    def get(self, request):
        # Get query parameter
        query = request.query_params.get('q', '').strip()
        
        if not query:
            return Response(
                {'error': 'Query parameter "q" is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get page number
        try:
            page = int(request.query_params.get('page', 1))
            if page < 1:
                page = 1
        except ValueError:
            page = 1
        
        # Get user ID if authenticated
        user_id = request.user.id if request.user.is_authenticated else None
        
        # Perform search
        try:
            results = search_service.search_authors(
                query=query,
                page=page,
                user_id=user_id
            )
            
            return Response(results, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Search failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AutocompleteView(APIView):
    """
    Get autocomplete suggestions for search query.
    
    GET /api/search/autocomplete?q=query&limit=10
    
    Query Parameters:
    - q: Partial search query (required)
    - limit: Maximum number of suggestions (default: 10)
    
    Requirements: 35.6
    """
    
    permission_classes = [AllowAny]
    
    @rate_limit('autocomplete', 200, 60)
    def get(self, request):
        # Get query parameter
        query = request.query_params.get('q', '').strip()
        
        if not query:
            return Response(
                {'error': 'Query parameter "q" is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get limit
        try:
            limit = int(request.query_params.get('limit', 10))
            if limit < 1:
                limit = 10
            elif limit > 50:
                limit = 50
        except ValueError:
            limit = 10
        
        # Get suggestions
        try:
            suggestions = search_service.autocomplete(query=query, limit=limit)
            
            return Response(
                {'suggestions': suggestions},
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {'error': f'Autocomplete failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PopularSearchesView(APIView):
    """
    Get popular search queries.
    
    GET /api/search/popular?days=7&limit=20
    
    Query Parameters:
    - days: Number of days to look back (default: 7)
    - limit: Maximum number of results (default: 20)
    
    Requirements: 35.10
    """
    
    permission_classes = [AllowAny]
    
    @rate_limit('search_tags', 100, 60)
    def get(self, request):
        # Get parameters
        try:
            days = int(request.query_params.get('days', 7))
            if days < 1:
                days = 7
            elif days > 90:
                days = 90
        except ValueError:
            days = 7
        
        try:
            limit = int(request.query_params.get('limit', 20))
            if limit < 1:
                limit = 20
            elif limit > 100:
                limit = 100
        except ValueError:
            limit = 20
        
        # Get popular searches
        try:
            popular = search_service.get_popular_searches(days=days, limit=limit)
            
            return Response(
                {'popular_searches': popular},
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get popular searches: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TrackSearchClickView(APIView):
    """
    Track when a user clicks on a search result.
    
    POST /api/search/track-click
    
    Request Body:
    {
        "query": "search query",
        "result_id": 123,
        "result_type": "story"
    }
    
    Requirements: 35.10
    """
    
    permission_classes = [AllowAny]
    
    @rate_limit('track_search', 100, 60)
    def post(self, request):
        # Get parameters
        query = request.data.get('query', '').strip()
        result_id = request.data.get('result_id')
        result_type = request.data.get('result_type', '').strip()
        
        # Validate parameters
        if not query:
            return Response(
                {'error': 'Query is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not result_id:
            return Response(
                {'error': 'Result ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if result_type not in ['story', 'author', 'tag']:
            return Response(
                {'error': 'Invalid result type'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get user ID if authenticated
        user_id = request.user.id if request.user.is_authenticated else None
        
        # Track click
        try:
            search_service.track_click(
                query=query,
                result_id=result_id,
                result_type=result_type,
                user_id=user_id
            )
            
            return Response(
                {'success': True},
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {'error': f'Failed to track click: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
