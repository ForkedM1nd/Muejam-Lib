# Database Replication Configuration Guide

This document explains how to configure and use database replication in the Django application.

## Overview

The database replication system provides:
- **High Availability**: Automatic failover when primary database fails
- **Read Scaling**: Distribute read queries across multiple replicas
- **Workload Isolation**: Separate read and write operations
- **Load Balancing**: Intelligent routing based on replica health and load

## Architecture

```
┌─────────────────┐
│ Django App      │
│ (ORM Queries)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Database Router │ ◄── Routes reads to 'replica', writes to 'default'
└────────┬────────┘
         │
         ├──────────────────┬──────────────────┐
         ▼                  ▼                  ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ Primary DB      │  │ Replica 1       │  │ Replica 2       │
│ (Write + Read)  │  │ (Read Only)     │  │ (Read Only)     │
└─────────────────┘  └─────────────────┘  └─────────────────┘
         │                  ▲                  ▲
         └──────replication─┴──────────────────┘
```

## Configuration

### 1. Django Settings

The database replication is configured in `backend/config/settings.py`:

```python
# Primary database connection
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'muejam',
        'USER': 'muejam_user',
        'PASSWORD': 'muejam_password',
        'HOST': 'localhost',
        'PORT': '5432',
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c statement_timeout=30000',
        },
    }
}

# Read replicas (minimum 3 for high availability)
DATABASE_REPLICAS = [
    {'HOST': 'replica1.example.com', 'PORT': '5432', 'WEIGHT': 1.0},
    {'HOST': 'replica2.example.com', 'PORT': '5432', 'WEIGHT': 1.0},
    {'HOST': 'replica3.example.com', 'PORT': '5432', 'WEIGHT': 1.0},
]

# Database router for read/write splitting
DATABASE_ROUTERS = ['infrastructure.database_router.ReplicationRouter']
```

### 2. Environment Variables

Configure these variables in your `.env` file:

```bash
# Primary Database
DATABASE_URL=postgresql://user:password@primary-host:5432/dbname

# Read Replicas
DATABASE_REPLICA_1_HOST=replica1.example.com
DATABASE_REPLICA_1_PORT=5432
DATABASE_REPLICA_1_WEIGHT=1.0

DATABASE_REPLICA_2_HOST=replica2.example.com
DATABASE_REPLICA_2_PORT=5432
DATABASE_REPLICA_2_WEIGHT=1.0

DATABASE_REPLICA_3_HOST=replica3.example.com
DATABASE_REPLICA_3_PORT=5432
DATABASE_REPLICA_3_WEIGHT=1.0

# Connection Pool Settings
DB_POOL_MIN_CONNECTIONS=10
DB_POOL_MAX_CONNECTIONS=50
DB_POOL_IDLE_TIMEOUT=300

# Workload Isolation
MAX_REPLICA_LAG=5.0
REPLICA_LAG_CHECK_INTERVAL=10

# High Availability
ENABLE_AUTO_FAILOVER=True
FAILOVER_TIMEOUT=30
HEALTH_CHECK_INTERVAL=10
HEALTH_CHECK_TIMEOUT=5

# Failover Notifications
FAILOVER_EMAIL_ENABLED=True
FAILOVER_EMAIL_RECIPIENTS=admin@example.com,ops@example.com
FAILOVER_SLACK_ENABLED=True
FAILOVER_SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

## Database Router

The `ReplicationRouter` automatically routes queries:

### Read Operations → Replicas
- `SELECT` queries
- `.get()`, `.filter()`, `.all()`, `.count()`, etc.
- Routed to healthy replicas with lowest load

### Write Operations → Primary
- `INSERT`, `UPDATE`, `DELETE` queries
- `.create()`, `.save()`, `.update()`, `.delete()`, etc.
- Always routed to primary database

### Critical Reads → Primary
For read-after-write consistency:

```python
# Force read from primary
user = User.objects.using('default').get(id=user_id)

# Or use hint
user = User.objects.db_manager(hints={'use_primary': True}).get(id=user_id)
```

## Replica Configuration

### Minimum Requirements

**Requirement 2.2**: Maintain at least 2 read replicas for redundancy
**Requirement 6.4**: Support at least 3 read replicas

The system is configured with 3 replicas by default to meet both requirements.

### Replica Weights

Weights control load distribution:
- `WEIGHT=1.0`: Normal capacity (default)
- `WEIGHT=2.0`: Double capacity (receives 2x traffic)
- `WEIGHT=0.5`: Half capacity (receives 0.5x traffic)

Use weights to account for different replica hardware specs.

### Replica Health Monitoring

The `HealthMonitor` checks replica health every 10 seconds:
- **Connectivity**: Can connect to replica
- **Replication Lag**: Lag below 5 seconds
- **CPU Utilization**: Below 80%
- **Memory**: Sufficient available memory
- **Disk**: Sufficient disk space

Unhealthy replicas are automatically removed from the pool.

## Automatic Failover

### Failover Process

**Requirement 2.1**: Automatic promotion within 30 seconds

When primary database fails:

1. **Detection** (0-10s): Health monitor detects primary failure
2. **Selection** (10-15s): Select healthiest replica based on:
   - Lowest replication lag
   - Lowest CPU utilization
   - Best connectivity
3. **Promotion** (15-25s): Promote selected replica to primary
4. **Routing Update** (25-30s): Update connection routing
5. **Notification** (30s+): Alert administrators

### Failover Configuration

```python
# Enable/disable automatic failover
ENABLE_AUTO_FAILOVER = True

# Maximum time to complete failover
FAILOVER_TIMEOUT = 30  # seconds

# Health check frequency
HEALTH_CHECK_INTERVAL = 10  # seconds
```

### Failover Notifications

**Requirement 2.5**: Notify administrators through configured channels

Supported notification channels:
- **Email**: Send alerts via Resend
- **Slack**: Post to Slack channel via webhook
- **PagerDuty**: Create incident via integration key

Configure in environment variables:

```bash
FAILOVER_EMAIL_ENABLED=True
FAILOVER_EMAIL_RECIPIENTS=admin@example.com,ops@example.com

FAILOVER_SLACK_ENABLED=True
FAILOVER_SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

FAILOVER_PAGERDUTY_ENABLED=True
FAILOVER_PAGERDUTY_KEY=your-integration-key
```

## Replication Lag Management

### Lag Monitoring

**Requirement 6.2**: Maintain replication lag below 2 seconds under normal load
**Requirement 6.3**: Alert when lag exceeds 5 seconds

The system continuously monitors replication lag:

```python
MAX_REPLICA_LAG = 5.0  # Alert threshold
REPLICA_LAG_CHECK_INTERVAL = 10  # Check every 10 seconds
```

### Lag-Based Routing

**Requirement 3.4**: Route reads to primary when replica lag exceeds 5 seconds

When a replica's lag exceeds the threshold:
1. Replica is marked as unhealthy
2. New reads are routed to other replicas or primary
3. Alert is sent to administrators
4. Replica is monitored for recovery

### Automatic Resync

**Requirement 6.5**: Automatically resync lagging replicas

When a replica falls behind:
1. System detects high lag
2. Replica is removed from active pool
3. Automatic resync is initiated from primary
4. Replica is re-added when lag is acceptable

## Connection Pooling

### Pool Configuration

**Requirement 4.1**: Maintain 10-50 connections per instance

```python
DB_POOL_MIN_CONNECTIONS = 10  # Pre-warmed connections
DB_POOL_MAX_CONNECTIONS = 50  # Maximum per instance
DB_POOL_IDLE_TIMEOUT = 300    # Close idle connections after 5 minutes
```

### Separate Pools

**Requirement 3.5**: Separate connection pools for read and write

The system maintains two connection pools:
- **Write Pool**: Connections to primary database
- **Read Pool**: Connections to replica databases

This isolation prevents read operations from exhausting write connections.

## Load Balancing

### Weighted Round-Robin

**Requirement 9.1, 9.2**: Distribute queries using weighted round-robin

The `LoadBalancer` distributes read queries across replicas:

```python
# Example: 3 replicas with different weights
Replica 1: WEIGHT=1.0 → 33% of traffic
Replica 2: WEIGHT=1.0 → 33% of traffic
Replica 3: WEIGHT=1.0 → 33% of traffic

# With different weights
Replica 1: WEIGHT=2.0 → 50% of traffic
Replica 2: WEIGHT=1.0 → 25% of traffic
Replica 3: WEIGHT=1.0 → 25% of traffic
```

### CPU-Based Traffic Reduction

**Requirement 9.3**: Reduce traffic to replicas at >80% CPU

When a replica reaches 80% CPU utilization:
1. Replica weight is automatically reduced
2. Traffic is redistributed to other replicas
3. Replica is monitored for recovery
4. Weight is restored when CPU drops below 70%

### Response Time Preference

**Requirement 9.4**: Prefer faster replicas

The load balancer tracks response times and adjusts routing:
- Fast replicas (< 50ms): Normal weight
- Medium replicas (50-100ms): Slightly reduced weight
- Slow replicas (> 100ms): Significantly reduced weight

## Usage Examples

### Basic Queries (Automatic Routing)

```python
# Read query → automatically routed to replica
users = User.objects.filter(is_active=True)

# Write query → automatically routed to primary
user = User.objects.create(username='john', email='john@example.com')

# Update → automatically routed to primary
user.email = 'newemail@example.com'
user.save()
```

### Forcing Primary for Consistency

```python
# Read-after-write scenario
user = User.objects.create(username='john')

# Force read from primary to ensure consistency
user_check = User.objects.using('default').get(id=user.id)
```

### Critical Operations

```python
# Critical read that must be consistent
user = User.objects.db_manager(hints={'use_primary': True}).get(id=user_id)
```

### Checking Replica Status

```python
from infrastructure.middleware import DatabaseInfrastructureMiddleware

# Get workload isolator
workload_isolator = DatabaseInfrastructureMiddleware.get_workload_isolator()

# Check replica status
replicas = workload_isolator.get_replica_status()
for replica in replicas:
    print(f"Replica: {replica['host']}:{replica['port']}")
    print(f"  Healthy: {replica['is_healthy']}")
    print(f"  Lag: {replica['replication_lag']}s")
    print(f"  CPU: {replica['cpu_utilization']}%")
```

## PostgreSQL Replication Setup

### Primary Database Configuration

Edit `postgresql.conf` on primary:

```conf
# Replication settings
wal_level = replica
max_wal_senders = 10
max_replication_slots = 10
synchronous_commit = off
```

Edit `pg_hba.conf` on primary:

```conf
# Allow replication connections
host replication replicator replica1.example.com/32 md5
host replication replicator replica2.example.com/32 md5
host replication replicator replica3.example.com/32 md5
```

Create replication user:

```sql
CREATE USER replicator WITH REPLICATION ENCRYPTED PASSWORD 'repl_password';
```

### Replica Database Setup

On each replica server:

```bash
# Stop PostgreSQL
sudo systemctl stop postgresql

# Remove existing data
sudo rm -rf /var/lib/postgresql/14/main/*

# Create base backup from primary
sudo -u postgres pg_basebackup -h primary.example.com -D /var/lib/postgresql/14/main -U replicator -P -v -R -X stream -C -S replica1_slot

# Start PostgreSQL
sudo systemctl start postgresql
```

The `-R` flag automatically creates `standby.signal` and configures replication.

### Verify Replication

On primary:

```sql
-- Check replication status
SELECT * FROM pg_stat_replication;

-- Check replication slots
SELECT * FROM pg_replication_slots;
```

On replica:

```sql
-- Check if in recovery mode (should be true)
SELECT pg_is_in_recovery();

-- Check replication lag
SELECT EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp())) AS lag_seconds;
```

## Monitoring

### Key Metrics

Monitor these metrics for healthy replication:

1. **Replication Lag**: Should be < 2 seconds
2. **Replica Health**: All replicas should be healthy
3. **Connection Pool Utilization**: Should be < 80%
4. **Query Distribution**: Reads should be distributed across replicas
5. **Failover Events**: Should be rare

### Health Check Endpoint

The system provides a health check endpoint:

```bash
curl http://localhost:8000/health/database/
```

Response:

```json
{
  "status": "healthy",
  "primary": {
    "host": "primary.example.com",
    "healthy": true,
    "response_time_ms": 5.2
  },
  "replicas": [
    {
      "host": "replica1.example.com",
      "healthy": true,
      "replication_lag": 0.8,
      "cpu_utilization": 45.2,
      "response_time_ms": 3.1
    },
    {
      "host": "replica2.example.com",
      "healthy": true,
      "replication_lag": 1.2,
      "cpu_utilization": 52.8,
      "response_time_ms": 4.5
    }
  ],
  "connection_pools": {
    "read": {
      "active": 15,
      "idle": 5,
      "utilization": 30.0
    },
    "write": {
      "active": 8,
      "idle": 12,
      "utilization": 16.0
    }
  }
}
```

## Troubleshooting

### Replica Not Receiving Updates

**Symptoms**: Replica lag increasing, data not syncing

**Solutions**:
1. Check replication connection: `SELECT * FROM pg_stat_replication;`
2. Check replication slot: `SELECT * FROM pg_replication_slots;`
3. Check network connectivity between primary and replica
4. Check disk space on replica
5. Restart replication if needed

### High Replication Lag

**Symptoms**: Lag > 5 seconds, reads routed to primary

**Solutions**:
1. Check replica CPU and disk I/O
2. Reduce write load on primary
3. Increase replica hardware resources
4. Check for long-running queries on replica
5. Consider adding more replicas

### Failover Not Working

**Symptoms**: Primary fails but no automatic promotion

**Solutions**:
1. Check `ENABLE_AUTO_FAILOVER=True` in settings
2. Check health monitor logs
3. Verify replica health status
4. Check network connectivity to replicas
5. Manually trigger failover if needed

### Connection Pool Exhaustion

**Symptoms**: `TimeoutError: Connection pool exhausted`

**Solutions**:
1. Increase `DB_POOL_MAX_CONNECTIONS`
2. Check for connection leaks
3. Reduce `DB_POOL_IDLE_TIMEOUT`
4. Scale horizontally (add more app instances)

## Best Practices

1. **Always configure at least 3 replicas** for high availability
2. **Monitor replication lag** continuously
3. **Test failover** regularly in staging environment
4. **Use read-after-write consistency** when needed
5. **Configure alerts** for all critical thresholds
6. **Document replica topology** and update as it changes
7. **Plan for replica maintenance** windows
8. **Test backup and restore** procedures regularly

## References

- Requirements: 2.1, 2.2, 6.1, 6.4
- Design Document: `.kiro/specs/db-cache-optimization/design.md`
- Django Integration: `backend/infrastructure/DJANGO_INTEGRATION.md`
- PostgreSQL Replication: https://www.postgresql.org/docs/current/high-availability.html
