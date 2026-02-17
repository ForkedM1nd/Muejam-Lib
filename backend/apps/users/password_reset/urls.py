"""
URL configuration for password reset endpoints.
"""
from django.urls import path
from . import views

urlpatterns = [
    # POST /api/forgot-password - Request password reset
    path('forgot-password/', views.forgot_password, name='forgot-password'),
    
    # GET /api/reset-password/:token - Validate token
    path('reset-password/<str:token>/', views.validate_token, name='validate-token'),
    
    # POST /api/reset-password - Complete password reset
    path('reset-password/', views.reset_password, name='reset-password'),
]
