# Error UI Components Usage Guide

This document provides examples of how to use the error UI components implemented for task 20.2.

## Components Overview

### 1. Offline Indicator (ConnectionStatus)
Already implemented in `ConnectionStatus.tsx`. Shows when the user is offline or connection is lost.

### 2. Rate Limit Notification (RateLimitNotification)
Displays when API rate limits are exceeded with countdown timer.

### 3. Error Toast Notifications (errorToast utilities)
Helper functions for displaying various error types as toast notifications.

### 4. Error Boundary Fallback UI (ErrorBoundary)
Already implemented. Catches React component errors and displays fallback UI.

---

## Usage Examples

### Offline Indicator

The offline indicator is automatically displayed via the `FloatingConnectionStatus` component in `App.tsx`:

```tsx
import { FloatingConnectionStatus } from "@/components/shared/ConnectionStatus";

function App() {
  return (
    <>
      {/* Your app content */}
      <FloatingConnectionStatus />
    </>
  );
}
```

For inline display in specific components:

```tsx
import { ConnectionStatus } from "@/components/shared/ConnectionStatus";

function MyComponent() {
  return (
    <div>
      <ConnectionStatus showDetails />
      {/* Rest of component */}
    </div>
  );
}
```

---

### Rate Limit Notification

Use when API returns a 429 status with `Retry-After` header:

```tsx
import { useState } from 'react';
import { RateLimitNotification } from "@/components/shared/RateLimitNotification";

function MyComponent() {
  const [rateLimitInfo, setRateLimitInfo] = useState<{ retryAfter: number } | null>(null);

  const handleApiCall = async () => {
    try {
      const response = await fetch('/api/endpoint');
      if (response.status === 429) {
        const retryAfter = parseInt(response.headers.get('Retry-After') || '60');
        setRateLimitInfo({ retryAfter });
      }
    } catch (error) {
      // Handle error
    }
  };

  return (
    <div>
      {rateLimitInfo && (
        <RateLimitNotification
          retryAfter={rateLimitInfo.retryAfter}
          onDismiss={() => setRateLimitInfo(null)}
        />
      )}
      {/* Rest of component */}
    </div>
  );
}
```

For floating notification:

```tsx
import { FloatingRateLimitNotification } from "@/components/shared/RateLimitNotification";

function MyComponent() {
  const [rateLimitInfo, setRateLimitInfo] = useState<{ retryAfter: number } | null>(null);

  return (
    <>
      {rateLimitInfo && (
        <FloatingRateLimitNotification
          retryAfter={rateLimitInfo.retryAfter}
          onDismiss={() => setRateLimitInfo(null)}
        />
      )}
      {/* Rest of component */}
    </>
  );
}
```

---

### Error Toast Notifications

Import and use the error toast utilities:

```tsx
import { 
  showErrorToast,
  showNetworkErrorToast,
  showRateLimitToast,
  showAuthErrorToast,
  showValidationErrorToast,
  showSuccessToast
} from "@/lib/errorToast";

// Generic error handling
try {
  await someApiCall();
} catch (error) {
  showErrorToast(error); // Automatically determines error type and shows appropriate toast
}

// Specific error types
showNetworkErrorToast(); // Network connection error
showRateLimitToast(60); // Rate limit with 60 second retry
showAuthErrorToast(); // Authentication required
showValidationErrorToast({ email: ['Invalid email format'] }); // Validation errors

// Success messages
showSuccessToast('Story published successfully!');
```

#### Integration with API Client

The error toast utilities work seamlessly with the API client error handling:

```tsx
import { api } from "@/lib/api";
import { showErrorToast } from "@/lib/errorToast";

async function createStory(data: StoryData) {
  try {
    const story = await api.createStory(data);
    showSuccessToast('Story created successfully!');
    return story;
  } catch (error) {
    showErrorToast(error, 'Failed to create story');
    throw error;
  }
}
```

#### Integration with React Query Mutations

```tsx
import { useMutation } from '@tanstack/react-query';
import { api } from "@/lib/api";
import { showErrorToast, showSuccessToast } from "@/lib/errorToast";

function useCreateStory() {
  return useMutation({
    mutationFn: (data: StoryData) => api.createStory(data),
    onSuccess: () => {
      showSuccessToast('Story created successfully!');
    },
    onError: (error) => {
      showErrorToast(error, 'Failed to create story');
    },
  });
}
```

---

### Error Boundary Fallback UI

Wrap components that might throw errors:

```tsx
import { ErrorBoundary } from "@/components/shared/ErrorBoundary";

function App() {
  return (
    <ErrorBoundary>
      <MyComponent />
    </ErrorBoundary>
  );
}
```

With custom fallback:

```tsx
import { ErrorBoundary } from "@/components/shared/ErrorBoundary";

function App() {
  return (
    <ErrorBoundary
      fallback={(error, reset) => (
        <div>
          <h1>Custom Error UI</h1>
          <p>{error.message}</p>
          <button onClick={reset}>Try Again</button>
        </div>
      )}
      onError={(error, errorInfo) => {
        console.error('Error caught:', error, errorInfo);
      }}
    >
      <MyComponent />
    </ErrorBoundary>
  );
}
```

For async errors outside of render:

```tsx
import { useErrorBoundary } from "@/components/shared/ErrorBoundary";

function MyComponent() {
  const throwError = useErrorBoundary();

  const handleAsyncError = async () => {
    try {
      await someAsyncOperation();
    } catch (error) {
      throwError(error as Error); // Triggers error boundary
    }
  };

  return <button onClick={handleAsyncError}>Do Something</button>;
}
```

---

## Complete Integration Example

Here's a complete example showing all error UI components working together:

```tsx
import { useState } from 'react';
import { ErrorBoundary } from "@/components/shared/ErrorBoundary";
import { FloatingConnectionStatus } from "@/components/shared/ConnectionStatus";
import { FloatingRateLimitNotification } from "@/components/shared/RateLimitNotification";
import { showErrorToast, showSuccessToast } from "@/lib/errorToast";
import { useMutation } from '@tanstack/react-query';
import { api } from "@/lib/api";

function MyFeature() {
  const [rateLimitInfo, setRateLimitInfo] = useState<{ retryAfter: number } | null>(null);

  const createMutation = useMutation({
    mutationFn: (data: FormData) => api.createResource(data),
    onSuccess: () => {
      showSuccessToast('Resource created successfully!');
    },
    onError: (error: any) => {
      // Check for rate limit
      if (error.type === 'RATE_LIMIT_EXCEEDED' && error.retryAfter) {
        setRateLimitInfo({ retryAfter: error.retryAfter });
      }
      // Show error toast
      showErrorToast(error, 'Failed to create resource');
    },
  });

  return (
    <ErrorBoundary>
      <div>
        {/* Your component content */}
        <button onClick={() => createMutation.mutate(formData)}>
          Create Resource
        </button>

        {/* Rate limit notification */}
        {rateLimitInfo && (
          <FloatingRateLimitNotification
            retryAfter={rateLimitInfo.retryAfter}
            onDismiss={() => setRateLimitInfo(null)}
          />
        )}

        {/* Connection status (automatically shown when offline) */}
        <FloatingConnectionStatus />
      </div>
    </ErrorBoundary>
  );
}
```

---

## Testing

All error UI components should be tested to ensure they work correctly:

```tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { RateLimitNotification } from './RateLimitNotification';
import { showErrorToast } from '@/lib/errorToast';

describe('RateLimitNotification', () => {
  it('should display countdown timer', async () => {
    const onDismiss = vi.fn();
    render(<RateLimitNotification retryAfter={5} onDismiss={onDismiss} />);
    
    expect(screen.getByText(/5 seconds/i)).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.getByText(/4 seconds/i)).toBeInTheDocument();
    }, { timeout: 1500 });
  });

  it('should call onDismiss when countdown reaches zero', async () => {
    const onDismiss = vi.fn();
    render(<RateLimitNotification retryAfter={1} onDismiss={onDismiss} />);
    
    await waitFor(() => {
      expect(onDismiss).toHaveBeenCalled();
    }, { timeout: 1500 });
  });
});
```

---

## Requirements Validation

This implementation satisfies the following requirements:

- **Requirement 17.3**: Offline indicator via `ConnectionStatus` component ✓
- **Requirement 17.4**: Rate limit notification with retry time via `RateLimitNotification` ✓
- **Requirement 17.9**: Fallback UI for component errors via `ErrorBoundary` ✓

Additional features implemented:
- Error toast notifications for all error types
- Integration with existing toast system
- Automatic error type detection
- Countdown timers for rate limits
- Floating and inline display options
