"""
Database Query Caching Utilities

This module provides decorators and utilities for caching expensive database queries
using the CacheManager (L1 + L2 caching).

Requirements: 33.3, 33.4
"""

import functools
import hashlib
import json
import logging
from typing import Any, Callable, List, Optional, Union

from django.db.models import QuerySet, Model
from django.core.serializers import serialize, deserialize

from .cache_manager import CacheManager

logger = logging.getLogger(__name__)

# Initialize global cache manager
cache_manager = CacheManager()

# Default TTL for database queries (5 minutes as per requirement 33.4)
DEFAULT_QUERY_TTL = 300  # 5 minutes in seconds


def generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    Generate a cache key from function arguments.
    
    Args:
        prefix: Cache key prefix (usually function name)
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        Cache key string
    """
    # Create a stable representation of arguments
    key_parts = [prefix]
    
    # Add positional arguments
    for arg in args:
        if isinstance(arg, (str, int, float, bool)):
            key_parts.append(str(arg))
        elif isinstance(arg, Model):
            # For Django models, use pk
            key_parts.append(f"{arg.__class__.__name__}:{arg.pk}")
        else:
            # For other types, use repr
            key_parts.append(repr(arg))
    
    # Add keyword arguments (sorted for consistency)
    for key in sorted(kwargs.keys()):
        value = kwargs[key]
        if isinstance(value, (str, int, float, bool)):
            key_parts.append(f"{key}={value}")
        elif isinstance(value, Model):
            key_parts.append(f"{key}={value.__class__.__name__}:{value.pk}")
        else:
            key_parts.append(f"{key}={repr(value)}")
    
    # Create hash of the key parts
    key_string = ":".join(key_parts)
    key_hash = hashlib.md5(key_string.encode()).hexdigest()
    
    return f"db_query:{prefix}:{key_hash}"


def cache_query(
    ttl: int = DEFAULT_QUERY_TTL,
    tags: Optional[List[str]] = None,
    key_prefix: Optional[str] = None
):
    """
    Decorator to cache database query results.
    
    Usage:
        @cache_query(ttl=300, tags=['user', 'profile'])
        def get_user_profile(user_id):
            return UserProfile.objects.get(user_id=user_id)
    
    Args:
        ttl: Time-to-live in seconds (default: 300 = 5 minutes)
        tags: Tags for cache invalidation
        key_prefix: Custom cache key prefix (defaults to function name)
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            prefix = key_prefix or func.__name__
            cache_key = generate_cache_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_value = cache_manager.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_value
            
            # Cache miss - execute function
            logger.debug(f"Cache miss for {cache_key}")
            result = func(*args, **kwargs)
            
            # Cache the result
            cache_manager.set(cache_key, result, ttl=ttl, tags=tags)
            
            return result
        
        return wrapper
    return decorator


def cache_queryset(
    ttl: int = DEFAULT_QUERY_TTL,
    tags: Optional[List[str]] = None,
    key_prefix: Optional[str] = None
):
    """
    Decorator to cache Django QuerySet results.
    
    Converts QuerySet to list before caching to avoid lazy evaluation issues.
    
    Usage:
        @cache_queryset(ttl=300, tags=['story', 'listing'])
        def get_featured_stories():
            return Story.objects.filter(featured=True)
    
    Args:
        ttl: Time-to-live in seconds (default: 300 = 5 minutes)
        tags: Tags for cache invalidation
        key_prefix: Custom cache key prefix (defaults to function name)
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            prefix = key_prefix or func.__name__
            cache_key = generate_cache_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_value = cache_manager.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_value
            
            # Cache miss - execute function
            logger.debug(f"Cache miss for {cache_key}")
            result = func(*args, **kwargs)
            
            # Convert QuerySet to list for caching
            if isinstance(result, QuerySet):
                result_list = list(result)
                cache_manager.set(cache_key, result_list, ttl=ttl, tags=tags)
                return result_list
            else:
                cache_manager.set(cache_key, result, ttl=ttl, tags=tags)
                return result
        
        return wrapper
    return decorator


def invalidate_cache(key_prefix: str, *args, **kwargs):
    """
    Invalidate cache for a specific query.
    
    Args:
        key_prefix: Cache key prefix (usually function name)
        *args: Positional arguments used in original query
        **kwargs: Keyword arguments used in original query
    """
    cache_key = generate_cache_key(key_prefix, *args, **kwargs)
    cache_manager.invalidate(cache_key)
    logger.debug(f"Invalidated cache for {cache_key}")


def invalidate_by_tags(tags: Union[str, List[str]]):
    """
    Invalidate all cache entries with specified tags.
    
    Args:
        tags: Tag or list of tags to invalidate
    """
    if isinstance(tags, str):
        tags = [tags]
    
    cache_manager.invalidate_by_tags(tags)
    logger.debug(f"Invalidated cache for tags: {tags}")


class CachedQueryMixin:
    """
    Mixin for Django models to provide automatic query caching.
    
    Usage:
        class Story(CachedQueryMixin, models.Model):
            cache_tags = ['story']
            cache_ttl = 300
            
            @classmethod
            def get_featured(cls):
                return cls.cached_query(
                    'featured_stories',
                    lambda: cls.objects.filter(featured=True)
                )
    """
    
    cache_tags: List[str] = []
    cache_ttl: int = DEFAULT_QUERY_TTL
    
    @classmethod
    def cached_query(
        cls,
        key_suffix: str,
        query_func: Callable,
        ttl: Optional[int] = None,
        tags: Optional[List[str]] = None
    ) -> Any:
        """
        Execute a query with caching.
        
        Args:
            key_suffix: Suffix for cache key
            query_func: Function that executes the query
            ttl: Time-to-live (defaults to cls.cache_ttl)
            tags: Tags for invalidation (defaults to cls.cache_tags)
            
        Returns:
            Query result
        """
        # Use class defaults if not specified
        actual_ttl = ttl if ttl is not None else cls.cache_ttl
        actual_tags = tags if tags is not None else cls.cache_tags
        
        # Generate cache key
        cache_key = f"db_query:{cls.__name__}:{key_suffix}"
        
        # Try to get from cache
        cached_value = cache_manager.get(cache_key)
        if cached_value is not None:
            logger.debug(f"Cache hit for {cache_key}")
            return cached_value
        
        # Cache miss - execute query
        logger.debug(f"Cache miss for {cache_key}")
        result = query_func()
        
        # Convert QuerySet to list if needed
        if isinstance(result, QuerySet):
            result = list(result)
        
        # Cache the result
        cache_manager.set(cache_key, result, ttl=actual_ttl, tags=actual_tags)
        
        return result
    
    @classmethod
    def invalidate_cache_by_tags(cls, tags: Optional[List[str]] = None):
        """
        Invalidate cache for this model.
        
        Args:
            tags: Tags to invalidate (defaults to cls.cache_tags)
        """
        actual_tags = tags if tags is not None else cls.cache_tags
        invalidate_by_tags(actual_tags)


# Pre-configured decorators for common query types
def cache_user_query(ttl: int = DEFAULT_QUERY_TTL):
    """Cache user-related queries."""
    return cache_query(ttl=ttl, tags=['user'])


def cache_story_query(ttl: int = DEFAULT_QUERY_TTL):
    """Cache story-related queries."""
    return cache_query(ttl=ttl, tags=['story'])


def cache_comment_query(ttl: int = DEFAULT_QUERY_TTL):
    """Cache comment-related queries."""
    return cache_query(ttl=ttl, tags=['comment'])


def cache_notification_query(ttl: int = DEFAULT_QUERY_TTL):
    """Cache notification-related queries."""
    return cache_query(ttl=ttl, tags=['notification'])


# Example usage documentation
USAGE_EXAMPLES = """
# Example 1: Cache a simple query
@cache_query(ttl=300, tags=['user', 'profile'])
def get_user_profile(user_id):
    return UserProfile.objects.get(user_id=user_id)

# Example 2: Cache a QuerySet
@cache_queryset(ttl=300, tags=['story', 'featured'])
def get_featured_stories():
    return Story.objects.filter(featured=True).select_related('author')

# Example 3: Invalidate cache on update
def update_user_profile(user_id, **updates):
    profile = UserProfile.objects.get(user_id=user_id)
    for key, value in updates.items():
        setattr(profile, key, value)
    profile.save()
    
    # Invalidate cache
    invalidate_by_tags(['user', 'profile'])

# Example 4: Use CachedQueryMixin
class Story(CachedQueryMixin, models.Model):
    cache_tags = ['story']
    cache_ttl = 300
    
    title = models.CharField(max_length=200)
    featured = models.BooleanField(default=False)
    
    @classmethod
    def get_featured(cls):
        return cls.cached_query(
            'featured_stories',
            lambda: cls.objects.filter(featured=True)
        )
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Invalidate cache on save
        self.invalidate_cache_by_tags()

# Example 5: Use pre-configured decorators
@cache_story_query(ttl=600)
def get_trending_stories(limit=10):
    return Story.objects.filter(
        published=True
    ).order_by('-view_count')[:limit]
"""
