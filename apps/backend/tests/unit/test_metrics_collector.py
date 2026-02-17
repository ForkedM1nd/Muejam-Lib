"""
Unit tests for MetricsCollector

Tests database and cache metrics collection, threshold monitoring, and
Prometheus format export.

Requirements: 10.1, 10.2, 10.3, 10.4
"""

import pytest
import time
from datetime import datetime, timedelta
from backend.infrastructure.metrics_collector import (
    MetricsCollector,
    ThresholdConfig,
    DatabaseMetrics,
    CacheMetrics,
    get_metrics_collector,
    reset_metrics_collector,
)


class TestDatabaseMetrics:
    """Test DatabaseMetrics data class."""
    
    def test_avg_latency_calculation(self):
        """Test average latency calculation."""
        metrics = DatabaseMetrics()
        metrics.query_count = 5
        metrics.total_latency_ms = 500.0
        
        assert metrics.avg_latency_ms == 100.0
    
    def test_avg_latency_zero_queries(self):
        """Test average latency with zero queries."""
        metrics = DatabaseMetrics()
        assert metrics.avg_latency_ms == 0.0
    
    def test_error_rate_calculation(self):
        """Test error rate calculation."""
        metrics = DatabaseMetrics()
        metrics.query_count = 95
        metrics.error_count = 5
        
        assert metrics.error_rate == 5.0
    
    def test_error_rate_zero_total(self):
        """Test error rate with zero total operations."""
        metrics = DatabaseMetrics()
        assert metrics.error_rate == 0.0


class TestCacheMetrics:
    """Test CacheMetrics data class."""
    
    def test_hit_rate_calculation(self):
        """Test cache hit rate calculation."""
        metrics = CacheMetrics()
        metrics.hits = 80
        metrics.misses = 20
        
        assert metrics.hit_rate == 80.0
    
    def test_miss_rate_calculation(self):
        """Test cache miss rate calculation."""
        metrics = CacheMetrics()
        metrics.hits = 80
        metrics.misses = 20
        
        assert metrics.miss_rate == 20.0
    
    def test_eviction_rate_calculation(self):
        """Test cache eviction rate calculation."""
        metrics = CacheMetrics()
        metrics.evictions = 10
        metrics.sets = 100
        
        assert metrics.eviction_rate == 10.0
    
    def test_rates_with_zero_operations(self):
        """Test rate calculations with zero operations."""
        metrics = CacheMetrics()
        
        assert metrics.hit_rate == 0.0
        assert metrics.miss_rate == 0.0
        assert metrics.eviction_rate == 0.0


class TestMetricsCollector:
    """Test MetricsCollector class."""
    
    @pytest.fixture
    def collector(self):
        """Create a fresh metrics collector for each test."""
        return MetricsCollector(retention_seconds=60)
    
    def test_initialization(self, collector):
        """Test metrics collector initialization."""
        assert collector.db_metrics.query_count == 0
        assert collector.cache_metrics.hits == 0
        assert len(collector._thresholds) == 0
    
    def test_record_query_success(self, collector):
        """Test recording successful query. Requirements: 10.1"""
        collector.record_query(latency_ms=50.0, is_error=False, is_slow=False)
        
        metrics = collector.get_database_metrics()
        assert metrics['query_count'] == 1
        assert metrics['avg_latency_ms'] == 50.0
        assert metrics['min_latency_ms'] == 50.0
        assert metrics['max_latency_ms'] == 50.0
        assert metrics['error_count'] == 0
    
    def test_record_query_error(self, collector):
        """Test recording query error. Requirements: 10.1"""
        collector.record_query(latency_ms=0.0, is_error=True, is_slow=False)
        
        metrics = collector.get_database_metrics()
        assert metrics['query_count'] == 0
        assert metrics['error_count'] == 1
        assert metrics['error_rate_percent'] == 100.0
    
    def test_record_slow_query(self, collector):
        """Test recording slow query. Requirements: 10.1, 10.3"""
        collector.record_query(latency_ms=150.0, is_error=False, is_slow=True)
        
        metrics = collector.get_database_metrics()
        assert metrics['slow_query_count'] == 1
    
    def test_multiple_queries_latency_stats(self, collector):
        """Test latency statistics with multiple queries. Requirements: 10.1"""
        collector.record_query(latency_ms=10.0, is_error=False)
        collector.record_query(latency_ms=50.0, is_error=False)
        collector.record_query(latency_ms=100.0, is_error=False)
        
        metrics = collector.get_database_metrics()
        assert metrics['query_count'] == 3
        assert metrics['avg_latency_ms'] == pytest.approx(53.33, rel=0.01)
        assert metrics['min_latency_ms'] == 10.0
        assert metrics['max_latency_ms'] == 100.0
    
    def test_throughput_calculation(self, collector):
        """Test throughput calculation. Requirements: 10.1"""
        collector.record_query(latency_ms=10.0, is_error=False)
        time.sleep(0.1)  # Wait a bit for throughput calculation
        
        metrics = collector.get_database_metrics()
        assert metrics['throughput_qps'] > 0
    
    def test_record_cache_hit(self, collector):
        """Test recording cache hit. Requirements: 10.2"""
        collector.record_cache_hit()
        
        metrics = collector.get_cache_metrics()
        assert metrics['hits'] == 1
        assert metrics['misses'] == 0
    
    def test_record_cache_miss(self, collector):
        """Test recording cache miss. Requirements: 10.2"""
        collector.record_cache_miss()
        
        metrics = collector.get_cache_metrics()
        assert metrics['hits'] == 0
        assert metrics['misses'] == 1
    
    def test_cache_hit_rate(self, collector):
        """Test cache hit rate calculation. Requirements: 10.2"""
        for _ in range(8):
            collector.record_cache_hit()
        for _ in range(2):
            collector.record_cache_miss()
        
        metrics = collector.get_cache_metrics()
        assert metrics['hit_rate_percent'] == 80.0
        assert metrics['miss_rate_percent'] == 20.0
    
    def test_cache_eviction_tracking(self, collector):
        """Test cache eviction tracking. Requirements: 10.2"""
        for _ in range(10):
            collector.record_cache_set()
        for _ in range(3):
            collector.record_cache_eviction()
        
        metrics = collector.get_cache_metrics()
        assert metrics['sets'] == 10
        assert metrics['evictions'] == 3
        assert metrics['eviction_rate_percent'] == 30.0
    
    def test_get_all_metrics(self, collector):
        """Test getting all metrics at once. Requirements: 10.1, 10.2"""
        collector.record_query(latency_ms=50.0, is_error=False)
        collector.record_cache_hit()
        
        all_metrics = collector.get_all_metrics()
        assert 'database' in all_metrics
        assert 'cache' in all_metrics
        assert 'timestamp' in all_metrics
        assert all_metrics['database']['query_count'] == 1
        assert all_metrics['cache']['hits'] == 1
    
    def test_threshold_monitoring(self, collector):
        """Test threshold monitoring and alerts. Requirements: 10.4"""
        alert_triggered = []
        
        def alert_callback(metric_name, current_value, threshold):
            alert_triggered.append((metric_name, current_value, threshold))
        
        # Add threshold for error rate > 10%
        threshold = ThresholdConfig(
            metric_name='error_rate_percent',
            threshold=10.0,
            comparison='gt',
            alert_callback=alert_callback
        )
        collector.add_threshold(threshold)
        
        # Record queries that breach threshold
        for _ in range(8):
            collector.record_query(latency_ms=10.0, is_error=False)
        for _ in range(2):
            collector.record_query(latency_ms=0.0, is_error=True)
        
        # Alert should have been triggered
        assert len(alert_triggered) > 0
        assert alert_triggered[0][0] == 'error_rate_percent'
        assert alert_triggered[0][1] > 10.0
    
    def test_threshold_comparison_operators(self, collector):
        """Test different threshold comparison operators. Requirements: 10.4"""
        assert collector._is_threshold_breached(15.0, 10.0, 'gt') is True
        assert collector._is_threshold_breached(10.0, 10.0, 'gt') is False
        assert collector._is_threshold_breached(10.0, 10.0, 'gte') is True
        assert collector._is_threshold_breached(5.0, 10.0, 'lt') is True
        assert collector._is_threshold_breached(10.0, 10.0, 'lt') is False
        assert collector._is_threshold_breached(10.0, 10.0, 'lte') is True
        assert collector._is_threshold_breached(10.0, 10.0, 'eq') is True
    
    def test_remove_threshold(self, collector):
        """Test removing a threshold."""
        threshold = ThresholdConfig(
            metric_name='error_rate_percent',
            threshold=10.0,
            comparison='gt'
        )
        collector.add_threshold(threshold)
        assert len(collector._thresholds) == 1
        
        collector.remove_threshold('error_rate_percent')
        assert len(collector._thresholds) == 0
    
    def test_reset_metrics(self, collector):
        """Test resetting metrics."""
        collector.record_query(latency_ms=50.0, is_error=False)
        collector.record_cache_hit()
        
        collector.reset_metrics()
        
        metrics = collector.get_all_metrics()
        assert metrics['database']['query_count'] == 0
        assert metrics['cache']['hits'] == 0
    
    def test_prometheus_export_format(self, collector):
        """Test Prometheus format export. Requirements: 10.1, 10.2"""
        collector.record_query(latency_ms=50.0, is_error=False)
        collector.record_cache_hit()
        collector.record_cache_miss()
        
        prometheus_output = collector.export_prometheus_format()
        
        # Check for required Prometheus format elements
        assert "# HELP db_query_count" in prometheus_output
        assert "# TYPE db_query_count counter" in prometheus_output
        assert "db_query_count 1" in prometheus_output
        assert "# HELP cache_hits" in prometheus_output
        assert "cache_hits 1" in prometheus_output
        assert "cache_misses 1" in prometheus_output
        assert "cache_hit_rate_percent 50.00" in prometheus_output
    
    def test_data_retention_cleanup(self, collector):
        """Test that old time-series data is cleaned up."""
        # Create collector with very short retention
        short_collector = MetricsCollector(retention_seconds=1)
        
        short_collector.record_query(latency_ms=50.0, is_error=False)
        assert len(short_collector._db_queries) == 1
        
        # Wait for retention period to expire
        time.sleep(1.1)
        
        # Record another query to trigger cleanup
        short_collector.record_query(latency_ms=60.0, is_error=False)
        
        # Old data should be cleaned up
        assert len(short_collector._db_queries) == 1


class TestGlobalMetricsCollector:
    """Test global metrics collector singleton."""
    
    def test_get_metrics_collector(self):
        """Test getting global metrics collector instance."""
        reset_metrics_collector()
        
        collector1 = get_metrics_collector()
        collector2 = get_metrics_collector()
        
        assert collector1 is collector2
    
    def test_reset_metrics_collector(self):
        """Test resetting global metrics collector."""
        collector1 = get_metrics_collector()
        collector1.record_query(latency_ms=50.0, is_error=False)
        
        reset_metrics_collector()
        
        collector2 = get_metrics_collector()
        assert collector2 is not collector1
        assert collector2.get_database_metrics()['query_count'] == 0
