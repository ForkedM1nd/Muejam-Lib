"""URL configuration for stories app."""
from django.urls import path
from . import views

urlpatterns = [
    # Story endpoints (note: these are prefixed with 'stories/' in main urls.py)
    path('', views.stories_list_create, name='stories_list_create'),  # GET, POST /v1/stories
    path('<str:slug>', views.get_story_by_slug, name='get_story_by_slug'),  # GET /v1/stories/{slug}
    path('<str:story_id>/update', views.update_story, name='update_story'),  # PUT /v1/stories/{id}/update
    path('<str:story_id>/delete', views.delete_story, name='delete_story'),  # DELETE /v1/stories/{id}/delete
    path('<str:story_id>/publish', views.publish_story, name='publish_story'),  # POST /v1/stories/{id}/publish
    
    # Chapter endpoints
    path('<str:story_id>/chapters', views.list_chapters, name='list_chapters'),  # GET /v1/stories/{id}/chapters
    path('<str:story_id>/chapters/create', views.create_chapter, name='create_chapter'),  # POST /v1/stories/{id}/chapters/create
]

# Chapter endpoints need to be at root level since they're accessed via /v1/chapters/{id}
# These should be added to a separate chapters app or handled differently
# For now, we'll keep them here but they won't match the URL pattern in the design doc
