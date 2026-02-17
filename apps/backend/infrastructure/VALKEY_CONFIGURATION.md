# Valkey/Redis Configuration Guide

This document describes the Valkey (Redis) configuration for caching and rate limiting in the MueJam Library application.

## Overview

The application uses Valkey/Redis for:
1. **Multi-layer caching** - L1 (in-memory LRU) and L2 (Redis) caching strategy
2. **Distributed rate limiting** - Per-user and global rate limits using sliding window algorithm
3. **Celery task queue** - Background job processing

## Connection Configuration

### Basic Connection

The primary Valkey connection is configured via the `VALKEY_URL` environment variable:

```bash
VALKEY_URL=redis://valkey:6379/0
```

For production deployments with authentication:

```bash
VALKEY_URL=redis://:password@valkey:6379/0
```

For Redis Cluster:

```bash
VALKEY_URL=redis://node1:6379,node2:6379,node3:6379/0
```

### Connection Pool Settings

The Django cache backend is configured with connection pooling:

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': VALKEY_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
        },
        'KEY_PREFIX': 'muejam',
        'VERSION': 1,
    }
}
```

**Configuration Parameters:**
- `max_connections`: Maximum connections in the pool (default: 50)
- `retry_on_timeout`: Automatically retry on timeout (default: True)
- `SOCKET_CONNECT_TIMEOUT`: Connection timeout in seconds (default: 5)
- `SOCKET_TIMEOUT`: Socket operation timeout in seconds (default: 5)
- `KEY_PREFIX`: Prefix for all cache keys to avoid collisions (default: 'muejam')

## Cache TTL Configuration

Different types of data have different TTL (Time To Live) values optimized for their access patterns:

### User-Related Data

```bash
CACHE_TTL_USER_PROFILE=300        # 5 minutes
CACHE_TTL_USER_PREFERENCES=600    # 10 minutes
CACHE_TTL_USER_LIBRARY=180        # 3 minutes
```

**Rationale:**
- User profiles change infrequently but should reflect updates reasonably quickly
- Preferences are rarely modified, can be cached longer
- Library contents change frequently as users add/remove stories

### Story-Related Data

```bash
CACHE_TTL_STORY_METADATA=600      # 10 minutes
CACHE_TTL_STORY_CHAPTERS=900      # 15 minutes
CACHE_TTL_STORY_CONTENT=1800      # 30 minutes
```

**Rationale:**
- Story metadata (title, author, description) changes infrequently
- Chapter lists are relatively stable
- Story content is immutable once published, can be cached longest

### Discovery and Feeds

```bash
CACHE_TTL_TRENDING=300            # 5 minutes
CACHE_TTL_NEW_STORIES=180         # 3 minutes
CACHE_TTL_RECOMMENDATIONS=600     # 10 minutes
```

**Rationale:**
- Trending stories need frequent updates to reflect current popularity
- New stories feed should update quickly to show latest content
- Recommendations can be cached longer as they're personalized and expensive to compute

### Social Data

```bash
CACHE_TTL_WHISPERS_FEED=60        # 1 minute
CACHE_TTL_NOTIFICATIONS=30        # 30 seconds
CACHE_TTL_FOLLOWER_COUNTS=300     # 5 minutes
```

**Rationale:**
- Whispers (micro-posts) are time-sensitive, need short TTL
- Notifications should appear quickly, shortest TTL
- Follower counts change slowly, can be cached longer

### Search Results

```bash
CACHE_TTL_SEARCH_RESULTS=300      # 5 minutes
CACHE_TTL_AUTOCOMPLETE=600        # 10 minutes
```

**Rationale:**
- Search results can be cached to reduce database load
- Autocomplete suggestions are relatively stable

### Static Data

```bash
CACHE_TTL_GENRES=3600             # 1 hour
CACHE_TTL_TAGS=3600               # 1 hour
```

**Rationale:**
- Genres and tags are rarely modified, can be cached longest

### Default TTL

```bash
CACHE_TTL_DEFAULT=300             # 5 minutes
```

Used for any cache type not explicitly configured.

## L1 Cache Configuration

The L1 cache is an in-memory LRU (Least Recently Used) cache that sits in front of Redis:

```bash
L1_CACHE_MAX_SIZE=1000            # Maximum entries in L1 cache
L1_CACHE_DEFAULT_TTL=60           # Default TTL for L1 entries (seconds)
```

**Benefits:**
- Ultra-fast access for hot data (no network round-trip)
- Reduces load on Redis
- Automatic eviction of least recently used items

**Trade-offs:**
- Memory usage per application instance
- Cache invalidation must clear both L1 and L2

## Rate Limiting Configuration

### Enable/Disable Rate Limiting

```bash
RATE_LIMIT_ENABLED=True           # Enable rate limiting
```

Set to `False` to disable rate limiting entirely (useful for development).

### Rate Limit Thresholds

```bash
RATE_LIMIT_PER_USER=100           # Queries per minute per user
RATE_LIMIT_GLOBAL=10000           # Queries per minute globally
RATE_LIMIT_WINDOW=60              # Window size in seconds
```

**Per-User Limits:**
- Protects against individual users overwhelming the system
- Default: 100 queries/minute per user
- Adjust based on expected user behavior

**Global Limits:**
- Protects against total system overload
- Default: 10,000 queries/minute across all users
- Adjust based on database capacity

**Window Size:**
- Time window for rate limit calculation
- Default: 60 seconds (1 minute)
- Uses sliding window algorithm for accuracy

### Admin Bypass

```bash
RATE_LIMIT_ADMIN_BYPASS=True      # Allow admins to bypass rate limits
```

When enabled, users with admin privileges bypass all rate limits.

### Rate Limit Redis Connection

```bash
RATE_LIMIT_REDIS_URL=redis://valkey:6379/0
```

Can use a separate Redis instance for rate limiting if desired. Defaults to `VALKEY_URL` if not specified.

## Usage in Application Code

### Using Cache Manager

```python
from infrastructure.cache_manager import CacheManager
from django.conf import settings

# Initialize cache manager (uses settings automatically)
cache_manager = CacheManager()

# Get TTL for specific cache type
ttl = cache_manager.get_ttl_for_type('user_profile')

# Cache a user profile
cache_manager.set(
    key=f'user:profile:{user_id}',
    value=user_data,
    ttl=ttl,
    tags=['user', f'user:{user_id}']
)

# Retrieve from cache
user_data = cache_manager.get(f'user:profile:{user_id}')

# Invalidate by tags (e.g., when user updates profile)
cache_manager.invalidate_by_tags([f'user:{user_id}'])
```

### Using Rate Limiter

```python
from infrastructure.rate_limiter import RateLimiter

# Initialize rate limiter (uses settings automatically)
rate_limiter = RateLimiter()

# Check if request is allowed
if rate_limiter.allow_request(user_id=user.id, is_admin=user.is_staff):
    # Process request
    pass
else:
    # Return 429 Too Many Requests
    return Response(
        {'error': 'Rate limit exceeded'},
        status=429
    )

# Get detailed limit info
limit_info = rate_limiter.get_limit_info(user_id=user.id)
```

## Monitoring and Metrics

### Cache Statistics

```python
# Get cache statistics
stats = cache_manager.get_stats()
print(f"Hit rate: {stats.hit_rate:.2%}")
print(f"Cache size: {stats.size}/{stats.max_size}")
print(f"Evictions: {stats.evictions}")
```

### Rate Limit Information

```python
# Get rate limit status for a user
limit_info = rate_limiter.get_limit_info(user_id)
print(f"Requests made: {limit_info.requests_made}/{limit_info.limit}")
print(f"Window: {limit_info.window_start} to {limit_info.window_end}")
```

## Production Deployment

### High Availability Setup

For production, use Redis Cluster or Redis Sentinel for high availability:

**Redis Cluster:**
```bash
VALKEY_URL=redis://node1:6379,node2:6379,node3:6379/0
```

**Redis Sentinel:**
```bash
VALKEY_URL=redis://sentinel1:26379,sentinel2:26379/mymaster
```

### Security Considerations

1. **Authentication:** Always use password authentication in production
   ```bash
   VALKEY_URL=redis://:strong_password@valkey:6379/0
   ```

2. **TLS/SSL:** Use encrypted connections for sensitive data
   ```bash
   VALKEY_URL=rediss://:password@valkey:6379/0
   ```

3. **Network Isolation:** Run Redis in a private network, not exposed to internet

4. **Firewall Rules:** Restrict Redis port (6379) to application servers only

### Performance Tuning

1. **Connection Pool Size:** Adjust based on concurrent requests
   - Low traffic: 10-20 connections
   - Medium traffic: 20-50 connections
   - High traffic: 50-100 connections

2. **TTL Values:** Monitor cache hit rates and adjust TTLs
   - High hit rate + frequent invalidations → increase TTL
   - Low hit rate → decrease TTL or remove caching

3. **L1 Cache Size:** Balance memory usage vs. hit rate
   - Monitor L1 eviction rate
   - Increase size if evictions are frequent and memory available

4. **Rate Limits:** Adjust based on actual usage patterns
   - Monitor rate limit rejections
   - Increase limits if legitimate users are being blocked
   - Decrease limits if system is overloaded

## Troubleshooting

### Redis Connection Failures

If Redis is unavailable:
- **Cache Manager:** Falls back to database queries (fail-open)
- **Rate Limiter:** Disables rate limiting (fail-open)

Check logs for warnings:
```
Warning: Redis connection failed: [error]. Operating without L2 cache.
Warning: Redis connection failed: [error]. Rate limiting disabled.
```

### High Memory Usage

If Redis memory usage is high:
1. Check TTL values - ensure keys are expiring
2. Monitor key count: `redis-cli DBSIZE`
3. Check for keys without TTL: `redis-cli KEYS *` (use carefully in production)
4. Consider increasing Redis memory limit or adding more nodes

### Cache Invalidation Issues

If users see stale data:
1. Verify cache invalidation is called on data updates
2. Check tag-based invalidation is working correctly
3. Reduce TTL values for affected cache types
4. Clear cache manually if needed: `cache_manager.l2_cache.flushdb()`

### Rate Limit Issues

If legitimate users are being rate limited:
1. Check rate limit thresholds in settings
2. Monitor actual request rates per user
3. Consider implementing tiered rate limits (free vs. premium users)
4. Verify admin bypass is working for admin users

## Requirements Validation

This configuration satisfies the following requirements:

- **Requirement 5.1:** Query results cached in Redis with configurable TTL values ✓
- **Requirement 7.1:** Per-user rate limiting at application level ✓
- **Requirement 7.2:** Global rate limiting at database connection level ✓

The configuration provides:
- Multi-layer caching with L1 (in-memory) and L2 (Redis)
- Configurable TTL values per application data type
- Distributed rate limiting using Redis
- Sliding window algorithm for accurate rate limiting
- Admin bypass capability
- Fail-open behavior for high availability
- Comprehensive monitoring and statistics
