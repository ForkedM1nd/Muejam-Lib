"""
URL configuration for Two-Factor Authentication endpoints.

Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.7, 7.8
"""
from django.urls import path
from . import views

urlpatterns = [
    # 2FA setup and verification
    path('setup', views.setup_2fa, name='setup_2fa'),
    path('verify-setup', views.verify_setup_2fa, name='verify_setup_2fa'),
    
    # 2FA login verification
    path('verify', views.verify_2fa, name='verify_2fa'),
    
    # Backup code verification
    path('backup-code', views.verify_backup_code, name='verify_backup_code'),
    
    # 2FA status check
    path('status', views.check_2fa_status, name='check_2fa_status'),
    
    # 2FA management
    path('', views.disable_2fa, name='disable_2fa'),  # DELETE /api/auth/2fa
    path('regenerate-backup-codes', views.regenerate_backup_codes, name='regenerate_backup_codes'),
]
