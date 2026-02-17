"""
Property-based tests for core data models.

Feature: db-cache-optimization
"""

import pytest
from hypothesis import given, strategies as st
from datetime import datetime
from infrastructure.models import (
    QueryLog, ReplicaInfo, CacheEntry, PoolStats, HealthStatus,
    QueryType
)


@pytest.mark.property
class TestQueryLogProperties:
    """Property-based tests for QueryLog model."""
    
    @given(
        query_id=st.text(min_size=1, max_size=100),
        execution_time=st.floats(min_value=0.0, max_value=10000.0, allow_nan=False, allow_infinity=False)
    )
    def test_query_log_execution_time_non_negative(self, query_id, execution_time):
        """Property: QueryLog execution_time should always be non-negative."""
        query_log = QueryLog(
            query_id=query_id,
            query_text="SELECT 1",
            execution_time=execution_time,
            timestamp=datetime.now(),
            execution_plan={},
            parameters={}
        )
        
        assert query_log.execution_time >= 0.0


@pytest.mark.property
class TestReplicaInfoProperties:
    """Property-based tests for ReplicaInfo model."""
    
    @given(
        host=st.text(min_size=1, max_size=255),
        port=st.integers(min_value=1, max_value=65535),
        weight=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False)
    )
    def test_replica_info_valid_ranges(self, host, port, weight):
        """Property: ReplicaInfo should accept valid host, port, and weight values."""
        replica = ReplicaInfo(
            host=host,
            port=port,
            weight=weight
        )
        
        assert replica.host == host
        assert 1 <= replica.port <= 65535
        assert replica.weight >= 0.0


@pytest.mark.property
class TestCacheEntryProperties:
    """Property-based tests for CacheEntry model."""
    
    @given(
        key=st.text(min_size=1, max_size=1000),
        ttl=st.integers(min_value=0, max_value=86400)
    )
    def test_cache_entry_ttl_non_negative(self, key, ttl):
        """Property: CacheEntry TTL should always be non-negative."""
        entry = CacheEntry(
            key=key,
            value="test",
            ttl=ttl
        )
        
        assert entry.ttl >= 0


@pytest.mark.property
class TestPoolStatsProperties:
    """Property-based tests for PoolStats model."""
    
    @given(
        total=st.integers(min_value=0, max_value=1000),
        active=st.integers(min_value=0, max_value=1000)
    )
    def test_pool_stats_active_not_exceed_total(self, total, active):
        """Property: Active connections should not exceed total connections."""
        # Ensure active doesn't exceed total
        active = min(active, total)
        idle = total - active
        
        stats = PoolStats(
            total_connections=total,
            active_connections=active,
            idle_connections=idle,
            utilization_percent=(active / total * 100) if total > 0 else 0.0,
            wait_time_avg=0.0,
            connection_errors=0
        )
        
        assert stats.active_connections <= stats.total_connections
        assert stats.active_connections + stats.idle_connections == stats.total_connections


@pytest.mark.property
class TestHealthStatusProperties:
    """Property-based tests for HealthStatus model."""
    
    @given(
        cpu=st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
        memory=st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
        disk=st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False)
    )
    def test_health_status_percentages_valid_range(self, cpu, memory, disk):
        """Property: Health status percentages should be between 0 and 100."""
        status = HealthStatus(
            instance="test",
            is_healthy=True,
            cpu_percent=cpu,
            memory_percent=memory,
            disk_percent=disk
        )
        
        assert 0.0 <= status.cpu_percent <= 100.0
        assert 0.0 <= status.memory_percent <= 100.0
        assert 0.0 <= status.disk_percent <= 100.0
