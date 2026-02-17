"""
Circuit Breaker for database connection failure protection.

This module implements the circuit breaker pattern to prevent cascading failures
when database connections fail repeatedly. The circuit breaker monitors failure
rates and transitions between CLOSED, OPEN, and HALF_OPEN states to protect
the system.
"""

import logging
import threading
import time
from collections import deque
from datetime import datetime, timedelta
from typing import Callable, Any, Optional, TypeVar, Deque

from infrastructure.models import CircuitState


logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitBreaker:
    """
    Circuit breaker for database connection failure protection.
    
    Implements a state machine with three states:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Failure threshold exceeded, requests fail immediately
    - HALF_OPEN: Testing if service recovered, single test request allowed
    
    State transitions:
    - CLOSED -> OPEN: When failure rate exceeds 50% over 60 seconds
    - OPEN -> HALF_OPEN: After 30 seconds in OPEN state
    - HALF_OPEN -> CLOSED: When test connection succeeds
    - HALF_OPEN -> OPEN: When test connection fails
    """
    
    def __init__(
        self,
        failure_threshold: float = 0.5,
        failure_window: int = 60,
        recovery_timeout: int = 30,
        backoff_delays: tuple = (1, 2, 4),
        name: str = "default"
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Failure rate threshold (0.0-1.0) to open circuit
            failure_window: Time window in seconds to calculate failure rate
            recovery_timeout: Seconds to wait in OPEN state before attempting test
            backoff_delays: Exponential backoff delays in seconds (e.g., 1s, 2s, 4s)
            name: Name for this circuit breaker instance
        """
        self.failure_threshold = failure_threshold
        self.failure_window = failure_window
        self.recovery_timeout = recovery_timeout
        self.backoff_delays = backoff_delays
        self.name = name
        
        # State management
        self.state = CircuitState.CLOSED
        self._lock = threading.RLock()
        
        # Failure tracking
        self._failures: Deque[datetime] = deque()
        self._successes: Deque[datetime] = deque()
        self.failure_count = 0
        self.success_count = 0
        
        # Timing
        self.last_failure_time: Optional[datetime] = None
        self.last_state_change: datetime = datetime.now()
        self.opened_at: Optional[datetime] = None
        
        # Retry tracking
        self._retry_attempt = 0
        
        logger.info(
            f"CircuitBreaker '{name}' initialized: "
            f"threshold={failure_threshold*100}%, "
            f"window={failure_window}s, "
            f"recovery={recovery_timeout}s"
        )
    
    def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func
            
        Returns:
            Result of func execution
            
        Raises:
            Exception: If circuit is OPEN or func raises exception
        """
        with self._lock:
            # Check if we should attempt reset from OPEN to HALF_OPEN
            if self.state == CircuitState.OPEN and self.should_attempt_reset():
                self._transition_to_half_open()
            
            # Reject immediately if circuit is OPEN
            if self.state == CircuitState.OPEN:
                logger.warning(
                    f"CircuitBreaker '{self.name}' is OPEN, rejecting request immediately"
                )
                raise Exception(
                    f"Circuit breaker '{self.name}' is OPEN. "
                    f"Service unavailable, please retry later."
                )
            
            # In HALF_OPEN state, only allow one test request at a time
            if self.state == CircuitState.HALF_OPEN:
                logger.info(
                    f"CircuitBreaker '{self.name}' is HALF_OPEN, attempting test connection"
                )
        
        # Execute the function
        try:
            result = func(*args, **kwargs)
            self.record_success()
            return result
            
        except Exception as e:
            self.record_failure()
            raise
    
    def record_success(self) -> None:
        """Record a successful operation."""
        with self._lock:
            now = datetime.now()
            self._successes.append(now)
            self.success_count += 1
            
            # Clean old entries
            self._clean_old_entries()
            
            # If in HALF_OPEN and test succeeded, close the circuit
            if self.state == CircuitState.HALF_OPEN:
                self._transition_to_closed()
                logger.info(
                    f"CircuitBreaker '{self.name}' test connection succeeded, "
                    f"transitioning to CLOSED"
                )
            
            # Reset retry attempt counter on success
            self._retry_attempt = 0
            
            logger.debug(f"CircuitBreaker '{self.name}' recorded success")
    
    def record_failure(self) -> None:
        """Record a failed operation."""
        with self._lock:
            now = datetime.now()
            self._failures.append(now)
            self.failure_count += 1
            self.last_failure_time = now
            
            # Clean old entries
            self._clean_old_entries()
            
            # Calculate current failure rate
            failure_rate = self._calculate_failure_rate()
            
            logger.warning(
                f"CircuitBreaker '{self.name}' recorded failure "
                f"(rate: {failure_rate*100:.1f}%, threshold: {self.failure_threshold*100}%)"
            )
            
            # Check if we should open the circuit
            # Only open if we have enough data points and exceed threshold
            if self.state == CircuitState.CLOSED:
                total_requests = len(self._failures) + len(self._successes)
                # Require at least 2 requests to calculate meaningful failure rate
                if total_requests >= 2 and failure_rate > self.failure_threshold:
                    self._transition_to_open()
                    logger.error(
                        f"CircuitBreaker '{self.name}' failure threshold exceeded, "
                        f"opening circuit (rate: {failure_rate*100:.1f}%)"
                    )
            
            # If in HALF_OPEN and test failed, reopen the circuit
            elif self.state == CircuitState.HALF_OPEN:
                self._transition_to_open()
                logger.error(
                    f"CircuitBreaker '{self.name}' test connection failed, "
                    f"reopening circuit"
                )
    
    def should_attempt_reset(self) -> bool:
        """
        Check if circuit should attempt to transition from OPEN to HALF_OPEN.
        
        Returns:
            True if recovery timeout has elapsed since circuit opened
        """
        if self.state != CircuitState.OPEN or self.opened_at is None:
            return False
        
        elapsed = (datetime.now() - self.opened_at).total_seconds()
        return elapsed >= self.recovery_timeout
    
    def get_backoff_delay(self, attempt: int) -> float:
        """
        Get exponential backoff delay for retry attempt.
        
        Args:
            attempt: Retry attempt number (0-indexed)
            
        Returns:
            Delay in seconds
        """
        if attempt >= len(self.backoff_delays):
            # Use last delay for attempts beyond configured delays
            return self.backoff_delays[-1]
        return self.backoff_delays[attempt]
    
    def reset(self) -> None:
        """Manually reset circuit breaker to CLOSED state."""
        with self._lock:
            self._transition_to_closed()
            self._failures.clear()
            self._successes.clear()
            self.failure_count = 0
            self.success_count = 0
            self.last_failure_time = None
            self._retry_attempt = 0
            logger.info(f"CircuitBreaker '{self.name}' manually reset to CLOSED")
    
    def get_state(self) -> CircuitState:
        """Get current circuit breaker state."""
        return self.state
    
    def get_stats(self) -> dict:
        """
        Get circuit breaker statistics.
        
        Returns:
            Dictionary with current statistics
        """
        with self._lock:
            self._clean_old_entries()
            failure_rate = self._calculate_failure_rate()
            
            return {
                "name": self.name,
                "state": self.state.value,
                "failure_count": self.failure_count,
                "success_count": self.success_count,
                "failure_rate": failure_rate,
                "failures_in_window": len(self._failures),
                "successes_in_window": len(self._successes),
                "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
                "last_state_change": self.last_state_change.isoformat(),
                "opened_at": self.opened_at.isoformat() if self.opened_at else None,
                "time_in_current_state": (datetime.now() - self.last_state_change).total_seconds()
            }
    
    def _calculate_failure_rate(self) -> float:
        """
        Calculate failure rate over the failure window.
        
        Returns:
            Failure rate as a float between 0.0 and 1.0
        """
        total_requests = len(self._failures) + len(self._successes)
        
        if total_requests == 0:
            return 0.0
        
        return len(self._failures) / total_requests
    
    def _clean_old_entries(self) -> None:
        """Remove entries older than the failure window."""
        cutoff = datetime.now() - timedelta(seconds=self.failure_window)
        
        # Remove old failures
        while self._failures and self._failures[0] < cutoff:
            self._failures.popleft()
        
        # Remove old successes
        while self._successes and self._successes[0] < cutoff:
            self._successes.popleft()
    
    def _transition_to_open(self) -> None:
        """Transition circuit breaker to OPEN state."""
        self.state = CircuitState.OPEN
        self.opened_at = datetime.now()
        self.last_state_change = datetime.now()
        logger.error(f"CircuitBreaker '{self.name}' transitioned to OPEN")
    
    def _transition_to_half_open(self) -> None:
        """Transition circuit breaker to HALF_OPEN state."""
        self.state = CircuitState.HALF_OPEN
        self.last_state_change = datetime.now()
        logger.info(f"CircuitBreaker '{self.name}' transitioned to HALF_OPEN")
    
    def _transition_to_closed(self) -> None:
        """Transition circuit breaker to CLOSED state."""
        self.state = CircuitState.CLOSED
        self.opened_at = None
        self.last_state_change = datetime.now()
        logger.info(f"CircuitBreaker '{self.name}' transitioned to CLOSED")


class ConnectionPoolWithCircuitBreaker:
    """
    Wrapper that adds circuit breaker protection to connection pool operations.
    
    This class wraps connection pool operations with retry logic and circuit
    breaker protection, implementing exponential backoff for failed connection
    attempts.
    """
    
    def __init__(
        self,
        connection_pool,
        circuit_breaker: Optional[CircuitBreaker] = None,
        max_retries: int = 3
    ):
        """
        Initialize connection pool with circuit breaker.
        
        Args:
            connection_pool: Underlying connection pool
            circuit_breaker: Circuit breaker instance (creates default if None)
            max_retries: Maximum number of retry attempts
        """
        self.connection_pool = connection_pool
        self.max_retries = max_retries
        
        if circuit_breaker is None:
            pool_type = getattr(connection_pool, 'pool_type', 'unknown')
            circuit_breaker = CircuitBreaker(name=f"{pool_type}_pool")
        
        self.circuit_breaker = circuit_breaker
        
        logger.info(
            f"ConnectionPoolWithCircuitBreaker initialized for "
            f"{self.circuit_breaker.name} with max_retries={max_retries}"
        )
    
    def get_connection(self, timeout: float = 5.0):
        """
        Get connection with retry logic and circuit breaker protection.
        
        Args:
            timeout: Connection timeout in seconds
            
        Returns:
            Database connection
            
        Raises:
            Exception: If all retry attempts fail or circuit is open
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                # Use circuit breaker to protect connection attempt
                conn = self.circuit_breaker.call(
                    self.connection_pool.get_connection,
                    timeout=timeout
                )
                return conn
                
            except Exception as e:
                last_exception = e
                
                # If circuit is open, don't retry
                if self.circuit_breaker.get_state() == CircuitState.OPEN:
                    logger.error(
                        f"Circuit breaker is OPEN, aborting retry attempts "
                        f"(attempt {attempt + 1}/{self.max_retries})"
                    )
                    raise
                
                # If not the last attempt, apply backoff and retry
                if attempt < self.max_retries - 1:
                    backoff_delay = self.circuit_breaker.get_backoff_delay(attempt)
                    logger.warning(
                        f"Connection attempt {attempt + 1}/{self.max_retries} failed, "
                        f"retrying in {backoff_delay}s: {e}"
                    )
                    time.sleep(backoff_delay)
                else:
                    logger.error(
                        f"All {self.max_retries} connection attempts failed: {e}"
                    )
        
        # All retries exhausted
        raise last_exception
    
    def release_connection(self, conn) -> None:
        """Release connection back to pool."""
        self.connection_pool.release_connection(conn)
    
    def get_stats(self) -> dict:
        """
        Get combined statistics from pool and circuit breaker.
        
        Returns:
            Dictionary with pool and circuit breaker stats
        """
        pool_stats = self.connection_pool.get_stats()
        circuit_stats = self.circuit_breaker.get_stats()
        
        return {
            "pool": pool_stats.__dict__ if hasattr(pool_stats, '__dict__') else pool_stats,
            "circuit_breaker": circuit_stats
        }
