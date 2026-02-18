"""
Django views for exposing metrics to Prometheus.

This module provides HTTP endpoints for Prometheus to scrape metrics from
the Django application.

Requirements: 10.1, 10.2
"""

from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from .metrics_collector import get_metrics_collector


@csrf_exempt
@require_http_methods(["GET"])
def metrics_view(request):
    """
    Expose metrics in Prometheus text format.
    
    This endpoint is scraped by Prometheus to collect application metrics.
    
    Returns:
        HttpResponse with metrics in Prometheus text format
    
    Requirements: 10.1, 10.2
    """
    collector = get_metrics_collector()
    metrics_text = collector.export_prometheus_format()
    
    return HttpResponse(
        metrics_text,
        content_type='text/plain; version=0.0.4; charset=utf-8'
    )


@csrf_exempt
@require_http_methods(["GET"])
def metrics_json_view(request):
    """
    Expose metrics in JSON format for debugging and monitoring dashboards.
    
    Returns:
        JsonResponse with all metrics
    
    Requirements: 10.1, 10.2
    """
    from django.http import JsonResponse
    
    collector = get_metrics_collector()
    metrics = collector.get_all_metrics()
    
    return JsonResponse(metrics)


@csrf_exempt
@require_http_methods(["GET"])
def health_check_view(request):
    """
    Health check endpoint for load balancer.
    
    Checks:
    - Database connection
    - Redis/cache connection
    
    Returns:
        - HTTP 200 if all systems are healthy
        - HTTP 503 if any system is unhealthy
    
    Requirements: 28.2
    """
    from django.http import JsonResponse
    from django.db import connection
    from django.core.cache import cache
    from datetime import datetime, timezone
    
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'service': 'muejam-library-backend',
        'checks': {}
    }
    
    # Check database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        health_status['checks']['database'] = 'ok'
    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['checks']['database'] = f'error: {str(e)}'
    
    # Check Redis/cache connection
    try:
        cache.set('health_check', 'ok', 10)
        if cache.get('health_check') == 'ok':
            health_status['checks']['cache'] = 'ok'
        else:
            health_status['status'] = 'unhealthy'
            health_status['checks']['cache'] = 'error: cache read/write failed'
    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['checks']['cache'] = f'error: {str(e)}'
    
    # Return appropriate status code
    status_code = 200 if health_status['status'] == 'healthy' else 503
    
    return JsonResponse(health_status, status=status_code)
