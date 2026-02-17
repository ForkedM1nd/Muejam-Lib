"""
Cache Manager with multi-layer caching (L1: in-memory LRU, L2: Redis).

This module implements a two-tier caching strategy:
- L1: In-memory LRU cache for hot data (1000 entries, 60s TTL)
- L2: Redis cache for distributed caching with configurable TTL

The cache manager checks L1 first, then L2, and populates both layers
on cache misses. Invalidation affects both layers to maintain consistency.
"""

import json
import time
from collections import OrderedDict
from datetime import datetime, timedelta
from threading import Lock
from typing import Any, List, Optional, Set

import redis
from redis.exceptions import RedisError

try:
    from django.conf import settings
    DJANGO_AVAILABLE = True
except ImportError:
    DJANGO_AVAILABLE = False
    settings = None

from .models import CacheEntry, CacheStats, CacheWarmQuery


class LRUCache:
    """
    Thread-safe in-memory LRU cache with TTL support.
    
    Implements Least Recently Used eviction policy with a maximum size
    of 1000 entries and default TTL of 60 seconds.
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 60):
        """
        Initialize LRU cache.
        
        Args:
            max_size: Maximum number of entries (default: 1000)
            default_ttl: Default time-to-live in seconds (default: 60)
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.lock = Lock()
        self.hits = 0
        self.misses = 0
        self.evictions = 0
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value if found and not expired, None otherwise
        """
        with self.lock:
            if key not in self.cache:
                self.misses += 1
                return None
            
            entry = self.cache[key]
            
            # Check if entry has expired
            age = (datetime.now() - entry.created_at).total_seconds()
            if age > entry.ttl:
                # Entry expired, remove it
                del self.cache[key]
                self.misses += 1
                return None
            
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            entry.access_count += 1
            self.hits += 1
            return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None, tags: Optional[List[str]] = None) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if not specified)
            tags: Optional tags for tag-based invalidation
        """
        with self.lock:
            # Use default TTL if not specified
            actual_ttl = ttl if ttl is not None else self.default_ttl
            
            # Create cache entry
            entry = CacheEntry(
                key=key,
                value=value,
                ttl=actual_ttl,
                tags=tags or [],
                created_at=datetime.now(),
                access_count=0
            )
            
            # If key exists, update it
            if key in self.cache:
                self.cache[key] = entry
                self.cache.move_to_end(key)
            else:
                # Check if we need to evict
                if len(self.cache) >= self.max_size:
                    # Remove least recently used item
                    self.cache.popitem(last=False)
                    self.evictions += 1
                
                self.cache[key] = entry
    
    def delete(self, key: str) -> bool:
        """
        Delete entry from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key was found and deleted, False otherwise
        """
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
    
    def delete_by_tags(self, tags: List[str]) -> int:
        """
        Delete all entries with any of the specified tags.
        
        Args:
            tags: List of tags
            
        Returns:
            Number of entries deleted
        """
        with self.lock:
            tag_set = set(tags)
            keys_to_delete = []
            
            for key, entry in self.cache.items():
                if any(tag in tag_set for tag in entry.tags):
                    keys_to_delete.append(key)
            
            for key in keys_to_delete:
                del self.cache[key]
            
            return len(keys_to_delete)
    
    def clear(self) -> None:
        """Clear all entries from cache."""
        with self.lock:
            self.cache.clear()
    
    def get_stats(self) -> CacheStats:
        """
        Get cache statistics.
        
        Returns:
            CacheStats object with current statistics
        """
        with self.lock:
            total_requests = self.hits + self.misses
            hit_rate = self.hits / total_requests if total_requests > 0 else 0.0
            
            return CacheStats(
                hits=self.hits,
                misses=self.misses,
                hit_rate=hit_rate,
                evictions=self.evictions,
                size=len(self.cache),
                max_size=self.max_size
            )


class CacheManager:
    """
    Multi-layer cache manager with L1 (in-memory) and L2 (Redis) caches.
    
    Implements a two-tier caching strategy:
    - L1: Fast in-memory LRU cache for hot data
    - L2: Distributed Redis cache for shared caching across instances
    
    Cache operations check L1 first, then L2, and populate both layers
    on cache misses. Invalidation affects both layers to maintain consistency.
    """
    
    def __init__(
        self,
        redis_url: Optional[str] = None,
        l1_max_size: Optional[int] = None,
        l1_default_ttl: Optional[int] = None
    ):
        """
        Initialize cache manager.
        
        Args:
            redis_url: Redis connection URL (defaults to settings.VALKEY_URL)
            l1_max_size: Maximum size of L1 cache (defaults to settings.L1_CACHE_MAX_SIZE)
            l1_default_ttl: Default TTL for L1 cache in seconds (defaults to settings.L1_CACHE_DEFAULT_TTL)
        """
        # Use settings values if not provided and Django is available
        if redis_url is None:
            if DJANGO_AVAILABLE and settings:
                redis_url = getattr(settings, 'VALKEY_URL', 'redis://localhost:6379/0')
            else:
                redis_url = 'redis://localhost:6379/0'
        
        if l1_max_size is None:
            if DJANGO_AVAILABLE and settings:
                l1_max_size = getattr(settings, 'L1_CACHE_MAX_SIZE', 1000)
            else:
                l1_max_size = 1000
        
        if l1_default_ttl is None:
            if DJANGO_AVAILABLE and settings:
                l1_default_ttl = getattr(settings, 'L1_CACHE_DEFAULT_TTL', 60)
            else:
                l1_default_ttl = 60
        
        self.l1_cache = LRUCache(max_size=l1_max_size, default_ttl=l1_default_ttl)
        
        # Initialize Redis client
        try:
            self.l2_cache = redis.from_url(redis_url, decode_responses=False)
            # Test connection
            self.l2_cache.ping()
            self.redis_available = True
        except Exception as e:
            print(f"Warning: Redis connection failed: {e}. Operating without L2 cache.")
            self.l2_cache = None
            self.redis_available = False
        
        # Tag tracking for Redis (store tag -> keys mapping)
        self.tag_prefix = "cache:tag:"
        self.key_prefix = "cache:data:"
    
    def get_ttl_for_type(self, cache_type: str) -> int:
        """
        Get configured TTL for a specific cache type.
        
        Args:
            cache_type: Type of cached data (e.g., 'user_profile', 'story_metadata')
            
        Returns:
            TTL in seconds for the specified cache type
        """
        if DJANGO_AVAILABLE and settings:
            cache_ttl_config = getattr(settings, 'CACHE_TTL', {})
            return cache_ttl_config.get(cache_type, cache_ttl_config.get('default', 300))
        else:
            # Default TTL when Django is not available
            return 300
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache (checks L1 then L2).
        
        Args:
            key: Cache key
            
        Returns:
            Cached value if found, None otherwise
        """
        # Check L1 cache first
        value = self.l1_cache.get(key)
        if value is not None:
            return value
        
        # Check L2 cache if available
        if self.redis_available and self.l2_cache:
            try:
                redis_key = self.key_prefix + key
                data = self.l2_cache.get(redis_key)
                
                if data is not None:
                    # Deserialize value
                    value = json.loads(data)
                    
                    # Get TTL from Redis
                    ttl = self.l2_cache.ttl(redis_key)
                    if ttl < 0:
                        ttl = self.l1_cache.default_ttl
                    
                    # Populate L1 cache
                    self.l1_cache.set(key, value, ttl=ttl)
                    
                    return value
            except (RedisError, json.JSONDecodeError) as e:
                print(f"Warning: Redis get failed for key {key}: {e}")
        
        return None
    
    def set(self, key: str, value: Any, ttl: int, tags: Optional[List[str]] = None) -> None:
        """
        Set value in both cache layers.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds
            tags: Optional tags for tag-based invalidation
        """
        # Set in L1 cache
        self.l1_cache.set(key, value, ttl=ttl, tags=tags)
        
        # Set in L2 cache if available
        if self.redis_available and self.l2_cache:
            try:
                redis_key = self.key_prefix + key
                
                # Serialize value
                data = json.dumps(value)
                
                # Set with TTL
                self.l2_cache.setex(redis_key, ttl, data)
                
                # Store tag associations
                if tags:
                    for tag in tags:
                        tag_key = self.tag_prefix + tag
                        self.l2_cache.sadd(tag_key, key)
                        # Set expiration on tag set (use max TTL to avoid premature deletion)
                        self.l2_cache.expire(tag_key, ttl * 2)
            except Exception as e:
                print(f"Warning: Redis set failed for key {key}: {e}")
    
    def invalidate(self, key: str) -> None:
        """
        Invalidate cache entry in both layers.
        
        Args:
            key: Cache key to invalidate
        """
        # Invalidate in L1
        self.l1_cache.delete(key)
        
        # Invalidate in L2 if available
        if self.redis_available and self.l2_cache:
            try:
                redis_key = self.key_prefix + key
                self.l2_cache.delete(redis_key)
            except Exception as e:
                print(f"Warning: Redis delete failed for key {key}: {e}")
    
    def invalidate_by_tags(self, tags: List[str]) -> None:
        """
        Invalidate all entries with specified tags in both layers.
        
        Args:
            tags: List of tags
        """
        # Invalidate in L1
        self.l1_cache.delete_by_tags(tags)
        
        # Invalidate in L2 if available
        if self.redis_available and self.l2_cache:
            try:
                for tag in tags:
                    tag_key = self.tag_prefix + tag
                    
                    # Get all keys with this tag
                    keys = self.l2_cache.smembers(tag_key)
                    
                    if keys:
                        # Delete all associated cache entries
                        redis_keys = [self.key_prefix + k.decode() if isinstance(k, bytes) else self.key_prefix + k for k in keys]
                        self.l2_cache.delete(*redis_keys)
                        
                        # Delete the tag set itself
                        self.l2_cache.delete(tag_key)
            except Exception as e:
                print(f"Warning: Redis tag-based invalidation failed: {e}")
    
    def warm_cache(self, queries: List[CacheWarmQuery]) -> None:
        """
        Pre-populate cache with predictable queries.
        
        Args:
            queries: List of cache warming queries
        """
        for query_config in queries:
            # Generate cache key from query and params
            key = self._generate_key(query_config.query, query_config.params)
            
            # Note: In a real implementation, this would execute the query
            # and cache the result. For now, we just set up the cache structure.
            # The actual query execution would be done by the caller.
            pass
    
    def get_stats(self) -> CacheStats:
        """
        Get cache statistics (L1 only).
        
        Returns:
            CacheStats object with L1 cache statistics
        """
        return self.l1_cache.get_stats()
    
    def _generate_key(self, query: str, params: dict) -> str:
        """
        Generate cache key from query and parameters.
        
        Args:
            query: Query string
            params: Query parameters
            
        Returns:
            Cache key string
        """
        # Simple key generation - in production, use a more robust hashing
        param_str = json.dumps(params, sort_keys=True)
        return f"{hash(query)}:{hash(param_str)}"
