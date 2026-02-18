# Application Performance Monitoring (APM) Setup

## Overview

APM is configured to monitor application performance, track slow queries, and alert on performance degradation. The system supports both New Relic and DataDog APM providers.

## Supported APM Providers

### Option 1: New Relic (Recommended)
- Comprehensive APM features
- Django, Celery, and database monitoring
- Free tier available
- Easy setup

### Option 2: DataDog
- Full-stack monitoring
- Infrastructure + APM
- Advanced alerting
- Higher cost

### Option 3: Built-in Metrics (No external APM)
- Uses internal metrics collector
- Prometheus-compatible metrics
- No external dependencies
- Limited features

## Configuration

### Environment Variables

```bash
# APM Provider Selection
APM_PROVIDER=newrelic  # or 'datadog' or 'none'
APM_ENABLED=True

# Performance Thresholds
API_P95_THRESHOLD_MS=500  # Alert if P95 > 500ms
API_P99_THRESHOLD_MS=1000  # Alert if P99 > 1000ms
SLOW_QUERY_THRESHOLD_MS=100  # Log queries > 100ms
DB_POOL_UTILIZATION_THRESHOLD=0.8  # Alert if pool > 80%

# Alert Configuration
PERFORMANCE_ALERT_EMAIL_ENABLED=True
PERFORMANCE_ALERT_EMAIL_RECIPIENTS=team@example.com,oncall@example.com
PERFORMANCE_ALERT_SLACK_ENABLED=True
PERFORMANCE_ALERT_SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

## New Relic Setup

### 1. Create New Relic Account

1. Go to [newrelic.com](https://newrelic.com)
2. Sign up for free account
3. Create new application
4. Get license key

### 2. Install New Relic Agent

```bash
pip install newrelic
```

### 3. Configure New Relic

Create `newrelic.ini`:
```ini
[newrelic]
license_key = YOUR_LICENSE_KEY
app_name = MueJam Backend (Production)
monitor_mode = true
log_level = info

# Transaction tracer settings
transaction_tracer.enabled = true
transaction_tracer.transaction_threshold = apdex_f
transaction_tracer.record_sql = obfuscated
transaction_tracer.stack_trace_threshold = 0.5
transaction_tracer.explain_enabled = true
transaction_tracer.explain_threshold = 0.5

# Error collector settings
error_collector.enabled = true
error_collector.ignore_errors = django.http:Http404

# Browser monitoring
browser_monitoring.auto_instrument = true

# Thread profiler
thread_profiler.enabled = true

# Distributed tracing
distributed_tracing.enabled = true
```

### 4. Set Environment Variables

```bash
export NEW_RELIC_CONFIG_FILE=newrelic.ini
export NEW_RELIC_LICENSE_KEY=your_license_key
export NEW_RELIC_APP_NAME="MueJam Backend (Production)"
export APM_PROVIDER=newrelic
export APM_ENABLED=True
```

### 5. Run with New Relic

```bash
# Development
NEW_RELIC_CONFIG_FILE=newrelic.ini newrelic-admin run-program python manage.py runserver

# Production (Gunicorn)
NEW_RELIC_CONFIG_FILE=newrelic.ini newrelic-admin run-program gunicorn config.wsgi:application

# Celery Worker
NEW_RELIC_CONFIG_FILE=newrelic.ini newrelic-admin run-program celery -A config worker
```

## DataDog Setup

### 1. Create DataDog Account

1. Go to [datadoghq.com](https://www.datadoghq.com)
2. Sign up for account
3. Get API key

### 2. Install DataDog Agent

```bash
pip install ddtrace
```

### 3. Configure DataDog

```bash
export DD_API_KEY=your_api_key
export DD_SERVICE=muejam-backend
export DD_ENV=production
export DD_VERSION=1.0.0
export DD_TRACE_ENABLED=true
export DD_PROFILING_ENABLED=true
export APM_PROVIDER=datadog
export APM_ENABLED=True
```

### 4. Run with DataDog

```bash
# Development
ddtrace-run python manage.py runserver

# Production (Gunicorn)
ddtrace-run gunicorn config.wsgi:application

# Celery Worker
ddtrace-run celery -A config worker
```

## Built-in Metrics (No External APM)

If you don't want to use external APM:

```bash
export APM_PROVIDER=none
export APM_ENABLED=True  # Still enables internal metrics
```

Access metrics at:
- `/metrics` - Prometheus-compatible metrics
- `/api/metrics/performance` - Performance metrics API

## Monitored Metrics

### 1. API Endpoint Performance
- Request duration (P50, P95, P99)
- Request rate
- Error rate
- Status code distribution
- Per-endpoint metrics

### 2. Database Performance
- Query duration
- Slow queries (> 100ms)
- Connection pool utilization
- Query count
- Transaction duration

### 3. External Service Calls
- HTTP request duration
- Success/failure rate
- Timeout rate
- Per-service metrics

### 4. Cache Performance
- Hit rate
- Miss rate
- Get/set duration
- Eviction rate

### 5. Celery Tasks
- Task duration
- Task success/failure rate
- Queue length
- Worker utilization

### 6. Business Metrics
- Story creation rate
- User registration rate
- Active users
- Content engagement

## Performance Thresholds

### API Response Times

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| P50 | < 100ms | 200ms | 300ms |
| P95 | < 500ms | 750ms | 1000ms |
| P99 | < 1000ms | 1500ms | 2000ms |

### Database Queries

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| Query Time | < 50ms | 100ms | 500ms |
| Pool Utilization | < 60% | 80% | 90% |
| Slow Queries | 0 | 5/min | 20/min |

### External Services

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| Response Time | < 200ms | 500ms | 1000ms |
| Error Rate | < 0.1% | 1% | 5% |
| Timeout Rate | < 0.1% | 0.5% | 1% |

## Alert Configuration

### New Relic Alerts

1. Go to Alerts & AI → Alert Conditions
2. Create new condition:

**API Response Time Alert**:
- Condition: Web transactions time (95th percentile) > 500ms for 5 minutes
- Severity: Warning
- Notification: Email + Slack

**Database Pool Alert**:
- Condition: Database pool utilization > 80% for 5 minutes
- Severity: Critical
- Notification: Email + Slack + PagerDuty

**Error Rate Alert**:
- Condition: Error rate > 1% for 5 minutes
- Severity: Warning
- Notification: Slack

### DataDog Monitors

1. Go to Monitors → New Monitor
2. Create APM monitor:

**Slow API Endpoints**:
```
avg(last_5m):avg:trace.django.request.duration{env:production} by {resource_name}.as_rate() > 0.5
```

**High Error Rate**:
```
sum(last_5m):sum:trace.django.request.errors{env:production}.as_count() > 10
```

**Database Connection Pool**:
```
avg(last_5m):avg:database.pool.utilization{env:production} > 0.8
```

## Dashboards

### New Relic Dashboard

Create dashboard with:
1. **Overview**:
   - Request rate
   - Error rate
   - Response time (P50, P95, P99)
   - Apdex score

2. **API Endpoints**:
   - Top 10 slowest endpoints
   - Top 10 most called endpoints
   - Error rate by endpoint

3. **Database**:
   - Query duration
   - Slow queries
   - Connection pool utilization
   - Top 10 slowest queries

4. **External Services**:
   - External call duration
   - External call error rate
   - Per-service metrics

5. **Celery**:
   - Task duration
   - Task success rate
   - Queue length

### DataDog Dashboard

Create dashboard with widgets:
- Timeseries: Request rate, error rate, latency
- Top List: Slowest endpoints, most errors
- Query Value: Current pool utilization, error rate
- Heatmap: Response time distribution

## Custom Instrumentation

### Track Custom Metrics

```python
from infrastructure.apm_config import PerformanceMonitor

# Track custom metric
PerformanceMonitor.track_custom_metric(
    name='story.created',
    value=1,
    tags={'genre': 'fantasy', 'user_tier': 'premium'}
)
```

### Track Database Queries

```python
from infrastructure.apm_database import track_database_query

with track_database_query('SELECT * FROM stories WHERE ...'):
    stories = Story.objects.filter(...)
```

### Track External Service Calls

```python
from infrastructure.apm_external import track_external_service

with track_external_service('clerk', 'get_user'):
    response = requests.get('https://api.clerk.com/v1/users/...')
```

### Track Celery Tasks

```python
from infrastructure.apm_celery import track_celery_task

@track_celery_task
@app.task
def process_story(story_id):
    # Task code
    pass
```

## Verification

### 1. Check APM is Enabled

```bash
python manage.py shell
```

```python
from infrastructure.apm_config import APMConfig
print(f"APM Enabled: {APMConfig.is_enabled()}")
print(f"APM Provider: {APMConfig.get_provider_name()}")
```

### 2. Generate Test Traffic

```bash
# Run load test
locust -f tests/load_tests/locustfile.py --host=http://localhost:8000 --users 10 --spawn-rate 2 --run-time 2m --headless
```

### 3. Check APM Dashboard

**New Relic**:
1. Go to APM → Applications → MueJam Backend
2. Verify transactions are being recorded
3. Check response times
4. Verify database queries are tracked

**DataDog**:
1. Go to APM → Services → muejam-backend
2. Verify traces are being collected
3. Check service map
4. Verify resource metrics

### 4. Test Alerts

Trigger slow endpoint:
```python
import time
from django.http import JsonResponse

def slow_endpoint(request):
    time.sleep(2)  # Simulate slow operation
    return JsonResponse({'status': 'ok'})
```

Call endpoint multiple times and verify alert fires.

## Troubleshooting

### APM Not Recording Data

1. **Check APM is enabled**:
   ```bash
   echo $APM_ENABLED
   echo $APM_PROVIDER
   ```

2. **Check agent is installed**:
   ```bash
   pip list | grep newrelic  # or ddtrace
   ```

3. **Check configuration**:
   ```bash
   # New Relic
   echo $NEW_RELIC_LICENSE_KEY
   cat newrelic.ini
   
   # DataDog
   echo $DD_API_KEY
   ```

4. **Check logs**:
   ```bash
   tail -f apps/backend/logs/muejam.log | grep -i apm
   ```

### High Overhead

APM can add overhead. To reduce:

1. **Lower sampling rate** (New Relic):
   ```ini
   transaction_tracer.transaction_threshold = 1.0  # Only trace slow transactions
   ```

2. **Disable features**:
   ```ini
   thread_profiler.enabled = false
   browser_monitoring.auto_instrument = false
   ```

3. **Use sampling** (DataDog):
   ```bash
   export DD_TRACE_SAMPLE_RATE=0.1  # Sample 10% of traces
   ```

### Missing Metrics

1. **Check middleware is enabled**:
   ```python
   from django.conf import settings
   print('infrastructure.apm_middleware.APMMiddleware' in settings.MIDDLEWARE)
   ```

2. **Check instrumentation**:
   - Verify decorators are applied
   - Check context managers are used
   - Verify imports are correct

3. **Check APM provider connection**:
   - Test network connectivity
   - Verify API keys
   - Check firewall rules

## Best Practices

1. **Use appropriate sampling rates**:
   - Production: 10-20% of transactions
   - Staging: 50-100% of transactions
   - Development: 100% of transactions

2. **Set meaningful transaction names**:
   - Use URL patterns, not full URLs
   - Group similar transactions
   - Avoid high cardinality

3. **Add custom attributes**:
   - User tier (free, premium)
   - Feature flags
   - A/B test variants
   - Request source (web, mobile, API)

4. **Monitor key business metrics**:
   - User signups
   - Story publications
   - Revenue events
   - Feature usage

5. **Set up alerts proactively**:
   - Don't wait for issues
   - Alert on trends, not just thresholds
   - Use multiple severity levels
   - Test alert delivery

6. **Review dashboards regularly**:
   - Daily: Check for anomalies
   - Weekly: Review trends
   - Monthly: Capacity planning
   - Quarterly: Optimization opportunities

7. **Optimize based on data**:
   - Focus on high-traffic endpoints
   - Optimize slow queries first
   - Cache frequently accessed data
   - Use async for slow operations

## Monitoring Checklist

- [ ] APM provider selected and configured
- [ ] Agent installed and running
- [ ] Middleware enabled
- [ ] Test traffic generated
- [ ] Metrics appearing in dashboard
- [ ] Alerts configured
- [ ] Alert delivery tested
- [ ] Dashboards created
- [ ] Team trained on APM usage
- [ ] Runbooks created for common issues

## Resources

- [New Relic Python Agent](https://docs.newrelic.com/docs/agents/python-agent/)
- [DataDog APM Python](https://docs.datadoghq.com/tracing/setup_overview/setup/python/)
- [Django Performance Optimization](https://docs.djangoproject.com/en/stable/topics/performance/)
- [Database Query Optimization](https://docs.djangoproject.com/en/stable/topics/db/optimization/)

## Support

For APM issues:
1. Check this documentation
2. Review APM provider docs
3. Check application logs
4. Test with manual instrumentation
5. Contact DevOps team
