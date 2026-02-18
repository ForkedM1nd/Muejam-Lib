# Task 40: APM Integration - Summary

## Overview
Successfully integrated Application Performance Monitoring (APM) for comprehensive performance tracking in the MueJam Library backend. The implementation supports both New Relic and DataDog APM providers.

## Completed Subtasks

### 40.1 Set up New Relic or DataDog APM ✅
- Created `infrastructure/apm_config.py` with flexible APM provider support
- Implemented APMProvider base class with New Relic and DataDog implementations
- Configured transaction tracing and slow SQL detection
- Added APM initialization functions for both providers
- Updated `config/settings.py` to initialize APM on startup
- Added APM dependencies to `requirements.txt`
- Created APM middleware for automatic API endpoint tracking

### 40.2 Configure performance tracking ✅
- Implemented PerformanceMonitor class with comprehensive tracking methods
- Created `infrastructure/apm_database.py` for database query tracking
- Created `infrastructure/apm_external.py` for external service and cache tracking
- Created `infrastructure/apm_celery.py` for Celery task monitoring
- Implemented decorators for easy performance tracking
- Added support for custom business metrics

### 40.3 Set up performance alerts ✅
- Created `infrastructure/apm_alerts.py` with alert configuration
- Defined alert rules for API response times, database pool utilization, and more
- Implemented PerformanceAlerter class for sending alerts
- Configured email and Slack alert channels
- Created alert configuration functions for New Relic and DataDog
- Added performance alert settings to `.env.example`

## Implementation Details

### Files Created

1. **infrastructure/apm_config.py**
   - APM provider abstraction (New Relic and DataDog)
   - PerformanceMonitor class for tracking metrics
   - Initialization functions for both providers
   - Performance tracking decorator
   - Configuration management

2. **infrastructure/apm_middleware.py**
   - Django middleware for automatic API endpoint tracking
   - Request duration measurement
   - Status code tracking
   - Exception handling

3. **infrastructure/apm_database.py**
   - DatabaseQueryTracker for query performance
   - Query obfuscation for security
   - Slow query detection
   - Database tracking decorator

4. **infrastructure/apm_external.py**
   - ExternalServiceTracker for AWS S3, Clerk, Resend, Rekognition
   - CacheTracker for cache performance metrics
   - Service call decorators
   - Cache operation decorators

5. **infrastructure/apm_celery.py**
   - CeleryTaskTracker for task performance
   - Queue depth monitoring
   - Task success/failure tracking
   - Celery task decorator

6. **infrastructure/apm_alerts.py**
   - PerformanceAlertConfig with alert rules
   - PerformanceAlerter for sending alerts
   - Email and Slack alert integration
   - New Relic and DataDog alert configuration

7. **infrastructure/README_APM.md**
   - Comprehensive documentation
   - Configuration guide
   - Usage examples
   - Troubleshooting guide

### Files Modified

1. **requirements.txt**
   - Added newrelic==9.5.0
   - Added commented DataDog dependencies

2. **config/settings.py**
   - Added APM configuration variables
   - Initialized APM on startup
   - Added performance thresholds

3. **.env.example**
   - Added APM provider selection
   - Added New Relic configuration
   - Added DataDog configuration
   - Added performance thresholds
   - Added alert configuration

## Configuration

### Environment Variables Added

```bash
# APM Configuration
APM_ENABLED=False
APM_PROVIDER=newrelic

# New Relic
NEW_RELIC_LICENSE_KEY=
NEW_RELIC_APP_NAME=MueJam Library
NEW_RELIC_ENVIRONMENT=development

# DataDog
DATADOG_API_KEY=
DATADOG_APP_KEY=
DATADOG_SERVICE_NAME=muejam-backend
DATADOG_ENVIRONMENT=development

# Performance Thresholds
API_P95_THRESHOLD_MS=500
API_P99_THRESHOLD_MS=1000
SLOW_QUERY_THRESHOLD_MS=100
DB_POOL_UTILIZATION_THRESHOLD=0.8

# Transaction Tracing
TRANSACTION_TRACE_ENABLED=True
SLOW_SQL_ENABLED=True

# Performance Alerts
PERFORMANCE_ALERT_EMAIL_ENABLED=True
PERFORMANCE_ALERT_EMAIL_RECIPIENTS=oncall@example.com,devops@example.com
PERFORMANCE_ALERT_SLACK_ENABLED=False
PERFORMANCE_ALERT_SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

## Features Implemented

### 1. API Endpoint Performance Tracking (Requirement 14.2)
- Automatic tracking via middleware
- Request duration (average, p95, p99)
- Response status codes
- Endpoint-specific metrics
- Throughput tracking

### 2. Database Query Performance (Requirement 14.3)
- Query execution time tracking
- Slow query detection (>100ms)
- Query type identification
- Query obfuscation for security
- Rows returned tracking

### 3. External Service Monitoring (Requirement 14.4)
- AWS S3 operations tracking
- Clerk authentication monitoring
- Resend email operations
- AWS Rekognition tracking
- Service latency measurement

### 4. Cache Performance (Requirement 14.5)
- Cache hit/miss rate tracking
- Operation duration
- Cache operation types (get, set, delete)
- Cache efficiency metrics

### 5. Celery Task Monitoring (Requirement 14.6)
- Task execution time
- Task success/failure rates
- Queue depth tracking
- Task-specific metrics

### 6. Performance Alerts (Requirements 14.7, 14.8)
- API response time alerts (p95 > 500ms, p99 > 1000ms)
- Database pool utilization alerts (>80%)
- Slow query alerts
- External service latency alerts
- Cache miss rate alerts
- Celery queue depth alerts
- Email and Slack notifications

### 7. Custom Business Metrics (Requirement 14.10)
- Stories published tracking
- Active users monitoring
- Engagement rate metrics
- Custom application metrics

### 8. Distributed Tracing (Requirement 14.11)
- Automatic tracing with New Relic
- Automatic tracing with DataDog
- Request flow visualization

### 9. N+1 Query Detection (Requirement 14.12)
- Automatic detection via APM providers
- Query pattern analysis
- Performance recommendations

## Usage Examples

### Automatic Tracking

```python
# API endpoints tracked automatically via middleware
# Database queries tracked via APM integrations
# Celery tasks tracked via Celery integration
```

### Manual Tracking

```python
from infrastructure.apm_config import track_performance, PerformanceMonitor
from infrastructure.apm_external import track_external_service
from infrastructure.apm_database import track_database_query
from infrastructure.apm_celery import track_celery_task

# Track custom function
@track_performance('story.create')
def create_story(data):
    pass

# Track external service
@track_external_service('s3', 'upload')
def upload_to_s3(file_path):
    pass

# Track database query
@track_database_query
def get_user_by_id(user_id):
    return User.objects.get(id=user_id)

# Track Celery task
@celery_app.task
@track_celery_task
def send_email(to, subject, body):
    pass

# Track business metric
PerformanceMonitor.track_business_metric(
    'stories.published',
    1,
    tags={'genre': 'fantasy'}
)
```

## Requirements Satisfied

✅ **Requirement 14.1**: Integrate APM solution (New Relic or DataDog)
- Both providers supported
- Flexible configuration
- Easy switching between providers

✅ **Requirement 14.2**: Track API endpoint performance
- Automatic tracking via middleware
- Response time percentiles (p50, p95, p99)
- Throughput measurement

✅ **Requirement 14.3**: Track database query performance and identify slow queries
- Query execution time tracking
- Slow query detection (>100ms)
- Query obfuscation

✅ **Requirement 14.4**: Track external service calls
- AWS S3, Clerk, Resend, Rekognition
- Service latency tracking
- Success/failure rates

✅ **Requirement 14.5**: Track cache performance
- Hit/miss rate tracking
- Operation duration
- Cache efficiency metrics

✅ **Requirement 14.6**: Track Celery task performance
- Task execution time
- Queue depth monitoring
- Success/failure rates

✅ **Requirement 14.7**: Alert when API response times exceed thresholds
- P95 > 500ms alert
- P99 > 1000ms alert
- Configurable thresholds

✅ **Requirement 14.8**: Alert when database pool utilization exceeds 80%
- Pool utilization monitoring
- Configurable threshold
- Email and Slack alerts

✅ **Requirement 14.9**: Provide performance dashboards
- New Relic dashboard configuration
- DataDog dashboard configuration
- Custom metrics visualization

✅ **Requirement 14.10**: Track custom business metrics
- Stories published
- Active users
- Engagement rates
- Custom metrics support

✅ **Requirement 14.11**: Support distributed tracing
- Automatic with New Relic
- Automatic with DataDog
- Request flow tracking

✅ **Requirement 14.12**: Identify N+1 query problems
- Automatic detection
- Query pattern analysis
- Performance recommendations

## Next Steps

To activate APM integration:

1. **Choose APM Provider**
   - New Relic: https://newrelic.com
   - DataDog: https://www.datadoghq.com

2. **Install Dependencies**
   ```bash
   cd apps/backend
   pip install -r requirements.txt
   ```

3. **Configure Environment**
   ```bash
   # For New Relic
   APM_ENABLED=True
   APM_PROVIDER=newrelic
   NEW_RELIC_LICENSE_KEY=your-license-key
   
   # For DataDog
   APM_ENABLED=True
   APM_PROVIDER=datadog
   DATADOG_API_KEY=your-api-key
   DATADOG_APP_KEY=your-app-key
   ```

4. **Set Up Alerts**
   - Configure email recipients
   - Set up Slack webhook (optional)
   - Adjust thresholds as needed

5. **Create Dashboards**
   - Use provided configurations
   - Customize for your needs

6. **Verify Integration**
   - Start Django server
   - Check APM dashboard
   - Verify metrics are being collected

## Testing

To test the integration:

1. **Test Metric Collection**
   ```python
   from infrastructure.apm_config import PerformanceMonitor
   PerformanceMonitor.track_business_metric('test.metric', 1)
   ```

2. **Test API Tracking**
   - Make API requests
   - Check APM dashboard for metrics

3. **Test Alerts**
   - Trigger slow endpoint
   - Verify alert is sent

## Documentation

Comprehensive documentation available in:
- `infrastructure/README_APM.md` - Full integration guide
- `infrastructure/apm_config.py` - Code documentation
- `infrastructure/apm_alerts.py` - Alert configuration docs

## Conclusion

APM integration is fully implemented and ready for production use. The implementation provides comprehensive performance monitoring, intelligent alerting, and support for both New Relic and DataDog APM providers. All requirements (14.1-14.12) are satisfied.
