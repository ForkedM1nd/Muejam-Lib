# Load Testing Guide

This directory contains load testing scenarios for the MueJam API using [Locust](https://locust.io/).

## Prerequisites

Install Locust:
```bash
pip install locust
```

## Test Scenarios

### 1. Basic Load Test (100 concurrent users)
Tests normal traffic patterns with authenticated and unauthenticated users.

```bash
locust -f locustfile.py --host=http://localhost:8000 --users 100 --spawn-rate 10 --run-time 5m
```

**Expected Results**:
- P95 latency < 500ms
- P99 latency < 1000ms
- Error rate < 1%
- Rate limiting working (429 responses)

### 2. Peak Load Test (1000 concurrent users)
Tests system behavior under peak load.

```bash
locust -f locustfile.py --host=http://localhost:8000 --users 1000 --spawn-rate 50 --run-time 10m
```

**Expected Results**:
- P95 latency < 1000ms
- P99 latency < 2000ms
- Error rate < 5%
- Graceful degradation under load

### 3. Sustained Load Test
Tests system stability over extended period.

```bash
locust -f locustfile.py --host=http://localhost:8000 --users 200 --spawn-rate 20 --run-time 30m
```

**Expected Results**:
- No memory leaks
- Stable performance over time
- Connection pool stable
- No resource exhaustion

### 4. Spike Test
Tests system recovery from sudden traffic spike.

```bash
# Start with low load
locust -f locustfile.py --host=http://localhost:8000 --users 50 --spawn-rate 10 --run-time 2m

# Then spike to high load
locust -f locustfile.py --host=http://localhost:8000 --users 500 --spawn-rate 100 --run-time 3m

# Then back to normal
locust -f locustfile.py --host=http://localhost:8000 --users 100 --spawn-rate 20 --run-time 5m
```

**Expected Results**:
- System handles spike without crashing
- Quick recovery to normal performance
- Rate limiting protects system

## User Types

### AuthenticatedUser (70% of traffic)
Simulates logged-in users performing typical actions:
- Browse discovery feed (10x weight)
- View stories (8x weight)
- View profile (5x weight)
- Browse library (3x weight)
- Search (2x weight)
- Create whispers (1x weight)

### UnauthenticatedUser (25% of traffic)
Simulates visitors browsing public content:
- Browse public stories (10x weight)
- View public story (5x weight)
- Search public content (2x weight)

### WriterUser (4% of traffic)
Simulates content creators:
- Create stories (5x weight)
- Update stories (3x weight)
- View own stories (2x weight)

### HealthCheckUser (1% of traffic)
Simulates load balancer health checks:
- Health check endpoint
- Readiness check endpoint

## Running Tests

### Interactive Mode (with Web UI)
```bash
locust -f locustfile.py --host=http://localhost:8000
```
Then open http://localhost:8089 in your browser.

### Headless Mode (for CI/CD)
```bash
locust -f locustfile.py \
  --host=http://localhost:8000 \
  --users 100 \
  --spawn-rate 10 \
  --run-time 5m \
  --headless \
  --html report.html \
  --csv results
```

### Distributed Mode (multiple workers)
Master:
```bash
locust -f locustfile.py --host=http://localhost:8000 --master
```

Workers (run on multiple machines):
```bash
locust -f locustfile.py --worker --master-host=<master-ip>
```

## Monitoring During Tests

### Key Metrics to Watch

1. **Application Metrics**:
   - Request latency (P50, P95, P99)
   - Error rate
   - Throughput (requests/second)
   - Rate limit hits (429 responses)

2. **Database Metrics**:
   - Connection pool utilization
   - Query latency
   - Slow queries
   - Connection errors

3. **System Metrics**:
   - CPU usage
   - Memory usage
   - Network I/O
   - Disk I/O

4. **Cache Metrics**:
   - Cache hit rate
   - Cache memory usage
   - Eviction rate

### Monitoring Commands

Check database connections:
```bash
# PostgreSQL
SELECT count(*) FROM pg_stat_activity;
SELECT state, count(*) FROM pg_stat_activity GROUP BY state;
```

Check Redis:
```bash
redis-cli INFO stats
redis-cli INFO memory
```

Check application logs:
```bash
tail -f apps/backend/logs/muejam.log | grep -E "(ERROR|WARNING|timeout|rate_limit)"
```

## Interpreting Results

### Success Criteria

| Metric | Target | Acceptable | Failure |
|--------|--------|------------|---------|
| P95 Latency | < 500ms | < 1000ms | > 1000ms |
| P99 Latency | < 1000ms | < 2000ms | > 2000ms |
| Error Rate | < 0.5% | < 2% | > 5% |
| Throughput | > 100 RPS | > 50 RPS | < 50 RPS |

### Common Issues

1. **High Latency**:
   - Check for N+1 queries
   - Check database connection pool
   - Check cache hit rate
   - Check slow query log

2. **High Error Rate**:
   - Check application logs
   - Check database errors
   - Check timeout errors
   - Check rate limiting

3. **Connection Errors**:
   - Check connection pool size
   - Check max connections
   - Check connection timeouts
   - Check network issues

4. **Memory Issues**:
   - Check for memory leaks
   - Check cache size
   - Check connection pool
   - Check worker processes

## Test Environment Setup

### Local Testing
```bash
# Start services
docker-compose up -d postgres redis

# Run migrations
python apps/backend/manage.py migrate

# Start application
python apps/backend/manage.py runserver 0.0.0.0:8000

# In another terminal, run load tests
locust -f tests/load_tests/locustfile.py --host=http://localhost:8000
```

### Staging Testing
```bash
# Point to staging environment
locust -f locustfile.py --host=https://staging.muejam.com --users 100 --spawn-rate 10
```

## Authentication Setup

For realistic load testing, you need valid JWT tokens:

1. **Option 1: Test Tokens**
   - Create test users in Clerk
   - Generate JWT tokens for each test user
   - Store tokens in environment variables or config file

2. **Option 2: Mock Authentication**
   - Set up test endpoint that bypasses auth
   - Use only in test environment
   - Never deploy to production

3. **Option 3: Token Generation**
   - Implement token generation in test setup
   - Use Clerk API to generate tokens
   - Rotate tokens during test

## Capacity Planning

Based on load test results, document:

1. **Current Capacity**:
   - Max concurrent users: ___
   - Max requests/second: ___
   - Breaking point: ___

2. **Bottlenecks**:
   - Database: ___
   - Cache: ___
   - Application: ___
   - Network: ___

3. **Scaling Strategy**:
   - Horizontal scaling: ___
   - Vertical scaling: ___
   - Database scaling: ___
   - Cache scaling: ___

## Continuous Load Testing

Integrate load tests into CI/CD:

```yaml
# .github/workflows/load-test.yml
name: Load Test
on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:

jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Install dependencies
        run: pip install locust
      - name: Run load test
        run: |
          locust -f tests/load_tests/locustfile.py \
            --host=${{ secrets.STAGING_URL }} \
            --users 100 \
            --spawn-rate 10 \
            --run-time 5m \
            --headless \
            --html report.html
      - name: Upload results
        uses: actions/upload-artifact@v2
        with:
          name: load-test-results
          path: report.html
```

## Troubleshooting

### Locust Issues

**Problem**: Locust workers disconnecting
**Solution**: Increase worker timeout, check network stability

**Problem**: High CPU on Locust master
**Solution**: Use more workers, reduce spawn rate

**Problem**: SSL certificate errors
**Solution**: Use `--insecure` flag for self-signed certs (test only)

### Application Issues

**Problem**: Connection pool exhausted
**Solution**: Increase pool size, check for connection leaks

**Problem**: Rate limiting too aggressive
**Solution**: Adjust rate limits, add user tiers

**Problem**: Timeouts under load
**Solution**: Optimize queries, increase timeout values, add caching

## Next Steps

After load testing:

1. Document capacity limits
2. Identify and fix bottlenecks
3. Implement auto-scaling
4. Set up monitoring alerts
5. Create runbooks for incidents
6. Plan for growth
