# Monitoring and Observability

This document describes the monitoring and observability features implemented in the MueJam Library frontend application.

## Overview

The application includes comprehensive monitoring capabilities:

- **Error Tracking**: Sentry integration for error logging and debugging
- **Performance Monitoring**: Web Vitals tracking and custom performance metrics
- **User Analytics**: Event tracking and user behavior analysis
- **Bundle Analysis**: Tools for analyzing and optimizing bundle size

## Error Tracking with Sentry

### Configuration

Sentry is configured via environment variables:

```env
VITE_ENABLE_SENTRY=true
VITE_SENTRY_DSN=your-sentry-dsn-here
VITE_ENABLE_PERFORMANCE_MONITORING=true
```

### Features

- **Automatic Error Capture**: All unhandled errors are automatically sent to Sentry
- **Error Filtering**: Sensitive data (tokens, passwords, emails) is automatically filtered
- **Error Context**: Errors include user context, breadcrumbs, and custom tags
- **Source Maps**: Production builds include source maps for better debugging

### Usage

```typescript
import { logError, logMessage, setUserContext, addBreadcrumb } from '@/lib/monitoring';

// Log an error
try {
  // Some code that might throw
} catch (error) {
  logError(error, { context: 'additional info' });
}

// Log a message
logMessage('Something important happened', 'info', { userId: '123' });

// Set user context
setUserContext({
  id: user.id,
  email: user.email,
  username: user.username,
});

// Add breadcrumb for debugging
addBreadcrumb('User clicked button', 'user-action', { buttonId: 'submit' });
```

## Performance Monitoring

### Web Vitals

The application automatically tracks Core Web Vitals:

- **CLS** (Cumulative Layout Shift): Visual stability
- **FID** (First Input Delay): Interactivity
- **FCP** (First Contentful Paint): Loading performance
- **LCP** (Largest Contentful Paint): Loading performance
- **TTFB** (Time to First Byte): Server response time

These metrics are automatically sent to Sentry and your analytics service.

### Custom Performance Metrics

Track custom performance metrics:

```typescript
import { trackPerformanceMetric, trackAPIResponseTime } from '@/lib/monitoring';

// Track custom metric
trackPerformanceMetric({
  name: 'custom_operation',
  value: 150,
  unit: 'ms',
  timestamp: Date.now(),
  tags: {
    operation: 'data-processing',
  },
});

// Track API response time (automatically called by API client)
trackAPIResponseTime('/api/stories', 250, 200);
```

### Bundle Size Monitoring

Monitor bundle size in production:

```typescript
import { trackBundleSize } from '@/lib/monitoring';

// Track bundle size (automatically called on app initialization)
trackBundleSize();
```

## User Analytics

### Configuration

Analytics is configured via environment variables:

```env
VITE_ENABLE_ANALYTICS=true
```

### Features

- **Page View Tracking**: Automatic page view tracking on navigation
- **Event Tracking**: Track custom user events
- **User Identification**: Associate events with specific users
- **Privacy Compliance**: Respects user privacy settings

### Usage

```typescript
import { analytics } from '@/lib/monitoring';

// Initialize analytics (automatically called on app start)
analytics.initialize();

// Identify user
analytics.identify(user.id, {
  email: user.email,
  username: user.username,
  plan: 'premium',
});

// Track page view
analytics.trackPageView('/discover');

// Track custom event
analytics.track('story_published', {
  storyId: 'story-123',
  genre: 'fantasy',
  wordCount: 5000,
});

// Reset analytics (on sign out)
analytics.reset();
```

## Bundle Analysis

### Running Bundle Analysis

Analyze your production bundle:

```bash
npm run build:analyze
```

This will:
1. Build the production bundle
2. Analyze all JavaScript and CSS files
3. Display a detailed report with:
   - Individual file sizes
   - Total bundle size
   - Recommendations for optimization

### Output Example

```
📦 Bundle Analysis

═══════════════════════════════════════════════════════════════════════════════

📄 JavaScript Files:

      450.23 KB  ████████████████████████████████████████████████  react-vendor-abc123.js
      320.15 KB  ████████████████████████████████  ui-def456.js
      180.50 KB  ██████████████████  charts-ghi789.js
      ...

  Total JS: 1250.88 KB

🎨 CSS Files:

       85.20 KB  ████████  index-jkl012.css
       ...

  Total CSS: 85.20 KB

📊 Summary:

  Total Bundle Size: 1336.08 KB
  JavaScript: 1250.88 KB (93.6%)
  CSS: 85.20 KB (6.4%)

💡 Recommendations:

  ✅ Bundle size is within acceptable limits
  ℹ️  Many chunk files detected
     This is normal for code-split applications.
     Ensure critical chunks are loaded first.

═══════════════════════════════════════════════════════════════════════════════

✅ Analysis complete!
```

## Lighthouse Audits

### Running Lighthouse Audits

Run Lighthouse audits on key pages:

```bash
# Start the development server
npm run dev

# In another terminal, run Lighthouse
npm run lighthouse
```

### Configuration

Lighthouse is configured in `lighthouse.config.js` with:

- **Performance**: Minimum score of 90
- **Accessibility**: Minimum score of 90
- **Best Practices**: Minimum score of 90
- **SEO**: Minimum score of 90

### Metrics Tracked

- First Contentful Paint (FCP) < 2s
- Largest Contentful Paint (LCP) < 2.5s
- Cumulative Layout Shift (CLS) < 0.1
- Total Blocking Time (TBT) < 300ms

### Reports

Reports are saved to `lighthouse-reports/` directory as HTML files. Open them in your browser to view detailed results.

## Best Practices

### Error Handling

1. **Always log errors**: Use `logError()` for all caught errors
2. **Add context**: Include relevant context with error logs
3. **Use breadcrumbs**: Add breadcrumbs for important user actions
4. **Set user context**: Always set user context after authentication

### Performance

1. **Monitor Web Vitals**: Keep an eye on Core Web Vitals metrics
2. **Track slow operations**: Use `trackPerformanceMetric()` for operations > 100ms
3. **Optimize bundles**: Run bundle analysis regularly
4. **Lazy load**: Use dynamic imports for heavy features

### Analytics

1. **Track key events**: Focus on business-critical events
2. **Respect privacy**: Always check privacy settings before tracking
3. **Use meaningful names**: Use clear, descriptive event names
4. **Include context**: Add relevant properties to events

## Troubleshooting

### Sentry Not Initializing

Check:
- `VITE_ENABLE_SENTRY` is set to `true`
- `VITE_SENTRY_DSN` is configured correctly
- No console errors during initialization

### Web Vitals Not Tracking

Check:
- `VITE_ENABLE_PERFORMANCE_MONITORING` is set to `true`
- Browser supports Performance API
- No ad blockers interfering with tracking

### Analytics Not Working

Check:
- `VITE_ENABLE_ANALYTICS` is set to `true`
- User has not opted out of analytics
- No console errors during tracking

## Production Checklist

Before deploying to production:

- [ ] Configure Sentry DSN
- [ ] Enable performance monitoring
- [ ] Run bundle analysis
- [ ] Run Lighthouse audits
- [ ] Verify all scores > 90
- [ ] Test error tracking
- [ ] Test analytics tracking
- [ ] Review and optimize bundle size
- [ ] Set up monitoring alerts
- [ ] Configure error notifications

## Resources

- [Sentry Documentation](https://docs.sentry.io/)
- [Web Vitals](https://web.dev/vitals/)
- [Lighthouse](https://developers.google.com/web/tools/lighthouse)
- [Performance API](https://developer.mozilla.org/en-US/docs/Web/API/Performance)
