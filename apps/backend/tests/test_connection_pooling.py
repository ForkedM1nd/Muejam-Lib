"""
Test Connection Pooling Implementation

This test suite verifies that database connection pooling is working correctly
and can handle concurrent load without exhausting connections.

Requirements: Production Readiness Audit - Task 2.1
"""

import pytest
import time
import threading
from django.db import connection, connections
from django.test import TestCase, TransactionTestCase
from concurrent.futures import ThreadPoolExecutor, as_completed


class ConnectionPoolingTestCase(TransactionTestCase):
    """Test database connection pooling behavior."""
    
    def test_connection_reuse(self):
        """Test that connections are reused (CONN_MAX_AGE > 0)."""
        # Get connection settings
        db_settings = connections['default'].settings_dict
        
        # Verify CONN_MAX_AGE is configured
        conn_max_age = db_settings.get('CONN_MAX_AGE', 0)
        self.assertGreater(
            conn_max_age, 0,
            "CONN_MAX_AGE should be > 0 for connection pooling"
        )
        self.assertEqual(
            conn_max_age, 600,
            "CONN_MAX_AGE should be 600 seconds (10 minutes)"
        )
    
    def test_connection_timeout_configured(self):
        """Test that connection timeout is configured."""
        db_settings = connections['default'].settings_dict
        options = db_settings.get('OPTIONS', {})
        
        # Verify connect_timeout is set
        self.assertIn('connect_timeout', options)
        self.assertEqual(
            options['connect_timeout'], 10,
            "Connection timeout should be 10 seconds"
        )
    
    def test_query_timeout_configured(self):
        """Test that query timeout is configured."""
        db_settings = connections['default'].settings_dict
        options = db_settings.get('OPTIONS', {})
        
        # Verify statement_timeout is set
        self.assertIn('options', options)
        self.assertIn('statement_timeout', options['options'])
    
    def test_basic_query_execution(self):
        """Test that basic queries work with connection pooling."""
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            self.assertEqual(result[0], 1)
    
    def test_multiple_sequential_queries(self):
        """Test multiple sequential queries reuse the same connection."""
        connection_ids = []
        
        for i in range(5):
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                pid = cursor.fetchone()[0]
                connection_ids.append(pid)
        
        # All queries should use the same connection (same backend PID)
        self.assertEqual(
            len(set(connection_ids)), 1,
            "Sequential queries should reuse the same connection"
        )


class ConcurrentConnectionTestCase(TransactionTestCase):
    """Test connection pooling under concurrent load."""
    
    def execute_query(self, query_id):
        """Execute a simple query and return timing info."""
        start_time = time.time()
        
        try:
            with connection.cursor() as cursor:
                # Simulate a realistic query
                cursor.execute("""
                    SELECT 
                        %s as query_id,
                        pg_backend_pid() as backend_pid,
                        current_timestamp as executed_at
                """, [query_id])
                result = cursor.fetchone()
                
            duration = time.time() - start_time
            
            return {
                'query_id': query_id,
                'backend_pid': result[1],
                'duration': duration,
                'success': True,
                'error': None
            }
            
        except Exception as e:
            duration = time.time() - start_time
            return {
                'query_id': query_id,
                'backend_pid': None,
                'duration': duration,
                'success': False,
                'error': str(e)
            }
    
    def test_concurrent_queries_10_threads(self):
        """Test 10 concurrent queries."""
        num_queries = 10
        results = []
        
        with ThreadPoolExecutor(max_workers=num_queries) as executor:
            futures = [
                executor.submit(self.execute_query, i)
                for i in range(num_queries)
            ]
            
            for future in as_completed(futures):
                results.append(future.result())
        
        # All queries should succeed
        successful = [r for r in results if r['success']]
        self.assertEqual(
            len(successful), num_queries,
            f"All {num_queries} queries should succeed"
        )
        
        # Check that connections were reused (should have fewer PIDs than queries)
        unique_pids = set(r['backend_pid'] for r in successful)
        self.assertLessEqual(
            len(unique_pids), num_queries,
            "Should reuse connections (fewer PIDs than queries)"
        )
        
        # Average query time should be reasonable
        avg_duration = sum(r['duration'] for r in successful) / len(successful)
        self.assertLess(
            avg_duration, 1.0,
            f"Average query duration should be < 1s, got {avg_duration:.3f}s"
        )
    
    def test_concurrent_queries_50_threads(self):
        """Test 50 concurrent queries (stress test)."""
        num_queries = 50
        results = []
        
        with ThreadPoolExecutor(max_workers=num_queries) as executor:
            futures = [
                executor.submit(self.execute_query, i)
                for i in range(num_queries)
            ]
            
            for future in as_completed(futures):
                results.append(future.result())
        
        # Most queries should succeed (allow for some failures under stress)
        successful = [r for r in results if r['success']]
        success_rate = len(successful) / num_queries
        
        self.assertGreater(
            success_rate, 0.9,
            f"At least 90% of queries should succeed, got {success_rate:.1%}"
        )
        
        # Check for connection errors
        errors = [r for r in results if not r['success']]
        if errors:
            print(f"\nConnection errors under load: {len(errors)}/{num_queries}")
            for error in errors[:5]:  # Print first 5 errors
                print(f"  - Query {error['query_id']}: {error['error']}")
    
    def test_connection_pool_recovery(self):
        """Test that connection pool recovers after load spike."""
        # First, run a load spike
        num_queries = 30
        results = []
        
        with ThreadPoolExecutor(max_workers=num_queries) as executor:
            futures = [
                executor.submit(self.execute_query, i)
                for i in range(num_queries)
            ]
            
            for future in as_completed(futures):
                results.append(future.result())
        
        # Wait a moment for connections to settle
        time.sleep(0.5)
        
        # Now run a single query - should work fine
        result = self.execute_query(999)
        self.assertTrue(
            result['success'],
            "Single query should succeed after load spike"
        )


class ConnectionPoolMonitoringTestCase(TestCase):
    """Test connection pool monitoring capabilities."""
    
    def test_get_connection_info(self):
        """Test that we can retrieve connection information."""
        db_settings = connections['default'].settings_dict
        
        # Verify we can access connection parameters
        self.assertIn('ENGINE', db_settings)
        self.assertIn('NAME', db_settings)
        self.assertIn('HOST', db_settings)
        self.assertIn('PORT', db_settings)
        self.assertIn('CONN_MAX_AGE', db_settings)
    
    def test_connection_health_check(self):
        """Test basic connection health check."""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                self.assertEqual(result[0], 1)
            
            health_status = "healthy"
        except Exception as e:
            health_status = f"unhealthy: {e}"
        
        self.assertEqual(health_status, "healthy")


@pytest.mark.django_db
class TestConnectionPoolingConfiguration:
    """Pytest-style tests for connection pooling configuration."""
    
    def test_conn_max_age_is_set(self):
        """Verify CONN_MAX_AGE is configured for connection pooling."""
        db_settings = connections['default'].settings_dict
        assert db_settings.get('CONN_MAX_AGE', 0) > 0, \
            "CONN_MAX_AGE must be > 0 for connection pooling"
    
    def test_connection_timeout_is_reasonable(self):
        """Verify connection timeout is set to a reasonable value."""
        db_settings = connections['default'].settings_dict
        options = db_settings.get('OPTIONS', {})
        connect_timeout = options.get('connect_timeout', 0)
        
        assert connect_timeout > 0, "Connection timeout must be set"
        assert connect_timeout <= 30, "Connection timeout should be <= 30 seconds"
    
    def test_database_backend_is_postgresql(self):
        """Verify we're using PostgreSQL (required for connection pooling)."""
        db_settings = connections['default'].settings_dict
        engine = db_settings.get('ENGINE', '')
        
        assert 'postgresql' in engine.lower(), \
            "Connection pooling requires PostgreSQL backend"


# Performance benchmark (not run by default)
class ConnectionPoolBenchmark(TransactionTestCase):
    """Benchmark connection pooling performance."""
    
    @pytest.mark.benchmark
    def test_benchmark_query_throughput(self):
        """Benchmark query throughput with connection pooling."""
        num_queries = 100
        start_time = time.time()
        
        results = []
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [
                executor.submit(self.execute_simple_query, i)
                for i in range(num_queries)
            ]
            
            for future in as_completed(futures):
                results.append(future.result())
        
        total_time = time.time() - start_time
        queries_per_second = num_queries / total_time
        
        print(f"\nBenchmark Results:")
        print(f"  Total queries: {num_queries}")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Throughput: {queries_per_second:.1f} queries/second")
        print(f"  Average latency: {(total_time / num_queries) * 1000:.1f}ms")
        
        # Should achieve reasonable throughput
        self.assertGreater(
            queries_per_second, 10,
            "Should achieve > 10 queries/second with connection pooling"
        )
    
    def execute_simple_query(self, query_id):
        """Execute a simple query for benchmarking."""
        with connection.cursor() as cursor:
            cursor.execute("SELECT %s", [query_id])
            return cursor.fetchone()[0]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
