"""
Unit tests for core data models.
"""

import pytest
from datetime import datetime
from infrastructure.models import (
    QueryLog, ReplicaInfo, CacheEntry, PoolStats, HealthStatus,
    Priority, CircuitState, QueryType
)


class TestDataModels:
    """Test core data model creation and attributes."""
    
    def test_query_log_creation(self):
        """Test QueryLog dataclass creation."""
        query_log = QueryLog(
            query_id="test-1",
            query_text="SELECT * FROM users",
            execution_time=100.0,
            timestamp=datetime.now(),
            execution_plan={"type": "Seq Scan"},
            parameters={}
        )
        
        assert query_log.query_id == "test-1"
        assert query_log.execution_time == 100.0
        assert query_log.query_type == QueryType.OTHER
    
    def test_replica_info_creation(self):
        """Test ReplicaInfo dataclass creation."""
        replica = ReplicaInfo(
            host="localhost",
            port=5432,
            weight=1.0
        )
        
        assert replica.host == "localhost"
        assert replica.port == 5432
        assert replica.is_healthy is True
        assert replica.cpu_utilization == 0.0
    
    def test_cache_entry_creation(self):
        """Test CacheEntry dataclass creation."""
        entry = CacheEntry(
            key="test:key",
            value={"data": "value"},
            ttl=300
        )
        
        assert entry.key == "test:key"
        assert entry.ttl == 300
        assert entry.tags == []
        assert entry.access_count == 0
    
    def test_pool_stats_creation(self):
        """Test PoolStats dataclass creation."""
        stats = PoolStats(
            total_connections=50,
            active_connections=30,
            idle_connections=20,
            utilization_percent=60.0,
            wait_time_avg=5.0,
            connection_errors=0
        )
        
        assert stats.total_connections == 50
        assert stats.utilization_percent == 60.0
    
    def test_health_status_creation(self):
        """Test HealthStatus dataclass creation."""
        status = HealthStatus(
            instance="primary",
            is_healthy=True,
            cpu_percent=50.0,
            memory_percent=60.0,
            disk_percent=40.0
        )
        
        assert status.instance == "primary"
        assert status.is_healthy is True
        assert status.replication_lag is None


class TestEnums:
    """Test enum definitions."""
    
    def test_priority_enum(self):
        """Test Priority enum values."""
        assert Priority.LOW.value == "low"
        assert Priority.NORMAL.value == "normal"
        assert Priority.HIGH.value == "high"
        assert Priority.CRITICAL.value == "critical"
    
    def test_circuit_state_enum(self):
        """Test CircuitState enum values."""
        assert CircuitState.CLOSED.value == "closed"
        assert CircuitState.OPEN.value == "open"
        assert CircuitState.HALF_OPEN.value == "half_open"
    
    def test_query_type_enum(self):
        """Test QueryType enum values."""
        assert QueryType.SELECT.value == "select"
        assert QueryType.INSERT.value == "insert"
        assert QueryType.UPDATE.value == "update"
        assert QueryType.DELETE.value == "delete"
        assert QueryType.OTHER.value == "other"
