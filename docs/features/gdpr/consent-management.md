# Consent Management Implementation

This document describes the consent management implementation for the MueJam Library platform.

## Overview

The consent management system allows users to:
- View their complete consent history
- Withdraw consent for optional data processing
- Track all privacy-related consent changes

## Requirements

Implements requirements 11.11-11.13 from the Production Readiness specification.

## Components

### 1. Consent History

**Service Method**: `PrivacySettingsService.get_consent_history(user_id)`

Retrieves all consent records for a user, including:
- Document type (TOS, Privacy Policy, etc.)
- Document version
- Consent timestamp
- IP address at time of consent

### 2. Consent Withdrawal

**Service Method**: `PrivacySettingsService.withdraw_consent(user_id, consent_type)`

Allows users to withdraw consent for optional data processing:
- **Analytics**: Sets `analytics_opt_out` to `True`
- **Marketing**: Sets `marketing_emails` to `False`

## API Endpoints

### Get Consent History

```
GET /api/gdpr/consent/history/
```

Returns the user's complete consent history.

**Authentication**: Required

**Response:**
```json
{
  "consents": [
    {
      "id": "uuid",
      "document_type": "PRIVACY",
      "document_version": "1.0",
      "consented_at": "2024-01-01T00:00:00Z",
      "ip_address": "192.168.1.1"
    },
    {
      "id": "uuid",
      "document_type": "TOS",
      "document_version": "1.0",
      "consented_at": "2024-01-01T00:00:00Z",
      "ip_address": "192.168.1.1"
    }
  ]
}
```

**Status Codes:**
- `200 OK`: Consent history retrieved successfully
- `401 Unauthorized`: User not authenticated
- `500 Internal Server Error`: Server error

### Withdraw Consent

```
POST /api/gdpr/consent/withdraw/
```

Withdraws consent for optional data processing.

**Authentication**: Required

**Request Body:**
```json
{
  "consent_type": "analytics"
}
```

**Valid Consent Types:**
- `analytics`: Withdraw consent for analytics tracking
- `marketing`: Withdraw consent for marketing emails

**Response:**
```json
{
  "message": "Consent withdrawn for analytics",
  "settings": {
    "id": "uuid",
    "user_id": "uuid",
    "profile_visibility": "PUBLIC",
    "reading_history_visibility": "PRIVATE",
    "analytics_opt_out": true,
    "marketing_emails": true,
    "comment_permissions": "ANYONE",
    "follower_approval_required": "ANYONE",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

**Status Codes:**
- `200 OK`: Consent withdrawn successfully
- `400 Bad Request`: Invalid consent type or missing consent_type
- `401 Unauthorized`: User not authenticated
- `500 Internal Server Error`: Server error

## Usage Examples

### Viewing Consent History

```python
import requests

# Get consent history
response = requests.get(
    'https://api.muejam.com/v1/gdpr/consent/history/',
    headers={'Authorization': 'Bearer <token>'}
)

consents = response.json()['consents']
for consent in consents:
    print(f"{consent['document_type']} v{consent['document_version']}")
    print(f"Consented at: {consent['consented_at']}")
```

### Withdrawing Analytics Consent

```python
import requests

# Withdraw analytics consent
response = requests.post(
    'https://api.muejam.com/v1/gdpr/consent/withdraw/',
    headers={'Authorization': 'Bearer <token>'},
    json={'consent_type': 'analytics'}
)

if response.status_code == 200:
    print("Analytics consent withdrawn")
    settings = response.json()['settings']
    print(f"Analytics opt-out: {settings['analytics_opt_out']}")
```

### Withdrawing Marketing Consent

```python
import requests

# Withdraw marketing consent
response = requests.post(
    'https://api.muejam.com/v1/gdpr/consent/withdraw/',
    headers={'Authorization': 'Bearer <token>'},
    json={'consent_type': 'marketing'}
)

if response.status_code == 200:
    print("Marketing consent withdrawn")
    settings = response.json()['settings']
    print(f"Marketing emails: {settings['marketing_emails']}")
```

## Consent Recording

### Automatic Recording

Consent is automatically recorded when:
1. User accepts Terms of Service during registration
2. User accepts Privacy Policy during registration
3. User updates cookie preferences
4. User changes privacy settings

Each consent record includes:
- User ID
- Document ID (links to specific version of legal document)
- Timestamp
- IP address
- User agent

### Consent Record Structure

```python
{
    'id': 'uuid',
    'user_id': 'uuid',
    'document_id': 'uuid',
    'consented_at': datetime,
    'ip_address': '192.168.1.1',
    'user_agent': 'Mozilla/5.0...'
}
```

## Data Processing After Consent Withdrawal

### Analytics Consent Withdrawal (Requirement 11.13)

When a user withdraws analytics consent:
1. `analytics_opt_out` is set to `True` immediately
2. All subsequent requests check this flag before tracking
3. No new analytics events are recorded
4. Existing analytics data is retained (as per GDPR requirements)
5. Processing stops within 24 hours (immediate in practice)

**Implementation:**
```python
from apps.gdpr.privacy_enforcement import PrivacyEnforcement

async def track_event(user_id, event_type, data):
    # Check if user has opted out
    should_track = await PrivacyEnforcement.should_track_analytics(user_id)
    
    if not should_track:
        logger.info(f"Analytics tracking skipped for user {user_id} (opted out)")
        return
    
    # Track the event
    await analytics_service.track(user_id, event_type, data)
```

### Marketing Consent Withdrawal (Requirement 11.13)

When a user withdraws marketing consent:
1. `marketing_emails` is set to `False` immediately
2. All email sending checks this flag
3. No new marketing emails are sent
4. Transactional emails (password reset, security alerts) continue
5. Processing stops within 24 hours (immediate in practice)

**Implementation:**
```python
from apps.gdpr.privacy_enforcement import PrivacyEnforcement

async def send_marketing_email(user_id, campaign_id):
    # Check if user has consented to marketing emails
    can_send = await PrivacyEnforcement.can_send_marketing_email(user_id)
    
    if not can_send:
        logger.info(f"Marketing email skipped for user {user_id} (no consent)")
        return
    
    # Send the email
    await email_service.send_marketing(user_id, campaign_id)
```

## Compliance Notes

### GDPR Compliance

1. **Right to Access (Article 15)**: Users can view their consent history
2. **Right to Withdraw Consent (Article 7.3)**: Users can withdraw consent at any time
3. **Processing Cessation**: Data processing stops within 24 hours of withdrawal
4. **Audit Trail**: All consent changes are logged with timestamps

### CCPA Compliance

1. **Right to Opt-Out**: Users can opt out of analytics tracking
2. **Right to Opt-Out of Sale**: Marketing consent withdrawal prevents data sharing
3. **Transparency**: Consent history provides clear record of all consents

## Testing

Test the consent management implementation:

```bash
# Run consent management tests
pytest apps/gdpr/tests/test_consent_management.py -v
```

## Integration with Other Systems

### Analytics System

Before tracking any analytics event:
```python
should_track = await PrivacyEnforcement.should_track_analytics(user_id)
if should_track:
    # Track event
```

### Email System

Before sending marketing emails:
```python
can_send = await PrivacyEnforcement.can_send_marketing_email(user_id)
if can_send:
    # Send email
```

### Privacy Settings

Consent withdrawal automatically updates privacy settings:
- Withdrawing analytics consent sets `analytics_opt_out = True`
- Withdrawing marketing consent sets `marketing_emails = False`

## Security Considerations

1. **Authentication Required**: All consent endpoints require authentication
2. **User Ownership**: Users can only view/modify their own consents
3. **Immutable Records**: Consent records cannot be modified or deleted
4. **Audit Trail**: All consent changes are logged
5. **IP Tracking**: IP addresses are recorded for legal compliance

## Future Enhancements

Potential future improvements:
1. Granular consent for different types of analytics
2. Consent expiration and renewal reminders
3. Consent export in machine-readable format
4. Consent delegation for minors (with parental consent)
5. Consent portability between platforms
