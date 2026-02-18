# Request Timeout Monitoring

This document describes how to monitor request timeouts in the application.

## Overview

The `TimeoutMiddleware` enforces a configurable timeout on all API requests to prevent resource exhaustion. When requests exceed the timeout, they are terminated and logged.

## Configuration

The timeout is configured via the `REQUEST_TIMEOUT` environment variable (default: 30 seconds):

```bash
REQUEST_TIMEOUT=30  # seconds
```

## Monitoring Timeout Events

### Log Monitoring

Timeout events are logged with the following structure:

```python
logger.error(
    f"Request timeout",
    extra={
        'path': request.path,
        'method': request.method,
        'timeout': self.timeout,
        'user': getattr(request, 'user_profile', None)
    }
)
```

### Key Metrics to Monitor

1. **Timeout Rate**
   - Metric: `request_timeouts_total`
   - Description: Total number of requests that exceeded the timeout
   - Alert threshold: > 1% of total requests

2. **Timeout by Endpoint**
   - Metric: `request_timeouts_by_path`
   - Description: Number of timeouts grouped by request path
   - Use to identify problematic endpoints

3. **Average Request Duration**
   - Metric: `request_duration_seconds`
   - Description: Average time to complete requests
   - Alert threshold: P95 > 80% of timeout value (24s for 30s timeout)

4. **Slow Endpoints**
   - Metric: `slow_requests_total`
   - Description: Requests taking > 50% of timeout
   - Alert threshold: > 5% of requests

## Sentry Integration

Timeout errors are automatically captured by Sentry with full context:

- Request path and method
- User information (if authenticated)
- Timeout value
- Stack trace

## APM Integration

If APM is enabled (New Relic or DataDog), timeout events are tracked as:

- Transaction errors
- Slow transaction traces
- Error rate metrics

## Grafana Dashboards

### Timeout Overview Dashboard

```
Panel 1: Timeout Rate (%)
- Query: (request_timeouts_total / requests_total) * 100
- Visualization: Time series graph
- Alert: > 1%

Panel 2: Timeouts by Endpoint
- Query: sum(request_timeouts_by_path) by (path)
- Visualization: Bar chart
- Shows which endpoints timeout most frequently

Panel 3: Request Duration Distribution
- Query: histogram_quantile(0.95, request_duration_seconds)
- Visualization: Heatmap
- Shows P50, P95, P99 latencies

Panel 4: Timeout Events (Last 24h)
- Query: increase(request_timeouts_total[24h])
- Visualization: Single stat
- Shows total timeouts in last 24 hours
```

## Alerts

### Critical Alert: High Timeout Rate

```yaml
alert: HighTimeoutRate
expr: (rate(request_timeouts_total[5m]) / rate(requests_total[5m])) > 0.01
for: 5m
labels:
  severity: critical
annotations:
  summary: "High request timeout rate detected"
  description: "{{ $value | humanizePercentage }} of requests are timing out"
```

### Warning Alert: Endpoint Consistently Timing Out

```yaml
alert: EndpointTimeouts
expr: rate(request_timeouts_by_path[10m]) > 0.1
for: 10m
labels:
  severity: warning
annotations:
  summary: "Endpoint {{ $labels.path }} timing out frequently"
  description: "{{ $value }} timeouts/sec on {{ $labels.path }}"
```

### Warning Alert: Requests Approaching Timeout

```yaml
alert: SlowRequests
expr: histogram_quantile(0.95, request_duration_seconds) > 24
for: 5m
labels:
  severity: warning
annotations:
  summary: "Requests approaching timeout threshold"
  description: "P95 latency is {{ $value }}s (timeout: 30s)"
```

## Troubleshooting Timeouts

### Common Causes

1. **Slow Database Queries**
   - Check slow query logs
   - Add missing indexes
   - Optimize N+1 queries
   - Use `select_related()` and `prefetch_related()`

2. **External API Calls**
   - Add circuit breakers
   - Implement timeouts on external calls
   - Use async/background tasks for slow operations

3. **Large Data Processing**
   - Move to background tasks (Celery)
   - Implement pagination
   - Add caching

4. **Resource Contention**
   - Check database connection pool utilization
   - Monitor worker thread usage
   - Check for deadlocks

### Investigation Steps

1. **Identify the endpoint**
   ```bash
   # Search logs for timeout events
   grep "Request timeout" logs/muejam.log | jq '.path' | sort | uniq -c
   ```

2. **Check request patterns**
   ```bash
   # Find common characteristics of timing out requests
   grep "Request timeout" logs/muejam.log | jq '{path, method, user}'
   ```

3. **Analyze database queries**
   ```sql
   -- Find slow queries
   SELECT query, mean_exec_time, calls
   FROM pg_stat_statements
   WHERE mean_exec_time > 1000  -- > 1 second
   ORDER BY mean_exec_time DESC
   LIMIT 10;
   ```

4. **Check APM traces**
   - Review transaction traces in New Relic/DataDog
   - Identify slow database queries
   - Check external API call durations

### Remediation

1. **Immediate (< 1 hour)**
   - Increase timeout temporarily if legitimate slow operations
   - Add endpoint to skip list if admin operation
   - Scale up resources if under heavy load

2. **Short-term (< 1 day)**
   - Add database indexes
   - Optimize slow queries
   - Add caching for expensive operations
   - Implement pagination

3. **Long-term (< 1 week)**
   - Move slow operations to background tasks
   - Implement async processing
   - Add circuit breakers for external calls
   - Optimize application code

## Best Practices

1. **Set Appropriate Timeouts**
   - API endpoints: 30s (default)
   - Admin operations: 60s (skip timeout)
   - Background tasks: No timeout (use Celery)

2. **Monitor Proactively**
   - Set up alerts before timeouts become critical
   - Review timeout metrics weekly
   - Investigate any endpoint with > 0.1% timeout rate

3. **Optimize Early**
   - Add indexes during development
   - Use `select_related()` and `prefetch_related()`
   - Cache expensive operations
   - Paginate large result sets

4. **Test Under Load**
   - Run load tests to identify slow endpoints
   - Test with realistic data volumes
   - Simulate slow external APIs

## Platform-Specific Notes

### Unix/Linux (Production)
- Uses `signal.SIGALRM` for timeout enforcement
- Fully supported and tested
- Recommended for production deployments

### Windows (Development)
- `SIGALRM` not available on Windows
- Middleware will fail on Windows
- Use Unix-based systems for production
- For Windows development, consider:
  - Using WSL (Windows Subsystem for Linux)
  - Docker containers
  - Disabling timeout middleware in development

## References

- Middleware implementation: `apps/backend/infrastructure/timeout_middleware.py`
- Configuration: `apps/backend/config/settings.py`
- Logging configuration: `apps/backend/infrastructure/logging_config.py`
