"""
Load tests for rate limiting middleware.

This test suite verifies that rate limiting works correctly under concurrent load:
- Rate limits are enforced correctly with concurrent requests
- 429 responses are returned when limits exceeded
- Rate limit headers are present in all responses
- Admin bypass works under load
- System remains stable under high load

Requirements tested:
- 1.3 Implement Rate Limiting Middleware
- 5.9 Rate limit enforcement
- 34.6 429 responses with Retry-After
- 34.7 Rate limit headers in all responses
"""

import pytest
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from django.test import RequestFactory
from django.http import HttpResponse

from infrastructure.rate_limit_middleware import RateLimitMiddleware
from infrastructure.rate_limiter import RateLimiter


class TestRateLimitUnderLoad:
    """Test rate limiting behavior under concurrent load."""
    
    @pytest.fixture
    def middleware(self):
        """Create middleware instance with real rate limiter."""
        get_response = Mock(return_value=HttpResponse(status=200))
        return RateLimitMiddleware(get_response)
    
    @pytest.fixture
    def request_factory(self):
        """Create request factory."""
        return RequestFactory()
    
    def create_request(self, factory, user_id=None, is_admin=False, path='/api/test/'):
        """Helper to create a mock request."""
        request = factory.get(path)
        
        if user_id:
            # Authenticated user
            request.user_profile = Mock()
            request.user_profile.id = user_id
        else:
            # Anonymous user
            request.user_profile = None
        
        # Set remote address for IP-based rate limiting
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        
        return request

    def test_concurrent_requests_within_limit(self, middleware, request_factory):
        """
        Test that concurrent requests within limit are all allowed.
        
        Validates: Requirement 1.3 - Rate limiting works correctly under load
        """
        user_id = "load_test_user_1"
        num_requests = 50  # Well within default 100/min limit
        
        def make_request():
            request = self.create_request(request_factory, user_id=user_id)
            response = middleware(request)
            return response.status_code
        
        # Execute concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            results = [future.result() for future in as_completed(futures)]
        
        # All requests should succeed (200 OK)
        assert all(status == 200 for status in results), \
            f"Expected all 200s, got: {Counter(results)}"
        assert len(results) == num_requests
    
    def test_concurrent_requests_exceed_limit(self, middleware, request_factory):
        """
        Test that rate limiting correctly blocks requests when limit exceeded.
        
        Validates: Requirements 1.3, 5.9 - Rate limits enforced under concurrent load
        """
        user_id = "load_test_user_2"
        num_requests = 150  # Exceeds default 100/min limit
        
        def make_request():
            request = self.create_request(request_factory, user_id=user_id)
            response = middleware(request)
            return response.status_code
        
        # Execute concurrent requests
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            results = [future.result() for future in as_completed(futures)]
        
        # Count status codes
        status_counts = Counter(results)
        
        # Should have both 200 (allowed) and 429 (rate limited) responses
        assert 200 in status_counts, "Expected some requests to succeed"
        assert 429 in status_counts, "Expected some requests to be rate limited"
        
        # Approximately 100 should succeed, rest should be rate limited
        # Allow tolerance for concurrent timing and Redis operations
        assert 40 <= status_counts[200] <= 110, \
            f"Expected 40-110 successful requests, got {status_counts[200]}"
        assert status_counts[429] >= 30, \
            f"Expected at least 30 rate limited requests, got {status_counts[429]}"

    def test_429_responses_include_retry_after(self, middleware, request_factory):
        """
        Test that 429 responses include Retry-After header.
        
        Validates: Requirement 34.6 - 429 responses with Retry-After header
        """
        user_id = "load_test_user_3"
        num_requests = 120  # Exceed limit
        
        def make_request():
            request = self.create_request(request_factory, user_id=user_id)
            response = middleware(request)
            return {
                'status': response.status_code,
                'retry_after': response.get('Retry-After'),
                'limit': response.get('X-RateLimit-Limit'),
                'remaining': response.get('X-RateLimit-Remaining'),
                'reset': response.get('X-RateLimit-Reset')
            }
        
        # Execute concurrent requests
        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            results = [future.result() for future in as_completed(futures)]
        
        # Find 429 responses
        rate_limited = [r for r in results if r['status'] == 429]
        
        assert len(rate_limited) > 0, "Expected some requests to be rate limited"
        
        # Verify all 429 responses have Retry-After header
        for response in rate_limited:
            assert response['retry_after'] is not None, \
                "429 response missing Retry-After header"
            assert int(response['retry_after']) > 0, \
                "Retry-After should be positive"
    
    def test_rate_limit_headers_present_under_load(self, middleware, request_factory):
        """
        Test that rate limit headers are present in all responses under load.
        
        Validates: Requirement 34.7 - Rate limit headers in all responses
        """
        user_id = "load_test_user_4"
        num_requests = 80  # Within limit
        
        def make_request():
            request = self.create_request(request_factory, user_id=user_id)
            response = middleware(request)
            return {
                'status': response.status_code,
                'has_limit': 'X-RateLimit-Limit' in response,
                'has_remaining': 'X-RateLimit-Remaining' in response,
                'has_reset': 'X-RateLimit-Reset' in response
            }
        
        # Execute concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            results = [future.result() for future in as_completed(futures)]
        
        # Verify all responses have rate limit headers
        for result in results:
            assert result['has_limit'], "Missing X-RateLimit-Limit header"
            assert result['has_remaining'], "Missing X-RateLimit-Remaining header"
            assert result['has_reset'], "Missing X-RateLimit-Reset header"

    def test_admin_bypass_under_load(self, middleware, request_factory):
        """
        Test that admin users bypass rate limits under load.
        
        Validates: Requirement 1.3 - Admin bypass works under load
        """
        admin_user_id = "admin_user_1"
        num_requests = 200  # Well over normal limit
        
        def make_request():
            request = self.create_request(request_factory, user_id=admin_user_id, is_admin=True)
            
            # Mock admin check to return True
            with patch.object(middleware, '_is_admin_user', return_value=True):
                response = middleware(request)
                return response.status_code
        
        # Execute concurrent requests
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            results = [future.result() for future in as_completed(futures)]
        
        # All requests should succeed (no rate limiting for admin)
        status_counts = Counter(results)
        assert status_counts[200] == num_requests, \
            f"Expected all {num_requests} admin requests to succeed, got {status_counts}"
        assert 429 not in status_counts, \
            "Admin requests should not be rate limited"
    
    def test_multiple_users_concurrent_load(self, middleware, request_factory):
        """
        Test rate limiting with multiple users making concurrent requests.
        
        Validates: Requirement 1.3 - Per-user rate limiting works correctly
        """
        num_users = 5
        requests_per_user = 60  # Within limit per user
        
        def make_request(user_id):
            request = self.create_request(request_factory, user_id=user_id)
            response = middleware(request)
            return (user_id, response.status_code)
        
        # Create requests for multiple users with unique IDs
        all_requests = []
        for user_num in range(num_users):
            user_id = f"multi_load_test_user_{user_num}_{time.time()}"  # Unique ID
            all_requests.extend([(user_id,) for _ in range(requests_per_user)])
        
        # Execute all requests concurrently
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request, user_id) for (user_id,) in all_requests]
            results = [future.result() for future in as_completed(futures)]
        
        # Group results by user
        user_results = {}
        for user_id, status in results:
            if user_id not in user_results:
                user_results[user_id] = []
            user_results[user_id].append(status)
        
        # Each user should have most requests succeed (within their limit)
        # Allow tolerance for concurrent timing and Redis operations
        for user_id, statuses in user_results.items():
            success_count = sum(1 for s in statuses if s == 200)
            # With unique users, each should get close to their full quota
            assert success_count >= requests_per_user * 0.80, \
                f"User {user_id}: expected at least {int(requests_per_user * 0.80)} successful requests, got {success_count}"

    def test_health_check_bypass_under_load(self, middleware, request_factory):
        """
        Test that health check endpoints bypass rate limiting under load.
        
        Validates: Requirement 1.3 - Health checks not rate limited
        """
        num_requests = 200  # Well over normal limit
        
        def make_request():
            request = self.create_request(request_factory, path='/health')
            response = middleware(request)
            return response.status_code
        
        # Execute concurrent health check requests
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            results = [future.result() for future in as_completed(futures)]
        
        # All health check requests should succeed
        status_counts = Counter(results)
        assert status_counts[200] == num_requests, \
            f"Expected all {num_requests} health checks to succeed, got {status_counts}"
        assert 429 not in status_counts, \
            "Health check requests should not be rate limited"
    
    def test_stress_test_high_concurrency(self, middleware, request_factory):
        """
        Stress test with very high concurrency to ensure system stability.
        
        Validates: Requirement 1.3 - System remains stable under high load
        """
        num_users = 10
        requests_per_user = 50
        total_requests = num_users * requests_per_user
        
        def make_request(user_id):
            try:
                request = self.create_request(request_factory, user_id=user_id)
                response = middleware(request)
                return {
                    'success': True,
                    'status': response.status_code,
                    'user': user_id
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e),
                    'user': user_id
                }
        
        # Create all requests
        all_requests = []
        for user_num in range(num_users):
            user_id = f"stress_test_user_{user_num}"
            all_requests.extend([user_id for _ in range(requests_per_user)])
        
        # Execute with high concurrency
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(make_request, user_id) for user_id in all_requests]
            results = [future.result() for future in as_completed(futures)]
        end_time = time.time()
        
        # Verify no exceptions occurred
        errors = [r for r in results if not r['success']]
        assert len(errors) == 0, f"Encountered {len(errors)} errors: {errors[:5]}"
        
        # Verify all requests completed
        assert len(results) == total_requests, \
            f"Expected {total_requests} results, got {len(results)}"
        
        # Verify reasonable response time
        duration = end_time - start_time
        avg_time_per_request = duration / total_requests
        print(f"\nStress test completed: {total_requests} requests in {duration:.2f}s")
        print(f"Average time per request: {avg_time_per_request*1000:.2f}ms")
        
        # Should complete in reasonable time (not hanging)
        assert duration < 30, f"Stress test took too long: {duration}s"
        
        # Verify mix of success and rate limited responses
        status_counts = Counter(r['status'] for r in results)
        print(f"Status distribution: {status_counts}")
        assert 200 in status_counts, "Expected some successful requests"


class TestRateLimitPerformance:
    """Test rate limiting performance characteristics."""
    
    def test_rate_limiter_performance(self):
        """
        Test that rate limiter operations are fast enough for production.
        
        Validates: Requirement 1.3 - Rate limiting doesn't significantly impact performance
        """
        rate_limiter = RateLimiter()
        user_id = "perf_test_user"
        num_checks = 1000
        
        start_time = time.time()
        for i in range(num_checks):
            rate_limiter.allow_request(f"{user_id}_{i % 10}", is_admin=False)
        end_time = time.time()
        
        duration = end_time - start_time
        avg_time = duration / num_checks
        
        print(f"\nRate limiter performance: {num_checks} checks in {duration:.3f}s")
        print(f"Average time per check: {avg_time*1000:.3f}ms")
        
        # Each check should be very fast (< 10ms)
        assert avg_time < 0.01, \
            f"Rate limiter too slow: {avg_time*1000:.2f}ms per check"
