# Rate Limiting Monitoring Documentation

This directory contains comprehensive documentation for monitoring rate limiting effectiveness in production.

## Quick Start

1. **For Operators**: Start with [Quick Reference Guide](./rate-limiting-quick-reference.md)
2. **For Setup**: Read the [Full Monitoring Guide](./rate-limiting-monitoring.md)
3. **For Dashboards**: Import [Grafana Dashboard](../../infra/monitoring/grafana-rate-limiting-dashboard.json)
4. **For Alerts**: Configure [Alert Rules](../../infra/monitoring/rate-limiting-alerts.yaml)

## Documentation Files

### [rate-limiting-monitoring.md](./rate-limiting-monitoring.md)
**Comprehensive monitoring guide** covering:
- Current implementation overview
- Rate limit events logged
- Monitoring strategies (log-based, metrics, dashboards, alerts)
- Response headers
- Production monitoring checklist
- Analyzing rate limit effectiveness
- Troubleshooting common issues
- Configuration and best practices

**Use this for**: Understanding the complete monitoring system and setting up production monitoring.

### [rate-limiting-quick-reference.md](./rate-limiting-quick-reference.md)
**Quick reference guide** for operators covering:
- Quick status checks
- Key log patterns
- Common queries
- Alert thresholds
- Troubleshooting steps
- Emergency response procedures

**Use this for**: Day-to-day operations and incident response.

### [grafana-rate-limiting-dashboard.json](../../infra/monitoring/grafana-rate-limiting-dashboard.json)
**Grafana dashboard configuration** including:
- Rate limit hit rate
- 429 response tracking
- Top rate-limited users and endpoints
- Redis health monitoring
- Admin activity tracking
- Performance metrics

**Use this for**: Importing into Grafana for visual monitoring.

### [rate-limiting-alerts.yaml](../../infra/monitoring/rate-limiting-alerts.yaml)
**Alert rules configuration** including:
- Critical alerts (Redis down, high hit rate)
- Warning alerts (elevated rate limiting, suspicious admin activity)
- Info alerts (pattern changes, frequently limited endpoints)
- Alert routing and notification configuration

**Use this for**: Configuring Prometheus Alertmanager or similar alerting systems.

## Implementation Status

✅ **Logging**: All rate limit events are logged with structured data
- Rate limit exceeded events (429 responses)
- User ID, endpoint, method, limit, retry_after
- Admin bypass events (implicit through absence of warnings)
- Redis connection failures

✅ **Response Headers**: Standard rate limit headers on all responses
- X-RateLimit-Limit
- X-RateLimit-Remaining
- X-RateLimit-Reset
- Retry-After (on 429 responses)

✅ **Middleware**: Rate limiting enforced on all requests
- Per-user rate limiting (100 req/min default)
- Global rate limiting (10,000 req/min default)
- Admin bypass capability
- Health check exemption

✅ **Redis Integration**: Distributed rate limiting with Redis
- Sliding window algorithm
- Automatic cleanup of old entries
- Fail-open on Redis failures (logged)

## Setup Instructions

### 1. Verify Logging

Check that rate limit events are being logged:

```bash
# Test rate limiting
for i in {1..105}; do
  curl -H "Authorization: Bearer YOUR_TOKEN" \
       http://localhost:8000/api/stories
done

# Check logs
grep "Rate limit exceeded" /var/log/app.log
```

### 2. Set Up Centralized Logging

Configure log aggregation (choose one):
- **ELK Stack**: Elasticsearch, Logstash, Kibana
- **Splunk**: Enterprise log management
- **CloudWatch**: AWS native logging
- **Datadog**: Unified monitoring platform

### 3. Import Grafana Dashboard

```bash
# Import dashboard JSON
curl -X POST http://grafana:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_GRAFANA_API_KEY" \
  -d @grafana-rate-limiting-dashboard.json
```

### 4. Configure Alerts

```bash
# For Prometheus Alertmanager
cp rate-limiting-alerts.yaml /etc/prometheus/alerts/

# Reload Prometheus
curl -X POST http://prometheus:9090/-/reload
```

### 5. Test Alerts

```bash
# Trigger rate limit alert (send many requests)
for i in {1..200}; do
  curl http://localhost:8000/api/stories &
done

# Check if alert fired
curl http://alertmanager:9093/api/v2/alerts
```

## Key Metrics

| Metric | Target | Alert Threshold | Severity |
|--------|--------|-----------------|----------|
| Rate Limit Hit Rate | < 1% | > 10% for 5min | Critical |
| Redis Uptime | 100% | < 100% | Critical |
| Rate Limited Users | < 10/hour | > 50/hour | Warning |
| Redis P95 Latency | < 10ms | > 100ms | Warning |
| Admin Request Rate | < 100/min | > 1000/min | Warning |

## Common Scenarios

### Scenario 1: DDoS Attack
**Symptoms**: Sudden spike in rate limit events, many unique IPs
**Response**: 
1. Check [Quick Reference](./rate-limiting-quick-reference.md#problem-high-rate-limit-hit-rate)
2. Review top rate-limited IPs
3. Block malicious IPs at firewall/WAF level
4. Consider temporary limit increase for legitimate users

### Scenario 2: Redis Failure
**Symptoms**: "Redis error" in logs, rate limiting disabled
**Response**:
1. Check [Quick Reference](./rate-limiting-quick-reference.md#problem-redis-connection-failures)
2. Verify Redis status
3. Restart Redis if needed
4. Monitor for recovery

### Scenario 3: Legitimate Users Rate Limited
**Symptoms**: User complaints, high rate limit hit rate, legitimate traffic
**Response**:
1. Review rate limit configuration
2. Analyze request patterns
3. Increase limits if appropriate
4. Consider per-endpoint limits

## Weekly Review Process

Follow this checklist weekly:

- [ ] Review rate limit hit rate trend
- [ ] Analyze top 20 rate-limited users
- [ ] Review rate-limited endpoints
- [ ] Check Redis health and performance
- [ ] Review admin account activity
- [ ] Adjust limits if needed
- [ ] Document any changes
- [ ] Update runbooks if needed

## Troubleshooting

For troubleshooting guidance, see:
- [Full Monitoring Guide - Troubleshooting Section](./rate-limiting-monitoring.md#troubleshooting)
- [Quick Reference - Troubleshooting](./rate-limiting-quick-reference.md#troubleshooting)

## Additional Resources

- **Implementation**: `apps/backend/infrastructure/rate_limit_middleware.py`
- **Rate Limiter**: `apps/backend/infrastructure/rate_limiter.py`
- **Configuration**: `apps/backend/config/settings.py`
- **Production readiness review**: `docs/operations/PRODUCTION_READINESS_REVIEW.md`
- **Deployment checklist**: `docs/deployment/checklist.md`

## Support

For issues or questions:
- **On-call**: Check PagerDuty for current on-call engineer
- **Team**: #engineering-ops Slack channel
- **Documentation**: This directory
- **Code**: `apps/backend/infrastructure/`

## Contributing

When updating rate limiting monitoring:
1. Update relevant documentation files
2. Test changes in staging
3. Update dashboard/alerts if needed
4. Document changes in this README
5. Notify team of changes
