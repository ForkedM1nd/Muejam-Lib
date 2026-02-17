"""URL configuration for uploads app."""
from django.urls import path
from . import views

urlpatterns = [
    path('presign', views.presign_upload, name='presign_upload'),
]
