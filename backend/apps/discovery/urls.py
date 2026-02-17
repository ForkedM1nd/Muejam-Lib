"""URL configuration for discovery app."""
from django.urls import path
from . import views

urlpatterns = [
    path('discover', views.discover_feed, name='discover_feed'),
]
