"""
Workload Isolator for query routing.

This module provides intelligent query routing to separate read and write
workloads, with support for priority-based routing and replica lag fallback.
"""

import logging
import re
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from infrastructure.models import Priority, QueryType, ReplicaInfo


logger = logging.getLogger(__name__)


@dataclass
class Query:
    """Represents a database query with metadata."""
    text: str
    params: Dict[str, Any]
    query_type: Optional[QueryType] = None
    priority: Priority = Priority.NORMAL


@dataclass
class DatabaseTarget:
    """Represents the target database for query execution."""
    target_type: str  # "primary" or "replica"
    host: str
    port: int
    reason: str  # Explanation for routing decision


class WorkloadIsolator:
    """
    Routes queries to appropriate database instances based on operation type,
    priority, and replica health.
    
    Implements workload isolation by:
    - Routing writes to primary database
    - Routing reads to replica instances
    - Using dedicated connections for critical operations
    - Falling back to primary when replica lag is high
    """
    
    # SQL patterns for query type detection
    WRITE_PATTERNS = [
        r'^\s*INSERT\s+INTO',
        r'^\s*UPDATE\s+',
        r'^\s*DELETE\s+FROM',
        r'^\s*CREATE\s+',
        r'^\s*ALTER\s+',
        r'^\s*DROP\s+',
        r'^\s*TRUNCATE\s+',
        r'^\s*REPLACE\s+INTO',
    ]
    
    READ_PATTERNS = [
        r'^\s*SELECT\s+',
        r'^\s*WITH\s+.*\s+SELECT\s+',  # CTE with SELECT
        r'^\s*SHOW\s+',
        r'^\s*DESCRIBE\s+',
        r'^\s*EXPLAIN\s+',
    ]
    
    def __init__(
        self,
        primary_host: str,
        primary_port: int,
        replicas: List[ReplicaInfo],
        max_replica_lag: float = 5.0,
        lag_check_callback=None
    ):
        """
        Initialize workload isolator.
        
        Args:
            primary_host: Primary database host
            primary_port: Primary database port
            replicas: List of replica instances
            max_replica_lag: Maximum acceptable replica lag in seconds
            lag_check_callback: Optional callback to check replica lag
        """
        self.primary_host = primary_host
        self.primary_port = primary_port
        self.replicas = replicas
        self.max_replica_lag = max_replica_lag
        self.lag_check_callback = lag_check_callback
        
        # Compile regex patterns for efficiency
        self._write_patterns = [re.compile(p, re.IGNORECASE) for p in self.WRITE_PATTERNS]
        self._read_patterns = [re.compile(p, re.IGNORECASE) for p in self.READ_PATTERNS]
        
        logger.info(
            f"WorkloadIsolator initialized: primary={primary_host}:{primary_port}, "
            f"replicas={len(replicas)}, max_lag={max_replica_lag}s"
        )
    
    def route_query(
        self,
        query: Query,
        priority: Priority = Priority.NORMAL
    ) -> DatabaseTarget:
        """
        Determine which database instance should handle the query.
        
        Args:
            query: Query object to route
            priority: Query priority level
            
        Returns:
            DatabaseTarget indicating where to execute the query
        """
        # Detect query type if not already set
        if query.query_type is None:
            query.query_type = self._detect_query_type(query.text)
        
        # Write operations always go to primary
        if self._is_write_operation(query.query_type):
            return DatabaseTarget(
                target_type="primary",
                host=self.primary_host,
                port=self.primary_port,
                reason="Write operation must go to primary"
            )
        
        # Critical operations use primary for consistency
        if priority == Priority.CRITICAL:
            return DatabaseTarget(
                target_type="primary",
                host=self.primary_host,
                port=self.primary_port,
                reason="Critical operation routed to primary for consistency"
            )
        
        # Read operations can go to replicas
        if self._is_read_operation(query.query_type):
            # Try to find a healthy replica with acceptable lag
            replica = self._select_healthy_replica()
            
            if replica:
                return DatabaseTarget(
                    target_type="replica",
                    host=replica.host,
                    port=replica.port,
                    reason=f"Read operation routed to replica (lag: {replica.replication_lag:.2f}s)"
                )
            else:
                # No healthy replicas, fall back to primary
                return DatabaseTarget(
                    target_type="primary",
                    host=self.primary_host,
                    port=self.primary_port,
                    reason="No healthy replicas available, falling back to primary"
                )
        
        # Unknown query type, route to primary for safety
        return DatabaseTarget(
            target_type="primary",
            host=self.primary_host,
            port=self.primary_port,
            reason="Unknown query type, routing to primary for safety"
        )
    
    def check_replica_lag(self, replica: str) -> float:
        """
        Check replication lag for a specific replica.
        
        Args:
            replica: Replica identifier (host:port format)
            
        Returns:
            Replication lag in seconds
        """
        if self.lag_check_callback:
            try:
                lag = self.lag_check_callback(replica)
                logger.debug(f"Replica {replica} lag: {lag:.2f}s")
                return lag
            except Exception as e:
                logger.error(f"Failed to check lag for replica {replica}: {e}")
                # Return high lag to trigger fallback
                return float('inf')
        
        # If no callback, check replica info
        for r in self.replicas:
            if f"{r.host}:{r.port}" == replica:
                return r.replication_lag
        
        logger.warning(f"Replica {replica} not found in replica list")
        return float('inf')
    
    def should_route_to_primary(
        self,
        query: Query,
        replica_lag: float
    ) -> bool:
        """
        Decide if query should go to primary despite being a read.
        
        Args:
            query: Query to evaluate
            replica_lag: Current replica lag in seconds
            
        Returns:
            True if query should go to primary, False otherwise
        """
        # Always route writes to primary
        if query.query_type and self._is_write_operation(query.query_type):
            return True
        
        # Route to primary if replica lag exceeds threshold
        if replica_lag > self.max_replica_lag:
            logger.warning(
                f"Replica lag ({replica_lag:.2f}s) exceeds threshold "
                f"({self.max_replica_lag}s), routing to primary"
            )
            return True
        
        # Route critical operations to primary
        if query.priority == Priority.CRITICAL:
            return True
        
        return False
    
    def _detect_query_type(self, query_text: str) -> QueryType:
        """
        Detect the type of SQL query.
        
        Args:
            query_text: SQL query string
            
        Returns:
            QueryType enum value
        """
        # Normalize whitespace
        normalized = ' '.join(query_text.split())
        
        # Check for write operations
        for pattern in self._write_patterns:
            if pattern.match(normalized):
                if 'INSERT' in normalized.upper():
                    return QueryType.INSERT
                elif 'UPDATE' in normalized.upper():
                    return QueryType.UPDATE
                elif 'DELETE' in normalized.upper():
                    return QueryType.DELETE
                else:
                    return QueryType.OTHER
        
        # Check for read operations
        for pattern in self._read_patterns:
            if pattern.match(normalized):
                return QueryType.SELECT
        
        # Default to OTHER for unknown patterns
        logger.debug(f"Could not detect query type for: {query_text[:50]}...")
        return QueryType.OTHER
    
    def _is_write_operation(self, query_type: QueryType) -> bool:
        """
        Check if query type is a write operation.
        
        Args:
            query_type: QueryType to check
            
        Returns:
            True if write operation, False otherwise
        """
        return query_type in (QueryType.INSERT, QueryType.UPDATE, QueryType.DELETE)
    
    def _is_read_operation(self, query_type: QueryType) -> bool:
        """
        Check if query type is a read operation.
        
        Args:
            query_type: QueryType to check
            
        Returns:
            True if read operation, False otherwise
        """
        return query_type == QueryType.SELECT
    
    def _select_healthy_replica(self) -> Optional[ReplicaInfo]:
        """
        Select a healthy replica with acceptable lag.
        
        Returns:
            ReplicaInfo for selected replica, or None if no healthy replicas
        """
        healthy_replicas = []
        
        for replica in self.replicas:
            # Check if replica is healthy
            if not replica.is_healthy:
                logger.debug(f"Skipping unhealthy replica {replica.host}:{replica.port}")
                continue
            
            # Check replication lag
            lag = replica.replication_lag
            if self.lag_check_callback:
                # Use callback for real-time lag check
                lag = self.check_replica_lag(f"{replica.host}:{replica.port}")
                replica.replication_lag = lag
            
            if lag <= self.max_replica_lag:
                healthy_replicas.append(replica)
            else:
                logger.debug(
                    f"Skipping replica {replica.host}:{replica.port} "
                    f"due to high lag ({lag:.2f}s > {self.max_replica_lag}s)"
                )
        
        if not healthy_replicas:
            logger.warning("No healthy replicas available with acceptable lag")
            return None
        
        # Select replica with lowest lag
        selected = min(healthy_replicas, key=lambda r: r.replication_lag)
        logger.debug(
            f"Selected replica {selected.host}:{selected.port} "
            f"(lag: {selected.replication_lag:.2f}s)"
        )
        
        return selected
    
    def update_replica_info(self, replicas: List[ReplicaInfo]) -> None:
        """
        Update the list of available replicas.
        
        Args:
            replicas: New list of replica instances
        """
        self.replicas = replicas
        logger.info(f"Updated replica list: {len(replicas)} replicas")
    
    def get_replica_status(self) -> List[Dict[str, Any]]:
        """
        Get status of all replicas.
        
        Returns:
            List of replica status dictionaries
        """
        status = []
        for replica in self.replicas:
            status.append({
                "host": replica.host,
                "port": replica.port,
                "is_healthy": replica.is_healthy,
                "replication_lag": replica.replication_lag,
                "cpu_utilization": replica.cpu_utilization,
                "avg_response_time": replica.avg_response_time,
                "weight": replica.weight
            })
        return status
