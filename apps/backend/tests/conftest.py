"""
Shared test fixtures and configuration for infrastructure tests.
"""

import pytest
from datetime import datetime
from hypothesis import settings, Verbosity

# Configure Hypothesis for property-based testing
settings.register_profile("default", max_examples=100, verbosity=Verbosity.normal)
settings.register_profile("ci", max_examples=200, verbosity=Verbosity.verbose)
settings.register_profile("dev", max_examples=50, verbosity=Verbosity.normal)
settings.load_profile("default")


@pytest.fixture
def mock_timestamp():
    """Provide a consistent timestamp for testing."""
    return datetime(2024, 1, 1, 12, 0, 0)


@pytest.fixture
def sample_query_log(mock_timestamp):
    """Provide a sample QueryLog for testing."""
    from infrastructure.models import QueryLog, QueryType
    
    return QueryLog(
        query_id="test-query-1",
        query_text="SELECT * FROM users WHERE id = $1",
        execution_time=50.0,
        timestamp=mock_timestamp,
        execution_plan={"type": "Index Scan", "cost": 0.5},
        parameters={"id": 1},
        user_id="user-123",
        app_name="test-app",
        query_type=QueryType.SELECT
    )


@pytest.fixture
def sample_replica_info(mock_timestamp):
    """Provide a sample ReplicaInfo for testing."""
    from infrastructure.models import ReplicaInfo
    
    return ReplicaInfo(
        host="replica-1.example.com",
        port=5432,
        weight=1.0,
        is_healthy=True,
        cpu_utilization=45.0,
        avg_response_time=25.0,
        replication_lag=0.5,
        last_health_check=mock_timestamp
    )


@pytest.fixture
def sample_cache_entry(mock_timestamp):
    """Provide a sample CacheEntry for testing."""
    from infrastructure.models import CacheEntry
    
    return CacheEntry(
        key="user:123",
        value={"id": 123, "name": "Test User"},
        ttl=300,
        tags=["user", "profile"],
        created_at=mock_timestamp,
        access_count=5
    )


@pytest.fixture
def sample_pool_stats():
    """Provide sample PoolStats for testing."""
    from infrastructure.models import PoolStats
    
    return PoolStats(
        total_connections=50,
        active_connections=30,
        idle_connections=20,
        utilization_percent=60.0,
        wait_time_avg=5.0,
        connection_errors=0
    )


@pytest.fixture
def sample_health_status(mock_timestamp):
    """Provide a sample HealthStatus for testing."""
    from infrastructure.models import HealthStatus
    
    return HealthStatus(
        instance="primary-db",
        is_healthy=True,
        cpu_percent=55.0,
        memory_percent=70.0,
        disk_percent=40.0,
        replication_lag=None,
        last_check=mock_timestamp,
        error_message=None
    )
