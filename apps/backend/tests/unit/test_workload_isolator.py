"""
Unit tests for WorkloadIsolator.

Tests query routing functionality including type detection, priority-based
routing, and replica lag fallback.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock

from infrastructure.workload_isolator import (
    WorkloadIsolator,
    Query,
    DatabaseTarget
)
from infrastructure.models import Priority, QueryType, ReplicaInfo


@pytest.fixture
def healthy_replicas():
    """Create a list of healthy replica instances."""
    return [
        ReplicaInfo(
            host="replica1.db.local",
            port=5432,
            weight=1.0,
            is_healthy=True,
            cpu_utilization=30.0,
            avg_response_time=10.0,
            replication_lag=1.0
        ),
        ReplicaInfo(
            host="replica2.db.local",
            port=5432,
            weight=1.0,
            is_healthy=True,
            cpu_utilization=40.0,
            avg_response_time=15.0,
            replication_lag=2.0
        ),
        ReplicaInfo(
            host="replica3.db.local",
            port=5432,
            weight=1.0,
            is_healthy=True,
            cpu_utilization=25.0,
            avg_response_time=12.0,
            replication_lag=0.5
        )
    ]


@pytest.fixture
def workload_isolator(healthy_replicas):
    """Create a workload isolator for testing."""
    return WorkloadIsolator(
        primary_host="primary.db.local",
        primary_port=5432,
        replicas=healthy_replicas,
        max_replica_lag=5.0
    )


class TestWorkloadIsolator:
    """Test cases for WorkloadIsolator class."""
    
    def test_initialization(self, healthy_replicas):
        """Test workload isolator initializes correctly."""
        isolator = WorkloadIsolator(
            primary_host="primary.db.local",
            primary_port=5432,
            replicas=healthy_replicas,
            max_replica_lag=5.0
        )
        
        assert isolator.primary_host == "primary.db.local"
        assert isolator.primary_port == 5432
        assert len(isolator.replicas) == 3
        assert isolator.max_replica_lag == 5.0
    
    def test_detect_select_query(self, workload_isolator):
        """Test detection of SELECT queries."""
        queries = [
            "SELECT * FROM users",
            "  SELECT id, name FROM products WHERE active = true",
            "select count(*) from orders",
            "WITH cte AS (SELECT * FROM items) SELECT * FROM cte"
        ]
        
        for query_text in queries:
            query_type = workload_isolator._detect_query_type(query_text)
            assert query_type == QueryType.SELECT, f"Failed for: {query_text}"
    
    def test_detect_insert_query(self, workload_isolator):
        """Test detection of INSERT queries."""
        queries = [
            "INSERT INTO users (name, email) VALUES ('John', 'john@example.com')",
            "  INSERT INTO products (name) VALUES ('Widget')",
            "insert into orders (user_id) values (1)"
        ]
        
        for query_text in queries:
            query_type = workload_isolator._detect_query_type(query_text)
            assert query_type == QueryType.INSERT, f"Failed for: {query_text}"
    
    def test_detect_update_query(self, workload_isolator):
        """Test detection of UPDATE queries."""
        queries = [
            "UPDATE users SET name = 'Jane' WHERE id = 1",
            "  UPDATE products SET price = 99.99",
            "update orders set status = 'shipped'"
        ]
        
        for query_text in queries:
            query_type = workload_isolator._detect_query_type(query_text)
            assert query_type == QueryType.UPDATE, f"Failed for: {query_text}"
    
    def test_detect_delete_query(self, workload_isolator):
        """Test detection of DELETE queries."""
        queries = [
            "DELETE FROM users WHERE id = 1",
            "  DELETE FROM products WHERE discontinued = true",
            "delete from orders where created_at < '2020-01-01'"
        ]
        
        for query_text in queries:
            query_type = workload_isolator._detect_query_type(query_text)
            assert query_type == QueryType.DELETE, f"Failed for: {query_text}"
    
    def test_write_operations_route_to_primary(self, workload_isolator):
        """Test write operations are routed to primary."""
        write_queries = [
            Query("INSERT INTO users (name) VALUES ('John')", {}),
            Query("UPDATE users SET name = 'Jane' WHERE id = 1", {}),
            Query("DELETE FROM users WHERE id = 1", {})
        ]
        
        for query in write_queries:
            target = workload_isolator.route_query(query)
            assert target.target_type == "primary"
            assert target.host == "primary.db.local"
            assert target.port == 5432
            assert "write" in target.reason.lower() or "primary" in target.reason.lower()
    
    def test_read_operations_route_to_replica(self, workload_isolator):
        """Test read operations are routed to replicas."""
        query = Query("SELECT * FROM users", {})
        
        target = workload_isolator.route_query(query)
        
        assert target.target_type == "replica"
        assert "replica" in target.host
        assert target.port == 5432
    
    def test_critical_operations_route_to_primary(self, workload_isolator):
        """Test critical operations are routed to primary regardless of type."""
        # Even a read query should go to primary if critical
        query = Query("SELECT * FROM users", {})
        
        target = workload_isolator.route_query(query, priority=Priority.CRITICAL)
        
        assert target.target_type == "primary"
        assert target.host == "primary.db.local"
        assert "critical" in target.reason.lower()
    
    def test_replica_selection_prefers_lowest_lag(self, workload_isolator):
        """Test replica selection prefers replica with lowest lag."""
        query = Query("SELECT * FROM users", {})
        
        # Route multiple times and check we get the lowest lag replica
        target = workload_isolator.route_query(query)
        
        # Should select replica3 which has 0.5s lag (lowest)
        assert target.host == "replica3.db.local"
    
    def test_unhealthy_replicas_are_skipped(self, healthy_replicas):
        """Test unhealthy replicas are not selected."""
        # Mark all replicas as unhealthy except one
        healthy_replicas[0].is_healthy = False
        healthy_replicas[1].is_healthy = False
        healthy_replicas[2].is_healthy = True
        
        isolator = WorkloadIsolator(
            primary_host="primary.db.local",
            primary_port=5432,
            replicas=healthy_replicas,
            max_replica_lag=5.0
        )
        
        query = Query("SELECT * FROM users", {})
        target = isolator.route_query(query)
        
        # Should route to the only healthy replica
        assert target.target_type == "replica"
        assert target.host == "replica3.db.local"
    
    def test_high_lag_replicas_trigger_primary_fallback(self, healthy_replicas):
        """Test high lag replicas cause fallback to primary."""
        # Set all replicas to have high lag
        for replica in healthy_replicas:
            replica.replication_lag = 10.0  # Exceeds max_replica_lag of 5.0
        
        isolator = WorkloadIsolator(
            primary_host="primary.db.local",
            primary_port=5432,
            replicas=healthy_replicas,
            max_replica_lag=5.0
        )
        
        query = Query("SELECT * FROM users", {})
        target = isolator.route_query(query)
        
        # Should fall back to primary
        assert target.target_type == "primary"
        assert "fallback" in target.reason.lower() or "no healthy" in target.reason.lower()
    
    def test_no_replicas_routes_to_primary(self):
        """Test routing to primary when no replicas available."""
        isolator = WorkloadIsolator(
            primary_host="primary.db.local",
            primary_port=5432,
            replicas=[],
            max_replica_lag=5.0
        )
        
        query = Query("SELECT * FROM users", {})
        target = isolator.route_query(query)
        
        assert target.target_type == "primary"
        assert target.host == "primary.db.local"
    
    def test_should_route_to_primary_for_writes(self, workload_isolator):
        """Test should_route_to_primary returns True for writes."""
        query = Query("INSERT INTO users (name) VALUES ('John')", {}, query_type=QueryType.INSERT)
        
        result = workload_isolator.should_route_to_primary(query, replica_lag=1.0)
        
        assert result is True
    
    def test_should_route_to_primary_for_high_lag(self, workload_isolator):
        """Test should_route_to_primary returns True for high lag."""
        query = Query("SELECT * FROM users", {}, query_type=QueryType.SELECT)
        
        result = workload_isolator.should_route_to_primary(query, replica_lag=10.0)
        
        assert result is True
    
    def test_should_route_to_primary_for_critical(self, workload_isolator):
        """Test should_route_to_primary returns True for critical operations."""
        query = Query(
            "SELECT * FROM users",
            {},
            query_type=QueryType.SELECT,
            priority=Priority.CRITICAL
        )
        
        result = workload_isolator.should_route_to_primary(query, replica_lag=1.0)
        
        assert result is True
    
    def test_should_not_route_to_primary_for_normal_read(self, workload_isolator):
        """Test should_route_to_primary returns False for normal reads."""
        query = Query("SELECT * FROM users", {}, query_type=QueryType.SELECT)
        
        result = workload_isolator.should_route_to_primary(query, replica_lag=1.0)
        
        assert result is False
    
    def test_check_replica_lag_with_callback(self, healthy_replicas):
        """Test replica lag checking with callback."""
        def mock_lag_callback(replica: str) -> float:
            if "replica1" in replica:
                return 2.5
            return 1.0
        
        isolator = WorkloadIsolator(
            primary_host="primary.db.local",
            primary_port=5432,
            replicas=healthy_replicas,
            max_replica_lag=5.0,
            lag_check_callback=mock_lag_callback
        )
        
        lag = isolator.check_replica_lag("replica1.db.local:5432")
        assert lag == 2.5
    
    def test_check_replica_lag_without_callback(self, workload_isolator):
        """Test replica lag checking without callback uses replica info."""
        lag = workload_isolator.check_replica_lag("replica1.db.local:5432")
        assert lag == 1.0  # From fixture
    
    def test_check_replica_lag_unknown_replica(self, workload_isolator):
        """Test checking lag for unknown replica returns infinity."""
        lag = workload_isolator.check_replica_lag("unknown.db.local:5432")
        assert lag == float('inf')
    
    def test_update_replica_info(self, workload_isolator):
        """Test updating replica information."""
        new_replicas = [
            ReplicaInfo(
                host="new-replica.db.local",
                port=5432,
                is_healthy=True,
                replication_lag=0.5
            )
        ]
        
        workload_isolator.update_replica_info(new_replicas)
        
        assert len(workload_isolator.replicas) == 1
        assert workload_isolator.replicas[0].host == "new-replica.db.local"
    
    def test_get_replica_status(self, workload_isolator):
        """Test getting replica status."""
        status = workload_isolator.get_replica_status()
        
        assert len(status) == 3
        assert all("host" in s for s in status)
        assert all("port" in s for s in status)
        assert all("is_healthy" in s for s in status)
        assert all("replication_lag" in s for s in status)
    
    def test_is_write_operation(self, workload_isolator):
        """Test write operation detection."""
        assert workload_isolator._is_write_operation(QueryType.INSERT) is True
        assert workload_isolator._is_write_operation(QueryType.UPDATE) is True
        assert workload_isolator._is_write_operation(QueryType.DELETE) is True
        assert workload_isolator._is_write_operation(QueryType.SELECT) is False
        assert workload_isolator._is_write_operation(QueryType.OTHER) is False
    
    def test_is_read_operation(self, workload_isolator):
        """Test read operation detection."""
        assert workload_isolator._is_read_operation(QueryType.SELECT) is True
        assert workload_isolator._is_read_operation(QueryType.INSERT) is False
        assert workload_isolator._is_read_operation(QueryType.UPDATE) is False
        assert workload_isolator._is_read_operation(QueryType.DELETE) is False
        assert workload_isolator._is_read_operation(QueryType.OTHER) is False
    
    def test_query_with_predefined_type(self, workload_isolator):
        """Test routing query with predefined query type."""
        query = Query(
            "some complex query",
            {},
            query_type=QueryType.INSERT
        )
        
        target = workload_isolator.route_query(query)
        
        # Should route to primary because it's a write
        assert target.target_type == "primary"
    
    def test_unknown_query_type_routes_to_primary(self, workload_isolator):
        """Test unknown query types route to primary for safety."""
        query = Query("SOME_UNKNOWN_COMMAND", {})
        
        target = workload_isolator.route_query(query)
        
        assert target.target_type == "primary"
        assert "unknown" in target.reason.lower() or "safety" in target.reason.lower()
    
    def test_priority_levels(self, workload_isolator):
        """Test different priority levels."""
        query = Query("SELECT * FROM users", {})
        
        # Normal priority should go to replica
        target = workload_isolator.route_query(query, priority=Priority.NORMAL)
        assert target.target_type == "replica"
        
        # High priority should still go to replica (only CRITICAL goes to primary)
        target = workload_isolator.route_query(query, priority=Priority.HIGH)
        assert target.target_type == "replica"
        
        # Critical priority should go to primary
        target = workload_isolator.route_query(query, priority=Priority.CRITICAL)
        assert target.target_type == "primary"
    
    def test_lag_check_callback_failure_returns_infinity(self, healthy_replicas):
        """Test lag check callback failure returns infinity."""
        def failing_callback(replica: str) -> float:
            raise Exception("Connection failed")
        
        isolator = WorkloadIsolator(
            primary_host="primary.db.local",
            primary_port=5432,
            replicas=healthy_replicas,
            max_replica_lag=5.0,
            lag_check_callback=failing_callback
        )
        
        lag = isolator.check_replica_lag("replica1.db.local:5432")
        assert lag == float('inf')
    
    def test_multiple_queries_load_distribution(self, workload_isolator):
        """Test multiple queries can be distributed across replicas."""
        query = Query("SELECT * FROM users", {})
        
        # Execute multiple queries
        targets = []
        for _ in range(10):
            target = workload_isolator.route_query(query)
            targets.append(target)
        
        # All should go to replicas (not primary)
        assert all(t.target_type == "replica" for t in targets)
        
        # Should consistently select the lowest lag replica
        assert all(t.host == "replica3.db.local" for t in targets)
