"""URL configuration for analytics app."""
from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.author_dashboard, name='author-dashboard'),
    path('stories/<str:story_id>/', views.story_analytics, name='story-analytics'),
    path('stories/<str:story_id>/export/', views.export_analytics, name='export-analytics'),
    path('follower-growth/', views.follower_growth, name='follower-growth'),
]
