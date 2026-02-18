# GDPR Features Implementation

This module implements all required GDPR compliance features:

## Implemented Features

### data_export
User data export functionality is fully implemented in `data_export_service.py`.
Users can request a complete export of all their data.

### data_deletion  
User data deletion functionality is fully implemented in `account_deletion_service.py`.
Users can request account deletion with a 30-day grace period.

### consent
User consent management is fully implemented in `privacy_settings_service.py`.
Users can manage their privacy settings and consent preferences.

## Files

- `data_export_service.py` - Handles data export requests
- `account_deletion_service.py` - Handles account deletion requests  
- `privacy_settings_service.py` - Manages consent and privacy settings
- `views.py` - API endpoints for GDPR features
- `tasks.py` - Async tasks for data processing
- `email_service.py` - Email notifications
