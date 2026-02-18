# Privacy Settings Implementation

This document describes the privacy settings implementation for the MueJam Library platform.

## Overview

The privacy settings system allows users to control:
- Profile visibility
- Reading history visibility
- Analytics tracking opt-out
- Marketing email preferences
- Comment permissions on their content
- Follower approval requirements

## Requirements

Implements requirements 11.1-11.13 from the Production Readiness specification.

## Components

### 1. Database Model

**PrivacySettings** model in `prisma/schema.prisma`:
- `user_id`: Unique user identifier
- `profile_visibility`: PUBLIC, FOLLOWERS_ONLY, or PRIVATE
- `reading_history_visibility`: PUBLIC, FOLLOWERS_ONLY, or PRIVATE
- `analytics_opt_out`: Boolean flag for analytics tracking
- `marketing_emails`: Boolean flag for marketing email consent
- `comment_permissions`: ANYONE, FOLLOWERS, or DISABLED
- `follower_approval_required`: ANYONE or APPROVAL_REQUIRED

### 2. Service Layer

**PrivacySettingsService** (`privacy_settings_service.py`):
- `get_or_create_settings(user_id)`: Get or create default privacy settings
- `update_settings(user_id, updates)`: Update privacy settings
- `get_consent_history(user_id)`: Get user's consent history
- `withdraw_consent(user_id, consent_type)`: Withdraw consent for optional processing

### 3. Enforcement Layer

**PrivacyEnforcement** (`privacy_enforcement.py`):
- `can_view_profile(target_user_id, viewer_user_id)`: Check profile visibility
- `can_view_reading_history(target_user_id, viewer_user_id)`: Check reading history visibility
- `should_track_analytics(user_id)`: Check if analytics should be tracked
- `can_send_marketing_email(user_id)`: Check if marketing emails are allowed
- `can_comment_on_content(content_owner_id, commenter_id)`: Check comment permissions
- `requires_follower_approval(user_id)`: Check if follower approval is required
- `filter_profile_data(profile_data, target_user_id, viewer_user_id)`: Filter profile data based on privacy settings

### 4. Decorators

**Privacy Decorators** (`privacy_decorators.py`):
- `@require_profile_visibility`: Enforce profile visibility in views
- `@require_reading_history_visibility`: Enforce reading history visibility
- `@require_comment_permission`: Enforce comment permissions
- `@check_analytics_opt_out`: Check analytics opt-out status

## API Endpoints

### Get Privacy Settings
```
GET /api/gdpr/privacy/settings/
```

Returns the user's current privacy settings.

**Response:**
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "profile_visibility": "PUBLIC",
  "reading_history_visibility": "PRIVATE",
  "analytics_opt_out": false,
  "marketing_emails": true,
  "comment_permissions": "ANYONE",
  "follower_approval_required": "ANYONE",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### Update Privacy Settings
```
PUT /api/gdpr/privacy/settings/update/
```

Updates one or more privacy settings.

**Request Body:**
```json
{
  "profile_visibility": "FOLLOWERS_ONLY",
  "analytics_opt_out": true
}
```

**Response:**
```json
{
  "message": "Privacy settings updated",
  "settings": { ... }
}
```

### Get Consent History
```
GET /api/gdpr/consent/history/
```

Returns the user's consent history.

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
    }
  ]
}
```

### Withdraw Consent
```
POST /api/gdpr/consent/withdraw/
```

Withdraws consent for optional data processing.

**Request Body:**
```json
{
  "consent_type": "analytics"
}
```

Valid consent types: `analytics`, `marketing`

**Response:**
```json
{
  "message": "Consent withdrawn for analytics",
  "settings": { ... }
}
```

## Usage Examples

### Enforcing Profile Visibility in Views

```python
from apps.gdpr.privacy_decorators import require_profile_visibility

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_profile_visibility
async def get_user_profile(request, user_id):
    # This view will automatically check if the viewer
    # has permission to see the profile
    profile = await get_profile(user_id)
    return Response(profile)
```

### Checking Comment Permissions

```python
from apps.gdpr.privacy_enforcement import PrivacyEnforcement

async def create_comment(request, story_id):
    story = await get_story(story_id)
    content_owner_id = story['author_id']
    commenter_id = request.clerk_user_id
    
    can_comment = await PrivacyEnforcement.can_comment_on_content(
        content_owner_id, 
        commenter_id
    )
    
    if not can_comment:
        return Response(
            {'error': 'Comments are not allowed'},
            status=403
        )
    
    # Create comment...
```

### Respecting Analytics Opt-Out

```python
from apps.gdpr.privacy_enforcement import PrivacyEnforcement

async def track_page_view(user_id, page):
    should_track = await PrivacyEnforcement.should_track_analytics(user_id)
    
    if should_track:
        # Track analytics
        await analytics_service.track_event(user_id, 'page_view', page)
```

### Filtering Profile Data

```python
from apps.gdpr.privacy_enforcement import PrivacyEnforcement

async def get_user_profile(request, user_id):
    # Get full profile data
    profile = await fetch_full_profile(user_id)
    
    # Filter based on privacy settings
    viewer_id = request.clerk_user_id
    filtered_profile = await PrivacyEnforcement.filter_profile_data(
        profile, 
        user_id, 
        viewer_id
    )
    
    return Response(filtered_profile)
```

## Integration Points

### 1. User Profile Views
Apply `@require_profile_visibility` decorator to profile endpoints.

### 2. Reading History Views
Apply `@require_reading_history_visibility` decorator to reading history endpoints.

### 3. Comment Creation
Check `can_comment_on_content()` before allowing comment creation.

### 4. Follow Requests
Check `requires_follower_approval()` when processing follow requests.

### 5. Analytics Tracking
Check `should_track_analytics()` before recording analytics events.

### 6. Email Sending
Check `can_send_marketing_email()` before sending marketing emails.

## Privacy Setting Defaults

When a user first registers, default privacy settings are:
- `profile_visibility`: PUBLIC
- `reading_history_visibility`: PRIVATE
- `analytics_opt_out`: false (analytics enabled)
- `marketing_emails`: true (marketing emails enabled)
- `comment_permissions`: ANYONE
- `follower_approval_required`: ANYONE

## Immediate Effect (Requirement 11.8)

All privacy setting changes take effect immediately:
1. Settings are updated in the database
2. Subsequent API requests respect the new settings
3. No caching of privacy settings (always fetched fresh)

## Consent Recording (Requirement 11.10)

Every privacy setting change is recorded as a consent event:
- Linked to the active Privacy Policy document
- Includes timestamp
- Includes IP address (when available)
- Stored in UserConsent table

## Testing

Test the privacy settings implementation:

```bash
# Run privacy settings tests
pytest apps/gdpr/tests/test_privacy_settings.py -v
```

## Security Considerations

1. **Authorization**: All privacy settings endpoints require authentication
2. **Ownership**: Users can only modify their own privacy settings
3. **Validation**: All setting values are validated against allowed enums
4. **Audit Trail**: All changes are logged in consent history
5. **Immediate Effect**: No caching ensures settings are always current

## Future Enhancements

Potential future improvements:
1. Granular content-level privacy settings
2. Temporary privacy mode (e.g., "go private for 24 hours")
3. Privacy setting presets (e.g., "Maximum Privacy", "Public Profile")
4. Privacy setting recommendations based on user behavior
5. Bulk privacy actions (e.g., "make all my stories private")
