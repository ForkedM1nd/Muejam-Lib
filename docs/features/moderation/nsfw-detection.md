# NSFW Content Detection

This module provides NSFW (Not Safe For Work) content detection and management using AWS Rekognition.

## Components

### NSFWDetector (`nsfw_detector.py`)

Service for detecting NSFW content in images using AWS Rekognition's moderation labels API.

**Features:**
- Analyzes images from S3 URLs or raw bytes
- Detects explicit content with configurable confidence threshold (default: 80%)
- Returns detailed labels and confidence scores
- Handles errors gracefully with fallback responses

**Usage:**
```python
from apps.moderation.nsfw_detector import get_nsfw_detector

detector = get_nsfw_detector()

# Analyze image from S3 URL
result = detector.analyze_image('s3://bucket/path/to/image.jpg')

# Analyze image bytes
with open('image.jpg', 'rb') as f:
    result = detector.analyze_image_bytes(f.read())

# Result format:
# {
#     'is_nsfw': bool,
#     'confidence': float,  # 0-100
#     'labels': [
#         {
#             'name': str,
#             'confidence': float,
#             'parent_name': str
#         }
#     ],
#     'error': str  # Optional, only present if error occurred
# }
```

**Explicit Labels:**
The detector flags content as NSFW when confidence > 80% for these labels:
- Explicit Nudity
- Graphic Violence Or Gore
- Sexual Activity

### NSFWService (`nsfw_service.py`)

Service for managing NSFW flags and user content preferences.

**Features:**
- Create and update NSFW flags for content
- Track detection method (automatic, manual, user-marked)
- Store confidence scores and labels
- Manage user NSFW preferences
- Support moderator overrides
- Query flags for review

**Usage:**
```python
from apps.moderation.nsfw_service import get_nsfw_service
from prisma.enums import NSFWContentType, NSFWDetectionMethod, NSFWPreference

service = get_nsfw_service()

# Create NSFW flag from automatic detection
await service.create_nsfw_flag(
    content_type=NSFWContentType.IMAGE,
    content_id='image-uuid',
    is_nsfw=True,
    detection_method=NSFWDetectionMethod.AUTOMATIC,
    confidence=95.5,
    labels=[{'name': 'Explicit Nudity', 'confidence': 95.5}]
)

# Check if content is NSFW
is_nsfw = await service.is_content_nsfw(
    NSFWContentType.IMAGE,
    'image-uuid'
)

# Get user's NSFW preference
preference = await service.get_user_nsfw_preference('user-uuid')

# Update user's NSFW preference
await service.create_user_nsfw_preference(
    'user-uuid',
    NSFWPreference.HIDE_NSFW
)

# Moderator override
await service.override_nsfw_flag(
    content_type=NSFWContentType.IMAGE,
    content_id='image-uuid',
    is_nsfw=False,
    moderator_id='moderator-uuid'
)
```

## Database Models

### NSFWFlag

Stores NSFW detection results for content.

**Fields:**
- `id`: UUID primary key
- `content_type`: Enum (STORY, CHAPTER, WHISPER, IMAGE)
- `content_id`: UUID of the content
- `is_nsfw`: Boolean flag
- `confidence`: Float (0-100) from detection
- `labels`: JSON array of detected labels
- `detection_method`: Enum (AUTOMATIC, MANUAL, USER_MARKED)
- `flagged_by`: UUID of user who flagged (optional)
- `flagged_at`: Timestamp
- `reviewed`: Boolean indicating if moderator reviewed

### ContentPreference

Stores user preferences for NSFW content display.

**Fields:**
- `id`: UUID primary key
- `user_id`: UUID of the user (unique)
- `nsfw_preference`: Enum (SHOW_ALL, BLUR_NSFW, HIDE_NSFW)
- `updated_at`: Timestamp

## NSFW Preferences

Users can choose how NSFW content is displayed:

1. **SHOW_ALL**: Display all content without filtering
2. **BLUR_NSFW**: Show NSFW content but blur images (default)
3. **HIDE_NSFW**: Completely hide NSFW content from feeds and searches

## Integration Points

### Image Upload Flow

When a user uploads an image:

1. Image is uploaded to S3
2. NSFWDetector analyzes the image
3. If confidence > 80% for explicit labels, create NSFW flag
4. Store flag with detection results
5. Apply user's NSFW preference when displaying content

### Content Creation

Content creators can manually mark their content as NSFW:

```python
await service.mark_content_as_nsfw(
    content_type=NSFWContentType.STORY,
    content_id='story-uuid',
    user_id='creator-uuid',
    is_manual=False  # USER_MARKED
)
```

### Moderation Dashboard

Moderators can:
- Review automatic NSFW flags
- Override incorrect classifications
- View detection confidence and labels

```python
# Get flags needing review
flags = await service.get_nsfw_flags_for_review(limit=50)

# Override a flag
await service.override_nsfw_flag(
    content_type=NSFWContentType.IMAGE,
    content_id='image-uuid',
    is_nsfw=False,
    moderator_id='moderator-uuid'
)
```

## Configuration

Required environment variables:

```env
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1  # Optional, defaults to us-east-1
```

## Error Handling

The NSFWDetector handles errors gracefully:

- **AWS API errors**: Returns `is_nsfw=False` with error message
- **Invalid S3 URLs**: Returns error with details
- **Network errors**: Retries up to 3 times, then returns error

Always check for the `error` field in results:

```python
result = detector.analyze_image(image_url)
if 'error' in result:
    logger.error(f"NSFW detection failed: {result['error']}")
    # Handle error appropriately
```

## Testing

The module includes comprehensive error handling and logging for production use. For testing:

1. Mock AWS Rekognition responses
2. Test with various confidence thresholds
3. Verify flag creation and updates
4. Test user preference management
5. Verify moderator override functionality

## Requirements Validation

This implementation satisfies the following requirements:

- **8.1**: Images scanned using AWS Rekognition
- **8.2**: Content flagged when confidence > 80%
- **8.3**: Manual NSFW marking supported
- **8.5**: User NSFW preferences stored and managed
- **8.8**: Moderator override functionality
- **8.10**: All NSFW detection events logged

## Future Enhancements

Potential improvements:

1. Batch image analysis for efficiency
2. Custom ML models for platform-specific content
3. Text content analysis for NSFW text
4. Appeal process for incorrect flags
5. Analytics dashboard for NSFW trends
