"""
URL configuration for infrastructure endpoints.
"""

from django.urls import path
from apps.admin.audit_log_views import (
    get_audit_logs,
    detect_suspicious_patterns,
    trigger_suspicious_pattern_alert
)
from infrastructure.health_check_views import (
    health_check_view,
    readiness_check_view,
    liveness_check_view,
    https_status_view
)

urlpatterns = [
    # Health check endpoints
    path('health/', health_check_view, name='health-check'),
    path('health/ready/', readiness_check_view, name='readiness-check'),
    path('health/live/', liveness_check_view, name='liveness-check'),
    path('health/https/', https_status_view, name='https-status'),
    
    # Audit log endpoints
    path('admin/audit-logs/', get_audit_logs, name='get-audit-logs'),
    path('admin/audit-logs/suspicious-patterns/', detect_suspicious_patterns, name='detect-suspicious-patterns'),
    path('admin/audit-logs/trigger-alert/', trigger_suspicious_pattern_alert, name='trigger-suspicious-pattern-alert'),
]
