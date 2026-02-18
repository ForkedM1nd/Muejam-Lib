# Database Connection Pooling Implementation

## Overview

This document describes the database connection pooling implementation for the MueJam Library backend. Connection pooling is critical for production readiness, preventing connection exhaustion under load.

## Problem Statement

Without connection pooling, Django creates a new database connection for every request, which causes:
- Connection exhaustion at ~50-100 concurrent users
- "too many connections" errors from PostgreSQL
- Poor performance due to connection overhead
- Service unavailability under load

## Solution

We implemented a two-tier connection pooling strategy:

### 1. Django Built-in Connection Pooling (CONN_MAX_AGE)

Django's `CONN_MAX_AGE` setting keeps database connections alive between requests, reusing them instead of creating new ones.

**Configuration:**
- `CONN_MAX_AGE = 600` (10 minutes)
- `connect_timeout = 10` seconds
- `statement_timeout = 30000` milliseconds (30 seconds)

**Benefits:**
- Simple to configure
- No additional infrastructure required
- Suitable for moderate load (< 500 concurrent users)

### 2. PgBouncer Connection Pooling (Optional)

For high-scale production deployments, we've added pgbouncer as an optional connection pooler.

**Configuration:**
- Pool mode: `transaction` (best for Django)
- Max client connections: 1000
- Default pool size: 25 connections per database
- Min pool size: 10 connections
- Reserve pool: 5 connections

**Benefits:**
- Handles thousands of concurrent connections
- Reduces PostgreSQL connection overhead
- Better resource utilization
- Suitable for high load (> 500 concurrent users)

## Implementation Details

### Files Created

1. **`config/database.py`**
   - `get_database_config()`: Returns Django database configuration with connection pooling
   - `get_pgbouncer_config()`: Returns configuration for pgbouncer connection
   - `should_use_pgbouncer()`: Determines which pooling strategy to use
   - `get_database_settings()`: Main entry point for database configuration

2. **`infrastructure/connection_pool_monitor.py`**
   - `ConnectionPoolMonitor`: Monitors connection pool health and statistics
   - `ConnectionPoolStats`: Data class for pool metrics
   - `get_connection_pool_health()`: Convenience function for health checks
   - `print_connection_pool_report()`: Detailed reporting function

3. **`infrastructure/management/commands/monitor_connection_pool.py`**
   - Django management command for monitoring
   - Supports continuous monitoring with `--watch`
   - JSON output with `--json`

4. **`tests/test_connection_pooling.py`**
   - Comprehensive test suite
   - Tests configuration, concurrent load, and recovery
   - Includes benchmark tests

5. **`docker-compose.yml`** (updated)
   - Added pgbouncer service
   - Configured with optimal settings
   - Health checks enabled

### Configuration

#### Environment Variables

**Basic Configuration (Django CONN_MAX_AGE):**
```bash
DATABASE_URL=postgresql://user:password@host:5432/database
DB_CONN_MAX_AGE=600  # seconds (default: 600)
DB_CONNECT_TIMEOUT=10  # seconds (default: 10)
DB_STATEMENT_TIMEOUT=30000  # milliseconds (default: 30000)
```

**PgBouncer Configuration (Optional):**
```bash
USE_PGBOUNCER=true
PGBOUNCER_URL=postgresql://user:password@pgbouncer:6432/database
# Or individual settings:
PGBOUNCER_HOST=localhost
PGBOUNCER_PORT=6432
```

#### Django Settings

The `settings.py` file now uses the centralized database configuration:

```python
from config.database import get_database_settings

DATABASES = get_database_settings()
```

This automatically:
- Parses `DATABASE_URL` or falls back to individual env vars
- Configures `CONN_MAX_AGE` for connection pooling
- Sets connection and query timeouts
- Switches to pgbouncer if `USE_PGBOUNCER=true`

## Usage

### Running Tests

```bash
# Run all connection pooling tests
python -m pytest tests/test_connection_pooling.py -v

# Run only configuration tests
python -m pytest tests/test_connection_pooling.py::ConnectionPoolingTestCase -v

# Run concurrent load tests
python -m pytest tests/test_connection_pooling.py::ConcurrentConnectionTestCase -v

# Run benchmark tests (not run by default)
python -m pytest tests/test_connection_pooling.py -v -m benchmark
```

### Monitoring Connection Pool

```bash
# Single report
python manage.py monitor_connection_pool

# Continuous monitoring (refresh every 5 seconds)
python manage.py monitor_connection_pool --watch

# Custom refresh interval
python manage.py monitor_connection_pool --watch --interval 10

# JSON output (for automation)
python manage.py monitor_connection_pool --json
```

### Example Monitoring Output

```
======================================================================
CONNECTION POOL HEALTH REPORT
======================================================================

Status: HEALTHY
Timestamp: 2026-02-18T14:29:39.099345

Database: muejam
Connection Max Age: 600s
Active Connections: 15/100
Utilization: 15.0%
Backend PID: 21180
Connection Age: 45.2s

Query Statistics:
  Total Queries: 1523
  Errors: 0
  Avg Query Time: 12.3ms

✓ No alerts

Active Connections:
  PID 21180: active (age: 45s, user: muejam_user)
  PID 21181: idle (age: 120s, user: muejam_user)
  ... and 13 more

======================================================================
```

## Performance Impact

### Before Connection Pooling
- New connection per request: ~50-100ms overhead
- Connection limit: ~100 concurrent users
- Failure mode: "too many connections" errors

### After Connection Pooling (CONN_MAX_AGE)
- Connection reuse: ~1-5ms overhead
- Connection limit: ~500 concurrent users
- Failure mode: Graceful degradation

### With PgBouncer
- Connection reuse: ~1-2ms overhead
- Connection limit: ~5000+ concurrent users
- Failure mode: Queue requests, graceful degradation

## Monitoring and Alerts

The connection pool monitor tracks:

1. **Utilization**: Active connections / Max connections
   - Warning: > 80% utilization
   - Critical: > 95% utilization

2. **Connection Age**: How long connections have been alive
   - Helps identify connection leaks

3. **Query Statistics**: Total queries, errors, average query time
   - Helps identify performance issues

4. **Idle Connections**: Connections idle > 5 minutes
   - Helps optimize pool size

## Troubleshooting

### Issue: "too many connections" error

**Cause**: Connection pool exhausted or PostgreSQL max_connections reached

**Solutions:**
1. Check current utilization: `python manage.py monitor_connection_pool`
2. Increase PostgreSQL `max_connections` setting
3. Enable pgbouncer: `USE_PGBOUNCER=true`
4. Reduce `CONN_MAX_AGE` to recycle connections faster

### Issue: High connection pool utilization

**Cause**: More concurrent requests than available connections

**Solutions:**
1. Enable pgbouncer for better pooling
2. Increase pgbouncer `DEFAULT_POOL_SIZE`
3. Add more application instances (horizontal scaling)
4. Optimize slow queries to free connections faster

### Issue: Connection timeouts

**Cause**: Database unreachable or slow to respond

**Solutions:**
1. Check database health
2. Increase `DB_CONNECT_TIMEOUT` if network is slow
3. Check for network issues between app and database
4. Verify database is not overloaded

### Issue: Query timeouts

**Cause**: Long-running queries exceeding statement_timeout

**Solutions:**
1. Optimize slow queries (add indexes, rewrite queries)
2. Increase `DB_STATEMENT_TIMEOUT` if queries legitimately need more time
3. Use async tasks for long-running operations
4. Check for missing indexes: `python manage.py create_indexes`

## Production Deployment

### Recommended Configuration

**Small Scale (< 100 concurrent users):**
```bash
DATABASE_URL=postgresql://user:password@host:5432/database
DB_CONN_MAX_AGE=600
```

**Medium Scale (100-500 concurrent users):**
```bash
DATABASE_URL=postgresql://user:password@host:5432/database
DB_CONN_MAX_AGE=600
# Increase PostgreSQL max_connections to 200
```

**Large Scale (> 500 concurrent users):**
```bash
USE_PGBOUNCER=true
PGBOUNCER_URL=postgresql://user:password@pgbouncer:6432/database
# PgBouncer handles pooling, can support 1000+ concurrent users
```

### Docker Deployment

The `docker-compose.yml` includes pgbouncer service:

```bash
# Start with pgbouncer
docker-compose up -d

# Backend will connect through pgbouncer on port 6432
# Set USE_PGBOUNCER=true in .env
```

### Kubernetes Deployment

For Kubernetes, deploy pgbouncer as a sidecar container or separate service:

```yaml
# Example sidecar configuration
containers:
- name: app
  image: muejam-backend
  env:
  - name: USE_PGBOUNCER
    value: "true"
  - name: PGBOUNCER_HOST
    value: "localhost"
  - name: PGBOUNCER_PORT
    value: "6432"

- name: pgbouncer
  image: pgbouncer/pgbouncer:latest
  env:
  - name: DATABASES_HOST
    value: "postgres.database.svc.cluster.local"
  - name: DEFAULT_POOL_SIZE
    value: "25"
```

## Testing Under Load

To verify connection pooling works under load:

```bash
# Run concurrent connection tests
python -m pytest tests/test_connection_pooling.py::ConcurrentConnectionTestCase -v

# Run load test with 50 concurrent threads
python -m pytest tests/test_connection_pooling.py::ConcurrentConnectionTestCase::test_concurrent_queries_50_threads -v

# Monitor during load test (in another terminal)
python manage.py monitor_connection_pool --watch
```

## Metrics to Monitor in Production

1. **Connection Pool Utilization**
   - Target: < 80%
   - Alert: > 80%
   - Critical: > 95%

2. **Average Query Time**
   - Target: < 50ms
   - Alert: > 100ms
   - Critical: > 500ms

3. **Connection Errors**
   - Target: 0
   - Alert: > 1% error rate
   - Critical: > 5% error rate

4. **Idle Connections**
   - Target: < 20% of pool
   - Alert: > 50% idle
   - Action: Reduce pool size

## References

- [Django Database Connection Management](https://docs.djangoproject.com/en/5.0/ref/databases/#connection-management)
- [PostgreSQL Connection Pooling](https://www.postgresql.org/docs/current/runtime-config-connection.html)
- [PgBouncer Documentation](https://www.pgbouncer.org/config.html)
- Production Readiness Audit - Requirements Document
- Production Readiness Audit - Design Document

## Changelog

### 2026-02-18 - Initial Implementation
- Implemented Django CONN_MAX_AGE connection pooling
- Added pgbouncer configuration to docker-compose.yml
- Created connection pool monitoring tools
- Added comprehensive test suite
- Documented configuration and usage

## Support

For issues or questions about connection pooling:
1. Check monitoring: `python manage.py monitor_connection_pool`
2. Review logs for connection errors
3. Consult this documentation
4. Contact DevOps team for production issues
