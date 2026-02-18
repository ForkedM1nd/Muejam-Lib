"""
APM External Service and Cache Tracking

This module provides utilities for tracking external service calls and cache operations.
Implements Requirements 14.4 and 14.5.
"""

import time
from functools import wraps
from typing import Callable, Optional
from infrastructure.apm_config import PerformanceMonitor, APMConfig


class ExternalServiceTracker:
    """
    Utility class for tracking external service calls.
    
    Implements Requirement 14.4: Track external service calls (AWS S3, Clerk, Resend).
    
    Tracks:
    - Service call duration
    - Success/failure rates
    - Service latency
    """
    
    @staticmethod
    def track_s3_operation(operation: str, duration_ms: float, success: bool):
        """
        Track AWS S3 operation.
        
        Args:
            operation: Operation name (upload, download, delete, etc.)
            duration_ms: Operation duration in milliseconds
            success: Whether the operation succeeded
        """
        if not APMConfig.is_enabled():
            return
        
        PerformanceMonitor.track_external_service(
            service='s3',
            operation=operation,
            duration_ms=duration_ms,
            success=success
        )
    
    @staticmethod
    def track_clerk_operation(operation: str, duration_ms: float, success: bool):
        """
        Track Clerk authentication operation.
        
        Args:
            operation: Operation name (verify_token, get_user, etc.)
            duration_ms: Operation duration in milliseconds
            success: Whether the operation succeeded
        """
        if not APMConfig.is_enabled():
            return
        
        PerformanceMonitor.track_external_service(
            service='clerk',
            operation=operation,
            duration_ms=duration_ms,
            success=success
        )
    
    @staticmethod
    def track_resend_operation(operation: str, duration_ms: float, success: bool):
        """
        Track Resend email operation.
        
        Args:
            operation: Operation name (send_email, etc.)
            duration_ms: Operation duration in milliseconds
            success: Whether the operation succeeded
        """
        if not APMConfig.is_enabled():
            return
        
        PerformanceMonitor.track_external_service(
            service='resend',
            operation=operation,
            duration_ms=duration_ms,
            success=success
        )
    
    @staticmethod
    def track_rekognition_operation(operation: str, duration_ms: float, success: bool):
        """
        Track AWS Rekognition operation.
        
        Args:
            operation: Operation name (detect_moderation_labels, etc.)
            duration_ms: Operation duration in milliseconds
            success: Whether the operation succeeded
        """
        if not APMConfig.is_enabled():
            return
        
        PerformanceMonitor.track_external_service(
            service='rekognition',
            operation=operation,
            duration_ms=duration_ms,
            success=success
        )


class CacheTracker:
    """
    Utility class for tracking cache operations.
    
    Implements Requirement 14.5: Track cache performance including hit rate, miss rate, and eviction rate.
    
    Tracks:
    - Cache hits and misses
    - Operation duration
    - Cache hit rate
    """
    
    @staticmethod
    def track_get(key: str, hit: bool, duration_ms: float = 0):
        """
        Track cache get operation.
        
        Args:
            key: Cache key
            hit: Whether it was a cache hit
            duration_ms: Operation duration in milliseconds
        """
        if not APMConfig.is_enabled():
            return
        
        PerformanceMonitor.track_cache_operation(
            operation='get',
            hit=hit,
            duration_ms=duration_ms
        )
    
    @staticmethod
    def track_set(key: str, duration_ms: float = 0):
        """
        Track cache set operation.
        
        Args:
            key: Cache key
            duration_ms: Operation duration in milliseconds
        """
        if not APMConfig.is_enabled():
            return
        
        PerformanceMonitor.track_cache_operation(
            operation='set',
            hit=False,  # Set operations are not hits
            duration_ms=duration_ms
        )
    
    @staticmethod
    def track_delete(key: str, duration_ms: float = 0):
        """
        Track cache delete operation.
        
        Args:
            key: Cache key
            duration_ms: Operation duration in milliseconds
        """
        if not APMConfig.is_enabled():
            return
        
        PerformanceMonitor.track_cache_operation(
            operation='delete',
            hit=False,
            duration_ms=duration_ms
        )


def track_external_service(service: str, operation: str):
    """
    Decorator to track external service calls.
    
    Args:
        service: Service name (s3, clerk, resend, rekognition)
        operation: Operation name
    
    Example:
        @track_external_service('s3', 'upload')
        def upload_file(file_path):
            # Upload implementation
            pass
    """
    def decorator(func: Callable) -> Callable:
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
                
                PerformanceMonitor.track_external_service(
                    service=service,
                    operation=operation,
                    duration_ms=duration_ms,
                    success=success
                )
        
        return wrapper
    return decorator


def track_cache_operation(operation: str):
    """
    Decorator to track cache operations.
    
    Args:
        operation: Operation type (get, set, delete)
    
    Example:
        @track_cache_operation('get')
        def get_from_cache(key):
            return cache.get(key)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not APMConfig.is_enabled():
                return func(*args, **kwargs)
            
            start_time = time.time()
            result = func(*args, **kwargs)
            duration_ms = (time.time() - start_time) * 1000
            
            # Determine if it was a hit (for get operations)
            hit = result is not None if operation == 'get' else False
            
            PerformanceMonitor.track_cache_operation(
                operation=operation,
                hit=hit,
                duration_ms=duration_ms
            )
            
            return result
        
        return wrapper
    return decorator


# Export public API
__all__ = [
    'ExternalServiceTracker',
    'CacheTracker',
    'track_external_service',
    'track_cache_operation',
]
