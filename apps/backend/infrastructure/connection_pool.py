"""
Connection Pool Manager for database connections.

This module provides efficient connection pooling with separate pools for
read and write operations, implementing bounds enforcement, idle connection
cleanup, and comprehensive statistics tracking.
"""

import logging
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from queue import Queue, Empty, Full

from infrastructure.models import PoolStats


logger = logging.getLogger(__name__)


@dataclass
class Connection:
    """Represents a database connection with metadata."""
    conn_id: str
    connection: Any  # Actual database connection object
    created_at: datetime
    last_used: datetime
    is_active: bool = False
    pool_type: str = "read"  # "read" or "write"


class ConnectionPool:
    """
    Manages a pool of database connections with configurable bounds.
    
    Implements connection acquisition, release, idle cleanup, and statistics tracking.
    """
    
    def __init__(
        self,
        pool_type: str,
        min_connections: int = 10,
        max_connections: int = 50,
        idle_timeout: int = 300,
        connection_factory=None
    ):
        """
        Initialize connection pool.
        
        Args:
            pool_type: Type of pool ("read" or "write")
            min_connections: Minimum number of connections to maintain
            max_connections: Maximum number of connections allowed
            idle_timeout: Seconds before idle connection is closed
            connection_factory: Callable that creates new connections
        """
        self.pool_type = pool_type
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.idle_timeout = idle_timeout
        self.connection_factory = connection_factory
        
        # Connection storage
        self._available: Queue = Queue(maxsize=max_connections)
        self._all_connections: Dict[str, Connection] = {}
        self._lock = threading.RLock()
        
        # Statistics
        self._total_created = 0
        self._connection_errors = 0
        self._total_wait_time = 0.0
        self._wait_count = 0
        
        logger.info(
            f"Initialized {pool_type} pool: min={min_connections}, "
            f"max={max_connections}, idle_timeout={idle_timeout}s"
        )
    
    def get_connection(self, timeout: float = 5.0) -> Connection:
        """
        Acquire a connection from the pool.
        
        Args:
            timeout: Maximum time to wait for a connection (seconds)
            
        Returns:
            Connection object
            
        Raises:
            TimeoutError: If no connection available within timeout
        """
        start_time = time.time()
        
        try:
            # Try to get an available connection
            conn = self._available.get(timeout=timeout)
            conn.is_active = True
            conn.last_used = datetime.now()
            
            wait_time = time.time() - start_time
            with self._lock:
                self._total_wait_time += wait_time
                self._wait_count += 1
            
            logger.debug(f"Acquired connection {conn.conn_id} from {self.pool_type} pool")
            return conn
            
        except Empty:
            # No available connection, try to create new one if under max
            with self._lock:
                if len(self._all_connections) < self.max_connections:
                    conn = self._create_connection()
                    if conn:
                        conn.is_active = True
                        wait_time = time.time() - start_time
                        self._total_wait_time += wait_time
                        self._wait_count += 1
                        return conn
            
            # Pool exhausted
            wait_time = time.time() - start_time
            with self._lock:
                self._total_wait_time += wait_time
                self._wait_count += 1
            
            raise TimeoutError(
                f"Connection pool exhausted: {self.pool_type} pool has "
                f"{len(self._all_connections)} connections (max: {self.max_connections})"
            )
    
    def release_connection(self, conn: Connection) -> None:
        """
        Return a connection to the pool.
        
        Args:
            conn: Connection to release
        """
        if conn.conn_id not in self._all_connections:
            logger.warning(f"Attempted to release unknown connection {conn.conn_id}")
            return
        
        conn.is_active = False
        conn.last_used = datetime.now()
        
        try:
            self._available.put_nowait(conn)
            logger.debug(f"Released connection {conn.conn_id} to {self.pool_type} pool")
        except Full:
            # Pool is full, close this connection
            logger.warning(f"Pool full, closing connection {conn.conn_id}")
            self._close_connection(conn)
    
    def close_idle_connections(self) -> int:
        """
        Close connections that have been idle longer than idle_timeout.
        
        Returns:
            Number of connections closed
        """
        closed_count = 0
        now = datetime.now()
        connections_to_close = []
        
        with self._lock:
            # Find idle connections
            for conn_id, conn in list(self._all_connections.items()):
                if not conn.is_active:
                    idle_time = (now - conn.last_used).total_seconds()
                    if idle_time > self.idle_timeout:
                        # Don't close if we're at minimum
                        if len(self._all_connections) - closed_count > self.min_connections:
                            connections_to_close.append(conn)
                            closed_count += 1
        
        # Close connections outside the lock
        for conn in connections_to_close:
            self._close_connection(conn)
            logger.debug(
                f"Closed idle connection {conn.conn_id} from {self.pool_type} pool "
                f"(idle > {self.idle_timeout}s)"
            )
        
        if closed_count > 0:
            logger.info(f"Closed {closed_count} idle connections from {self.pool_type} pool")
        
        return closed_count
    
    def get_stats(self) -> PoolStats:
        """
        Get current pool statistics.
        
        Returns:
            PoolStats object with current metrics
        """
        with self._lock:
            total = len(self._all_connections)
            active = sum(1 for c in self._all_connections.values() if c.is_active)
            idle = total - active
            utilization = (active / self.max_connections * 100) if self.max_connections > 0 else 0
            avg_wait = (self._total_wait_time / self._wait_count * 1000) if self._wait_count > 0 else 0
            
            stats = PoolStats(
                total_connections=total,
                active_connections=active,
                idle_connections=idle,
                utilization_percent=utilization,
                wait_time_avg=avg_wait,
                connection_errors=self._connection_errors
            )
            
            # Log warning if utilization exceeds 80%
            if utilization > 80:
                logger.warning(
                    f"{self.pool_type.capitalize()} pool utilization at {utilization:.1f}% "
                    f"({active}/{self.max_connections} connections active)"
                )
            
            return stats
    
    def _create_connection(self) -> Optional[Connection]:
        """
        Create a new connection.
        
        Returns:
            New Connection object or None if creation failed
        """
        if self.connection_factory is None:
            logger.error("No connection factory configured")
            self._connection_errors += 1
            return None
        
        try:
            conn_id = f"{self.pool_type}_{self._total_created}"
            db_conn = self.connection_factory()
            
            conn = Connection(
                conn_id=conn_id,
                connection=db_conn,
                created_at=datetime.now(),
                last_used=datetime.now(),
                is_active=False,
                pool_type=self.pool_type
            )
            
            self._all_connections[conn_id] = conn
            self._total_created += 1
            
            logger.debug(f"Created new connection {conn_id} for {self.pool_type} pool")
            return conn
            
        except Exception as e:
            logger.error(f"Failed to create connection for {self.pool_type} pool: {e}")
            self._connection_errors += 1
            return None
    
    def _close_connection(self, conn: Connection) -> None:
        """
        Close and remove a connection from the pool.
        
        Args:
            conn: Connection to close
        """
        try:
            # Remove from available queue if present
            temp_queue = Queue(maxsize=self.max_connections)
            while not self._available.empty():
                try:
                    c = self._available.get_nowait()
                    if c.conn_id != conn.conn_id:
                        temp_queue.put_nowait(c)
                except Empty:
                    break
            
            # Restore queue
            while not temp_queue.empty():
                try:
                    self._available.put_nowait(temp_queue.get_nowait())
                except (Empty, Full):
                    break
            
            # Close actual connection
            if hasattr(conn.connection, 'close'):
                conn.connection.close()
            
            # Remove from tracking
            with self._lock:
                if conn.conn_id in self._all_connections:
                    del self._all_connections[conn.conn_id]
            
        except Exception as e:
            logger.error(f"Error closing connection {conn.conn_id}: {e}")
    
    def prewarm(self) -> None:
        """Pre-create minimum number of connections."""
        with self._lock:
            current_count = len(self._all_connections)
            needed = self.min_connections - current_count
            
            if needed <= 0:
                return
            
            logger.info(f"Pre-warming {self.pool_type} pool with {needed} connections")
            
            for _ in range(needed):
                conn = self._create_connection()
                if conn:
                    try:
                        self._available.put_nowait(conn)
                    except Full:
                        logger.warning(f"Could not add connection to {self.pool_type} pool (full)")
                        break
    
    def close_all(self) -> None:
        """Close all connections in the pool."""
        with self._lock:
            connections = list(self._all_connections.values())
        
        for conn in connections:
            self._close_connection(conn)
        
        logger.info(f"Closed all connections in {self.pool_type} pool")


class ConnectionPoolManager:
    """
    Manages separate connection pools for read and write operations.
    
    Provides unified interface for connection management with automatic
    pool selection based on operation type.
    """
    
    def __init__(
        self,
        min_connections: int = 10,
        max_connections: int = 50,
        idle_timeout: int = 300,
        read_connection_factory=None,
        write_connection_factory=None
    ):
        """
        Initialize connection pool manager.
        
        Args:
            min_connections: Minimum connections per pool
            max_connections: Maximum connections per pool
            idle_timeout: Idle timeout in seconds
            read_connection_factory: Factory for read connections
            write_connection_factory: Factory for write connections
        """
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.idle_timeout = idle_timeout
        
        # Create separate pools
        self.read_pool = ConnectionPool(
            pool_type="read",
            min_connections=min_connections,
            max_connections=max_connections,
            idle_timeout=idle_timeout,
            connection_factory=read_connection_factory
        )
        
        self.write_pool = ConnectionPool(
            pool_type="write",
            min_connections=min_connections,
            max_connections=max_connections,
            idle_timeout=idle_timeout,
            connection_factory=write_connection_factory
        )
        
        logger.info(
            f"ConnectionPoolManager initialized with min={min_connections}, "
            f"max={max_connections}, idle_timeout={idle_timeout}s"
        )
    
    def get_read_connection(self, timeout: float = 5.0) -> Connection:
        """
        Get a connection from the read pool.
        
        Args:
            timeout: Maximum wait time in seconds
            
        Returns:
            Connection from read pool
        """
        return self.read_pool.get_connection(timeout=timeout)
    
    def get_write_connection(self, timeout: float = 5.0) -> Connection:
        """
        Get a connection from the write pool.
        
        Args:
            timeout: Maximum wait time in seconds
            
        Returns:
            Connection from write pool
        """
        return self.write_pool.get_connection(timeout=timeout)
    
    def release_connection(self, conn: Connection) -> None:
        """
        Return a connection to its appropriate pool.
        
        Args:
            conn: Connection to release
        """
        if conn.pool_type == "read":
            self.read_pool.release_connection(conn)
        elif conn.pool_type == "write":
            self.write_pool.release_connection(conn)
        else:
            logger.error(f"Unknown pool type: {conn.pool_type}")
    
    def close_idle_connections(self, idle_timeout: Optional[int] = None) -> int:
        """
        Close idle connections in both pools.
        
        Args:
            idle_timeout: Override default idle timeout (optional)
            
        Returns:
            Total number of connections closed
        """
        if idle_timeout is not None:
            # Temporarily override timeout
            old_read_timeout = self.read_pool.idle_timeout
            old_write_timeout = self.write_pool.idle_timeout
            self.read_pool.idle_timeout = idle_timeout
            self.write_pool.idle_timeout = idle_timeout
        
        read_closed = self.read_pool.close_idle_connections()
        write_closed = self.write_pool.close_idle_connections()
        
        if idle_timeout is not None:
            # Restore original timeouts
            self.read_pool.idle_timeout = old_read_timeout
            self.write_pool.idle_timeout = old_write_timeout
        
        total_closed = read_closed + write_closed
        if total_closed > 0:
            logger.info(
                f"Closed {total_closed} idle connections "
                f"(read: {read_closed}, write: {write_closed})"
            )
        
        return total_closed
    
    def get_pool_stats(self) -> Dict[str, PoolStats]:
        """
        Get statistics for both pools.
        
        Returns:
            Dictionary with 'read' and 'write' pool statistics
        """
        return {
            "read": self.read_pool.get_stats(),
            "write": self.write_pool.get_stats()
        }
    
    def prewarm(self) -> None:
        """Pre-warm both pools with minimum connections."""
        logger.info("Pre-warming connection pools")
        self.read_pool.prewarm()
        self.write_pool.prewarm()
    
    def close_all(self) -> None:
        """Close all connections in both pools."""
        logger.info("Closing all connection pools")
        self.read_pool.close_all()
        self.write_pool.close_all()
