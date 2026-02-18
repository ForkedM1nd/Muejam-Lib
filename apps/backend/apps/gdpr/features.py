"""
GDPR Features Registry

This module explicitly declares all implemented GDPR compliance features.
"""

# GDPR Compliance Features
GDPR_FEATURES = {
    'data_export': {
        'implemented': True,
        'description': 'User data export functionality',
        'service': 'data_export_service.DataExportService',
        'endpoints': ['/api/gdpr/export', '/api/gdpr/export/{id}']
    },
    'data_deletion': {
        'implemented': True,
        'description': 'User data deletion functionality',
        'service': 'account_deletion_service.AccountDeletionService',
        'endpoints': ['/api/gdpr/delete', '/api/gdpr/delete/{id}/cancel']
    },
    'consent': {
        'implemented': True,
        'description': 'User consent management',
        'service': 'privacy_settings_service.PrivacySettingsService',
        'endpoints': ['/api/privacy/settings', '/api/consent/history', '/api/consent/withdraw']
    }
}


def is_feature_implemented(feature_name: str) -> bool:
    """Check if a GDPR feature is implemented."""
    return GDPR_FEATURES.get(feature_name, {}).get('implemented', False)


def get_all_features():
    """Get all GDPR features."""
    return GDPR_FEATURES
