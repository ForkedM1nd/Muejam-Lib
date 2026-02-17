"""
Metrics Collection and Exposure System

This module implements comprehensive metrics collection for database and cache
operations, with support for Prometheus/Grafana integration and threshold-based
alerting.

Requirements: 10.1, 10.2, 10.3, 10.4
"""

import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from threading import Lock
from collections import deque
import logging

logger = logging.getLogger(__name__)


@dataclass
class MetricValue:
    """A single metric value with timestamp."""
    value: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ThresholdConfig:
    """Configuration for metric threshold monitoring."""
    metric_name: str
    threshold: float
    comparison: str  # 'gt', 'lt', 'gte', 'lte', 'eq'
    window_seconds: int = 60
    alert_callback: Optional[Callable[[str, float, float], None]] = None


@dataclass
class DatabaseMetrics:
    """Database performance metrics."""
    query_count: int = 0
    total_latency_ms: float = 0.0
    min_latency_ms: float = float('inf')
    max_latency_ms: float = 0.0
    error_count: int = 0
    slow_query_count: int = 0
    
    @property
    def avg_latency_ms(self) -> float:
        """Calculate average query latency."""
        return self.total_latency_ms / self.query_count if self.query_count > 0 else 0.0
    
    @property
    def error_rate(self) -> float:
        """Calculate error rate as percentage."""
        total = self.query_count + self.error_count
        return (self.error_count / total * 100) if total > 0 else 0.0
    
    @property
    def throughput_qps(self) -> float:
        """Queries per second (calculated externally based on time window)."""
        return 0.0  # Calculated by MetricsCollector


@dataclass
class CacheMetrics:
    """Cache performance metrics."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    sets: int = 0
    deletes: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate as percentage."""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0
    
    @property
    def miss_rate(self) -> float:
        """Calculate cache miss rate as percentage."""
        total = self.hits + self.misses
        return (self.misses / total * 100) if total > 0 else 0.0
    
    @property
    def eviction_rate(self) -> float:
        """Calculate eviction rate as percentage of sets."""
        return (self.evictions / self.sets * 100) if self.sets > 0 else 0.0


class MetricsCollector:
    """
    Central metrics collection and exposure system.
    
    Collects metrics from database and cache operations, maintains time-series
    data, monitors thresholds, and exposes metrics for Prometheus/Grafana.
    
    Requirements: 10.1, 10.2, 10.3, 10.4
    """
    
    def __init__(self, retention_seconds: int = 3600):
        """
        Initialize metrics collector.
        
        Args:
            retention_seconds: How long to retain time-series data
        """
        self.retention_seconds = retention_seconds
        self._lock = Lock()
        
        # Current aggregated metrics
        self.db_metrics = DatabaseMetrics()
        self.cache_metrics = CacheMetrics()
        
        # Time-series data for windowed calculations
        self._db_latencies: deque = deque()
        self._db_errors: deque = deque()
        self._db_queries: deque = deque()
        self._cache_operations: deque = deque()
        
        # Threshold monitoring
        self._thresholds: List[ThresholdConfig] = []
        
        # Metrics start time for throughput calculation
        self._start_time = time.time()
        
        logger.info("MetricsCollector initialized with %ds retention", retention_seconds)
    
    def record_query(self, latency_ms: float, is_error: bool = False, is_slow: bool = False) -> None:
        """
        Record a database query execution.
        
        Args:
            latency_ms: Query execution time in milliseconds
            is_error: Whether the query resulted in an error
            is_slow: Whether the query exceeded slow query threshold
        
        Requirements: 10.1
        """
        with self._lock:
            now = datetime.now()
            
            if is_error:
                self.db_metrics.error_count += 1
                self._db_errors.append(MetricValue(1.0, now))
            else:
                self.db_metrics.query_count += 1
                self.db_metrics.total_latency_ms += latency_ms
                self.db_metrics.min_latency_ms = min(self.db_metrics.min_latency_ms, latency_ms)
                self.db_metrics.max_latency_ms = max(self.db_metrics.max_latency_ms, latency_ms)
                
                if is_slow:
                    self.db_metrics.slow_query_count += 1
                
                self._db_latencies.append(MetricValue(latency_ms, now))
                self._db_queries.append(MetricValue(1.0, now))
            
            # Clean old data
            self._cleanup_old_data()
            
            # Check thresholds
            self._check_thresholds()
    
    def record_cache_hit(self) -> None:
        """
        Record a cache hit.
        
        Requirements: 10.2
        """
        with self._lock:
            self.cache_metrics.hits += 1
            self._cache_operations.append(MetricValue(1.0, datetime.now()))
            self._cleanup_old_data()
    
    def record_cache_miss(self) -> None:
        """
        Record a cache miss.
        
        Requirements: 10.2
        """
        with self._lock:
            self.cache_metrics.misses += 1
            self._cache_operations.append(MetricValue(0.0, datetime.now()))
            self._cleanup_old_data()
    
    def record_cache_set(self) -> None:
        """
        Record a cache set operation.
        
        Requirements: 10.2
        """
        with self._lock:
            self.cache_metrics.sets += 1
    
    def record_cache_eviction(self) -> None:
        """
        Record a cache eviction.
        
        Requirements: 10.2
        """
        with self._lock:
            self.cache_metrics.evictions += 1
    
    def record_cache_delete(self) -> None:
        """
        Record a cache delete operation.
        
        Requirements: 10.2
        """
        with self._lock:
            self.cache_metrics.deletes += 1
    
    def get_database_metrics(self) -> Dict[str, Any]:
        """
        Get current database metrics.
        
        Returns:
            Dictionary containing database metrics including latency, throughput, and error rates
        
        Requirements: 10.1
        """
        with self._lock:
            elapsed_seconds = time.time() - self._start_time
            throughput = self.db_metrics.query_count / elapsed_seconds if elapsed_seconds > 0 else 0.0
            
            return {
                'query_count': self.db_metrics.query_count,
                'avg_latency_ms': self.db_metrics.avg_latency_ms,
                'min_latency_ms': self.db_metrics.min_latency_ms if self.db_metrics.min_latency_ms != float('inf') else 0.0,
                'max_latency_ms': self.db_metrics.max_latency_ms,
                'error_count': self.db_metrics.error_count,
                'error_rate_percent': self.db_metrics.error_rate,
                'slow_query_count': self.db_metrics.slow_query_count,
                'throughput_qps': throughput,
            }
    
    def get_cache_metrics(self) -> Dict[str, Any]:
        """
        Get current cache metrics.
        
        Returns:
            Dictionary containing cache metrics including hit rate, miss rate, and eviction rate
        
        Requirements: 10.2
        """
        with self._lock:
            return {
                'hits': self.cache_metrics.hits,
                'misses': self.cache_metrics.misses,
                'hit_rate_percent': self.cache_metrics.hit_rate,
                'miss_rate_percent': self.cache_metrics.miss_rate,
                'evictions': self.cache_metrics.evictions,
                'eviction_rate_percent': self.cache_metrics.eviction_rate,
                'sets': self.cache_metrics.sets,
                'deletes': self.cache_metrics.deletes,
            }
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """
        Get all metrics in a single call.
        
        Returns:
            Dictionary containing both database and cache metrics
        
        Requirements: 10.1, 10.2
        """
        return {
            'database': self.get_database_metrics(),
            'cache': self.get_cache_metrics(),
            'timestamp': datetime.now().isoformat(),
        }
    
    def add_threshold(self, config: ThresholdConfig) -> None:
        """
        Add a threshold for monitoring.
        
        Args:
            config: Threshold configuration
        
        Requirements: 10.4
        """
        with self._lock:
            self._thresholds.append(config)
            logger.info("Added threshold: %s %s %.2f", config.metric_name, config.comparison, config.threshold)
    
    def remove_threshold(self, metric_name: str) -> None:
        """
        Remove a threshold by metric name.
        
        Args:
            metric_name: Name of the metric to stop monitoring
        """
        with self._lock:
            self._thresholds = [t for t in self._thresholds if t.metric_name != metric_name]
            logger.info("Removed threshold for: %s", metric_name)
    
    def _check_thresholds(self) -> None:
        """
        Check all configured thresholds and trigger alerts if breached.
        
        Requirements: 10.4
        """
        current_metrics = {
            'avg_latency_ms': self.db_metrics.avg_latency_ms,
            'error_rate_percent': self.db_metrics.error_rate,
            'cache_hit_rate_percent': self.cache_metrics.hit_rate,
            'cache_miss_rate_percent': self.cache_metrics.miss_rate,
        }
        
        for threshold in self._thresholds:
            if threshold.metric_name not in current_metrics:
                continue
            
            current_value = current_metrics[threshold.metric_name]
            breached = self._is_threshold_breached(current_value, threshold.threshold, threshold.comparison)
            
            if breached and threshold.alert_callback:
                try:
                    threshold.alert_callback(threshold.metric_name, current_value, threshold.threshold)
                except Exception as e:
                    logger.error("Error in threshold alert callback: %s", e)
    
    def _is_threshold_breached(self, value: float, threshold: float, comparison: str) -> bool:
        """
        Check if a value breaches a threshold.
        
        Args:
            value: Current metric value
            threshold: Threshold value
            comparison: Comparison operator ('gt', 'lt', 'gte', 'lte', 'eq')
        
        Returns:
            True if threshold is breached
        """
        if comparison == 'gt':
            return value > threshold
        elif comparison == 'gte':
            return value >= threshold
        elif comparison == 'lt':
            return value < threshold
        elif comparison == 'lte':
            return value <= threshold
        elif comparison == 'eq':
            return value == threshold
        return False
    
    def _cleanup_old_data(self) -> None:
        """
        Remove time-series data older than retention period.
        """
        cutoff = datetime.now() - timedelta(seconds=self.retention_seconds)
        
        self._db_latencies = deque(
            [m for m in self._db_latencies if m.timestamp > cutoff]
        )
        self._db_errors = deque(
            [m for m in self._db_errors if m.timestamp > cutoff]
        )
        self._db_queries = deque(
            [m for m in self._db_queries if m.timestamp > cutoff]
        )
        self._cache_operations = deque(
            [m for m in self._cache_operations if m.timestamp > cutoff]
        )
    
    def reset_metrics(self) -> None:
        """
        Reset all metrics to initial state.
        
        Useful for testing or periodic resets.
        """
        with self._lock:
            self.db_metrics = DatabaseMetrics()
            self.cache_metrics = CacheMetrics()
            self._db_latencies.clear()
            self._db_errors.clear()
            self._db_queries.clear()
            self._cache_operations.clear()
            self._start_time = time.time()
            logger.info("Metrics reset")
    
    def export_prometheus_format(self) -> str:
        """
        Export metrics in Prometheus text format.
        
        Returns:
            Metrics formatted for Prometheus scraping
        
        Requirements: 10.1, 10.2
        """
        db_metrics = self.get_database_metrics()
        cache_metrics = self.get_cache_metrics()
        
        lines = [
            "# HELP db_query_count Total number of database queries",
            "# TYPE db_query_count counter",
            f"db_query_count {db_metrics['query_count']}",
            "",
            "# HELP db_avg_latency_ms Average query latency in milliseconds",
            "# TYPE db_avg_latency_ms gauge",
            f"db_avg_latency_ms {db_metrics['avg_latency_ms']:.2f}",
            "",
            "# HELP db_error_count Total number of database errors",
            "# TYPE db_error_count counter",
            f"db_error_count {db_metrics['error_count']}",
            "",
            "# HELP db_error_rate_percent Database error rate as percentage",
            "# TYPE db_error_rate_percent gauge",
            f"db_error_rate_percent {db_metrics['error_rate_percent']:.2f}",
            "",
            "# HELP db_throughput_qps Database queries per second",
            "# TYPE db_throughput_qps gauge",
            f"db_throughput_qps {db_metrics['throughput_qps']:.2f}",
            "",
            "# HELP cache_hits Total number of cache hits",
            "# TYPE cache_hits counter",
            f"cache_hits {cache_metrics['hits']}",
            "",
            "# HELP cache_misses Total number of cache misses",
            "# TYPE cache_misses counter",
            f"cache_misses {cache_metrics['misses']}",
            "",
            "# HELP cache_hit_rate_percent Cache hit rate as percentage",
            "# TYPE cache_hit_rate_percent gauge",
            f"cache_hit_rate_percent {cache_metrics['hit_rate_percent']:.2f}",
            "",
            "# HELP cache_evictions Total number of cache evictions",
            "# TYPE cache_evictions counter",
            f"cache_evictions {cache_metrics['evictions']}",
            "",
        ]
        
        return "\n".join(lines)


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """
    Get the global metrics collector instance.
    
    Returns:
        Global MetricsCollector instance
    """
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def reset_metrics_collector() -> None:
    """
    Reset the global metrics collector instance.
    
    Useful for testing.
    """
    global _metrics_collector
    _metrics_collector = None