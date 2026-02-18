"""URL configuration for moderation app."""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.submit_report, name='submit_report'),
    path('queue/', views.get_moderation_queue, name='moderation_queue'),
    path('reports/<str:report_id>/', views.get_report_details, name='report_details'),
    path('actions/', views.take_moderation_action, name='moderation_action'),
    path('stats/', views.get_moderation_stats, name='moderation_stats'),
    path('moderators/', views.list_moderators, name='list_moderators'),
    path('moderators/assign/', views.assign_moderator_role, name='assign_moderator'),
    path('moderators/<str:moderator_id>/', views.remove_moderator_role, name='remove_moderator'),
    path('filters/', views.list_filter_configs, name='list_filter_configs'),
    path('filters/<str:filter_type>/', views.get_filter_config, name='get_filter_config'),
    path('filters/<str:filter_type>/update/', views.update_filter_config, name='update_filter_config'),
    path('nsfw/preference/', views.get_nsfw_preference, name='get_nsfw_preference'),
    path('nsfw/preference/update/', views.update_nsfw_preference, name='update_nsfw_preference'),
    path('nsfw/override/', views.override_nsfw_flag, name='override_nsfw_flag'),
]
