"""
Unit tests for RateLimiter class.

Tests cover:
- Per-user rate limiting
- Global rate limiting
- Admin bypass functionality
- Sliding window algorithm behavior
- Redis failure handling (fail-open)
"""

import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

import pytest
from redis.exceptions import RedisError

from infrastructure.rate_limiter import RateLimiter
from infrastructure.models import RateLimitResult, LimitInfo


class TestRateLimiter:
    """Test suite for RateLimiter class."""
    
    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        with patch('infrastructure.rate_limiter.redis') as mock:
            redis_client = MagicMock()
            redis_client.ping.return_value = True
            redis_client.zremrangebyscore.return_value = None
            redis_client.zcard.return_value = 0
            redis_client.zadd.return_value = 1
            redis_client.expire.return_value = True
            redis_client.zrange.return_value = []
            
            mock.from_url.return_value = redis_client
            yield redis_client
    
    @pytest.fixture
    def rate_limiter(self, mock_redis):
        """Create a RateLimiter instance with mocked Redis."""
        return RateLimiter()
    
    def test_initialization_with_redis(self, mock_redis):
        """Test RateLimiter initializes correctly with Redis."""
        limiter = RateLimiter()
        
        assert limiter.redis_available is True
        assert limiter.PER_USER_LIMIT == 100
        assert limiter.GLOBAL_LIMIT == 10000
        assert limiter.WINDOW_SIZE == 60
    
    def test_initialization_without_redis(self):
        """Test RateLimiter handles Redis connection failure gracefully."""
        with patch('infrastructure.rate_limiter.redis') as mock:
            mock.from_url.side_effect = Exception("Connection failed")
            
            limiter = RateLimiter()
            
            assert limiter.redis_available is False
            assert limiter.redis_client is None
    
    def test_check_user_limit_allows_first_request(self, rate_limiter, mock_redis):
        """Test that first request from user is allowed."""
        mock_redis.zcard.return_value = 0
        
        result = rate_limiter.check_user_limit("user123")
        
        assert result.allowed is True
        assert result.limit == 100
        assert result.remaining == 99
        assert isinstance(result.reset_at, datetime)
        
        # Verify Redis operations
        mock_redis.zremrangebyscore.assert_called_once()
        mock_redis.zcard.assert_called_once()
        mock_redis.zadd.assert_called_once()
    
    def test_check_user_limit_blocks_at_limit(self, rate_limiter, mock_redis):
        """Test that user is blocked when limit is reached."""
        # Simulate 100 requests already made
        mock_redis.zcard.return_value = 100
        mock_redis.zrange.return_value = [(f"req1", time.time() - 30)]
        
        result = rate_limiter.check_user_limit("user123")
        
        assert result.allowed is False
        assert result.limit == 100
        assert result.remaining == 0
        assert result.retry_after is not None
        assert result.retry_after > 0
    
    def test_check_user_limit_tracks_remaining(self, rate_limiter, mock_redis):
        """Test that remaining count decreases correctly."""
        # Simulate 50 requests already made
        mock_redis.zcard.return_value = 50
        
        result = rate_limiter.check_user_limit("user123")
        
        assert result.allowed is True
        assert result.remaining == 49  # 100 - 50 - 1
    
    def test_check_user_limit_sliding_window(self, rate_limiter, mock_redis):
        """Test that old requests are removed from window."""
        current_time = time.time()
        window_start = current_time - 60
        
        rate_limiter.check_user_limit("user123")
        
        # Verify old entries are removed
        call_args = mock_redis.zremrangebyscore.call_args
        assert call_args[0][0] == "ratelimit:user:user123"
        assert call_args[0][1] == 0
        assert abs(call_args[0][2] - window_start) < 1  # Allow 1 second tolerance
    
    def test_check_global_limit_allows_first_request(self, rate_limiter, mock_redis):
        """Test that first global request is allowed."""
        mock_redis.zcard.return_value = 0
        
        result = rate_limiter.check_global_limit()
        
        assert result.allowed is True
        assert result.limit == 10000
        assert result.remaining == 9999
    
    def test_check_global_limit_blocks_at_limit(self, rate_limiter, mock_redis):
        """Test that global limit blocks when reached."""
        # Simulate 10000 requests already made
        mock_redis.zcard.return_value = 10000
        mock_redis.zrange.return_value = [(f"req1", time.time() - 30)]
        
        result = rate_limiter.check_global_limit()
        
        assert result.allowed is False
        assert result.limit == 10000
        assert result.remaining == 0
        assert result.retry_after is not None
    
    def test_allow_request_checks_both_limits(self, rate_limiter, mock_redis):
        """Test that allow_request checks both user and global limits."""
        mock_redis.zcard.return_value = 0
        
        allowed = rate_limiter.allow_request("user123", is_admin=False)
        
        assert allowed is True
        # Should check both user and global limits
        assert mock_redis.zcard.call_count == 2
    
    def test_allow_request_admin_bypass(self, rate_limiter, mock_redis):
        """Test that admin users bypass rate limits."""
        # Even if limits would be exceeded
        mock_redis.zcard.return_value = 10000
        
        allowed = rate_limiter.allow_request("admin_user", is_admin=True)
        
        assert allowed is True
        # Should not check limits for admin
        mock_redis.zcard.assert_not_called()
    
    def test_allow_request_blocked_by_user_limit(self, rate_limiter, mock_redis):
        """Test that request is blocked if user limit exceeded."""
        # First call (user limit check) returns 100, second call not reached
        mock_redis.zcard.side_effect = [100]
        mock_redis.zrange.return_value = [(f"req1", time.time() - 30)]
        
        allowed = rate_limiter.allow_request("user123", is_admin=False)
        
        assert allowed is False
    
    def test_allow_request_blocked_by_global_limit(self, rate_limiter, mock_redis):
        """Test that request is blocked if global limit exceeded."""
        # First call (user limit) returns 50, second call (global) returns 10000
        mock_redis.zcard.side_effect = [50, 10000]
        mock_redis.zrange.return_value = [(f"req1", time.time() - 30)]
        
        allowed = rate_limiter.allow_request("user123", is_admin=False)
        
        assert allowed is False
    
    def test_get_limit_info(self, rate_limiter, mock_redis):
        """Test getting current limit info for a user."""
        mock_redis.zcard.return_value = 42
        
        info = rate_limiter.get_limit_info("user123")
        
        assert info.user_id == "user123"
        assert info.requests_made == 42
        assert info.limit == 100
        assert isinstance(info.window_start, datetime)
        assert isinstance(info.window_end, datetime)
        assert info.window_end > info.window_start
    
    def test_redis_failure_fails_open(self, rate_limiter, mock_redis):
        """Test that Redis failures result in allowing requests (fail-open)."""
        mock_redis.zremrangebyscore.side_effect = RedisError("Connection lost")
        
        result = rate_limiter.check_user_limit("user123")
        
        # Should allow request despite Redis error
        assert result.allowed is True
    
    def test_no_redis_allows_all_requests(self):
        """Test that without Redis, all requests are allowed."""
        with patch('infrastructure.rate_limiter.redis') as mock:
            mock.from_url.side_effect = Exception("No Redis")
            
            limiter = RateLimiter()
            
            # Should allow requests
            result = limiter.check_user_limit("user123")
            assert result.allowed is True
            
            result = limiter.check_global_limit()
            assert result.allowed is True
            
            allowed = limiter.allow_request("user123")
            assert allowed is True
    
    def test_key_expiration_set(self, rate_limiter, mock_redis):
        """Test that Redis keys have expiration set."""
        mock_redis.zcard.return_value = 0
        
        rate_limiter.check_user_limit("user123")
        
        # Verify expiration is set (2x window size)
        mock_redis.expire.assert_called()
        call_args = mock_redis.expire.call_args
        assert call_args[0][1] == 120  # 2 * 60 seconds
    
    def test_different_users_independent_limits(self, rate_limiter, mock_redis):
        """Test that different users have independent rate limits."""
        mock_redis.zcard.return_value = 0
        
        rate_limiter.check_user_limit("user1")
        rate_limiter.check_user_limit("user2")
        
        # Verify different keys are used
        calls = mock_redis.zremrangebyscore.call_args_list
        assert calls[0][0][0] == "ratelimit:user:user1"
        assert calls[1][0][0] == "ratelimit:user:user2"
    
    def test_retry_after_calculation(self, rate_limiter, mock_redis):
        """Test that retry_after is calculated correctly."""
        current_time = time.time()
        oldest_timestamp = current_time - 30  # 30 seconds ago
        
        mock_redis.zcard.return_value = 100
        mock_redis.zrange.return_value = [(f"req1", oldest_timestamp)]
        
        result = rate_limiter.check_user_limit("user123")
        
        assert result.allowed is False
        # Should retry after ~30 seconds (when oldest request expires)
        assert 25 <= result.retry_after <= 35
    
    def test_reset_at_calculation(self, rate_limiter, mock_redis):
        """Test that reset_at is calculated correctly."""
        mock_redis.zcard.return_value = 0
        
        before = datetime.now()
        result = rate_limiter.check_user_limit("user123")
        after = datetime.now()
        
        # reset_at should be approximately 60 seconds from now
        expected_reset = before + timedelta(seconds=60)
        assert result.reset_at >= expected_reset - timedelta(seconds=2)
        assert result.reset_at <= after + timedelta(seconds=62)
