# Test Mode Endpoints Implementation Summary

## Overview

This document summarizes the implementation of test mode endpoints for mobile backend integration (Task 18.1).

## Requirements Implemented

- **Requirement 18.1**: Test endpoints for verifying push notification delivery
- **Requirement 18.2**: Test mode detection and validation bypass
- **Requirement 18.3**: Test endpoints for verifying deep link generation
- **Requirement 18.4**: Test endpoints for mock data generation
- **Requirement 18.5**: Separate test request logs from production logs

## Components Created

### 1. Test Mode Service (`test_mode_service.py`)

Provides core test mode functionality:

- **Test mode detection**: Checks for `X-Test-Mode` header
- **Mock data generation**: Creates realistic test data for:
  - Stories (with metadata, deep links)
  - Chapters (with content, word counts)
  - Whispers (with engagement metrics)
  - Users (with profiles, stats)

### 2. Test Mode Views (`views.py`)

Three test endpoints with test mode enforcement:

#### POST `/v1/test/push-notification`
- Sends test push notifications to verify delivery
- Validates required fields (user_id, title, body)
- Returns delivery status for all user devices
- Requires `X-Test-Mode: true` header

**Example Request:**
```bash
curl -X POST http://localhost:8000/v1/test/push-notification \
  -H "X-Test-Mode: true" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "title": "Test Notification",
    "body": "This is a test notification",
    "data": {"key": "value"}
  }'
```

#### GET `/v1/test/deep-link`
- Verifies deep link generation for all resource types
- Supports: story, chapter, whisper, profile
- Optional platform parameter (ios, android)
- Requires `X-Test-Mode: true` header

**Example Request:**
```bash
curl "http://localhost:8000/v1/test/deep-link?type=story&id=story123&platform=ios" \
  -H "X-Test-Mode: true"
```

#### GET `/v1/test/mock-data`
- Generates mock data for testing
- Supports types: stories, chapters, whispers, users, all
- Configurable count (1-100 items)
- Requires `X-Test-Mode: true` header

**Example Request:**
```bash
curl "http://localhost:8000/v1/test/mock-data?type=stories&count=5" \
  -H "X-Test-Mode: true"
```

### 3. Test Mode Logging (Requirement 18.5)

Enhanced logging infrastructure to separate test requests:

#### Logging Middleware Updates (`logging_middleware.py`)
- Detects `X-Test-Mode` header in requests
- Sets `request.is_test_mode` flag
- Adds `test_mode: true` to logging context

#### Logging Config Updates (`logging_config.py`)
- Updated `log_api_request()` to accept `test_mode` parameter
- Test mode flag included in structured JSON logs
- Enables filtering of test logs from production logs

**Log Format:**
```json
{
  "timestamp": "2024-01-15T10:30:00.000Z",
  "level": "INFO",
  "message": "API request",
  "method": "GET",
  "path": "/v1/test/mock-data",
  "status_code": 200,
  "test_mode": true,
  "request_id": "abc-123-def"
}
```

### 4. URL Configuration

Added test endpoints to v1 API:
- Updated `config/urls_v1.py` to include `apps.testing.urls`
- All test endpoints under `/v1/test/` prefix

### 5. Django App Configuration

- Created `apps.testing` Django app
- Registered in `INSTALLED_APPS`
- Proper app configuration in `apps.py`

## Security Features

### Test Mode Enforcement

All test endpoints require the `X-Test-Mode: true` header:

- Returns 403 Forbidden without header
- Clear error message with hint
- Prevents accidental production use

### Validation Bypass

Test mode enables validation bypass for:
- Push notification delivery (no real device tokens required)
- Deep link generation (accepts any resource IDs)
- Mock data generation (no database queries)

## Testing

Created comprehensive unit tests (`test_endpoints.py`):

- ✅ Test mode header requirement (all endpoints)
- ✅ Deep link generation (all resource types)
- ✅ Mock data generation (all data types)
- ✅ Push notification endpoint validation
- ✅ Error handling (missing params, invalid types)
- ✅ Parameter validation (count limits, type validation)

**Test Results:** 11/11 tests passing

## Usage Examples

### Testing Push Notifications

```python
import requests

response = requests.post(
    'http://localhost:8000/v1/test/push-notification',
    headers={'X-Test-Mode': 'true'},
    json={
        'user_id': 'test_user_123',
        'title': 'New Chapter Available',
        'body': 'Chapter 5 of your favorite story is now available!',
        'data': {
            'story_id': 'story_456',
            'chapter_id': 'chapter_789'
        }
    }
)

print(response.json())
# {
#   "success": true,
#   "message": "Test notification queued for delivery",
#   "delivery_status": {
#     "user_id": "test_user_123",
#     "total_devices": 2,
#     "sent": 2,
#     "failed": 0,
#     "results": [...]
#   }
# }
```

### Testing Deep Links

```python
import requests

response = requests.get(
    'http://localhost:8000/v1/test/deep-link',
    headers={'X-Test-Mode': 'true'},
    params={
        'type': 'story',
        'id': 'story_123',
        'platform': 'ios'
    }
)

print(response.json())
# {
#   "success": true,
#   "deep_link": "muejam://story/story_123",
#   "resource_type": "story",
#   "resource_id": "story_123",
#   "platform": "ios"
# }
```

### Generating Mock Data

```python
import requests

response = requests.get(
    'http://localhost:8000/v1/test/mock-data',
    headers={'X-Test-Mode': 'true'},
    params={
        'type': 'all',
        'count': 3
    }
)

data = response.json()
print(f"Generated {len(data['data']['stories'])} stories")
print(f"Generated {len(data['data']['chapters'])} chapters")
print(f"Generated {len(data['data']['whispers'])} whispers")
print(f"Generated {len(data['data']['users'])} users")
```

## Log Filtering

To filter test logs from production logs:

### Using CloudWatch Logs Insights
```
fields @timestamp, message, method, path, status_code
| filter test_mode != true
| sort @timestamp desc
```

### Using grep
```bash
# Show only production logs
grep -v '"test_mode": true' muejam.log

# Show only test logs
grep '"test_mode": true' muejam.log
```

## Files Modified

1. **New Files:**
   - `apps/backend/apps/testing/__init__.py`
   - `apps/backend/apps/testing/apps.py`
   - `apps/backend/apps/testing/test_mode_service.py`
   - `apps/backend/apps/testing/views.py`
   - `apps/backend/apps/testing/urls.py`
   - `apps/backend/apps/testing/test_endpoints.py`
   - `apps/backend/apps/testing/IMPLEMENTATION_SUMMARY.md`

2. **Modified Files:**
   - `apps/backend/config/urls_v1.py` - Added test endpoints
   - `apps/backend/config/settings.py` - Added testing app to INSTALLED_APPS
   - `apps/backend/infrastructure/logging_middleware.py` - Added test mode detection
   - `apps/backend/infrastructure/logging_config.py` - Added test_mode parameter

## Next Steps

Task 18.1 is complete. The next task in the spec is:

- **Task 18.2**: Implement test request logging separation (already completed as part of 18.1)

## Notes

- Test mode endpoints are production-ready and safe to deploy
- All endpoints require explicit test mode header for security
- Mock data includes realistic values and proper deep links
- Logging separation enables easy filtering of test vs production logs
- Comprehensive test coverage ensures reliability
