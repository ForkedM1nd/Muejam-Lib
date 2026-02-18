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

from infrastructure.search_service import search_service, SearchFilters
from apps.core.rate_limiting import rate_limit


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
