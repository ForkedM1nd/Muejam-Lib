"""
Comprehensive Health Check Implementation

This module provides detailed health checks for all critical system components,
fixing the issue where health checks returned minimal information.
"""

import time
import logging
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache

logger = logging.getLogger(__name__)


def health_check_view(request):
    """
    Comprehensive health check endpoint for load balancers and monitoring.
    
    Checks:
    - Database connectivity
    - Cache (Redis) connectivity
    - Disk space
    - Overall system health
    
    Returns:
    - 200 OK if all checks pass
    - 503 Service Unavailable if any check fails
    """
    start_time = time.time()
    
    checks = {
        'database': check_database(),
        'cache': check_cache(),
        'disk': check_disk_space(),
    }
    
    # Calculate overall status
    all_healthy = all(
        check['status'] == 'healthy' 
        for check in checks.values()
    )
    
    # Determine HTTP status code
    status_code = 200 if all_healthy else 503
    
    # Build response
    response_data = {
        'status': 'healthy' if all_healthy else 'unhealthy',
        'timestamp': time.time(),
        'response_time_ms': (time.time() - start_time) * 1000,
        'checks': checks
    }
    
    # Log unhealthy status
    if not all_healthy:
        logger.error(
            f"Health check failed",
            extra={
                'checks': checks,
                'status': 'unhealthy'
            }
        )
    
    return JsonResponse(response_data, status=status_code)


def check_database() -> dict:
    """
    Check database connectivity and responsiveness.
    
    Returns:
        Dictionary with status and latency information
    """
    try:
        start_time = time.time()
        
        # Execute simple query
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
        
        latency_ms = (time.time() - start_time) * 1000
        
        if result and result[0] == 1:
            return {
                'status': 'healthy',
                'latency_ms': round(latency_ms, 2),
                'message': 'Database connection successful'
            }
        else:
            return {
                'status': 'unhealthy',
                'error': 'Unexpected query result',
                'latency_ms': round(latency_ms, 2)
            }
            
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            'status': 'unhealthy',
            'error': str(e),
            'message': 'Database connection failed'
        }


def check_cache() -> dict:
    """
    Check Redis/cache connectivity and responsiveness.
    
    Returns:
        Dictionary with status and latency information
    """
    try:
        start_time = time.time()
        
        # Test cache set/get
        test_key = f'health_check_{time.time()}'
        test_value = 'test_value'
        
        cache.set(test_key, test_value, 10)
        retrieved = cache.get(test_key)
        
        latency_ms = (time.time() - start_time) * 1000
        
        if retrieved == test_value:
            # Clean up test key
            cache.delete(test_key)
            
            return {
                'status': 'healthy',
                'latency_ms': round(latency_ms, 2),
                'message': 'Cache connection successful'
            }
        else:
            return {
                'status': 'unhealthy',
                'error': 'Cache value mismatch',
                'latency_ms': round(latency_ms, 2),
                'message': 'Cache read/write failed'
            }
            
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        return {
            'status': 'unhealthy',
            'error': str(e),
            'message': 'Cache connection failed'
        }


def check_disk_space() -> dict:
    """
    Check available disk space.
    
    Returns:
        Dictionary with status and disk usage information
    """
    try:
        import shutil
        
        stat = shutil.disk_usage('/')
        percent_used = (stat.used / stat.total) * 100
        
        # Determine status based on usage
        if percent_used > 90:
            status = 'unhealthy'
            message = 'Disk space critically low'
        elif percent_used > 80:
            status = 'degraded'
            message = 'Disk space running low'
        else:
            status = 'healthy'
            message = 'Disk space sufficient'
        
        return {
            'status': status,
            'percent_used': round(percent_used, 2),
            'total_gb': round(stat.total / (1024**3), 2),
            'used_gb': round(stat.used / (1024**3), 2),
            'free_gb': round(stat.free / (1024**3), 2),
            'message': message
        }
        
    except Exception as e:
        logger.error(f"Disk space check failed: {e}")
        return {
            'status': 'unknown',
            'error': str(e),
            'message': 'Disk space check failed'
        }


def readiness_check_view(request):
    """
    Readiness check for Kubernetes/container orchestration.
    
    Returns 200 if the application is ready to serve traffic.
    """
    # Check if critical components are ready
    checks = {
        'database': check_database(),
        'cache': check_cache(),
    }
    
    all_ready = all(
        check['status'] == 'healthy'
        for check in checks.values()
    )
    
    if all_ready:
        return JsonResponse({'status': 'ready'}, status=200)
    else:
        return JsonResponse(
            {'status': 'not_ready', 'checks': checks},
            status=503
        )


def liveness_check_view(request):
    """
    Liveness check for Kubernetes/container orchestration.
    
    Returns 200 if the application is alive (not deadlocked).
    """
    # Simple check that the application is responding
    return JsonResponse({'status': 'alive'}, status=200)


def https_status_view(request):
    """
    HTTPS configuration status endpoint.
    
    Returns current HTTPS enforcement and security configuration.
    Useful for security audits and compliance checks.
    
    Requirement: 6.4
    """
    from infrastructure.https_enforcement import get_https_status
    
    status = get_https_status()
    
    return JsonResponse({
        'https_configuration': status,
        'timestamp': time.time()
    }, status=200)
