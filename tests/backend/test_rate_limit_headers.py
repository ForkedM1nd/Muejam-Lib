"""
Test rate limit response headers.

Verifies that rate limit middleware adds the required headers:
- X-RateLimit-Remaining
- X-RateLimit-Reset
- Retry-After (for 429 responses)

Requirements: 8.3
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from django.test import RequestFactory
from django.http import HttpResponse, JsonResponse

from infrastructure.rate_limit_middleware import RateLimitMiddleware
from infrastructure.models import RateLimitResult


class TestRateLimitHeaders:
    """Test rate limit response headers per Requirement 8.3."""
    
    @pytest.fixture
    def middleware(self):
        """Create middleware instance."""
        get_response = Mock(return_value=HttpResponse(status=200))
        return RateLimitMiddleware(get_response)
    
    @pytest.fixture
    def mock_request(self):
        """Create mock request."""
        factory = RequestFactory()
        request = factory.get('/api/test/')
        request.user_profile = Mock()
        request.user_profile.id = 'user123'
        request.client_type = 'mobile-ios'
        return request
    
    def test_rate_limit_headers_on_success(self, middleware, mock_request):
        """
        Test that rate limit headers are added to successful responses.
        
        Validates: Requirement 8.3
        """
        reset_time = datetime.now() + timedelta(seconds=60)
        
        # Mock rate limiter to allow request
        mock_result = RateLimitResult(
            allowed=True,
            limit=150,
            remaining=100,
            reset_at=reset_time,
            retry_after=None
        )
        
        with patch.object(middleware.rate_limiter, 'allow_request', return_value=True):
            with patch.object(middleware.rate_limiter, 'check_user_limit', return_value=mock_result):
                response = middleware(mock_request)
                
                # Verify response is successful
                assert response.status_code == 200
                
                # Verify rate limit headers are present
                assert 'X-RateLimit-Limit' in response
                assert 'X-RateLimit-Remaining' in response
                assert 'X-RateLimit-Reset' in response
                
                # Verify header values
                assert response['X-RateLimit-Limit'] == '150'
                assert response['X-RateLimit-Remaining'] == '100'
                assert response['X-RateLimit-Reset'] == reset_time.isoformat()
                
                # Retry-After should NOT be present for successful requests
                assert 'Retry-After' not in response
    
    def test_rate_limit_headers_on_429(self, middleware, mock_request):
        """
        Test that rate limit headers including Retry-After are added to 429 responses.
        
        Validates: Requirement 8.3
        """
        reset_time = datetime.now() + timedelta(seconds=60)
        
        # Mock rate limiter to block request
        mock_result = RateLimitResult(
            allowed=False,
            limit=150,
            remaining=0,
            reset_at=reset_time,
            retry_after=60
        )
        
        with patch.object(middleware.rate_limiter, 'allow_request', return_value=False):
            with patch.object(middleware.rate_limiter, 'check_user_limit', return_value=mock_result):
                response = middleware(mock_request)
                
                # Verify response is 429
                assert response.status_code == 429
                
                # Verify all rate limit headers are present
                assert 'X-RateLimit-Limit' in response
                assert 'X-RateLimit-Remaining' in response
                assert 'X-RateLimit-Reset' in response
                assert 'Retry-After' in response
                
                # Verify header values
                assert response['X-RateLimit-Limit'] == '150'
                assert response['X-RateLimit-Remaining'] == '0'
                assert response['X-RateLimit-Reset'] == reset_time.isoformat()
                assert response['Retry-After'] == '60'
    
    def test_retry_after_header_format(self, middleware, mock_request):
        """
        Test that Retry-After header is in seconds format.
        
        Validates: Requirement 8.3
        """
        reset_time = datetime.now() + timedelta(seconds=120)
        
        # Mock rate limiter to block request
        mock_result = RateLimitResult(
            allowed=False,
            limit=150,
            remaining=0,
            reset_at=reset_time,
            retry_after=120
        )
        
        with patch.object(middleware.rate_limiter, 'allow_request', return_value=False):
            with patch.object(middleware.rate_limiter, 'check_user_limit', return_value=mock_result):
                response = middleware(mock_request)
                
                # Verify Retry-After is a string representing seconds
                assert 'Retry-After' in response
                retry_after = response['Retry-After']
                assert retry_after.isdigit()
                assert int(retry_after) == 120
    
    def test_rate_limit_reset_header_format(self, middleware, mock_request):
        """
        Test that X-RateLimit-Reset header is in ISO format.
        
        Validates: Requirement 8.3
        """
        reset_time = datetime.now() + timedelta(seconds=60)
        
        # Mock rate limiter to allow request
        mock_result = RateLimitResult(
            allowed=True,
            limit=150,
            remaining=100,
            reset_at=reset_time,
            retry_after=None
        )
        
        with patch.object(middleware.rate_limiter, 'allow_request', return_value=True):
            with patch.object(middleware.rate_limiter, 'check_user_limit', return_value=mock_result):
                response = middleware(mock_request)
                
                # Verify X-RateLimit-Reset is in ISO format
                assert 'X-RateLimit-Reset' in response
                reset_header = response['X-RateLimit-Reset']
                
                # Should be able to parse as ISO datetime
                parsed_time = datetime.fromisoformat(reset_header)
                assert isinstance(parsed_time, datetime)
