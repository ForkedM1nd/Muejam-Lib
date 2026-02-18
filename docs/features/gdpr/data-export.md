# GDPR Data Export

This document describes the data export functionality for GDPR compliance.

## Overview

The data export feature allows users to download a comprehensive copy of all their data stored in the MueJam Library platform, fulfilling GDPR's right to data portability.

## Requirements

- **10.1**: Provide "Download My Data" feature accessible from user account settings
- **10.2**: Generate comprehensive JSON file containing all user data
- **10.3**: Include profile, stories, chapters, whispers, comments, likes, follows, reading history
- **10.4**: Send email notification with secure download link
- **10.5**: Expire download links after 7 days

## Architecture

### Components

1. **DataExportRequest Model**: Tracks export requests and their status
2. **DataExportService**: Generates comprehensive user data exports
3. **Celery Task**: Processes exports asynchronously
4. **Email Service**: Sends notifications when exports are ready
5. **S3 Storage**: Stores generated export files

### Flow

```
User Request → Create Export Request → Queue Celery Task
                                              ↓
                                    Generate Export Data
                                              ↓
                                    Upload to S3
                                              ↓
                                    Generate Presigned URL
                                              ↓
                                    Send Email Notification
```

## API Endpoints

### Request Data Export

```http
POST /api/gdpr/export/
Authorization: Bearer <token>
```

**Response:**
```json
{
  "message": "Data export request created",
  "export_request": {
    "id": "uuid",
    "user_id": "user_id",
    "status": "PENDING",
    "requested_at": "2024-01-15T10:30:00Z"
  }
}
```

### Get Export Status

```http
GET /api/gdpr/export/{export_id}/
Authorization: Bearer <token>
```

**Response (Pending):**
```json
{
  "id": "uuid",
  "user_id": "user_id",
  "status": "PENDING",
  "requested_at": "2024-01-15T10:30:00Z",
  "completed_at": null,
  "download_url": null,
  "expires_at": null,
  "error_message": null
}
```

**Response (Completed):**
```json
{
  "id": "uuid",
  "user_id": "user_id",
  "status": "COMPLETED",
  "requested_at": "2024-01-15T10:30:00Z",
  "completed_at": "2024-01-15T10:35:00Z",
  "download_url": "https://s3.amazonaws.com/...",
  "expires_at": "2024-01-22T10:35:00Z",
  "error_message": null
}
```

## Export Data Format

The export is a JSON file with the following structure:

```json
{
  "export_info": {
    "generated_at": "2024-01-15T10:35:00Z",
    "user_id": "user_id",
    "format_version": "1.0"
  },
  "profile": {
    "id": "user_id",
    "handle": "username",
    "display_name": "Display Name",
    "bio": "User bio",
    "created_at": "2023-01-01T00:00:00Z"
  },
  "stories": [
    {
      "id": "story_id",
      "title": "Story Title",
      "blurb": "Story description",
      "published": true,
      "created_at": "2023-06-01T00:00:00Z"
    }
  ],
  "chapters": [
    {
      "id": "chapter_id",
      "story_id": "story_id",
      "chapter_number": 1,
      "title": "Chapter Title",
      "content": "Chapter content...",
      "created_at": "2023-06-01T00:00:00Z"
    }
  ],
  "whispers": [...],
  "likes": [...],
  "follows": {
    "following": [...],
    "followers": [...]
  },
  "reading_progress": [...],
  "bookmarks": [...],
  "highlights": [...],
  "notifications": [...],
  "consent_records": [...]
}
```

## Data Included

The export includes:

1. **Profile Information**
   - Handle, display name, bio
   - Avatar reference
   - Account creation date
   - Age verification status

2. **Content**
   - All stories (published and unpublished)
   - All chapters with full content
   - All whispers (posts and replies)

3. **Social Data**
   - Whisper likes
   - Following list
   - Followers list

4. **Reading Data**
   - Reading progress for all stories
   - Bookmarks
   - Highlights

5. **System Data**
   - Notifications
   - Consent records

## Security Considerations

1. **Authentication**: All endpoints require authentication
2. **Authorization**: Users can only access their own export requests
3. **Presigned URLs**: Download links are temporary (7 days) and signed
4. **Encryption**: Data is encrypted in transit (HTTPS) and at rest (S3)
5. **Audit Logging**: All export requests are logged

## Processing Time

- Small accounts (<100 stories): 1-2 minutes
- Medium accounts (100-1000 stories): 2-5 minutes
- Large accounts (>1000 stories): 5-15 minutes

## Storage and Cleanup

- Export files are stored in S3 bucket: `muejam-data-exports`
- Files are organized by user: `exports/{user_id}/{export_id}.json`
- Presigned URLs expire after 7 days
- Files should be cleaned up after expiration (implement lifecycle policy)

## Email Notifications

When an export is ready, users receive an email with:
- Download link (presigned URL)
- Expiration date
- List of included data
- Security notice

## Error Handling

If export generation fails:
- Status is set to `FAILED`
- Error message is stored
- Task is retried up to 3 times with exponential backoff
- User should be notified to try again or contact support

## Celery Configuration

The export task requires Celery to be configured:

```python
# celery.py
from celery import Celery

app = Celery('muejam')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
```

## Environment Variables

Required environment variables:

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

## Testing

### Manual Testing

1. Request export:
```bash
curl -X POST https://api.muejam.com/api/gdpr/export/ \
  -H "Authorization: Bearer <token>"
```

2. Check status:
```bash
curl https://api.muejam.com/api/gdpr/export/{export_id}/ \
  -H "Authorization: Bearer <token>"
```

3. Download export:
```bash
curl -o my_data.json "<download_url>"
```

### Automated Testing

See `tests/test_data_export.py` for unit and integration tests.

## Monitoring

Monitor the following metrics:
- Export request rate
- Processing time
- Success/failure rate
- S3 storage usage
- Email delivery rate

## Compliance Notes

This implementation satisfies GDPR Article 20 (Right to Data Portability):
- Data is provided in a structured, commonly used format (JSON)
- Data is machine-readable
- Export includes all personal data
- Process is user-initiated and free of charge
- Data is delivered within a reasonable timeframe

## Future Enhancements

1. Support multiple export formats (CSV, XML)
2. Incremental exports (only new data since last export)
3. Scheduled automatic exports
4. Export compression for large datasets
5. Direct download without email (for immediate small exports)
