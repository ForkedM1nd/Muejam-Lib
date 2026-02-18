"""
URL configuration for MueJam Library project.
"""

from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from apps.stories import views as story_views
from apps.highlights import views as highlight_views
from infrastructure.metrics_views import metrics_view, metrics_json_view, health_check_view

urlpatterns = [
    path('django-admin/', admin.site.urls),  # Changed from 'admin/' to avoid namespace conflict
    
    # Monitoring endpoints
    path('metrics', metrics_view, name='metrics'),
    path('metrics/json', metrics_json_view, name='metrics-json'),
    path('health', health_check_view, name='health-check'),
    
    # API v1 endpoints
    path('v1/', include([
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
        path('admin/', include('apps.admin.urls')),
        path('status/', include('apps.status.urls')),
        path('', include('infrastructure.urls')),
    ])),
    
    # API Documentation
    path('v1/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('v1/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
