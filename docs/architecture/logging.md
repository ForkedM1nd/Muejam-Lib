# Structured Logging Implementation

This document describes the structured logging implementation for the MueJam Library platform.

## Overview

The platform uses JSON-formatted structured logging with automatic PII redaction and CloudWatch Logs integration. All logs include standard fields for easy searching and filtering.

**Implements Requirements:** 15.1-15.12 from production-readiness spec

## Features

- **JSON Structured Logging** (Requirement 15.1)
- **Standard Fields** (Requirement 15.2): timestamp, log level, service name, request ID, user ID, message
- **API Request Logging** (Requirement 15.3): method, path, status code, response time, user agent
- **Authentication Event Logging** (Requirement 15.4): login, logout, token refresh, failures
- **Moderation Action Logging** (Requirement 15.5): moderator ID, action type, content ID, reason
- **Rate Limiting Event Logging** (Requirement 15.6): IP address, endpoint, limit exceeded
- **CloudWatch Logs Integration** (Requirement 15.7)
- **Log Retention** (Requirement 15.8): 90 days hot, 1 year cold
- **Automatic PII Redaction** (Requirement 15.10): passwords, tokens, credit cards, SSN, emails, phones
- **Log-Based Alerting Support** (Requirement 15.11)
- **Log Volume Monitoring** (Requirement 15.12)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Django Application                        │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         RequestLoggingMiddleware                       │ │
│  │  - Captures all API requests                           │ │
│  │  - Adds request ID and timing                          │ │
│  │  - Logs request/response details                       │ │
│  └────────────────────────────────────────────────────────┘ │
│                           │                                  │
│  ┌────────────────────────▼──────────────────────────────┐ │
│  │         StructuredLogger                              │ │
│  │  - Automatic context injection                        │ │
│  │  - Request ID, user ID, IP address                    │ │
│  │  - Custom fields support                              │ │
│  └────────────────────────────────────────────────────────┘ │
│                           │                                  │
│  ┌────────────────────────▼──────────────────────────────┐ │
│  │         JSONFormatter                                 │ │
│  │  - Formats logs as JSON                               │ │
│  │  - Adds standard fields                               │ │
│  │  - Includes exception info                            │ │
│  └────────────────────────────────────────────────────────┘ │
│                           │                                  │
│  ┌────────────────────────▼──────────────────────────────┐ │
│  │         PIIRedactor                                   │ │
│  │  - Redacts sensitive data                             │ │
│  │  - Email, phone, SSN, credit cards                    │ │
│  │  - Password, token, API key fields                    │ │
│  └────────────────────────────────────────────────────────┘ │
│                           │                                  │
└───────────────────────────┼──────────────────────────────────┘
                            │
            ┌───────────────┴───────────────┐
            │                               │
    ┌───────▼────────┐            ┌────────▼─────────┐
    │  Console/File  │            │  CloudWatch Logs │
    │    Handler     │            │     Handler      │
    └────────────────┘            └──────────────────┘
```

## Configuration

### Environment Variables

```bash
# Logging Configuration
LOG_LEVEL=INFO                          # Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
ENVIRONMENT=production                  # Environment name
SERVICE_NAME=muejam-backend            # Service name for logs

# CloudWatch Logs (Requirement 15.7)
CLOUDWATCH_LOGS_ENABLED=True           # Enable CloudWatch Logs integration
CLOUDWATCH_LOG_GROUP=/muejam/backend   # CloudWatch log group
CLOUDWATCH_LOG_STREAM=production-muejam-backend  # CloudWatch log stream
AWS_REGION=us-east-1                   # AWS region

# Log Retention (Requirement 15.8)
LOG_RETENTION_DAYS_HOT=90              # Hot storage retention (days)
LOG_RETENTION_DAYS_COLD=365            # Cold storage retention (days)

# Log Volume Alerting (Requirement 15.12)
LOG_VOLUME_ALERT_THRESHOLD=10000       # Alert threshold (logs per minute)
LOG_VOLUME_CHECK_INTERVAL=60           # Check interval (seconds)
```

### Django Settings

The logging configuration is automatically loaded in `config/settings.py`:

```python
from infrastructure.logging_config import LoggingConfig

LOGGING = LoggingConfig.get_logging_config()
```

## Usage

### Basic Logging

```python
from infrastructure.logging_config import get_logger

logger = get_logger(__name__)

# Simple log messages
logger.info('User registered successfully')
logger.warning('Cache miss for key: user_profile_123')
logger.error('Failed to send email')

# Log with additional fields
logger.info(
    'Story published',
    story_id='story_123',
    author_id='user_456',
    word_count=5000,
)
```

### API Request Logging (Automatic)

API requests are automatically logged by `RequestLoggingMiddleware`:

```json
{
  "timestamp": "2024-02-17T10:30:45.123Z",
  "level": "INFO",
  "service": "muejam-backend",
  "message": "API request",
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "user_id": "user_123",
  "ip_address": "192.168.1.100",
  "event_type": "api_request",
  "method": "GET",
  "path": "/api/stories/123",
  "status_code": 200,
  "response_time_ms": 45.2,
  "user_agent": "Mozilla/5.0..."
}
```

### Authentication Event Logging

```python
from infrastructure.logging_config import get_logger, log_authentication_event

logger = get_logger(__name__)

# Successful login
log_authentication_event(
    logger=logger,
    event_type='login',
    user_id='user_123',
    success=True,
)

# Failed login
log_authentication_event(
    logger=logger,
    event_type='login',
    user_id='user_123',
    success=False,
    reason='Invalid password',
)

# Token refresh
log_authentication_event(
    logger=logger,
    event_type='token_refresh',
    user_id='user_123',
    success=True,
)
```

### Moderation Action Logging

```python
from infrastructure.logging_config import get_logger, log_moderation_action

logger = get_logger(__name__)

log_moderation_action(
    logger=logger,
    moderator_id='moderator_456',
    action_type='HIDE',
    content_id='story_789',
    reason='Violates content policy',
)
```

### Rate Limiting Event Logging

```python
from infrastructure.logging_config import get_logger, log_rate_limit_event

logger = get_logger(__name__)

log_rate_limit_event(
    logger=logger,
    ip_address='192.168.1.100',
    endpoint='/api/stories',
    limit_type='ip',
    limit_exceeded='100/minute',
)
```

### Context Management

```python
from infrastructure.logging_config import get_logger

logger = get_logger(__name__)

# Set context for all subsequent logs
logger.set_context(
    request_id='req_123',
    user_id='user_456',
    ip_address='192.168.1.100',
)

# All logs will include context
logger.info('Processing request')  # Includes request_id, user_id, ip_address
logger.info('Request completed')   # Includes request_id, user_id, ip_address

# Clear context
logger.clear_context()
```

### Exception Logging

```python
from infrastructure.logging_config import get_logger

logger = get_logger(__name__)

try:
    # Some operation
    result = risky_operation()
except Exception as e:
    logger.exception('Operation failed', operation='risky_operation')
```

## Log Format

### Standard Fields (Requirement 15.2)

Every log entry includes:

- `timestamp`: ISO 8601 timestamp in UTC
- `level`: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `service`: Service name (muejam-backend)
- `message`: Log message
- `logger`: Logger name
- `module`: Python module name
- `function`: Function name
- `line`: Line number

### Optional Fields

- `request_id`: Unique request identifier
- `user_id`: Authenticated user ID
- `ip_address`: Client IP address
- `event_type`: Event type (api_request, authentication, moderation, rate_limit)
- Custom fields via `**kwargs`

### Example Log Entry

```json
{
  "timestamp": "2024-02-17T10:30:45.123456Z",
  "level": "INFO",
  "service": "muejam-backend",
  "message": "Story published successfully",
  "logger": "apps.stories.views",
  "module": "views",
  "function": "create_story",
  "line": 42,
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "user_id": "user_123",
  "ip_address": "192.168.1.100",
  "story_id": "story_456",
  "word_count": 5000,
  "genre": "fantasy"
}
```

## PII Redaction (Requirement 15.10)

The logging system automatically redacts sensitive data:

### Redacted Patterns

- **Email addresses**: `user@example.com` → `[EMAIL_REDACTED]`
- **Phone numbers**: `555-123-4567` → `[PHONE_REDACTED]`
- **SSN**: `123-45-6789` → `[SSN_REDACTED]`
- **Credit cards**: `4111-1111-1111-1111` → `[CARD_REDACTED]`

### Redacted Fields

Fields with these names are automatically redacted:
- `password`, `token`, `secret`, `api_key`, `authorization`
- `credit_card`, `ssn`, `social_security`
- `access_token`, `refresh_token`
- `private_key`, `secret_key`

### Example

```python
logger.info(
    'User updated profile',
    email='user@example.com',  # Redacted
    password='secret123',       # Redacted
    display_name='John Doe',    # Not redacted
)
```

Output:
```json
{
  "message": "User updated profile",
  "email": "[EMAIL_REDACTED]",
  "password": "[REDACTED]",
  "display_name": "John Doe"
}
```

## CloudWatch Logs Integration (Requirement 15.7)

### Setup

1. Install watchtower:
```bash
pip install watchtower
```

2. Configure environment variables:
```bash
CLOUDWATCH_LOGS_ENABLED=True
CLOUDWATCH_LOG_GROUP=/muejam/backend
CLOUDWATCH_LOG_STREAM=production-muejam-backend
AWS_REGION=us-east-1
```

3. Ensure AWS credentials are configured (IAM role or environment variables)

### Log Groups and Streams

- **Log Group**: `/muejam/backend`
- **Log Stream**: `{environment}-{service_name}` (e.g., `production-muejam-backend`)

### Retention Policy

Configure retention in CloudWatch Logs console:
- **Hot storage**: 90 days (Requirement 15.8)
- **Cold storage**: 1 year (archive to S3)

## Log-Based Alerting (Requirement 15.11)

### CloudWatch Alarms

Create CloudWatch metric filters and alarms for critical patterns:

#### Repeated Authentication Failures

```
Filter Pattern: { $.event_type = "authentication" && $.success = false }
Metric: AuthenticationFailures
Alarm: > 10 failures in 5 minutes
```

#### Database Errors

```
Filter Pattern: { $.level = "ERROR" && $.message = "*database*" }
Metric: DatabaseErrors
Alarm: > 5 errors in 5 minutes
```

#### External Service Failures

```
Filter Pattern: { $.level = "ERROR" && $.message = "*external service*" }
Metric: ExternalServiceErrors
Alarm: > 10 errors in 5 minutes
```

### PagerDuty Integration

Configure CloudWatch alarms to trigger PagerDuty incidents for critical issues.

## Log Volume Monitoring (Requirement 15.12)

### Metric Tracking

Track log volume to detect potential attacks or system issues:

```python
from infrastructure.logging_config import LoggingConfig

# Alert threshold
threshold = LoggingConfig.LOG_VOLUME_ALERT_THRESHOLD  # 10,000 logs/minute

# Check interval
interval = LoggingConfig.LOG_VOLUME_CHECK_INTERVAL  # 60 seconds
```

### CloudWatch Metric

Create a CloudWatch metric for log volume:

```
Metric Name: LogVolume
Namespace: MueJam/Backend
Unit: Count
Period: 1 minute
```

### Alert Configuration

```
Alarm Name: HighLogVolume
Condition: LogVolume > 10,000 for 2 consecutive periods
Action: Send SNS notification → PagerDuty
```

## Log Search and Filtering (Requirement 15.9)

### CloudWatch Logs Insights

Query logs using CloudWatch Logs Insights:

```sql
# Find all errors for a specific user
fields @timestamp, message, level, user_id, request_id
| filter user_id = "user_123" and level = "ERROR"
| sort @timestamp desc
| limit 100

# Find slow API requests
fields @timestamp, path, response_time_ms, user_id
| filter event_type = "api_request" and response_time_ms > 1000
| sort response_time_ms desc
| limit 50

# Find authentication failures
fields @timestamp, user_id, reason
| filter event_type = "authentication" and success = false
| stats count() by user_id
| sort count desc

# Find rate limiting events
fields @timestamp, ip_address, endpoint, limit_exceeded
| filter event_type = "rate_limit"
| stats count() by ip_address
| sort count desc
```

### Search by Standard Fields

- **Time range**: Filter by `@timestamp`
- **Log level**: Filter by `level`
- **Service**: Filter by `service`
- **User**: Filter by `user_id`
- **Request**: Filter by `request_id`
- **Custom fields**: Filter by any custom field

## Testing

### Unit Tests

```python
import json
from infrastructure.logging_config import JSONFormatter, PIIRedactor, get_logger

def test_json_formatter():
    """Test JSON log formatting."""
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name='test',
        level=logging.INFO,
        pathname='test.py',
        lineno=10,
        msg='Test message',
        args=(),
        exc_info=None,
    )
    
    output = formatter.format(record)
    log_entry = json.loads(output)
    
    assert log_entry['level'] == 'INFO'
    assert log_entry['message'] == 'Test message'
    assert 'timestamp' in log_entry

def test_pii_redaction():
    """Test PII redaction."""
    text = 'Contact me at user@example.com or 555-123-4567'
    redacted = PIIRedactor.redact_text(text)
    
    assert '[EMAIL_REDACTED]' in redacted
    assert '[PHONE_REDACTED]' in redacted
    assert 'user@example.com' not in redacted
    assert '555-123-4567' not in redacted

def test_structured_logger():
    """Test structured logger with context."""
    logger = get_logger('test')
    
    logger.set_context(request_id='req_123', user_id='user_456')
    logger.info('Test message', custom_field='value')
    
    # Verify log entry includes context
    # (Check log output or mock logger)
```

## Troubleshooting

### Logs Not Appearing in CloudWatch

1. Check AWS credentials are configured
2. Verify IAM permissions for CloudWatch Logs
3. Check `CLOUDWATCH_LOGS_ENABLED=True`
4. Verify log group and stream names
5. Check watchtower is installed: `pip install watchtower`

### PII Not Being Redacted

1. Check PIIRedactor patterns match your data format
2. Verify JSONFormatter is using PIIRedactor
3. Add custom patterns if needed

### High Log Volume

1. Increase log level to WARNING or ERROR
2. Reduce verbose logging in high-traffic endpoints
3. Implement sampling for high-volume logs
4. Check for log loops or excessive logging

## Best Practices

1. **Use structured logging**: Always use `get_logger()` instead of `logging.getLogger()`
2. **Add context**: Use `logger.set_context()` for request-scoped fields
3. **Use appropriate log levels**:
   - DEBUG: Detailed diagnostic information
   - INFO: General informational messages
   - WARNING: Warning messages for potentially harmful situations
   - ERROR: Error messages for failures
   - CRITICAL: Critical messages for severe failures
4. **Include relevant fields**: Add custom fields for better searchability
5. **Don't log sensitive data**: PII redaction is automatic, but avoid logging sensitive data when possible
6. **Use log helpers**: Use `log_api_request()`, `log_authentication_event()`, etc. for consistency
7. **Monitor log volume**: Set up alerts for unusual log volume spikes

## References

- [Production readiness review](../operations/PRODUCTION_READINESS_REVIEW.md)
- [CloudWatch Logs Documentation](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/)
- [Python Logging Documentation](https://docs.python.org/3/library/logging.html)
- [Watchtower Documentation](https://github.com/kislyuk/watchtower)
