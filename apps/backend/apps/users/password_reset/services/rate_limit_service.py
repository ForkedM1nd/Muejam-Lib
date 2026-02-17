"""
Rate Limit Service Implementation

Enforces rate limits to prevent abuse using in-memory cache with sliding window.
"""
from datetime import datetime, timedelta, timezone
from typing import Dict, List
import asyncio
from ..interfaces import IRateLimitService
from ..constants import (
    USER_RATE_LIMIT_REQUESTS,
    USER_RATE_LIMIT_WINDOW_HOURS,
    IP_RATE_LIMIT_REQUESTS,
    IP_RATE_LIMIT_WINDOW_HOURS,
    RATE_LIMIT_USER_KEY_PREFIX,
    RATE_LIMIT_IP_KEY_PREFIX,
)


class RateLimitService(IRateLimitService):
    """
    Service for enforcing rate limits on password reset requests.
    
    Implements user-based (3 requests/hour) and IP-based (10 requests/hour)
    rate limiting with sliding window tracking using in-memory cache.
    
    Requirements:
    - 3.1: User-based rate limiting (3 requests per hour)
    - 3.3: IP-based rate limiting (10 requests per hour)
    - 3.4: Rate limit window expiration
    """
    
    def __init__(self):
        """Initialize the rate limit service with in-memory cache."""
        # In-memory cache: key -> list of timestamps
        self._cache: Dict[str, List[datetime]] = {}
        self._lock = asyncio.Lock()
    
    async def is_user_rate_limited(self, email: str) -> bool:
        """
        Check if a user has exceeded rate limits.
        
        Uses sliding window to track attempts within the last hour.
        
        Args:
            email: User's email address
            
        Returns:
            True if rate limit exceeded (>= 3 requests in last hour)
        """
        key = f"{RATE_LIMIT_USER_KEY_PREFIX}{email}"
        return await self._is_rate_limited(
            key,
            USER_RATE_LIMIT_REQUESTS,
            USER_RATE_LIMIT_WINDOW_HOURS
        )
    
    async def is_ip_rate_limited(self, ip_address: str) -> bool:
        """
        Check if an IP address has exceeded rate limits.
        
        Uses sliding window to track attempts within the last hour.
        
        Args:
            ip_address: The IP address
            
        Returns:
            True if rate limit exceeded (>= 10 requests in last hour)
        """
        key = f"{RATE_LIMIT_IP_KEY_PREFIX}{ip_address}"
        return await self._is_rate_limited(
            key,
            IP_RATE_LIMIT_REQUESTS,
            IP_RATE_LIMIT_WINDOW_HOURS
        )
    
    async def record_attempt(self, email: str, ip_address: str) -> None:
        """
        Record a password reset attempt for both user and IP.
        
        Adds current timestamp to the sliding window for both email and IP.
        
        Args:
            email: User's email address
            ip_address: Request origin IP
        """
        now = datetime.now(timezone.utc)
        
        async with self._lock:
            # Record user attempt
            user_key = f"{RATE_LIMIT_USER_KEY_PREFIX}{email}"
            if user_key not in self._cache:
                self._cache[user_key] = []
            self._cache[user_key].append(now)
            
            # Record IP attempt
            ip_key = f"{RATE_LIMIT_IP_KEY_PREFIX}{ip_address}"
            if ip_key not in self._cache:
                self._cache[ip_key] = []
            self._cache[ip_key].append(now)
    
    async def _is_rate_limited(
        self,
        key: str,
        max_requests: int,
        window_hours: int
    ) -> bool:
        """
        Check if a key has exceeded rate limits using sliding window.
        
        Args:
            key: Cache key (user or IP)
            max_requests: Maximum allowed requests in window
            window_hours: Time window in hours
            
        Returns:
            True if rate limit exceeded
        """
        async with self._lock:
            if key not in self._cache:
                return False
            
            # Calculate window start time
            now = datetime.now(timezone.utc)
            window_start = now - timedelta(hours=window_hours)
            
            # Filter attempts within the sliding window
            attempts = self._cache[key]
            valid_attempts = [ts for ts in attempts if ts > window_start]
            
            # Update cache with only valid attempts
            self._cache[key] = valid_attempts
            
            # Check if rate limit exceeded
            return len(valid_attempts) >= max_requests
    
    async def clear_cache(self) -> None:
        """
        Clear all rate limit data from cache.
        
        Useful for testing and maintenance.
        """
        async with self._lock:
            self._cache.clear()
