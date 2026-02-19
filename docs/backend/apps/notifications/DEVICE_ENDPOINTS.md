# Device Token Management Endpoints

This document describes the device token management endpoints for mobile push notifications.

## Endpoints

### 1. Register Device Token

**Endpoint:** `POST /v1/devices/register`

**Description:** Register a device token for push notifications.

**Authentication:** Required (JWT token)

**Request Body:**
```json
{
  "token": "device_token_from_fcm_or_apns",
  "platform": "ios",  // or "android"
  "app_version": "1.0.0"  // optional
}
```

**Response (200 OK):**
```json
{
  "data": {
    "id": "device_token_id",
    "user_id": "user_id",
    "platform": "ios",
    "app_version": "1.0.0",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z",
    "last_used_at": "2024-01-01T00:00:00Z"
  },
  "message": "Device registered successfully"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required

---

### 2. Unregister Device Token

**Endpoint:** `DELETE /v1/devices/unregister`

**Description:** Unregister a device token (marks it as inactive).

**Authentication:** Required (JWT token)

**Request Body:**
```json
{
  "token": "device_token_to_unregister"
}
```

**Response (200 OK):**
```json
{
  "message": "Device unregistered successfully"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `404 Not Found`: Device token not found

---

### 3. Update Device Preferences

**Endpoint:** `PUT /v1/devices/preferences`

**Description:** Update notification preferences for a specific device.

**Authentication:** Required (JWT token)

**Request Body:**
```json
{
  "token": "device_token",
  "enabled": true,  // or false to disable notifications
  "notification_types": ["reply", "follow", "like"]  // optional
}
```

**Response (200 OK):**
```json
{
  "message": "Device preferences updated successfully",
  "data": {
    "token": "device_token",
    "enabled": true,
    "notification_types": ["reply", "follow", "like"]
  }
}
```

**Error Responses:**
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `404 Not Found`: Device token not found for this user

---

## Requirements Implemented

- **Requirement 4.1**: Register device token for push notifications
- **Requirement 4.2**: Store token with user and platform information
- **Requirement 4.3**: Update notification preferences per device
- **Requirement 4.4**: Handle device token deregistration

## Integration with Push Service

These endpoints integrate with the `PushNotificationService` located at:
`apps/backend/apps/notifications/push_service.py`

The push service handles:
- Device token storage in the database
- Integration with FCM (Android) and APNs (iOS)
- Notification delivery with retry logic
- Invalid token handling

## Database Models

### DeviceToken Model
```prisma
model DeviceToken {
  id            String   @id @default(cuid())
  user_id       String
  token         String   @unique
  platform      String   // 'ios' or 'android'
  app_version   String?
  is_active     Boolean  @default(true)
  created_at    DateTime @default(now())
  updated_at    DateTime @updatedAt
  last_used_at  DateTime @default(now())
  
  @@index([user_id])
  @@index([platform])
  @@index([is_active])
}
```

## Usage Example

### iOS Client (Swift)
```swift
// Register device token
let token = // ... get from APNs
let body = [
    "token": token,
    "platform": "ios",
    "app_version": Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String
]

// Make POST request to /v1/devices/register
```

### Android Client (Kotlin)
```kotlin
// Register device token
val token = // ... get from FCM
val body = mapOf(
    "token" to token,
    "platform" to "android",
    "app_version" to BuildConfig.VERSION_NAME
)

// Make POST request to /v1/devices/register
```

## Testing

To test these endpoints manually:

1. Start the Django server
2. Obtain a valid JWT token from Clerk
3. Use curl or Postman to make requests:

```bash
# Register device
curl -X POST http://localhost:8000/v1/devices/register \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "test_device_token_123",
    "platform": "ios",
    "app_version": "1.0.0"
  }'

# Unregister device
curl -X DELETE http://localhost:8000/v1/devices/unregister \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "test_device_token_123"
  }'

# Update preferences
curl -X PUT http://localhost:8000/v1/devices/preferences \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "test_device_token_123",
    "enabled": true,
    "notification_types": ["reply", "follow"]
  }'
```
