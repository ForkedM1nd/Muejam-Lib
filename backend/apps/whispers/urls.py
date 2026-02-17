"""URL configuration for whispers app."""
from django.urls import path
from . import views

urlpatterns = [
    # Whisper endpoints (note: these are prefixed with 'whispers/' in main urls.py)
    path('', views.whispers, name='whispers'),  # GET, POST /v1/whispers
    path('<str:whisper_id>', views.delete_whisper, name='delete_whisper'),  # DELETE /v1/whispers/{id}
    path('<str:whisper_id>/replies', views.whisper_replies, name='whisper_replies'),  # GET, POST /v1/whispers/{id}/replies
    path('<str:whisper_id>/like', views.like_whisper, name='like_whisper'),  # POST /v1/whispers/{id}/like
    path('<str:whisper_id>/unlike', views.unlike_whisper, name='unlike_whisper'),  # DELETE /v1/whispers/{id}/like (using unlike path)
]
