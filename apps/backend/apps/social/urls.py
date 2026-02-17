from django.urls import path
from . import views

urlpatterns = [
    # Follow endpoints (note: these will be prefixed with 'v1/' from main urls.py)
    path('<str:id>/follow', views.follow, name='follow'),
    path('<str:id>/followers', views.followers, name='followers'),
    path('<str:id>/following', views.following, name='following'),
    
    # Block endpoints
    path('<str:id>/block', views.block, name='block'),
]
