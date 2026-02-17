# MueJam Library API Documentation

## Overview

The MueJam Library API is documented using OpenAPI 3.0 specification with interactive Swagger UI.

## Accessing the Documentation

### Interactive Swagger UI

Once the Django development server is running, you can access the interactive API documentation at:

```
http://localhost:8000/v1/docs/
```

The Swagger UI provides:
- Complete list of all API endpoints
- Request/response schemas
- Example requests and responses
- Interactive "Try it out" functionality to test endpoints
- Authentication configuration

### OpenAPI Schema

The raw OpenAPI schema (YAML format) is available at:

```
http://localhost:8000/v1/schema/
```

You can also generate a static schema file using:

```bash
python manage.py spectacular --color --file schema.yml
```

## API Structure

### Base URL

All API endpoints are prefixed with `/v1`:

```
http://localhost:8000/v1/
```

### Authentication

Most endpoints require authentication using Clerk-issued JWT tokens.

Include the token in the Authorization header:

```
Authorization: Bearer <your_clerk_token>
```

### Response Format

All responses follow a consistent JSON structure:

**Success Response:**
```json
{
  "data": { ... }
}
```

**Error Response:**
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": { ... }
  }
}
```

### Pagination

List endpoints use cursor-based pagination:

**Request:**
```
GET /v1/stories?cursor=<cursor_token>&page_size=20
```

**Response:**
```json
{
  "data": [ ... ],
  "next_cursor": "eyJpZCI6IjEyMyJ9"
}
```

When `next_cursor` is `null`, there are no more results.

## API Endpoints by Category

### Authentication
- `GET /v1/me` - Get current user profile
- `PUT /v1/me` - Update current user profile
- `GET /v1/users/{handle}` - Get public user profile

### Stories
- `GET /v1/stories` - List stories
- `POST /v1/stories` - Create story draft
- `GET /v1/stories/{slug}` - Get story by slug
- `PUT /v1/stories/{id}` - Update story
- `DELETE /v1/stories/{id}` - Soft delete story
- `POST /v1/stories/{id}/publish` - Publish story

### Chapters
- `GET /v1/stories/{id}/chapters` - List chapters
- `POST /v1/stories/{id}/chapters` - Create chapter draft
- `GET /v1/chapters/{id}` - Get chapter content
- `PUT /v1/chapters/{id}` - Update chapter
- `DELETE /v1/chapters/{id}` - Soft delete chapter
- `POST /v1/chapters/{id}/publish` - Publish chapter

### Library
- `GET /v1/library/shelves` - List user's shelves
- `POST /v1/library/shelves` - Create shelf
- `PUT /v1/library/shelves/{id}` - Update shelf
- `DELETE /v1/library/shelves/{id}` - Delete shelf
- `POST /v1/library/shelves/{id}/items` - Add story to shelf
- `DELETE /v1/library/shelves/{id}/items/{story_id}` - Remove story

### Reading
- `POST /v1/chapters/{id}/progress` - Update reading progress
- `GET /v1/chapters/{id}/progress` - Get reading progress
- `POST /v1/chapters/{id}/bookmarks` - Create bookmark
- `GET /v1/chapters/{id}/bookmarks` - List bookmarks
- `DELETE /v1/bookmarks/{id}` - Delete bookmark
- `POST /v1/chapters/{id}/highlights` - Create highlight
- `GET /v1/chapters/{id}/highlights` - List highlights
- `DELETE /v1/highlights/{id}` - Delete highlight

### Whispers
- `GET /v1/whispers` - List whispers
- `POST /v1/whispers` - Create whisper
- `DELETE /v1/whispers/{id}` - Soft delete whisper
- `POST /v1/whispers/{id}/replies` - Reply to whisper
- `GET /v1/whispers/{id}/replies` - List replies
- `POST /v1/whispers/{id}/like` - Like whisper
- `DELETE /v1/whispers/{id}/like` - Unlike whisper

### Social
- `POST /v1/users/{id}/follow` - Follow user
- `DELETE /v1/users/{id}/follow` - Unfollow user
- `POST /v1/users/{id}/block` - Block user
- `DELETE /v1/users/{id}/block` - Unblock user
- `GET /v1/users/{id}/followers` - List followers
- `GET /v1/users/{id}/following` - List following

### Discovery
- `GET /v1/discover` - Get discovery feed (trending/new/for-you)

### Search
- `GET /v1/search` - Full-text search
- `GET /v1/search/suggest` - Autocomplete suggestions

### Notifications
- `GET /v1/notifications` - List notifications
- `POST /v1/notifications/{id}/read` - Mark as read
- `POST /v1/notifications/read-all` - Mark all as read

### Uploads
- `POST /v1/uploads/presign` - Get presigned S3 URL

### Moderation
- `POST /v1/reports` - Submit report

### Health
- `GET /v1/health` - System health check (no auth required)

## Rate Limits

The following rate limits are enforced:

- **Whispers**: 10 per minute
- **Replies**: 20 per minute
- **Publish operations**: 5 per hour

When rate limit is exceeded, the API returns HTTP 429 with a `Retry-After` header.

## Development

### Updating Documentation

The API documentation is automatically generated from:

1. **DRF Spectacular decorators** in view functions (`@extend_schema`)
2. **Serializer definitions** in serializers.py files
3. **Settings** in `config/settings.py` (`SPECTACULAR_SETTINGS`)

To add or update documentation:

1. Add `@extend_schema` decorator to view functions
2. Include descriptions, parameters, examples
3. Regenerate schema: `python manage.py spectacular --file schema.yml`

### Example Documentation Decorator

```python
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

@extend_schema(
    tags=['Stories'],
    summary='Create a new story',
    description='Create a new story draft. Story will be unpublished by default.',
    request=StoryCreateSerializer,
    responses={
        201: StoryDetailSerializer,
        400: OpenApiTypes.OBJECT,
        401: OpenApiTypes.OBJECT,
    },
    examples=[
        OpenApiExample(
            'Create Story Example',
            value={
                'title': 'My Story',
                'blurb': 'An amazing tale',
                'cover_key': 'covers/uuid.jpg'
            },
            request_only=True,
        ),
    ]
)
@api_view(['POST'])
def create_story(request):
    # Implementation
    pass
```

## Support

For API support or questions, contact: support@muejam.com
