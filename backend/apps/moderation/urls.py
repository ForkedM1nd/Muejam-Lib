"""URL configuration for moderation app."""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.submit_report, name='submit_report'),
]
