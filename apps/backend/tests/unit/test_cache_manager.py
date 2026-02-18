"""
Unit tests for CacheManager with multi-layer caching.

Tests cover:
- L1 (in-memory LRU) cache operations
- L2 (Redis) cache operations
- Multi-layer cache coordination
- Cache invalidation (single key and tag-based)
- TTL expiration
- Cache statistics
"""

import json
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

import pytest

from infrastructure.cache_manager import LRUCache, CacheManager
from infrastructure.models import CacheEntry, CacheStats


class TestLRUCache:
    """Test cases for LRU cache implementation."""
    
    def test_basic_get_set(self):
        """Test basic get and set operations."""
        cache = LRUCache(max_size=10, default_ttl=60)
        
        # Set a value
        cache.set("key1", "value1")
        
        # Get the value
        assert cache.get("key1") == "value1"
    
    def test_cache_miss(self):
        """Test cache miss returns None."""
        cache = LRUCache(max_size=10, default_ttl=60)
        
        assert cache.get("nonexistent") is None
    
    def test_lru_eviction(self):
        """Test LRU eviction when max size is reached."""
        cache = LRUCache(max_size=3, default_ttl=60)
        
        # Fill cache to capacity
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        # Add one more - should evict key1 (least recently used)
        cache.set("key4", "value4")
        
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"
    
    def test_lru_access_updates_order(self):
        """Test that accessing an entry updates its position in LRU order."""
        cache = LRUCache(max_size=3, default_ttl=60)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        # Access key1 to make it most recently used
        cache.get("key1")
        
        # Add key4 - should evict key2 (now least recently used)
        cache.set("key4", "value4")
        
        assert cache.get("key1") == "value1"
        assert cache.get("key2") is None
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"
    
    def test_ttl_expiration(self):
        """Test that entries expire after TTL."""
        cache = LRUCache(max_size=10, default_ttl=1)  # 1 second TTL
        
        cache.set("key1", "value1")
        
        # Should be available immediately
        assert cache.get("key1") == "value1"
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should be expired now
        assert cache.get("key1") is None
    
    def test_custom_ttl(self):
        """Test setting custom TTL per entry."""
        cache = LRUCache(max_size=10, default_ttl=60)
        
        cache.set("key1", "value1", ttl=1)  # 1 second TTL
        cache.set("key2", "value2", ttl=10)  # 10 second TTL
        
        # Both should be available immediately
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        
        # Wait for key1 to expire
        time.sleep(1.1)
        
        # key1 should be expired, key2 should still be available
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"
    
    def test_delete(self):
        """Test deleting entries."""
        cache = LRUCache(max_size=10, default_ttl=60)
        
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        
        # Delete the entry
        result = cache.delete("key1")
        assert result is True
        assert cache.get("key1") is None
        
        # Deleting non-existent key returns False
        result = cache.delete("key1")
        assert result is False
    
    def test_tag_based_invalidation(self):
        """Test tag-based cache invalidation."""
        cache = LRUCache(max_size=10, default_ttl=60)
        
        cache.set("user:1", "data1", tags=["user", "profile"])
        cache.set("user:2", "data2", tags=["user", "profile"])
        cache.set("post:1", "data3", tags=["post"])
        
        # Invalidate by tag
        deleted = cache.delete_by_tags(["user"])
        
        assert deleted == 2
        assert cache.get("user:1") is None
        assert cache.get("user:2") is None
        assert cache.get("post:1") == "data3"
    
    def test_clear(self):
        """Test clearing all entries."""
        cache = LRUCache(max_size=10, default_ttl=60)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        cache.clear()
        
        assert cache.get("key1") is None
        assert cache.get("key2") is None
    
    def test_statistics(self):
        """Test cache statistics tracking."""
        cache = LRUCache(max_size=10, default_ttl=60)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        # Generate some hits and misses
        cache.get("key1")  # hit
        cache.get("key1")  # hit
        cache.get("key3")  # miss
        
        stats = cache.get_stats()
        
        assert stats.hits == 2
        assert stats.misses == 1
        assert stats.hit_rate == 2/3
        assert stats.size == 2
        assert stats.max_size == 10


class TestCacheManager:
    """Test cases for multi-layer CacheManager."""
    
    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        mock = MagicMock()
        mock.ping.return_value = True
        mock.get.return_value = None
        mock.setex.return_value = True
        mock.delete.return_value = 1
        mock.sadd.return_value = 1
        mock.expire.return_value = True
        mock.smembers.return_value = set()
        mock.ttl.return_value = 60
        return mock
    
    @pytest.fixture
    def cache_manager(self, mock_redis):
        """Create a CacheManager with mocked Redis."""
        with patch('infrastructure.cache_manager.redis.from_url', return_value=mock_redis):
            manager = CacheManager(
                redis_url="redis://localhost:6379/0",
                l1_max_size=1000,
                l1_default_ttl=60
            )
            return manager
    
    def test_initialization_with_redis(self, mock_redis):
        """Test CacheManager initialization with Redis available."""
        with patch('infrastructure.cache_manager.redis.from_url', return_value=mock_redis):
            manager = CacheManager()
            
            assert manager.redis_available is True
            assert manager.l1_cache is not None
            assert manager.l2_cache is not None
    
    def test_initialization_without_redis(self):
        """Test CacheManager initialization when Redis is unavailable."""
        with patch('infrastructure.cache_manager.redis.from_url', side_effect=Exception("Connection failed")):
            manager = CacheManager()
            
            assert manager.redis_available is False
            assert manager.l1_cache is not None
            assert manager.l2_cache is None
    
    def test_get_from_l1(self, cache_manager):
        """Test getting value from L1 cache."""
        # Set in L1
        cache_manager.l1_cache.set("key1", "value1")
        
        # Get should return from L1
        result = cache_manager.get("key1")
        
        assert result == "value1"
        # Redis should not be called
        cache_manager.l2_cache.get.assert_not_called()
    
    def test_get_from_l2_populates_l1(self, cache_manager, mock_redis):
        """Test getting value from L2 populates L1."""
        # Mock Redis to return a value
        mock_redis.get.return_value = json.dumps("value1").encode()
        mock_redis.ttl.return_value = 60
        
        # Get should check L1 (miss), then L2 (hit)
        result = cache_manager.get("key1")
        
        assert result == "value1"
        # L1 should now have the value
        assert cache_manager.l1_cache.get("key1") == "value1"
    
    def test_get_miss_both_layers(self, cache_manager):
        """Test cache miss in both layers."""
        result = cache_manager.get("nonexistent")
        
        assert result is None
    
    def test_set_both_layers(self, cache_manager, mock_redis):
        """Test setting value in both cache layers."""
        cache_manager.set("key1", "value1", ttl=60, tags=["tag1"])
        
        # L1 should have the value
        assert cache_manager.l1_cache.get("key1") == "value1"
        
        # Redis should have been called
        mock_redis.setex.assert_called_once()
        mock_redis.sadd.assert_called_once()
    
    def test_invalidate_both_layers(self, cache_manager, mock_redis):
        """Test invalidating entry in both layers."""
        # Set in both layers
        cache_manager.set("key1", "value1", ttl=60)
        
        # Invalidate
        cache_manager.invalidate("key1")
        
        # L1 should not have the value
        assert cache_manager.l1_cache.get("key1") is None
        
        # Redis delete should have been called
        mock_redis.delete.assert_called()
    
    def test_invalidate_by_tags_both_layers(self, cache_manager, mock_redis):
        """Test tag-based invalidation in both layers."""
        # Set entries with tags
        cache_manager.set("key1", "value1", ttl=60, tags=["tag1"])
        cache_manager.set("key2", "value2", ttl=60, tags=["tag1"])
        
        # Mock Redis to return keys for the tag
        mock_redis.smembers.return_value = {b"key1", b"key2"}
        
        # Invalidate by tag
        cache_manager.invalidate_by_tags(["tag1"])
        
        # L1 should not have the values
        assert cache_manager.l1_cache.get("key1") is None
        assert cache_manager.l1_cache.get("key2") is None
        
        # Redis should have been called
        mock_redis.smembers.assert_called()
        assert mock_redis.delete.call_count >= 1
    
    def test_get_stats(self, cache_manager):
        """Test getting cache statistics."""
        cache_manager.set("key1", "value1", ttl=60)
        cache_manager.get("key1")
        cache_manager.get("key2")
        
        stats = cache_manager.get_stats()
        
        assert isinstance(stats, CacheStats)
        assert stats.hits >= 1
        assert stats.misses >= 1
    
    def test_redis_failure_graceful_degradation(self, cache_manager, mock_redis):
        """Test that Redis failures don't break the cache manager."""
        # Make Redis operations fail
        mock_redis.setex.side_effect = Exception("Redis error")
        
        # Should still work with L1 only
        cache_manager.set("key1", "value1", ttl=60)
        
        # L1 should have the value
        assert cache_manager.l1_cache.get("key1") == "value1"
    
    def test_cache_manager_without_redis(self):
        """Test CacheManager operates correctly without Redis."""
        with patch('infrastructure.cache_manager.redis.from_url', side_effect=Exception("No Redis")):
            manager = CacheManager()
            
            # Should still work with L1 only
            manager.set("key1", "value1", ttl=60)
            assert manager.get("key1") == "value1"
            
            manager.invalidate("key1")
            assert manager.get("key1") is None
