"""
Connection Pool Monitoring

This module provides monitoring and alerting for database connection pool health.
It tracks connection usage, identifies bottlenecks, and alerts on issues.

Requirements: Production Readiness Audit - Task 2.1
"""

import logging
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

from django.db import connections, connection
from django.core.cache import cache

logger = logging.getLogger(__name__)


@dataclass
class ConnectionPoolStats:
    """Statistics for connection pool monitoring."""
    timestamp: datetime
    database: str
    conn_max_age: int
    active_connections: int
    max_connections: int
    utilization_percent: float
    backend_pid: Optional[int]
    connection_age_seconds: Optional[float]
    query_count: int
    error_count: int
    avg_query_time_ms: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


class ConnectionPoolMonitor:
    """
    Monitor database connection pool health and performance.
    
    Tracks connection usage, identifies bottlenecks, and provides
    alerting for connection pool issues.
    """
    
    # Alert thresholds
    HIGH_UTILIZATION_THRESHOLD = 80  # Alert when > 80% utilized
    CRITICAL_UTILIZATION_THRESHOLD = 95  # Critical alert when > 95%
    
    # Cache keys
    STATS_CACHE_KEY = 'connection_pool_stats'
    STATS_CACHE_TTL = 60  # 1 minute
    
    def __init__(self, database_alias: str = 'default'):
        """
        Initialize connection pool monitor.
        
        Args:
            database_alias: Database alias to monitor (default: 'default')
        """
        self.database_alias = database_alias
        self.query_count = 0
        self.error_count = 0
        self.total_query_time = 0.0
    
    def get_current_stats(self) -> ConnectionPoolStats:
        """
        Get current connection pool statistics.
        
        Returns:
            ConnectionPoolStats object with current metrics
        """
        db_conn = connections[self.database_alias]
        db_settings = db_conn.settings_dict
        
        # Get connection configuration
        conn_max_age = db_settings.get('CONN_MAX_AGE', 0)
        
        # Get active connection info
        backend_pid = None
        connection_age = None
        active_connections = 0
        
        try:
            with connection.cursor() as cursor:
                # Get current backend PID
                cursor.execute("SELECT pg_backend_pid()")
                backend_pid = cursor.fetchone()[0]
                
                # Get number of active connections to this database
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM pg_stat_activity 
                    WHERE datname = %s
                """, [db_settings['NAME']])
                active_connections = cursor.fetchone()[0]
                
                # Get connection age (if available)
                cursor.execute("""
                    SELECT EXTRACT(EPOCH FROM (NOW() - backend_start))
                    FROM pg_stat_activity
                    WHERE pid = pg_backend_pid()
                """)
                connection_age = cursor.fetchone()[0]
                
        except Exception as e:
            logger.error(f"Failed to get connection stats: {e}")
            self.error_count += 1
        
        # Get max_connections from PostgreSQL
        max_connections = self._get_max_connections()
        
        # Calculate utilization
        utilization = (active_connections / max_connections * 100) if max_connections > 0 else 0
        
        # Calculate average query time
        avg_query_time = (
            (self.total_query_time / self.query_count * 1000)
            if self.query_count > 0 else 0
        )
        
        stats = ConnectionPoolStats(
            timestamp=datetime.now(),
            database=db_settings['NAME'],
            conn_max_age=conn_max_age,
            active_connections=active_connections,
            max_connections=max_connections,
            utilization_percent=utilization,
            backend_pid=backend_pid,
            connection_age_seconds=connection_age,
            query_count=self.query_count,
            error_count=self.error_count,
            avg_query_time_ms=avg_query_time
        )
        
        # Cache stats
        cache.set(self.STATS_CACHE_KEY, stats.to_dict(), self.STATS_CACHE_TTL)
        
        return stats
    
    def _get_max_connections(self) -> int:
        """
        Get max_connections setting from PostgreSQL.
        
        Returns:
            Maximum number of connections allowed
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute("SHOW max_connections")
                max_conn = cursor.fetchone()[0]
                return int(max_conn)
        except Exception as e:
            logger.error(f"Failed to get max_connections: {e}")
            return 100  # Default PostgreSQL value
    
    def check_health(self) -> Dict[str, Any]:
        """
        Check connection pool health and return status.
        
        Returns:
            Dictionary with health status and alerts
        """
        stats = self.get_current_stats()
        
        health = {
            'healthy': True,
            'status': 'healthy',
            'alerts': [],
            'stats': stats.to_dict()
        }
        
        # Check for high utilization
        if stats.utilization_percent >= self.CRITICAL_UTILIZATION_THRESHOLD:
            health['healthy'] = False
            health['status'] = 'critical'
            health['alerts'].append({
                'severity': 'critical',
                'message': f'Connection pool at CRITICAL utilization: '
                          f'{stats.utilization_percent:.1f}% '
                          f'({stats.active_connections}/{stats.max_connections})',
                'recommendation': 'Increase max_connections or add connection pooling (pgbouncer)'
            })
        elif stats.utilization_percent >= self.HIGH_UTILIZATION_THRESHOLD:
            health['healthy'] = False
            health['status'] = 'warning'
            health['alerts'].append({
                'severity': 'warning',
                'message': f'Connection pool at HIGH utilization: '
                          f'{stats.utilization_percent:.1f}% '
                          f'({stats.active_connections}/{stats.max_connections})',
                'recommendation': 'Monitor closely and consider scaling'
            })
        
        # Check for connection pooling disabled
        if stats.conn_max_age == 0:
            health['alerts'].append({
                'severity': 'warning',
                'message': 'Connection pooling is DISABLED (CONN_MAX_AGE=0)',
                'recommendation': 'Enable connection pooling by setting CONN_MAX_AGE > 0'
            })
        
        # Check for high error rate
        if stats.query_count > 0:
            error_rate = (stats.error_count / stats.query_count) * 100
            if error_rate > 5:
                health['healthy'] = False
                health['alerts'].append({
                    'severity': 'error',
                    'message': f'High error rate: {error_rate:.1f}% '
                              f'({stats.error_count}/{stats.query_count})',
                    'recommendation': 'Check database logs for connection errors'
                })
        
        return health
    
    def log_stats(self):
        """Log current connection pool statistics."""
        stats = self.get_current_stats()
        
        logger.info(
            f"Connection Pool Stats: "
            f"database={stats.database}, "
            f"active={stats.active_connections}/{stats.max_connections} "
            f"({stats.utilization_percent:.1f}%), "
            f"conn_max_age={stats.conn_max_age}s, "
            f"queries={stats.query_count}, "
            f"errors={stats.error_count}, "
            f"avg_query_time={stats.avg_query_time_ms:.1f}ms"
        )
        
        # Log warnings if needed
        if stats.utilization_percent >= self.HIGH_UTILIZATION_THRESHOLD:
            logger.warning(
                f"High connection pool utilization: {stats.utilization_percent:.1f}%"
            )
    
    def track_query(self, duration: float, success: bool = True):
        """
        Track a query execution for statistics.
        
        Args:
            duration: Query execution time in seconds
            success: Whether the query succeeded
        """
        self.query_count += 1
        self.total_query_time += duration
        
        if not success:
            self.error_count += 1
    
    def get_connection_list(self) -> List[Dict[str, Any]]:
        """
        Get list of all active connections to the database.
        
        Returns:
            List of connection information dictionaries
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        pid,
                        usename,
                        application_name,
                        client_addr,
                        backend_start,
                        state,
                        state_change,
                        query,
                        EXTRACT(EPOCH FROM (NOW() - backend_start)) as age_seconds,
                        EXTRACT(EPOCH FROM (NOW() - state_change)) as state_age_seconds
                    FROM pg_stat_activity
                    WHERE datname = %s
                    ORDER BY backend_start DESC
                """, [connections[self.database_alias].settings_dict['NAME']])
                
                columns = [col[0] for col in cursor.description]
                connections_list = []
                
                for row in cursor.fetchall():
                    conn_info = dict(zip(columns, row))
                    # Convert timestamps to strings
                    if conn_info.get('backend_start'):
                        conn_info['backend_start'] = conn_info['backend_start'].isoformat()
                    if conn_info.get('state_change'):
                        conn_info['state_change'] = conn_info['state_change'].isoformat()
                    connections_list.append(conn_info)
                
                return connections_list
                
        except Exception as e:
            logger.error(f"Failed to get connection list: {e}")
            return []
    
    def get_idle_connections(self, idle_threshold_seconds: int = 300) -> List[Dict[str, Any]]:
        """
        Get list of idle connections that have been idle longer than threshold.
        
        Args:
            idle_threshold_seconds: Threshold in seconds (default: 300 = 5 minutes)
            
        Returns:
            List of idle connection information
        """
        all_connections = self.get_connection_list()
        
        idle_connections = [
            conn for conn in all_connections
            if conn.get('state') == 'idle' and
               conn.get('state_age_seconds', 0) > idle_threshold_seconds
        ]
        
        if idle_connections:
            logger.info(
                f"Found {len(idle_connections)} idle connections "
                f"(idle > {idle_threshold_seconds}s)"
            )
        
        return idle_connections


def get_connection_pool_health() -> Dict[str, Any]:
    """
    Get connection pool health status (convenience function).
    
    Returns:
        Dictionary with health status
    """
    monitor = ConnectionPoolMonitor()
    return monitor.check_health()


def log_connection_pool_stats():
    """Log connection pool statistics (convenience function)."""
    monitor = ConnectionPoolMonitor()
    monitor.log_stats()


# Django management command helper
def print_connection_pool_report():
    """
    Print a detailed connection pool report.
    
    This can be called from a Django management command for monitoring.
    """
    monitor = ConnectionPoolMonitor()
    
    print("\n" + "=" * 70)
    print("CONNECTION POOL HEALTH REPORT")
    print("=" * 70)
    
    # Get health status
    health = monitor.check_health()
    stats = health['stats']
    
    print(f"\nStatus: {health['status'].upper()}")
    print(f"Timestamp: {stats['timestamp']}")
    print(f"\nDatabase: {stats['database']}")
    print(f"Connection Max Age: {stats['conn_max_age']}s")
    print(f"Active Connections: {stats['active_connections']}/{stats['max_connections']}")
    print(f"Utilization: {stats['utilization_percent']:.1f}%")
    print(f"Backend PID: {stats['backend_pid']}")
    print(f"Connection Age: {stats['connection_age_seconds']:.1f}s" if stats['connection_age_seconds'] else "N/A")
    print(f"\nQuery Statistics:")
    print(f"  Total Queries: {stats['query_count']}")
    print(f"  Errors: {stats['error_count']}")
    print(f"  Avg Query Time: {stats['avg_query_time_ms']:.1f}ms")
    
    # Print alerts
    if health['alerts']:
        print(f"\nAlerts ({len(health['alerts'])}):")
        for alert in health['alerts']:
            print(f"  [{alert['severity'].upper()}] {alert['message']}")
            if 'recommendation' in alert:
                print(f"    → {alert['recommendation']}")
    else:
        print("\n✓ No alerts")
    
    # Print active connections
    print(f"\nActive Connections:")
    connections_list = monitor.get_connection_list()
    if connections_list:
        for conn in connections_list[:10]:  # Show first 10
            print(f"  PID {conn['pid']}: {conn['state']} "
                  f"(age: {conn['age_seconds']:.0f}s, "
                  f"user: {conn['usename']})")
        if len(connections_list) > 10:
            print(f"  ... and {len(connections_list) - 10} more")
    else:
        print("  No active connections found")
    
    # Print idle connections
    idle_connections = monitor.get_idle_connections()
    if idle_connections:
        print(f"\nIdle Connections (> 5 minutes): {len(idle_connections)}")
        for conn in idle_connections[:5]:  # Show first 5
            print(f"  PID {conn['pid']}: idle for {conn['state_age_seconds']:.0f}s")
    
    print("\n" + "=" * 70 + "\n")


if __name__ == '__main__':
    # Run report when executed directly
    print_connection_pool_report()
