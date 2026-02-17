# Users App - Clerk Authentication

This app handles user authentication and profile management using Clerk.

## Components

### ClerkAuthMiddleware (`middleware.py`)

The authentication middleware that:
1. Extracts JWT tokens from the `Authorization` header
2. Verifies tokens with Clerk using `authenticate_request`
3. Extracts the `clerk_user_id` from verified tokens
4. Fetches or creates a `UserProfile` for the authenticated user
5. Attaches `clerk_user_id` and `user_profile` to the request object

**Usage:**
The middleware is automatically applied to all requests via `config/settings.py`.

**Request Attributes:**
- `request.clerk_user_id`: The Clerk user ID (string) or None if not authenticated
- `request.user_profile`: The UserProfile instance or None if not authenticated

### get_or_create_profile (`utils.py`)

Async utility function that retrieves an existing UserProfile or creates a new one.

**Features:**
- Searches for existing profile by `clerk_user_id`
- Creates new profile with auto-generated handle if not found
- Ensures handle uniqueness by appending numbers if needed
- Default handle format: `user_{clerk_user_id[:8]}`

**Requirements Satisfied:**
- 1.1: Clerk authentication flow integration
- 1.2: Create or retrieve UserProfile using clerk_user_id
- 1.5: Handle format validation (alphanumeric with underscores)

## Testing

### Manual Testing

Test the authentication middleware using the test endpoint:

```bash
# Without authentication (should return authenticated: false)
curl http://localhost:8000/v1/users/test-auth/

# With authentication (requires valid Clerk JWT token)
curl -H "Authorization: Bearer YOUR_CLERK_JWT_TOKEN" \
     http://localhost:8000/v1/users/test-auth/
```

### Automated Tests

Run the test suite:

```bash
cd backend
pytest apps/users/tests.py -v
```

## Configuration

Required environment variables in `.env`:

```env
CLERK_SECRET_KEY=your-clerk-secret-key
CLERK_PUBLISHABLE_KEY=your-clerk-publishable-key
```

## Implementation Notes

1. **Async/Sync Bridge**: The middleware uses `asyncio.run_until_complete()` to call the async `get_or_create_profile` function from the synchronous middleware context.

2. **Error Handling**: Authentication failures are logged but don't block the request. The request continues with `clerk_user_id=None` and `user_profile=None`.

3. **Profile Creation**: New profiles are created automatically on first authentication with default values. Users can update their profile later via the profile management endpoints.

4. **Handle Generation**: Default handles are generated from the first 8 characters of the clerk_user_id with a "user_" prefix. If a handle collision occurs, a numeric suffix is appended.

## Next Steps

- Implement profile update endpoints (PUT /v1/me)
- Implement profile retrieval endpoints (GET /v1/me, GET /v1/users/{handle})
- Add handle format validation for user updates
- Add avatar upload functionality
