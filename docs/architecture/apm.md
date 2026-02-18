# Application Performance Monitoring (APM) Integration

This document describes the APM integration for the MueJam Library platform.

## Overview

APM is integrated to provide comprehensive performance monitoring for the Django backend. The integration supports both New Relic and DataDog APM providers, allowing you to choose the solution that best fits your needs.

**Implements Requirements:**
- 14.1: Integrate APM solution (New Relic or DataDog)
- 14.2: Track API endpoint performance
- 14.3: Track database query performance and identify slow queries
- 14.4: Track external service calls (AWS S3, Clerk, Resend)
- 14.5: Track cache performance
- 14.6: Track Celery task performance
- 14.7: Alert when API response times exceed thresholds
- 14.8: Alert when database pool utilization exceeds 80%
- 14.10: Track custom business metrics
- 14.11: Support distributed tracing
- 14.12: Identify N+1 query problems

## Features

### 1. API Endpoint Performance Tracking
- Request duration (average, p95, p99)
- Response status codes
- Throughput (requests per second)
- Endpoint-specific metrics

### 2. Database Query Performance
- Query execution time
- Slow query detection (>100ms)
- Query type tracking (SELECT, INSERT, UPDATE, DELETE)
- N+1 query detection

### 3. External Service Monitoring
- AWS S3 operations (upload, download, delete)
- Clerk authentication calls
- Resend email operations
- AWS Rekognition image analysis
- Service latency tracking

### 4. Cache Performance
- Cache hit/miss rates
- Operation duration
- Cache eviction tracking

### 5. Celery Task Monitoring
- Task execution time
- Task success/failure rates
- Queue depth tracking
- Task-specific metrics

### 6. Performance Alerts
- API response time alerts (p95 > 500ms, p99 > 1000ms)
- Database pool utilization alerts (>80%)
- Slow query alerts
- External service latency alerts
- High cache miss rate alerts
- High Celery queue depth alerts

### 7. Custom Business Metrics
- Stories published per day
- Active users
- Content engagement rates
- Custom application metrics

## Configuration

### Environment Variables

```bash
# APM Provider Selection
APM_ENABLED=True
APM_PROVIDER=newrelic  # or 'datadog'

# New Relic Configuration
NEW_RELIC_LICENSE_KEY=your-license-key
NEW_RELIC_APP_NAME=MueJam Library
NEW_RELIC_ENVIRONMENT=production

# DataDog Configuration
DATADOG_API_KEY=your-api-key
DATADOG_APP_KEY=your-app-key
DATADOG_SERVICE_NAME=muejam-backend
DATADOG_ENVIRONMENT=production

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

### Getting Started with New Relic

1. **Create New Relic Account**
   - Sign up at https://newrelic.com
   - Create a new APM application
   - Copy the license key

2. **Configure Environment**
   ```bash
   APM_ENABLED=True
   APM_PROVIDER=newrelic
   NEW_RELIC_LICENSE_KEY=your-license-key
   NEW_RELIC_APP_NAME=MueJam Library
   NEW_RELIC_ENVIRONMENT=production
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Start Application**
   ```bash
   python manage.py runserver
   ```

5. **Verify Integration**
   - Check New Relic dashboard for data
   - View transactions and metrics

### Getting Started with DataDog

1. **Create DataDog Account**
   - Sign up at https://www.datadoghq.com
   - Get API and App keys from settings
   - Install DataDog agent (optional)

2. **Configure Environment**
   ```bash
   APM_ENABLED=True
   APM_PROVIDER=datadog
   DATADOG_API_KEY=your-api-key
   DATADOG_APP_KEY=your-app-key
   DATADOG_SERVICE_NAME=muejam-backend
   DATADOG_ENVIRONMENT=production
   ```

3. **Update Requirements**
   ```bash
   # Uncomment DataDog dependencies in requirements.txt
   # ddtrace==2.5.0
   # datadog==0.48.0
   pip install -r requirements.txt
   ```

4. **Start Application**
   ```bash
   python manage.py runserver
   ```

5. **Verify Integration**
   - Check DataDog APM dashboard
   - View traces and metrics

## Usage

### Automatic Tracking

Most performance metrics are tracked automatically:

- **API Endpoints**: Tracked via APM middleware
- **Database Queries**: Tracked via APM integrations
- **Celery Tasks**: Tracked via Celery integration

### Manual Tracking

#### Track Custom Functions

```python
from infrastructure.apm_config import track_performance

@track_performance('story.create')
def create_story(data):
    # Function implementation
    pass
```

#### Track External Service Calls

```python
from infrastructure.apm_external import track_external_service

@track_external_service('s3', 'upload')
def upload_to_s3(file_path):
    # Upload implementation
    pass
```

#### Track Cache Operations

```python
from infrastructure.apm_external import track_cache_operation

@track_cache_operation('get')
def get_from_cache(key):
    return cache.get(key)
```

#### Track Database Queries

```python
from infrastructure.apm_database import track_database_query

@track_database_query
def get_user_by_id(user_id):
    return User.objects.get(id=user_id)
```

#### Track Celery Tasks

```python
from infrastructure.apm_celery import track_celery_task

@celery_app.task
@track_celery_task
def send_email(to, subject, body):
    # Task implementation
    pass
```

#### Track Business Metrics

```python
from infrastructure.apm_config import PerformanceMonitor

# Track story publication
PerformanceMonitor.track_business_metric(
    'stories.published',
    1,
    tags={'genre': 'fantasy'}
)

# Track active users
PerformanceMonitor.track_business_metric(
    'users.active',
    active_user_count
)

# Track engagement
PerformanceMonitor.track_business_metric(
    'engagement.rate',
    engagement_rate,
    tags={'content_type': 'story'}
)
```

### Manual Metric Recording

#### API Endpoint Performance

```python
from infrastructure.apm_config import PerformanceMonitor

PerformanceMonitor.track_api_endpoint(
    endpoint='/api/stories',
    method='GET',
    status_code=200,
    duration_ms=150.5
)
```

#### Database Query Performance

```python
from infrastructure.apm_config import PerformanceMonitor

PerformanceMonitor.track_database_query(
    query='SELECT * FROM stories',
    duration_ms=85.2,
    rows_returned=100
)
```

#### External Service Calls

```python
from infrastructure.apm_config import PerformanceMonitor

PerformanceMonitor.track_external_service(
    service='s3',
    operation='upload',
    duration_ms=250.0,
    success=True
)
```

#### Cache Operations

```python
from infrastructure.apm_config import PerformanceMonitor

PerformanceMonitor.track_cache_operation(
    operation='get',
    hit=True,
    duration_ms=5.0
)
```

#### Celery Tasks

```python
from infrastructure.apm_config import PerformanceMonitor

PerformanceMonitor.track_celery_task(
    task_name='send_email',
    duration_ms=500.0,
    success=True,
    queue_depth=10
)
```

## Performance Alerts

### Alert Configuration

Alerts are automatically configured based on thresholds:

1. **API Response Time Alerts**
   - P95 > 500ms (high severity)
   - P99 > 1000ms (high severity)

2. **Database Alerts**
   - Pool utilization > 80% (high severity)
   - Slow queries > 100ms (medium severity)

3. **External Service Alerts**
   - Latency > 2000ms (medium severity)

4. **Cache Alerts**
   - Miss rate > 50% (low severity)

5. **Celery Alerts**
   - Queue depth > 100 (medium severity)

### Alert Channels

Alerts can be sent via:

- **Email**: Configured recipients receive alert emails
- **Slack**: Real-time notifications to engineering channel

### Configuring Alerts in New Relic

```python
from infrastructure.apm_alerts import configure_newrelic_alerts

# Get alert configuration
alert_config = configure_newrelic_alerts()

# Apply via New Relic API or dashboard
```

### Configuring Monitors in DataDog

```python
from infrastructure.apm_alerts import configure_datadog_monitors

# Get monitor configuration
monitor_config = configure_datadog_monitors()

# Apply via DataDog API or dashboard
```

## Dashboards

### New Relic Dashboards

Key dashboards to create:

1. **API Performance**
   - Response time trends (p50, p95, p99)
   - Throughput by endpoint
   - Error rates
   - Slow endpoints

2. **Database Performance**
   - Query execution time
   - Slow queries
   - Connection pool utilization
   - Query types distribution

3. **External Services**
   - Service latency by provider
   - Success/failure rates
   - Call volume

4. **Business Metrics**
   - Stories published
   - Active users
   - Engagement rates

### DataDog Dashboards

Key dashboards to create:

1. **Service Overview**
   - Request rate
   - Error rate
   - Latency (p50, p95, p99)
   - Apdex score

2. **Database Metrics**
   - Query performance
   - Connection pool stats
   - Slow query log

3. **Infrastructure**
   - CPU usage
   - Memory usage
   - Disk I/O

4. **Custom Metrics**
   - Business KPIs
   - Application-specific metrics

## Best Practices

### 1. Set Appropriate Thresholds

Adjust thresholds based on your application's performance characteristics:

```bash
# For high-traffic applications
API_P95_THRESHOLD_MS=300
API_P99_THRESHOLD_MS=800

# For low-latency requirements
API_P95_THRESHOLD_MS=200
API_P99_THRESHOLD_MS=500
```

### 2. Monitor Key Endpoints

Focus on critical endpoints:

```python
# Track important endpoints
@track_performance('story.create')
def create_story(data):
    pass

@track_performance('user.authenticate')
def authenticate_user(credentials):
    pass
```

### 3. Track Business Metrics

Monitor business KPIs alongside technical metrics:

```python
# Daily story publications
PerformanceMonitor.track_business_metric('stories.published.daily', count)

# User engagement
PerformanceMonitor.track_business_metric('engagement.rate', rate)

# Revenue metrics
PerformanceMonitor.track_business_metric('revenue.daily', amount)
```

### 4. Use Distributed Tracing

Enable distributed tracing to track requests across services:

- New Relic: Automatically enabled
- DataDog: Automatically enabled with ddtrace

### 5. Optimize Based on Data

Regularly review APM data to identify:

- Slow endpoints
- N+1 query problems
- High-latency external calls
- Cache inefficiencies

## Troubleshooting

### No Data in APM Dashboard

1. **Check Configuration**
   ```bash
   echo $APM_ENABLED
   echo $APM_PROVIDER
   echo $NEW_RELIC_LICENSE_KEY  # or DATADOG_API_KEY
   ```

2. **Verify Integration**
   ```python
   from infrastructure.apm_config import APMConfig
   print(APMConfig.is_enabled())
   print(APMConfig.get_provider().enabled)
   ```

3. **Check Logs**
   - Look for APM initialization messages
   - Check for connection errors

### High Overhead

1. **Reduce Sample Rates**
   - Lower transaction tracing percentage
   - Reduce metric collection frequency

2. **Disable Unnecessary Tracking**
   - Remove tracking from high-frequency functions
   - Focus on critical paths

### Alert Fatigue

1. **Adjust Thresholds**
   - Increase thresholds to reduce false positives
   - Use percentiles instead of averages

2. **Implement Alert Grouping**
   - Group similar alerts
   - Use alert suppression during maintenance

## Resources

- [New Relic Documentation](https://docs.newrelic.com/)
- [DataDog APM Documentation](https://docs.datadoghq.com/tracing/)
- [Django Performance Optimization](https://docs.djangoproject.com/en/stable/topics/performance/)
- [Database Query Optimization](https://docs.djangoproject.com/en/stable/topics/db/optimization/)
