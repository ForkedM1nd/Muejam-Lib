"""
Django Middleware for Database and Caching Infrastructure Integration.

This module provides Django middleware that integrates:
- ConnectionPoolManager with Django database settings
- WorkloadIsolator for Django ORM query routing
- CacheManager with Django cache framework
- RateLimiter for request rate limiting
- QueryOptimizer for Prisma query hooks

The middleware handles request lifecycle, connection management, rate limiting,
and query optimization transparently for Django applications.
"""

import logging
import time
from typing import Callable, Optional
from datetime import datetime

from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils.deprecation import MiddlewareMixin

from infrastructure.connection_pool import ConnectionPoolManager
from infrastructure.workload_isolator import WorkloadIsolator, Query
from infrastructure.cache_manager import CacheManager
from infrastructure.rate_limiter import RateLimiter
from infrastructure.query_optimizer import QueryOptimizer
from infrastructure.models import Priority, ReplicaInfo
from apps.users.account_suspension import AccountSuspensionService


logger = logging.getLogger(__name__)


class DatabaseInfrastructureMiddleware(MiddlewareMixin):
    """
    Middleware for integrating database infrastructure components with Django.
    
    This middleware:
    - Initializes connection pools on application startup
    - Manages connection lifecycle per request
    - Integrates workload isolation for query routing
    - Provides connection pool statistics
    
    Requirements: 3.1, 3.2, 4.1, 4.2
    """
    
    # Singleton instances
    _pool_manager: Optional[ConnectionPoolManager] = None
    _workload_isolator: Optional[WorkloadIsolator] = None
    _initialized = False
    
    def __init__(self, get_response: Callable):
        """Initialize middleware."""
        super().__init__(get_response)
        self.get_response = get_response
        
        # Initialize infrastructure on first instantiation
        if not DatabaseInfrastructureMiddleware._initialized:
            self._initialize_infrastructure()
            DatabaseInfrastructureMiddleware._initialized = True
    
    def _initialize_infrastructure(self):
        """Initialize connection pool and workload isolator."""
        try:
            # Get configuration from Django settings
            db_config = settings.DATABASES.get('default', {})
            
            # Initialize connection pool manager
            min_connections = getattr(settings, 'DB_POOL_MIN_CONNECTIONS', 10)
            max_connections = getattr(settings, 'DB_POOL_MAX_CONNECTIONS', 50)
            idle_timeout = getattr(settings, 'DB_POOL_IDLE_TIMEOUT', 300)
            
            # Connection factories (placeholder - actual implementation depends on DB driver)
            def read_connection_factory():
                # This would create actual database connections
                # For now, return a mock connection
                logger.debug("Creating read connection")
                return None
            
            def write_connection_factory():
                # This would create actual database connections
                # For now, return a mock connection
                logger.debug("Creating write connection")
                return None
            
            DatabaseInfrastructureMiddleware._pool_manager = ConnectionPoolManager(
                min_connections=min_connections,
                max_connections=max_connections,
                idle_timeout=idle_timeout,
                read_connection_factory=read_connection_factory,
                write_connection_factory=write_connection_factory
            )
            
            # Pre-warm connection pools
            DatabaseInfrastructureMiddleware._pool_manager.prewarm()
            
            # Initialize workload isolator
            primary_host = db_config.get('HOST', 'localhost')
            primary_port = int(db_config.get('PORT', 5432))
            
            # Get replica configuration from settings
            replica_configs = getattr(settings, 'DATABASE_REPLICAS', [])
            replicas = [
                ReplicaInfo(
                    host=r.get('HOST', 'localhost'),
                    port=int(r.get('PORT', 5432)),
                    weight=r.get('WEIGHT', 1.0),
                    is_healthy=True,
                    cpu_utilization=0.0,
                    avg_response_time=0.0,
                    replication_lag=0.0,
                    last_health_check=datetime.now()
                )
                for r in replica_configs
            ]
            
            max_replica_lag = getattr(settings, 'MAX_REPLICA_LAG', 5.0)
            
            DatabaseInfrastructureMiddleware._workload_isolator = WorkloadIsolator(
                primary_host=primary_host,
                primary_port=primary_port,
                replicas=replicas,
                max_replica_lag=max_replica_lag
            )
            
            logger.info("Database infrastructure middleware initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database infrastructure: {e}", exc_info=True)
            raise
    
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """
        Process incoming request.
        
        Attaches connection pool and workload isolator to request for use
        by views and ORM.
        
        Args:
            request: Django HTTP request
            
        Returns:
            None to continue processing, or HttpResponse to short-circuit
        """
        # Attach infrastructure to request
        request.db_pool = DatabaseInfrastructureMiddleware._pool_manager
        request.workload_isolator = DatabaseInfrastructureMiddleware._workload_isolator
        
        # Track request start time for metrics
        request._db_infra_start_time = time.time()
        
        return None
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """
        Process outgoing response.
        
        Cleans up request-specific resources and logs metrics.
        
        Args:
            request: Django HTTP request
            response: Django HTTP response
            
        Returns:
            Modified response
        """
        # Calculate request duration
        if hasattr(request, '_db_infra_start_time'):
            duration = (time.time() - request._db_infra_start_time) * 1000
            logger.debug(f"Request completed in {duration:.2f}ms")
        
        # Add pool statistics to response headers (for debugging)
        if getattr(settings, 'DEBUG', False) and DatabaseInfrastructureMiddleware._pool_manager:
            stats = DatabaseInfrastructureMiddleware._pool_manager.get_pool_stats()
            response['X-DB-Pool-Read-Utilization'] = f"{stats['read'].utilization_percent:.1f}%"
            response['X-DB-Pool-Write-Utilization'] = f"{stats['write'].utilization_percent:.1f}%"
        
        return response
    
    @classmethod
    def get_pool_manager(cls) -> Optional[ConnectionPoolManager]:
        """Get the connection pool manager instance."""
        return cls._pool_manager
    
    @classmethod
    def get_workload_isolator(cls) -> Optional[WorkloadIsolator]:
        """Get the workload isolator instance."""
        return cls._workload_isolator


class CacheMiddleware(MiddlewareMixin):
    """
    Middleware for integrating CacheManager with Django cache framework.
    
    This middleware:
    - Initializes multi-layer cache (L1: in-memory, L2: Redis)
    - Provides cache access through request object
    - Tracks cache statistics
    - Handles cache warming on startup
    
    Requirements: 5.1, 5.2, 5.3, 5.4
    """
    
    # Singleton instance
    _cache_manager: Optional[CacheManager] = None
    _initialized = False
    
    def __init__(self, get_response: Callable):
        """Initialize middleware."""
        super().__init__(get_response)
        self.get_response = get_response
        
        # Initialize cache manager on first instantiation
        if not CacheMiddleware._initialized:
            self._initialize_cache_manager()
            CacheMiddleware._initialized = True
    
    def _initialize_cache_manager(self):
        """Initialize cache manager with Django cache backend."""
        try:
            # Get Redis URL from Django cache settings
            cache_config = settings.CACHES.get('default', {})
            redis_url = cache_config.get('LOCATION', 'redis://localhost:6379/0')
            
            # L1 cache configuration
            l1_max_size = getattr(settings, 'CACHE_L1_MAX_SIZE', 1000)
            l1_default_ttl = getattr(settings, 'CACHE_L1_DEFAULT_TTL', 60)
            
            # L2 cache configuration
            l2_default_ttl = getattr(settings, 'CACHE_L2_DEFAULT_TTL', 300)
            
            CacheMiddleware._cache_manager = CacheManager(
                redis_url=redis_url,
                l1_max_size=l1_max_size,
                l1_default_ttl=l1_default_ttl,
                l2_default_ttl=l2_default_ttl
            )
            
            # Perform cache warming if configured
            warm_queries = getattr(settings, 'CACHE_WARM_QUERIES', [])
            if warm_queries:
                CacheMiddleware._cache_manager.warm_cache(warm_queries)
            
            logger.info("Cache middleware initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize cache middleware: {e}", exc_info=True)
            raise
    
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """
        Process incoming request.
        
        Attaches cache manager to request for use by views.
        
        Args:
            request: Django HTTP request
            
        Returns:
            None to continue processing
        """
        # Attach cache manager to request
        request.cache_manager = CacheMiddleware._cache_manager
        
        return None
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """
        Process outgoing response.
        
        Adds cache statistics to response headers in debug mode.
        
        Args:
            request: Django HTTP request
            response: Django HTTP response
            
        Returns:
            Modified response
        """
        # Add cache statistics to response headers (for debugging)
        if getattr(settings, 'DEBUG', False) and CacheMiddleware._cache_manager:
            stats = CacheMiddleware._cache_manager.get_stats()
            response['X-Cache-L1-Hit-Rate'] = f"{stats.l1_hit_rate:.2f}%"
            response['X-Cache-L2-Hit-Rate'] = f"{stats.l2_hit_rate:.2f}%"
            response['X-Cache-Overall-Hit-Rate'] = f"{stats.overall_hit_rate:.2f}%"
        
        return response
    
    @classmethod
    def get_cache_manager(cls) -> Optional[CacheManager]:
        """Get the cache manager instance."""
        return cls._cache_manager


class RateLimitMiddleware(MiddlewareMixin):
    """
    Middleware for request rate limiting.
    
    This middleware:
    - Enforces per-user rate limits (100 queries/minute)
    - Enforces global rate limits (10,000 queries/minute)
    - Allows admin bypass
    - Returns 429 Too Many Requests when limits exceeded
    
    Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
    """
    
    # Singleton instance
    _rate_limiter: Optional[RateLimiter] = None
    _initialized = False
    
    def __init__(self, get_response: Callable):
        """Initialize middleware."""
        super().__init__(get_response)
        self.get_response = get_response
        
        # Initialize rate limiter on first instantiation
        if not RateLimitMiddleware._initialized:
            self._initialize_rate_limiter()
            RateLimitMiddleware._initialized = True
    
    def _initialize_rate_limiter(self):
        """Initialize rate limiter with Redis backend."""
        try:
            # Get Redis URL from Django cache settings
            cache_config = settings.CACHES.get('default', {})
            redis_url = cache_config.get('LOCATION', 'redis://localhost:6379/0')
            
            RateLimitMiddleware._rate_limiter = RateLimiter(redis_url=redis_url)
            
            logger.info("Rate limit middleware initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize rate limit middleware: {e}", exc_info=True)
            raise
    
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """
        Process incoming request and enforce rate limits.
        
        Args:
            request: Django HTTP request
            
        Returns:
            None to continue processing, or 429 response if rate limit exceeded
        """
        if not RateLimitMiddleware._rate_limiter:
            # Rate limiter not available, allow request
            return None
        
        # Get user identifier
        user_id = self._get_user_id(request)
        
        # Check if user is admin (bypass rate limits)
        is_admin = self._is_admin_user(request)
        
        # Store user_id and is_admin on request for use in process_response
        request._rate_limit_user_id = user_id
        request._rate_limit_is_admin = is_admin
        
        # Check rate limits
        user_result = RateLimitMiddleware._rate_limiter.check_user_limit(user_id)
        
        # Skip rate limiting for admins
        if is_admin and RateLimitMiddleware._rate_limiter.admin_bypass:
            # Store result for headers but don't enforce
            request._rate_limit_result = user_result
            request.rate_limiter = RateLimitMiddleware._rate_limiter
            return None
        
        # Store result for adding headers in process_response
        request._rate_limit_result = user_result
        
        if not user_result.allowed:
            # Log rate limit event (Requirement 15.6)
            from infrastructure.logging_config import get_logger, log_rate_limit_event
            structured_logger = get_logger(__name__)
            
            # Get client IP
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0].strip()
            else:
                ip_address = request.META.get('REMOTE_ADDR', 'unknown')
            
            log_rate_limit_event(
                logger=structured_logger,
                ip_address=ip_address,
                endpoint=request.path,
                limit_type='user' if not user_id.startswith('anon:') else 'ip',
                limit_exceeded=f'{user_result.limit}/minute',
            )
            
            # Return 429 Too Many Requests
            response = JsonResponse(
                {
                    'error': 'Rate limit exceeded',
                    'message': f'Too many requests. Please try again in {user_result.retry_after} seconds.',
                    'limit': user_result.limit,
                    'remaining': user_result.remaining,
                    'reset_at': user_result.reset_at.isoformat()
                },
                status=429
            )
            
            # Add rate limit headers (Requirements 34.6, 34.7)
            response['X-RateLimit-Limit'] = str(user_result.limit)
            response['X-RateLimit-Remaining'] = str(user_result.remaining)
            response['X-RateLimit-Reset'] = str(int(user_result.reset_at.timestamp()))
            response['Retry-After'] = str(user_result.retry_after)
            
            logger.warning(f"Rate limit exceeded for user {user_id}")
            return response
        
        # Attach rate limiter to request
        request.rate_limiter = RateLimitMiddleware._rate_limiter
        
        return None
    
    def _get_user_id(self, request: HttpRequest) -> str:
        """
        Extract user identifier from request.
        
        Args:
            request: Django HTTP request
            
        Returns:
            User identifier string
        """
        # Try to get authenticated user ID
        if hasattr(request, 'user') and request.user.is_authenticated:
            return str(request.user.id)
        
        # Fall back to IP address for anonymous users
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        
        return f"anon:{ip}"
    
    def _is_admin_user(self, request: HttpRequest) -> bool:
        """
        Check if user is an admin.
        
        Args:
            request: Django HTTP request
            
        Returns:
            True if user is admin, False otherwise
        """
        if hasattr(request, 'user') and request.user.is_authenticated:
            return request.user.is_staff or request.user.is_superuser
        return False
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """
        Process outgoing response and add rate limit headers.
        
        Adds rate limit headers to ALL API responses per Requirement 34.7.
        
        Args:
            request: Django HTTP request
            response: Django HTTP response
            
        Returns:
            Modified response with rate limit headers
        """
        # Add rate limit headers to all responses (Requirement 34.7)
        if hasattr(request, '_rate_limit_result'):
            result = request._rate_limit_result
            
            # Add standard rate limit headers
            response['X-RateLimit-Limit'] = str(result.limit)
            response['X-RateLimit-Remaining'] = str(result.remaining)
            # Use Unix timestamp for X-RateLimit-Reset (standard practice)
            response['X-RateLimit-Reset'] = str(int(result.reset_at.timestamp()))
            
            # Only add Retry-After if rate limit was exceeded
            if not result.allowed and result.retry_after:
                response['Retry-After'] = str(result.retry_after)
        
        return response
    
    @classmethod
    def get_rate_limiter(cls) -> Optional[RateLimiter]:
        """Get the rate limiter instance."""
        return cls._rate_limiter


class QueryOptimizerMiddleware(MiddlewareMixin):
    """
    Middleware for integrating QueryOptimizer with Django ORM.
    
    This middleware:
    - Initializes query optimizer
    - Tracks queries per request for N+1 detection
    - Logs slow queries
    - Provides query statistics
    
    Requirements: 1.1, 1.2, 1.4, 1.5
    """
    
    # Singleton instance
    _query_optimizer: Optional[QueryOptimizer] = None
    _initialized = False
    
    def __init__(self, get_response: Callable):
        """Initialize middleware."""
        super().__init__(get_response)
        self.get_response = get_response
        
        # Initialize query optimizer on first instantiation
        if not QueryOptimizerMiddleware._initialized:
            self._initialize_query_optimizer()
            QueryOptimizerMiddleware._initialized = True
    
    def _initialize_query_optimizer(self):
        """Initialize query optimizer."""
        try:
            # Get configuration from Django settings
            slow_query_threshold = getattr(settings, 'SLOW_QUERY_THRESHOLD_MS', 100.0)
            enable_explain = getattr(settings, 'ENABLE_QUERY_EXPLAIN_ANALYZE', True)
            max_history = getattr(settings, 'QUERY_OPTIMIZER_MAX_HISTORY', 1000)
            
            QueryOptimizerMiddleware._query_optimizer = QueryOptimizer(
                slow_query_threshold=slow_query_threshold,
                enable_explain_analyze=enable_explain,
                max_query_history=max_history
            )
            
            logger.info("Query optimizer middleware initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize query optimizer middleware: {e}", exc_info=True)
            raise
    
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """
        Process incoming request.
        
        Starts query tracking for the request.
        
        Args:
            request: Django HTTP request
            
        Returns:
            None to continue processing
        """
        if QueryOptimizerMiddleware._query_optimizer:
            # Generate request ID for query tracking
            request_id = f"{id(request)}_{time.time()}"
            request._query_optimizer_request_id = request_id
            
            # Start request context for N+1 detection
            QueryOptimizerMiddleware._query_optimizer.start_request_context(request_id)
            
            # Attach query optimizer to request
            request.query_optimizer = QueryOptimizerMiddleware._query_optimizer
        
        return None
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """
        Process outgoing response.
        
        Analyzes queries for N+1 patterns and logs statistics.
        
        Args:
            request: Django HTTP request
            response: Django HTTP response
            
        Returns:
            Modified response
        """
        if QueryOptimizerMiddleware._query_optimizer and hasattr(request, '_query_optimizer_request_id'):
            request_id = request._query_optimizer_request_id
            
            # End request context and check for N+1 patterns
            context = QueryOptimizerMiddleware._query_optimizer.end_request_context(request_id)
            
            if context:
                # Detect N+1 patterns
                n_plus_one_patterns = QueryOptimizerMiddleware._query_optimizer.detect_n_plus_one(
                    [q.query_text for q in context.queries]
                )
                
                if n_plus_one_patterns:
                    logger.warning(
                        f"N+1 query pattern detected in request {request_id}: "
                        f"{len(n_plus_one_patterns)} patterns found"
                    )
                
                # Add query statistics to response headers (for debugging)
                if getattr(settings, 'DEBUG', False):
                    response['X-Query-Count'] = str(len(context.queries))
                    response['X-Query-N-Plus-One'] = str(len(n_plus_one_patterns))
        
        return response
    
    @classmethod
    def get_query_optimizer(cls) -> Optional[QueryOptimizer]:
        """Get the query optimizer instance."""
        return cls._query_optimizer



class AccountSuspensionMiddleware(MiddlewareMixin):
    """
    Middleware for enforcing account suspensions.
    
    This middleware:
    - Checks if authenticated user is suspended
    - Prevents access for suspended accounts
    - Returns 403 Forbidden with suspension details
    
    Requirements: 5.14
    """
    
    def __init__(self, get_response: Callable):
        """Initialize middleware."""
        super().__init__(get_response)
        self.get_response = get_response
        self.suspension_service = AccountSuspensionService()
    
    async def __call__(self, request: HttpRequest) -> HttpResponse:
        """
        Process request and check for account suspension.
        
        Args:
            request: Django HTTP request
            
        Returns:
            Response or 403 if account is suspended
        """
        # Only check authenticated users
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Get user ID from Clerk user
            user_id = getattr(request.user, 'id', None)
            
            if user_id:
                # Check suspension status
                suspension = await self.suspension_service.check_suspension(user_id)
                
                if suspension:
                    # Account is suspended, return 403
                    logger.warning(
                        f"Suspended user {user_id} attempted to access {request.path}"
                    )
                    
                    # Format expiration message
                    if suspension['is_permanent']:
                        duration_msg = "This suspension is permanent."
                    else:
                        expires_at = suspension['expires_at']
                        duration_msg = f"This suspension expires at {expires_at.isoformat()}."
                    
                    return JsonResponse(
                        {
                            'error': 'Account Suspended',
                            'message': 'Your account has been suspended.',
                            'reason': suspension['reason'],
                            'suspended_at': suspension['suspended_at'].isoformat(),
                            'expires_at': suspension['expires_at'].isoformat() if suspension['expires_at'] else None,
                            'is_permanent': suspension['is_permanent'],
                            'duration_message': duration_msg
                        },
                        status=403
                    )
        
        # Continue processing
        response = await self.get_response(request)
        return response
