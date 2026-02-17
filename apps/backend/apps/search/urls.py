"""URL configuration for search app."""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.search, name='search'),
    path('suggest', views.suggest, name='suggest'),
]
