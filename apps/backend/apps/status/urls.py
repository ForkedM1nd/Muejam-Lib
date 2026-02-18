"""
Status Page URL Configuration.

Implements Requirements 18.1-18.12.
"""
from django.urls import path
from .views import (
    StatusPageView,
    ComponentStatusView,
    IncidentHistoryView,
    IncidentManagementView,
    IncidentUpdateView,
    IncidentResolutionView,
    MaintenanceWindowView,
    StatusRSSFeedView,
    HealthCheckView
)

app_name = 'status'

urlpatterns = [
    # Public endpoints
    path('', StatusPageView.as_view(), name='status-page'),
    path('components/<str:component_id>', ComponentStatusView.as_view(), name='component-status'),
    path('incidents', IncidentHistoryView.as_view(), name='incident-history'),
    path('maintenance', MaintenanceWindowView.as_view(), name='maintenance'),
    path('rss', StatusRSSFeedView.as_view(), name='rss-feed'),
    
    # Admin endpoints
    path('incidents/create', IncidentManagementView.as_view(), name='create-incident'),
    path('incidents/<str:incident_id>/updates', IncidentUpdateView.as_view(), name='incident-update'),
    path('incidents/<str:incident_id>/resolve', IncidentResolutionView.as_view(), name='resolve-incident'),
    path('health-check', HealthCheckView.as_view(), name='health-check'),
]
