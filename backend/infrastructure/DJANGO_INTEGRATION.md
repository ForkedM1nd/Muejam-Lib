# Django Integration Guide

This document explains how to integrate the database and caching infrastructure components with Django.

## Overview

The infrastructure provides four middleware components:

1. **DatabaseInfrastructureMiddleware** - Connection pooling and workload isolation
2. **CacheMiddleware** - Multi-layer caching (L1: in-memory, L2: Redis)
3. **RateLimitMiddleware** - Request rate limiting
4. **QueryOptimizerMiddleware** - Query analysis and optimization

## Installation

### 1. Add Middleware to Django Settings

Add the middleware to your `MIDDLEWARE` list in `settings.py`:

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    
    # Add infrastructure middleware
    'infrastructure.middleware.DatabaseInfrastructureMiddleware',
    'infrastructure.middleware.CacheMiddleware',
    'infrastructure.middleware.RateLimitMiddleware',
    'infrastructure.middleware.QueryOptimizerMiddleware',
    
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # ... rest of middleware
]
```

**Order matters:**
- `DatabaseInfrastructureMiddleware` should be early to initialize connection pools
- `RateLimitMiddleware` should be early to reject rate-limited requests quickly
- `CacheMiddleware` can be anywhere but before view processing
- `QueryOptimizerMiddleware` should be early to track all queries

### 2. Configure Database Settings

Add database replica configuration to `settings.py`:

```python
# Primary database (existing configuration)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'mydb',
        'USER': 'myuser',
        'PASSWORD': 'mypassword',
        'HOST': 'primary.db.example.com',
        'PORT': '5432',
    }
}

# Read replicas configuration
DATABASE_REPLICAS = [
    {
        'HOST': 'replica1.db.example.com',
        'PORT': '5432',
        'WEIGHT': 1.0,  # Load balancing weight
    },
    {
        'HOST': 'replica2.db.example.com',
        'PORT': '5432',
        'WEIGHT': 1.0,
    },
    {
        'HOST': 'replica3.db.example.com',
        'PORT': '5432',
        'WEIGHT': 1.0,
    },
]

# Connection pool settings
DB_POOL_MIN_CONNECTIONS = 10  # Minimum connections per pool
DB_POOL_MAX_CONNECTIONS = 50  # Maximum connections per pool
DB_POOL_IDLE_TIMEOUT = 300    # Idle timeout in seconds

# Workload isolation settings
MAX_REPLICA_LAG = 5.0  # Maximum acceptable replica lag in seconds
```

### 3. Configure Cache Settings

Ensure Redis/Valkey is configured in `settings.py`:

```python
# Cache configuration (existing)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://localhost:6379/0',
    }
}

# Multi-layer cache settings
CACHE_L1_MAX_SIZE = 1000      # L1 (in-memory) cache max entries
CACHE_L1_DEFAULT_TTL = 60     # L1 default TTL in seconds
CACHE_L2_DEFAULT_TTL = 300    # L2 (Redis) default TTL in seconds

# Cache warming (optional)
CACHE_WARM_QUERIES = [
    # Add queries to pre-populate cache on startup
    # CacheWarmQuery(key="popular_stories", query="...", ttl=300)
]
```

### 4. Configure Query Optimizer Settings

Add query optimizer configuration to `settings.py`:

```python
# Query optimizer settings
SLOW_QUERY_THRESHOLD_MS = 100.0        # Threshold for slow query detection
ENABLE_QUERY_EXPLAIN_ANALYZE = True    # Enable EXPLAIN ANALYZE
QUERY_OPTIMIZER_MAX_HISTORY = 1000     # Max queries to keep in history
```

### 5. Configure Rate Limiting (Optional)

Rate limiting is configured with default values but can be customized:

```python
# Rate limiting is handled by RateLimiter class
# Default values:
# - Per-user limit: 100 queries/minute
# - Global limit: 10,000 queries/minute
# - Window size: 60 seconds

# To customize, modify infrastructure/rate_limiter.py constants
```

## Usage

### Accessing Infrastructure Components in Views

The middleware attaches infrastructure components to the request object:

```python
from django.http import JsonResponse
from infrastructure.models import Priority, Query

def my_view(request):
    # Access connection pool
    pool_manager = request.db_pool
    stats = pool_manager.get_pool_stats()
    
    # Access workload isolator
    workload_isolator = request.workload_isolator
    query = Query(text="SELECT * FROM users WHERE id = ?", params={"id": 1})
    target = workload_isolator.route_query(query, priority=Priority.NORMAL)
    
    # Access cache manager
    cache_manager = request.cache_manager
    
    # Get from cache
    value = cache_manager.get("my_key")
    if value is None:
        # Cache miss, fetch from database
        value = fetch_from_database()
        # Store in cache
        cache_manager.set("my_key", value, ttl=300, tags=["users"])
    
    # Access query optimizer
    query_optimizer = request.query_optimizer
    metrics = query_optimizer.get_metrics()
    
    # Access rate limiter
    rate_limiter = request.rate_limiter
    limit_info = rate_limiter.get_limit_info(str(request.user.id))
    
    return JsonResponse({
        "data": value,
        "pool_stats": {
            "read": stats["read"].__dict__,
            "write": stats["write"].__dict__,
        },
        "cache_stats": cache_manager.get_stats().__dict__,
        "query_metrics": metrics,
        "rate_limit": limit_info.__dict__,
    })
```

### Using Cache Manager

```python
from infrastructure.middleware import CacheMiddleware

# Get cache manager instance
cache_manager = CacheMiddleware.get_cache_manager()

# Basic operations
cache_manager.set("key", "value", ttl=300)
value = cache_manager.get("key")
cache_manager.invalidate("key")

# Tag-based invalidation
cache_manager.set("user:1", user_data, ttl=300, tags=["users", "user:1"])
cache_manager.set("user:2", user_data, ttl=300, tags=["users", "user:2"])
cache_manager.invalidate_by_tags(["users"])  # Invalidates both entries

# Pattern-based invalidation
cache_manager.invalidate_by_pattern("user:*")  # Invalidates all user keys

# Get statistics
stats = cache_manager.get_stats()
print(f"L1 hit rate: {stats.l1_hit_rate}%")
print(f"L2 hit rate: {stats.l2_hit_rate}%")
print(f"Overall hit rate: {stats.overall_hit_rate}%")
```

### Using Query Optimizer

```python
from infrastructure.middleware import QueryOptimizerMiddleware

# Get query optimizer instance
query_optimizer = QueryOptimizerMiddleware.get_query_optimizer()

# Track a query
query_optimizer.track_query(
    query="SELECT * FROM users WHERE email = ?",
    execution_time=150.0,  # milliseconds
    params={"email": "user@example.com"},
    request_id="req_123",
    user_id="user_456"
)

# Analyze a query
analysis = query_optimizer.analyze_query(
    query="SELECT * FROM users WHERE email = ?",
    params={"email": "user@example.com"}
)
print(f"Has index: {analysis.has_index}")
print(f"Suggestions: {analysis.optimization_suggestions}")

# Detect N+1 patterns
patterns = query_optimizer.detect_n_plus_one(request_id="req_123")
for pattern in patterns:
    print(f"N+1 detected: {pattern.count} queries")
    print(f"Recommendation: {pattern.recommendation}")

# Get index suggestions
suggestions = query_optimizer.suggest_indexes()
for suggestion in suggestions:
    print(f"Suggest index on {suggestion.table_name}.{suggestion.columns}")
    print(f"Reason: {suggestion.reason}")
    print(f"Estimated improvement: {suggestion.estimated_improvement}%")

# Get metrics
metrics = query_optimizer.get_metrics()
print(f"Total queries: {metrics['total_queries']}")
print(f"Slow queries: {metrics['total_slow_queries']}")
print(f"Slow query rate: {metrics['slow_query_rate']}%")
```

### Using Workload Isolator

```python
from infrastructure.middleware import DatabaseInfrastructureMiddleware
from infrastructure.models import Query, Priority, QueryType

# Get workload isolator instance
workload_isolator = DatabaseInfrastructureMiddleware.get_workload_isolator()

# Route a read query
read_query = Query(
    text="SELECT * FROM users WHERE id = ?",
    params={"id": 1},
    query_type=QueryType.SELECT,
    priority=Priority.NORMAL
)
target = workload_isolator.route_query(read_query)
print(f"Route to: {target.target_type} at {target.host}:{target.port}")
print(f"Reason: {target.reason}")

# Route a write query
write_query = Query(
    text="UPDATE users SET name = ? WHERE id = ?",
    params={"name": "John", "id": 1},
    query_type=QueryType.UPDATE,
    priority=Priority.NORMAL
)
target = workload_isolator.route_query(write_query)
# Always routes to primary

# Route a critical query
critical_query = Query(
    text="SELECT * FROM users WHERE id = ?",
    params={"id": 1},
    query_type=QueryType.SELECT,
    priority=Priority.CRITICAL
)
target = workload_isolator.route_query(critical_query)
# Routes to primary for consistency

# Check replica status
replicas = workload_isolator.get_replica_status()
for replica in replicas:
    print(f"Replica: {replica['host']}:{replica['port']}")
    print(f"  Healthy: {replica['is_healthy']}")
    print(f"  Lag: {replica['replication_lag']}s")
    print(f"  CPU: {replica['cpu_utilization']}%")
```

## Monitoring

### Debug Headers

When `DEBUG = True`, the middleware adds diagnostic headers to responses:

```
X-DB-Pool-Read-Utilization: 45.2%
X-DB-Pool-Write-Utilization: 23.1%
X-Cache-L1-Hit-Rate: 78.5%
X-Cache-L2-Hit-Rate: 92.3%
X-Cache-Overall-Hit-Rate: 85.4%
X-Query-Count: 12
X-Query-N-Plus-One: 1
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 2024-01-15T10:30:00Z
```

### Logging

The infrastructure components log to the following loggers:

- `infrastructure.connection_pool` - Connection pool events
- `infrastructure.workload_isolator` - Query routing decisions
- `infrastructure.cache_manager` - Cache operations
- `infrastructure.rate_limiter` - Rate limiting events
- `infrastructure.query_optimizer` - Query analysis and optimization
- `infrastructure.middleware` - Middleware lifecycle events

Configure logging in `settings.py`:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'infrastructure.log',
        },
    },
    'loggers': {
        'infrastructure': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'infrastructure.query_optimizer': {
            'handlers': ['console', 'file'],
            'level': 'WARNING',  # Only log slow queries and N+1 patterns
        },
    },
}
```

## Integration with Prisma

To integrate the QueryOptimizer with Prisma query hooks:

```python
from prisma import Prisma
from infrastructure.middleware import QueryOptimizerMiddleware

# Get query optimizer
query_optimizer = QueryOptimizerMiddleware.get_query_optimizer()

# Set up Prisma client with query logging
prisma = Prisma()

# Hook into Prisma query execution
@prisma.on_query
async def log_query(query_info):
    query_optimizer.track_query(
        query=query_info.query,
        execution_time=query_info.duration,
        params=query_info.params,
        request_id=query_info.request_id,
    )
```

## Performance Considerations

### Connection Pool Sizing

- **Min connections**: Set to handle baseline load (default: 10)
- **Max connections**: Set based on database capacity and application instances
  - Formula: `max_connections = (database_max_connections / num_app_instances) * 0.8`
  - Example: 200 DB connections / 4 instances * 0.8 = 40 per instance

### Cache TTL Tuning

- **L1 (in-memory)**: Short TTL (60s) for hot data, small size (1000 entries)
- **L2 (Redis)**: Longer TTL (300s+) for distributed caching
- **Critical data**: Use write-through caching with short TTL

### Rate Limiting

- **Per-user limits**: Adjust based on expected user behavior
- **Global limits**: Set based on database capacity
- **Admin bypass**: Use for administrative operations and monitoring

### Query Optimization

- **Slow query threshold**: Start at 100ms, adjust based on application needs
- **EXPLAIN ANALYZE**: Disable in production if overhead is too high
- **N+1 detection**: Monitor logs for patterns, fix with eager loading

## Troubleshooting

### Connection Pool Exhaustion

**Symptom**: `TimeoutError: Connection pool exhausted`

**Solutions**:
1. Increase `DB_POOL_MAX_CONNECTIONS`
2. Check for connection leaks (connections not being released)
3. Reduce connection idle timeout
4. Scale horizontally (add more application instances)

### High Cache Miss Rate

**Symptom**: Low cache hit rate in headers/logs

**Solutions**:
1. Increase L1 cache size
2. Increase TTL values
3. Implement cache warming for predictable queries
4. Check cache invalidation logic (too aggressive?)

### Rate Limiting False Positives

**Symptom**: Legitimate users getting 429 errors

**Solutions**:
1. Increase per-user rate limits
2. Adjust time window
3. Implement user-specific limits based on subscription tier
4. Add rate limit exemptions for specific endpoints

### Slow Query Alerts

**Symptom**: Many slow query warnings in logs

**Solutions**:
1. Review index suggestions from query optimizer
2. Add recommended indexes to database
3. Optimize queries based on suggestions
4. Consider query result caching
5. Implement pagination for large result sets

## Testing

### Unit Tests

Test infrastructure components in isolation:

```python
from infrastructure.middleware import CacheMiddleware
from django.test import TestCase, RequestFactory

class CacheMiddlewareTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = CacheMiddleware(lambda r: None)
    
    def test_cache_operations(self):
        cache_manager = CacheMiddleware.get_cache_manager()
        
        # Test set/get
        cache_manager.set("test_key", "test_value", ttl=60)
        value = cache_manager.get("test_key")
        self.assertEqual(value, "test_value")
        
        # Test invalidation
        cache_manager.invalidate("test_key")
        value = cache_manager.get("test_key")
        self.assertIsNone(value)
```

### Integration Tests

Test middleware integration with Django:

```python
from django.test import TestCase, Client

class MiddlewareIntegrationTest(TestCase):
    def setUp(self):
        self.client = Client()
    
    def test_rate_limiting(self):
        # Make requests up to limit
        for i in range(100):
            response = self.client.get('/api/endpoint/')
            self.assertEqual(response.status_code, 200)
        
        # Next request should be rate limited
        response = self.client.get('/api/endpoint/')
        self.assertEqual(response.status_code, 429)
        self.assertIn('Retry-After', response)
```

## Migration Guide

### From Existing Django Application

1. **Backup your database** before making changes
2. **Install middleware** in settings.py
3. **Configure replicas** if using read replicas
4. **Test in staging** environment first
5. **Monitor metrics** after deployment
6. **Gradually enable features**:
   - Start with connection pooling
   - Add caching
   - Enable rate limiting
   - Enable query optimization

### Rollback Plan

If issues occur, disable middleware by commenting out in `settings.py`:

```python
MIDDLEWARE = [
    # 'infrastructure.middleware.DatabaseInfrastructureMiddleware',
    # 'infrastructure.middleware.CacheMiddleware',
    # 'infrastructure.middleware.RateLimitMiddleware',
    # 'infrastructure.middleware.QueryOptimizerMiddleware',
]
```

No database changes are required, so rollback is safe and immediate.

## Support

For issues or questions:
1. Check logs for error messages
2. Review this documentation
3. Check infrastructure component documentation
4. File an issue with logs and configuration details
