# Authentication Implementation Guide

This document describes the authentication implementation in the MueJam Library frontend application.

## Overview

The application uses [Clerk](https://clerk.com/) for authentication, providing a complete auth solution with:
- User sign-up and sign-in
- Session management
- Token-based API authentication
- User profile management
- Social login support (configurable in Clerk dashboard)

## Architecture

### Components

1. **Sign-In Page** (`/sign-in`)
   - Full-page Clerk sign-in component
   - Redirects to `/discover` after successful sign-in
   - Link to sign-up page

2. **Sign-Up Page** (`/sign-up`)
   - Full-page Clerk sign-up component
   - Redirects to `/discover` after successful sign-up
   - Link to sign-in page

3. **Protected Routes**
   - Wraps pages that require authentication
   - Redirects to `/sign-in` if not authenticated
   - Shows loading state while checking auth status

4. **Auth Hooks**
   - `useSafeAuth`: Safe wrapper around Clerk's `useAuth` hook
   - Works even when Clerk is not configured (dev mode)
   - Provides: `isSignedIn`, `isLoaded`, `userId`, `getToken`

### Authentication Flow

```
User visits protected route
  ↓
ProtectedRoute checks auth status
  ↓
If not authenticated → Redirect to /sign-in
  ↓
User signs in via Clerk
  ↓
Clerk sets session cookie
  ↓
Redirect back to original route
  ↓
API calls include Bearer token
```

## Setup Instructions

### 1. Create Clerk Account

1. Go to [clerk.com](https://clerk.com/) and sign up
2. Create a new application
3. Copy your Publishable Key

### 2. Configure Environment Variables

Create a `.env` file in the `frontend` directory:

```bash
# Required
VITE_CLERK_PUBLISHABLE_KEY=pk_test_your_key_here

# Optional (defaults shown)
VITE_CLERK_SIGN_IN_URL=/sign-in
VITE_CLERK_SIGN_UP_URL=/sign-up
VITE_CLERK_AFTER_SIGN_IN_URL=/discover
VITE_CLERK_AFTER_SIGN_UP_URL=/discover

# API Configuration
VITE_API_BASE_URL=http://localhost:8000/v1
```

### 3. Configure Clerk Dashboard

In your Clerk dashboard:

1. **Paths**:
   - Sign-in URL: `/sign-in`
   - Sign-up URL: `/sign-up`
   - After sign-in URL: `/discover`
   - After sign-up URL: `/discover`

2. **Session Settings**:
   - Enable "Multi-session" if you want users to be signed in across multiple tabs
   - Set session lifetime (default: 7 days)

3. **Social Connections** (optional):
   - Enable Google, GitHub, etc. in the "Social Connections" section

4. **User Profile**:
   - Configure required fields (email, username, etc.)
   - Set up profile picture requirements

## API Integration

### Token Injection

The application automatically injects Clerk tokens into API requests:

```typescript
// In App.tsx
function TokenInjector() {
  const { getToken } = useAuth();
  useEffect(() => {
    setTokenGetter(() => getToken());
  }, [getToken]);
  return null;
}
```

### API Client

The API client (`lib/api.ts`) automatically adds the Bearer token:

```typescript
// Add authentication token
if (getTokenFn) {
  const token = await getTokenFn();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
}
```

## Usage Examples

### Protecting a Route

```typescript
import ProtectedRoute from "@/components/shared/ProtectedRoute";

function App() {
  return (
    <Routes>
      <Route 
        path="/library" 
        element={
          <AppShell>
            <ProtectedRoute>
              <Library />
            </ProtectedRoute>
          </AppShell>
        } 
      />
    </Routes>
  );
}
```

### Using Auth in Components

```typescript
import { useSafeAuth } from "@/hooks/useSafeAuth";

function MyComponent() {
  const { isSignedIn, isLoaded, userId, getToken } = useSafeAuth();

  if (!isLoaded) {
    return <LoadingSpinner />;
  }

  if (!isSignedIn) {
    return <p>Please sign in</p>;
  }

  return <p>Welcome, user {userId}!</p>;
}
```

### Making Authenticated API Calls

```typescript
import { api } from "@/lib/api";

// The token is automatically included
const stories = await api.getStories();
```

### Custom Sign-In Button

```typescript
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";

function CustomSignInButton() {
  const navigate = useNavigate();
  
  return (
    <Button onClick={() => navigate("/sign-in")}>
      Sign In
    </Button>
  );
}
```

## Development Mode

The application works without Clerk configuration for development:

1. If `VITE_CLERK_PUBLISHABLE_KEY` is not set:
   - Auth buttons show "Auth not configured"
   - Protected routes show a message instead of redirecting
   - API calls work without authentication

2. This allows:
   - Frontend development without backend
   - Testing UI without auth setup
   - Easier onboarding for new developers

## Troubleshooting

### "Clerk is not loaded" Error

**Problem**: Clerk components fail to load

**Solutions**:
1. Check that `VITE_CLERK_PUBLISHABLE_KEY` is set correctly
2. Verify the key starts with `pk_test_` or `pk_live_`
3. Restart the dev server after changing `.env`

### Infinite Redirect Loop

**Problem**: User keeps getting redirected between pages

**Solutions**:
1. Check Clerk dashboard paths match your routes
2. Verify `afterSignInUrl` and `afterSignUpUrl` are correct
3. Clear browser cookies and try again

### Token Not Included in API Calls

**Problem**: API returns 401 Unauthorized

**Solutions**:
1. Check that `TokenInjector` is rendered in `App.tsx`
2. Verify `setTokenGetter` is called with Clerk's `getToken`
3. Check browser console for token-related errors
4. Verify backend is accepting Clerk tokens

### Sign-In Page Not Styled

**Problem**: Clerk components don't match app theme

**Solutions**:
1. Customize appearance in Clerk dashboard
2. Use `appearance` prop on Clerk components:

```typescript
<SignIn
  appearance={{
    elements: {
      rootBox: "mx-auto",
      card: "shadow-lg",
      formButtonPrimary: "bg-primary hover:bg-primary/90",
    },
  }}
/>
```

## Security Best Practices

1. **Never commit `.env` files**
   - Add `.env` to `.gitignore`
   - Use `.env.example` for documentation

2. **Use environment-specific keys**
   - Test keys (`pk_test_`) for development
   - Live keys (`pk_live_`) for production

3. **Configure CORS properly**
   - Set allowed origins in Clerk dashboard
   - Match your deployment URLs

4. **Enable MFA** (optional)
   - Configure in Clerk dashboard
   - Require for admin users

5. **Monitor sessions**
   - Review active sessions in Clerk dashboard
   - Set appropriate session timeouts

## Testing

### Unit Tests

```typescript
import { render, screen } from "@testing-library/react";
import { useSafeAuth } from "@/hooks/useSafeAuth";

// Mock the auth hook
jest.mock("@/hooks/useSafeAuth");

test("shows content when authenticated", () => {
  (useSafeAuth as jest.Mock).mockReturnValue({
    isSignedIn: true,
    isLoaded: true,
    userId: "user_123",
    getToken: async () => "token",
  });

  render(<ProtectedComponent />);
  expect(screen.getByText("Protected content")).toBeInTheDocument();
});
```

### Integration Tests

```typescript
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

test("redirects to sign-in when accessing protected route", async () => {
  render(<App />);
  
  // Try to access protected route
  await userEvent.click(screen.getByText("Library"));
  
  // Should redirect to sign-in
  await waitFor(() => {
    expect(screen.getByText("Sign in to MueJam")).toBeInTheDocument();
  });
});
```

## Migration Guide

### From Another Auth Provider

If migrating from another auth provider:

1. **Export user data** from old provider
2. **Import users** to Clerk via dashboard or API
3. **Update auth hooks** to use `useSafeAuth`
4. **Replace auth components** with Clerk components
5. **Update API token validation** on backend
6. **Test thoroughly** before deploying

### Backend Integration

The backend should validate Clerk tokens:

```python
# Django example
from clerk_backend_api import Clerk

clerk = Clerk(bearer_auth=os.environ.get("CLERK_SECRET_KEY"))

def verify_token(token: str):
    try:
        session = clerk.sessions.verify_session(token)
        return session.user_id
    except Exception:
        raise AuthenticationError("Invalid token")
```

## Additional Resources

- [Clerk Documentation](https://clerk.com/docs)
- [Clerk React SDK](https://clerk.com/docs/references/react/overview)
- [Clerk Dashboard](https://dashboard.clerk.com/)
- [Clerk Community](https://clerk.com/community)

## Support

For authentication issues:
1. Check this documentation
2. Review Clerk documentation
3. Check browser console for errors
4. Contact team lead or create an issue
