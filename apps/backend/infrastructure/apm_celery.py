"""
APM Celery Task Tracking

This module provides utilities for tracking Celery task performance.
Implements Requirement 14.6: Track Celery task performance including queue depth, processing time, and failure rate.
"""

import time
from functools import wraps
from typing import Callable
from infrastructure.apm_config import PerformanceMonitor, APMConfig


class CeleryTaskTracker:
    """
    Utility class for tracking Celery task performance.
    
    Tracks:
    - Task execution time
    - Task success/failure rates
    - Queue depth
    """
    
    @staticmethod
    def track_task(task_name: str, duration_ms: float, success: bool, queue_depth: int = 0):
        """
        Track Celery task execution.
        
        Args:
            task_name: Name of the Celery task
            duration_ms: Task duration in milliseconds
            success: Whether the task succeeded
            queue_depth: Current queue depth
        """
        if not APMConfig.is_enabled():
            return
        
        PerformanceMonitor.track_celery_task(
            task_name=task_name,
            duration_ms=duration_ms,
            success=success,
            queue_depth=queue_depth
        )
    
    @staticmethod
    def get_queue_depth(queue_name: str = 'celery') -> int:
        """
        Get current queue depth for a Celery queue.
        
        Args:
            queue_name: Name of the queue
        
        Returns:
            Number of tasks in the queue
        """
        try:
            from celery import current_app
            
            # Get queue length from Redis
            inspect = current_app.control.inspect()
            active = inspect.active()
            reserved = inspect.reserved()
            
            if active and reserved:
                total = 0
                for worker_tasks in active.values():
                    total += len(worker_tasks)
                for worker_tasks in reserved.values():
                    total += len(worker_tasks)
                return total
            
            return 0
        except Exception:
            return 0


def track_celery_task(func: Callable) -> Callable:
    """
    Decorator to track Celery task performance.
    
    Example:
        @celery_app.task
        @track_celery_task
        def send_email(to, subject, body):
            # Task implementation
            pass
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not APMConfig.is_enabled():
            return func(*args, **kwargs)
        
        start_time = time.time()
        success = True
        
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            success = False
            raise
        finally:
            duration_ms = (time.time() - start_time) * 1000
            
            # Get queue depth
            queue_depth = CeleryTaskTracker.get_queue_depth()
            
            # Track task
            CeleryTaskTracker.track_task(
                task_name=func.__name__,
                duration_ms=duration_ms,
                success=success,
                queue_depth=queue_depth
            )
    
    return wrapper


# Export public API
__all__ = [
    'CeleryTaskTracker',
    'track_celery_task',
]
