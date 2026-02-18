# Content Filter Pipeline Integration

This document describes the integration of the content filter pipeline with content submission endpoints, implementing requirements 4.1-4.5 from the production readiness specification.

## Overview

The content filter pipeline is automatically applied to all user-generated content submissions:
- **Whispers**: Content is filtered before creation
- **Stories**: Title and blurb are filtered before creation
- **Chapters**: Title and content are filtered before creation

## Components

### ContentFilterIntegration Service

The `ContentFilterIntegration` service (`apps/moderation/content_filter_integration.py`) provides:

1. **Content Validation**: Runs all configured filters on content
2. **Error Generation**: Creates user-friendly error messages for blocked content
3. **Automated Reporting**: Creates high-priority reports for hate speech detection
4. **Flag Logging**: Records all automated detections in the database

### Integration Points

#### 1. Whisper Creation (`apps/whispers/views.py`)

**Endpoint**: `POST /v1/whispers`

**Filter Behavior**:
- Filters whisper content before creation
- Blocks submission if spam or high-severity profanity detected
- Creates automated report if hate speech detected
- Returns 400 error with specific reason if blocked

**Example Blocked Response**:
```json
{
  "error": {
    "code": "CONTENT_BLOCKED",
    "message": "Your content was blocked due to spam detection. Please remove excessive links, repeated text, or promotional content.",
    "flags": ["spam"]
  }
}
```

#### 2. Story Creation (`apps/stories/views.py`)

**Endpoint**: `POST /v1/stories`

**Filter Behavior**:
- Filters both title and blurb
- Blocks submission if either is flagged
- Creates automated reports for hate speech in either field
- Returns specific error indicating which field was blocked

**Example Blocked Response**:
```json
{
  "error": {
    "code": "CONTENT_BLOCKED",
    "message": "Story title blocked: Your content contains inappropriate language. Please revise your content and try again.",
    "flags": ["profanity"]
  }
}
```

#### 3. Chapter Creation (`apps/stories/views.py`)

**Endpoint**: `POST /v1/stories/{id}/chapters`

**Filter Behavior**:
- Filters both title and content
- Blocks submission if either is flagged
- Creates automated reports for hate speech in either field
- Returns specific error indicating which field was blocked

## Requirements Mapping

### Requirement 4.1: Profanity Filtering
- **Implementation**: `ProfanityFilter` checks content against configurable word lists
- **Behavior**: High-severity profanity blocks content; lower severity may be allowed based on sensitivity
- **User Feedback**: "Your content contains inappropriate language. Please revise your content and try again."

### Requirement 4.2: Spam Detection
- **Implementation**: `SpamDetector` checks for excessive links, repeated text, promotional content
- **Behavior**: Detected spam always blocks content submission
- **User Feedback**: "Your content was blocked due to spam detection. Please remove excessive links, repeated text, or promotional content."

### Requirement 4.3: Appropriate Error Messages
- **Implementation**: `ContentFilterIntegration._generate_error_message()` creates user-friendly messages
- **Behavior**: Different messages for different flag types (spam, profanity, malicious URLs)
- **User Experience**: Clear, actionable feedback without exposing filter internals

### Requirement 4.4: Hate Speech Auto-Reporting
- **Implementation**: `ContentFilterIntegration.handle_auto_actions()` creates reports
- **Behavior**: When hate speech detected, creates report with "system" user as reporter
- **Priority**: Reports are created with PENDING status for moderator review
- **Reason**: "Automated detection: hate speech, profanity" (lists all detected flags)

### Requirement 4.5: Automated Filtering Logs
- **Implementation**: `FilterConfigService.log_automated_flag()` records detections
- **Behavior**: All flags are logged to `AutomatedFlag` table with confidence scores
- **Data**: Stores content_type, content_id, flag_type, confidence, timestamp

## Filter Configuration

Filters use database configuration from `ContentFilterConfig` table:

```python
from apps.moderation.filter_config_service import FilterConfigService

# Get configured pipeline
config_service = FilterConfigService(db)
pipeline = await config_service.get_pipeline()

# Pipeline automatically uses database settings for:
# - Sensitivity levels (STRICT, MODERATE, PERMISSIVE)
# - Enabled/disabled filters
# - Custom whitelists and blacklists
```

## Error Handling

### Content Blocked (400 Bad Request)
```json
{
  "error": {
    "code": "CONTENT_BLOCKED",
    "message": "User-friendly error message",
    "flags": ["spam", "profanity"]
  }
}
```

### Internal Errors (500)
If filter integration fails, the endpoint returns a generic error and logs the exception. Content is **not** created if filtering fails.

## Automated Reports

When hate speech is detected:

1. **System User**: Reports are created with a "system" user (clerk_user_id: "system")
2. **Report Reason**: "Automated detection: hate speech, profanity"
3. **Status**: PENDING (requires moderator review)
4. **Content Reference**: Links to the specific content (story_id, chapter_id, or whisper_id)

**Note**: The system user is automatically created on first use if it doesn't exist.

## Testing

### Manual Testing

**Test Spam Detection**:
```bash
curl -X POST http://localhost:8000/v1/whispers \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Buy now! Click here! http://spam.com http://spam2.com http://spam3.com",
    "scope": "GLOBAL"
  }'
```

Expected: 400 error with spam message

**Test Profanity Detection**:
```bash
curl -X POST http://localhost:8000/v1/whispers \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "This contains fuck and shit",
    "scope": "GLOBAL"
  }'
```

Expected: 400 error with profanity message (if sensitivity is STRICT or MODERATE)

**Test Hate Speech Detection**:
```bash
curl -X POST http://localhost:8000/v1/whispers \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Content with hate speech keywords",
    "scope": "GLOBAL"
  }'
```

Expected: Content may be created, but automated report is generated

### Automated Tests

Run filter integration tests:
```bash
pytest apps/moderation/test_content_filter_integration.py -v
```

## Performance Considerations

1. **Synchronous Filtering**: Filters run synchronously during content creation
2. **Database Queries**: Each filter check may query `ContentFilterConfig` table
3. **Async Handling**: Uses `asyncio.run_until_complete()` to bridge sync/async boundary

**Optimization Opportunities**:
- Cache filter configurations in Redis
- Run filters asynchronously in background
- Batch automated flag logging

## Future Enhancements

1. **Machine Learning**: Replace keyword matching with ML-based detection
2. **Multi-language Support**: Detect content in multiple languages
3. **User Appeals**: Allow users to appeal blocked content
4. **Filter Analytics**: Track filter accuracy and false positive rates
5. **Graduated Responses**: Warn users before blocking (e.g., "Your content may contain...")

## Troubleshooting

### Content Not Being Filtered

1. Check filter configuration: `ContentFilterConfig` table
2. Verify filters are enabled: `enabled = true`
3. Check sensitivity settings: May be too permissive
4. Review logs for filter errors

### False Positives

1. Add terms to whitelist in `ContentFilterConfig`
2. Adjust sensitivity level (STRICT → MODERATE → PERMISSIVE)
3. Review and update filter word lists

### Automated Reports Not Created

1. Verify system user exists: `clerk_user_id = 'system'`
2. Check hate speech detection threshold
3. Review filter logs in `AutomatedFlag` table
4. Check application logs for errors

## Related Documentation

- [Content Filtering System](content-filters.md)
- [Filter Configuration Service](filter_config_service.py)
- [Moderation Dashboard](dashboard.md)
