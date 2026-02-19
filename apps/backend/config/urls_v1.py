"""
API v1 URL configuration.

Current stable API endpoints for both web and mobile clients.
"""

from django.urls import path, include
from apps.stories import views as story_views
from apps.highlights import views as highlight_views
from apps.notifications import urls as notification_urls
from apps.core import urls as core_urls

urlpatterns = [
    path('users/', include([
        path('', include('apps.users.urls')),
        # Social endpoints under users
        path('', include('apps.social.urls')),
    ])),
    # Password reset endpoints
    path('', include('apps.users.password_reset.urls')),
    path('stories/', include('apps.stories.urls')),
    # Chapter endpoints (direct access by chapter ID)
    path('chapters/<str:chapter_id>', story_views.get_chapter, name='get_chapter'),
    path('chapters/<str:chapter_id>/update', story_views.update_chapter, name='update_chapter'),
    path('chapters/<str:chapter_id>/delete', story_views.delete_chapter, name='delete_chapter'),
    path('chapters/<str:chapter_id>/publish', story_views.publish_chapter, name='publish_chapter'),
    # Reading progress endpoints
    path('chapters/<str:chapter_id>/progress', story_views.reading_progress, name='reading_progress'),  # GET, POST
    # Bookmark endpoints
    path('chapters/<str:chapter_id>/bookmarks', story_views.bookmarks, name='bookmarks'),  # GET, POST
    path('bookmarks/<str:bookmark_id>', story_views.delete_bookmark, name='delete_bookmark'),  # DELETE
    # Highlight endpoints
    path('chapters/<str:chapter_id>/highlights', highlight_views.highlights, name='highlights'),  # GET, POST
    path('highlights/<str:highlight_id>', highlight_views.delete_highlight, name='delete_highlight'),  # DELETE
    path('library/', include('apps.library.urls')),
    path('whispers/', include('apps.whispers.urls')),
    path('highlights/', include('apps.highlights.urls')),
    path('notifications/', include('apps.notifications.urls')),
    # Device token management endpoints (mobile-backend-integration)
    path('devices/', include(notification_urls.device_urlpatterns)),
    # Data synchronization endpoints (mobile-backend-integration)
    path('sync/', include(core_urls.sync_urlpatterns)),
    # Mobile configuration endpoints (mobile-backend-integration)
    path('config/', include(core_urls.config_urlpatterns)),
    path('discover/', include('apps.discovery.urls')),
    path('search/', include('apps.search.urls')),
    path('uploads/', include('apps.uploads.urls')),
    path('reports/', include('apps.moderation.urls')),
    path('legal/', include('apps.legal.urls')),
    path('gdpr/', include('apps.gdpr.urls')),
    path('health/', include('apps.core.urls')),
    path('onboarding/', include('apps.onboarding.urls')),
    path('help/', include('apps.help.urls')),
    path('analytics/', include('apps.analytics.urls')),
    path('app-admin/', include('apps.admin.urls')),  # Changed from 'admin/' to avoid namespace conflict
    path('status/', include('apps.status.urls')),
    path('security/', include('apps.security.urls')),  # Certificate pinning endpoints
    path('test/', include('apps.testing.urls')),  # Test mode endpoints
    path('', include('infrastructure.urls')),
]
