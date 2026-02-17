"""URL configuration for library app."""
from django.urls import path
from . import views

urlpatterns = [
    # Library endpoint
    path('', views.get_library, name='get_library'),  # GET /v1/library
    
    # Shelf endpoints (note: these are prefixed with 'library/' in main urls.py)
    path('shelves', views.shelves_list_create, name='shelves_list_create'),  # GET, POST /v1/library/shelves
    path('shelves/<str:shelf_id>', views.update_shelf, name='update_shelf'),  # PUT /v1/library/shelves/{id}
    path('shelves/<str:shelf_id>/delete', views.delete_shelf, name='delete_shelf'),  # DELETE /v1/library/shelves/{id}/delete
    
    # ShelfItem endpoints
    path('shelves/<str:shelf_id>/items', views.add_story_to_shelf, name='add_story_to_shelf'),  # POST /v1/library/shelves/{id}/items
    path('shelves/<str:shelf_id>/items/<str:story_id>', views.remove_story_from_shelf, name='remove_story_from_shelf'),  # DELETE /v1/library/shelves/{id}/items/{story_id}
]
