"""
Integration tests for rate limit response handling.

Tests verify that rate limit responses include proper status codes,
headers, and retry information per Requirements 5.9, 34.6, and 34.7.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, Mock
from django.test import RequestFactory
from django.http import HttpResponse

from infrastructure.middleware import RateLimitMiddleware
from infrastructure.models import RateLimitResult


class TestRateLimitResponseHandling:
    """Test rate limit response handling per Requirements 5.9, 34.6, 34.7."""
    
    @pytest.fixture
    def middleware(self):
        """Create middleware instance."""
        get_response = Mock(return_value=HttpResponse())
        return RateLimitMiddleware(get_response)
    
    @pytest.fixture
    def mock_request(self):
        """Create mock request."""
        factory = RequestFactory()
        request = factory.get('/api/test/')
        request.user = Mock()
        request.user.is_authenticated = True
        request.user.id = 123
        request.user.is_staff = False
        request.user.is_superuser = False
        return request
    
    def test_429_status_code_when_rate_limited(self, middleware, mock_request):
        """
        Test that 429 status code is returned when rate limit exceeded.
        
        Validates: Requirements 5.9, 34.6
        """
        if not RateLimitMiddleware._rate_limiter:
            pytest.skip("Rate limiter not available")
        
        # Mock rate limit exceeded
        mock_result = RateLimitResult(
            allowed=False,
            limit=100,
            remaining=0,
            reset_at=datetime.now() + timedelta(seconds=60),
            retry_after=60
        )
        
        with patch.object(RateLimitMiddleware._rate_limiter, 'check_user_limit', return_value=mock_result):
            response = middleware.process_request(mock_request)
            
            # Verify 429 status code
            assert response is not None
            assert response.status_code == 429
    
    def test_retry_after_header_when_rate_limited(self, middleware, mock_request):
        """
        Test that Retry-After header is included when rate limited.
        
        Validates: Requirements 5.9, 34.6
        """
        if not RateLimitMiddleware._rate_limiter:
            pytest.skip("Rate limiter not available")
        
        # Mock rate limit exceeded
        mock_result = RateLimitResult(
            allowed=False,
            limit=100,
            remaining=0,
            reset_at=datetime.now() + timedelta(seconds=60),
            retry_after=60
        )
        
        with patch.object(RateLimitMiddleware._rate_limiter, 'check_user_limit', return_value=mock_result):
            response = middleware.process_request(mock_request)
            
            # Verify Retry-After header
            assert 'Retry-After' in response
            assert response['Retry-After'] == '60'
    
    def test_rate_limit_headers_in_all_responses(self, middleware, mock_request):
        """
        Test that rate limit headers are included in ALL responses.
        
        Validates: Requirement 34.7
        """
        if not RateLimitMiddleware._rate_limiter:
            pytest.skip("Rate limiter not available")
        
        # Mock rate limit NOT exceeded (normal request)
        mock_result = RateLimitResult(
            allowed=True,
            limit=100,
            remaining=50,
            reset_at=datetime.now() + timedelta(seconds=60)
        )
        
        with patch.object(RateLimitMiddleware._rate_limiter, 'check_user_limit', return_value=mock_result):
            # Process request (should be allowed)
            request_response = middleware.process_request(mock_request)
            assert request_response is None  # Request allowed
            
            # Create a normal response
            response = HttpResponse(status=200)
            
            # Process response to add headers
            response = middleware.process_response(mock_request, response)
            
            # Verify rate limit headers are present
            assert 'X-RateLimit-Limit' in response
            assert 'X-RateLimit-Remaining' in response
            assert 'X-RateLimit-Reset' in response
            
            # Verify header values
            assert response['X-RateLimit-Limit'] == '100'
            assert response['X-RateLimit-Remaining'] == '50'
            
            # Retry-After should NOT be present for allowed requests
            assert 'Retry-After' not in response
    
    def test_rate_limit_headers_format(self, middleware, mock_request):
        """
        Test that rate limit headers have correct format.
        
        Validates: Requirement 34.7
        """
        if not RateLimitMiddleware._rate_limiter:
            pytest.skip("Rate limiter not available")
        
        # Mock rate limit result
        reset_time = datetime.now() + timedelta(seconds=60)
        mock_result = RateLimitResult(
            allowed=True,
            limit=100,
            remaining=75,
            reset_at=reset_time
        )
        
        with patch.object(RateLimitMiddleware._rate_limiter, 'check_user_limit', return_value=mock_result):
            # Process request
            middleware.process_request(mock_request)
            
            # Create and process response
            response = HttpResponse(status=200)
            response = middleware.process_response(mock_request, response)
            
            # Verify X-RateLimit-Limit is a number
            assert response['X-RateLimit-Limit'].isdigit()
            assert int(response['X-RateLimit-Limit']) == 100
            
            # Verify X-RateLimit-Remaining is a number
            assert response['X-RateLimit-Remaining'].isdigit()
            assert int(response['X-RateLimit-Remaining']) == 75
            
            # Verify X-RateLimit-Reset is a Unix timestamp
            assert response['X-RateLimit-Reset'].isdigit()
            reset_timestamp = int(response['X-RateLimit-Reset'])
            assert reset_timestamp > 0
    
    def test_complete_rate_limit_flow(self, middleware, mock_request):
        """
        Test complete rate limit flow from request to response.
        
        Validates: Requirements 5.9, 34.6, 34.7
        """
        if not RateLimitMiddleware._rate_limiter:
            pytest.skip("Rate limiter not available")
        
        # Scenario 1: Request within limit
        mock_result_allowed = RateLimitResult(
            allowed=True,
            limit=100,
            remaining=50,
            reset_at=datetime.now() + timedelta(seconds=60)
        )
        
        with patch.object(RateLimitMiddleware._rate_limiter, 'check_user_limit', return_value=mock_result_allowed):
            # Process request
            request_response = middleware.process_request(mock_request)
            assert request_response is None  # Allowed
            
            # Process response
            response = HttpResponse(status=200)
            response = middleware.process_response(mock_request, response)
            
            # Verify headers present but no Retry-After
            assert 'X-RateLimit-Limit' in response
            assert 'X-RateLimit-Remaining' in response
            assert 'X-RateLimit-Reset' in response
            assert 'Retry-After' not in response
        
        # Scenario 2: Request exceeds limit
        mock_result_blocked = RateLimitResult(
            allowed=False,
            limit=100,
            remaining=0,
            reset_at=datetime.now() + timedelta(seconds=60),
            retry_after=60
        )
        
        with patch.object(RateLimitMiddleware._rate_limiter, 'check_user_limit', return_value=mock_result_blocked):
            # Process request
            request_response = middleware.process_request(mock_request)
            
            # Should return 429 response immediately
            assert request_response is not None
            assert request_response.status_code == 429
            
            # Verify all headers including Retry-After
            assert 'X-RateLimit-Limit' in request_response
            assert 'X-RateLimit-Remaining' in request_response
            assert 'X-RateLimit-Reset' in request_response
            assert 'Retry-After' in request_response
            
            # Verify values
            assert request_response['X-RateLimit-Limit'] == '100'
            assert request_response['X-RateLimit-Remaining'] == '0'
            assert request_response['Retry-After'] == '60'
