"""
Rate Limiter with sliding window algorithm for multi-layer rate limiting.

This module implements rate limiting at multiple levels:
- Per-user rate limiting (configurable, default: 100 queries/minute)
- Global rate limiting (configurable, default: 10,000 queries/minute)
- Admin bypass capability
- Distributed rate limiting using Redis

The sliding window algorithm provides accurate rate limiting by tracking
requests within a moving time window, preventing burst traffic at window boundaries.
"""

import time
from datetime import datetime, timedelta
from typing import Optional

import redis
from redis.exceptions import RedisError

try:
    from django.conf import settings
    DJANGO_AVAILABLE = True
except ImportError:
    DJANGO_AVAILABLE = False
    settings = None

from .models import RateLimitResult, LimitInfo


class RateLimiter:
    """
    Multi-layer rate limiter with sliding window algorithm.
    
    Implements rate limiting at two levels:
    1. Per-user limits: Configurable queries per minute per user (default: 100)
    2. Global limits: Configurable queries per minute across all users (default: 10,000)
    
    Uses Redis for distributed rate limiting state, allowing the rate limiter
    to work correctly across multiple application instances.
    
    Admin users can bypass rate limits for administrative operations.
    """
    
    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize rate limiter.
        
        Args:
            redis_url: Redis connection URL for distributed state (defaults to settings.RATE_LIMIT_REDIS_URL)
        """
        # Load configuration from settings if Django is available
        if redis_url is None:
            if DJANGO_AVAILABLE and settings:
                redis_url = getattr(settings, 'RATE_LIMIT_REDIS_URL', 
                                  getattr(settings, 'VALKEY_URL', 'redis://localhost:6379/0'))
            else:
                redis_url = 'redis://localhost:6379/0'
        
        if DJANGO_AVAILABLE and settings:
            self.PER_USER_LIMIT = getattr(settings, 'RATE_LIMIT_PER_USER', 100)
            self.GLOBAL_LIMIT = getattr(settings, 'RATE_LIMIT_GLOBAL', 10000)
            self.WINDOW_SIZE = getattr(settings, 'RATE_LIMIT_WINDOW', 60)
            self.enabled = getattr(settings, 'RATE_LIMIT_ENABLED', True)
            self.admin_bypass = getattr(settings, 'RATE_LIMIT_ADMIN_BYPASS', True)
        else:
            # Default values when Django is not available
            self.PER_USER_LIMIT = 100
            self.GLOBAL_LIMIT = 10000
            self.WINDOW_SIZE = 60
            self.enabled = True
            self.admin_bypass = True
        
        # Initialize Redis client
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            self.redis_client.ping()
            self.redis_available = True
        except Exception as e:
            print(f"Warning: Redis connection failed: {e}. Rate limiting disabled.")
            self.redis_client = None
            self.redis_available = False
        
        # Key prefixes for Redis
        self.user_prefix = "ratelimit:user:"
        self.global_key = "ratelimit:global"
    
    def check_user_limit(self, user_id: str) -> RateLimitResult:
        """
        Check per-user rate limit using sliding window algorithm.
        
        Args:
            user_id: User identifier
            
        Returns:
            RateLimitResult with limit status
        """
        if not self.redis_available:
            # If Redis is unavailable, allow all requests
            return RateLimitResult(
                allowed=True,
                limit=self.PER_USER_LIMIT,
                remaining=self.PER_USER_LIMIT,
                reset_at=datetime.now() + timedelta(seconds=self.WINDOW_SIZE)
            )
        
        key = self.user_prefix + user_id
        current_time = time.time()
        window_start = current_time - self.WINDOW_SIZE
        
        try:
            # Use Redis sorted set for sliding window
            # Score is timestamp, value is unique request ID
            
            # Remove old entries outside the window
            self.redis_client.zremrangebyscore(key, 0, window_start)
            
            # Count requests in current window
            request_count = self.redis_client.zcard(key)
            
            # Check if limit exceeded
            if request_count >= self.PER_USER_LIMIT:
                # Get the oldest request timestamp to calculate reset time
                oldest_requests = self.redis_client.zrange(key, 0, 0, withscores=True)
                if oldest_requests:
                    oldest_timestamp = oldest_requests[0][1]
                    reset_at = datetime.fromtimestamp(oldest_timestamp + self.WINDOW_SIZE)
                    retry_after = int((oldest_timestamp + self.WINDOW_SIZE) - current_time)
                else:
                    reset_at = datetime.now() + timedelta(seconds=self.WINDOW_SIZE)
                    retry_after = self.WINDOW_SIZE
                
                return RateLimitResult(
                    allowed=False,
                    limit=self.PER_USER_LIMIT,
                    remaining=0,
                    reset_at=reset_at,
                    retry_after=max(1, retry_after)
                )
            
            # Add current request
            request_id = f"{current_time}:{id(self)}"
            self.redis_client.zadd(key, {request_id: current_time})
            
            # Set expiration on the key to clean up inactive users
            self.redis_client.expire(key, self.WINDOW_SIZE * 2)
            
            # Calculate remaining requests
            remaining = self.PER_USER_LIMIT - (request_count + 1)
            
            # Calculate reset time (end of current window)
            reset_at = datetime.now() + timedelta(seconds=self.WINDOW_SIZE)
            
            return RateLimitResult(
                allowed=True,
                limit=self.PER_USER_LIMIT,
                remaining=remaining,
                reset_at=reset_at
            )
            
        except RedisError as e:
            print(f"Warning: Redis error in check_user_limit: {e}")
            # Fail open - allow request if Redis fails
            return RateLimitResult(
                allowed=True,
                limit=self.PER_USER_LIMIT,
                remaining=self.PER_USER_LIMIT,
                reset_at=datetime.now() + timedelta(seconds=self.WINDOW_SIZE)
            )
    
    def check_global_limit(self) -> RateLimitResult:
        """
        Check global rate limit using sliding window algorithm.
        
        Returns:
            RateLimitResult with global limit status
        """
        if not self.redis_available:
            # If Redis is unavailable, allow all requests
            return RateLimitResult(
                allowed=True,
                limit=self.GLOBAL_LIMIT,
                remaining=self.GLOBAL_LIMIT,
                reset_at=datetime.now() + timedelta(seconds=self.WINDOW_SIZE)
            )
        
        key = self.global_key
        current_time = time.time()
        window_start = current_time - self.WINDOW_SIZE
        
        try:
            # Use Redis sorted set for sliding window
            
            # Remove old entries outside the window
            self.redis_client.zremrangebyscore(key, 0, window_start)
            
            # Count requests in current window
            request_count = self.redis_client.zcard(key)
            
            # Check if limit exceeded
            if request_count >= self.GLOBAL_LIMIT:
                # Get the oldest request timestamp to calculate reset time
                oldest_requests = self.redis_client.zrange(key, 0, 0, withscores=True)
                if oldest_requests:
                    oldest_timestamp = oldest_requests[0][1]
                    reset_at = datetime.fromtimestamp(oldest_timestamp + self.WINDOW_SIZE)
                    retry_after = int((oldest_timestamp + self.WINDOW_SIZE) - current_time)
                else:
                    reset_at = datetime.now() + timedelta(seconds=self.WINDOW_SIZE)
                    retry_after = self.WINDOW_SIZE
                
                return RateLimitResult(
                    allowed=False,
                    limit=self.GLOBAL_LIMIT,
                    remaining=0,
                    reset_at=reset_at,
                    retry_after=max(1, retry_after)
                )
            
            # Add current request
            request_id = f"{current_time}:{id(self)}"
            self.redis_client.zadd(key, {request_id: current_time})
            
            # Set expiration on the key
            self.redis_client.expire(key, self.WINDOW_SIZE * 2)
            
            # Calculate remaining requests
            remaining = self.GLOBAL_LIMIT - (request_count + 1)
            
            # Calculate reset time (end of current window)
            reset_at = datetime.now() + timedelta(seconds=self.WINDOW_SIZE)
            
            return RateLimitResult(
                allowed=True,
                limit=self.GLOBAL_LIMIT,
                remaining=remaining,
                reset_at=reset_at
            )
            
        except RedisError as e:
            print(f"Warning: Redis error in check_global_limit: {e}")
            # Fail open - allow request if Redis fails
            return RateLimitResult(
                allowed=True,
                limit=self.GLOBAL_LIMIT,
                remaining=self.GLOBAL_LIMIT,
                reset_at=datetime.now() + timedelta(seconds=self.WINDOW_SIZE)
            )
    
    def allow_request(self, user_id: str, is_admin: bool = False) -> bool:
        """
        Determine if request should be allowed based on rate limits.
        
        Checks both per-user and global rate limits. Admin users bypass
        all rate limits if admin_bypass is enabled.
        
        Args:
            user_id: User identifier
            is_admin: Whether user has admin privileges
            
        Returns:
            True if request is allowed, False if rate limited
        """
        # Check if rate limiting is enabled
        if not self.enabled:
            return True
        
        # Admin bypass
        if is_admin and self.admin_bypass:
            return True
        
        # Check per-user limit
        user_result = self.check_user_limit(user_id)
        if not user_result.allowed:
            return False
        
        # Check global limit
        global_result = self.check_global_limit()
        if not global_result.allowed:
            return False
        
        return True
    
    def get_limit_info(self, user_id: str) -> LimitInfo:
        """
        Get current rate limit status for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            LimitInfo with current limit status
        """
        if not self.redis_available:
            # If Redis is unavailable, return default info
            now = datetime.now()
            return LimitInfo(
                user_id=user_id,
                requests_made=0,
                limit=self.PER_USER_LIMIT,
                window_start=now,
                window_end=now + timedelta(seconds=self.WINDOW_SIZE)
            )
        
        key = self.user_prefix + user_id
        current_time = time.time()
        window_start = current_time - self.WINDOW_SIZE
        
        try:
            # Remove old entries
            self.redis_client.zremrangebyscore(key, 0, window_start)
            
            # Count current requests
            request_count = self.redis_client.zcard(key)
            
            return LimitInfo(
                user_id=user_id,
                requests_made=request_count,
                limit=self.PER_USER_LIMIT,
                window_start=datetime.fromtimestamp(window_start),
                window_end=datetime.now() + timedelta(seconds=self.WINDOW_SIZE)
            )
            
        except RedisError as e:
            print(f"Warning: Redis error in get_limit_info: {e}")
            now = datetime.now()
            return LimitInfo(
                user_id=user_id,
                requests_made=0,
                limit=self.PER_USER_LIMIT,
                window_start=now,
                window_end=now + timedelta(seconds=self.WINDOW_SIZE)
            )


class MobileRateLimiter(RateLimiter):
    """
    Extended rate limiter with mobile-specific policies.
    
    Applies different rate limits based on client type:
    - Web clients: 100 requests/minute (default)
    - Mobile clients (iOS/Android): 150 requests/minute
    
    This allows mobile clients higher rate limits to accommodate
    mobile-specific usage patterns and batch operations.
    
    Requirements: 8.1, 8.2
    """
    
    # Rate limits per minute by client type
    RATE_LIMITS = {
        'web': 100,
        'mobile-ios': 150,
        'mobile-android': 150,
        'default': 100
    }
    
    def get_rate_limit(self, client_type: str) -> int:
        """
        Get rate limit for client type.
        
        Args:
            client_type: Client type string (web, mobile-ios, mobile-android)
            
        Returns:
            Requests per minute limit for the client type
        """
        if DJANGO_AVAILABLE and settings:
            web_limit = getattr(settings, 'RATE_LIMIT_PER_USER', self.PER_USER_LIMIT)
            mobile_limit = getattr(
                settings,
                'RATE_LIMIT_MOBILE_PER_USER',
                self.RATE_LIMITS['mobile-ios']
            )

            if client_type in ('mobile-ios', 'mobile-android'):
                return mobile_limit

            return web_limit

        return self.RATE_LIMITS.get(client_type, self.RATE_LIMITS['default'])
    
    def check_user_limit(self, user_id: str, client_type: str = 'web') -> RateLimitResult:
        """
        Check per-user rate limit with client-type-specific limits.
        
        Args:
            user_id: User identifier
            client_type: Client type for rate limit selection
            
        Returns:
            RateLimitResult with limit status
        """
        # Get client-specific rate limit
        per_user_limit = self.get_rate_limit(client_type)
        
        if not self.redis_available:
            # If Redis is unavailable, allow all requests
            return RateLimitResult(
                allowed=True,
                limit=per_user_limit,
                remaining=per_user_limit,
                reset_at=datetime.now() + timedelta(seconds=self.WINDOW_SIZE)
            )
        
        key = f"{self.user_prefix}{user_id}:{client_type}"
        current_time = time.time()
        window_start = current_time - self.WINDOW_SIZE
        
        try:
            # Use Redis sorted set for sliding window
            # Remove old entries outside the window
            self.redis_client.zremrangebyscore(key, 0, window_start)
            
            # Count requests in current window
            request_count = self.redis_client.zcard(key)
            
            # Check if limit exceeded
            if request_count >= per_user_limit:
                # Get the oldest request timestamp to calculate reset time
                oldest_requests = self.redis_client.zrange(key, 0, 0, withscores=True)
                if oldest_requests:
                    oldest_timestamp = oldest_requests[0][1]
                    reset_at = datetime.fromtimestamp(oldest_timestamp + self.WINDOW_SIZE)
                    retry_after = int((oldest_timestamp + self.WINDOW_SIZE) - current_time)
                else:
                    reset_at = datetime.now() + timedelta(seconds=self.WINDOW_SIZE)
                    retry_after = self.WINDOW_SIZE
                
                return RateLimitResult(
                    allowed=False,
                    limit=per_user_limit,
                    remaining=0,
                    reset_at=reset_at,
                    retry_after=max(1, retry_after)
                )
            
            # Add current request
            request_id = f"{current_time}:{id(self)}"
            self.redis_client.zadd(key, {request_id: current_time})
            
            # Set expiration on the key to clean up inactive users
            self.redis_client.expire(key, self.WINDOW_SIZE * 2)
            
            # Calculate remaining requests
            remaining = per_user_limit - (request_count + 1)
            
            # Calculate reset time (end of current window)
            reset_at = datetime.now() + timedelta(seconds=self.WINDOW_SIZE)
            
            return RateLimitResult(
                allowed=True,
                limit=per_user_limit,
                remaining=remaining,
                reset_at=reset_at
            )
            
        except RedisError as e:
            print(f"Warning: Redis error in check_user_limit: {e}")
            # Fail open - allow request if Redis fails
            return RateLimitResult(
                allowed=True,
                limit=per_user_limit,
                remaining=per_user_limit,
                reset_at=datetime.now() + timedelta(seconds=self.WINDOW_SIZE)
            )
    
    def allow_request(self, user_id: str, is_admin: bool = False, client_type: str = 'web') -> bool:
        """
        Determine if request should be allowed based on rate limits.
        
        Checks both per-user and global rate limits with client-type-specific
        limits. Admin users bypass all rate limits if admin_bypass is enabled.
        
        Args:
            user_id: User identifier
            is_admin: Whether user has admin privileges
            client_type: Client type for rate limit selection
            
        Returns:
            True if request is allowed, False if rate limited
        """
        # Check if rate limiting is enabled
        if not self.enabled:
            return True
        
        # Admin bypass
        if is_admin and self.admin_bypass:
            return True
        
        # Check per-user limit with client type
        user_result = self.check_user_limit(user_id, client_type)
        if not user_result.allowed:
            return False
        
        # Check global limit
        global_result = self.check_global_limit()
        if not global_result.allowed:
            return False
        
        return True
    
    def get_limit_info(self, user_id: str, client_type: str = 'web') -> LimitInfo:
        """
        Get current rate limit status for a user with client-type-specific limits.
        
        Args:
            user_id: User identifier
            client_type: Client type for rate limit selection
            
        Returns:
            LimitInfo with current limit status
        """
        # Get client-specific rate limit
        per_user_limit = self.get_rate_limit(client_type)
        
        if not self.redis_available:
            # If Redis is unavailable, return default info
            now = datetime.now()
            return LimitInfo(
                user_id=user_id,
                requests_made=0,
                limit=per_user_limit,
                window_start=now,
                window_end=now + timedelta(seconds=self.WINDOW_SIZE)
            )
        
        key = f"{self.user_prefix}{user_id}:{client_type}"
        current_time = time.time()
        window_start = current_time - self.WINDOW_SIZE
        
        try:
            # Remove old entries
            self.redis_client.zremrangebyscore(key, 0, window_start)
            
            # Count current requests
            request_count = self.redis_client.zcard(key)
            
            return LimitInfo(
                user_id=user_id,
                requests_made=request_count,
                limit=per_user_limit,
                window_start=datetime.fromtimestamp(window_start),
                window_end=datetime.now() + timedelta(seconds=self.WINDOW_SIZE)
            )
            
        except RedisError as e:
            print(f"Warning: Redis error in get_limit_info: {e}")
            now = datetime.now()
            return LimitInfo(
                user_id=user_id,
                requests_made=0,
                limit=per_user_limit,
                window_start=now,
                window_end=now + timedelta(seconds=self.WINDOW_SIZE)
            )
