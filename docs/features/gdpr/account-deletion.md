# GDPR Account Deletion

This document describes the account deletion functionality for GDPR compliance.

## Overview

The account deletion feature allows users to request permanent deletion of their account and all associated data, fulfilling GDPR's right to erasure (right to be forgotten).

## Requirements

- **10.6**: Provide "Delete My Account" feature requiring password confirmation
- **10.7**: Send confirmation email with cancellation link
- **10.8**: Complete account deletion within 30 days unless user cancels
- **10.9**: Remove all PII and replace content author with "Deleted User"
- **10.10**: Retain content for 30 days in soft-deleted state
- **10.11**: Permanently delete all user data after 30-day retention period
- **10.13**: Send final confirmation email when deletion complete
- **10.14**: Allow users to cancel deletion request within 30-day window

## Architecture

### Two-Phase Deletion Process

The deletion process follows a two-phase approach:

1. **Soft Delete (Anonymization)**: Immediate removal of PII while retaining content
2. **Hard Delete (Permanent)**: Complete removal of all data after 30-day retention

### Components

1. **DeletionRequest Model**: Tracks deletion requests with 30-day retention period
2. **AccountDeletionService**: Manages deletion lifecycle
3. **Celery Task**: Processes scheduled deletions daily
4. **Email Service**: Sends confirmation and completion notifications

### Flow

```
User Request → Password Confirmation → Create Deletion Request
                                              ↓
                                    Send Confirmation Email
                                              ↓
                                    30-Day Waiting Period
                                              ↓
                                    (User can cancel anytime)
                                              ↓
                                    Scheduled Deletion Date
                                              ↓
                                    Anonymize Account (Soft Delete)
                                              ↓
                                    Permanently Delete (Hard Delete)
                                              ↓
                                    Send Final Confirmation Email
```

## API Endpoints

### Request Account Deletion

```http
POST /api/gdpr/delete/
Authorization: Bearer <token>
Content-Type: application/json

{
  "password": "user_password"
}
```

**Response:**
```json
{
  "message": "Account deletion request created",
  "deletion_request": {
    "id": "uuid",
    "user_id": "user_id",
    "status": "PENDING",
    "requested_at": "2024-01-15T10:30:00Z",
    "scheduled_deletion_at": "2024-02-14T10:30:00Z"
  }
}
```

### Get Deletion Status

```http
GET /api/gdpr/delete/{deletion_id}/
Authorization: Bearer <token>
```

**Response:**
```json
{
  "id": "uuid",
  "user_id": "user_id",
  "status": "PENDING",
  "requested_at": "2024-01-15T10:30:00Z",
  "scheduled_deletion_at": "2024-02-14T10:30:00Z",
  "cancelled_at": null,
  "completed_at": null
}
```

### Cancel Deletion Request

```http
POST /api/gdpr/delete/{deletion_id}/cancel/
Authorization: Bearer <token>
```

**Response:**
```json
{
  "message": "Account deletion request cancelled",
  "deletion_request": {
    "id": "uuid",
    "user_id": "user_id",
    "status": "CANCELLED",
    "requested_at": "2024-01-15T10:30:00Z",
    "scheduled_deletion_at": "2024-02-14T10:30:00Z",
    "cancelled_at": "2024-01-20T14:00:00Z",
    "completed_at": null
  }
}
```

## Deletion Phases

### Phase 1: Soft Delete (Anonymization)

When the scheduled deletion date arrives, the account is anonymized:

**Profile Changes:**
- `display_name` → "Deleted User"
- `bio` → null
- `avatar_key` → null
- `handle` → "deleted_{user_id_prefix}"

**Sensitive Data Deleted:**
- TOTP devices (2FA)
- Backup codes
- API keys
- Email verification tokens
- Authentication events (optional)

**Content Preserved:**
- Stories remain visible with author "Deleted User"
- Chapters remain accessible
- Comments/whispers remain for context
- This preserves community discussions and story integrity

### Phase 2: Hard Delete (Permanent Deletion)

After anonymization, all data is permanently deleted:

**Deleted Data:**
- User profile
- All stories and chapters
- All whispers and comments
- Whisper likes
- Follows (as follower and following)
- Reading progress
- Bookmarks
- Highlights
- Notifications
- Reports made by user
- Consent records

**Note:** In production, you may want to keep stories/chapters with anonymized author instead of deleting them entirely.

## Deletion Statuses

- **PENDING**: Deletion scheduled, waiting for 30-day period
- **CANCELLED**: User cancelled the deletion request
- **COMPLETED**: Deletion has been executed

## Scheduled Deletion Processing

A Celery task runs daily to process scheduled deletions:

```python
# Schedule in celerybeat
from celery.schedules import crontab

CELERYBEAT_SCHEDULE = {
    'process-scheduled-deletions': {
        'task': 'apps.gdpr.tasks.process_scheduled_deletions',
        'schedule': crontab(hour=2, minute=0),  # Run at 2 AM daily
    },
}
```

## Email Notifications

### Confirmation Email (Immediate)

Sent when deletion is requested:
- Scheduled deletion date
- Cancellation link
- What happens during 30-day period
- Warning that action is irreversible after 30 days

### Final Confirmation Email (After Deletion)

Sent after deletion is complete:
- Confirmation that account is deleted
- List of what was deleted
- Note about preserved public content
- Thank you message

## Security Considerations

1. **Password Confirmation**: Required to prevent accidental deletions
2. **30-Day Grace Period**: Allows users to change their mind
3. **Email Notifications**: Keeps users informed at each step
4. **Audit Logging**: All deletion requests are logged
5. **Irreversible**: After 30 days, deletion cannot be undone

## Cancellation

Users can cancel deletion at any time during the 30-day period:
- Via cancellation link in email
- Via account settings
- Via API endpoint

Once cancelled, the deletion request status changes to CANCELLED and no deletion occurs.

## Data Retention

- **30-Day Soft Delete**: Account is anonymized but data retained
- **After 30 Days**: All data permanently deleted
- **Audit Logs**: Deletion requests logged indefinitely for compliance

## Compliance Notes

This implementation satisfies GDPR Article 17 (Right to Erasure):
- User-initiated deletion process
- Reasonable timeframe (30 days)
- Complete removal of personal data
- Notification of deletion completion
- Ability to cancel before execution
- Audit trail for compliance

## Error Handling

If deletion processing fails:
- Error is logged with details
- Deletion request remains PENDING
- Will be retried on next scheduled run
- Administrators should be alerted for manual intervention

## Testing

### Manual Testing

1. Request deletion:
```bash
curl -X POST https://api.muejam.com/api/gdpr/delete/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"password": "user_password"}'
```

2. Check status:
```bash
curl https://api.muejam.com/api/gdpr/delete/{deletion_id}/ \
  -H "Authorization: Bearer <token>"
```

3. Cancel deletion:
```bash
curl -X POST https://api.muejam.com/api/gdpr/delete/{deletion_id}/cancel/ \
  -H "Authorization: Bearer <token>"
```

### Testing Scheduled Deletion

To test the scheduled deletion process:

```python
# Run the task manually
from apps.gdpr.tasks import process_scheduled_deletions
result = process_scheduled_deletions.delay()
```

## Monitoring

Monitor the following metrics:
- Deletion request rate
- Cancellation rate
- Successful deletion rate
- Failed deletion attempts
- Time to completion

## Best Practices

1. **Backup Before Deletion**: Consider creating a final backup before permanent deletion
2. **Notify Dependent Systems**: If user data is replicated elsewhere, ensure those systems are notified
3. **Content Preservation**: Consider keeping public content (stories) with anonymized author
4. **Legal Hold**: Check for legal holds before deleting (e.g., ongoing investigations)
5. **Audit Trail**: Maintain comprehensive logs of all deletion activities

## Future Enhancements

1. Immediate deletion option (skip 30-day period)
2. Selective deletion (delete specific data types)
3. Export before delete (automatic data export)
4. Deletion reason tracking
5. Account reactivation within grace period
6. Soft delete for longer periods (e.g., 90 days)
