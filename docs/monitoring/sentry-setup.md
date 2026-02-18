# Sentry Error Tracking Setup

## Overview

Sentry is configured for comprehensive error tracking and monitoring across the MueJam platform. This document covers setup, verification, and usage.

## Configuration

### Environment Variables

Required:
```bash
SENTRY_DSN=https://your-key@sentry.io/your-project-id
```

Optional:
```bash
SENTRY_ENVIRONMENT=production  # or staging, development
SENTRY_TRACES_SAMPLE_RATE=0.1  # 10% of transactions (0.0 to 1.0)
SENTRY_PROFILES_SAMPLE_RATE=0.1  # 10% of transactions (0.0 to 1.0)
APP_VERSION=1.0.0  # For release tracking

# Alert Configuration
SENTRY_CRITICAL_ERROR_THRESHOLD=10
SENTRY_ERROR_RATE_THRESHOLD=0.01  # 1%
SENTRY_EMAIL_ALERTS_ENABLED=True
SENTRY_ALERT_EMAIL_RECIPIENTS=team@example.com,oncall@example.com
SENTRY_SLACK_ALERTS_ENABLED=True
SENTRY_SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
SENTRY_SLACK_CHANNEL=#engineering-alerts
```

### Getting Your Sentry DSN

1. Log in to [Sentry.io](https://sentry.io)
2. Create a new project or select existing project
3. Go to Settings → Projects → [Your Project] → Client Keys (DSN)
4. Copy the DSN and set it as `SENTRY_DSN` environment variable

## Features

### 1. Error Tracking

Automatically captures:
- Unhandled exceptions
- Django errors
- Celery task failures
- Redis connection errors
- HTTP errors (4xx, 5xx)

### 2. Performance Monitoring

Tracks:
- Request/response times
- Database query performance
- External API calls
- Celery task execution time

### 3. Sensitive Data Scrubbing

Automatically removes:
- Authorization headers
- API keys and tokens
- Passwords
- Session cookies
- Credit card numbers
- SSN
- Email addresses (from user context)
- IP addresses (from user context)

### 4. Error Grouping

Errors are grouped by:
- Database errors (by query type)
- Authentication errors (by function)
- External service errors (by service)
- Rate limiting errors (by endpoint)
- Validation errors (by function)

### 5. Integrations

- **Django**: Tracks middleware, signals, and request/response cycle
- **Celery**: Monitors background tasks and beat schedules
- **Redis**: Tracks cache operations and connection issues

## Verification

### 1. Run Unit Tests

```bash
cd apps/backend
python manage.py test tests.test_sentry_integration
```

Expected output:
```
test_sentry_dsn_configured ... ok
test_sentry_initialization ... ok
test_sensitive_data_scrubbing ... ok
test_breadcrumb_scrubbing ... ok
test_ignored_errors ... ok
test_error_tracker_capture_exception ... ok
test_sentry_integrations_configured ... ok
test_alert_thresholds ... ok
test_email_alert_configuration ... ok
test_slack_integration_configuration ... ok
test_error_grouping_rules ... ok

----------------------------------------------------------------------
Ran 11 tests in 0.XXXs

OK
```

### 2. Send Test Error

```bash
python manage.py shell
```

```python
import sentry_sdk

# Send test exception
try:
    raise Exception("Test error from manual verification")
except Exception as e:
    event_id = sentry_sdk.capture_exception(e)
    print(f"Event ID: {event_id}")

# Send test message
event_id = sentry_sdk.capture_message("Test message from manual verification", level='info')
print(f"Message Event ID: {event_id}")
```

### 3. Check Sentry Dashboard

1. Go to your Sentry project dashboard
2. Navigate to Issues
3. Verify you see the test error and message
4. Check that sensitive data is redacted

### 4. Verify Integration Status

```bash
python apps/backend/scripts/verify_sentry.py
```

## Usage

### Capturing Exceptions

```python
from infrastructure.sentry_config import ErrorTracker

try:
    # Your code
    risky_operation()
except Exception as e:
    # Capture with custom context
    ErrorTracker.capture_exception(
        e,
        context={
            'user_id': user.id,
            'action': 'create_story',
            'story_id': story.id
        },
        level='error'
    )
```

### Capturing Messages

```python
import sentry_sdk

# Info message
sentry_sdk.capture_message("User completed onboarding", level='info')

# Warning message
sentry_sdk.capture_message("Cache miss rate high", level='warning')

# Error message
sentry_sdk.capture_message("External API degraded", level='error')
```

### Adding Custom Context

```python
import sentry_sdk

# Set user context
sentry_sdk.set_user({
    "id": user.id,
    "username": user.handle,
    # Don't include email or IP - they're scrubbed
})

# Set custom tags
sentry_sdk.set_tag("feature", "story_creation")
sentry_sdk.set_tag("plan", "premium")

# Set custom context
sentry_sdk.set_context("story", {
    "id": story.id,
    "genre": story.genre,
    "word_count": story.word_count
})
```

### Adding Breadcrumbs

```python
import sentry_sdk

# Add breadcrumb for debugging
sentry_sdk.add_breadcrumb(
    category='user_action',
    message='User clicked publish button',
    level='info',
    data={
        'story_id': story.id,
        'draft_status': story.is_draft
    }
)
```

## Alert Configuration

### Email Alerts

Configured in Sentry dashboard:
1. Go to Settings → Alerts
2. Create new alert rule
3. Set conditions (e.g., "When error count > 10 in 5 minutes")
4. Add email action with recipients from `SENTRY_ALERT_EMAIL_RECIPIENTS`

### Slack Alerts

1. Create Slack webhook:
   - Go to Slack → Apps → Incoming Webhooks
   - Add to your workspace
   - Copy webhook URL

2. Configure in Sentry:
   - Go to Settings → Integrations → Slack
   - Add webhook URL
   - Configure alert rules to post to Slack

3. Set environment variables:
   ```bash
   SENTRY_SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
   SENTRY_SLACK_ALERTS_ENABLED=True
   SENTRY_SLACK_CHANNEL=#engineering-alerts
   ```

### Alert Rules

Recommended alert rules:

1. **Critical Errors**:
   - Condition: Error count > 10 in 5 minutes
   - Action: Email + Slack
   - Priority: High

2. **Error Rate Spike**:
   - Condition: Error rate > 1% in 10 minutes
   - Action: Email + Slack
   - Priority: High

3. **New Error Type**:
   - Condition: First seen error
   - Action: Slack
   - Priority: Medium

4. **Performance Degradation**:
   - Condition: P95 latency > 1000ms
   - Action: Slack
   - Priority: Medium

## Error Grouping

Errors are automatically grouped using fingerprints:

### Database Errors
```python
fingerprint: ['{{ default }}', 'database', '{{ transaction }}']
```
Groups by database operation type.

### Authentication Errors
```python
fingerprint: ['{{ default }}', 'auth', '{{ function }}']
```
Groups by authentication function.

### External Service Errors
```python
fingerprint: ['{{ default }}', 'external', '{{ function }}']
```
Groups by external service call.

### Custom Grouping

```python
import sentry_sdk

with sentry_sdk.configure_scope() as scope:
    scope.fingerprint = ['custom-group', 'payment-processing', 'stripe']
    # Your code that might error
```

## Ignored Errors

These errors are not sent to Sentry (too noisy):
- `django.http.Http404` - Not found errors
- `rest_framework.exceptions.NotFound` - API not found
- `rest_framework.exceptions.PermissionDenied` - Permission denied

To ignore additional errors, update `ignore_errors` in `sentry_config.py`.

## Performance Monitoring

### Transaction Sampling

- Default: 10% of transactions are sampled
- Adjust via `SENTRY_TRACES_SAMPLE_RATE`
- Production: 0.1 (10%)
- Staging: 0.5 (50%)
- Development: 1.0 (100%)

### Custom Transactions

```python
import sentry_sdk

with sentry_sdk.start_transaction(op="task", name="process_story"):
    # Your code
    process_story(story_id)
```

### Spans for Detailed Timing

```python
import sentry_sdk

with sentry_sdk.start_transaction(op="task", name="create_story"):
    with sentry_sdk.start_span(op="db", description="Save story"):
        story.save()
    
    with sentry_sdk.start_span(op="http", description="Notify users"):
        send_notifications(story)
```

## Troubleshooting

### Sentry Not Capturing Errors

1. Check `SENTRY_DSN` is set:
   ```bash
   echo $SENTRY_DSN
   ```

2. Verify initialization:
   ```python
   from django.conf import settings
   print(settings.SENTRY_DSN)
   ```

3. Check logs for Sentry errors:
   ```bash
   tail -f apps/backend/logs/muejam.log | grep -i sentry
   ```

4. Test with manual capture:
   ```python
   import sentry_sdk
   sentry_sdk.capture_message("Test", level='info')
   ```

### Sensitive Data Not Scrubbed

1. Verify `scrub_sensitive_data` is configured in `before_send`
2. Check `send_default_pii=False` in Sentry init
3. Add custom scrubbing rules in `sentry_config.py`

### Too Many Errors

1. Increase `ignore_errors` list
2. Adjust error grouping fingerprints
3. Add rate limiting to Sentry project settings
4. Filter by environment (only production)

### Performance Impact

Sentry has minimal performance impact:
- Error capture: ~1-5ms overhead
- Transaction sampling: Configurable (default 10%)
- Async sending: Errors sent in background

To reduce impact:
- Lower `SENTRY_TRACES_SAMPLE_RATE`
- Lower `SENTRY_PROFILES_SAMPLE_RATE`
- Increase `ignore_errors` list

## Best Practices

1. **Always scrub sensitive data** - Never send passwords, tokens, or PII
2. **Use appropriate log levels** - Info for informational, Error for actual errors
3. **Add context** - Include user ID, action, relevant IDs
4. **Group errors properly** - Use fingerprints for better grouping
5. **Set up alerts** - Don't rely on checking dashboard manually
6. **Monitor error trends** - Look for patterns and spikes
7. **Fix errors promptly** - Don't let error count grow
8. **Use releases** - Track errors by version
9. **Test in staging** - Verify Sentry works before production
10. **Document custom errors** - Add comments for custom error handling

## Monitoring Checklist

- [ ] SENTRY_DSN configured
- [ ] Test error sent and received
- [ ] Sensitive data scrubbing verified
- [ ] Email alerts configured
- [ ] Slack alerts configured
- [ ] Error grouping rules tested
- [ ] Performance monitoring enabled
- [ ] Alert thresholds set
- [ ] Team trained on Sentry usage
- [ ] Runbook created for common errors

## Resources

- [Sentry Documentation](https://docs.sentry.io/)
- [Django Integration](https://docs.sentry.io/platforms/python/guides/django/)
- [Celery Integration](https://docs.sentry.io/platforms/python/guides/celery/)
- [Performance Monitoring](https://docs.sentry.io/product/performance/)
- [Alert Rules](https://docs.sentry.io/product/alerts/)

## Support

For issues with Sentry integration:
1. Check this documentation
2. Review Sentry logs
3. Test with manual error capture
4. Contact DevOps team
5. Check Sentry status page: https://status.sentry.io/
