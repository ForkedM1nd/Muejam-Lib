"""URL configuration for discovery app."""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.discover_feed, name='discover_feed'),
    
    # New discovery endpoints (Task 67)
    path('trending/', views.trending_stories_v2, name='trending-stories'),
    path('genre/<str:genre>/', views.stories_by_genre, name='stories-by-genre'),
    path('recommended/', views.recommended_stories, name='recommended-stories'),
    path('similar/<str:story_id>/', views.similar_stories, name='similar-stories'),
    path('new-and-noteworthy/', views.new_and_noteworthy, name='new-and-noteworthy'),
    path('staff-picks/', views.staff_picks, name='staff-picks'),
    path('rising-authors/', views.rising_authors, name='rising-authors'),
]
