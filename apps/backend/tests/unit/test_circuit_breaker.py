"""
Unit tests for CircuitBreaker class.

Tests the circuit breaker state machine, failure rate monitoring,
exponential backoff, and test connection logic.
"""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from infrastructure.circuit_breaker import CircuitBreaker, ConnectionPoolWithCircuitBreaker
from infrastructure.models import CircuitState


class TestCircuitBreaker:
    """Test suite for CircuitBreaker class."""
    
    def test_initial_state_is_closed(self):
        """Circuit breaker should start in CLOSED state."""
        cb = CircuitBreaker(name="test")
        assert cb.get_state() == CircuitState.CLOSED
    
    def test_successful_call_in_closed_state(self):
        """Successful calls should pass through when circuit is CLOSED."""
        cb = CircuitBreaker(name="test")
        
        def success_func():
            return "success"
        
        result = cb.call(success_func)
        assert result == "success"
        assert cb.get_state() == CircuitState.CLOSED
        assert cb.success_count == 1
    
    def test_failed_call_records_failure(self):
        """Failed calls should be recorded."""
        cb = CircuitBreaker(name="test")
        
        def failing_func():
            raise Exception("Connection failed")
        
        with pytest.raises(Exception, match="Connection failed"):
            cb.call(failing_func)
        
        assert cb.failure_count == 1
        assert cb.last_failure_time is not None
    
    def test_circuit_opens_at_failure_threshold(self):
        """Circuit should open when failure rate exceeds threshold."""
        cb = CircuitBreaker(
            failure_threshold=0.5,
            failure_window=60,
            name="test"
        )
        
        def failing_func():
            raise Exception("Connection failed")
        
        def success_func():
            return "success"
        
        # Record 1 success and 2 failures (66% failure rate > 50% threshold)
        cb.call(success_func)
        
        with pytest.raises(Exception):
            cb.call(failing_func)
        
        with pytest.raises(Exception):
            cb.call(failing_func)
        
        # Circuit should now be OPEN
        assert cb.get_state() == CircuitState.OPEN
    
    def test_open_circuit_rejects_immediately(self):
        """OPEN circuit should reject requests immediately without calling function."""
        cb = CircuitBreaker(
            failure_threshold=0.5,
            failure_window=60,
            name="test"
        )
        
        # Force circuit to OPEN state
        cb._transition_to_open()
        
        mock_func = Mock()
        
        with pytest.raises(Exception, match="Circuit breaker.*is OPEN"):
            cb.call(mock_func)
        
        # Function should not have been called
        mock_func.assert_not_called()
    
    def test_should_attempt_reset_after_recovery_timeout(self):
        """Circuit should attempt reset after recovery timeout."""
        cb = CircuitBreaker(
            recovery_timeout=2,  # 2 seconds
            name="test"
        )
        
        # Open the circuit
        cb._transition_to_open()
        
        # Immediately after opening, should not attempt reset
        assert not cb.should_attempt_reset()
        
        # After recovery timeout, should attempt reset
        time.sleep(2.1)
        assert cb.should_attempt_reset()
    
    def test_transition_to_half_open_after_timeout(self):
        """Circuit should transition to HALF_OPEN after recovery timeout."""
        cb = CircuitBreaker(
            recovery_timeout=1,  # 1 second
            name="test"
        )
        
        # Open the circuit
        cb._transition_to_open()
        assert cb.get_state() == CircuitState.OPEN
        
        # Wait for recovery timeout
        time.sleep(1.1)
        
        # Next call should transition to HALF_OPEN
        def success_func():
            return "success"
        
        result = cb.call(success_func)
        
        # Should have transitioned to CLOSED after successful test
        assert result == "success"
        assert cb.get_state() == CircuitState.CLOSED
    
    def test_half_open_success_closes_circuit(self):
        """Successful test in HALF_OPEN should close the circuit."""
        cb = CircuitBreaker(name="test")
        
        # Manually set to HALF_OPEN
        cb._transition_to_half_open()
        assert cb.get_state() == CircuitState.HALF_OPEN
        
        def success_func():
            return "success"
        
        result = cb.call(success_func)
        
        assert result == "success"
        assert cb.get_state() == CircuitState.CLOSED
    
    def test_half_open_failure_reopens_circuit(self):
        """Failed test in HALF_OPEN should reopen the circuit."""
        cb = CircuitBreaker(name="test")
        
        # Manually set to HALF_OPEN
        cb._transition_to_half_open()
        assert cb.get_state() == CircuitState.HALF_OPEN
        
        def failing_func():
            raise Exception("Test connection failed")
        
        with pytest.raises(Exception, match="Test connection failed"):
            cb.call(failing_func)
        
        assert cb.get_state() == CircuitState.OPEN
    
    def test_exponential_backoff_delays(self):
        """Backoff delays should follow exponential pattern."""
        cb = CircuitBreaker(
            backoff_delays=(1, 2, 4),
            name="test"
        )
        
        assert cb.get_backoff_delay(0) == 1
        assert cb.get_backoff_delay(1) == 2
        assert cb.get_backoff_delay(2) == 4
        # Beyond configured delays, use last delay
        assert cb.get_backoff_delay(3) == 4
        assert cb.get_backoff_delay(10) == 4
    
    def test_failure_rate_calculation(self):
        """Failure rate should be calculated correctly."""
        cb = CircuitBreaker(
            failure_threshold=0.5,
            failure_window=60,
            name="test"
        )
        
        def success_func():
            return "success"
        
        def failing_func():
            raise Exception("Failed")
        
        # 2 successes, 1 failure = 33% failure rate
        cb.call(success_func)
        cb.call(success_func)
        
        with pytest.raises(Exception):
            cb.call(failing_func)
        
        stats = cb.get_stats()
        assert stats["failure_rate"] == pytest.approx(0.333, rel=0.01)
        assert cb.get_state() == CircuitState.CLOSED  # Below threshold
    
    def test_old_entries_cleaned_from_window(self):
        """Entries older than failure window should be removed."""
        cb = CircuitBreaker(
            failure_threshold=0.5,
            failure_window=1,  # 1 second window
            name="test"
        )
        
        def failing_func():
            raise Exception("Failed")
        
        # Record a failure
        with pytest.raises(Exception):
            cb.call(failing_func)
        
        assert cb.failure_count == 1
        stats = cb.get_stats()
        assert stats["failures_in_window"] == 1
        
        # Wait for window to expire
        time.sleep(1.1)
        
        # Clean old entries
        cb._clean_old_entries()
        
        stats = cb.get_stats()
        # Total count persists, but window count should be 0
        assert cb.failure_count == 1
        assert stats["failures_in_window"] == 0
    
    def test_manual_reset(self):
        """Manual reset should clear state and return to CLOSED."""
        cb = CircuitBreaker(name="test")
        
        # Open the circuit
        cb._transition_to_open()
        cb.failure_count = 10
        cb.success_count = 5
        
        assert cb.get_state() == CircuitState.OPEN
        
        # Reset
        cb.reset()
        
        assert cb.get_state() == CircuitState.CLOSED
        assert cb.failure_count == 0
        assert cb.success_count == 0
        assert cb.last_failure_time is None
    
    def test_get_stats_returns_complete_info(self):
        """get_stats should return comprehensive statistics."""
        cb = CircuitBreaker(name="test_breaker")
        
        def success_func():
            return "success"
        
        cb.call(success_func)
        
        stats = cb.get_stats()
        
        assert stats["name"] == "test_breaker"
        assert stats["state"] == "closed"
        assert stats["failure_count"] == 0
        assert stats["success_count"] == 1
        assert stats["failure_rate"] == 0.0
        assert "last_state_change" in stats
        assert "time_in_current_state" in stats


class TestConnectionPoolWithCircuitBreaker:
    """Test suite for ConnectionPoolWithCircuitBreaker."""
    
    def test_successful_connection_with_circuit_breaker(self):
        """Successful connection should work through circuit breaker."""
        mock_pool = Mock()
        mock_conn = Mock()
        mock_pool.get_connection.return_value = mock_conn
        
        pool_with_cb = ConnectionPoolWithCircuitBreaker(
            connection_pool=mock_pool,
            max_retries=3
        )
        
        conn = pool_with_cb.get_connection(timeout=5.0)
        
        assert conn == mock_conn
        mock_pool.get_connection.assert_called_once_with(timeout=5.0)
    
    def test_retry_with_exponential_backoff(self):
        """Failed connections should retry with exponential backoff."""
        mock_pool = Mock()
        mock_conn = Mock()
        
        # Add initial success to establish baseline, then fail twice, then succeed
        mock_pool.get_connection.side_effect = [
            Mock(),  # Initial success
            Exception("Connection failed"),
            Exception("Connection failed"),
            mock_conn
        ]
        
        # Create circuit breaker with higher threshold to allow retries
        cb = CircuitBreaker(
            failure_threshold=0.9,  # 90% threshold to allow multiple failures
            failure_window=60,
            name="test_pool"
        )
        
        pool_with_cb = ConnectionPoolWithCircuitBreaker(
            connection_pool=mock_pool,
            circuit_breaker=cb,
            max_retries=3
        )
        
        # First call succeeds to establish baseline
        initial_conn = pool_with_cb.get_connection(timeout=5.0)
        pool_with_cb.release_connection(initial_conn)
        
        # Now test retry with backoff
        start_time = time.time()
        conn = pool_with_cb.get_connection(timeout=5.0)
        elapsed = time.time() - start_time
        
        assert conn == mock_conn
        # Should have waited 1s + 2s = 3s for backoff
        assert elapsed >= 3.0
        assert mock_pool.get_connection.call_count == 4  # 1 initial + 3 retries
    
    def test_max_retries_exhausted(self):
        """Should raise exception after max retries exhausted."""
        mock_pool = Mock()
        mock_pool.get_connection.side_effect = Exception("Connection failed")
        
        # Create circuit breaker with very high threshold to allow all retries
        cb = CircuitBreaker(
            failure_threshold=0.99,  # 99% threshold to allow multiple failures
            failure_window=60,
            name="test_pool"
        )
        
        pool_with_cb = ConnectionPoolWithCircuitBreaker(
            connection_pool=mock_pool,
            circuit_breaker=cb,
            max_retries=3
        )
        
        # Add initial success to establish baseline
        mock_pool.get_connection.side_effect = [
            Mock(),  # Initial success
            Exception("Connection failed"),
            Exception("Connection failed"),
            Exception("Connection failed")
        ]
        
        # First call succeeds
        initial_conn = pool_with_cb.get_connection(timeout=5.0)
        pool_with_cb.release_connection(initial_conn)
        
        # Reset side effect for failure test
        mock_pool.get_connection.side_effect = Exception("Connection failed")
        
        with pytest.raises(Exception, match="Connection failed"):
            pool_with_cb.get_connection(timeout=5.0)
        
        # Should have tried 3 times (after initial success)
        assert mock_pool.get_connection.call_count == 4  # 1 initial + 3 retries
    
    def test_open_circuit_aborts_retries(self):
        """OPEN circuit should abort retry attempts immediately."""
        mock_pool = Mock()
        mock_pool.get_connection.side_effect = Exception("Connection failed")
        
        cb = CircuitBreaker(
            failure_threshold=0.5,
            failure_window=60,
            name="test"
        )
        
        # Force circuit to OPEN
        cb._transition_to_open()
        
        pool_with_cb = ConnectionPoolWithCircuitBreaker(
            connection_pool=mock_pool,
            circuit_breaker=cb,
            max_retries=3
        )
        
        with pytest.raises(Exception, match="Circuit breaker.*is OPEN"):
            pool_with_cb.get_connection(timeout=5.0)
        
        # Should not have called pool at all (circuit rejected immediately)
        mock_pool.get_connection.assert_not_called()
    
    def test_release_connection_delegates_to_pool(self):
        """release_connection should delegate to underlying pool."""
        mock_pool = Mock()
        mock_conn = Mock()
        
        pool_with_cb = ConnectionPoolWithCircuitBreaker(
            connection_pool=mock_pool,
            max_retries=3
        )
        
        pool_with_cb.release_connection(mock_conn)
        
        mock_pool.release_connection.assert_called_once_with(mock_conn)
    
    def test_get_stats_combines_pool_and_circuit_stats(self):
        """get_stats should return both pool and circuit breaker stats."""
        from infrastructure.models import PoolStats
        
        mock_pool = Mock()
        mock_pool.get_stats.return_value = PoolStats(
            total_connections=10,
            active_connections=5,
            idle_connections=5,
            utilization_percent=50.0,
            wait_time_avg=10.0,
            connection_errors=0
        )
        
        pool_with_cb = ConnectionPoolWithCircuitBreaker(
            connection_pool=mock_pool,
            max_retries=3
        )
        
        stats = pool_with_cb.get_stats()
        
        assert "pool" in stats
        assert "circuit_breaker" in stats
        assert stats["pool"]["total_connections"] == 10
        assert stats["circuit_breaker"]["state"] == "closed"


class TestCircuitBreakerEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_zero_failure_threshold(self):
        """Circuit with 0% threshold should open after enough failures."""
        cb = CircuitBreaker(
            failure_threshold=0.0,
            failure_window=60,
            name="test"
        )
        
        def failing_func():
            raise Exception("Failed")
        
        def success_func():
            return "success"
        
        # Need at least 2 requests for meaningful failure rate
        # 1 success, 1 failure = 50% failure rate > 0% threshold
        cb.call(success_func)
        
        with pytest.raises(Exception):
            cb.call(failing_func)
        
        # Circuit should open because 50% > 0%
        assert cb.get_state() == CircuitState.OPEN
    
    def test_hundred_percent_failure_threshold(self):
        """Circuit with 100% threshold should only open when exceeding 100%."""
        cb = CircuitBreaker(
            failure_threshold=1.0,
            failure_window=60,
            name="test"
        )
        
        def failing_func():
            raise Exception("Failed")
        
        def success_func():
            return "success"
        
        # 100% failure rate (all failures) should not exceed threshold
        # First, add a success to establish baseline
        cb.call(success_func)
        
        # Then add failures - as long as we have at least one success, 
        # we won't exceed 100%
        for _ in range(5):
            with pytest.raises(Exception):
                cb.call(failing_func)
        
        # Should still be closed because failure rate is 83% (5/6), not > 100%
        assert cb.get_state() == CircuitState.CLOSED
    
    def test_concurrent_access_thread_safety(self):
        """Circuit breaker should be thread-safe."""
        import threading
        
        cb = CircuitBreaker(
            failure_threshold=0.5,
            failure_window=60,
            name="test"
        )
        
        results = []
        
        def worker():
            try:
                result = cb.call(lambda: "success")
                results.append(result)
            except Exception as e:
                results.append(str(e))
        
        # Create multiple threads
        threads = [threading.Thread(target=worker) for _ in range(10)]
        
        # Start all threads
        for t in threads:
            t.start()
        
        # Wait for completion
        for t in threads:
            t.join()
        
        # All should have succeeded
        assert len(results) == 10
        assert all(r == "success" for r in results)
    
    def test_empty_backoff_delays(self):
        """Circuit breaker should handle empty backoff delays gracefully."""
        cb = CircuitBreaker(
            backoff_delays=(),
            name="test"
        )
        
        # Should not raise exception, but behavior is undefined
        # In practice, this would use default or raise IndexError
        # The implementation uses the last delay, so empty tuple would fail
        # This test documents the edge case
        with pytest.raises(IndexError):
            cb.get_backoff_delay(0)
