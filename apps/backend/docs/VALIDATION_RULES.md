# Input Validation Rules

This document describes the input validation rules implemented across all API endpoints.

## Overview

All API endpoints use Django REST Framework (DRF) serializers for input validation. The custom exception handler ensures consistent error responses across all endpoints.

## Error Response Format

All validation errors return a consistent JSON format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable error message",
    "details": {
      "field_name": ["Error message for this field"]
    }
  }
}
```

## Validation Rules by Endpoint

### Upload Endpoints

#### POST /api/uploads/presign

**Serializer**: `PresignUploadRequestSerializer`

**Required Fields**:
- `type`: Upload type (choices: 'avatar', 'cover', 'whisper_media')
- `content_type`: MIME type (choices: 'image/jpeg', 'image/png', 'image/webp', 'image/gif')

**Validation Rules**:
- `type` must be one of the allowed upload types
- `content_type` must be one of the allowed image formats
- Both fields are required

**Example Valid Request**:
```json
{
  "type": "avatar",
  "content_type": "image/jpeg"
}
```

**Example Error Response**:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": {
      "type": ["Upload type must be one of: avatar, cover, whisper_media"]
    }
  }
}
```

---

### Discovery Endpoints

#### GET /api/discover

**Serializer**: `DiscoverFeedQuerySerializer`

**Query Parameters**:
- `tab`: Feed tab (choices: 'trending', 'new', 'for-you', default: 'trending')
- `tag`: Tag slug for filtering (optional, max 100 chars)
- `q`: Search query (optional, max 200 chars)
- `cursor`: Pagination cursor (optional)
- `page_size`: Results per page (optional, default: 20, min: 1, max: 100)

**Validation Rules**:
- `tab` must be one of the allowed values
- `tag` cannot exceed 100 characters
- `q` cannot exceed 200 characters
- `page_size` must be between 1 and 100

**Example Valid Request**:
```
GET /api/discover?tab=trending&page_size=50&tag=fantasy
```

**Example Error Response**:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid query parameters",
    "details": {
      "tab": ["Tab must be one of: trending, new, for-you"],
      "page_size": ["Ensure this value is less than or equal to 100"]
    }
  }
}
```

---

#### GET /api/discover/genre/:genre

**Serializer**: `GenreQuerySerializer`

**Query Parameters**:
- `cursor`: Pagination cursor (optional)
- `page_size`: Results per page (optional, default: 20, min: 1, max: 100)

**Validation Rules**:
- `page_size` must be between 1 and 100

---

#### GET /api/discover/similar/:story_id

**Serializer**: `SimilarStoriesQuerySerializer`

**Query Parameters**:
- `limit`: Number of similar stories (optional, default: 10, min: 1, max: 50)

**Validation Rules**:
- `limit` must be between 1 and 50

---

### User Profile Endpoints

#### PUT /api/v1/me

**Serializer**: `UserProfileWriteSerializer`

**Fields**:
- `handle`: User handle (optional, 3-30 chars, alphanumeric + underscore)
- `display_name`: Display name (optional, max 100 chars)
- `bio`: User bio (optional, max 500 chars)
- `avatar_key`: S3 object key (optional, max 255 chars)
- `banner_key`: S3 object key (optional, max 255 chars)
- `theme_color`: Hex color code (optional, max 7 chars, e.g., #6366f1)
- `twitter_url`: Twitter URL (optional, valid URL, max 255 chars)
- `instagram_url`: Instagram URL (optional, valid URL, max 255 chars)
- `website_url`: Website URL (optional, valid URL, max 255 chars)
- `pinned_story_1`: Story ID (optional, max 36 chars)
- `pinned_story_2`: Story ID (optional, max 36 chars)
- `pinned_story_3`: Story ID (optional, max 36 chars)

**Validation Rules**:
- `handle` must match pattern: `^[a-zA-Z0-9_]{3,30}$`
- `handle` must be unique across all users
- All string fields are trimmed of whitespace
- URL fields must be valid URLs
- `theme_color` must be a valid hex color code

**Example Valid Request**:
```json
{
  "handle": "john_doe",
  "display_name": "John Doe",
  "bio": "Writer and storyteller",
  "theme_color": "#6366f1"
}
```

**Example Error Response**:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": {
      "handle": ["Handle must contain only alphanumeric characters and underscores, and be between 3-30 characters long."]
    }
  }
}
```

---

### Story Endpoints

#### POST /api/v1/stories

**Serializer**: `StoryCreateSerializer`

**Required Fields**:
- `title`: Story title (max 200 chars, cannot be empty after trimming)
- `blurb`: Story description (max 500 chars, cannot be empty after trimming)

**Optional Fields**:
- `cover_key`: S3 object key for cover image
- `genre`: Story genre
- `tags`: Array of tag slugs
- `is_mature`: Boolean for mature content flag

**Validation Rules**:
- `title` and `blurb` are trimmed and cannot be empty
- Content is sanitized for XSS prevention
- Content is filtered for profanity, spam, and hate speech

---

#### PUT /api/v1/stories/:id

**Serializer**: `StoryUpdateSerializer`

**Fields**: Same as create, but all optional

**Validation Rules**: Same as create

---

### Whisper Endpoints

#### POST /api/v1/whispers

**Serializer**: `WhisperCreateSerializer`

**Required Fields**:
- `content`: Whisper content (max 280 chars)
- `scope`: Whisper scope (choices: 'GLOBAL', 'STORY', 'HIGHLIGHT')

**Conditional Fields**:
- `story_id`: Required if scope is 'STORY'
- `highlight_id`: Required if scope is 'HIGHLIGHT'

**Optional Fields**:
- `media_key`: S3 object key for media
- `mark_as_nsfw`: Boolean for NSFW marking

**Validation Rules**:
- `content` cannot exceed 280 characters
- `scope` must be one of the allowed values
- `story_id` must exist if provided
- `highlight_id` must exist if provided
- Content is sanitized for XSS prevention
- Content is filtered for profanity, spam, and hate speech

---

### Password Reset Endpoints

#### POST /api/forgot-password

**Serializer**: `ForgotPasswordRequestSerializer`

**Required Fields**:
- `email`: Email address (valid email format)

**Validation Rules**:
- Must be a valid email address format

---

#### POST /api/reset-password

**Serializer**: `ResetPasswordRequestSerializer`

**Required Fields**:
- `token`: Reset token (min 32 chars)
- `new_password`: New password (min 8 chars)

**Validation Rules**:
- `token` must be at least 32 characters
- `new_password` must be at least 8 characters
- Password is hashed before storage

---

## Common Validation Patterns

### String Fields
- All string fields are trimmed of leading/trailing whitespace
- Empty strings after trimming are rejected for required fields
- Maximum length is enforced

### URL Fields
- Must be valid URL format
- Protocol (http/https) is required

### Choice Fields
- Value must be one of the predefined choices
- Case-sensitive matching

### Integer Fields
- Must be valid integer
- Min/max value constraints are enforced

### UUID Fields
- Must be valid UUID format
- Used for resource IDs

---

## Content Filtering

All user-generated content goes through multiple filters:

1. **XSS Prevention**: Content is sanitized using `ContentSanitizer`
2. **Profanity Filter**: Detects and blocks profane language
3. **Spam Detection**: Identifies spam patterns
4. **Hate Speech Detection**: Blocks hate speech and creates high-priority reports

Content that fails filtering returns:
```json
{
  "error": {
    "code": "CONTENT_BLOCKED",
    "message": "Content blocked due to policy violation",
    "flags": ["profanity", "spam"]
  }
}
```

---

## Custom Exception Handler

The custom exception handler (`apps.core.exceptions.custom_exception_handler`) provides:

- Consistent error response format
- Proper HTTP status codes
- Detailed validation error messages
- Error logging for debugging

---

## Testing Validation

All serializers have comprehensive test coverage in `tests/backend/apps/`:

- Valid input tests
- Invalid input tests
- Edge case tests
- Boundary value tests

Run validation tests:
```bash
python -m pytest tests/backend/apps/*_serializer_tests.py -v
```

---

## Adding New Validation Rules

When adding new endpoints:

1. Create a serializer in `apps/<app>/serializers.py`
2. Define all fields with appropriate validators
3. Add custom `validate_<field>()` methods if needed
4. Use the serializer in your view
5. Add tests in `tests/backend/apps/<app>_serializer_tests.py`
6. Document the validation rules in this file

Example:
```python
class MySerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100, required=True)
    
    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Name cannot be empty")
        return value.strip()
```

---

## Security Considerations

- All input is validated before processing
- SQL injection is prevented by using ORM
- XSS is prevented by content sanitization
- CSRF protection is enabled
- Rate limiting is enforced
- Authentication is required for protected endpoints

---

## References

- Django REST Framework Serializers: https://www.django-rest-framework.org/api-guide/serializers/
- Django Validators: https://docs.djangoproject.com/en/stable/ref/validators/
- Custom Exception Handler: `apps/backend/apps/core/exceptions.py`
