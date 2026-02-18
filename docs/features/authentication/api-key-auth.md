# API Key Authentication

This module implements API key authentication for external integrations, supporting key generation, rotation, and secure validation.

**Requirements:** 6.10

## Overview

The API key authentication system provides a secure way for external applications and services to authenticate with the MueJam Library API. It includes:

- Secure API key generation using cryptographically secure random tokens
- SHA-256 hashing for key storage (keys are never stored in plain text)
- Key rotation capability for security best practices
- Key expiration and revocation
- Scoped permissions for fine-grained access control
- Last-used tracking for monitoring

## Database Schema

### APIKey Model

```prisma
model APIKey {
  id           String    @id @default(uuid())
  key_hash     String    @unique
  name         String
  user_id      String
  created_at   DateTime  @default(now())
  last_used_at DateTime?
  expires_at   DateTime
  is_active    Boolean   @default(true)
  permissions  Json      @default("{}")
}
```

**Fields:**
- `id`: Unique identifier for the API key
- `key_hash`: SHA-256 hash of the API key (never store plain text keys!)
- `name`: Descriptive name for the key (e.g., "Production Server", "CI/CD Pipeline")
- `user_id`: The user who owns this API key
- `created_at`: When the key was created
- `last_used_at`: Last time the key was used for authentication
- `expires_at`: When the key expires (default: 1 year from creation)
- `is_active`: Whether the key is active (can be revoked)
- `permissions`: JSON object containing scoped permissions

## Components

### APIKeyService

The `APIKeyService` class provides methods for managing API keys:

#### `generate_api_key() -> str`
Generates a secure 64-character hexadecimal API key using `secrets.token_hex(32)`.

#### `hash_api_key(api_key: str) -> str`
Hashes an API key using SHA-256 for secure storage.

#### `create_api_key(user_id, name, expires_in_days=365, permissions=None) -> (APIKey, str)`
Creates a new API key for a user. Returns both the database record and the plain text key.

**Important:** The plain text key is only returned once during creation!

#### `rotate_api_key(api_key_id: str) -> (APIKey, str)`
Rotates an existing API key by generating a new key value while preserving the key ID and metadata.

#### `revoke_api_key(api_key_id: str) -> APIKey`
Revokes an API key by marking it as inactive.

#### `validate_api_key(plain_key: str) -> Optional[APIKey]`
Validates an API key and returns the associated record if valid. Updates the `last_used_at` timestamp.

#### `list_user_api_keys(user_id: str, include_inactive=False) -> list[APIKey]`
Lists all API keys for a user.

### APIKeyAuthentication

Django REST Framework authentication class that validates API keys from the `X-API-Key` header.

**Usage:**

Add to `REST_FRAMEWORK` settings:

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'apps.core.api_key_auth.APIKeyAuthentication',
        # ... other authentication classes
    ]
}
```

## API Endpoints

### Create API Key

**POST** `/api/core/api-keys/`

Creates a new API key for the authenticated user.

**Request Body:**
```json
{
  "name": "Production Server",
  "expires_in_days": 365,
  "permissions": {
    "read": true,
    "write": false
  }
}
```

**Response (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Production Server",
  "api_key": "a1b2c3d4e5f6...64-char-hex-string",
  "created_at": "2024-02-17T16:30:00Z",
  "expires_at": "2025-02-17T16:30:00Z",
  "permissions": {
    "read": true,
    "write": false
  },
  "warning": "Store this API key securely. It will not be shown again."
}
```

### List API Keys

**GET** `/api/core/api-keys/list/`

Lists all API keys for the authenticated user.

**Query Parameters:**
- `include_inactive` (boolean, optional): Include revoked keys (default: false)

**Response (200 OK):**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Production Server",
    "created_at": "2024-02-17T16:30:00Z",
    "last_used_at": "2024-02-17T18:45:00Z",
    "expires_at": "2025-02-17T16:30:00Z",
    "is_active": true,
    "is_expired": false,
    "permissions": {
      "read": true,
      "write": false
    }
  }
]
```

### Rotate API Key

**POST** `/api/core/api-keys/{key_id}/rotate/`

Rotates an existing API key by generating a new key value.

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Production Server",
  "api_key": "new-64-char-hex-string",
  "created_at": "2024-02-17T16:30:00Z",
  "expires_at": "2025-02-17T16:30:00Z",
  "permissions": {
    "read": true,
    "write": false
  },
  "warning": "Store this API key securely. It will not be shown again."
}
```

### Revoke API Key

**DELETE** `/api/core/api-keys/{key_id}/revoke/`

Revokes an API key by marking it as inactive.

**Response (200 OK):**
```json
{
  "message": "API key revoked successfully"
}
```

## Using API Keys

To authenticate with an API key, include it in the `X-API-Key` header:

```bash
curl -H "X-API-Key: your-64-char-api-key" \
     https://api.muejam.com/api/stories/
```

## Security Best Practices

1. **Never log or display API keys** after initial creation
2. **Store keys securely** using environment variables or secret management systems
3. **Rotate keys regularly** (recommended: every 90-180 days)
4. **Use scoped permissions** to limit key capabilities
5. **Monitor last_used_at** to detect unused or compromised keys
6. **Revoke keys immediately** if compromised
7. **Set appropriate expiration dates** (default: 1 year)

## Key Rotation Strategy

Regular key rotation is a security best practice:

1. Create a new API key with the same permissions
2. Update your application to use the new key
3. Verify the new key works correctly
4. Revoke the old key
5. Monitor for any issues

Alternatively, use the rotate endpoint to generate a new key value while keeping the same key ID.

## Permissions System

The `permissions` field is a JSON object that can store scoped permissions:

```json
{
  "read": true,
  "write": false,
  "admin": false,
  "resources": ["stories", "whispers"],
  "rate_limit": 1000
}
```

**Note:** Permission enforcement must be implemented in your API views based on your application's requirements.

## Monitoring and Auditing

- Track `last_used_at` to identify inactive keys
- Monitor key creation and rotation events
- Alert on suspicious patterns (e.g., many failed authentication attempts)
- Regularly audit active keys and revoke unused ones

## Testing

Example test for API key authentication:

```python
import pytest
from apps.core.api_key_auth import APIKeyService

@pytest.mark.asyncio
async def test_create_and_validate_api_key():
    # Create API key
    api_key_obj, plain_key = await APIKeyService.create_api_key(
        user_id="test-user-id",
        name="Test Key"
    )
    
    assert api_key_obj.name == "Test Key"
    assert len(plain_key) == 64
    
    # Validate API key
    validated_key = await APIKeyService.validate_api_key(plain_key)
    assert validated_key is not None
    assert validated_key.id == api_key_obj.id
    
    # Invalid key should return None
    invalid_key = await APIKeyService.validate_api_key("invalid-key")
    assert invalid_key is None
```

## Implementation Notes

- API keys are 64-character hexadecimal strings (256 bits of entropy)
- Keys are hashed using SHA-256 before storage
- The authentication class uses asyncio to call async Prisma methods
- Keys are validated on every request and `last_used_at` is updated
- Expired or inactive keys are rejected during validation

## Future Enhancements

Potential improvements for the API key system:

1. Rate limiting per API key
2. IP address whitelisting
3. Usage analytics and reporting
4. Automatic key rotation reminders
5. Webhook notifications for key events
6. Multi-factor authentication for key creation
7. Key usage quotas and billing integration
