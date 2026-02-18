# Rate Limiting Monitoring Guide

## Overview

This guide explains how to monitor rate limiting effectiveness in production. The rate limiting middleware logs all rate limit events and provides metrics for tracking abuse, performance, and system health.

## Current Implementation

The rate limiting system consists of:
- **RateLimitMiddleware**: Enforces rate limits on all requests
- **RateLimiter**: Implements sliding window algorithm with Redis
- **Logging**: Comprehensive logging of rate limit events
- **Headers**: Standard rate limit headers on all responses

## Rate Limit Events Logged

### 1. Rate Limit Exceeded (429 Responses)

When a user exceeds their rate limit, the middleware logs a warning:

```python
logger.warning(
    f"Rate limit exceeded for {user_id}",
    extra={
        'user_id': user_id,
        'path': request.path,
        'method': request.method,
        'limit': user_result.limit,
        'retry_after': user_result.retry_after
    }
)
```

**Log Fields:**
- `user_id`: User identifier (e.g., "user:123" or "ip:192.168.1.1")
- `path`: Request path that was rate limited
- `method`: HTTP method (GET, POST, etc.)
- `limit`: Rate limit threshold (requests per minute)
- `retry_after`: Seconds until user can retry

**Example Log Entry:**
```
WARNING Rate limit exceeded for user:550e8400-e29b-41d4-a716-446655440000
  user_id: user:550e8400-e29b-41d4-a716-446655440000
  path: /api/stories
  method: GET
  limit: 100
  retry_after: 45
```

### 2. Admin Bypass Events

Admin users bypass rate limits. This is logged implicitly through the absence of rate limit warnings for admin users.

**Monitoring Admin Bypass:**
- Track requests from admin users
- Compare request rates between admin and non-admin users
- Alert if admin accounts show suspicious activity

### 3. Redis Connection Failures

If Redis is unavailable, the rate limiter fails open (allows all requests) and logs warnings:

```
Warning: Redis error in check_user_limit: Connection refused
```

**Critical Alert:** Redis failures disable rate limiting entirely.

## Monitoring Strategies

### 1. Log-Based Monitoring

**Query rate limit exceeded events:**

```bash
# Count rate limit events in the last hour
grep "Rate limit exceeded" /var/log/app.log | grep "$(date -u +%Y-%m-%d\ %H)" | wc -l

# Top rate-limited users
grep "Rate limit exceeded" /var/log/app.log | \
  grep -oP "user_id: \K[^,]+" | \
  sort | uniq -c | sort -rn | head -20

# Top rate-limited endpoints
grep "Rate limit exceeded" /var/log/app.log | \
  grep -oP "path: \K[^,]+" | \
  sort | uniq -c | sort -rn | head -20
```

**Using structured logging (JSON):**

```bash
# If logs are in JSON format
cat /var/log/app.log | jq 'select(.message | contains("Rate limit exceeded"))'

# Count by user
cat /var/log/app.log | \
  jq -r 'select(.message | contains("Rate limit exceeded")) | .extra.user_id' | \
  sort | uniq -c | sort -rn
```

### 2. Metrics Collection

**Key Metrics to Track:**

1. **Rate Limit Hit Rate**
   - Total 429 responses / Total requests
   - Target: < 1% for normal traffic
   - Alert: > 5% indicates potential attack or misconfigured limits

2. **Rate Limited Users**
   - Unique users receiving 429 responses
   - Track daily/hourly trends
   - Alert: Sudden spike indicates attack

3. **Rate Limited Endpoints**
   - Which endpoints are most frequently rate limited
   - Helps identify if limits are too restrictive

4. **Admin Bypass Usage**
   - Track admin request rates
   - Alert: Admin accounts with abnormal request patterns

5. **Redis Health**
   - Redis connection failures
   - Redis response time
   - Alert: Any Redis failures (disables rate limiting)

**Example Prometheus Metrics:**

```python
# Add to rate_limit_middleware.py
from prometheus_client import Counter, Histogram

rate_limit_exceeded = Counter(
    'rate_limit_exceeded_total',
    'Total rate limit exceeded events',
    ['user_type', 'endpoint']
)

rate_limit_response_time = Histogram(
    'rate_limit_check_duration_seconds',
    'Time spent checking rate limits'
)
```

### 3. Dashboard Setup

**Recommended Dashboard Panels:**

1. **Rate Limit Overview**
   - Total requests vs rate limited requests (last 24h)
   - Rate limit hit rate percentage
   - Trend line showing rate limit events over time

2. **Top Rate Limited Users**
   - Table showing users with most 429 responses
   - Include user_id, request count, last seen

3. **Top Rate Limited Endpoints**
   - Bar chart of endpoints by 429 count
   - Helps identify if specific endpoints need adjustment

4. **Rate Limit Response Times**
   - P50, P95, P99 latency for rate limit checks
   - Should be < 10ms for Redis operations

5. **Redis Health**
   - Redis connection status
   - Redis operation latency
   - Redis memory usage

6. **Admin Activity**
   - Request rates for admin users
   - Admin bypass events
   - Anomaly detection for admin accounts

### 4. Alerting Rules

**Critical Alerts:**

1. **Redis Down**
   ```
   Alert: Rate limiting Redis unavailable
   Condition: Redis connection failures > 0
   Severity: CRITICAL
   Action: Page on-call engineer immediately
   Impact: Rate limiting is disabled
   ```

2. **High Rate Limit Hit Rate**
   ```
   Alert: High rate limit hit rate
   Condition: 429 responses > 10% of total requests for 5 minutes
   Severity: HIGH
   Action: Investigate potential attack or misconfiguration
   ```

3. **Suspicious Admin Activity**
   ```
   Alert: Admin account excessive requests
   Condition: Admin user > 1000 requests/minute
   Severity: MEDIUM
   Action: Review admin account activity
   ```

**Warning Alerts:**

1. **Elevated Rate Limiting**
   ```
   Alert: Elevated rate limiting
   Condition: 429 responses > 5% of total requests for 15 minutes
   Severity: MEDIUM
   Action: Monitor for attack or adjust limits
   ```

2. **New User Hitting Limits**
   ```
   Alert: Multiple users hitting rate limits
   Condition: > 50 unique users rate limited in 1 hour
   Severity: LOW
   Action: Review if limits are too restrictive
   ```

## Response Headers

All responses include rate limit headers for client-side monitoring:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 2024-01-15T10:30:00Z
```

When rate limited:
```
HTTP/1.1 429 Too Many Requests
Retry-After: 45
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 2024-01-15T10:30:00Z

{
  "error": "Rate limit exceeded",
  "message": "Too many requests. Limit: 100 requests per minute.",
  "limit": 100,
  "retry_after": 45
}
```

**Client-Side Monitoring:**
- Clients should respect Retry-After header
- Clients should track X-RateLimit-Remaining
- Clients should implement exponential backoff

## Production Monitoring Checklist

- [ ] **Logging configured**: Ensure application logs are collected centrally
- [ ] **Log retention**: Keep rate limit logs for at least 30 days
- [ ] **Metrics collection**: Set up Prometheus or similar metrics system
- [ ] **Dashboard created**: Create rate limiting dashboard with key metrics
- [ ] **Alerts configured**: Set up critical and warning alerts
- [ ] **Redis monitoring**: Monitor Redis health and performance
- [ ] **On-call runbook**: Document response procedures for rate limit alerts
- [ ] **Regular review**: Review rate limit effectiveness weekly

## Analyzing Rate Limit Effectiveness

### Questions to Answer:

1. **Are limits appropriate?**
   - Are legitimate users being rate limited?
   - Are limits preventing abuse?
   - Do different endpoints need different limits?

2. **Is the system under attack?**
   - Sudden spike in rate limit events?
   - Many unique IPs hitting limits?
   - Distributed attack pattern?

3. **Are admin bypasses working?**
   - Are admin users able to perform operations?
   - Are admin accounts being abused?

4. **Is Redis healthy?**
   - Any connection failures?
   - Response times acceptable?
   - Memory usage stable?

### Weekly Review Process:

1. **Review metrics dashboard**
   - Check rate limit hit rate trend
   - Identify any anomalies

2. **Analyze top rate-limited users**
   - Are they legitimate users or bots?
   - Should limits be adjusted?
   - Should users be blocked?

3. **Review rate-limited endpoints**
   - Are limits appropriate per endpoint?
   - Should some endpoints have higher/lower limits?

4. **Check Redis health**
   - Any performance issues?
   - Memory usage trending up?
   - Need to scale Redis?

5. **Review admin activity**
   - Any suspicious admin account activity?
   - Admin bypass working correctly?

## Troubleshooting

### High Rate Limit Hit Rate

**Symptoms:**
- Many 429 responses
- User complaints about rate limiting

**Possible Causes:**
1. Limits too restrictive
2. DDoS attack
3. Misconfigured client (retry loop)
4. Legitimate traffic spike

**Investigation Steps:**
1. Check if spike is from single user or distributed
2. Review request patterns (same endpoint? same user?)
3. Check if legitimate traffic or attack
4. Review rate limit configuration

**Resolution:**
- If attack: Block IPs, adjust limits temporarily
- If legitimate: Increase limits, optimize endpoints
- If misconfigured client: Contact user, fix client

### Redis Connection Failures

**Symptoms:**
- "Redis error" warnings in logs
- Rate limiting not working
- All requests allowed

**Possible Causes:**
1. Redis server down
2. Network issues
3. Redis out of memory
4. Connection pool exhausted

**Investigation Steps:**
1. Check Redis server status
2. Check network connectivity
3. Check Redis memory usage
4. Check Redis logs

**Resolution:**
- Restart Redis if crashed
- Scale Redis if out of memory
- Fix network issues
- Increase connection pool if exhausted

### Admin Bypass Not Working

**Symptoms:**
- Admin users receiving 429 responses
- Admin operations failing

**Possible Causes:**
1. Admin check failing
2. ModeratorRole not set correctly
3. Database connection issues

**Investigation Steps:**
1. Check admin user has ModeratorRole
2. Check ModeratorRole.is_active = True
3. Check database connectivity
4. Review middleware logs

**Resolution:**
- Fix ModeratorRole records
- Fix database connection
- Review admin check logic

## Configuration

Current rate limit configuration (in `settings.py`):

```python
# Rate limiting settings
RATE_LIMIT_ENABLED = True
RATE_LIMIT_PER_USER = 100  # requests per minute
RATE_LIMIT_GLOBAL = 10000  # requests per minute
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_ADMIN_BYPASS = True
RATE_LIMIT_REDIS_URL = os.getenv('VALKEY_URL', 'redis://localhost:6379/0')
```

**Adjusting Limits:**
- Increase `RATE_LIMIT_PER_USER` if legitimate users hit limits
- Increase `RATE_LIMIT_GLOBAL` if system can handle more load
- Decrease limits if under attack
- Set `RATE_LIMIT_ADMIN_BYPASS = False` to test admin rate limiting

## Best Practices

1. **Start conservative**: Begin with lower limits and increase based on monitoring
2. **Monitor continuously**: Review metrics weekly, alerts daily
3. **Document changes**: Log all rate limit configuration changes
4. **Test regularly**: Test rate limiting in staging before production changes
5. **Communicate**: Inform users of rate limits via API documentation
6. **Provide feedback**: Return clear error messages with retry information
7. **Implement backoff**: Encourage clients to implement exponential backoff
8. **Review regularly**: Adjust limits based on traffic patterns and abuse

## Additional Resources

- **Rate Limiter Implementation**: `apps/backend/infrastructure/rate_limiter.py`
- **Middleware Implementation**: `apps/backend/infrastructure/rate_limit_middleware.py`
- **Configuration**: `apps/backend/config/settings.py`
- **Design Document**: `.kiro/specs/production-readiness-audit/design.md`

## Summary

The rate limiting system provides comprehensive logging and monitoring capabilities:

✅ **Logging**: All rate limit exceeded events logged with context
✅ **Headers**: Standard rate limit headers on all responses  
✅ **Admin Bypass**: Admin users bypass rate limits (logged implicitly)
✅ **Redis Monitoring**: Redis failures logged and rate limiting fails open
✅ **Metrics Ready**: Structured logs ready for metrics collection
✅ **Dashboard Ready**: Key metrics identified for dashboard creation
✅ **Alerts Defined**: Critical and warning alerts documented

**Next Steps:**
1. Set up centralized logging (e.g., ELK, Splunk, CloudWatch)
2. Create metrics collection (e.g., Prometheus)
3. Build monitoring dashboard (e.g., Grafana)
4. Configure alerts (e.g., PagerDuty, Opsgenie)
5. Document on-call runbook
6. Schedule weekly review process
