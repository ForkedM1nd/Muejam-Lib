# Moderation Dashboard API

This document describes the moderation dashboard endpoints implemented for Phase 2 of the Production Readiness spec.

## Overview

The moderation dashboard provides endpoints for moderators to review and act on content reports. These endpoints support the content moderation workflow including viewing pending reports, examining report details, taking moderation actions, and viewing moderation statistics.

## Requirements

These endpoints fulfill the following requirements:
- **2.1**: Display all pending reports in moderation queue
- **2.2**: Sort reports by priority (high, medium, low) and creation date
- **2.3**: Display reported content, reporter reason, content metadata, and reporter history
- **2.4**: Support actions: dismiss, warn, hide, delete, suspend
- **2.9**: Display moderator performance metrics

## Endpoints

### 1. GET /v1/reports/queue/

Get all pending reports sorted by priority and creation date.

**Authentication**: Required

**Response**:
```json
{
  "reports": [
    {
      "id": "uuid",
      "reporter_id": "uuid",
      "reporter_handle": "username",
      "content_type": "story|chapter|whisper|user",
      "content_id": "uuid",
      "reason": "Report reason text",
      "status": "PENDING",
      "created_at": "2024-01-01T00:00:00Z",
      "priority_score": 125.5,
      "priority_level": "high|medium|low"
    }
  ],
  "count": 10
}
```

**Priority Algorithm**:
- Duplicate reports: +10 per duplicate
- Automated flags: +50 if automated flag exists
- Reporter accuracy: +20 * accuracy (0-1)
- Content type: +30 for user reports
- Age: +2 per hour (capped at 100)

**Priority Levels**:
- High: score >= 100
- Medium: score >= 50
- Low: score < 50

### 2. GET /v1/reports/reports/{report_id}/

Get detailed information about a specific report.

**Authentication**: Required

**Parameters**:
- `report_id` (path): UUID of the report

**Response**:
```json
{
  "id": "uuid",
  "status": "PENDING|REVIEWED|RESOLVED",
  "reason": "Report reason text",
  "created_at": "2024-01-01T00:00:00Z",
  "reporter": {
    "id": "uuid",
    "handle": "username",
    "display_name": "Display Name",
    "total_reports": 5
  },
  "content": {
    "type": "story|chapter|whisper|user",
    "id": "uuid",
    "title": "Content Title",
    "author": {
      "id": "uuid",
      "handle": "author_handle",
      "display_name": "Author Name"
    },
    "created_at": "2024-01-01T00:00:00Z"
  },
  "moderation_actions": [
    {
      "id": "uuid",
      "action_type": "DISMISS|WARN|HIDE|DELETE|SUSPEND",
      "reason": "Action reason",
      "moderator_id": "uuid",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

**Error Responses**:
- `404 Not Found`: Report does not exist

### 3. POST /v1/reports/actions/

Take a moderation action on a report.

**Authentication**: Required

**Request Body**:
```json
{
  "report_id": "uuid",
  "action_type": "DISMISS|WARN|HIDE|DELETE|SUSPEND",
  "reason": "Reason for the action"
}
```

**Action Types**:
- `DISMISS`: Dismiss the report (no action taken on content)
- `WARN`: Warn the content author
- `HIDE`: Hide content from public view (soft delete)
- `DELETE`: Permanently delete content
- `SUSPEND`: Suspend user account

**Response**:
```json
{
  "id": "uuid",
  "report_id": "uuid",
  "moderator_id": "uuid",
  "action_type": "DISMISS",
  "reason": "Action reason",
  "created_at": "2024-01-01T00:00:00Z"
}
```

**Error Responses**:
- `400 Bad Request`: Missing required fields or invalid action type
- `404 Not Found`: Report does not exist

**Side Effects**:
- Report status is updated to `RESOLVED`
- For `HIDE` action: Content `deleted_at` field is set
- For `DELETE` action: Content is permanently removed from database
- Moderation action is recorded in audit log

### 4. GET /v1/reports/stats/

Get moderation performance metrics.

**Authentication**: Required

**Response**:
```json
{
  "pending_reports": 15,
  "resolved_reports": 234,
  "total_reports": 249,
  "average_response_time_seconds": 3600.5,
  "action_distribution": {
    "DISMISS": 120,
    "WARN": 45,
    "HIDE": 30,
    "DELETE": 15,
    "SUSPEND": 24
  }
}
```

**Metrics**:
- `pending_reports`: Number of reports with PENDING status
- `resolved_reports`: Number of reports with RESOLVED status
- `total_reports`: Total number of reports in the system
- `average_response_time_seconds`: Average time from report creation to first moderation action
- `action_distribution`: Count of each action type taken

## Usage Example

```python
import requests

# Get moderation queue
response = requests.get(
    'http://localhost:8000/v1/reports/queue/',
    headers={'Authorization': 'Bearer <token>'}
)
queue = response.json()

# Get report details
report_id = queue['reports'][0]['id']
response = requests.get(
    f'http://localhost:8000/v1/reports/reports/{report_id}/',
    headers={'Authorization': 'Bearer <token>'}
)
report = response.json()

# Take moderation action
response = requests.post(
    'http://localhost:8000/v1/reports/actions/',
    headers={'Authorization': 'Bearer <token>'},
    json={
        'report_id': report_id,
        'action_type': 'DISMISS',
        'reason': 'False positive - content is appropriate'
    }
)
action = response.json()

# Get moderation stats
response = requests.get(
    'http://localhost:8000/v1/reports/stats/',
    headers={'Authorization': 'Bearer <token>'}
)
stats = response.json()
```

## Database Models

### ModerationAction
```python
{
  'id': UUID,
  'report_id': UUID (FK to Report),
  'moderator_id': UUID,
  'action_type': Enum['DISMISS', 'WARN', 'HIDE', 'DELETE', 'SUSPEND'],
  'reason': Text,
  'created_at': DateTime,
  'metadata': JSON (optional)
}
```

### Report
```python
{
  'id': UUID,
  'reporter_id': UUID (FK to UserProfile),
  'reported_user_id': UUID (FK to UserProfile, nullable),
  'story_id': UUID (FK to Story, nullable),
  'chapter_id': UUID (FK to Chapter, nullable),
  'whisper_id': UUID (FK to Whisper, nullable),
  'reason': String,
  'status': Enum['PENDING', 'REVIEWED', 'RESOLVED'],
  'created_at': DateTime
}
```

## Future Enhancements

The following features are planned for future phases:

1. **Automated Content Filtering** (Phase 3)
   - Integration with profanity filters
   - Spam detection
   - Hate speech detection
   - Automated flag creation for high-priority reports

2. **Moderator Roles and Permissions** (Phase 2, Task 7)
   - Role-based access control
   - Permission checks for different action types
   - Moderator management endpoints

3. **Content Takedown Notifications** (Phase 2, Task 6.4)
   - Email notifications to content authors
   - Appeal process information

## Related Documentation

- [Moderation queue service](./queue.md) - Priority calculation algorithm
- [Production readiness review](../../operations/PRODUCTION_READINESS_REVIEW.md)
- [Deployment checklist](../../deployment/checklist.md)
