"""
Unit tests for ConnectionPoolManager.

Tests connection pool functionality including acquisition, release,
idle cleanup, and statistics tracking.
"""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock

from infrastructure.connection_pool import (
    Connection,
    ConnectionPool,
    ConnectionPoolManager
)
from infrastructure.models import PoolStats


class MockDBConnection:
    """Mock database connection for testing."""
    
    def __init__(self):
        self.closed = False
    
    def close(self):
        self.closed = True


@pytest.fixture
def mock_connection_factory():
    """Factory that creates mock database connections."""
    def factory():
        return MockDBConnection()
    return factory


@pytest.fixture
def connection_pool(mock_connection_factory):
    """Create a connection pool for testing."""
    pool = ConnectionPool(
        pool_type="test",
        min_connections=2,
        max_connections=5,
        idle_timeout=10,
        connection_factory=mock_connection_factory
    )
    pool.prewarm()
    yield pool
    pool.close_all()


@pytest.fixture
def pool_manager(mock_connection_factory):
    """Create a connection pool manager for testing."""
    manager = ConnectionPoolManager(
        min_connections=2,
        max_connections=5,
        idle_timeout=10,
        read_connection_factory=mock_connection_factory,
        write_connection_factory=mock_connection_factory
    )
    manager.prewarm()
    yield manager
    manager.close_all()


class TestConnectionPool:
    """Test cases for ConnectionPool class."""
    
    def test_pool_initialization(self, mock_connection_factory):
        """Test pool initializes with correct parameters."""
        pool = ConnectionPool(
            pool_type="read",
            min_connections=10,
            max_connections=50,
            idle_timeout=300,
            connection_factory=mock_connection_factory
        )
        
        assert pool.pool_type == "read"
        assert pool.min_connections == 10
        assert pool.max_connections == 50
        assert pool.idle_timeout == 300
        
        pool.close_all()
    
    def test_prewarm_creates_minimum_connections(self, mock_connection_factory):
        """Test prewarming creates minimum number of connections."""
        pool = ConnectionPool(
            pool_type="test",
            min_connections=3,
            max_connections=10,
            connection_factory=mock_connection_factory
        )
        
        pool.prewarm()
        stats = pool.get_stats()
        
        assert stats.total_connections == 3
        assert stats.idle_connections == 3
        assert stats.active_connections == 0
        
        pool.close_all()
    
    def test_get_connection_acquires_from_pool(self, connection_pool):
        """Test getting a connection from the pool."""
        conn = connection_pool.get_connection(timeout=1.0)
        
        assert conn is not None
        assert conn.is_active is True
        assert conn.pool_type == "test"
        
        connection_pool.release_connection(conn)
    
    def test_release_connection_returns_to_pool(self, connection_pool):
        """Test releasing a connection returns it to the pool."""
        conn = connection_pool.get_connection(timeout=1.0)
        initial_stats = connection_pool.get_stats()
        
        connection_pool.release_connection(conn)
        
        assert conn.is_active is False
        final_stats = connection_pool.get_stats()
        assert final_stats.active_connections == initial_stats.active_connections - 1
    
    def test_pool_exhaustion_raises_timeout(self, mock_connection_factory):
        """Test pool exhaustion raises TimeoutError."""
        pool = ConnectionPool(
            pool_type="test",
            min_connections=1,
            max_connections=2,
            connection_factory=mock_connection_factory
        )
        pool.prewarm()
        
        # Acquire all connections
        conn1 = pool.get_connection(timeout=1.0)
        conn2 = pool.get_connection(timeout=1.0)
        
        # Try to acquire one more - should timeout
        with pytest.raises(TimeoutError, match="Connection pool exhausted"):
            pool.get_connection(timeout=0.5)
        
        pool.release_connection(conn1)
        pool.release_connection(conn2)
        pool.close_all()
    
    def test_idle_connection_cleanup(self, mock_connection_factory):
        """Test idle connections are closed after timeout."""
        pool = ConnectionPool(
            pool_type="test",
            min_connections=2,
            max_connections=5,
            idle_timeout=1,  # 1 second timeout
            connection_factory=mock_connection_factory
        )
        pool.prewarm()
        
        # Create an extra connection
        conn = pool.get_connection(timeout=1.0)
        pool.release_connection(conn)
        
        # Wait for idle timeout
        time.sleep(1.5)
        
        # Manually set last_used to simulate idle time
        for c in pool._all_connections.values():
            c.last_used = datetime.now() - timedelta(seconds=2)
        
        # Close idle connections
        closed = pool.close_idle_connections()
        
        # Should close down to minimum
        stats = pool.get_stats()
        assert stats.total_connections >= pool.min_connections
        
        pool.close_all()
    
    def test_pool_stats_tracking(self, connection_pool):
        """Test pool statistics are tracked correctly."""
        # Get initial stats
        stats = connection_pool.get_stats()
        assert stats.total_connections >= 2
        
        # Acquire a connection
        conn = connection_pool.get_connection(timeout=1.0)
        stats = connection_pool.get_stats()
        assert stats.active_connections >= 1
        
        # Release connection
        connection_pool.release_connection(conn)
        stats = connection_pool.get_stats()
        assert stats.idle_connections >= 1
    
    def test_pool_utilization_calculation(self, mock_connection_factory):
        """Test pool utilization percentage is calculated correctly."""
        pool = ConnectionPool(
            pool_type="test",
            min_connections=2,
            max_connections=10,
            connection_factory=mock_connection_factory
        )
        pool.prewarm()
        
        # Acquire 5 connections (50% utilization)
        connections = []
        for _ in range(5):
            conn = pool.get_connection(timeout=1.0)
            connections.append(conn)
        
        stats = pool.get_stats()
        assert stats.utilization_percent == 50.0
        
        # Release all
        for conn in connections:
            pool.release_connection(conn)
        
        pool.close_all()
    
    def test_connection_error_tracking(self, mock_connection_factory):
        """Test connection errors are tracked."""
        # Create pool with factory that fails
        def failing_factory():
            raise Exception("Connection failed")
        
        pool = ConnectionPool(
            pool_type="test",
            min_connections=1,
            max_connections=5,
            connection_factory=failing_factory
        )
        
        # Try to create connection
        conn = pool._create_connection()
        assert conn is None
        
        stats = pool.get_stats()
        assert stats.connection_errors > 0
        
        pool.close_all()


class TestConnectionPoolManager:
    """Test cases for ConnectionPoolManager class."""
    
    def test_manager_initialization(self, mock_connection_factory):
        """Test manager initializes with separate pools."""
        manager = ConnectionPoolManager(
            min_connections=10,
            max_connections=50,
            idle_timeout=300,
            read_connection_factory=mock_connection_factory,
            write_connection_factory=mock_connection_factory
        )
        
        assert manager.min_connections == 10
        assert manager.max_connections == 50
        assert manager.idle_timeout == 300
        assert manager.read_pool is not None
        assert manager.write_pool is not None
        
        manager.close_all()
    
    def test_get_read_connection(self, pool_manager):
        """Test getting a read connection."""
        conn = pool_manager.get_read_connection(timeout=1.0)
        
        assert conn is not None
        assert conn.pool_type == "read"
        assert conn.is_active is True
        
        pool_manager.release_connection(conn)
    
    def test_get_write_connection(self, pool_manager):
        """Test getting a write connection."""
        conn = pool_manager.get_write_connection(timeout=1.0)
        
        assert conn is not None
        assert conn.pool_type == "write"
        assert conn.is_active is True
        
        pool_manager.release_connection(conn)
    
    def test_release_connection_routes_to_correct_pool(self, pool_manager):
        """Test releasing connection routes to correct pool."""
        read_conn = pool_manager.get_read_connection(timeout=1.0)
        write_conn = pool_manager.get_write_connection(timeout=1.0)
        
        # Release both
        pool_manager.release_connection(read_conn)
        pool_manager.release_connection(write_conn)
        
        # Verify they're back in their respective pools
        assert read_conn.is_active is False
        assert write_conn.is_active is False
    
    def test_close_idle_connections_both_pools(self, pool_manager):
        """Test closing idle connections in both pools."""
        # Create extra connections
        read_conn = pool_manager.get_read_connection(timeout=1.0)
        write_conn = pool_manager.get_write_connection(timeout=1.0)
        
        pool_manager.release_connection(read_conn)
        pool_manager.release_connection(write_conn)
        
        # Simulate idle time
        for conn in pool_manager.read_pool._all_connections.values():
            conn.last_used = datetime.now() - timedelta(seconds=20)
        for conn in pool_manager.write_pool._all_connections.values():
            conn.last_used = datetime.now() - timedelta(seconds=20)
        
        # Close idle connections
        closed = pool_manager.close_idle_connections(idle_timeout=10)
        
        # Should have closed some connections
        assert closed >= 0
    
    def test_get_pool_stats_both_pools(self, pool_manager):
        """Test getting statistics for both pools."""
        stats = pool_manager.get_pool_stats()
        
        assert "read" in stats
        assert "write" in stats
        assert isinstance(stats["read"], PoolStats)
        assert isinstance(stats["write"], PoolStats)
    
    def test_prewarm_both_pools(self, mock_connection_factory):
        """Test prewarming creates connections in both pools."""
        manager = ConnectionPoolManager(
            min_connections=3,
            max_connections=10,
            read_connection_factory=mock_connection_factory,
            write_connection_factory=mock_connection_factory
        )
        
        manager.prewarm()
        
        stats = manager.get_pool_stats()
        assert stats["read"].total_connections == 3
        assert stats["write"].total_connections == 3
        
        manager.close_all()
    
    def test_pool_bounds_enforcement(self, pool_manager):
        """Test pool enforces min and max connection bounds."""
        stats = pool_manager.get_pool_stats()
        
        # Should have at least min connections
        assert stats["read"].total_connections >= pool_manager.min_connections
        assert stats["write"].total_connections >= pool_manager.min_connections
        
        # Try to exhaust pool
        read_connections = []
        for _ in range(pool_manager.max_connections):
            try:
                conn = pool_manager.get_read_connection(timeout=0.5)
                read_connections.append(conn)
            except TimeoutError:
                break
        
        # Should not exceed max
        stats = pool_manager.get_pool_stats()
        assert stats["read"].total_connections <= pool_manager.max_connections
        
        # Release all
        for conn in read_connections:
            pool_manager.release_connection(conn)
    
    def test_separate_pool_isolation(self, pool_manager):
        """Test read and write pools are isolated."""
        # Exhaust read pool
        read_connections = []
        for _ in range(pool_manager.max_connections):
            try:
                conn = pool_manager.get_read_connection(timeout=0.5)
                read_connections.append(conn)
            except TimeoutError:
                break
        
        # Write pool should still be available
        write_conn = pool_manager.get_write_connection(timeout=1.0)
        assert write_conn is not None
        
        # Release all
        for conn in read_connections:
            pool_manager.release_connection(conn)
        pool_manager.release_connection(write_conn)
