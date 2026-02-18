"""
URL configuration for email verification endpoints.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('send', views.send_verification_email, name='send_verification_email'),
    path('verify', views.verify_email, name='verify_email'),
    path('status', views.check_verification_status, name='check_verification_status'),
    path('resend', views.resend_verification, name='resend_verification'),
]
