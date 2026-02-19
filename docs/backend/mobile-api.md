# Mobile API Documentation

## Overview

This document provides mobile-specific API documentation for iOS and Android clients integrating with the MueJam Library backend. The mobile API builds on the standard REST API with additional features optimized for mobile platforms including push notifications, deep linking, offline support, and bandwidth optimization.

## Mobile Client Identification

### X-Client-Type Header

All mobile clients MUST include the `X-Client-Type` header in every API request to identify the client platform.

**Header Format:**
```
X-Client-Type: mobile-ios
```

**Allowed Values:**
- `mobile-ios` - iOS native app
- `mobile-android` - Android native app
- `web` - Web browser (default if header is omitted)

**Example Request:**
```http
GET /v1/stories HTTP/1.1
Host: api.muejam.com
Authorization: Bearer <jwt_token>
X-Client-Type: mobile-ios
```

**Benefits:**
- Enables mobile-optimized response formats
- Applies mobile-specific rate limits (higher than web)
- Includes deep links in responses
- Enables analytics tracking per platform
- Triggers mobile-specific features

**Error Response for Invalid Client Type:**
```json
{
  "error": {
    "code": "INVALID_CLIENT_TYPE",
    "message": "Invalid client type. Must be one of: web, mobile-ios, mobile-android",
    "details": {
      "provided": "mobile-web",
      "allowed": ["web", "mobile-ios", "mobile-android"]
    }
  }
}
```

## Deep Links

### Overview

Deep links allow mobile apps to navigate directly to specific content when users tap notifications, share links, or open URLs from external sources. The API automatically includes deep links in responses when the `X-Client-Type` header indicates a mobile client.

### URL Scheme

**iOS and Android:**
```
muejam://
```

### Deep Link Patterns

#### Story Deep Link
```
muejam://story/{story_id}
```

**Example:**
```
muejam://story/clx1a2b3c4d5e6f7g8h9i0j1
```

**API Response (when X-Client-Type is mobile-ios or mobile-android):**
```json
{
  "id": "clx1a2b3c4d5e6f7g8h9i0j1",
  "title": "The Midnight Garden",
  "slug": "the-midnight-garden",
  "deep_link": "muejam://story/clx1a2b3c4d5e6f7g8h9i0j1"
}
```

#### Chapter Deep Link
```
muejam://chapter/{chapter_id}
```

**Example:**
```
muejam://chapter/clx2b3c4d5e6f7g8h9i0j1k2
```

#### Whisper Deep Link
```
muejam://whisper/{whisper_id}
```

**Example:**
```
muejam://whisper/clx3c4d5e6f7g8h9i0j1k2l3
```

#### User Profile Deep Link
```
muejam://profile/{user_id}
```

**Example:**
```
muejam://profile/clx4d5e6f7g8h9i0j1k2l3m4
```

### Universal Links / App Links

For better user experience, implement universal links (iOS) and app links (Android) that work in browsers and automatically open the app if installed.

**Web URL Format:**
```
https://muejam.com/story/{slug}
https://muejam.com/chapter/{slug}
https://muejam.com/whisper/{id}
https://muejam.com/profile/{handle}
```

**Implementation:**
- iOS: Configure associated domains in Xcode
- Android: Configure intent filters in AndroidManifest.xml
- Both platforms should handle both `muejam://` and `https://muejam.com/` URLs

## Push Notifications

### Device Registration

Mobile clients must register device tokens to receive push notifications.

#### Register Device Token

**Endpoint:** `POST /v1/devices/register`

**Request:**
```json
{
  "token": "device_token_from_fcm_or_apns",
  "platform": "ios",
  "app_version": "1.2.0"
}
```

**Parameters:**
- `token` (required): Device token from FCM (Android) or APNs (iOS)
- `platform` (required): Either "ios" or "android"
- `app_version` (optional): App version string for analytics

**Response:**
```json
{
  "id": "clx5e6f7g8h9i0j1k2l3m4n5",
  "user_id": "clx6f7g8h9i0j1k2l3m4n5o6",
  "token": "device_token_from_fcm_or_apns",
  "platform": "ios",
  "app_version": "1.2.0",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### Unregister Device Token

**Endpoint:** `DELETE /v1/devices/unregister`

**Request:**
```json
{
  "token": "device_token_from_fcm_or_apns"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Device token unregistered successfully"
}
```

#### Update Notification Preferences

**Endpoint:** `PUT /v1/devices/preferences`

**Request:**
```json
{
  "token": "device_token_from_fcm_or_apns",
  "preferences": {
    "whisper_replies": true,
    "story_updates": true,
    "new_followers": false,
    "likes": false
  }
}
```

**Response:**
```json
{
  "success": true,
  "preferences": {
    "whisper_replies": true,
    "story_updates": true,
    "new_followers": false,
    "likes": false
  }
}
```

### Push Notification Payload Formats

#### iOS (APNs) Payload

```json
{
  "aps": {
    "alert": {
      "title": "New Reply",
      "body": "Alice replied to your whisper"
    },
    "badge": 3,
    "sound": "default",
    "category": "WHISPER_REPLY"
  },
  "data": {
    "type": "whisper_reply",
    "whisper_id": "clx7g8h9i0j1k2l3m4n5o6p7",
    "reply_id": "clx8h9i0j1k2l3m4n5o6p7q8",
    "deep_link": "muejam://whisper/clx7g8h9i0j1k2l3m4n5o6p7"
  }
}
```

#### Android (FCM) Payload

```json
{
  "notification": {
    "title": "New Reply",
    "body": "Alice replied to your whisper",
    "icon": "ic_notification",
    "color": "#6366F1",
    "sound": "default",
    "tag": "whisper_reply"
  },
  "data": {
    "type": "whisper_reply",
    "whisper_id": "clx7g8h9i0j1k2l3m4n5o6p7",
    "reply_id": "clx8h9i0j1k2l3m4n5o6p7q8",
    "deep_link": "muejam://whisper/clx7g8h9i0j1k2l3m4n5o6p7"
  }
}
```

### Notification Types

#### Whisper Reply
```json
{
  "type": "whisper_reply",
  "title": "New Reply",
  "body": "{username} replied to your whisper",
  "data": {
    "whisper_id": "clx...",
    "reply_id": "clx...",
    "deep_link": "muejam://whisper/{whisper_id}"
  }
}
```

#### Story Update
```json
{
  "type": "story_update",
  "title": "New Chapter",
  "body": "{author} published a new chapter in {story_title}",
  "data": {
    "story_id": "clx...",
    "chapter_id": "clx...",
    "deep_link": "muejam://chapter/{chapter_id}"
  }
}
```

#### New Follower
```json
{
  "type": "new_follower",
  "title": "New Follower",
  "body": "{username} started following you",
  "data": {
    "user_id": "clx...",
    "deep_link": "muejam://profile/{user_id}"
  }
}
```

#### Whisper Like
```json
{
  "type": "whisper_like",
  "title": "New Like",
  "body": "{username} liked your whisper",
  "data": {
    "whisper_id": "clx...",
    "user_id": "clx...",
    "deep_link": "muejam://whisper/{whisper_id}"
  }
}
```

## Mobile-Specific Request Examples

### List Stories with Field Filtering

Mobile clients can request only specific fields to reduce bandwidth usage.

**Request:**
```http
GET /v1/stories?fields=id,title,slug,cover_url HTTP/1.1
Host: api.muejam.com
Authorization: Bearer <jwt_token>
X-Client-Type: mobile-ios
```

**Response:**
```json
{
  "data": [
    {
      "id": "clx1a2b3c4d5e6f7g8h9i0j1",
      "title": "The Midnight Garden",
      "slug": "the-midnight-garden",
      "cover_url": "https://cdn.muejam.com/covers/abc123.jpg",
      "deep_link": "muejam://story/clx1a2b3c4d5e6f7g8h9i0j1"
    }
  ],
  "next_cursor": "eyJpZCI6IjEyMyJ9"
}
```

### Lightweight List Mode

Request lightweight responses with minimal data for list views.

**Request:**
```http
GET /v1/stories?lightweight=true HTTP/1.1
Host: api.muejam.com
Authorization: Bearer <jwt_token>
X-Client-Type: mobile-android
```

**Response:**
```json
{
  "data": [
    {
      "id": "clx1a2b3c4d5e6f7g8h9i0j1",
      "title": "The Midnight Garden",
      "slug": "the-midnight-garden",
      "cover_url": "https://cdn.muejam.com/covers/abc123.jpg",
      "author": {
        "id": "clx2b3c4d5e6f7g8h9i0j1k2",
        "handle": "alice"
      },
      "deep_link": "muejam://story/clx1a2b3c4d5e6f7g8h9i0j1"
    }
  ],
  "next_cursor": "eyJpZCI6IjEyMyJ9"
}
```

### Conditional Requests for Caching

Use conditional requests to leverage cached data and reduce bandwidth.

**Request with If-None-Match:**
```http
GET /v1/stories/the-midnight-garden HTTP/1.1
Host: api.muejam.com
Authorization: Bearer <jwt_token>
X-Client-Type: mobile-ios
If-None-Match: "33a64df551425fcc55e4d42a148795d9f25f89d4"
```

**Response (if content unchanged):**
```http
HTTP/1.1 304 Not Modified
ETag: "33a64df551425fcc55e4d42a148795d9f25f89d4"
Last-Modified: Mon, 15 Jan 2024 10:30:00 GMT
Cache-Control: max-age=3600
```

**Request with If-Modified-Since:**
```http
GET /v1/stories/the-midnight-garden HTTP/1.1
Host: api.muejam.com
Authorization: Bearer <jwt_token>
X-Client-Type: mobile-android
If-Modified-Since: Mon, 15 Jan 2024 10:30:00 GMT
```

### Incremental Sync

Fetch only data modified since last sync.

**Request:**
```http
GET /v1/sync/stories?since=2024-01-15T10:30:00Z HTTP/1.1
Host: api.muejam.com
Authorization: Bearer <jwt_token>
X-Client-Type: mobile-ios
```

**Response:**
```json
{
  "data": [
    {
      "id": "clx1a2b3c4d5e6f7g8h9i0j1",
      "title": "The Midnight Garden - Updated",
      "updated_at": "2024-01-15T11:45:00Z",
      "deep_link": "muejam://story/clx1a2b3c4d5e6f7g8h9i0j1"
    }
  ],
  "sync_timestamp": "2024-01-15T12:00:00Z"
}
```

### Batch Operations

Submit multiple operations in a single request.

**Request:**
```http
POST /v1/sync/batch HTTP/1.1
Host: api.muejam.com
Authorization: Bearer <jwt_token>
X-Client-Type: mobile-android
Content-Type: application/json

{
  "operations": [
    {
      "type": "create",
      "resource": "whisper",
      "data": {
        "content": "Great story!",
        "story_id": "clx1a2b3c4d5e6f7g8h9i0j1"
      }
    },
    {
      "type": "update",
      "resource": "progress",
      "data": {
        "chapter_id": "clx2b3c4d5e6f7g8h9i0j1k2",
        "progress_percent": 75
      }
    }
  ]
}
```

**Response:**
```json
{
  "results": [
    {
      "status": "success",
      "resource_id": "clx9i0j1k2l3m4n5o6p7q8r9"
    },
    {
      "status": "success",
      "resource_id": "clx0j1k2l3m4n5o6p7q8r9s0"
    }
  ]
}
```

## Mobile Media Upload

### Single File Upload

**Endpoint:** `POST /v1/uploads/media`

**Supported Formats:**
- Images: HEIC, HEIF, JPG, JPEG, PNG
- Videos: MP4, MOV

**Maximum File Size:** 50 MB

**Request:**
```http
POST /v1/uploads/media HTTP/1.1
Host: api.muejam.com
Authorization: Bearer <jwt_token>
X-Client-Type: mobile-ios
Content-Type: multipart/form-data

--boundary
Content-Disposition: form-data; name="file"; filename="photo.heic"
Content-Type: image/heic

<binary data>
--boundary--
```

**Response:**
```json
{
  "id": "clx1a2b3c4d5e6f7g8h9i0j1",
  "url": "https://cdn.muejam.com/uploads/abc123.jpg",
  "thumbnail_url": "https://cdn.muejam.com/uploads/abc123_thumb.jpg",
  "size": 2048576,
  "format": "jpeg",
  "width": 1920,
  "height": 1080
}
```

**Notes:**
- HEIC/HEIF images are automatically converted to JPEG
- EXIF metadata (including location) is automatically stripped
- Images are optimized for web delivery

### Chunked Upload (for large files)

#### 1. Initiate Upload

**Endpoint:** `POST /v1/uploads/chunked/init`

**Request:**
```json
{
  "filename": "video.mp4",
  "total_size": 45000000,
  "content_type": "video/mp4"
}
```

**Response:**
```json
{
  "session_id": "clx2b3c4d5e6f7g8h9i0j1k2",
  "chunk_size": 5242880,
  "expires_at": "2024-01-16T10:30:00Z"
}
```

#### 2. Upload Chunks

**Endpoint:** `POST /v1/uploads/chunked/chunk`

**Request:**
```json
{
  "session_id": "clx2b3c4d5e6f7g8h9i0j1k2",
  "chunk_number": 1,
  "chunk_data": "<base64_encoded_chunk>"
}
```

**Response:**
```json
{
  "chunk_number": 1,
  "status": "received",
  "progress": 11.6
}
```

#### 3. Complete Upload

**Endpoint:** `POST /v1/uploads/chunked/complete`

**Request:**
```json
{
  "session_id": "clx2b3c4d5e6f7g8h9i0j1k2"
}
```

**Response:**
```json
{
  "id": "clx3c4d5e6f7g8h9i0j1k2l3",
  "url": "https://cdn.muejam.com/uploads/video123.mp4",
  "size": 45000000,
  "format": "mp4"
}
```

## Mobile Error Codes

### Client Errors (4xx)

#### INVALID_CLIENT_TYPE (422)
```json
{
  "error": {
    "code": "INVALID_CLIENT_TYPE",
    "message": "Invalid client type. Must be one of: web, mobile-ios, mobile-android",
    "details": {
      "provided": "mobile-web",
      "allowed": ["web", "mobile-ios", "mobile-android"]
    }
  }
}
```

#### TOKEN_EXPIRED (401)
```json
{
  "error": {
    "code": "TOKEN_EXPIRED",
    "message": "Your authentication token has expired. Please refresh your token.",
    "details": {
      "expired_at": "2024-01-15T10:30:00Z",
      "refresh_endpoint": "/v1/auth/refresh"
    },
    "retry_guidance": "Refresh your authentication token and retry the request"
  }
}
```

#### FILE_TOO_LARGE (413)
```json
{
  "error": {
    "code": "FILE_TOO_LARGE",
    "message": "File size exceeds the maximum allowed size for mobile uploads",
    "details": {
      "file_size": 52428800,
      "max_size": 52428800,
      "max_size_mb": 50
    },
    "retry_guidance": "Reduce file size or use chunked upload for files larger than 50MB"
  }
}
```

#### RATE_LIMIT_EXCEEDED (429)
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests. Please wait before trying again.",
    "details": {
      "limit": 150,
      "window": "1 minute",
      "retry_after": 45
    },
    "retry_guidance": "Wait 45 seconds before retrying"
  }
}
```

#### SYNC_CONFLICT (409)
```json
{
  "error": {
    "code": "SYNC_CONFLICT",
    "message": "The data you're trying to update has been modified by another client",
    "details": {
      "resource_type": "whisper",
      "resource_id": "clx1a2b3c4d5e6f7g8h9i0j1",
      "client_version": "2024-01-15T10:30:00Z",
      "server_version": "2024-01-15T11:45:00Z",
      "conflicting_fields": ["content"]
    },
    "retry_guidance": "Fetch the latest version and reapply your changes"
  }
}
```

#### UNSUPPORTED_FORMAT (422)
```json
{
  "error": {
    "code": "UNSUPPORTED_FORMAT",
    "message": "The uploaded file format is not supported",
    "details": {
      "provided_format": "gif",
      "supported_formats": ["heic", "heif", "jpg", "jpeg", "png", "mp4", "mov"]
    },
    "retry_guidance": "Convert the file to a supported format and retry"
  }
}
```

### Server Errors (5xx)

#### PUSH_SERVICE_ERROR (502)
```json
{
  "error": {
    "code": "PUSH_SERVICE_ERROR",
    "message": "Failed to send push notification due to external service error",
    "details": {
      "service": "FCM",
      "error_type": "service_unavailable"
    },
    "retry_guidance": "The notification will be retried automatically. No action needed."
  }
}
```

#### STORAGE_SERVICE_ERROR (502)
```json
{
  "error": {
    "code": "STORAGE_SERVICE_ERROR",
    "message": "Failed to upload file due to storage service error",
    "details": {
      "service": "S3",
      "error_type": "timeout"
    },
    "retry_guidance": "Wait a few moments and retry the upload"
  }
}
```

#### EXTERNAL_SERVICE_TIMEOUT (504)
```json
{
  "error": {
    "code": "EXTERNAL_SERVICE_TIMEOUT",
    "message": "Request timed out while communicating with external service",
    "details": {
      "service": "image_processing",
      "timeout_seconds": 30
    },
    "retry_guidance": "Retry the request. If the problem persists, try a smaller file."
  }
}
```

## Rate Limits

Mobile clients have higher rate limits than web clients to accommodate app usage patterns.

### Rate Limit Tiers

| Client Type | Requests per Minute | Authenticated Multiplier |
|-------------|---------------------|-------------------------|
| mobile-ios | 150 | 2x (300/min) |
| mobile-android | 150 | 2x (300/min) |
| web | 100 | 2x (200/min) |

### Rate Limit Headers

All responses include rate limit information:

```http
X-RateLimit-Limit: 150
X-RateLimit-Remaining: 142
X-RateLimit-Reset: 1705318200
```

### Rate Limit Exceeded Response

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 45
X-RateLimit-Limit: 150
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1705318200

{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests. Please wait before trying again.",
    "details": {
      "limit": 150,
      "window": "1 minute",
      "retry_after": 45
    }
  }
}
```

## Response Headers

### Cache Control

Mobile responses include cache control headers for offline support:

```http
Cache-Control: max-age=3600, must-revalidate
ETag: "33a64df551425fcc55e4d42a148795d9f25f89d4"
Last-Modified: Mon, 15 Jan 2024 10:30:00 GMT
```

### Response Metadata

```http
X-Response-Size: 15234
X-Client-Type: mobile-ios
X-API-Version: v1
```

## Mobile Configuration

### Get Mobile Configuration

**Endpoint:** `GET /v1/config/mobile`

**Query Parameters:**
- `platform` (required): "ios" or "android"
- `app_version` (optional): Current app version

**Request:**
```http
GET /v1/config/mobile?platform=ios&app_version=1.2.0 HTTP/1.1
Host: api.muejam.com
Authorization: Bearer <jwt_token>
X-Client-Type: mobile-ios
```

**Response:**
```json
{
  "platform": "ios",
  "min_supported_version": "1.0.0",
  "latest_version": "1.2.0",
  "force_update": false,
  "features": {
    "push_notifications": true,
    "offline_mode": true,
    "video_upload": true,
    "dark_mode": true
  },
  "settings": {
    "max_upload_size_mb": 50,
    "chunk_size_mb": 5,
    "cache_ttl_hours": 24,
    "sync_interval_minutes": 15
  }
}
```

## Testing Support

### Test Push Notification

**Endpoint:** `POST /v1/test/push-notification`

**Request:**
```json
{
  "token": "device_token_from_fcm_or_apns",
  "platform": "ios"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Test notification sent successfully",
  "notification_id": "clx1a2b3c4d5e6f7g8h9i0j1"
}
```

### Verify Deep Link

**Endpoint:** `GET /v1/test/deep-link`

**Query Parameters:**
- `type`: "story", "chapter", "whisper", or "profile"
- `id`: Resource ID

**Request:**
```http
GET /v1/test/deep-link?type=story&id=clx1a2b3c4d5e6f7g8h9i0j1 HTTP/1.1
Host: api.muejam.com
Authorization: Bearer <jwt_token>
X-Client-Type: mobile-ios
```

**Response:**
```json
{
  "deep_link": "muejam://story/clx1a2b3c4d5e6f7g8h9i0j1",
  "web_url": "https://muejam.com/story/the-midnight-garden",
  "valid": true
}
```

## Best Practices

### Authentication
- Store JWT tokens securely using Keychain (iOS) or Keystore (Android)
- Implement token refresh before expiration
- Handle 401 errors by refreshing token and retrying

### Offline Support
- Cache API responses using ETag and Last-Modified headers
- Use conditional requests (If-None-Match, If-Modified-Since)
- Implement sync queue for offline operations
- Use incremental sync endpoints when coming back online

### Push Notifications
- Register device token on app launch and after login
- Unregister token on logout
- Handle notification permissions gracefully
- Implement deep link handling for notification taps

### Media Upload
- Use chunked upload for files larger than 10MB
- Show upload progress to users
- Implement retry logic for failed uploads
- Compress images before upload when appropriate

### Error Handling
- Always check error codes, not just HTTP status
- Display user-friendly error messages from API
- Implement exponential backoff for retries
- Log errors for debugging but don't expose sensitive data

### Performance
- Use field filtering to reduce response size
- Implement pagination for list views
- Use lightweight mode for list endpoints
- Compress requests when sending large payloads

### Rate Limiting
- Respect Retry-After headers
- Implement exponential backoff for rate limit errors
- Cache responses to reduce API calls
- Batch operations when possible

## Support

For mobile API support or questions:
- Email: mobile-support@muejam.com
- Documentation: https://docs.muejam.com/mobile-api
- Status: https://status.muejam.com
