"""
Versioned URL routing for API endpoints.

This module provides path-based API versioning to support independent
evolution of mobile and web clients while maintaining backward compatibility.
"""

from django.urls import path, include

urlpatterns = [
    path('api/', include('config.legacy_api_urls')),
    path('v1/', include('config.urls_v1')),
    path('v2/', include('config.urls_v2')),  # Future version placeholder
]
