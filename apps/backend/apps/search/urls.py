"""
Search API URLs
"""

from django.urls import path
from .views import (
    LegacySearchView,
    LegacySuggestView,
    SearchStoriesView,
    SearchAuthorsView,
    AutocompleteView,
    PopularSearchesView,
    TrackSearchClickView
)

urlpatterns = [
    path('', LegacySearchView.as_view(), name='search-legacy'),
    path('suggest', LegacySuggestView.as_view(), name='search-suggest-legacy'),
    path('stories', SearchStoriesView.as_view(), name='search-stories'),
    path('authors', SearchAuthorsView.as_view(), name='search-authors'),
    path('autocomplete', AutocompleteView.as_view(), name='search-autocomplete'),
    path('popular', PopularSearchesView.as_view(), name='search-popular'),
    path('track-click', TrackSearchClickView.as_view(), name='search-track-click'),
]
