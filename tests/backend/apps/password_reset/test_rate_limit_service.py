"""
Unit tests for RateLimitService.

Tests cover:
- User-based rate limiting (3 requests per hour)
- IP-based rate limiting (10 requests per hour)
- Sliding window behavior
- Rate limit window expiration
"""
import pytest
from datetime import datetime, timedelta, timezone
from ..services.rate_limit_service import RateLimitService
from ..constants import (
    USER_RATE_LIMIT_REQUESTS,
    IP_RATE_LIMIT_REQUESTS,
)


@pytest.fixture
def rate_limit_service():
    """Create a fresh RateLimitService instance for each test."""
    return RateLimitService()


class TestRateLimitService:
    """Test suite for RateLimitService."""
    
    @pytest.mark.asyncio
    async def test_first_request_not_rate_limited(self, rate_limit_service):
        """Test that first request is not rate limited."""
        email = "user@example.com"
        ip = "192.168.1.1"
        
        # First request should not be rate limited
        assert await rate_limit_service.is_user_rate_limited(email) is False
        assert await rate_limit_service.is_ip_rate_limited(ip) is False
    
    @pytest.mark.asyncio
    async def test_user_rate_limit_within_limit(self, rate_limit_service):
        """Test that requests within user rate limit are allowed."""
        email = "user@example.com"
        ip = "192.168.1.1"
        
        # Make 3 requests (at the limit)
        for _ in range(USER_RATE_LIMIT_REQUESTS):
            await rate_limit_service.record_attempt(email, ip)
        
        # Should be rate limited after 3 requests
        assert await rate_limit_service.is_user_rate_limited(email) is True
    
    @pytest.mark.asyncio
    async def test_user_rate_limit_exceeded(self, rate_limit_service):
        """Test that user is rate limited after exceeding limit."""
        email = "user@example.com"
        ip = "192.168.1.1"
        
        # Make 4 requests (exceeding the limit of 3)
        for _ in range(USER_RATE_LIMIT_REQUESTS + 1):
            await rate_limit_service.record_attempt(email, ip)
        
        # Should be rate limited
        assert await rate_limit_service.is_user_rate_limited(email) is True
    
    @pytest.mark.asyncio
    async def test_ip_rate_limit_within_limit(self, rate_limit_service):
        """Test that requests within IP rate limit are allowed."""
        email = "user@example.com"
        ip = "192.168.1.1"
        
        # Make 10 requests (at the limit)
        for _ in range(IP_RATE_LIMIT_REQUESTS):
            await rate_limit_service.record_attempt(email, ip)
        
        # Should be rate limited after 10 requests
        assert await rate_limit_service.is_ip_rate_limited(ip) is True
    
    @pytest.mark.asyncio
    async def test_ip_rate_limit_exceeded(self, rate_limit_service):
        """Test that IP is rate limited after exceeding limit."""
        email = "user@example.com"
        ip = "192.168.1.1"
        
        # Make 11 requests (exceeding the limit of 10)
        for _ in range(IP_RATE_LIMIT_REQUESTS + 1):
            await rate_limit_service.record_attempt(email, ip)
        
        # Should be rate limited
        assert await rate_limit_service.is_ip_rate_limited(ip) is True
    
    @pytest.mark.asyncio
    async def test_different_users_independent_limits(self, rate_limit_service):
        """Test that different users have independent rate limits."""
        email1 = "user1@example.com"
        email2 = "user2@example.com"
        ip = "192.168.1.1"
        
        # User 1 makes 3 requests
        for _ in range(USER_RATE_LIMIT_REQUESTS):
            await rate_limit_service.record_attempt(email1, ip)
        
        # User 1 should be rate limited
        assert await rate_limit_service.is_user_rate_limited(email1) is True
        
        # User 2 should not be rate limited
        assert await rate_limit_service.is_user_rate_limited(email2) is False
    
    @pytest.mark.asyncio
    async def test_different_ips_independent_limits(self, rate_limit_service):
        """Test that different IPs have independent rate limits."""
        email = "user@example.com"
        ip1 = "192.168.1.1"
        ip2 = "192.168.1.2"
        
        # IP 1 makes 10 requests
        for _ in range(IP_RATE_LIMIT_REQUESTS):
            await rate_limit_service.record_attempt(email, ip1)
        
        # IP 1 should be rate limited
        assert await rate_limit_service.is_ip_rate_limited(ip1) is True
        
        # IP 2 should not be rate limited
        assert await rate_limit_service.is_ip_rate_limited(ip2) is False
    
    @pytest.mark.asyncio
    async def test_sliding_window_removes_old_attempts(self, rate_limit_service):
        """Test that old attempts outside the window are removed."""
        email = "user@example.com"
        ip = "192.168.1.1"
        
        # Manually add old attempts (more than 1 hour ago)
        old_time = datetime.now(timezone.utc) - timedelta(hours=2)
        user_key = f"rate_limit:user:{email}"
        rate_limit_service._cache[user_key] = [old_time] * 5
        
        # Old attempts should not count
        assert await rate_limit_service.is_user_rate_limited(email) is False
        
        # Make 3 new requests
        for _ in range(USER_RATE_LIMIT_REQUESTS):
            await rate_limit_service.record_attempt(email, ip)
        
        # Should be rate limited based on new requests only
        assert await rate_limit_service.is_user_rate_limited(email) is True
    
    @pytest.mark.asyncio
    async def test_rate_limit_window_expiration(self, rate_limit_service):
        """Test that rate limits expire after the time window."""
        email = "user@example.com"
        ip = "192.168.1.1"
        
        # Add attempts that are just outside the window
        almost_expired_time = datetime.now(timezone.utc) - timedelta(hours=1, minutes=1)
        user_key = f"rate_limit:user:{email}"
        rate_limit_service._cache[user_key] = [almost_expired_time] * 3
        
        # Old attempts should not count (outside 1-hour window)
        assert await rate_limit_service.is_user_rate_limited(email) is False
    
    @pytest.mark.asyncio
    async def test_record_attempt_updates_both_user_and_ip(self, rate_limit_service):
        """Test that record_attempt updates both user and IP caches."""
        email = "user@example.com"
        ip = "192.168.1.1"
        
        await rate_limit_service.record_attempt(email, ip)
        
        # Check that both caches have entries
        user_key = f"rate_limit:user:{email}"
        ip_key = f"rate_limit:ip:{ip}"
        
        assert user_key in rate_limit_service._cache
        assert ip_key in rate_limit_service._cache
        assert len(rate_limit_service._cache[user_key]) == 1
        assert len(rate_limit_service._cache[ip_key]) == 1
    
    @pytest.mark.asyncio
    async def test_clear_cache(self, rate_limit_service):
        """Test that clear_cache removes all rate limit data."""
        email = "user@example.com"
        ip = "192.168.1.1"
        
        # Add some attempts
        for _ in range(3):
            await rate_limit_service.record_attempt(email, ip)
        
        # Clear cache
        await rate_limit_service.clear_cache()
        
        # Cache should be empty
        assert len(rate_limit_service._cache) == 0
        
        # Should not be rate limited after clearing
        assert await rate_limit_service.is_user_rate_limited(email) is False
        assert await rate_limit_service.is_ip_rate_limited(ip) is False
    
    @pytest.mark.asyncio
    async def test_concurrent_requests_thread_safe(self, rate_limit_service):
        """Test that concurrent requests are handled safely."""
        import asyncio
        
        email = "user@example.com"
        ip = "192.168.1.1"
        
        # Make 5 concurrent requests
        tasks = [
            rate_limit_service.record_attempt(email, ip)
            for _ in range(5)
        ]
        await asyncio.gather(*tasks)
        
        # Check that all 5 attempts were recorded
        user_key = f"rate_limit:user:{email}"
        assert len(rate_limit_service._cache[user_key]) == 5
    
    @pytest.mark.asyncio
    async def test_user_at_exact_limit_boundary(self, rate_limit_service):
        """Test behavior at exact rate limit boundary."""
        email = "user@example.com"
        ip = "192.168.1.1"
        
        # Make exactly 2 requests (one below limit)
        for _ in range(USER_RATE_LIMIT_REQUESTS - 1):
            await rate_limit_service.record_attempt(email, ip)
        
        # Should not be rate limited yet
        assert await rate_limit_service.is_user_rate_limited(email) is False
        
        # Make one more request to reach the limit
        await rate_limit_service.record_attempt(email, ip)
        
        # Should now be rate limited
        assert await rate_limit_service.is_user_rate_limited(email) is True
    
    @pytest.mark.asyncio
    async def test_ip_at_exact_limit_boundary(self, rate_limit_service):
        """Test IP rate limit at exact boundary."""
        email = "user@example.com"
        ip = "192.168.1.1"
        
        # Make exactly 9 requests (one below limit)
        for _ in range(IP_RATE_LIMIT_REQUESTS - 1):
            await rate_limit_service.record_attempt(email, ip)
        
        # Should not be rate limited yet
        assert await rate_limit_service.is_ip_rate_limited(ip) is False
        
        # Make one more request to reach the limit
        await rate_limit_service.record_attempt(email, ip)
        
        # Should now be rate limited
        assert await rate_limit_service.is_ip_rate_limited(ip) is True
    
    @pytest.mark.asyncio
    async def test_mixed_old_and_new_attempts(self, rate_limit_service):
        """Test sliding window with mix of old and new attempts."""
        email = "user@example.com"
        ip = "192.168.1.1"
        
        # Add 2 old attempts (outside window)
        old_time = datetime.now(timezone.utc) - timedelta(hours=2)
        user_key = f"rate_limit:user:{email}"
        rate_limit_service._cache[user_key] = [old_time, old_time]
        
        # Add 2 new attempts
        for _ in range(2):
            await rate_limit_service.record_attempt(email, ip)
        
        # Should not be rate limited (only 2 valid attempts)
        assert await rate_limit_service.is_user_rate_limited(email) is False
        
        # Add one more to reach limit
        await rate_limit_service.record_attempt(email, ip)
        
        # Should now be rate limited
        assert await rate_limit_service.is_user_rate_limited(email) is True
