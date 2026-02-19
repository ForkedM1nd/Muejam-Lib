from django.urls import path
from . import views

urlpatterns = [
    path('', views.notifications, name='notifications'),
    path('<str:id>/read', views.mark_read, name='mark_read'),
    path('read-all', views.mark_all_read, name='mark_all_read'),
    path('preferences', views.notification_preferences, name='notification_preferences'),
    path('preferences/update', views.update_notification_preferences, name='update_notification_preferences'),
]

# Device token management endpoints (mobile-backend-integration)
device_urlpatterns = [
    path('register', views.register_device, name='register_device'),
    path('unregister', views.unregister_device, name='unregister_device'),
    path('preferences', views.update_device_preferences, name='update_device_preferences'),
]
