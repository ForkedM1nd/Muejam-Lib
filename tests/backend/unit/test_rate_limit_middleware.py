"""
Unit tests for Rate Limit Middleware.

Tests the RateLimitMiddleware to ensure it properly enforces rate limits
on incoming requests and adds appropriate headers to responses.
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
from unittest.mock import Mock, patch, MagicMock
from django.test import RequestFactory
from django.http import HttpResponse
from datetime import datetime, timedelta

from infrastructure.rate_limit_middleware import RateLimitMiddleware
from infrastructure.models import RateLimitResult


class TestRateLimitMiddleware:
    """Test RateLimitMiddleware functionality."""
    
    @pytest.fixture
    def middleware(self):
        """Create middleware instance."""
        get_response = Mock(return_value=HttpResponse())
        return RateLimitMiddleware(get_response)
    
    @pytest.fixture
    def mock_request(self):
        """Create mock request with authenticated user."""
        factory = RequestFactory()
        request = factory.get('/api/test/')
        
        # Mock user_profile (set by ClerkAuthMiddleware)
        request.user_profile = Mock()
        request.user_profile.id = 'user-123'
        
        return request
    
    @pytest.fixture
    def anonymous_request(self):
        """Create mock request for anonymous user."""
        factory = RequestFactory()
        request = factory.get('/api/test/')
        request.user_profile = None
        return request
    
    def test_skip_health_check_endpoints(self, middleware):
        """Test that health check endpoints skip rate limiting."""
        factory = RequestFactory()
        request = factory.get('/health')
        
        # Should not check rate limits
        with patch.object(middleware.rate_limiter, 'allow_request') as mock_allow:
            response = middleware(request)
            
            # allow_request should not be called
            mock_allow.assert_not_called()
            
            # Should return normal response
            assert response.status_code == 200
    
    def test_skip_metrics_endpoints(self, middleware):
        """Test that metrics endpoints skip rate limiting."""
        factory = RequestFactory()
        request = factory.get('/metrics')
        
        # Should not check rate limits
        with patch.object(middleware.rate_limiter, 'allow_request') as mock_allow:
            response = middleware(request)
            
            # allow_request should not be called
            mock_allow.assert_not_called()
            
            # Should return normal response
            assert response.status_code == 200
    
    def test_authenticated_user_identifier(self, middleware, mock_request):
        """Test that authenticated users are identified by user_profile.id."""
        user_id = middleware._get_user_identifier(mock_request)
        assert user_id == 'user:user-123'
    
    def test_anonymous_user_identifier(self, middleware, anonymous_request):
        """Test that anonymous users are identified by IP address."""
        # Set IP address in request
        anonymous_request.META['REMOTE_ADDR'] = '192.168.1.100'
        
        user_id = middleware._get_user_identifier(anonymous_request)
        assert user_id == 'ip:192.168.1.100'
    
    def test_get_client_ip_from_remote_addr(self, middleware):
        """Test getting client IP from REMOTE_ADDR."""
        factory = RequestFactory()
        request = factory.get('/api/test/')
        request.META['REMOTE_ADDR'] = '10.0.0.1'
        
        ip = middleware._get_client_ip(request)
        assert ip == '10.0.0.1'
    
    def test_get_client_ip_from_x_forwarded_for(self, middleware):
        """Test getting client IP from X-Forwarded-For header."""
        factory = RequestFactory()
        request = factory.get('/api/test/')
        request.META['HTTP_X_FORWARDED_FOR'] = '203.0.113.1, 198.51.100.1'
        request.META['REMOTE_ADDR'] = '10.0.0.1'
        
        ip = middleware._get_client_ip(request)
        # Should use first IP from X-Forwarded-For
        assert ip == '203.0.113.1'
    
    def test_allow_request_within_limit(self, middleware, mock_request):
        """Test that requests within rate limit are allowed."""
        mock_result = RateLimitResult(
            allowed=True,
            limit=100,
            remaining=50,
            reset_at=datetime.now() + timedelta(seconds=60)
        )
        
        with patch.object(middleware.rate_limiter, 'allow_request', return_value=True):
            with patch.object(middleware.rate_limiter, 'check_user_limit', return_value=mock_result):
                response = middleware(mock_request)
                
                # Should return normal response
                assert response.status_code == 200
                
                # Should have rate limit headers
                assert 'X-RateLimit-Limit' in response
                assert 'X-RateLimit-Remaining' in response
                assert 'X-RateLimit-Reset' in response
                
                # Verify header values
                assert response['X-RateLimit-Limit'] == '100'
                assert response['X-RateLimit-Remaining'] == '50'
    
    def test_block_request_over_limit(self, middleware, mock_request):
        """Test that requests over rate limit are blocked with 429."""
        mock_result = RateLimitResult(
            allowed=False,
            limit=100,
            remaining=0,
            reset_at=datetime.now() + timedelta(seconds=60),
            retry_after=60
        )
        
        with patch.object(middleware.rate_limiter, 'allow_request', return_value=False):
            with patch.object(middleware.rate_limiter, 'check_user_limit', return_value=mock_result):
                response = middleware(mock_request)
                
                # Should return 429 Too Many Requests
                assert response.status_code == 429
                
                # Should have rate limit headers
                assert 'X-RateLimit-Limit' in response
                assert 'X-RateLimit-Remaining' in response
                assert 'X-RateLimit-Reset' in response
                assert 'Retry-After' in response
                
                # Verify header values
                assert response['X-RateLimit-Limit'] == '100'
                assert response['X-RateLimit-Remaining'] == '0'
                assert response['Retry-After'] == '60'
                
                # Verify response body
                import json
                data = json.loads(response.content)
                assert data['error'] == 'Rate limit exceeded'
                assert data['limit'] == 100
                assert data['retry_after'] == 60
    
    def test_admin_bypass(self, middleware, mock_request):
        """Test that admin users bypass rate limits."""
        # Mock Django database cursor to return moderator role
        from unittest.mock import MagicMock
        
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = [1]  # Count > 0 means admin
        
        with patch('django.db.connection') as mock_connection:
            mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
            
            # Check admin status
            is_admin = middleware._is_admin_user(mock_request)
            assert is_admin is True
            
            # Verify cursor was called correctly
            mock_cursor.execute.assert_called_once()
    
    def test_non_admin_user(self, middleware, mock_request):
        """Test that non-admin users are not identified as admin."""
        # Mock Django database cursor to return no moderator role
        from unittest.mock import MagicMock
        
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = [0]  # Count = 0 means not admin
        
        with patch('django.db.connection') as mock_connection:
            mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
            
            # Check admin status
            is_admin = middleware._is_admin_user(mock_request)
            assert is_admin is False
    
    def test_admin_bypass_with_rate_limiter(self, middleware, mock_request):
        """Test that admin users bypass rate limits in allow_request."""
        # Mock user as admin
        with patch.object(middleware, '_is_admin_user', return_value=True):
            with patch.object(middleware.rate_limiter, 'allow_request', return_value=True) as mock_allow:
                # Mock result for headers
                mock_result = RateLimitResult(
                    allowed=True,
                    limit=100,
                    remaining=100,
                    reset_at=datetime.now() + timedelta(seconds=60)
                )
                with patch.object(middleware.rate_limiter, 'check_user_limit', return_value=mock_result):
                    response = middleware(mock_request)
                    
                    # Should call allow_request with is_admin=True
                    mock_allow.assert_called_once()
                    call_args = mock_allow.call_args
                    assert call_args[0][1] is True  # is_admin parameter
                    
                    # Should return normal response
                    assert response.status_code == 200
    
    def test_anonymous_user_not_admin(self, middleware, anonymous_request):
        """Test that anonymous users are not identified as admin."""
        is_admin = middleware._is_admin_user(anonymous_request)
        assert is_admin is False
    
    def test_rate_limit_headers_format(self, middleware, mock_request):
        """Test that rate limit headers are in correct format."""
        reset_time = datetime.now() + timedelta(seconds=60)
        mock_result = RateLimitResult(
            allowed=True,
            limit=100,
            remaining=75,
            reset_at=reset_time
        )
        
        with patch.object(middleware.rate_limiter, 'allow_request', return_value=True):
            with patch.object(middleware.rate_limiter, 'check_user_limit', return_value=mock_result):
                response = middleware(mock_request)
                
                # Verify header formats
                assert response['X-RateLimit-Limit'] == '100'
                assert response['X-RateLimit-Remaining'] == '75'
                assert response['X-RateLimit-Reset'] == reset_time.isoformat()
    
    def test_logging_on_rate_limit_exceeded(self, middleware, mock_request):
        """Test that rate limit exceeded events are logged."""
        mock_result = RateLimitResult(
            allowed=False,
            limit=100,
            remaining=0,
            reset_at=datetime.now() + timedelta(seconds=60),
            retry_after=60
        )
        
        with patch.object(middleware.rate_limiter, 'allow_request', return_value=False):
            with patch.object(middleware.rate_limiter, 'check_user_limit', return_value=mock_result):
                with patch('infrastructure.rate_limit_middleware.logger') as mock_logger:
                    response = middleware(mock_request)
                    
                    # Should log warning
                    mock_logger.warning.assert_called_once()
                    log_message = mock_logger.warning.call_args[0][0]
                    assert 'Rate limit exceeded' in log_message
    
    def test_error_handling_in_admin_check(self, middleware, mock_request):
        """Test that errors in admin check are handled gracefully."""
        # Mock Django connection to raise exception
        with patch('django.db.connection') as mock_connection:
            mock_connection.cursor.side_effect = Exception("Database error")
            
            # Should return False and not crash
            is_admin = middleware._is_admin_user(mock_request)
            assert is_admin is False
    
    def test_multiple_requests_from_same_user(self, middleware, mock_request):
        """Test multiple requests from the same user."""
        # First request - within limit
        mock_result_1 = RateLimitResult(
            allowed=True,
            limit=100,
            remaining=99,
            reset_at=datetime.now() + timedelta(seconds=60)
        )
        
        with patch.object(middleware.rate_limiter, 'allow_request', return_value=True):
            with patch.object(middleware.rate_limiter, 'check_user_limit', return_value=mock_result_1):
                response1 = middleware(mock_request)
                assert response1.status_code == 200
                assert response1['X-RateLimit-Remaining'] == '99'
        
        # Second request - still within limit
        mock_result_2 = RateLimitResult(
            allowed=True,
            limit=100,
            remaining=98,
            reset_at=datetime.now() + timedelta(seconds=60)
        )
        
        with patch.object(middleware.rate_limiter, 'allow_request', return_value=True):
            with patch.object(middleware.rate_limiter, 'check_user_limit', return_value=mock_result_2):
                response2 = middleware(mock_request)
                assert response2.status_code == 200
                assert response2['X-RateLimit-Remaining'] == '98'


class TestRateLimitMiddlewareIntegration:
    """Integration tests for rate limit middleware."""
    
    @pytest.fixture
    def middleware(self):
        """Create middleware instance."""
        get_response = Mock(return_value=HttpResponse())
        return RateLimitMiddleware(get_response)
    
    def test_middleware_with_real_rate_limiter(self, middleware):
        """Test middleware with actual RateLimiter instance."""
        factory = RequestFactory()
        request = factory.get('/api/test/')
        request.user_profile = Mock()
        request.user_profile.id = 'test-user-integration'
        
        # Make request (should succeed if Redis is available)
        response = middleware(request)
        
        # Should have rate limit headers
        assert 'X-RateLimit-Limit' in response
        assert 'X-RateLimit-Remaining' in response
        assert 'X-RateLimit-Reset' in response
    
    def test_middleware_chain_order(self):
        """Test that middleware works correctly in a chain."""
        # Create middleware chain
        def final_view(request):
            return HttpResponse("Success")
        
        middleware = RateLimitMiddleware(final_view)
        
        factory = RequestFactory()
        request = factory.get('/api/test/')
        request.user_profile = Mock()
        request.user_profile.id = 'test-user-chain'
        
        # Mock rate limiter to allow request
        with patch.object(middleware.rate_limiter, 'allow_request', return_value=True):
            mock_result = RateLimitResult(
                allowed=True,
                limit=100,
                remaining=50,
                reset_at=datetime.now() + timedelta(seconds=60)
            )
            with patch.object(middleware.rate_limiter, 'check_user_limit', return_value=mock_result):
                response = middleware(request)
                
                # Should reach final view
                assert response.status_code == 200
                assert response.content == b"Success"
                
                # Should have rate limit headers
                assert 'X-RateLimit-Limit' in response


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
