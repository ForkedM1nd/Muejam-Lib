# GDPR Compliance Module

This module implements GDPR (General Data Protection Regulation) compliance features for the MueJam Library platform, specifically focusing on the right to data portability (Article 20) and the right to erasure (Article 17).

## Overview

The GDPR module provides two main features:
1. **Data Export**: Users can download a comprehensive copy of all their data
2. **Account Deletion**: Users can request permanent deletion of their account with a 30-day grace period

## Requirements Satisfied

### Requirement 10: GDPR Data Export and Deletion

**Priority:** P0 (Blocking Launch)

#### Data Export (10.1-10.5)
- ✅ 10.1: Provide "Download My Data" feature accessible from user account settings
- ✅ 10.2: Generate comprehensive JSON file containing all user data
- ✅ 10.3: Include profile, stories, chapters, whispers, comments, likes, follows, reading history
- ✅ 10.4: Send email notification with secure download link
- ✅ 10.5: Expire download links after 7 days

#### Account Deletion (10.6-10.14)
- ✅ 10.6: Provide "Delete My Account" feature requiring password confirmation
- ✅ 10.7: Send confirmation email with cancellation link
- ✅ 10.8: Complete account deletion within 30 days unless user cancels
- ✅ 10.9: Remove all PII and replace content author with "Deleted User"
- ✅ 10.10: Retain content for 30 days in soft-deleted state
- ✅ 10.11: Permanently delete all user data after 30-day retention period
- ✅ 10.12: Log all data export and deletion requests for compliance audit
- ✅ 10.13: Send final confirmation email when deletion complete
- ✅ 10.14: Allow users to cancel deletion request within 30-day window

## Architecture

### Database Models

#### DataExportRequest
Tracks data export requests and their processing status.

```prisma
model DataExportRequest {
  id            String           @id @default(uuid())
  user_id       String
  status        DataExportStatus @default(PENDING)
  requested_at  DateTime         @default(now())
  completed_at  DateTime?
  download_url  String?
  expires_at    DateTime?
  error_message String?
}

enum DataExportStatus {
  PENDING
  PROCESSING
  COMPLETED
  FAILED
}
```

#### DeletionRequest
Tracks account deletion requests with 30-day retention period.

```prisma
model DeletionRequest {
  id                    String          @id @default(uuid())
  user_id               String
  requested_at          DateTime        @default(now())
  scheduled_deletion_at DateTime
  cancelled_at          DateTime?
  completed_at          DateTime?
  status                DeletionStatus  @default(PENDING)
}

enum DeletionStatus {
  PENDING
  CANCELLED
  COMPLETED
}
```

### Services

#### DataExportService
Generates comprehensive user data exports including:
- Profile information
- Stories and chapters
- Whispers and likes
- Follows (following and followers)
- Reading progress and bookmarks
- Highlights
- Notifications
- Consent records

#### AccountDeletionService
Manages the account deletion lifecycle:
- Creates deletion requests with 30-day retention
- Handles cancellation requests
- Performs account anonymization (soft delete)
- Executes permanent deletion (hard delete)
- Processes scheduled deletions

### Celery Tasks

#### generate_data_export
Asynchronously generates user data exports:
- Gathers all user data
- Creates JSON file
- Uploads to S3
- Generates presigned URL
- Sends email notification

#### process_scheduled_deletions
Daily task to process due deletions:
- Finds deletion requests past scheduled date
- Anonymizes accounts
- Permanently deletes data
- Sends final confirmation emails

### Email Notifications

#### Export Ready Email
Sent when data export is complete:
- Download link (presigned URL)
- Expiration date (7 days)
- List of included data
- Security notice

#### Deletion Confirmation Email
Sent when deletion is requested:
- Scheduled deletion date
- Cancellation link
- 30-day grace period information
- Warning about irreversibility

#### Deletion Complete Email
Sent after deletion is executed:
- Confirmation of deletion
- List of deleted data
- Note about preserved public content

## API Endpoints

### Data Export

```
POST   /api/gdpr/export/              - Request data export
GET    /api/gdpr/export/{export_id}/  - Get export status
```

### Account Deletion

```
POST   /api/gdpr/delete/                      - Request account deletion
GET    /api/gdpr/delete/{deletion_id}/        - Get deletion status
POST   /api/gdpr/delete/{deletion_id}/cancel/ - Cancel deletion request
```

## Data Export Format

The export is a JSON file with the following structure:

```json
{
  "export_info": {
    "generated_at": "2024-01-15T10:35:00Z",
    "user_id": "user_id",
    "format_version": "1.0"
  },
  "profile": { ... },
  "stories": [ ... ],
  "chapters": [ ... ],
  "whispers": [ ... ],
  "likes": [ ... ],
  "follows": {
    "following": [ ... ],
    "followers": [ ... ]
  },
  "reading_progress": [ ... ],
  "bookmarks": [ ... ],
  "highlights": [ ... ],
  "notifications": [ ... ],
  "consent_records": [ ... ]
}
```

## Deletion Process

### Two-Phase Deletion

1. **Phase 1: Soft Delete (Anonymization)**
   - Anonymize profile (display name, bio, avatar)
   - Delete sensitive data (2FA, API keys, tokens)
   - Preserve content with "Deleted User" author
   - Executed on scheduled deletion date

2. **Phase 2: Hard Delete (Permanent Deletion)**
   - Delete all user data
   - Delete stories, chapters, whispers
   - Delete social connections
   - Delete reading history
   - Executed immediately after anonymization

### 30-Day Grace Period

- Users can cancel deletion anytime during 30 days
- Cancellation restores normal account status
- After 30 days, deletion is irreversible

## Security Considerations

1. **Authentication**: All endpoints require authentication
2. **Authorization**: Users can only access their own requests
3. **Password Confirmation**: Required for deletion requests
4. **Presigned URLs**: Temporary download links (7 days)
5. **Encryption**: Data encrypted in transit and at rest
6. **Audit Logging**: All requests logged for compliance

## Configuration

### Environment Variables

```env
# AWS S3
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
DATA_EXPORT_BUCKET=muejam-data-exports

# Email
RESEND_API_KEY=your_resend_key

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### Celery Beat Schedule

```python
from celery.schedules import crontab

CELERYBEAT_SCHEDULE = {
    'process-scheduled-deletions': {
        'task': 'apps.gdpr.tasks.process_scheduled_deletions',
        'schedule': crontab(hour=2, minute=0),  # Run at 2 AM daily
    },
}
```

## Usage Examples

### Request Data Export

```bash
curl -X POST https://api.muejam.com/api/gdpr/export/ \
  -H "Authorization: Bearer <token>"
```

### Check Export Status

```bash
curl https://api.muejam.com/api/gdpr/export/{export_id}/ \
  -H "Authorization: Bearer <token>"
```

### Request Account Deletion

```bash
curl -X POST https://api.muejam.com/api/gdpr/delete/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"password": "user_password"}'
```

### Cancel Deletion

```bash
curl -X POST https://api.muejam.com/api/gdpr/delete/{deletion_id}/cancel/ \
  -H "Authorization: Bearer <token>"
```

## Monitoring

### Key Metrics

- Export request rate
- Export processing time
- Export success/failure rate
- Deletion request rate
- Deletion cancellation rate
- Scheduled deletion success rate

### Alerts

- Failed export generation
- Failed scheduled deletion
- High error rate
- S3 storage issues
- Email delivery failures

## Testing

### Unit Tests

Test individual components:
- DataExportService methods
- AccountDeletionService methods
- Email service functions

### Integration Tests

Test complete workflows:
- Export request to download
- Deletion request to completion
- Cancellation flow

### Manual Testing

See individual README files:
- [Data Export Testing](./data-export.md#testing)
- [Account Deletion Testing](./account-deletion.md#testing)

## Compliance Checklist

- ✅ Data export in machine-readable format (JSON)
- ✅ Comprehensive data inclusion
- ✅ Reasonable processing time (<15 minutes)
- ✅ Secure delivery mechanism (presigned URLs)
- ✅ User-initiated process
- ✅ Free of charge
- ✅ 30-day grace period for deletion
- ✅ Complete PII removal
- ✅ Audit trail maintained
- ✅ Email notifications at each step
- ✅ Cancellation capability

## Legal Compliance

### GDPR Articles Satisfied

- **Article 15**: Right of access by the data subject
- **Article 17**: Right to erasure ('right to be forgotten')
- **Article 20**: Right to data portability

### CCPA Compliance

- Right to know what personal information is collected
- Right to delete personal information
- Right to opt-out of sale of personal information

## Future Enhancements

1. **Data Export**
   - Multiple export formats (CSV, XML)
   - Incremental exports
   - Scheduled automatic exports
   - Export compression
   - Direct download for small exports

2. **Account Deletion**
   - Immediate deletion option
   - Selective data deletion
   - Longer grace periods (90 days)
   - Account reactivation
   - Deletion reason tracking

3. **General**
   - Data portability to other platforms
   - Automated compliance reporting
   - GDPR dashboard for administrators
   - Data retention policy enforcement

## Documentation

- [Data Export README](./data-export.md) - Detailed data export documentation
- [Account Deletion README](./account-deletion.md) - Detailed deletion documentation

## Support

For issues or questions:
1. Check the documentation in this directory
2. Review the requirements document
3. Contact the development team
4. Consult with legal/compliance team for policy questions

## License

This module is part of the MueJam Library platform and follows the same license.
