# Rate Limiting Monitoring - Quick Reference

## Quick Status Check

### Check if rate limiting is working
```bash
# Test rate limit (should get 429 after 100 requests)
for i in {1..105}; do
  curl -H "Authorization: Bearer YOUR_TOKEN" \
       http://localhost:8000/api/stories
done
```

### View recent rate limit events
```bash
# Last 100 rate limit events
tail -n 1000 /var/log/app.log | grep "Rate limit exceeded"

# Count rate limit events in last hour
grep "Rate limit exceeded" /var/log/app.log | \
  grep "$(date -u +%Y-%m-%d\ %H)" | wc -l
```

### Check Redis health
```bash
# Connect to Redis
redis-cli -h localhost -p 6379

# Check connection
PING

# Check rate limit keys
KEYS ratelimit:*

# Check specific user's rate limit
ZCARD ratelimit:user:USER_ID_HERE
```

## Key Log Patterns

### Rate Limit Exceeded
```
WARNING Rate limit exceeded for user:550e8400-e29b-41d4-a716-446655440000
  user_id: user:550e8400-e29b-41d4-a716-446655440000
  path: /api/stories
  method: GET
  limit: 100
  retry_after: 45
```

### Redis Connection Failure (CRITICAL)
```
Warning: Redis error in check_user_limit: Connection refused
Warning: Redis connection failed: Connection refused. Rate limiting disabled.
```

## Response Headers

### Normal Response
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 2024-01-15T10:30:00Z
```

### Rate Limited Response (429)
```
HTTP/1.1 429 Too Many Requests
Retry-After: 45
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 2024-01-15T10:30:00Z
```

## Common Queries

### Top 10 rate-limited users
```bash
grep "Rate limit exceeded" /var/log/app.log | \
  grep -oP "user_id: \K[^,]+" | \
  sort | uniq -c | sort -rn | head -10
```

### Top 10 rate-limited endpoints
```bash
grep "Rate limit exceeded" /var/log/app.log | \
  grep -oP "path: \K[^,]+" | \
  sort | uniq -c | sort -rn | head -10
```

### Rate limit events by hour (last 24h)
```bash
grep "Rate limit exceeded" /var/log/app.log | \
  grep -oP "\d{4}-\d{2}-\d{2} \d{2}" | \
  sort | uniq -c
```

### Check if specific user is rate limited
```bash
grep "Rate limit exceeded" /var/log/app.log | \
  grep "user:USER_ID_HERE"
```

## Alert Thresholds

| Alert | Threshold | Severity | Action |
|-------|-----------|----------|--------|
| Redis Down | Any connection failure | CRITICAL | Page on-call immediately |
| High Rate Limit Hit Rate | >10% of requests for 5min | HIGH | Investigate attack/config |
| Elevated Rate Limiting | >5% of requests for 15min | MEDIUM | Monitor for attack |
| Suspicious Admin Activity | Admin >1000 req/min | MEDIUM | Review admin account |
| Multiple Users Limited | >50 users in 1 hour | LOW | Review if limits too restrictive |

## Configuration

Current settings (in `settings.py`):
```python
RATE_LIMIT_ENABLED = True
RATE_LIMIT_PER_USER = 100  # requests per minute
RATE_LIMIT_GLOBAL = 10000  # requests per minute
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_ADMIN_BYPASS = True
```

## Troubleshooting

### Problem: High rate limit hit rate
**Check:**
1. Is it a DDoS attack? (many unique IPs)
2. Is it a misconfigured client? (same user, retry loop)
3. Are limits too restrictive? (legitimate users affected)

**Action:**
- If attack: Block IPs, adjust limits temporarily
- If misconfigured client: Contact user
- If too restrictive: Increase limits

### Problem: Redis connection failures
**Check:**
1. Is Redis running? `systemctl status redis`
2. Can app connect? `redis-cli -h HOST -p PORT PING`
3. Is Redis out of memory? `redis-cli INFO memory`

**Action:**
- Restart Redis if crashed
- Scale Redis if out of memory
- Fix network connectivity

### Problem: Admin users rate limited
**Check:**
1. Does user have ModeratorRole? `SELECT * FROM "ModeratorRole" WHERE user_id = 'USER_ID'`
2. Is is_active = TRUE?
3. Is RATE_LIMIT_ADMIN_BYPASS = True?

**Action:**
- Fix ModeratorRole record
- Enable admin bypass in settings

## Emergency Response

### Disable rate limiting (emergency only)
```python
# In settings.py
RATE_LIMIT_ENABLED = False
```

### Increase limits temporarily
```python
# In settings.py
RATE_LIMIT_PER_USER = 500  # Increase from 100
RATE_LIMIT_GLOBAL = 50000  # Increase from 10000
```

### Block specific user
```bash
# Add to Redis with long TTL
redis-cli SET "ratelimit:blocked:user:USER_ID" "1" EX 86400
```

## Metrics to Track

1. **Rate Limit Hit Rate**: 429 responses / Total requests (target: <1%)
2. **Rate Limited Users**: Unique users receiving 429 (track trends)
3. **Rate Limited Endpoints**: Which endpoints most frequently limited
4. **Admin Bypass Usage**: Admin request rates (detect abuse)
5. **Redis Health**: Connection status, latency, memory usage

## Weekly Review Checklist

- [ ] Review rate limit hit rate trend
- [ ] Analyze top 20 rate-limited users
- [ ] Review rate-limited endpoints
- [ ] Check Redis health and performance
- [ ] Review admin account activity
- [ ] Adjust limits if needed
- [ ] Document any changes

## Contact

For rate limiting issues:
- **On-call engineer**: Check PagerDuty
- **Documentation**: `/docs/monitoring/rate-limiting-monitoring.md`
- **Code**: `apps/backend/infrastructure/rate_limit_middleware.py`
