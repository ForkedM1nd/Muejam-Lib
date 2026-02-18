# Sentry Error Tracking Integration

This document describes the Sentry error tracking integration for the MueJam Library platform.

## Overview

Sentry is integrated to provide comprehensive error tracking and monitoring for the Django backend. The integration captures unhandled exceptions, performance metrics, and provides real-time alerts for critical errors.

**Implements Requirements:**
- 13.1: Integrate Sentry for error tracking
- 13.2: Send error details including stack trace, user context, and request data
- 13.4: Group similar errors and track error frequency
- 13.5: Send email alerts for critical errors
- 13.6: Redact sensitive data from error reports
- 13.12: Integrate with Slack for real-time notifications

## Features

### 1. Error Tracking
- Automatic capture of unhandled exceptions
- Stack traces with source code context
- Request data (URL, method, headers, body)
- User context (user ID, email, username)
- Breadcrumbs showing user actions leading to errors

### 2. Performance Monitoring
- Transaction tracing for API endpoints
- Database query performance tracking
- External service call monitoring
- Celery task performance tracking
- Redis operation monitoring

### 3. Sensitive Data Scrubbing
All sensitive data is automatically removed from error reports:
- Authorization headers
- API keys
- Passwords and tokens
- Session cookies
- Credit card numbers
- Social security numbers
- Email addresses and IP addresses (in user context)

### 4. Error Grouping
Errors are automatically grouped by:
- Database errors (by query type)
- Authentication errors (by function)
- External service errors (by service)
- Rate limiting errors (by endpoint)
- Validation errors (by function)

### 5. Alerting
Alerts are triggered for:
- Critical errors (10+ occurrences in 1 minute)
- High error rates (>1% of requests)
- Database connection failures
- External service failures

Alerts can be sent via:
- Email to on-call engineers
- Slack notifications to engineering channel

## Configuration

### Environment Variables

```bash
# Required
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id

# Optional
SENTRY_ENVIRONMENT=production  # development, staging, production
SENTRY_TRACES_SAMPLE_RATE=0.1  # 0.0 to 1.0 (10% of transactions)
SENTRY_PROFILES_SAMPLE_RATE=0.1  # 0.0 to 1.0 (10% of transactions)
APP_VERSION=1.0.0  # Application version for release tracking

# Alert Configuration
SENTRY_CRITICAL_ERROR_THRESHOLD=10  # Number of errors to trigger alert
SENTRY_ERROR_RATE_THRESHOLD=0.01  # Error rate threshold (1%)
SENTRY_EMAIL_ALERTS_ENABLED=True
SENTRY_ALERT_EMAIL_RECIPIENTS=oncall@example.com,engineering@example.com
SENTRY_SLACK_ALERTS_ENABLED=False
SENTRY_SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
SENTRY_SLACK_CHANNEL=#engineering-alerts
```

### Getting Started

1. **Create a Sentry Project**
   - Sign up at https://sentry.io
   - Create a new project for Django
   - Copy the DSN from project settings

2. **Configure Environment Variables**
   - Add `SENTRY_DSN` to your `.env` file
   - Set `SENTRY_ENVIRONMENT` to match your deployment environment
   - Configure alert settings as needed

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify Integration**
   - Start the Django server
   - Check Sentry dashboard for initialization event
   - Trigger a test error to verify capture

## Usage

### Automatic Error Capture

Most errors are captured automatically by Sentry's Django integration:

```python
# This error will be automatically captured
def my_view(request):
    raise Exception("Something went wrong!")
```

### Manual Error Capture

Use the `ErrorTracker` class for manual error capture with custom context:

```python
from infrastructure.sentry_config import ErrorTracker

try:
    # Some operation
    process_payment(user_id, amount)
except PaymentError as e:
    # Capture with custom context
    ErrorTracker.capture_exception(
        e,
        context={
            'payment': {
                'user_id': user_id,
                'amount': amount,
                'currency': 'USD',
            }
        },
        level='error'
    )
```

### Capture Messages

Capture informational messages or warnings:

```python
from infrastructure.sentry_config import ErrorTracker

# Log a warning
ErrorTracker.capture_message(
    'User attempted to access restricted content',
    level='warning',
    context={
        'user': {'id': user_id},
        'content': {'id': content_id},
    }
)
```

### Set User Context

Set user context for better error tracking:

```python
from infrastructure.sentry_config import ErrorTracker

# Set user context
ErrorTracker.set_user(
    user_id=user.id,
    email=user.email,
    username=user.username
)
```

### Set Tags

Add tags for filtering errors in Sentry:

```python
from infrastructure.sentry_config import ErrorTracker

# Set tags
ErrorTracker.set_tag('payment_provider', 'stripe')
ErrorTracker.set_tag('feature', 'checkout')
```

### Set Custom Context

Add custom context for specific operations:

```python
from infrastructure.sentry_config import ErrorTracker

# Set custom context
ErrorTracker.set_context('database', {
    'query': 'SELECT * FROM users',
    'duration_ms': 150,
    'rows_returned': 100,
})
```

## Alert Configuration

### Email Alerts

Email alerts are sent to on-call engineers when:
- 10+ errors occur within 1 minute
- Error rate exceeds 1% of requests
- Critical error patterns are detected

Configure recipients in `.env`:
```bash
SENTRY_EMAIL_ALERTS_ENABLED=True
SENTRY_ALERT_EMAIL_RECIPIENTS=oncall@example.com,engineering@example.com
```

### Slack Alerts

Slack notifications provide real-time alerts to the engineering team:

1. **Create Slack Webhook**
   - Go to https://api.slack.com/apps
   - Create a new app or select existing
   - Enable Incoming Webhooks
   - Add webhook to your channel
   - Copy webhook URL

2. **Configure in .env**
   ```bash
   SENTRY_SLACK_ALERTS_ENABLED=True
   SENTRY_SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
   SENTRY_SLACK_CHANNEL=#engineering-alerts
   ```

3. **Test Slack Integration**
   ```python
   from infrastructure.sentry_alerts import SlackNotifier
   
   notifier = SlackNotifier()
   notifier.send_error_notification(
       error_message='Test error notification',
       error_type='TestError',
       error_count=1,
       sentry_url='https://sentry.io/issues/123456'
   )
   ```

## Error Grouping

Sentry automatically groups similar errors together. Custom grouping rules are configured for:

### Database Errors
Grouped by query type and transaction:
- Connection errors
- Query timeouts
- Integrity violations

### Authentication Errors
Grouped by function:
- Invalid tokens
- Permission denied
- Authentication failed

### External Service Errors
Grouped by service:
- AWS S3 errors
- Clerk authentication errors
- Resend email errors

### Rate Limiting Errors
Grouped by endpoint:
- API rate limits
- User rate limits
- IP rate limits

## Performance Monitoring

Sentry tracks performance metrics for:

### API Endpoints
- Response times (average, p95, p99)
- Throughput (requests per second)
- Error rates

### Database Queries
- Query execution time
- Slow queries (>100ms)
- N+1 query detection

### External Services
- AWS S3 upload/download times
- Clerk authentication latency
- Resend email delivery times

### Celery Tasks
- Task execution time
- Queue depth
- Task failure rates

## Best Practices

### 1. Don't Over-Capture
Only capture errors that require attention. Use appropriate log levels:
- `error`: Requires immediate attention
- `warning`: Should be investigated
- `info`: Informational only

### 2. Add Context
Always add relevant context to errors:
```python
ErrorTracker.capture_exception(
    exception,
    context={
        'user': {'id': user_id},
        'operation': 'payment_processing',
        'metadata': {'amount': amount, 'currency': 'USD'},
    }
)
```

### 3. Use Tags for Filtering
Add tags to make errors easier to filter:
```python
ErrorTracker.set_tag('feature', 'checkout')
ErrorTracker.set_tag('payment_provider', 'stripe')
```

### 4. Monitor Performance
Review performance metrics regularly:
- Identify slow endpoints
- Optimize database queries
- Reduce external service latency

### 5. Review Alerts
Regularly review and tune alert thresholds:
- Reduce false positives
- Ensure critical errors are caught
- Adjust sample rates as needed

## Troubleshooting

### Errors Not Appearing in Sentry

1. **Check DSN Configuration**
   ```bash
   echo $SENTRY_DSN
   ```

2. **Verify Sentry Initialization**
   ```python
   import sentry_sdk
   print(sentry_sdk.Hub.current.client)
   ```

3. **Check Error Filtering**
   - Ensure error is not in `ignore_errors` list
   - Check if error matches ignored patterns

### High Error Volume

1. **Review Error Grouping**
   - Check if errors are properly grouped
   - Adjust grouping rules if needed

2. **Adjust Sample Rates**
   - Reduce `SENTRY_TRACES_SAMPLE_RATE`
   - Reduce `SENTRY_PROFILES_SAMPLE_RATE`

3. **Filter Noisy Errors**
   - Add to `ignore_errors` in `sentry_config.py`
   - Adjust alert thresholds

### Slack Notifications Not Working

1. **Verify Webhook URL**
   ```bash
   curl -X POST -H 'Content-type: application/json' \
     --data '{"text":"Test message"}' \
     $SENTRY_SLACK_WEBHOOK_URL
   ```

2. **Check Configuration**
   ```bash
   echo $SENTRY_SLACK_ALERTS_ENABLED
   echo $SENTRY_SLACK_WEBHOOK_URL
   ```

3. **Review Logs**
   - Check for Slack notification errors in logs
   - Verify network connectivity

## Resources

- [Sentry Documentation](https://docs.sentry.io/)
- [Django Integration](https://docs.sentry.io/platforms/python/guides/django/)
- [Performance Monitoring](https://docs.sentry.io/product/performance/)
- [Alert Rules](https://docs.sentry.io/product/alerts/)
- [Slack Integration](https://docs.sentry.io/product/integrations/notification-incidents/slack/)
