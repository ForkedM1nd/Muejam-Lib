"""
Unit tests for Mobile Rate Limiter.

Tests the MobileRateLimiter to ensure it properly applies client-type-specific
rate limits for mobile and web clients.

Requirements: 8.1, 8.2
"""

import os
import sys
import django
from pathlib import Path

# Configure Django settings before importing Django modules
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent.parent / 'apps' / 'backend'
sys.path.insert(0, str(backend_dir))

# Setup Django
django.setup()

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from infrastructure.rate_limiter import MobileRateLimiter
from infrastructure.models import RateLimitResult


class TestMobileRateLimiter:
    """Test MobileRateLimiter functionality."""
    
    @pytest.fixture
    def rate_limiter(self):
        """Create MobileRateLimiter instance."""
        # Mock Redis to avoid actual Redis dependency in tests
        with patch('infrastructure.rate_limiter.redis.from_url') as mock_redis:
            mock_client = Mock()
            mock_client.ping.return_value = True
            mock_redis.return_value = mock_client
            
            limiter = MobileRateLimiter()
            limiter.redis_available = False  # Disable Redis for unit tests
            return limiter
    
    def test_get_rate_limit_web(self, rate_limiter):
        """Test that web clients get 100 requests/minute limit."""
        limit = rate_limiter.get_rate_limit('web')
        assert limit == 100
    
    def test_get_rate_limit_mobile_ios(self, rate_limiter):
        """Test that iOS mobile clients get 150 requests/minute limit."""
        limit = rate_limiter.get_rate_limit('mobile-ios')
        assert limit == 150
    
    def test_get_rate_limit_mobile_android(self, rate_limiter):
        """Test that Android mobile clients get 150 requests/minute limit."""
        limit = rate_limiter.get_rate_limit('mobile-android')
        assert limit == 150
    
    def test_get_rate_limit_unknown_client_type(self, rate_limiter):
        """Test that unknown client types get default limit."""
        limit = rate_limiter.get_rate_limit('unknown-client')
        assert limit == 100  # Default limit
    
    def test_check_user_limit_web_client(self, rate_limiter):
        """Test checking user limit for web client."""
        result = rate_limiter.check_user_limit('user-123', 'web')
        
        assert result.allowed is True
        assert result.limit == 100
        assert result.remaining == 100
        assert isinstance(result.reset_at, datetime)
    
    def test_check_user_limit_mobile_ios_client(self, rate_limiter):
        """Test checking user limit for iOS mobile client."""
        result = rate_limiter.check_user_limit('user-123', 'mobile-ios')
        
        assert result.allowed is True
        assert result.limit == 150
        assert result.remaining == 150
        assert isinstance(result.reset_at, datetime)
    
    def test_check_user_limit_mobile_android_client(self, rate_limiter):
        """Test checking user limit for Android mobile client."""
        result = rate_limiter.check_user_limit('user-123', 'mobile-android')
        
        assert result.allowed is True
        assert result.limit == 150
        assert result.remaining == 150
        assert isinstance(result.reset_at, datetime)
    
    def test_allow_request_with_client_type(self, rate_limiter):
        """Test allow_request with client type parameter."""
        # Web client
        allowed = rate_limiter.allow_request('user-123', is_admin=False, client_type='web')
        assert allowed is True
        
        # Mobile iOS client
        allowed = rate_limiter.allow_request('user-456', is_admin=False, client_type='mobile-ios')
        assert allowed is True
        
        # Mobile Android client
        allowed = rate_limiter.allow_request('user-789', is_admin=False, client_type='mobile-android')
        assert allowed is True
    
    def test_allow_request_admin_bypass(self, rate_limiter):
        """Test that admin users bypass rate limits regardless of client type."""
        # Admin web client
        allowed = rate_limiter.allow_request('admin-123', is_admin=True, client_type='web')
        assert allowed is True
        
        # Admin mobile client
        allowed = rate_limiter.allow_request('admin-456', is_admin=True, client_type='mobile-ios')
        assert allowed is True
    
    def test_get_limit_info_with_client_type(self, rate_limiter):
        """Test get_limit_info with client type parameter."""
        # Web client
        info = rate_limiter.get_limit_info('user-123', 'web')
        assert info.limit == 100
        assert info.user_id == 'user-123'
        
        # Mobile iOS client
        info = rate_limiter.get_limit_info('user-456', 'mobile-ios')
        assert info.limit == 150
        assert info.user_id == 'user-456'
        
        # Mobile Android client
        info = rate_limiter.get_limit_info('user-789', 'mobile-android')
        assert info.limit == 150
        assert info.user_id == 'user-789'
    
    def test_rate_limits_configuration(self, rate_limiter):
        """Test that rate limits are configured correctly."""
        assert rate_limiter.RATE_LIMITS['web'] == 100
        assert rate_limiter.RATE_LIMITS['mobile-ios'] == 150
        assert rate_limiter.RATE_LIMITS['mobile-android'] == 150
        assert rate_limiter.RATE_LIMITS['default'] == 100


class TestMobileRateLimiterWithRedis:
    """Test MobileRateLimiter with Redis integration."""
    
    @pytest.fixture
    def rate_limiter_with_redis(self):
        """Create MobileRateLimiter with mocked Redis."""
        with patch('infrastructure.rate_limiter.redis.from_url') as mock_redis:
            mock_client = Mock()
            mock_client.ping.return_value = True
            mock_redis.return_value = mock_client
            
            limiter = MobileRateLimiter()
            limiter.redis_client = mock_client
            limiter.redis_available = True
            return limiter
    
    def test_check_user_limit_with_redis_web(self, rate_limiter_with_redis):
        """Test check_user_limit with Redis for web client."""
        limiter = rate_limiter_with_redis
        
        # Mock Redis responses
        limiter.redis_client.zremrangebyscore.return_value = None
        limiter.redis_client.zcard.return_value = 50  # 50 requests made
        limiter.redis_client.zadd.return_value = 1
        limiter.redis_client.expire.return_value = True
        
        result = limiter.check_user_limit('user-123', 'web')
        
        assert result.allowed is True
        assert result.limit == 100
        assert result.remaining == 49  # 100 - 50 - 1
        
        # Verify Redis key includes client type
        limiter.redis_client.zremrangebyscore.assert_called_once()
        key_used = limiter.redis_client.zremrangebyscore.call_args[0][0]
        assert 'user-123:web' in key_used
    
    def test_check_user_limit_with_redis_mobile(self, rate_limiter_with_redis):
        """Test check_user_limit with Redis for mobile client."""
        limiter = rate_limiter_with_redis
        
        # Mock Redis responses
        limiter.redis_client.zremrangebyscore.return_value = None
        limiter.redis_client.zcard.return_value = 100  # 100 requests made
        limiter.redis_client.zadd.return_value = 1
        limiter.redis_client.expire.return_value = True
        
        result = limiter.check_user_limit('user-456', 'mobile-ios')
        
        assert result.allowed is True
        assert result.limit == 150
        assert result.remaining == 49  # 150 - 100 - 1
        
        # Verify Redis key includes client type
        limiter.redis_client.zremrangebyscore.assert_called_once()
        key_used = limiter.redis_client.zremrangebyscore.call_args[0][0]
        assert 'user-456:mobile-ios' in key_used
    
    def test_check_user_limit_exceeded_web(self, rate_limiter_with_redis):
        """Test that web client is blocked at 100 requests."""
        limiter = rate_limiter_with_redis
        
        # Mock Redis responses - 100 requests already made
        limiter.redis_client.zremrangebyscore.return_value = None
        limiter.redis_client.zcard.return_value = 100
        limiter.redis_client.zrange.return_value = [(b'req1', 1234567890.0)]
        
        result = limiter.check_user_limit('user-123', 'web')
        
        assert result.allowed is False
        assert result.limit == 100
        assert result.remaining == 0
        assert result.retry_after > 0
    
    def test_check_user_limit_exceeded_mobile(self, rate_limiter_with_redis):
        """Test that mobile client is blocked at 150 requests."""
        limiter = rate_limiter_with_redis
        
        # Mock Redis responses - 150 requests already made
        limiter.redis_client.zremrangebyscore.return_value = None
        limiter.redis_client.zcard.return_value = 150
        limiter.redis_client.zrange.return_value = [(b'req1', 1234567890.0)]
        
        result = limiter.check_user_limit('user-456', 'mobile-ios')
        
        assert result.allowed is False
        assert result.limit == 150
        assert result.remaining == 0
        assert result.retry_after > 0
    
    def test_different_limits_for_same_user(self, rate_limiter_with_redis):
        """Test that same user gets different limits for different client types."""
        limiter = rate_limiter_with_redis
        
        # Mock Redis responses
        limiter.redis_client.zremrangebyscore.return_value = None
        limiter.redis_client.zcard.return_value = 0
        limiter.redis_client.zadd.return_value = 1
        limiter.redis_client.expire.return_value = True
        
        # Check web limit
        result_web = limiter.check_user_limit('user-123', 'web')
        assert result_web.limit == 100
        
        # Check mobile limit
        result_mobile = limiter.check_user_limit('user-123', 'mobile-ios')
        assert result_mobile.limit == 150
        
        # Verify different Redis keys were used
        calls = limiter.redis_client.zremrangebyscore.call_args_list
        assert len(calls) == 2
        assert 'user-123:web' in calls[0][0][0]
        assert 'user-123:mobile-ios' in calls[1][0][0]


class TestMobileRateLimiterMiddlewareIntegration:
    """Test MobileRateLimiter integration with middleware."""
    
    def test_middleware_uses_mobile_rate_limiter(self):
        """Test that middleware uses MobileRateLimiter."""
        from infrastructure.rate_limit_middleware import RateLimitMiddleware
        
        get_response = Mock()
        middleware = RateLimitMiddleware(get_response)
        
        # Verify middleware uses MobileRateLimiter
        assert isinstance(middleware.rate_limiter, MobileRateLimiter)
    
    def test_middleware_passes_client_type(self):
        """Test that middleware passes client type to rate limiter."""
        from infrastructure.rate_limit_middleware import RateLimitMiddleware
        from django.test import RequestFactory
        from django.http import HttpResponse
        
        get_response = Mock(return_value=HttpResponse())
        middleware = RateLimitMiddleware(get_response)
        
        factory = RequestFactory()
        request = factory.get('/api/test/')
        request.user_profile = Mock()
        request.user_profile.id = 'user-123'
        request.client_type = 'mobile-ios'  # Set by ClientTypeMiddleware
        
        # Mock rate limiter methods
        with patch.object(middleware.rate_limiter, 'allow_request', return_value=True) as mock_allow:
            mock_result = RateLimitResult(
                allowed=True,
                limit=150,
                remaining=100,
                reset_at=datetime.now() + timedelta(seconds=60)
            )
            with patch.object(middleware.rate_limiter, 'check_user_limit', return_value=mock_result):
                # Mock admin check to avoid database access
                with patch.object(middleware, '_is_admin_user', return_value=False):
                    response = middleware(request)
                    
                    # Verify allow_request was called with client_type
                    mock_allow.assert_called_once()
                    call_args = mock_allow.call_args
                    assert call_args[0][2] == 'mobile-ios'  # client_type parameter


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
