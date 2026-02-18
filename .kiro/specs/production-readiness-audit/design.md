# Production Readiness Fixes - Design Document

## Overview

This document provides detailed technical solutions for all critical production readiness issues identified in the audit. The fixes are organized by priority and include implementation details, code examples, and testing strategies.

## Architecture Changes

### 1. Authentication Layer Redesign

**Current State**: JWT tokens decoded without signature verification
**Target State**: Proper JWT verification with Clerk public keys

**Components**:
- JWT verification service
- Clerk public key fetcher
- Token validation middleware
- Error handling for expired/invalid tokens

### 2. Database Layer Redesign

**Current State**: No connection pooling, direct Django ORM usage
**Target State**: Connection pooling with pgbouncer, optimized queries

**Components**:
- Connection pool configuration
- Query optimization layer
- Transaction management
- Read replica routing

### 3. Security Layer Implementation

**Current State**: Secrets in environment variables, no validation
**Target State**: AWS Secrets Manager integration, validated configuration

**Components**:
- Secrets manager client
- Configuration validator
- Secret rotation automation
- Audit logging

### 4. Reliability Layer Implementation

**Current State**: No timeouts, no circuit breakers
**Target State**: Request timeouts, circuit breakers, graceful degradation

**Components**:
- Timeout middleware
- Circuit breaker wrapper
- Health check system
- Graceful shutdown

## Detailed Solutions

### Solution 1: JWT Verification Service

**File**: `apps/backend/apps/users/jwt_service.py`

**Purpose**: Properly verify JWT tokens with Clerk's public keys

**Implementation**:

```python
import jwt
import requests
from functools import lru_cache
from django.conf import settings
from django.core.cache import cache

class JWTVerificationService:
    """Service for verifying Clerk JWT tokens with proper signature validation"""
    
    JWKS_CACHE_KEY = 'clerk_jwks'
    JWKS_CACHE_TTL = 3600  # 1 hour
    
    @staticmethod
    @lru_cache(maxsize=1)
    def get_clerk_jwks_url():
        """Get Clerk JWKS URL from publishable key"""
        pub_key = settings.CLERK_PUBLISHABLE_KEY
        # Extract instance ID from publishable key (pk_test_xxx or pk_live_xxx)
        return f"https://api.clerk.com/v1/jwks"
    
    @classmethod
    def get_jwks(cls):
        """Fetch and cache Clerk's JWKS (JSON Web Key Set)"""
        jwks = cache.get(cls.JWKS_CACHE_KEY)
        if jwks:
            return jwks
        
        try:
            response = requests.get(cls.get_clerk_jwks_url(), timeout=5)
            response.raise_for_status()
            jwks = response.json()
            cache.set(cls.JWKS_CACHE_KEY, jwks, cls.JWKS_CACHE_TTL)
            return jwks
        except Exception as e:
            raise Exception(f"Failed to fetch Clerk JWKS: {e}")
    
    @classmethod
    def verify_token(cls, token: str) -> dict:
        """Verify JWT token and return decoded payload"""
        try:
            # Get JWKS
            jwks = cls.get_jwks()
            
            # Decode header to get key ID
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get('kid')
            
            # Find matching key
            key = None
            for jwk in jwks.get('keys', []):
                if jwk.get('kid') == kid:
                    key = jwt.algorithms.RSAAlgorithm.from_jwk(jwk)
                    break
            
            if not key:
                raise jwt.InvalidTokenError("No matching key found")
            
            # Verify and decode token
            decoded = jwt.decode(
                token,
                key=key,
                algorithms=['RS256'],
                audience=settings.CLERK_PUBLISHABLE_KEY,
                options={
                    'verify_signature': True,
                    'verify_exp': True,
                    'verify_aud': True
                }
            )
            
            return decoded
            
        except jwt.ExpiredSignatureError:
            raise Exception("Token has expired")
        except jwt.InvalidTokenError as e:
            raise Exception(f"Invalid token: {e}")
```

**Testing Strategy**:
- Test with valid Clerk token
- Test with expired token
- Test with invalid signature
- Test with wrong audience
- Test JWKS caching
- Test JWKS refresh on failure

---

### Solution 2: Secure Configuration Management

**File**: `apps/backend/config/secure_settings.py`

**Purpose**: Enforce secure configuration with no defaults

**Implementation**:
```python
import os
from django.core.exceptions import ImproperlyConfigured

class SecureConfig:
    """Secure configuration management with validation"""
    
    @staticmethod
    def get_required(key: str, description: str = "") -> str:
        """Get required environment variable or raise error"""
        value = os.getenv(key)
        if not value:
            raise ImproperlyConfigured(
                f"Required environment variable '{key}' is not set.\n"
                f"Description: {description}\n"
                f"Set it in your environment or .env file."
            )
        return value
    
    @staticmethod
    def get_secret_key() -> str:
        """Get Django SECRET_KEY with validation"""
        key = SecureConfig.get_required(
            'SECRET_KEY',
            'Django secret key for cryptographic signing'
        )
        
        # Validate it's not a default/example value
        insecure_patterns = [
            'django-insecure',
            'change-this',
            'your-secret-key',
            'example',
            'test-key'
        ]
        
        if any(pattern in key.lower() for pattern in insecure_patterns):
            raise ImproperlyConfigured(
                f"SECRET_KEY appears to be an example value. "
                f"Generate a secure key with: "
                f"python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'"
            )
        
        if len(key) < 50:
            raise ImproperlyConfigured(
                f"SECRET_KEY is too short ({len(key)} chars). "
                f"It should be at least 50 characters."
            )
        
        return key
    
    @staticmethod
    def validate_production_config():
        """Validate all production-required configuration"""
        if os.getenv('ENVIRONMENT') == 'production':
            # Ensure DEBUG is False
            if os.getenv('DEBUG', 'False') != 'False':
                raise ImproperlyConfigured(
                    "DEBUG must be False in production"
                )
            
            # Ensure HTTPS is enforced
            if os.getenv('SECURE_SSL_REDIRECT', 'True') != 'True':
                raise ImproperlyConfigured(
                    "SECURE_SSL_REDIRECT must be True in production"
                )
            
            # Ensure monitoring is configured
            if not os.getenv('SENTRY_DSN'):
                raise ImproperlyConfigured(
                    "SENTRY_DSN must be set in production"
                )
```

**Update settings.py**:
```python
from config.secure_settings import SecureConfig

# Replace insecure SECRET_KEY line with:
SECRET_KEY = SecureConfig.get_secret_key()

# Add production validation
if os.getenv('ENVIRONMENT') == 'production':
    SecureConfig.validate_production_config()
```

---

### Solution 3: Database Connection Pooling

**File**: `apps/backend/config/database.py`

**Purpose**: Implement proper connection pooling

**Implementation**:
```python
import os
from django.conf import settings

def get_database_config():
    """Get database configuration with connection pooling"""
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ImproperlyConfigured("DATABASE_URL must be set")
    
    # Parse DATABASE_URL properly
    from urllib.parse import urlparse
    parsed = urlparse(database_url)
    
    config = {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': parsed.path[1:],  # Remove leading /
        'USER': parsed.username,
        'PASSWORD': parsed.password,
        'HOST': parsed.hostname,
        'PORT': parsed.port or 5432,
        'CONN_MAX_AGE': 600,  # Keep connections alive for 10 minutes
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c statement_timeout=30000',  # 30 second query timeout
            'pool_size': int(os.getenv('DB_POOL_SIZE', '20')),
            'max_overflow': int(os.getenv('DB_POOL_MAX_OVERFLOW', '10')),
        },
    }
    
    return config
```

**Install pgbouncer** (recommended for production):
```yaml
# docker-compose.yml addition
pgbouncer:
  image: pgbouncer/pgbouncer:latest
  environment:
    - DATABASES_HOST=postgres
    - DATABASES_PORT=5432
    - DATABASES_USER=muejam_user
    - DATABASES_PASSWORD=muejam_password
    - DATABASES_DBNAME=muejam
    - POOL_MODE=transaction
    - MAX_CLIENT_CONN=1000
    - DEFAULT_POOL_SIZE=25
  ports:
    - "6432:6432"
```

---

### Solution 4: Request Timeout Middleware

**File**: `apps/backend/infrastructure/timeout_middleware.py`

**Purpose**: Prevent long-running requests from exhausting resources

**Implementation**:
```python
import signal
import logging
from django.conf import settings
from django.http import JsonResponse

logger = logging.getLogger(__name__)

class TimeoutMiddleware:
    """Middleware to enforce request timeouts"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.timeout = getattr(settings, 'REQUEST_TIMEOUT', 30)
    
    def __call__(self, request):
        # Set alarm for timeout
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Request exceeded {self.timeout}s timeout")
        
        # Only apply timeout to non-admin requests
        if not request.path.startswith('/django-admin/'):
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(self.timeout)
        
        try:
            response = self.get_response(request)
            return response
        except TimeoutError as e:
            logger.error(
                f"Request timeout: {request.method} {request.path}",
                extra={
                    'request_path': request.path,
                    'request_method': request.method,
                    'timeout': self.timeout
                }
            )
            return JsonResponse(
                {'error': 'Request timeout', 'detail': str(e)},
                status=504
            )
        finally:
            # Cancel alarm
            if not request.path.startswith('/django-admin/'):
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
```

**Add to MIDDLEWARE in settings.py**:
```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'infrastructure.timeout_middleware.TimeoutMiddleware',  # Add early
    # ... rest of middleware
]

REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '30'))
```

---

### Solution 5: Fix Async/Sync Pattern

**File**: `apps/backend/apps/users/middleware.py` (refactored)

**Purpose**: Remove nest_asyncio anti-pattern

**Implementation Option 1 - Convert to Sync**:
```python
from .utils import get_or_create_profile_sync  # Rename async function to sync

class ClerkAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.jwt_service = JWTVerificationService()
    
    def __call__(self, request):
        request.clerk_user_id = None
        request.user_profile = None
        request.auth_error = None
        
        auth_header = request.headers.get('Authorization', '')
        
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            
            try:
                # Verify token with proper signature validation
                decoded = self.jwt_service.verify_token(token)
                request.clerk_user_id = decoded.get('sub')
                
                if request.clerk_user_id:
                    # Use synchronous database call
                    request.user_profile = get_or_create_profile_sync(
                        request.clerk_user_id
                    )
                    
                    if request.user_profile:
                        log_authentication_event(
                            logger=structured_logger,
                            event_type='token_verification',
                            user_id=str(request.user_profile.id),
                            success=True,
                        )
                        
            except Exception as e:
                logger.warning(f"Authentication failed: {e}")
                request.auth_error = str(e)
        
        response = self.get_response(request)
        return response
```

**Create sync version of utils**:
```python
# apps/backend/apps/users/utils.py
from prisma import Prisma

def get_or_create_profile_sync(clerk_user_id: str):
    """Synchronous version - use Django ORM instead of Prisma"""
    from .models import UserProfile  # Assuming Django model exists
    
    profile, created = UserProfile.objects.get_or_create(
        clerk_user_id=clerk_user_id,
        defaults={
            'handle': f'user_{clerk_user_id[:8]}',
            'display_name': 'New User'
        }
    )
    return profile
```

---

### Solution 6: Transaction Management

**File**: `apps/backend/apps/core/decorators.py`

**Purpose**: Ensure atomic operations

**Implementation**:
```python
from functools import wraps
from django.db import transaction
from rest_framework.response import Response
import logging

logger = logging.getLogger(__name__)

def atomic_api_view(func):
    """Decorator for atomic API views with proper error handling"""
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        try:
            with transaction.atomic():
                return func(request, *args, **kwargs)
        except Exception as e:
            logger.error(
                f"Transaction failed in {func.__name__}: {e}",
                exc_info=True,
                extra={
                    'view': func.__name__,
                    'user': getattr(request, 'user_profile', None),
                    'path': request.path
                }
            )
            return Response(
                {'error': 'Operation failed', 'detail': str(e)},
                status=500
            )
    return wrapper
```

**Usage in views**:
```python
from apps.core.decorators import atomic_api_view

@atomic_api_view
def create_story_with_chapters(request):
    # All database operations are atomic
    story = Story.objects.create(...)
    for chapter_data in request.data.get('chapters', []):
        Chapter.objects.create(story=story, ...)
    return Response({'id': story.id})
```

---

### Solution 7: Rate Limiting Enforcement

**File**: `apps/backend/infrastructure/rate_limit_middleware.py`

**Purpose**: Enforce rate limits on all requests

**Implementation**:
```python
from django.http import JsonResponse
from infrastructure.rate_limiter import RateLimiter
import logging

logger = logging.getLogger(__name__)

class RateLimitMiddleware:
    """Middleware to enforce rate limiting"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.rate_limiter = RateLimiter()
    
    def __call__(self, request):
        # Skip rate limiting for health checks
        if request.path in ['/health', '/metrics']:
            return self.get_response(request)
        
        # Get user ID (use IP if not authenticated)
        user_id = None
        if hasattr(request, 'user_profile') and request.user_profile:
            user_id = str(request.user_profile.id)
        else:
            user_id = self.get_client_ip(request)
        
        # Check if admin (bypass rate limiting)
        is_admin = self.is_admin_user(request)
        
        # Check rate limit
        if not self.rate_limiter.allow_request(user_id, is_admin):
            user_result = self.rate_limiter.check_user_limit(user_id)
            
            logger.warning(
                f"Rate limit exceeded for {user_id}",
                extra={
                    'user_id': user_id,
                    'path': request.path,
                    'limit': user_result.limit,
                    'retry_after': user_result.retry_after
                }
            )
            
            response = JsonResponse(
                {
                    'error': 'Rate limit exceeded',
                    'limit': user_result.limit,
                    'retry_after': user_result.retry_after
                },
                status=429
            )
            response['Retry-After'] = str(user_result.retry_after)
            response['X-RateLimit-Limit'] = str(user_result.limit)
            response['X-RateLimit-Remaining'] = '0'
            response['X-RateLimit-Reset'] = user_result.reset_at.isoformat()
            return response
        
        # Add rate limit headers to response
        response = self.get_response(request)
        user_result = self.rate_limiter.check_user_limit(user_id)
        response['X-RateLimit-Limit'] = str(user_result.limit)
        response['X-RateLimit-Remaining'] = str(user_result.remaining)
        response['X-RateLimit-Reset'] = user_result.reset_at.isoformat()
        
        return response
    
    @staticmethod
    def get_client_ip(request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    @staticmethod
    def is_admin_user(request):
        """Check if user is admin"""
        if hasattr(request, 'user_profile') and request.user_profile:
            # Check if user has admin role
            from apps.admin.models import ModeratorRole
            return ModeratorRole.objects.filter(
                user_id=request.user_profile.id,
                is_active=True
            ).exists()
        return False
```

**Add to MIDDLEWARE**:
```python
MIDDLEWARE = [
    # ... other middleware
    'infrastructure.rate_limit_middleware.RateLimitMiddleware',
    # ... rest
]
```

---

### Solution 8: Health Check Implementation

**File**: `apps/backend/infrastructure/health_check.py`

**Purpose**: Comprehensive health checks

**Implementation**:
```python
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
import time
import logging

logger = logging.getLogger(__name__)

def health_check_view(request):
    """Comprehensive health check endpoint"""
    checks = {
        'database': check_database(),
        'cache': check_cache(),
        'disk': check_disk_space(),
    }
    
    # Overall status
    all_healthy = all(check['status'] == 'healthy' for check in checks.values())
    status_code = 200 if all_healthy else 503
    
    response_data = {
        'status': 'healthy' if all_healthy else 'unhealthy',
        'timestamp': time.time(),
        'checks': checks
    }
    
    if not all_healthy:
        logger.error(f"Health check failed: {checks}")
    
    return JsonResponse(response_data, status=status_code)

def check_database():
    """Check database connectivity"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return {'status': 'healthy', 'latency_ms': 0}
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {'status': 'unhealthy', 'error': str(e)}

def check_cache():
    """Check Redis/cache connectivity"""
    try:
        test_key = 'health_check_test'
        test_value = str(time.time())
        cache.set(test_key, test_value, 10)
        retrieved = cache.get(test_key)
        if retrieved == test_value:
            return {'status': 'healthy'}
        else:
            return {'status': 'unhealthy', 'error': 'Cache value mismatch'}
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        return {'status': 'unhealthy', 'error': str(e)}

def check_disk_space():
    """Check available disk space"""
    try:
        import shutil
        stat = shutil.disk_usage('/')
        percent_used = (stat.used / stat.total) * 100
        
        if percent_used > 90:
            return {'status': 'unhealthy', 'percent_used': percent_used}
        elif percent_used > 80:
            return {'status': 'degraded', 'percent_used': percent_used}
        else:
            return {'status': 'healthy', 'percent_used': percent_used}
    except Exception as e:
        return {'status': 'unknown', 'error': str(e)}
```

---

## Testing Strategy

### Unit Tests
- Test JWT verification with valid/invalid tokens
- Test rate limiting with various scenarios
- Test transaction rollback
- Test health checks

### Integration Tests
- Test authentication flow end-to-end
- Test rate limiting across requests
- Test database connection pooling
- Test timeout handling

### Load Tests
- Test with 100 concurrent users
- Test with 1000 concurrent users
- Test rate limiting under load
- Test connection pool under load

### Security Tests
- Test JWT signature verification
- Test rate limiting bypass attempts
- Test timeout attacks
- Test secret key validation

## Deployment Checklist

- [ ] All environment variables set
- [ ] SECRET_KEY generated and secure
- [ ] Database connection pooling configured
- [ ] Rate limiting enabled
- [ ] Health checks working
- [ ] Monitoring configured
- [ ] Load tests passed
- [ ] Security scan passed

## Rollback Plan

If issues occur after deployment:
1. Revert to previous version
2. Check logs for errors
3. Verify configuration
4. Test in staging
5. Redeploy with fixes

## Monitoring

Key metrics to monitor:
- Request latency (P50, P95, P99)
- Error rate
- Rate limit hits
- Database connection pool utilization
- Health check status
- JWT verification failures

## Documentation

- Update API documentation
- Document new environment variables
- Create runbooks for common issues
- Document rollback procedures
