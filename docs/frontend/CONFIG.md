# Configuration Management

This document describes the configuration management system for the MueJam Library frontend application.

## Overview

The application uses a centralized configuration system that supports:
- Environment-specific settings (development, staging, production)
- Feature flags for gradual rollouts
- A/B testing experiments
- Dynamic configuration from the backend
- Hot-reloading in development

## Environment Variables

All configuration is loaded from environment variables prefixed with `VITE_`.

### Core Configuration

```bash
# Environment (automatically set by Vite)
MODE=development|staging|production

# API Configuration
VITE_API_BASE_URL=https://api.muejam.com/v1
VITE_WS_URL=wss://api.muejam.com/ws

# Authentication
VITE_CLERK_PUBLISHABLE_KEY=your-clerk-key

# Push Notifications
VITE_VAPID_PUBLIC_KEY=your-vapid-key
```

### Feature Flags

Feature flags can be enabled/disabled via environment variables:

```bash
VITE_ENABLE_PUSH_NOTIFICATIONS=true
VITE_ENABLE_OFFLINE_MODE=true
VITE_ENABLE_ANALYTICS=true
VITE_ENABLE_WEBSOCKET=true
VITE_ENABLE_SERVICE_WORKER=true
```

### A/B Testing

Experiments can be configured using a comma-separated list:

```bash
VITE_EXPERIMENTS=newDesign:true,betaFeature:false
```

### Monitoring

```bash
VITE_ENABLE_SENTRY=true
VITE_SENTRY_DSN=https://your-dsn@sentry.io/project
VITE_ENABLE_PERFORMANCE_MONITORING=true
```

## Usage

### Accessing Configuration

```typescript
import { config, isFeatureEnabled, isExperimentEnabled } from "@/lib/config";

// Access configuration
const apiUrl = config.api.baseUrl;
const isDev = config.isDevelopment;

// Check feature flags
if (isFeatureEnabled("enablePushNotifications")) {
  // Enable push notifications
}

// Check experiments
if (isExperimentEnabled("newDesign")) {
  // Show new design
}
```

### Using Feature Flags in Components

```tsx
import { FeatureFlag } from "@/components/shared/FeatureFlag";

function MyComponent() {
  return (
    <FeatureFlag feature="enablePushNotifications">
      <PushNotificationSettings />
    </FeatureFlag>
  );
}
```

### Using Feature Flag Hooks

```tsx
import { useFeatureFlag, useExperiment } from "@/components/shared/FeatureFlag";

function MyComponent() {
  const isPushEnabled = useFeatureFlag("enablePushNotifications");
  const isNewDesign = useExperiment("newDesign");

  return (
    <div>
      {isPushEnabled && <PushSettings />}
      {isNewDesign ? <NewDesign /> : <OldDesign />}
    </div>
  );
}
```

### Dynamic Configuration

Fetch configuration from the backend:

```tsx
import { useDynamicConfig } from "@/hooks/useDynamicConfig";

function MyComponent() {
  const { data: config, isLoading } = useDynamicConfig("/config/mobile/");

  if (isLoading) return <Loading />;

  return <div>{/* Use config */}</div>;
}
```

### Feature Flag Provider

For advanced use cases with dynamic flags from the backend:

```tsx
import { FeatureFlagProvider, useFeatureFlags } from "@/contexts/FeatureFlagContext";

// In your app root
function App() {
  return (
    <FeatureFlagProvider fetchDynamic>
      <YourApp />
    </FeatureFlagProvider>
  );
}

// In your components
function MyComponent() {
  const { isFeatureEnabled, refreshFlags } = useFeatureFlags();

  return (
    <div>
      {isFeatureEnabled("enableAnalytics") && <Analytics />}
      <button onClick={refreshFlags}>Refresh Flags</button>
    </div>
  );
}
```

## Environment Files

The project includes example environment files for each environment:

- `.env.example` - Development environment
- `.env.staging.example` - Staging environment
- `.env.production.example` - Production environment

Copy the appropriate file to `.env` and update the values:

```bash
# For development
cp .env.example .env

# For staging
cp .env.staging.example .env.staging

# For production
cp .env.production.example .env.production
```

## Building for Different Environments

```bash
# Development build
npm run build

# Staging build
npm run build -- --mode staging

# Production build
npm run build -- --mode production
```

## Validation

The configuration system validates required values on startup:
- In development: Logs warnings for missing values
- In production: Throws errors for missing required values

## Hot Reloading

In development mode, configuration changes are automatically detected and reloaded without restarting the dev server.

## Best Practices

1. **Never commit `.env` files** - Use `.env.example` files as templates
2. **Use feature flags for new features** - Enable gradually in production
3. **Test experiments in staging first** - Validate before production rollout
4. **Keep sensitive values secure** - Use environment-specific secrets
5. **Document new configuration** - Update this file when adding new config options
6. **Validate configuration** - Add validation for new required values

## Troubleshooting

### Configuration not loading

1. Check that environment variables are prefixed with `VITE_`
2. Restart the dev server after changing `.env` files
3. Check the console for validation errors

### Feature flag not working

1. Verify the feature flag name matches the config
2. Check that the environment variable is set correctly
3. Clear the browser cache and reload

### Dynamic configuration failing

1. Check network requests in browser DevTools
2. Verify the backend endpoint is accessible
3. Check for CORS issues
