# Moderation Queue Service

## Overview

The Moderation Queue Service manages the prioritization and sorting of content reports for moderators. It implements a sophisticated priority algorithm to ensure the most critical reports are reviewed first.

## Priority Algorithm

The priority score is calculated based on multiple factors:

### 1. Duplicate Reports (+10 per duplicate)
Reports for the same content from different users increase priority. This helps identify content that multiple users find problematic.

### 2. Automated Flags (+50)
Content flagged by automated detection systems (profanity, spam, hate speech) receives higher priority. *(To be implemented in Phase 3)*

### 3. Reporter Accuracy (+20 × accuracy)
The historical accuracy of the reporter affects priority:
- Accuracy = (valid reports) / (total resolved reports)
- Valid reports are those that resulted in action (not dismissed)
- New reporters receive a neutral score of 0.5

### 4. Content Type (+30 for user reports)
User reports are prioritized higher than content reports (stories, chapters, whispers) as they may indicate more serious issues.

### 5. Report Age (+2 per hour, capped at 100)
Older reports receive higher priority to ensure timely review. The age bonus is capped at 100 points to prevent extremely old reports from dominating the queue.

## Priority Levels

Priority scores are categorized into three levels:
- **High**: Score ≥ 100
- **Medium**: Score ≥ 50 and < 100
- **Low**: Score < 50

## API Endpoint

### GET /v1/reports/queue/

Returns all pending reports sorted by priority score (descending) and creation date (ascending).

**Response:**
```json
{
  "reports": [
    {
      "id": "report-uuid",
      "reporter_id": "user-uuid",
      "reporter_handle": "username",
      "content_type": "story|chapter|whisper|user",
      "content_id": "content-uuid",
      "reason": "Report reason text",
      "status": "PENDING",
      "created_at": "2024-01-01T00:00:00Z",
      "priority_score": 85.5,
      "priority_level": "medium"
    }
  ],
  "count": 1
}
```

## Usage

### In Views
```python
from apps.moderation.views import fetch_moderation_queue

async def my_view():
    queue = await fetch_moderation_queue()
    # Process queue...
```

### Direct Service Usage
```python
from apps.moderation.queue_service import ModerationQueueService

async def process_queue():
    async with ModerationQueueService() as queue_service:
        reports = await queue_service.get_queue()
        # Process reports...
```

## Requirements Satisfied

- **2.1**: Display all pending reports in moderation queue
- **2.2**: Sort reports by priority (high, medium, low) and creation date

## Testing

Run the moderation queue tests:
```bash
python -m pytest tests/backend/apps/moderation_tests.py::ModerationQueueTests -v
```

Tests verify:
- Queue returns only pending reports
- Reports are sorted by priority score
- Duplicate reports increase priority
- User reports have higher priority than content reports
- Older reports have higher priority
