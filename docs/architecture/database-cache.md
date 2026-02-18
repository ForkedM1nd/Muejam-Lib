# Database Query Caching

This document describes the database query caching implementation for optimizing expensive database queries.

## Overview

The database caching system provides automatic caching of expensive database queries using a two-tier caching strategy:
- **L1 Cache**: In-memory LRU cache for hot data (1000 entries, 60s TTL)
- **L2 Cache**: Redis cache for distributed caching with configurable TTL

## Requirements

Implements the following requirements:
- **Requirement 33.3**: Use database query caching for frequently accessed read-only data
- **Requirement 33.4**: Implement Redis caching for expensive queries with 5-minute TTL

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  @cache_query, @cache_queryset, CachedQueryMixin            │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Cache Manager                             │
│  (Multi-layer caching with L1 + L2)                         │
└─────────────────────────────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                ▼                       ▼
┌───────────────────────┐   ┌───────────────────────┐
│   L1: LRU Cache       │   │   L2: Redis Cache     │
│   (In-memory)         │   │   (Distributed)       │
│   1000 entries        │   │   Configurable TTL    │
│   60s default TTL     │   │   Tag-based           │
└───────────────────────┘   └───────────────────────┘
```

## Components

### 1. Cache Manager (`cache_manager.py`)

The `CacheManager` class provides the core caching functionality:
- Two-tier caching (L1: in-memory LRU, L2: Redis)
- Tag-based cache invalidation
- Automatic TTL management
- Thread-safe operations

### 2. Database Cache Utilities (`database_cache.py`)

Provides decorators and utilities for caching database queries:

#### Decorators

**`@cache_query(ttl, tags, key_prefix)`**
- Cache any function that returns database results
- Default TTL: 300 seconds (5 minutes)
- Supports tag-based invalidation

**`@cache_queryset(ttl, tags, key_prefix)`**
- Cache Django QuerySet results
- Automatically converts QuerySet to list
- Default TTL: 300 seconds (5 minutes)

**Pre-configured decorators:**
- `@cache_user_query(ttl)` - For user-related queries
- `@cache_story_query(ttl)` - For story-related queries
- `@cache_comment_query(ttl)` - For comment-related queries
- `@cache_notification_query(ttl)` - For notification-related queries

#### Utilities

**`invalidate_cache(key_prefix, *args, **kwargs)`**
- Invalidate cache for a specific query

**`invalidate_by_tags(tags)`**
- Invalidate all cache entries with specified tags

**`CachedQueryMixin`**
- Mixin for Django models to provide automatic query caching
- Provides `cached_query()` and `invalidate_cache_by_tags()` methods

## Usage Examples

### Example 1: Cache a Simple Query

```python
from infrastructure.database_cache import cache_query, invalidate_by_tags

@cache_query(ttl=300, tags=['user', 'profile'])
def get_user_profile(user_id):
    """Get user profile with caching."""
    return UserProfile.objects.select_related('user').get(user_id=user_id)

# Use the cached function
profile = get_user_profile(123)

# Invalidate cache when profile is updated
def update_user_profile(user_id, **updates):
    profile = UserProfile.objects.get(user_id=user_id)
    for key, value in updates.items():
        setattr(profile, key, value)
    profile.save()
    
    # Invalidate cache
    invalidate_by_tags(['user', 'profile'])
```

### Example 2: Cache a QuerySet

```python
from infrastructure.database_cache import cache_queryset

@cache_queryset(ttl=300, tags=['story', 'featured'])
def get_featured_stories():
    """Get featured stories with caching."""
    return Story.objects.filter(
        featured=True,
        published=True
    ).select_related('author').prefetch_related('tags')

# Use the cached function
stories = get_featured_stories()  # Returns list of Story objects
```

### Example 3: Use CachedQueryMixin

```python
from django.db import models
from infrastructure.database_cache import CachedQueryMixin

class Story(CachedQueryMixin, models.Model):
    cache_tags = ['story']
    cache_ttl = 300  # 5 minutes
    
    title = models.CharField(max_length=200)
    featured = models.BooleanField(default=False)
    published = models.BooleanField(default=False)
    view_count = models.IntegerField(default=0)
    
    @classmethod
    def get_featured(cls):
        """Get featured stories with caching."""
        return cls.cached_query(
            'featured_stories',
            lambda: cls.objects.filter(featured=True, published=True)
        )
    
    @classmethod
    def get_trending(cls, limit=10):
        """Get trending stories with caching."""
        return cls.cached_query(
            f'trending_stories_{limit}',
            lambda: cls.objects.filter(
                published=True
            ).order_by('-view_count')[:limit]
        )
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Invalidate cache on save
        self.invalidate_cache_by_tags()

# Usage
featured_stories = Story.get_featured()
trending_stories = Story.get_trending(limit=20)
```

### Example 4: Use Pre-configured Decorators

```python
from infrastructure.database_cache import cache_story_query, cache_user_query

@cache_story_query(ttl=600)  # 10 minutes
def get_trending_stories(limit=10):
    """Get trending stories with extended caching."""
    return Story.objects.filter(
        published=True
    ).order_by('-view_count')[:limit]

@cache_user_query(ttl=300)  # 5 minutes
def get_user_stats(user_id):
    """Get user statistics with caching."""
    return {
        'story_count': Story.objects.filter(author_id=user_id).count(),
        'follower_count': Follow.objects.filter(following_id=user_id).count(),
        'total_views': Story.objects.filter(author_id=user_id).aggregate(
            total=models.Sum('view_count')
        )['total'] or 0
    }
```

### Example 5: Cache Invalidation on Updates

```python
from infrastructure.database_cache import invalidate_by_tags, invalidate_cache

# Invalidate by tags (recommended for related data)
def publish_story(story_id):
    story = Story.objects.get(id=story_id)
    story.published = True
    story.save()
    
    # Invalidate all story-related caches
    invalidate_by_tags(['story', 'featured'])

# Invalidate specific cache
def update_user_profile(user_id, **updates):
    profile = UserProfile.objects.get(user_id=user_id)
    for key, value in updates.items():
        setattr(profile, key, value)
    profile.save()
    
    # Invalidate specific cache entry
    invalidate_cache('get_user_profile', user_id)
```

## Cache Key Generation

Cache keys are automatically generated from function names and arguments:

```python
# Function: get_user_profile(user_id=123)
# Cache key: db_query:get_user_profile:<hash>

# Function: get_stories(author_id=456, published=True)
# Cache key: db_query:get_stories:<hash>
```

The hash is generated from a stable representation of all arguments to ensure consistency.

## Cache Invalidation Strategies

### 1. Tag-Based Invalidation (Recommended)

Use tags to group related cache entries:

```python
# Cache with tags
@cache_query(ttl=300, tags=['user', 'profile', 'settings'])
def get_user_settings(user_id):
    return UserSettings.objects.get(user_id=user_id)

# Invalidate all user-related caches
invalidate_by_tags(['user'])

# Invalidate specific subset
invalidate_by_tags(['user', 'settings'])
```

### 2. Specific Key Invalidation

Invalidate a specific cache entry:

```python
# Invalidate specific cache
invalidate_cache('get_user_profile', user_id=123)
```

### 3. Model-Level Invalidation

Use `CachedQueryMixin` for automatic invalidation:

```python
class Story(CachedQueryMixin, models.Model):
    cache_tags = ['story']
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.invalidate_cache_by_tags()  # Invalidates all 'story' caches
```

## Best Practices

### 1. Choose Appropriate TTL

- **Hot data** (frequently accessed, rarely changes): 5-10 minutes
- **Warm data** (moderately accessed): 2-5 minutes
- **Cold data** (rarely accessed): 1-2 minutes
- **Real-time data**: Don't cache or use very short TTL (30-60 seconds)

### 2. Use Tags Effectively

Group related cache entries with tags:

```python
# Good: Specific tags for fine-grained invalidation
@cache_query(ttl=300, tags=['user', 'profile', 'public'])
def get_public_profile(user_id):
    return UserProfile.objects.get(user_id=user_id)

# Bad: Too generic
@cache_query(ttl=300, tags=['data'])
def get_public_profile(user_id):
    return UserProfile.objects.get(user_id=user_id)
```

### 3. Invalidate on Writes

Always invalidate cache when data changes:

```python
def update_story(story_id, **updates):
    story = Story.objects.get(id=story_id)
    for key, value in updates.items():
        setattr(story, key, value)
    story.save()
    
    # Invalidate related caches
    invalidate_by_tags(['story'])
```

### 4. Cache Expensive Queries Only

Don't cache simple queries that are faster than cache lookup:

```python
# Good: Cache expensive query
@cache_queryset(ttl=300, tags=['story', 'trending'])
def get_trending_stories():
    return Story.objects.filter(
        published=True
    ).select_related('author').prefetch_related(
        'tags', 'comments'
    ).annotate(
        score=F('view_count') + F('like_count') * 2
    ).order_by('-score')[:50]

# Bad: Don't cache simple query
@cache_query(ttl=300, tags=['user'])
def get_user_by_id(user_id):
    return User.objects.get(id=user_id)  # Too simple, not worth caching
```

### 5. Monitor Cache Performance

Use cache statistics to monitor performance:

```python
from infrastructure.cache_manager import cache_manager

# Get cache statistics
stats = cache_manager.get_stats()
print(f"Hit rate: {stats.hit_rate:.2%}")
print(f"Hits: {stats.hits}, Misses: {stats.misses}")
print(f"Size: {stats.size}/{stats.max_size}")
```

## Configuration

### Environment Variables

```bash
# Redis Configuration
VALKEY_URL=redis://localhost:6379/0

# L1 Cache Configuration
L1_CACHE_MAX_SIZE=1000
L1_CACHE_DEFAULT_TTL=60

# Cache TTL Configuration (optional)
CACHE_TTL_USER_PROFILE=300
CACHE_TTL_STORY_LISTING=300
CACHE_TTL_SEARCH_RESULTS=300
```

### Django Settings

```python
# settings.py

# Cache TTL configuration
CACHE_TTL = {
    'default': 300,  # 5 minutes
    'user_profile': 300,
    'story_listing': 300,
    'search_results': 300,
    'trending': 600,  # 10 minutes
}

# L1 Cache configuration
L1_CACHE_MAX_SIZE = 1000
L1_CACHE_DEFAULT_TTL = 60

# Redis configuration
VALKEY_URL = os.getenv('VALKEY_URL', 'redis://localhost:6379/0')
```

## Performance Considerations

### Cache Hit Rate

Target cache hit rate: **> 80%**

Monitor and optimize:
- Increase TTL for stable data
- Add more cache entries for frequently accessed data
- Use appropriate cache keys to avoid collisions

### Memory Usage

L1 cache is limited to 1000 entries by default. Adjust based on available memory:

```python
# For servers with more memory
L1_CACHE_MAX_SIZE = 5000

# For memory-constrained environments
L1_CACHE_MAX_SIZE = 500
```

### Cache Stampede Prevention

The cache manager handles cache stampede by:
1. Single query execution on cache miss
2. Immediate cache population
3. TTL jitter (optional, can be added)

## Monitoring and Debugging

### Enable Debug Logging

```python
import logging

logging.getLogger('infrastructure.database_cache').setLevel(logging.DEBUG)
logging.getLogger('infrastructure.cache_manager').setLevel(logging.DEBUG)
```

### Cache Statistics

```python
from infrastructure.cache_manager import cache_manager

# Get statistics
stats = cache_manager.get_stats()
print(f"Cache Statistics:")
print(f"  Hit Rate: {stats.hit_rate:.2%}")
print(f"  Hits: {stats.hits}")
print(f"  Misses: {stats.misses}")
print(f"  Evictions: {stats.evictions}")
print(f"  Size: {stats.size}/{stats.max_size}")
```

## Testing

### Unit Tests

```python
from infrastructure.database_cache import cache_query, invalidate_by_tags

def test_cache_query():
    call_count = 0
    
    @cache_query(ttl=60, tags=['test'])
    def expensive_query():
        nonlocal call_count
        call_count += 1
        return {'result': 'data'}
    
    # First call - cache miss
    result1 = expensive_query()
    assert call_count == 1
    
    # Second call - cache hit
    result2 = expensive_query()
    assert call_count == 1  # Not called again
    assert result1 == result2
    
    # Invalidate and call again
    invalidate_by_tags(['test'])
    result3 = expensive_query()
    assert call_count == 2  # Called again after invalidation
```

## Related Documentation

- [Cache Manager](./cache_manager.py) - Core caching implementation
- [Database Configuration](./README_DATABASE_CONFIG.md) - Database setup and connection pooling
- [Database Indexes](./README_DATABASE_INDEXES.md) - Index optimization

## Support

For issues or questions:
1. Check cache statistics for performance issues
2. Enable debug logging to trace cache operations
3. Review cache hit rate and adjust TTL if needed
4. Ensure proper cache invalidation on data updates
