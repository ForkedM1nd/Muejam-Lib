# Two-Factor Authentication Login Flow

This document describes how 2FA is integrated into the login flow for MueJam Library.

## Overview

The platform uses Clerk for authentication. When a user has 2FA enabled, they must verify their TOTP code or backup code after authenticating with Clerk before they can access protected endpoints.

## Requirements

- **7.4**: WHEN 2FA is enabled and user logs in, THE System SHALL require TOTP code after password verification
- **7.9**: WHEN 2FA is enabled or disabled, THE System SHALL send email notification to the user

## Architecture

### Components

1. **TwoFactorAuthMiddleware**: Enforces 2FA verification for users who have it enabled
2. **TwoFactorEmailService**: Sends email notifications for 2FA events
3. **Session-based verification**: Tracks 2FA verification status in Django sessions

### Login Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    User Login Flow with 2FA                      │
└─────────────────────────────────────────────────────────────────┘

1. User authenticates with Clerk (frontend)
   │
   ├─> Clerk issues JWT token
   │
2. User makes API request with JWT token
   │
   ├─> ClerkAuthMiddleware validates JWT
   │   └─> Sets request.clerk_user_id and request.user_profile
   │
3. TwoFactorAuthMiddleware checks 2FA status
   │
   ├─> Check if user has 2FA enabled
   │   │
   │   ├─> NO: Allow request to proceed
   │   │
   │   └─> YES: Check if 2FA is verified in session
   │       │
   │       ├─> YES: Allow request to proceed
   │       │
   │       └─> NO: Return 403 with 2FA_REQUIRED error
   │           │
   │           └─> Frontend redirects to 2FA verification page
   │
4. User submits TOTP code or backup code
   │
   ├─> POST /v1/users/2fa/verify (TOTP)
   │   OR
   ├─> POST /v1/users/2fa/backup-code (backup code)
   │
5. Backend verifies code
   │
   ├─> If valid:
   │   ├─> Set session['2fa_verified'] = True
   │   ├─> Set session['2fa_user_id'] = user_id
   │   └─> Return success response
   │
   └─> If invalid:
       └─> Return error response
   │
6. User can now access protected endpoints
```

## API Endpoints

### Check 2FA Status

```http
GET /v1/users/2fa/status
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "enabled": true,
  "verified": false
}
```

### Verify TOTP Code

```http
POST /v1/users/2fa/verify
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "token": "123456"
}
```

**Response:**
```json
{
  "message": "2FA verification successful",
  "verified": true
}
```

### Verify Backup Code

```http
POST /v1/users/2fa/backup-code
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "code": "ABCD1234"
}
```

**Response:**
```json
{
  "message": "Backup code verified successfully",
  "verified": true,
  "remaining_codes": 9
}
```

## Error Responses

### 2FA Required

When a user with 2FA enabled tries to access a protected endpoint without verifying:

```json
{
  "error": {
    "code": "2FA_REQUIRED",
    "message": "Two-factor authentication verification required",
    "details": "Please verify your 2FA token to continue"
  }
}
```

**Status Code:** 403 Forbidden

## Session Management

The 2FA verification status is stored in Django sessions:

- `session['2fa_verified']`: Boolean indicating if 2FA is verified
- `session['2fa_user_id']`: User ID to ensure verification matches current user

Sessions are configured with:
- Secure cookies (HTTPS only)
- HttpOnly flag (prevents JavaScript access)
- SameSite=Strict (CSRF protection)
- 30-day expiration

## Exempt Endpoints

The following endpoints do NOT require 2FA verification:

- `/v1/users/2fa/verify` - TOTP verification
- `/v1/users/2fa/backup-code` - Backup code verification
- `/v1/users/2fa/setup` - 2FA setup
- `/v1/users/2fa/verify-setup` - Setup verification
- `/v1/users/2fa/status` - Status check
- `/v1/health/` - Health checks
- `/health` - Health check
- `/metrics` - Metrics
- `/v1/schema/` - API schema
- `/v1/docs/` - API documentation

## Email Notifications

### 2FA Enabled

When a user enables 2FA, they receive an email notification with:
- Confirmation that 2FA is enabled
- Reminder to save backup codes
- Security warning if they didn't enable it

### 2FA Disabled

When a user disables 2FA, they receive an email notification with:
- Confirmation that 2FA is disabled
- Recommendation to re-enable for security
- Link to re-enable 2FA
- Security warning if they didn't disable it

## Frontend Integration

### 1. Check 2FA Status After Login

After successful Clerk authentication, check if 2FA is required:

```javascript
const response = await fetch('/v1/users/2fa/status', {
  headers: {
    'Authorization': `Bearer ${clerkToken}`
  }
});

const { enabled, verified } = await response.json();

if (enabled && !verified) {
  // Redirect to 2FA verification page
  router.push('/verify-2fa');
}
```

### 2. Handle 2FA Required Errors

Intercept 403 errors with `2FA_REQUIRED` code:

```javascript
// In API client interceptor
if (response.status === 403 && response.data?.error?.code === '2FA_REQUIRED') {
  // Redirect to 2FA verification page
  router.push('/verify-2fa');
}
```

### 3. Verify 2FA Code

```javascript
const response = await fetch('/v1/users/2fa/verify', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${clerkToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ token: totpCode })
});

if (response.ok) {
  // 2FA verified, redirect to original destination
  router.push(originalPath);
}
```

## Security Considerations

1. **Session Security**: Sessions use secure cookies with HttpOnly and SameSite flags
2. **User Verification**: Session verification checks that the user ID matches
3. **Token Validation**: TOTP tokens use a 1-window validation (30 seconds before/after)
4. **Backup Codes**: Hashed with bcrypt and invalidated after use
5. **Email Notifications**: Users are notified of all 2FA changes for security awareness

## Testing

### Manual Testing

1. Enable 2FA for a test user
2. Log out and log back in with Clerk
3. Try to access a protected endpoint - should get 2FA_REQUIRED error
4. Verify TOTP code - should succeed
5. Access protected endpoint - should succeed

### Automated Testing

See `test_views.py` for comprehensive test coverage including:
- 2FA verification flow
- Backup code verification
- Session management
- Email notifications

## Troubleshooting

### Issue: 2FA verification not persisting

**Cause**: Session not being saved properly

**Solution**: Ensure `request.session.save()` is called after setting session variables

### Issue: 2FA required for exempt endpoints

**Cause**: Endpoint path not in EXEMPT_PATHS list

**Solution**: Add the endpoint path to `TwoFactorAuthMiddleware.EXEMPT_PATHS`

### Issue: Email notifications not sending

**Cause**: Resend API key not configured or invalid

**Solution**: Check `RESEND_API_KEY` environment variable

## Implementation Notes

- The middleware is placed after `ClerkAuthMiddleware` to ensure user authentication is complete
- Session-based verification is used instead of JWT claims to avoid token refresh issues
- Email notifications are sent asynchronously and don't block the request if they fail
- The status endpoint allows the frontend to check 2FA requirements proactively
