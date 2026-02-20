"""URL configuration for highlights app."""
from django.urls import path
from . import views

urlpatterns = [
    # User highlight feed endpoint
    path('', views.user_highlights, name='user_highlights'),  # GET /v1/highlights
]
