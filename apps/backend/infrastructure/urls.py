"""
URL configuration for infrastructure endpoints.
"""

from django.urls import path
from apps.admin.audit_log_views import (
    get_audit_logs,
    detect_suspicious_patterns,
    trigger_suspicious_pattern_alert
)

urlpatterns = [
    # Audit log endpoints
    path('admin/audit-logs/', get_audit_logs, name='get-audit-logs'),
    path('admin/audit-logs/suspicious-patterns/', detect_suspicious_patterns, name='detect-suspicious-patterns'),
    path('admin/audit-logs/trigger-alert/', trigger_suspicious_pattern_alert, name='trigger-suspicious-pattern-alert'),
]
