from django.urls import path
from . import views

urlpatterns = [
    path('test-auth/', views.test_auth, name='test-auth'),
    
    # User profile endpoints
    path('me/', views.me, name='me'),  # GET /v1/users/me, PUT /v1/users/me
    path('<str:handle>/', views.user_by_handle, name='user-by-handle'),  # GET /v1/users/{handle}
]
