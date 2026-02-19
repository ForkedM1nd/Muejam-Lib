# Zustand Stores

This directory contains global state management stores using Zustand.

## Onboarding Store

The `useOnboardingStore` manages the user onboarding state and progress.

### Features

- **State Persistence**: Onboarding progress is persisted to localStorage
- **Backend Integration**: Syncs with backend API endpoints
- **Completion Prompt**: Automatically shows dismissible prompt for incomplete onboarding
- **Progress Tracking**: Tracks profile setup, interests selection, and tutorial completion

### Usage

```typescript
import { useOnboardingStore } from '@/stores/useOnboardingStore';

function MyComponent() {
  const { progress, loading, fetchProgress, updateStep } = useOnboardingStore();
  
  // Fetch progress on mount
  useEffect(() => {
    fetchProgress();
  }, []);
  
  // Update a step
  const handleComplete = async () => {
    const success = await updateStep('profile_completed');
    if (success) {
      // Handle success
    }
  };
}
```

### API Methods

- `fetchProgress()`: Fetches onboarding progress from backend
- `updateStep(step: string)`: Updates a specific onboarding step
- `skipOnboarding()`: Skips onboarding (can be completed later)
- `markAsOnboarded()`: Marks onboarding as fully complete
- `dismissCompletionPrompt()`: Dismisses the completion prompt for 24 hours

### State

- `progress`: Current onboarding progress data
- `loading`: Loading state for API calls
- `error`: Error message if any
- `showCompletionPrompt`: Whether to show the completion prompt

### Requirements Validated

- **4.5**: Marks user as onboarded via backend
- **4.7**: Displays completion prompt for incomplete onboarding
- **4.8**: Persists onboarding progress across sessions
