# Deployment Verification Guide

This guide provides procedures for verifying deployments and ensuring system health.

## Pre-Deployment Verification

Before deploying to any environment, verify:

### 1. Code Quality

```bash
# Run linters
cd apps/backend
flake8 apps/
black --check apps/

cd apps/frontend
npm run lint
```

### 2. Test Suite

```bash
# Backend tests
cd apps/backend
python -m pytest --cov=apps --cov-report=term-missing

# Frontend tests
cd apps/frontend
npm test -- --coverage
```

### 3. Build Verification

```bash
# Backend build
cd apps/backend
python manage.py check
python manage.py collectstatic --noinput --dry-run

# Frontend build
cd apps/frontend
npm run build
```

### 4. Security Scan

```bash
# Check for known vulnerabilities
cd apps/backend
pip-audit

cd apps/frontend
npm audit
```

## Post-Deployment Verification

After deploying to an environment, verify:

### 1. Health Checks

```bash
# Check application health
curl https://api.muejam.com/health

# Expected response:
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.2.0",
  "services": {
    "database": "healthy",
    "cache": "healthy",
    "storage": "healthy"
  }
}
```

### 2. Smoke Tests

Run automated smoke tests:

```bash
./scripts/deployment/smoke-tests.sh production
```

Smoke tests verify:
- API endpoints respond
- Authentication works
- Database connectivity
- Cache connectivity
- File uploads work
- Critical user flows

### 3. Database Migrations

```bash
# Verify migrations applied
python manage.py showmigrations

# Check for pending migrations
python manage.py migrate --check
```

### 4. Static Files

```bash
# Verify static files served correctly
curl https://muejam.com/static/css/main.css
curl https://muejam.com/favicon.ico
```

### 5. API Endpoints

Test critical endpoints:

```bash
# Health check
curl https://api.muejam.com/health

# Authentication
curl -X POST https://api.muejam.com/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test"}'

# User profile
curl https://api.muejam.com/api/users/me/ \
  -H "Authorization: Bearer $TOKEN"
```

### 6. Performance Metrics

```bash
# Check response times
./scripts/deployment/check-latency.sh production

# Check error rates
./scripts/deployment/check-error-rate.sh production
```

Expected metrics:
- Response time (p95): < 500ms
- Response time (p99): < 1000ms
- Error rate: < 0.1%

### 7. Monitoring and Alerts

Verify monitoring systems:

```bash
# Check Sentry
curl https://sentry.io/api/0/projects/muejam/muejam-backend/issues/

# Check New Relic
curl https://api.newrelic.com/v2/applications/$APP_ID.json \
  -H "X-Api-Key: $NEW_RELIC_API_KEY"
```

## Verification Checklist

### Staging Environment

- [ ] All tests pass
- [ ] Build succeeds
- [ ] Health check returns healthy
- [ ] Database migrations applied
- [ ] Static files accessible
- [ ] API endpoints respond correctly
- [ ] Authentication works
- [ ] File uploads work
- [ ] Email sending works
- [ ] Background jobs run
- [ ] Monitoring active
- [ ] Logs flowing correctly

### Production Environment

All staging checks plus:

- [ ] SSL certificate valid
- [ ] CDN serving content
- [ ] Auto-scaling configured
- [ ] Backups running
- [ ] Alerts configured
- [ ] Rate limiting active
- [ ] Security headers present
- [ ] CORS configured correctly
- [ ] Performance acceptable
- [ ] No errors in logs

## Automated Verification Script

Use the verification script:

```bash
# Run all verification checks
python scripts/verification/verify-restructure.py

# Run specific checks
python scripts/verification/verify-restructure.py --checks health,api,database
```

The script verifies:
- Directory structure
- File movements
- Import paths
- Configuration files
- Test discovery
- Django check
- API health

## Manual Testing

### Critical User Flows

Test these flows manually after deployment:

1. **User Registration**:
   - Register new account
   - Receive verification email
   - Verify email
   - Complete profile

2. **Authentication**:
   - Log in
   - Log out
   - Password reset
   - 2FA (if enabled)

3. **Content Creation**:
   - Create story
   - Upload image
   - Publish story
   - View published story

4. **Social Features**:
   - Follow user
   - Like content
   - Comment on content
   - Receive notification

5. **Moderation**:
   - Report content
   - Moderator review
   - Content action (approve/remove)

### Browser Testing

Test on multiple browsers:
- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

### Device Testing

Test on multiple devices:
- Desktop (1920x1080)
- Laptop (1366x768)
- Tablet (iPad)
- Mobile (iPhone, Android)

## Performance Testing

### Load Testing

```bash
# Run load test
locust -f tests/load/locustfile.py \
  --host https://api.muejam.com \
  --users 100 \
  --spawn-rate 10 \
  --run-time 5m
```

Monitor:
- Response times
- Error rates
- Resource utilization
- Database performance

### Stress Testing

```bash
# Gradually increase load
locust -f tests/load/locustfile.py \
  --host https://api.muejam.com \
  --users 1000 \
  --spawn-rate 50 \
  --run-time 10m
```

Identify:
- Breaking point
- Bottlenecks
- Resource limits
- Recovery behavior

## Rollback Verification

If rollback is needed:

```bash
# Perform rollback
./scripts/deployment/rollback.sh production

# Verify rollback
./scripts/deployment/smoke-tests.sh production

# Check version
curl https://api.muejam.com/health | jq .version
```

## Monitoring After Deployment

Monitor for 24 hours after deployment:

### Metrics to Watch

- **Error Rate**: Should remain < 0.1%
- **Response Time**: Should remain < 500ms (p95)
- **CPU Usage**: Should remain < 70%
- **Memory Usage**: Should remain < 80%
- **Database Connections**: Should not max out
- **Cache Hit Rate**: Should remain > 80%

### Alerts to Monitor

- Critical errors in Sentry
- Performance degradation in New Relic
- Infrastructure alerts in CloudWatch
- User-reported issues

### Log Analysis

```bash
# Check for errors
aws logs tail /aws/ecs/muejam-backend --follow --filter-pattern "ERROR"

# Check for slow queries
aws logs tail /aws/ecs/muejam-backend --follow --filter-pattern "slow_query"

# Check for rate limit hits
aws logs tail /aws/ecs/muejam-backend --follow --filter-pattern "rate_limit"
```

## Troubleshooting

### Deployment Failed

1. Check CI/CD logs
2. Verify Docker images built
3. Check ECS task status
4. Review CloudWatch logs
5. Verify environment variables
6. Check IAM permissions

### Health Check Failing

1. Check application logs
2. Verify database connectivity
3. Check cache connectivity
4. Verify environment variables
5. Check security groups
6. Review recent changes

### High Error Rate

1. Check Sentry for error details
2. Review application logs
3. Check database performance
4. Verify external service status
5. Check rate limiting
6. Review recent deployments

### Slow Response Times

1. Check New Relic APM
2. Review database query performance
3. Check cache hit rate
4. Verify CDN working
5. Check resource utilization
6. Review recent code changes

## Resources

- [Smoke Tests Script](../../scripts/deployment/smoke-tests.sh)
- [Verification Script](../../scripts/verification/verify-restructure.py)
- [Deployment Guide](../deployment/migration-guide.md)
- [Troubleshooting Guide](../development/troubleshooting.md)
