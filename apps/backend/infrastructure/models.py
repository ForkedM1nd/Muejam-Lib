"""
Core data models and interfaces for database and caching infrastructure.

This module defines the foundational data structures used across all
infrastructure components.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional, List, Dict


# Enums

class Priority(Enum):
    """Query priority levels for workload isolation."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class QueryType(Enum):
    """Database query operation types."""
    SELECT = "select"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    OTHER = "other"


# Data Models

@dataclass
class QueryLog:
    """Log entry for database query execution."""
    query_id: str
    query_text: str
    execution_time: float  # in milliseconds
    timestamp: datetime
    execution_plan: Dict[str, Any]
    parameters: Dict[str, Any]
    user_id: Optional[str] = None
    app_name: str = "unknown"
    query_type: QueryType = QueryType.OTHER


@dataclass
class ReplicaInfo:
    """Information about a database replica instance."""
    host: str
    port: int
    weight: float = 1.0
    is_healthy: bool = True
    cpu_utilization: float = 0.0
    avg_response_time: float = 0.0  # in milliseconds
    replication_lag: float = 0.0  # in seconds
    last_health_check: datetime = field(default_factory=datetime.now)


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    key: str
    value: Any
    ttl: int  # in seconds
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    access_count: int = 0


@dataclass
class PoolStats:
    """Connection pool statistics."""
    total_connections: int
    active_connections: int
    idle_connections: int
    utilization_percent: float
    wait_time_avg: float  # in milliseconds
    connection_errors: int


@dataclass
class HealthStatus:
    """Health status of a database instance."""
    instance: str
    is_healthy: bool
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    replication_lag: Optional[float] = None  # in seconds
    last_check: datetime = field(default_factory=datetime.now)
    error_message: Optional[str] = None


@dataclass
class QueryAnalysis:
    """Analysis result for a database query."""
    query_id: str
    has_index: bool
    estimated_cost: float
    actual_cost: float
    rows_examined: int
    rows_returned: int
    optimization_suggestions: List[str] = field(default_factory=list)
    is_slow: bool = False


@dataclass
class NPlusOnePattern:
    """Detected N+1 query pattern."""
    parent_query: str
    child_queries: List[str]
    count: int
    recommendation: str


@dataclass
class IndexSuggestion:
    """Suggested database index for optimization."""
    table_name: str
    columns: List[str]
    index_type: str = "btree"
    reason: str = ""
    estimated_improvement: float = 0.0  # percentage


@dataclass
class RateLimitResult:
    """Result of rate limit check."""
    allowed: bool
    limit: int
    remaining: int
    reset_at: datetime
    retry_after: Optional[int] = None  # in seconds


@dataclass
class LimitInfo:
    """Current rate limit status for a user."""
    user_id: str
    requests_made: int
    limit: int
    window_start: datetime
    window_end: datetime


@dataclass
class CacheStats:
    """Cache performance statistics."""
    hits: int
    misses: int
    hit_rate: float
    evictions: int
    size: int
    max_size: int


@dataclass
class MigrationRecord:
    """Database migration record."""
    migration_id: str
    name: str
    applied_at: datetime
    rollback_script: str
    status: str = "applied"


@dataclass
class MigrationResult:
    """Result of migration execution."""
    success: bool
    migration_id: str
    message: str
    execution_time: float  # in seconds
    error: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of migration validation."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class HealthEvent:
    """Health monitoring event."""
    event_type: str
    instance: str
    timestamp: datetime
    severity: str  # info, warning, error, critical
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CacheWarmQuery:
    """Query configuration for cache warming."""
    query: str
    params: Dict[str, Any]
    ttl: int
    tags: List[str] = field(default_factory=list)
