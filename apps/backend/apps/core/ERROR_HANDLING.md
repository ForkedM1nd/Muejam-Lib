# API Error Handling and Validation

This document describes the error handling and validation implementation for the MueJam Library API.

## Overview

The API implements consistent error handling across all endpoints with:
- Standardized error response format
- Appropriate HTTP status codes
- Detailed validation error messages
- Authentication and authorization error handling

## Error Response Format

All API errors follow this consistent JSON structure:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field": "Specific field error details"
    }
  }
}
```

### Fields

- **code**: Uppercase error code identifying the error type (e.g., `VALIDATION_ERROR`, `AUTHENTICATION_FAILED`)
- **message**: Human-readable description of the error
- **details**: Additional context about the error (e.g., which fields failed validation)

## HTTP Status Codes

The API uses standard HTTP status codes:

| Status Code | Meaning | When Used |
|------------|---------|-----------|
| 400 | Bad Request | Invalid input, validation failures |
| 401 | Unauthorized | Missing or invalid authentication token |
| 403 | Forbidden | Authenticated but not authorized (e.g., accessing blocked content) |
| 404 | Not Found | Resource does not exist or is soft-deleted |
| 409 | Conflict | Duplicate resource (e.g., handle already taken) |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Unexpected server error |
| 503 | Service Unavailable | Dependency unavailable (database, cache, etc.) |

## Custom Exception Classes

The following custom exceptions are available in `apps.core.exceptions`:

### Authentication Exceptions

- **AuthenticationRequired**: Raised when authentication is required but not provided (HTTP 401)
- **InvalidToken**: Raised when authentication token is invalid or expired (HTTP 401)

### Authorization Exceptions

- **InsufficientPermissions**: Raised when user lacks required permissions (HTTP 403)
- **UserBlocked**: Raised when accessing blocked user's content (HTTP 403)

### Resource Exceptions

- **ContentDeleted**: Raised when accessing soft-deleted content (HTTP 404)
- **DuplicateResource**: Raised when attempting to create duplicate resource (HTTP 409)

### Validation Exceptions

- **InvalidCursor**: Raised when pagination cursor is invalid (HTTP 400)
- **InvalidOffset**: Raised when highlight offsets are invalid (HTTP 400)

### Rate Limiting Exceptions

- **RateLimitExceeded**: Raised when rate limit is exceeded (HTTP 429)

## Request Validation

### Serializer Validation

All endpoints use Django REST Framework serializers for request validation. Serializers define:

- Field types and constraints (max_length, min_value, etc.)
- Required vs optional fields
- Custom validation logic

Example:

```python
from rest_framework import serializers

class StoryCreateSerializer(serializers.Serializer):
    title = serializers.CharField(
        required=True,
        max_length=200,
        help_text="Story title (max 200 characters)"
    )
    blurb = serializers.CharField(
        required=True,
        max_length=1000,
        help_text="Story description/blurb (max 1000 characters)"
    )
    
    def validate_title(self, value):
        """Custom validation for title field."""
        if not value.strip():
            raise serializers.ValidationError("Title cannot be empty.")
        return value.strip()
```

### Using Validation in Views

Use the `validate_serializer` helper function for consistent validation:

```python
from apps.core.exceptions import validate_serializer

def create_story(request):
    serializer = StoryCreateSerializer(data=request.data)
    validate_serializer(serializer, raise_exception=True)
    
    # Serializer is valid, access cleaned data
    validated_data = serializer.validated_data
    # ... create story
```

When `raise_exception=True`, validation errors are automatically caught by the custom exception handler and formatted consistently.

## Authentication and Authorization

### Authentication Middleware

The `ClerkAuthMiddleware` handles JWT token verification:

1. Extracts token from `Authorization: Bearer <token>` header
2. Verifies token with Clerk
3. Sets `request.clerk_user_id` and `request.user_profile`
4. Sets `request.auth_error` if authentication fails

### Requiring Authentication

Use the `@require_authentication` decorator to protect endpoints:

```python
from apps.core.decorators import require_authentication

@require_authentication
def my_protected_view(request):
    # request.clerk_user_id and request.user_profile are guaranteed to exist
    user_id = request.clerk_user_id
    profile = request.user_profile
    # ... handle request
```

This decorator:
- Checks if user is authenticated
- Raises `AuthenticationRequired` (HTTP 401) if not authenticated
- Raises `InvalidToken` (HTTP 401) if token is invalid/expired

### Requiring Ownership

Use the `@require_ownership` decorator to ensure user owns a resource:

```python
from apps.core.decorators import require_authentication, require_ownership

def get_story_owner(request, story_id):
    # Fetch story and return author_id
    story = get_story_by_id(story_id)
    return story.author_id

@require_authentication
@require_ownership(get_story_owner)
def update_story(request, story_id):
    # User is guaranteed to own the story
    # ... update story
```

This decorator:
- Checks if authenticated user owns the resource
- Raises `InsufficientPermissions` (HTTP 403) if not the owner

### Checking Block Status

Use the `@check_not_blocked` decorator to prevent access to blocked users' content:

```python
from apps.core.decorators import require_authentication, check_not_blocked

def get_author_id(request, story_id):
    # Fetch story and return author_id
    story = get_story_by_id(story_id)
    return story.author_id

@require_authentication
@check_not_blocked(get_author_id)
async def view_story(request, story_id):
    # User has not blocked the story author
    # ... display story
```

This decorator:
- Checks if user has blocked the target user
- Raises `UserBlocked` (HTTP 403) if blocked

## Error Examples

### Validation Error

Request:
```http
POST /v1/stories
Content-Type: application/json

{
  "title": "",
  "blurb": "A great story"
}
```

Response (HTTP 400):
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": {
      "errors": [
        {
          "title": ["Title cannot be empty."]
        }
      ]
    }
  }
}
```

### Authentication Error

Request:
```http
GET /v1/me
```

Response (HTTP 401):
```json
{
  "error": {
    "code": "AUTHENTICATION_REQUIRED",
    "message": "Authentication credentials were not provided.",
    "details": {}
  }
}
```

### Authorization Error

Request:
```http
PUT /v1/stories/abc123
Authorization: Bearer <valid_token>
Content-Type: application/json

{
  "title": "Updated Title"
}
```

Response (HTTP 403):
```json
{
  "error": {
    "code": "INSUFFICIENT_PERMISSIONS",
    "message": "You do not have permission to modify this resource.",
    "details": {}
  }
}
```

### Rate Limit Error

Request:
```http
POST /v1/whispers
Authorization: Bearer <valid_token>
Content-Type: application/json

{
  "content": "My 11th whisper in a minute",
  "scope": "GLOBAL"
}
```

Response (HTTP 429):
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Please try again later.",
    "details": {}
  }
}
```

## Testing

Error handling is tested in `apps/core/tests_error_handling.py`:

- Custom exception handler formatting
- HTTP status code mapping
- Custom exception classes
- Validation helper function
- Error response structure

Run tests:
```bash
python -m pytest backend/apps/core/tests_error_handling.py -v
```

## Requirements Mapping

This implementation satisfies the following requirements:

- **17.2**: Return JSON with error code, message, and details
- **17.3**: Map Django/DRF exceptions to appropriate HTTP status codes
- **17.5**: Add DRF serializer validation for all endpoints
- **17.6**: Return HTTP 400 with detailed validation errors
- **17.7**: Return HTTP 401 for missing/invalid tokens
- **17.8**: Return HTTP 403 for authorization failures
