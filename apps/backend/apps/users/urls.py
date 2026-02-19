from django.urls import path, include
from . import views
from . import profile_views
from . import mobile_session_views

urlpatterns = [
    path('test-auth/', views.test_auth, name='test-auth'),
    
    # User profile endpoints
    path('me/', views.me, name='me'),  # GET /v1/users/me, PUT /v1/users/me
    path('me/pin-story/', profile_views.pin_story, name='pin-story'),  # POST /v1/users/me/pin-story
    path('me/pin-story/<int:position>/', profile_views.unpin_story, name='unpin-story'),  # DELETE /v1/users/me/pin-story/{position}
    
    path('<str:handle>/', views.user_by_handle, name='user-by-handle'),  # GET /v1/users/{handle}
    path('<str:handle>/statistics/', profile_views.user_statistics, name='user-statistics'),  # GET /v1/users/{handle}/statistics
    path('<str:handle>/pinned/', profile_views.user_pinned_stories, name='user-pinned'),  # GET /v1/users/{handle}/pinned
    path('<str:handle>/badges/', profile_views.user_badges, name='user-badges'),  # GET /v1/users/{handle}/badges
    
    # Email verification endpoints
    path('email-verification/', include('apps.users.email_verification.urls')),
    
    # Two-Factor Authentication endpoints
    path('2fa/', include('apps.users.two_factor_auth.urls')),
    
    # Mobile session management endpoints
    path('sessions/create/', mobile_session_views.create_session, name='create-session'),  # POST /v1/users/sessions/create
    path('sessions/refresh/', mobile_session_views.refresh_token, name='refresh-token'),  # POST /v1/users/sessions/refresh
    path('sessions/revoke/', mobile_session_views.revoke_session, name='revoke-session'),  # POST /v1/users/sessions/revoke
    path('sessions/active/', mobile_session_views.get_active_sessions, name='active-sessions'),  # GET /v1/users/sessions/active
    path('sessions/revoke-all/', mobile_session_views.revoke_all_sessions, name='revoke-all-sessions'),  # POST /v1/users/sessions/revoke-all
]

