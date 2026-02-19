"""
URL configuration for testing endpoints.

Requirements: 18.1, 18.2, 18.3, 18.4
"""

from django.urls import path
from . import views

urlpatterns = [
    # Test mode endpoints
    path('push-notification', views.test_push_notification, name='test_push_notification'),
    path('deep-link', views.test_deep_link, name='test_deep_link'),
    path('mock-data', views.test_mock_data, name='test_mock_data'),
]
