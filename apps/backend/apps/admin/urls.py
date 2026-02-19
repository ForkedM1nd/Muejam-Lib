"""
Admin Dashboard URL Configuration.

Implements Requirements 17.1-17.5.
"""
from django.urls import path
from .views import (
    AdminDashboardView,
    RealTimeMetricsView,
    BusinessMetricsView,
    SystemHealthView,
    ModerationMetricsView
)

app_name = 'app_admin'

urlpatterns = [
    # Main dashboard endpoint
    path('dashboard', AdminDashboardView.as_view(), name='dashboard'),
    
    # Metrics endpoints
    path('metrics/real-time', RealTimeMetricsView.as_view(), name='real-time-metrics'),
    path('metrics/business', BusinessMetricsView.as_view(), name='business-metrics'),
    path('metrics/moderation', ModerationMetricsView.as_view(), name='moderation-metrics'),
    
    # Health endpoint
    path('health', SystemHealthView.as_view(), name='system-health'),
]
