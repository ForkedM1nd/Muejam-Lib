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
    Simple health check endpoint for monitoring.
    
    Returns:
        HttpResponse with status 200 if application is healthy
    """
    from django.http import JsonResponse
    
    return JsonResponse({
        'status': 'healthy',
        'service': 'muejam-library-backend'
    })
