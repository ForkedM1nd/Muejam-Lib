# Connection Pool Tuning Guide

This guide provides detailed instructions for tuning connection pool parameters to optimize performance and resource utilization.

## Table of Contents

1. [Overview](#overview)
2. [Connection Pool Parameters](#connection-pool-parameters)
3. [Sizing Guidelines](#sizing-guidelines)
4. [Performance Tuning](#performance-tuning)
5. [Monitoring and Metrics](#monitoring-and-metrics)
6. [Common Scenarios](#common-scenarios)
7. [Troubleshooting](#troubleshooting)

## Overview

Connection pooling is critical for database performance. Proper tuning ensures:

- Efficient resource utilization
- Optimal query throughput
- Minimal connection overhead
- Stable performance under load

## Connection Pool Parameters

### Min Connections

**Parameter**: `min_connections`  
**Default**: 10  
**Range**: 5-20

Minimum number of connections maintained in the pool.

**Considerations**:
- Higher values reduce connection establishment overhead
- Lower values conserve database resources
- Should be based on baseline load

**Tuning**:
```python
CONNECTION_POOL_CONFIG = {
    'min_connections': 10,  # Default
}

# Low-traffic application
CONNECTION_POOL_CONFIG = {
    'min_connections': 5,
}

# High-traffic application
CONNECTION_POOL_CONFIG = {
    'min_connections': 20,
}
```

### Max Connections

**Parameter**: `max_connections`  
**Default**: 50  
**Range**: 20-200

Maximum number of connections allowed in the pool.

**Considerations**:
- Must be less than PostgreSQL `max_connections`
- Higher values support more concurrent requests
- Too high can overwhelm database
- Formula: `max_connections = (concurrent_requests * 1.2) / num_app_servers`

**Tuning**:
```python
# Calculate based on load
concurrent_requests = 100
num_app_servers = 2
max_connections = int((concurrent_requests * 1.2) / num_app_servers)  # 60

CONNECTION_POOL_CONFIG = {
    'max_connections': max_connections,
}
```

### Idle Timeout

**Parameter**: `idle_timeout`  
**Default**: 300 seconds (5 minutes)  
**Range**: 60-600 seconds

Time before idle connections are closed.

**Considerations**:
- Shorter timeouts free resources faster
- Longer timeouts reduce connection churn
- Balance between resource usage and overhead

**Tuning**:
```python
# Aggressive cleanup (high connection churn acceptable)
CONNECTION_POOL_CONFIG = {
    'idle_timeout': 60,
}

# Conservative cleanup (minimize connection overhead)
CONNECTION_POOL_CONFIG = {
    'idle_timeout': 600,
}
```

### Connection Lifetime

**Parameter**: `max_lifetime`  
**Default**: 3600 seconds (1 hour)  
**Range**: 1800-7200 seconds

Maximum lifetime of a connection before forced closure.

**Considerations**:
- Prevents connection leaks
- Ensures fresh connections periodically
- Helps with database maintenance

**Tuning**:
```python
CONNECTION_POOL_CONFIG = {
    'max_lifetime': 3600,  # 1 hour
}
```

## Sizing Guidelines

### Small Application

**Profile**:
- < 1000 requests/minute
- < 10 concurrent users
- Single application server

**Configuration**:
```python
CONNECTION_POOL_CONFIG = {
    'min_connections': 5,
    'max_connections': 20,
    'idle_timeout': 300,
    'max_lifetime': 3600,
}
```

### Medium Application

**Profile**:
- 1000-10000 requests/minute
- 10-100 concurrent users
- 2-4 application servers

**Configuration**:
```python
CONNECTION_POOL_CONFIG = {
    'min_connections': 10,
    'max_connections': 50,
    'idle_timeout': 300,
    'max_lifetime': 3600,
}
```

### Large Application

**Profile**:
- > 10000 requests/minute
- > 100 concurrent users
- 5+ application servers

**Configuration**:
```python
CONNECTION_POOL_CONFIG = {
    'min_connections': 20,
    'max_connections': 100,
    'idle_timeout': 180,
    'max_lifetime': 1800,
}
```

## Performance Tuning

### Read/Write Pool Separation

Separate pools for read and write operations:

```python
CONNECTION_POOL_CONFIG = {
    'write_pool': {
        'min_connections': 10,
        'max_connections': 30,
        'idle_timeout': 300,
    },
    'read_pool': {
        'min_connections': 20,
        'max_connections': 100,
        'idle_timeout': 180,
    },
}
```

**Rationale**:
- Read operations typically outnumber writes (80/20 rule)
- Larger read pool handles query load
- Smaller write pool prevents primary overload

### Connection Acquisition Timeout

Configure timeout for acquiring connections:

```python
CONNECTION_POOL_CONFIG = {
    'acquisition_timeout': 30,  # seconds
}
```

**Tuning**:
- Lower values fail fast under load
- Higher values queue requests longer
- Balance between user experience and resource protection

### Connection Validation

Enable connection validation before use:

```python
CONNECTION_POOL_CONFIG = {
    'validate_on_borrow': True,
    'validation_query': 'SELECT 1',
    'validation_timeout': 5,
}
```

**Impact**:
- Adds small overhead per query
- Prevents using stale connections
- Recommended for production

## Monitoring and Metrics

### Key Metrics

Monitor these metrics via `/metrics/json`:

```json
{
  "connection_pool": {
    "total_connections": 45,
    "active_connections": 32,
    "idle_connections": 13,
    "utilization_percent": 71.1,
    "wait_time_avg_ms": 12.5,
    "connection_errors": 0
  }
}
```

### Utilization Thresholds

**Healthy**: 40-70% utilization  
**Warning**: 70-85% utilization  
**Critical**: > 85% utilization

### Alert Configuration

```yaml
# prometheus/alerts/connection_pool_alerts.yml
- alert: HighConnectionPoolUtilization
  expr: connection_pool_utilization_percent > 80
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Connection pool utilization high"
    description: "Pool utilization is {{ $value }}%"
```

### Grafana Dashboard

Monitor connection pool metrics:

- Total/Active/Idle connections over time
- Utilization percentage
- Average wait time
- Connection errors

## Common Scenarios

### Scenario 1: Pool Exhaustion

**Symptoms**:
- Requests timing out
- High wait times
- 100% pool utilization

**Diagnosis**:
```bash
curl http://localhost:8000/metrics/json | jq '.connection_pool'
```

**Solutions**:

1. **Increase max_connections**:
```python
CONNECTION_POOL_CONFIG = {
    'max_connections': 100,  # Increased from 50
}
```

2. **Optimize slow queries**:
```sql
-- Find slow queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

3. **Add connection timeout**:
```python
DATABASES = {
    'default': {
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c statement_timeout=30000',
        },
    },
}
```

### Scenario 2: Connection Churn

**Symptoms**:
- High connection creation rate
- Increased latency
- Database CPU spikes

**Diagnosis**:
```sql
-- Check connection rate
SELECT count(*) FROM pg_stat_activity WHERE state = 'active';
```

**Solutions**:

1. **Increase min_connections**:
```python
CONNECTION_POOL_CONFIG = {
    'min_connections': 20,  # Increased from 10
}
```

2. **Increase idle_timeout**:
```python
CONNECTION_POOL_CONFIG = {
    'idle_timeout': 600,  # Increased from 300
}
```

3. **Enable connection persistence**:
```python
DATABASES = {
    'default': {
        'CONN_MAX_AGE': 600,  # Keep connections for 10 minutes
    },
}
```

### Scenario 3: Idle Connections

**Symptoms**:
- Many idle connections
- Low utilization
- Wasted database resources

**Diagnosis**:
```sql
-- Check idle connections
SELECT count(*) FROM pg_stat_activity WHERE state = 'idle';
```

**Solutions**:

1. **Decrease min_connections**:
```python
CONNECTION_POOL_CONFIG = {
    'min_connections': 5,  # Decreased from 10
}
```

2. **Decrease idle_timeout**:
```python
CONNECTION_POOL_CONFIG = {
    'idle_timeout': 120,  # Decreased from 300
}
```

3. **Enable aggressive cleanup**:
```python
CONNECTION_POOL_CONFIG = {
    'idle_cleanup_interval': 30,  # Check every 30 seconds
}
```

### Scenario 4: Connection Leaks

**Symptoms**:
- Connections never released
- Gradual pool exhaustion
- Application restarts required

**Diagnosis**:
```python
# Check for long-running transactions
SELECT pid, now() - pg_stat_activity.query_start AS duration, query
FROM pg_stat_activity
WHERE state = 'active'
ORDER BY duration DESC;
```

**Solutions**:

1. **Set max_lifetime**:
```python
CONNECTION_POOL_CONFIG = {
    'max_lifetime': 1800,  # Force close after 30 minutes
}
```

2. **Add statement timeout**:
```python
DATABASES = {
    'default': {
        'OPTIONS': {
            'options': '-c statement_timeout=60000',  # 60 seconds
        },
    },
}
```

3. **Review code for unclosed connections**:
```python
# Bad: Connection not explicitly closed
def bad_query():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    return cursor.fetchall()
    # Connection never closed!

# Good: Use context manager
def good_query():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users")
            return cursor.fetchall()
    # Connection automatically closed
```

## Troubleshooting

### High Wait Times

**Check**:
```bash
curl http://localhost:8000/metrics/json | jq '.connection_pool.wait_time_avg_ms'
```

**If > 50ms**:
1. Increase max_connections
2. Optimize slow queries
3. Add read replicas
4. Review connection acquisition code

### Connection Errors

**Check**:
```bash
curl http://localhost:8000/metrics/json | jq '.connection_pool.connection_errors'
```

**If > 0**:
1. Check database connectivity
2. Verify credentials
3. Check firewall rules
4. Review database logs

### Low Utilization

**Check**:
```bash
curl http://localhost:8000/metrics/json | jq '.connection_pool.utilization_percent'
```

**If < 30%**:
1. Decrease min_connections
2. Decrease max_connections
3. Increase idle_timeout
4. Review application load

## Best Practices

1. **Start Conservative**: Begin with default values and tune based on metrics
2. **Monitor Continuously**: Track pool metrics in production
3. **Load Test**: Test configuration under realistic load
4. **Document Changes**: Record tuning decisions and results
5. **Review Regularly**: Revisit configuration as load patterns change

## Calculation Formulas

### Max Connections

```
max_connections = (peak_concurrent_requests * 1.2) / num_app_servers
```

### Min Connections

```
min_connections = (avg_concurrent_requests * 0.8) / num_app_servers
```

### Idle Timeout

```
idle_timeout = avg_request_interval * 2
```

## Environment-Specific Configurations

### Development

```python
CONNECTION_POOL_CONFIG = {
    'min_connections': 2,
    'max_connections': 10,
    'idle_timeout': 60,
    'max_lifetime': 600,
}
```

### Staging

```python
CONNECTION_POOL_CONFIG = {
    'min_connections': 5,
    'max_connections': 25,
    'idle_timeout': 180,
    'max_lifetime': 1800,
}
```

### Production

```python
CONNECTION_POOL_CONFIG = {
    'min_connections': 10,
    'max_connections': 50,
    'idle_timeout': 300,
    'max_lifetime': 3600,
}
```

## Additional Resources

- [PostgreSQL Connection Pooling](https://www.postgresql.org/docs/current/runtime-config-connection.html)
- [Django Database Configuration](https://docs.djangoproject.com/en/4.2/ref/databases/)
- [PgBouncer Documentation](https://www.pgbouncer.org/config.html)
