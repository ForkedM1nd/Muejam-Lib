"""
APM Database Query Tracking

This module provides utilities for tracking database query performance.
Implements Requirement 14.3: Track database query performance and identify slow queries.
"""

import time
from functools import wraps
from typing import Callable
from infrastructure.apm_config import PerformanceMonitor, APMConfig


class DatabaseQueryTracker:
    """
    Utility class for tracking database query performance.
    
    Tracks:
    - Query execution time
    - Slow queries (>100ms)
    - Query types (SELECT, INSERT, UPDATE, DELETE)
    - Rows returned
    """
    
    @staticmethod
    def track_query(query: str, duration_ms: float, rows_returned: int = 0):
        """
        Track a database query.
        
        Args:
            query: SQL query (will be obfuscated)
            duration_ms: Query duration in milliseconds
            rows_returned: Number of rows returned
        """
        if not APMConfig.is_enabled():
            return
        
        # Obfuscate query (remove values)
        obfuscated_query = DatabaseQueryTracker._obfuscate_query(query)
        
        # Track query performance
        PerformanceMonitor.track_database_query(
            query=obfuscated_query,
            duration_ms=duration_ms,
            rows_returned=rows_returned
        )
    
    @staticmethod
    def _obfuscate_query(query: str) -> str:
        """
        Obfuscate SQL query by removing sensitive values.
        
        Args:
            query: Original SQL query
        
        Returns:
            Obfuscated query with values replaced by placeholders
        """
        # Simple obfuscation - replace values with ?
        # In production, use a proper SQL parser
        import re
        
        # Remove string literals
        query = re.sub(r"'[^']*'", "'?'", query)
        
        # Remove numbers
        query = re.sub(r'\b\d+\b', '?', query)
        
        return query


def track_database_query(func: Callable) -> Callable:
    """
    Decorator to track database query performance.
    
    Example:
        @track_database_query
        def get_user_by_id(user_id):
            return User.objects.get(id=user_id)
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not APMConfig.is_enabled():
            return func(*args, **kwargs)
        
        start_time = time.time()
        result = func(*args, **kwargs)
        duration_ms = (time.time() - start_time) * 1000
        
        # Track query
        DatabaseQueryTracker.track_query(
            query=func.__name__,
            duration_ms=duration_ms,
            rows_returned=1 if result else 0
        )
        
        return result
    
    return wrapper


# Export public API
__all__ = [
    'DatabaseQueryTracker',
    'track_database_query',
]
