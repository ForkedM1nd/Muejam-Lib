# Rate Limiting Configuration Guide

This guide provides comprehensive instructions for configuring and tuning rate limiting to protect your database and application from overload.

## Table of Contents

1. [Overview](#overview)
2. [Rate Limiting Strategies](#rate-limiting-strategies)
3. [Configuration](#configuration)
4. [Tuning Guidelines](#tuning-guidelines)
5. [Implementation Patterns](#implementation-patterns)
6. [Monitoring](#monitoring)
7. [Troubleshooting](#troubleshooting)

## Overview

Rate limiting protects your infrastructure by:

- Preventing database overload
- Mitigating abuse and DoS attacks
- Ensuring fair resource allocation
- Maintaining service quality for all users

## Rate Limiting Strategies

### Per-User Rate Limiting

Limits requests per individual user.

**Use Cases**:
- Prevent single user from monopolizing resources
- Enforce API usage quotas
- Protect against compromised accounts

**Configuration**:
```python
RATE_LIMITING = {
    'per_user': {
        'queries_per_minute': 100,
        'window_seconds': 60,
    },
}
```

### Global Rate Limiting

Limits total requests across all users.

**Use Cases**:
- Protect database from total overload
- Maintain system stability
- Prevent cascading failures

**Configuration**:
```python
RATE_LIMITING = {
    'global': {
        'queries_per_minute': 10000,
        'window_seconds': 60,
    },
}
```

### Endpoint-Specific Rate Limiting

Different limits for different endpoints.

**Use Cases**:
- Expensive operations (search, reports)
- Public vs authenticated endpoints
- Read vs write operations

**Configuration**:
```python
RATE_LIMITING_ENDPOINTS = {
    '/v1/search/': {
        'queries_per_minute': 20,
    },
    '/v1/stories/': {
        'queries_per_minute': 100,
    },
    '/v1/users/profile/': {
        'queries_per_minute': 50,
    },
}
```

### Tiered Rate Limiting

Different limits based on user tier.

**Use Cases**:
- Free vs paid users
- Different subscription levels
- Internal vs external users

**Configuration**:
```python
RATE_LIMITING_TIERS = {
    'free': {
        'queries_per_minute': 50,
    },
    'basic': {
        'queries_per_minute': 200,
    },
    'premium': {
        'queries_per_minute': 1000,
    },
    'enterprise': {
        'queries_per_minute': 10000,
    },
}
```

## Configuration

### Basic Configuration

```python
# config/settings.py

RATE_LIMITING = {
    # Enable/disable rate limiting
    'enabled': True,
    
    # Backend (redis, memory)
    'backend': 'redis',
    'redis_url': f"redis://:{os.getenv('REDIS_PASSWORD')}@{os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT')}/1",
    
    # Per-user limits
    'per_user': {
        'queries_per_minute': 100,
        'window_seconds': 60,
    },
    
    # Global limits
    'global': {
        'queries_per_minute': 10000,
        'window_seconds': 60,
    },
    
    # Algorithm (fixed_window, sliding_window, token_bucket)
    'algorithm': 'sliding_window',
    
    # Admin bypass
    'admin_bypass': True,
    
    # Whitelist IPs
    'whitelist_ips': [
        '10.0.0.0/8',  # Internal network
        '192.168.0.0/16',  # Private network
    ],
    
    # Response headers
    'include_headers': True,
    'header_limit': 'X-RateLimit-Limit',
    'header_remaining': 'X-RateLimit-Remaining',
    'header_reset': 'X-RateLimit-Reset',
}
```

### Environment Variables

```bash
# .env

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_USER=100
RATE_LIMIT_GLOBAL=10000
RATE_LIMIT_WINDOW=60
RATE_LIMIT_ALGORITHM=sliding_window

# Redis for rate limiting
REDIS_HOST=redis.example.com
REDIS_PORT=6379
REDIS_PASSWORD=strong_password
```

### Middleware Setup

```python
# config/settings.py

MIDDLEWARE = [
    # ... other middleware ...
    'infrastructure.middleware.RateLimitMiddleware',
]
```

## Tuning Guidelines

### Determining Appropriate Limits

#### Step 1: Analyze Current Traffic

```bash
# Check request rate
tail -f /var/log/nginx/access.log | pv -l -i 1 -r > /dev/null

# Analyze by endpoint
awk '{print $7}' /var/log/nginx/access.log | sort | uniq -c | sort -rn | head -20
```

#### Step 2: Calculate Baseline

```python
# Calculate requests per minute
total_requests = 100000  # From logs
time_period_minutes = 60
requests_per_minute = total_requests / time_period_minutes  # 1667

# Add 20% buffer
recommended_limit = int(requests_per_minute * 1.2)  # 2000
```

#### Step 3: Set Conservative Initial Limits

```python
RATE_LIMITING = {
    'per_user': {
        'queries_per_minute': 100,  # Start conservative
    },
    'global': {
        'queries_per_minute': 5000,  # 50% of calculated capacity
    },
}
```

#### Step 4: Monitor and Adjust

Monitor rate limit hits and adjust accordingly.

### Per-User Limits

**Low Traffic Application**:
```python
RATE_LIMITING = {
    'per_user': {
        'queries_per_minute': 50,
    },
}
```

**Medium Traffic Application**:
```python
RATE_LIMITING = {
    'per_user': {
        'queries_per_minute': 100,
    },
}
```

**High Traffic Application**:
```python
RATE_LIMITING = {
    'per_user': {
        'queries_per_minute': 200,
    },
}
```

### Global Limits

**Small Database (< 100 connections)**:
```python
RATE_LIMITING = {
    'global': {
        'queries_per_minute': 5000,
    },
}
```

**Medium Database (100-500 connections)**:
```python
RATE_LIMITING = {
    'global': {
        'queries_per_minute': 10000,
    },
}
```

**Large Database (> 500 connections)**:
```python
RATE_LIMITING = {
    'global': {
        'queries_per_minute': 50000,
    },
}
```

### Time Windows

**Short Window (Real-time Protection)**:
```python
RATE_LIMITING = {
    'per_user': {
        'queries_per_minute': 100,
        'window_seconds': 10,  # 10-second window
    },
}
```

**Medium Window (Balanced)**:
```python
RATE_LIMITING = {
    'per_user': {
        'queries_per_minute': 100,
        'window_seconds': 60,  # 1-minute window
    },
}
```

**Long Window (Hourly Quotas)**:
```python
RATE_LIMITING = {
    'per_user': {
        'queries_per_hour': 5000,
        'window_seconds': 3600,  # 1-hour window
    },
}
```

## Implementation Patterns

### Pattern 1: Tiered Limits by User Type

```python
# infrastructure/rate_limiter.py

def get_user_rate_limit(user):
    """Get rate limit based on user tier."""
    if user.is_superuser:
        return None  # No limit for admins
    
    tier_limits = {
        'free': 50,
        'basic': 200,
        'premium': 1000,
        'enterprise': 10000,
    }
    
    return tier_limits.get(user.subscription_tier, 50)

# Usage in middleware
class RateLimitMiddleware:
    def __call__(self, request):
        if request.user.is_authenticated:
            limit = get_user_rate_limit(request.user)
            if limit and not self.check_rate_limit(request.user.id, limit):
                return HttpResponse('Rate limit exceeded', status=429)
        return self.get_response(request)
```

### Pattern 2: Endpoint-Specific Limits

```python
# infrastructure/rate_limiter.py

ENDPOINT_LIMITS = {
    '/v1/search/': 20,
    '/v1/reports/': 10,
    '/v1/stories/': 100,
    '/v1/users/': 50,
}

def get_endpoint_limit(path):
    """Get rate limit for specific endpoint."""
    for endpoint, limit in ENDPOINT_LIMITS.items():
        if path.startswith(endpoint):
            return limit
    return 100  # Default limit

# Usage in middleware
class RateLimitMiddleware:
    def __call__(self, request):
        limit = get_endpoint_limit(request.path)
        key = f"{request.user.id}:{request.path}"
        if not self.check_rate_limit(key, limit):
            return HttpResponse('Rate limit exceeded', status=429)
        return self.get_response(request)
```

### Pattern 3: Burst Allowance

```python
# infrastructure/rate_limiter.py

RATE_LIMITING = {
    'per_user': {
        'sustained_rate': 100,  # Sustained rate
        'burst_rate': 200,  # Allow bursts
        'burst_duration': 10,  # For 10 seconds
    },
}

def check_rate_limit_with_burst(user_id, timestamp):
    """Check rate limit with burst allowance."""
    # Check burst rate (10-second window)
    burst_key = f"rate_limit:burst:{user_id}"
    burst_count = redis_client.incr(burst_key)
    redis_client.expire(burst_key, 10)
    
    if burst_count > 200:
        return False
    
    # Check sustained rate (60-second window)
    sustained_key = f"rate_limit:sustained:{user_id}"
    sustained_count = redis_client.incr(sustained_key)
    redis_client.expire(sustained_key, 60)
    
    if sustained_count > 100:
        return False
    
    return True
```

### Pattern 4: Graceful Degradation

```python
# infrastructure/rate_limiter.py

def check_rate_limit_with_degradation(user_id, limit):
    """Check rate limit with graceful degradation."""
    current_count = get_current_count(user_id)
    
    if current_count < limit:
        # Normal operation
        return {'allowed': True, 'priority': 'normal'}
    elif current_count < limit * 1.2:
        # Soft limit - allow but deprioritize
        return {'allowed': True, 'priority': 'low'}
    else:
        # Hard limit - reject
        return {'allowed': False, 'priority': None}

# Usage
result = check_rate_limit_with_degradation(user_id, 100)
if not result['allowed']:
    return HttpResponse('Rate limit exceeded', status=429)
elif result['priority'] == 'low':
    # Process request with lower priority
    request.priority = 'low'
```

## Monitoring

### Key Metrics

Monitor via `/metrics/json`:

```json
{
  "rate_limiting": {
    "total_requests": 150000,
    "rate_limited_requests": 1250,
    "rate_limit_hit_rate": 0.83,
    "per_user_violations": 45,
    "global_violations": 5
  }
}
```

### Grafana Dashboard

Create dashboard with panels for:

- Rate limit violations over time
- Top rate-limited users
- Rate limit hit rate by endpoint
- Global vs per-user violations

### Alerts

```yaml
# prometheus/alerts/rate_limiting_alerts.yml
groups:
  - name: rate_limiting_alerts
    rules:
      - alert: HighRateLimitViolations
        expr: rate(rate_limited_requests[5m]) > 100
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High rate of rate limit violations"
          description: "{{ $value }} requests/sec being rate limited"
      
      - alert: GlobalRateLimitHit
        expr: global_rate_limit_violations > 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Global rate limit reached"
          description: "System-wide rate limit has been hit"
```

## Troubleshooting

### Issue 1: Legitimate Users Being Rate Limited

**Symptoms**:
- User complaints about 429 errors
- High rate limit violation rate
- Normal usage patterns being blocked

**Diagnosis**:
```bash
# Check rate limit violations by user
redis-cli --scan --pattern "rate_limit:user:*" | while read key; do
    echo "$key: $(redis-cli get $key)"
done | sort -t: -k3 -rn | head -20
```

**Solutions**:

1. **Increase per-user limit**:
```python
RATE_LIMITING = {
    'per_user': {
        'queries_per_minute': 200,  # Increased from 100
    },
}
```

2. **Implement tiered limits**:
```python
# Give power users higher limits
if user.is_power_user:
    limit = 500
else:
    limit = 100
```

3. **Add burst allowance**:
```python
RATE_LIMITING = {
    'per_user': {
        'sustained_rate': 100,
        'burst_rate': 200,
    },
}
```

### Issue 2: Rate Limiting Not Working

**Symptoms**:
- No 429 responses
- Database overload despite rate limiting
- Rate limit metrics show zero violations

**Diagnosis**:
```python
# Test rate limiter
from infrastructure.rate_limiter import RateLimiter

limiter = RateLimiter()
for i in range(150):
    result = limiter.check_user_limit('test_user')
    print(f"Request {i}: {result}")
```

**Solutions**:

1. **Verify middleware is enabled**:
```python
# config/settings.py
MIDDLEWARE = [
    # ...
    'infrastructure.middleware.RateLimitMiddleware',  # Must be present
]
```

2. **Check Redis connectivity**:
```bash
redis-cli -h $REDIS_HOST -p $REDIS_PORT -a $REDIS_PASSWORD ping
```

3. **Verify configuration**:
```python
# Check settings
from django.conf import settings
print(settings.RATE_LIMITING)
```

### Issue 3: Redis Performance Issues

**Symptoms**:
- Slow rate limit checks
- High Redis CPU usage
- Rate limiting adding latency

**Diagnosis**:
```bash
# Check Redis performance
redis-cli --latency
redis-cli --stat
```

**Solutions**:

1. **Use pipelining**:
```python
# Batch Redis operations
pipe = redis_client.pipeline()
pipe.incr(key)
pipe.expire(key, window)
results = pipe.execute()
```

2. **Optimize key structure**:
```python
# Use shorter keys
# Bad: rate_limit:user:12345:endpoint:/v1/stories/:window:60
# Good: rl:u:12345:e:stories:w:60
```

3. **Add Redis cluster**:
```python
# Distribute load across Redis nodes
RATE_LIMITING = {
    'redis_url': 'redis://redis-cluster:6379/1',
    'redis_cluster': True,
}
```

## Best Practices

1. **Start Conservative**: Begin with lower limits and increase based on monitoring
2. **Monitor Continuously**: Track rate limit violations and adjust
3. **Communicate Limits**: Document rate limits in API documentation
4. **Provide Feedback**: Include rate limit info in response headers
5. **Implement Gracefully**: Use 429 status with Retry-After header
6. **Test Thoroughly**: Load test with rate limiting enabled
7. **Plan for Growth**: Review limits as traffic increases

## Response Headers

Include rate limit information in responses:

```python
# Response headers
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1645123456

# On rate limit exceeded
HTTP/1.1 429 Too Many Requests
Retry-After: 60
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1645123456
```

## Additional Resources

- [Rate Limiting Algorithms](https://en.wikipedia.org/wiki/Rate_limiting)
- [Redis Rate Limiting](https://redis.io/docs/manual/patterns/rate-limiter/)
- [API Rate Limiting Best Practices](https://cloud.google.com/architecture/rate-limiting-strategies-techniques)
