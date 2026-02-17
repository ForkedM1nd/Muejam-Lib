"""
Database and Caching Infrastructure Optimization

This package provides optimized database and caching infrastructure components
for Django/Python applications using Prisma ORM with PostgreSQL and Redis.
"""

__version__ = "0.1.0"

from infrastructure.models import (
    Priority,
    QueryType,
    CircuitState,
    QueryLog,
    ReplicaInfo,
    CacheEntry,
    PoolStats,
    HealthStatus,
    QueryAnalysis,
    NPlusOnePattern,
    IndexSuggestion,
    RateLimitResult,
    LimitInfo,
    CacheStats,
    MigrationRecord,
    MigrationResult,
    ValidationResult,
    HealthEvent,
    CacheWarmQuery
)

from infrastructure.connection_pool import (
    Connection,
    ConnectionPool,
    ConnectionPoolManager
)

from infrastructure.workload_isolator import (
    WorkloadIsolator,
    Query,
    DatabaseTarget
)

from infrastructure.cache_manager import (
    LRUCache,
    CacheManager
)

from infrastructure.health_monitor import (
    HealthMonitor,
    AlertChannel
)

from infrastructure.load_balancer import (
    LoadBalancer
)

from infrastructure.query_optimizer import (
    QueryOptimizer,
    QueryContext
)

from infrastructure.schema_manager import (
    SchemaManager,
    Migration
)

__all__ = [
    # Enums
    "Priority",
    "QueryType",
    "CircuitState",
    # Data Models
    "QueryLog",
    "ReplicaInfo",
    "CacheEntry",
    "PoolStats",
    "HealthStatus",
    "QueryAnalysis",
    "NPlusOnePattern",
    "IndexSuggestion",
    "RateLimitResult",
    "LimitInfo",
    "CacheStats",
    "MigrationRecord",
    "MigrationResult",
    "ValidationResult",
    "HealthEvent",
    "CacheWarmQuery",
    # Connection Pool
    "Connection",
    "ConnectionPool",
    "ConnectionPoolManager",
    # Workload Isolator
    "WorkloadIsolator",
    "Query",
    "DatabaseTarget",
    # Cache Manager
    "LRUCache",
    "CacheManager",
    # Health Monitor
    "HealthMonitor",
    "AlertChannel",
    # Load Balancer
    "LoadBalancer",
    # Query Optimizer
    "QueryOptimizer",
    "QueryContext",
    # Schema Manager
    "SchemaManager",
    "Migration",
]
