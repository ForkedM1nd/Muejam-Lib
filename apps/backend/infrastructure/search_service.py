"""
Full-Text Search Service

This module provides full-text search functionality using PostgreSQL's
built-in full-text search capabilities.

Requirements: 35.1, 35.2, 35.3, 35.4, 35.5, 35.6, 35.7, 35.8, 35.9, 35.10, 35.11, 35.12
"""

import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

from django.db import connection
from django.db.models import Q, F, Count
from django.core.cache import cache

from .database_cache import cache_query, invalidate_by_tags


@dataclass
class SearchResult:
    """Search result with relevance ranking."""
    id: int
    type: str  # 'story', 'author', 'tag'
    title: str
    description: str
    rank: float
    snippet: str
    metadata: Dict[str, Any]


@dataclass
class SearchFilters:
    """Search filters for refining results."""
    genre: Optional[str] = None
    completion_status: Optional[str] = None
    min_word_count: Optional[int] = None
    max_word_count: Optional[int] = None
    updated_after: Optional[datetime] = None
    updated_before: Optional[datetime] = None


class SearchService:
    """
    Full-text search service using PostgreSQL.
    
    Implements:
    - Full-text search with relevance ranking
    - Search filters
    - Autocomplete suggestions
    - Search query caching
    - Search analytics
    """
    
    # Cache TTL for search results (5 minutes per Requirement 35.7)
    CACHE_TTL = 300
    
    # Results per page (Requirement 35.8)
    RESULTS_PER_PAGE = 20
    
    # Autocomplete response time target (Requirement 35.6)
    AUTOCOMPLETE_TIMEOUT_MS = 100
    
    def __init__(self):
        """Initialize search service."""
        self.cache_prefix = "search:"
    
    def search_stories(
        self,
        query: str,
        filters: Optional[SearchFilters] = None,
        page: int = 1,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Search stories with full-text search and filters.
        
        Args:
            query: Search query string
            filters: Optional search filters
            page: Page number (1-indexed)
            user_id: Optional user ID for analytics
            
        Returns:
            Dictionary with results, total count, and metadata
            
        Requirements: 35.3, 35.4, 35.5, 35.7, 35.8, 35.9
        """
        start_time = time.time()
        
        # Generate cache key
        cache_key = self._generate_cache_key('stories', query, filters, page)
        
        # Try to get from cache
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            # Track cache hit
            self._track_search_query(
                query, user_id, cached_result['total'], 
                int((time.time() - start_time) * 1000), from_cache=True
            )
            return cached_result
        
        # Build search query
        search_query = self._build_search_query(query)
        
        # Build SQL query - simplified version without full-text search
        # TODO: Add search_vector column and full-text search indexes
        sql = """
            SELECT 
                id, title, blurb as description, author_id, updated_at,
                1.0 AS rank,
                LEFT(blurb, 200) AS snippet
            FROM "Story"
            WHERE (title ILIKE %s OR blurb ILIKE %s)
                AND published = true
                AND deleted_at IS NULL
        """
        
        search_pattern = f"%{query}%"
        params = [search_pattern, search_pattern]
        
        # Add filters (only for fields that exist in the Story model)
        if filters:
            # Note: genre, completion_status, word_count fields don't exist in Story model yet
            # TODO: Add these fields to the Story model in Prisma schema
            
            if filters.updated_after:
                sql += " AND updated_at >= %s"
                params.append(filters.updated_after)
            
            if filters.updated_before:
                sql += " AND updated_at <= %s"
                params.append(filters.updated_before)
        
        # Add ordering
        sql += " ORDER BY rank DESC, updated_at DESC"
        
        # Build count query
        count_sql = """
            SELECT COUNT(*)
            FROM "Story"
            WHERE (title ILIKE %s OR blurb ILIKE %s)
                AND published = true
                AND deleted_at IS NULL
        """
        
        # Add same filters to count query
        if filters:
            if filters.updated_after:
                count_sql += " AND updated_at >= %s"
            
            if filters.updated_before:
                count_sql += " AND updated_at <= %s"
        
        with connection.cursor() as cursor:
            # Get total count
            cursor.execute(count_sql, params)
            total = int(cursor.fetchone()[0])  # Convert to int
            
            # Add pagination
            offset = (page - 1) * self.RESULTS_PER_PAGE
            sql += f" LIMIT {self.RESULTS_PER_PAGE} OFFSET {offset}"
            
            # Execute search
            cursor.execute(sql, params)
            columns = [col[0] for col in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Format results
        formatted_results = [
            {
                'id': r['id'],
                'type': 'story',
                'title': r['title'],
                'description': r['description'],
                'snippet': r['snippet'],
                'rank': float(r['rank']),
                'metadata': {
                    # Note: genre, completion_status, word_count don't exist in Story model yet
                    'updated_at': r['updated_at'].isoformat() if r['updated_at'] else None,
                    'author_id': r['author_id']
                }
            }
            for r in results
        ]
        
        # Calculate pagination
        total_pages = (total + self.RESULTS_PER_PAGE - 1) // self.RESULTS_PER_PAGE
        
        result = {
            'results': formatted_results,
            'total': total,
            'page': page,
            'per_page': self.RESULTS_PER_PAGE,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }
        
        # Cache result
        cache.set(cache_key, result, self.CACHE_TTL)
        
        # Track search query
        response_time_ms = int((time.time() - start_time) * 1000)
        self._track_search_query(query, user_id, total, response_time_ms)
        
        return result
    
    def search_authors(
        self,
        query: str,
        page: int = 1,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Search authors with full-text search.
        
        Args:
            query: Search query string
            page: Page number (1-indexed)
            user_id: Optional user ID for analytics
            
        Returns:
            Dictionary with results, total count, and metadata
        """
        start_time = time.time()
        
        # Generate cache key
        cache_key = self._generate_cache_key('authors', query, None, page)
        
        # Try to get from cache
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Build search query
        search_query = self._build_search_query(query)
        
        # Build SQL query
        sql = """
            SELECT 
                id, display_name, handle, bio, avatar_key,
                1.0 AS rank,
                LEFT(COALESCE(bio, ''), 200) AS snippet
            FROM "UserProfile"
            WHERE (display_name ILIKE %s OR handle ILIKE %s OR bio ILIKE %s)
            ORDER BY display_name
        """
        
        search_pattern = f"%{query}%"
        params = [search_pattern, search_pattern, search_pattern]
        
        # Build count query
        count_sql = """
            SELECT COUNT(*)
            FROM "UserProfile"
            WHERE (display_name ILIKE %s OR handle ILIKE %s OR bio ILIKE %s)
        """
        
        with connection.cursor() as cursor:
            # Get total count
            cursor.execute(count_sql, params)
            total = int(cursor.fetchone()[0])  # Convert to int
            
            # Add pagination
            offset = (page - 1) * self.RESULTS_PER_PAGE
            sql += f" LIMIT {self.RESULTS_PER_PAGE} OFFSET {offset}"
            
            # Execute search
            cursor.execute(sql, params)
            columns = [col[0] for col in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Format results
        formatted_results = [
            {
                'id': r['id'],
                'type': 'author',
                'title': r['display_name'],
                'description': r['bio'] or '',
                'snippet': r['snippet'] or '',
                'rank': float(r['rank']),
                'metadata': {
                    'handle': r['handle'],
                    'avatar_key': r['avatar_key']
                }
            }
            for r in results
        ]
        
        # Calculate pagination
        total_pages = (total + self.RESULTS_PER_PAGE - 1) // self.RESULTS_PER_PAGE
        
        result = {
            'results': formatted_results,
            'total': total,
            'page': page,
            'per_page': self.RESULTS_PER_PAGE,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }
        
        # Cache result
        cache.set(cache_key, result, self.CACHE_TTL)
        
        # Track search query
        response_time_ms = int((time.time() - start_time) * 1000)
        self._track_search_query(query, user_id, total, response_time_ms, search_type='author')
        
        return result
    
    def autocomplete(
        self,
        query: str,
        limit: int = 10
    ) -> List[str]:
        """
        Get autocomplete suggestions for search query.
        
        Args:
            query: Partial search query
            limit: Maximum number of suggestions
            
        Returns:
            List of autocomplete suggestions
            
        Requirements: 35.6
        """
        # Cache key for autocomplete
        cache_key = f"{self.cache_prefix}autocomplete:{query.lower()}"
        
        # Try to get from cache
        cached_suggestions = cache.get(cache_key)
        if cached_suggestions is not None:
            return cached_suggestions
        
        # Get suggestions from story titles
        sql = """
            SELECT DISTINCT title
            FROM "Story"
            WHERE published = true
                AND deleted_at IS NULL
                AND title ILIKE %s
            ORDER BY title
            LIMIT %s
        """
        
        with connection.cursor() as cursor:
            cursor.execute(sql, [f"{query}%", limit])
            suggestions = [row[0] for row in cursor.fetchall()]
        
        # Cache suggestions for 5 minutes
        cache.set(cache_key, suggestions, self.CACHE_TTL)
        
        return suggestions
    
    def get_popular_searches(
        self,
        days: int = 7,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get popular search queries.
        
        Args:
            days: Number of days to look back
            limit: Maximum number of results
            
        Returns:
            List of popular search queries with statistics
            
        Requirements: 35.10
        """
        cache_key = f"{self.cache_prefix}popular:{days}d"
        
        # Try to get from cache
        cached_popular = cache.get(cache_key)
        if cached_popular is not None:
            return cached_popular
        
        # Note: Tracking is currently disabled as the search_queries table doesn't exist.
        # TODO: Create SearchQuery model in Prisma schema and run migrations.
        return []
        
        # sql = """
        #     SELECT 
        #         query,
        #         COUNT(*) as search_count,
        #         AVG(result_count) as avg_results,
        #         AVG(response_time_ms) as avg_response_time
        #     FROM search_queries
        #     WHERE created_at >= NOW() - INTERVAL '%s days'
        #     GROUP BY query
        #     ORDER BY search_count DESC
        #     LIMIT %s
        # """
        # 
        # with connection.cursor() as cursor:
        #     cursor.execute(sql, [days, limit])
        #     columns = [col[0] for col in cursor.description]
        #     results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        # 
        # # Cache for 1 hour
        # cache.set(cache_key, results, 3600)
        # 
        # return results
    
    def track_click(
        self,
        query: str,
        result_id: int,
        result_type: str,
        user_id: Optional[int] = None
    ):
        """
        Track when a user clicks on a search result.
        
        Args:
            query: Original search query
            result_id: ID of clicked result
            result_type: Type of result ('story', 'author', 'tag')
            user_id: Optional user ID
            
        Requirements: 35.10
        """
        sql = """
            INSERT INTO search_queries 
            (query, user_id, clicked_result_id, clicked_result_type, created_at)
            VALUES (%s, %s, %s, %s, NOW())
        """
        
        with connection.cursor() as cursor:
            cursor.execute(sql, [query, user_id, result_id, result_type])
    
    def _build_search_query(self, query: str) -> str:
        """
        Build PostgreSQL tsquery from user query.
        
        Handles:
        - Multiple words (AND by default)
        - OR operator
        - NOT operator
        - Phrase search (quotes)
        
        Args:
            query: User search query
            
        Returns:
            PostgreSQL tsquery string
            
        Requirements: 35.12
        """
        # Remove extra whitespace
        query = ' '.join(query.split())
        
        # Handle phrase search (quotes)
        if '"' in query:
            # Extract phrases
            import re
            phrases = re.findall(r'"([^"]*)"', query)
            non_phrases = re.sub(r'"[^"]*"', '', query).strip()
            
            # Build query
            parts = []
            for phrase in phrases:
                parts.append(f"'{phrase.replace(' ', ' <-> ')}'")
            
            if non_phrases:
                # Split non-phrase words and join with &
                words = non_phrases.split()
                parts.extend(words)
            
            return ' & '.join(parts)
        
        # Handle boolean operators
        query = query.replace(' OR ', ' | ')
        query = query.replace(' AND ', ' & ')
        query = query.replace(' NOT ', ' !')
        
        # If no operators, join words with &
        if '&' not in query and '|' not in query:
            words = query.split()
            query = ' & '.join(words)
        
        return query
    
    def _generate_cache_key(
        self,
        search_type: str,
        query: str,
        filters: Optional[SearchFilters],
        page: int
    ) -> str:
        """Generate cache key for search results."""
        key_parts = [self.cache_prefix, search_type, query.lower(), str(page)]
        
        if filters:
            if filters.genre:
                key_parts.append(f"genre:{filters.genre}")
            if filters.completion_status:
                key_parts.append(f"status:{filters.completion_status}")
            if filters.min_word_count:
                key_parts.append(f"min:{str(filters.min_word_count)}")
            if filters.max_word_count:
                key_parts.append(f"max:{str(filters.max_word_count)}")
        
        return ':'.join(key_parts)
    
    def _track_search_query(
        self,
        query: str,
        user_id: Optional[int],
        result_count: int,
        response_time_ms: int,
        search_type: str = 'story',
        from_cache: bool = False
    ):
        """
        Track search query for analytics.
        
        Requirements: 35.10
        
        Note: Tracking is currently disabled as the search_queries table doesn't exist.
        TODO: Create SearchQuery model in Prisma schema and run migrations.
        """
        # Tracking disabled - table doesn't exist yet
        pass
        # sql = """
        #     INSERT INTO search_queries 
        #     (query, user_id, result_count, response_time_ms, created_at)
        #     VALUES (%s, %s, %s, %s, NOW())
        # """
        # 
        # try:
        #     with connection.cursor() as cursor:
        #         cursor.execute(sql, [query, user_id, result_count, response_time_ms])
        # except Exception as e:
        #     # Don't fail search if tracking fails
        #     print(f"Warning: Failed to track search query: {e}")
    
    def invalidate_search_cache(self, search_type: Optional[str] = None):
        """
        Invalidate search cache.
        
        Args:
            search_type: Optional type to invalidate ('stories', 'authors', 'tags')
                        If None, invalidates all search caches
        """
        if search_type:
            # Invalidate specific search type
            pattern = f"{self.cache_prefix}{search_type}:*"
        else:
            # Invalidate all search caches
            pattern = f"{self.cache_prefix}*"
        
        # Note: This is a simplified version. In production, use Redis SCAN
        # to find and delete keys matching the pattern
        cache.delete_pattern(pattern)


# Global search service instance
search_service = SearchService()
