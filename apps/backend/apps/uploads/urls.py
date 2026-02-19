"""URL configuration for uploads app."""
from django.urls import path
from . import views

urlpatterns = [
    path('presign', views.presign_upload, name='presign_upload'),
    path('media', views.mobile_media_upload, name='mobile_media_upload'),
    path('chunked/init', views.chunked_upload_init, name='chunked_upload_init'),
    path('chunked/chunk', views.chunked_upload_chunk, name='chunked_upload_chunk'),
    path('chunked/complete', views.chunked_upload_complete, name='chunked_upload_complete'),
]
