# Load Testing Quick Start

## Installation

```bash
pip install locust
```

## Quick Test (5 minutes)

```bash
cd apps/backend/tests/load_tests
locust -f locustfile.py --host=http://localhost:8000 --users 100 --spawn-rate 10 --run-time 5m --headless
```

## Interactive Mode (with Web UI)

```bash
locust -f locustfile.py --host=http://localhost:8000
```

Then open http://localhost:8089 in your browser.

## Run All Tests

```bash
chmod +x run_tests.sh
./run_tests.sh
```

## Test Scenarios

### 1. Basic Load Test
Tests normal traffic with mixed user types (authenticated, unauthenticated, writers).

```bash
locust -f locustfile.py --host=http://localhost:8000 --users 100 --spawn-rate 10 --run-time 5m --headless
```

### 2. Rate Limiting Test
Tests rate limiting with rapid requests.

```bash
locust -f scenarios.py --host=http://localhost:8000 --users 50 --spawn-rate 25 --run-time 3m --headless --user-classes RateLimitTestUser
```

### 3. Database Stress Test
Tests database connection pooling and query performance.

```bash
locust -f scenarios.py --host=http://localhost:8000 --users 100 --spawn-rate 20 --run-time 5m --headless --user-classes DatabaseStressUser
```

### 4. Cache Performance Test
Tests caching behavior and cache hit rates.

```bash
locust -f scenarios.py --host=http://localhost:8000 --users 75 --spawn-rate 15 --run-time 5m --headless --user-classes CacheTestUser
```

### 5. Write-Heavy Test
Tests write operations (creates, updates).

```bash
locust -f scenarios.py --host=http://localhost:8000 --users 50 --spawn-rate 10 --run-time 5m --headless --user-classes WriteHeavyUser
```

### 6. Peak Load Test
Tests system under peak load (1000 users).

```bash
locust -f locustfile.py --host=http://localhost:8000 --users 1000 --spawn-rate 50 --run-time 10m --headless
```

## Before Running Tests

1. **Start the application**:
   ```bash
   python apps/backend/manage.py runserver 0.0.0.0:8000
   ```

2. **Ensure services are running**:
   ```bash
   docker-compose up -d postgres redis
   ```

3. **Set up test authentication** (see README.md for details)

## Monitoring During Tests

### Watch application logs:
```bash
tail -f apps/backend/logs/muejam.log
```

### Monitor database connections:
```bash
# PostgreSQL
docker exec -it <postgres-container> psql -U muejam_user -d muejam -c "SELECT count(*) FROM pg_stat_activity;"
```

### Monitor Redis:
```bash
docker exec -it <redis-container> redis-cli INFO stats
```

## Interpreting Results

### Success Criteria
- P95 latency < 500ms
- P99 latency < 1000ms
- Error rate < 1%
- Rate limiting working (429 responses)

### Common Issues
- High latency → Check for N+1 queries, missing indexes
- Connection errors → Check connection pool size
- Timeouts → Check slow queries, increase timeout values
- High error rate → Check application logs

## Next Steps

After running tests:
1. Review HTML reports in `load_test_results/`
2. Document capacity limits in `docs/operations/capacity-planning.md`
3. Identify and fix bottlenecks
4. Re-run tests to validate improvements

## Help

For detailed documentation, see:
- `README.md` - Comprehensive guide
- `scenarios.py` - Specific test scenarios
- `docs/operations/capacity-planning.md` - Capacity planning
