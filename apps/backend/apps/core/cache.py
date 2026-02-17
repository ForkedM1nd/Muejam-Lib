"""Cache management utilities."""
from django.core.cache import cache
from typing import Optional, Callable, Any
import hashlib
import json


class CacheManager:
    """
    Cache manager with TTL configurations for different content types.
    
    Implements cache-aside pattern with Valkey backend.
    """
    
    # TTL configurations (in seconds)
    TTL_CONFIG = {
        'discover_feed': 180,        # 3 minutes
        'trending_feed': 300,        # 5 minutes
        'whispers_feed': 60,         # 1 minute
        'story_metadata': 600,       # 10 minutes
        'search_suggest': 1200,      # 20 minutes
        'for_you_feed': 7200,        # 2 hours
        'user_profile': 300,         # 5 minutes
    }
    
    @staticmethod
    def make_key(prefix: str, **params) -> str:
        """
        Generate cache key from prefix and parameters.
        
        Args:
            prefix: Cache key prefix (e.g., 'discover_feed')
            **params: Key-value parameters to include in key
            
        Returns:
            Cache key string
            
        Example:
            make_key('discover_feed', tab='trending', cursor='abc123')
            # Returns: 'discover_feed:a1b2c3d4'
        """
        param_str = json.dumps(params, sort_keys=True)
        param_hash = hashlib.md5(param_str.encode()).hexdigest()[:8]
        return f"{prefix}:{param_hash}"
    
    @staticmethod
    def get_or_set(
        key: str,
        fetch_func: Callable,
        ttl: int,
        *args,
        **kwargs
    ) -> Any:
        """
        Get from cache or fetch and cache.
        
        Args:
            key: Cache key
            fetch_func: Function to call if cache miss
            ttl: Time to live in seconds
            *args: Arguments to pass to fetch_func
            **kwargs: Keyword arguments to pass to fetch_func
            
        Returns:
            Cached or fetched data
            
        Example:
            data = CacheManager.get_or_set(
                'story:123',
                fetch_story,
                CacheManager.TTL_CONFIG['story_metadata'],
                story_id='123'
            )
        """
        cached = cache.get(key)
        if cached is not None:
            return cached
        
        result = fetch_func(*args, **kwargs)
        cache.set(key, result, ttl)
        return result
    
    @staticmethod
    def invalidate(key: str):
        """
        Invalidate a specific cache key.
        
        Args:
            key: Cache key to invalidate
        """
        cache.delete(key)
    
    @staticmethod
    def invalidate_pattern(pattern: str):
        """
        Invalidate all keys matching pattern.
        
        Note: This requires Valkey SCAN command support.
        For now, we'll use Django's cache.delete_pattern if available.
        
        Args:
            pattern: Pattern to match (e.g., 'discover_feed:*')
        """
        try:
            # Try to use delete_pattern if available (Redis/Valkey backend)
            cache.delete_pattern(pattern)
        except AttributeError:
            # Fallback: delete_pattern not available
            # In production, ensure using Redis/Valkey cache backend
            pass


class CacheInvalidator:
    """
    Handle cache invalidation on data changes.
    """
    
    @staticmethod
    def on_story_published(story_id: str):
        """
        Invalidate caches when story is published.
        
        Args:
            story_id: ID of published story
        """
        # Invalidate discover feeds
        CacheManager.invalidate_pattern('discover_feed:*')
        # Invalidate story metadata
        CacheManager.invalidate(f'story:{story_id}')
    
    @staticmethod
    def on_whisper_created(whisper_id: str, scope: str, story_id: str = None):
        """
        Invalidate caches when whisper is created.
        
        Args:
            whisper_id: ID of created whisper
            scope: Whisper scope (GLOBAL, STORY, HIGHLIGHT)
            story_id: Story ID if scope is STORY
        """
        # Invalidate global whispers feed
        if scope == 'GLOBAL':
            CacheManager.invalidate_pattern('whispers_feed:global:*')
        # Invalidate story-specific feed
        elif scope == 'STORY' and story_id:
            CacheManager.invalidate_pattern(f'whispers_feed:story:{story_id}:*')
    
    @staticmethod
    def on_user_profile_updated(user_id: str):
        """
        Invalidate caches when profile is updated.
        
        Args:
            user_id: ID of updated user
        """
        CacheManager.invalidate(f'user_profile:{user_id}')
