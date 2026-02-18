"""
Search API URLs
"""

from django.urls import path
from .views import (
    SearchStoriesView,
    SearchAuthorsView,
    AutocompleteView,
    PopularSearchesView,
    TrackSearchClickView
)

urlpatterns = [
    path('stories', SearchStoriesView.as_view(), name='search-stories'),
    path('authors', SearchAuthorsView.as_view(), name='search-authors'),
    path('autocomplete', AutocompleteView.as_view(), name='search-autocomplete'),
    path('popular', PopularSearchesView.as_view(), name='search-popular'),
    path('track-click', TrackSearchClickView.as_view(), name='search-track-click'),
]
