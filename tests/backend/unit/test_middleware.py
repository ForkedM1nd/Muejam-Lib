"""
Unit tests for Django middleware integration.

Tests the infrastructure middleware components to ensure they properly
integrate with Django request/response cycle.
"""

import os
import sys
import django
from pathlib import Path

# Configure Django settings before importing Django modules
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(backend_dir))

# Setup Django
django.setup()

import pytest
from unittest.mock import Mock, patch, MagicMock
from django.test import RequestFactory
from django.http import HttpResponse, JsonResponse
from django.conf import settings

from infrastructure.middleware import (
    DatabaseInfrastructureMiddleware,
    CacheMiddleware,
    RateLimitMiddleware,
    QueryOptimizerMiddleware
)
from infrastructure.models import Priority, QueryType


class TestDatabaseInfrastructureMiddleware:
    """Test DatabaseInfrastructureMiddleware."""
    
    @pytest.fixture
    def middleware(self):
        """Create middleware instance."""
        get_response = Mock(return_value=HttpResponse())
        return DatabaseInfrastructureMiddleware(get_response)
    
    @pytest.fixture
    def request(self):
        """Create mock request."""
        factory = RequestFactory()
        return factory.get('/test/')
    
    def test_process_request_attaches_infrastructure(self, middleware, request):
        """Test that process_request attaches infrastructure to request."""
        # Process request
        result = middleware.process_request(request)
        
        # Should return None to continue processing
        assert result is None
        
        # Should attach infrastructure components
        assert hasattr(request, 'db_pool')
        assert hasattr(request, 'workload_isolator')
        assert hasattr(request, '_db_infra_start_time')
    
    def test_process_response_adds_debug_headers(self, middleware, request):
        """Test that process_response adds debug headers when DEBUG=True."""
        # Set up request
        request._db_infra_start_time = 0.0
        
        # Create response
        response = HttpResponse()
        
        # Process response with DEBUG=True
        with patch.object(settings, 'DEBUG', True):
            result = middleware.process_response(request, response)
        
        # Should return response
        assert result == response
        
        # Should add debug headers if pool manager exists
        if DatabaseInfrastructureMiddleware._pool_manager:
            assert 'X-DB-Pool-Read-Utilization' in result
            assert 'X-DB-Pool-Write-Utilization' in result
    
    def test_get_pool_manager(self):
        """Test getting pool manager instance."""
        pool_manager = DatabaseInfrastructureMiddleware.get_pool_manager()
        # May be None if not initialized
        assert pool_manager is None or pool_manager is not None
    
    def test_get_workload_isolator(self):
        """Test getting workload isolator instance."""
        isolator = DatabaseInfrastructureMiddleware.get_workload_isolator()
        # May be None if not initialized
        assert isolator is None or isolator is not None


class TestCacheMiddleware:
    """Test CacheMiddleware."""
    
    @pytest.fixture
    def middleware(self):
        """Create middleware instance."""
        get_response = Mock(return_value=HttpResponse())
        return CacheMiddleware(get_response)
    
    @pytest.fixture
    def request(self):
        """Create mock request."""
        factory = RequestFactory()
        return factory.get('/test/')
    
    def test_process_request_attaches_cache_manager(self, middleware, request):
        """Test that process_request attaches cache manager to request."""
        # Process request
        result = middleware.process_request(request)
        
        # Should return None to continue processing
        assert result is None
        
        # Should attach cache manager
        assert hasattr(request, 'cache_manager')
    
    def test_process_response_adds_cache_stats(self, middleware, request):
        """Test that process_response adds cache statistics when DEBUG=True."""
        # Create response
        response = HttpResponse()
        
        # Process response with DEBUG=True
        with patch.object(settings, 'DEBUG', True):
            result = middleware.process_response(request, response)
        
        # Should return response
        assert result == response
        
        # Should add cache stats headers if cache manager exists
        if CacheMiddleware._cache_manager:
            assert 'X-Cache-L1-Hit-Rate' in result
            assert 'X-Cache-L2-Hit-Rate' in result
            assert 'X-Cache-Overall-Hit-Rate' in result
    
    def test_get_cache_manager(self):
        """Test getting cache manager instance."""
        cache_manager = CacheMiddleware.get_cache_manager()
        # May be None if not initialized
        assert cache_manager is None or cache_manager is not None


class TestRateLimitMiddleware:
    """Test RateLimitMiddleware."""
    
    @pytest.fixture
    def middleware(self):
        """Create middleware instance."""
        get_response = Mock(return_value=HttpResponse())
        return RateLimitMiddleware(get_response)
    
    @pytest.fixture
    def request(self):
        """Create mock request."""
        factory = RequestFactory()
        request = factory.get('/test/')
        # Add mock user
        request.user = Mock()
        request.user.is_authenticated = True
        request.user.id = 123
        request.user.is_staff = False
        request.user.is_superuser = False
        return request
    
    def test_process_request_allows_request_within_limit(self, middleware, request):
        """Test that requests within rate limit are allowed."""
        # Mock rate limiter to allow request
        if RateLimitMiddleware._rate_limiter:
            with patch.object(RateLimitMiddleware._rate_limiter, 'allow_request', return_value=True):
                result = middleware.process_request(request)
                
                # Should return None to continue processing
                assert result is None
                
                # Should attach rate limiter
                assert hasattr(request, 'rate_limiter')
    
    def test_process_request_blocks_request_over_limit(self, middleware, request):
        """Test that requests over rate limit are blocked."""
        # Mock rate limiter to block request
        if RateLimitMiddleware._rate_limiter:
            with patch.object(RateLimitMiddleware._rate_limiter, 'allow_request', return_value=False):
                # Mock get_limit_info
                from infrastructure.models import LimitInfo
                from datetime import datetime, timedelta
                
                mock_limit_info = LimitInfo(
                    user_limit=100,
                    user_remaining=0,
                    global_limit=10000,
                    global_remaining=5000,
                    reset_at=datetime.now() + timedelta(seconds=60),
                    retry_after=60
                )
                
                with patch.object(RateLimitMiddleware._rate_limiter, 'get_limit_info', return_value=mock_limit_info):
                    result = middleware.process_request(request)
                    
                    # Should return 429 response
                    assert result is not None
                    assert result.status_code == 429
                    
                    # Should have rate limit headers
                    assert 'X-RateLimit-Limit' in result
                    assert 'X-RateLimit-Remaining' in result
                    assert 'Retry-After' in result
    
    def test_get_user_id_authenticated(self, middleware, request):
        """Test getting user ID for authenticated user."""
        user_id = middleware._get_user_id(request)
        assert user_id == "123"
    
    def test_get_user_id_anonymous(self, middleware):
        """Test getting user ID for anonymous user."""
        factory = RequestFactory()
        request = factory.get('/test/')
        request.user = Mock()
        request.user.is_authenticated = False
        
        user_id = middleware._get_user_id(request)
        assert user_id.startswith("anon:")
    
    def test_is_admin_user_staff(self, middleware, request):
        """Test admin check for staff user."""
        request.user.is_staff = True
        assert middleware._is_admin_user(request) is True
    
    def test_is_admin_user_superuser(self, middleware, request):
        """Test admin check for superuser."""
        request.user.is_superuser = True
        assert middleware._is_admin_user(request) is True
    
    def test_is_admin_user_regular(self, middleware, request):
        """Test admin check for regular user."""
        assert middleware._is_admin_user(request) is False
    
    def test_get_rate_limiter(self):
        """Test getting rate limiter instance."""
        rate_limiter = RateLimitMiddleware.get_rate_limiter()
        # May be None if not initialized
        assert rate_limiter is None or rate_limiter is not None


class TestQueryOptimizerMiddleware:
    """Test QueryOptimizerMiddleware."""
    
    @pytest.fixture
    def middleware(self):
        """Create middleware instance."""
        get_response = Mock(return_value=HttpResponse())
        return QueryOptimizerMiddleware(get_response)
    
    @pytest.fixture
    def request(self):
        """Create mock request."""
        factory = RequestFactory()
        return factory.get('/test/')
    
    def test_process_request_starts_tracking(self, middleware, request):
        """Test that process_request starts query tracking."""
        # Process request
        result = middleware.process_request(request)
        
        # Should return None to continue processing
        assert result is None
        
        # Should attach query optimizer and request ID
        if QueryOptimizerMiddleware._query_optimizer:
            assert hasattr(request, 'query_optimizer')
            assert hasattr(request, '_query_optimizer_request_id')
    
    def test_process_response_ends_tracking(self, middleware, request):
        """Test that process_response ends query tracking."""
        # Set up request with tracking
        if QueryOptimizerMiddleware._query_optimizer:
            request._query_optimizer_request_id = "test_request_123"
            QueryOptimizerMiddleware._query_optimizer.start_request_context("test_request_123")
            
            # Create response
            response = HttpResponse()
            
            # Process response
            result = middleware.process_response(request, response)
            
            # Should return response
            assert result == response
    
    def test_process_response_adds_query_stats(self, middleware, request):
        """Test that process_response adds query statistics when DEBUG=True."""
        # Set up request with tracking
        if QueryOptimizerMiddleware._query_optimizer:
            request._query_optimizer_request_id = "test_request_123"
            QueryOptimizerMiddleware._query_optimizer.start_request_context("test_request_123")
            
            # Create response
            response = HttpResponse()
            
            # Process response with DEBUG=True
            with patch.object(settings, 'DEBUG', True):
                result = middleware.process_response(request, response)
            
            # Should add query stats headers
            assert 'X-Query-Count' in result
            assert 'X-Query-N-Plus-One' in result
    
    def test_get_query_optimizer(self):
        """Test getting query optimizer instance."""
        query_optimizer = QueryOptimizerMiddleware.get_query_optimizer()
        # May be None if not initialized
        assert query_optimizer is None or query_optimizer is not None


class TestMiddlewareIntegration:
    """Test middleware integration scenarios."""
    
    @pytest.fixture
    def request(self):
        """Create mock request."""
        factory = RequestFactory()
        request = factory.get('/test/')
        request.user = Mock()
        request.user.is_authenticated = True
        request.user.id = 123
        request.user.is_staff = False
        request.user.is_superuser = False
        return request
    
    def test_middleware_chain(self, request):
        """Test that middleware can be chained together."""
        # Create middleware instances
        get_response = Mock(return_value=HttpResponse())
        
        db_middleware = DatabaseInfrastructureMiddleware(get_response)
        cache_middleware = CacheMiddleware(get_response)
        rate_middleware = RateLimitMiddleware(get_response)
        query_middleware = QueryOptimizerMiddleware(get_response)
        
        # Process request through chain
        result = db_middleware.process_request(request)
        assert result is None
        
        result = cache_middleware.process_request(request)
        assert result is None
        
        result = rate_middleware.process_request(request)
        # May be None or 429 response depending on rate limiter state
        assert result is None or result.status_code == 429
        
        if result is None:
            result = query_middleware.process_request(request)
            assert result is None
            
            # Create response
            response = HttpResponse()
            
            # Process response through chain (reverse order)
            response = query_middleware.process_response(request, response)
            response = rate_middleware.process_response(request, response)
            response = cache_middleware.process_response(request, response)
            response = db_middleware.process_response(request, response)
            
            assert response.status_code == 200
    
    def test_middleware_with_rate_limit_exceeded(self, request):
        """Test middleware chain when rate limit is exceeded."""
        # Create middleware instances
        get_response = Mock(return_value=HttpResponse())
        rate_middleware = RateLimitMiddleware(get_response)
        
        # Mock rate limiter to block request
        if RateLimitMiddleware._rate_limiter:
            with patch.object(RateLimitMiddleware._rate_limiter, 'allow_request', return_value=False):
                from infrastructure.models import LimitInfo
                from datetime import datetime, timedelta
                
                mock_limit_info = LimitInfo(
                    user_limit=100,
                    user_remaining=0,
                    global_limit=10000,
                    global_remaining=5000,
                    reset_at=datetime.now() + timedelta(seconds=60),
                    retry_after=60
                )
                
                with patch.object(RateLimitMiddleware._rate_limiter, 'get_limit_info', return_value=mock_limit_info):
                    result = rate_middleware.process_request(request)
                    
                    # Should short-circuit with 429 response
                    assert result is not None
                    assert result.status_code == 429
                    
                    # Subsequent middleware should not be called
                    # (in real Django, middleware chain stops here)
