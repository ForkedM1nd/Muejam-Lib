"""
URL configuration for MueJam Library project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.http import JsonResponse
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from infrastructure.metrics_views import metrics_view, metrics_json_view
from infrastructure.health_check_views import health_check_view, readiness_check_view, liveness_check_view


def root_status_view(request):
    response = JsonResponse({'status': 'ok'})
    hsts_value = f"max-age={getattr(settings, 'SECURE_HSTS_SECONDS', 31536000)}"
    if getattr(settings, 'SECURE_HSTS_INCLUDE_SUBDOMAINS', True):
        hsts_value += '; includeSubDomains'
    if getattr(settings, 'SECURE_HSTS_PRELOAD', True):
        hsts_value += '; preload'
    response['Strict-Transport-Security'] = hsts_value
    return response

urlpatterns = [
    path('django-admin/', admin.site.urls),  # Changed from 'admin/' to avoid namespace conflict
    
    # Monitoring endpoints
    path('metrics', metrics_view, name='metrics'),
    path('metrics/json', metrics_json_view, name='metrics-json'),
    path('health', health_check_view, name='health-check'),
    path('health/ready', readiness_check_view, name='readiness-check'),
    path('health/live', liveness_check_view, name='liveness-check'),
    path('', root_status_view, name='root-status'),
    
    # Versioned API endpoints
    path('', include('config.versioned_urls')),
    
    # API Documentation
    path('v1/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('v1/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
