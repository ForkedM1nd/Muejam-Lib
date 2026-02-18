# Email Verification Module

This module implements email verification functionality for user accounts, ensuring that users verify their email addresses before they can create content on the platform.

## Requirements

This implementation satisfies the following requirements from the production-readiness spec:

- **Requirement 5.1**: Email verification required before content creation
- **Requirement 5.2**: Send verification emails with time-limited tokens (24 hours expiration)
- **Requirement 5.3**: Block content creation for unverified users

## Components

### Database Model

**EmailVerification** (`prisma/schema.prisma`)
- `id`: UUID primary key
- `user_id`: User ID (references UserProfile)
- `email`: Email address to verify
- `token`: Unique verification token
- `created_at`: Timestamp when verification was created
- `expires_at`: Token expiration timestamp (24 hours from creation)
- `verified_at`: Timestamp when email was verified (null if not verified)

### Service Layer

**EmailVerificationService** (`service.py`)

Main service class that handles:
- Token generation using cryptographically secure random tokens
- Creating verification records with 24-hour expiration
- Sending verification emails via Resend
- Validating verification tokens
- Checking verification status
- Resending verification emails

Key methods:
- `create_verification(user_id, email)`: Creates verification record and sends email
- `send_verification_email(email, token)`: Sends verification email via Resend
- `verify_token(token)`: Validates token and marks email as verified
- `is_email_verified(user_id)`: Checks if user's email is verified
- `resend_verification(user_id, email)`: Resends verification email

### API Endpoints

All endpoints are prefixed with `/api/v1/users/email-verification/`

#### 1. Send Verification Email
```
POST /api/v1/users/email-verification/send
```

**Authentication**: Required

**Request Body**:
```json
{
  "email": "user@example.com"
}
```

**Response** (200 OK):
```json
{
  "message": "Verification email sent successfully",
  "email": "user@example.com"
}
```

**Errors**:
- 400: Email does not match account
- 500: Failed to send email

#### 2. Verify Email
```
POST /api/v1/users/email-verification/verify
```

**Authentication**: Not required (public endpoint)

**Request Body**:
```json
{
  "token": "verification_token_here"
}
```

**Response** (200 OK):
```json
{
  "message": "Email verified successfully",
  "user_id": "user_id_here"
}
```

**Errors**:
- 400: Invalid or expired token
- 500: Failed to verify email

#### 3. Check Verification Status
```
GET /api/v1/users/email-verification/status
```

**Authentication**: Required

**Response** (200 OK):
```json
{
  "is_verified": true,
  "message": "Email is verified"
}
```

**Errors**:
- 500: Failed to check status

#### 4. Resend Verification Email
```
POST /api/v1/users/email-verification/resend
```

**Authentication**: Required

**Request Body**:
```json
{
  "email": "user@example.com"
}
```

**Response** (200 OK):
```json
{
  "message": "Verification email resent successfully",
  "email": "user@example.com"
}
```

**Errors**:
- 400: Email already verified or does not match account
- 500: Failed to resend email

## Email Template

The verification email includes:
- Clear call-to-action button
- Verification link (also as plain text for copy/paste)
- 24-hour expiration warning
- Support contact information
- Both HTML and plain text versions

## Security Features

1. **Cryptographically Secure Tokens**: Uses `secrets.token_urlsafe(32)` for token generation
2. **Token Expiration**: Tokens expire after 24 hours
3. **Single-Use Tokens**: Tokens are marked as used after verification
4. **Email Validation**: Verifies email matches user's Clerk account
5. **Rate Limiting**: Should be applied at the API gateway level

## Integration with Resend

The service uses the Resend email API to send verification emails:
- API key configured via `RESEND_API_KEY` environment variable
- From email configured via `RESEND_FROM_EMAIL` environment variable
- Frontend URL configured via `FRONTEND_URL` environment variable

## Usage Example

### Backend Integration

```python
from apps.users.email_verification.service import EmailVerificationService

# Create verification and send email
service = EmailVerificationService()
token = await service.create_verification(user_id, email)

# Check if email is verified
is_verified = await service.is_email_verified(user_id)

# Verify token
user_id = await service.verify_token(token)
```

### Frontend Integration

1. **After Registration**: Call `/send` endpoint to send verification email
2. **Verification Page**: Extract token from URL query parameter and call `/verify` endpoint
3. **Before Content Creation**: Check `/status` endpoint to ensure email is verified
4. **Resend Option**: Provide UI to call `/resend` endpoint if user didn't receive email

## Testing

To test the email verification flow:

1. Create a user account
2. Call the send verification endpoint
3. Check email for verification link
4. Click link or use token to verify
5. Confirm verification status

## Environment Variables

Required environment variables:
- `RESEND_API_KEY`: Resend API key for sending emails
- `RESEND_FROM_EMAIL`: Email address to send from (default: noreply@muejam.com)
- `FRONTEND_URL`: Frontend base URL for verification links (default: http://localhost:3000)

## Next Steps

To complete the abuse prevention system (Requirement 5.3), implement middleware to:
1. ~~Check email verification status before allowing content creation~~ ✅ **COMPLETED**
2. ~~Return appropriate error message for unverified users~~ ✅ **COMPLETED**
3. ~~Apply to all content creation endpoints (stories, chapters, whispers)~~ ✅ **COMPLETED**

**Task 12.2 is now complete!** See archived documentation in `docs/archive/ai-artifacts/MIDDLEWARE_IMPLEMENTATION.md` for details.
