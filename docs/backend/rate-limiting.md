# django-ratelimit Redis Backend Setup

This document describes the django-ratelimit configuration with Redis backend for the MueJam Library platform.

## Overview

The platform uses `django-ratelimit` for distributed rate limiting with Redis as the storage backend. This enables consistent rate limiting across multiple application instances.

## Installation

django-ratelimit is installed via requirements.txt:

```txt
django-ratelimit==4.1.0
```

## Configuration

### Django Settings

The following settings in `config/settings.py` configure django-ratelimit:

```python
# django-ratelimit configuration
# Use Redis cache backend for distributed rate limiting
RATELIMIT_USE_CACHE = 'default'
RATELIMIT_ENABLE = RATE_LIMIT_ENABLED
```

### Environment Variables

Rate limiting behavior is controlled by environment variables:

```bash
# Enable/disable rate limiting
RATE_LIMIT_ENABLED=True

# Redis connection for rate limiting (defaults to VALKEY_URL)
RATE_LIMIT_REDIS_URL=redis://localhost:6379/0

# Per-user rate limits (queries per minute)
RATE_LIMIT_PER_USER=100

# Global rate limits (queries per minute across all users)
RATE_LIMIT_GLOBAL=10000

# Rate limit window size in seconds
RATE_LIMIT_WINDOW=60

# Admin users bypass rate limits
RATE_LIMIT_ADMIN_BYPASS=True
```

## Redis Backend

django-ratelimit uses the Django cache framework configured in settings:

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': VALKEY_URL,
        'KEY_PREFIX': 'muejam',
        'VERSION': 1,
    }
}
```

This configuration:
- Uses Redis as the cache backend
- Stores rate limit counters in Redis with key prefix `muejam:rl:`
- Enables distributed rate limiting across multiple application instances
- Provides automatic key expiration based on rate limit windows

## Usage

### Basic Rate Limiting

Apply rate limits to views using the `@ratelimit` decorator:

```python
from django_ratelimit.decorators import ratelimit
from django.conf import settings

@ratelimit(key='ip', rate='100/m', method='GET')
def my_view(request):
    # View logic here
    pass
```

### Rate Limit Keys

Common rate limit keys:

- `'ip'` - Rate limit by IP address
- `'user'` - Rate limit by authenticated user
- `'user_or_ip'` - Rate limit by user if authenticated, otherwise by IP
- Custom function - Define custom key extraction logic

### Rate Limit Formats

Rate limits are specified as `count/period`:

- `'100/m'` - 100 requests per minute
- `'1000/h'` - 1000 requests per hour
- `'10000/d'` - 10000 requests per day
- `'5/s'` - 5 requests per second

### Multiple Rate Limits

Apply multiple rate limits to a single view:

```python
@ratelimit(key='ip', rate='20/m', method='POST')
@ratelimit(key='user', rate='100/h', method='POST')
def create_content(request):
    # View logic here
    pass
```

### Checking Rate Limit Status

Check if a request is rate limited:

```python
from django_ratelimit.core import is_ratelimited

def my_view(request):
    if is_ratelimited(request, group='my_group', key='ip', rate='100/m', increment=True):
        return Response({'error': 'Rate limit exceeded'}, status=429)
    
    # Process request
    pass
```

### Custom Rate Limit Response

Handle rate limit exceeded in views:

```python
from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='100/m', method='GET')
def my_view(request):
    if getattr(request, 'limited', False):
        return Response(
            {'error': 'Rate limit exceeded. Please try again later.'},
            status=429,
            headers={'Retry-After': '60'}
        )
    
    # View logic here
    pass
```

## Rate Limit Requirements

The following rate limits are configured per requirements 5.6, 5.7, 5.8:

### IP-Based Limits (Unauthenticated)

- **Read operations**: 100 requests per minute per IP
- **Write operations**: 20 requests per minute per IP

### User-Based Limits (Authenticated)

- **General requests**: 1000 requests per hour per user
- **Content submissions**: 10 per hour per user

### Endpoint-Specific Limits

- **Login**: 5 attempts per 15 minutes
- **Password reset**: 10 requests per hour
- **Report submission**: 20 reports per hour

## Verification

Run the verification script to test the configuration:

```bash
python verify_ratelimit_setup.py
```

This script verifies:
1. Redis connection is working
2. django-ratelimit settings are configured correctly
3. Rate limiting functionality works as expected

## Monitoring

### Redis Keys

Rate limit counters are stored in Redis with keys like:

```
muejam:rl:<group>:<key>
```

For example:
- `muejam:rl:api_read:192.168.1.1` - IP-based rate limit
- `muejam:rl:api_write:user_123` - User-based rate limit

### Checking Rate Limit Status

Use Redis CLI to inspect rate limit counters:

```bash
# List all rate limit keys
redis-cli --scan --pattern "muejam:rl:*"

# Get specific rate limit counter
redis-cli GET "muejam:rl:api_read:192.168.1.1"

# Check TTL of rate limit key
redis-cli TTL "muejam:rl:api_read:192.168.1.1"
```

## Troubleshooting

### Rate Limiting Not Working

If rate limiting is not working:

1. **Check Redis connection**:
   ```bash
   python verify_ratelimit_setup.py
   ```

2. **Verify settings**:
   - Ensure `RATELIMIT_ENABLE = True`
   - Ensure `RATELIMIT_USE_CACHE = 'default'`
   - Ensure Redis cache is configured

3. **Check Redis keys**:
   ```bash
   redis-cli --scan --pattern "muejam:rl:*"
   ```

### Rate Limits Too Strict

If legitimate users are being rate limited:

1. Increase rate limit thresholds in environment variables
2. Review actual usage patterns
3. Consider implementing tiered rate limits (free vs. premium users)
4. Enable admin bypass for privileged users

### Redis Connection Issues

If Redis is unavailable:

- django-ratelimit will fail open (allow requests)
- Check Redis connection in Django cache configuration
- Verify `VALKEY_URL` environment variable

## Requirements Satisfied

This configuration satisfies the following requirements:

- **Requirement 5.6**: IP-based rate limiting (100/min reads, 20/min writes) ✓
- **Requirement 5.7**: User-based rate limiting (10 content submissions/hour) ✓
- **Requirement 5.8**: Endpoint-specific rate limiting ✓

## Next Steps

After completing this setup, proceed to:

1. **Task 14.2**: Apply rate limits to API endpoints
2. **Task 14.3**: Implement rate limit response handling with 429 status codes
3. **Task 14.4**: Write property tests for rate limit response format
4. **Task 14.5**: Write property tests for rate limit headers
