from django.urls import path
from .views import (
    request_data_export,
    get_export_status,
    request_account_deletion,
    cancel_deletion_request,
    get_deletion_status,
    get_privacy_settings,
    update_privacy_settings,
    get_consent_history,
    withdraw_consent
)

urlpatterns = [
    # Data Export
    path('export/', request_data_export, name='request-data-export'),
    path('export/<str:export_id>/', get_export_status, name='get-export-status'),
    
    # Account Deletion
    path('delete/', request_account_deletion, name='request-account-deletion'),
    path('delete/<str:deletion_id>/', get_deletion_status, name='get-deletion-status'),
    path('delete/<str:deletion_id>/cancel/', cancel_deletion_request, name='cancel-deletion-request'),
    
    # Privacy Settings
    path('privacy/settings/', get_privacy_settings, name='get-privacy-settings'),
    path('privacy/settings/update/', update_privacy_settings, name='update-privacy-settings'),
    
    # Consent Management
    path('consent/history/', get_consent_history, name='get-consent-history'),
    path('consent/withdraw/', withdraw_consent, name='withdraw-consent'),
]
