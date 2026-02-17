# Operations Runbook

This runbook provides step-by-step procedures for common operational tasks and incident response for the database and caching infrastructure.

## Table of Contents

1. [Daily Operations](#daily-operations)
2. [Incident Response](#incident-response)
3. [Maintenance Procedures](#maintenance-procedures)
4. [Backup and Recovery](#backup-and-recovery)
5. [Performance Optimization](#performance-optimization)
6. [Emergency Procedures](#emergency-procedures)

## Daily Operations

### Morning Health Check

**Frequency**: Daily at 9:00 AM  
**Duration**: 10 minutes  
**Owner**: On-call engineer

**Procedure**:

1. **Check System Health**:
```bash
# Check application health
curl http://localhost:8000/health

# Check metrics endpoint
curl http://localhost:8000/metrics/json
```

2. **Review Dashboards**:
   - Open Grafana: http://localhost:3000
   - Check "Database Performance Metrics" dashboard
   - Check "Cache Performance Metrics" dashboard
   - Verify all metrics are within normal ranges

3. **Check Alerts**:
   - Review Alertmanager: http://localhost:9093
   - Verify no active alerts
   - Review resolved alerts from past 24 hours

4. **Check Replication Status**:
```sql
-- On primary database
SELECT
    client_addr,
    state,
    sync_state,
    EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp())) AS lag_seconds
FROM pg_stat_replication;
```

5. **Check Connection Pool**:
```bash
curl http://localhost:8000/metrics/json | jq '.connection_pool'
```

6. **Check Cache Performance**:
```bash
curl http://localhost:8000/metrics/json | jq '.cache'
```

**Expected Results**:
- All health checks return 200 OK
- Replication lag < 2 seconds
- Connection pool utilization 40-70%
- Cache hit rate > 70%
- No active critical alerts

**Escalation**:
If any checks fail, follow incident response procedures.

### Weekly Maintenance

**Frequency**: Weekly on Sunday at 2:00 AM  
**Duration**: 30 minutes  
**Owner**: Database administrator

**Procedure**:

1. **Database Maintenance**:
```sql
-- Vacuum and analyze
VACUUM ANALYZE;

-- Reindex if needed
REINDEX DATABASE muejam_library;

-- Update statistics
ANALYZE;
```

2. **Check Database Size**:
```sql
SELECT
    pg_size_pretty(pg_database_size('muejam_library')) AS db_size,
    pg_size_pretty(pg_total_relation_size('stories')) AS stories_size,
    pg_size_pretty(pg_total_relation_size('users')) AS users_size;
```

3. **Review Slow Queries**:
```sql
SELECT
    query,
    calls,
    mean_exec_time,
    max_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 20;
```

4. **Clear Old Logs**:
```bash
# Clear logs older than 30 days
find /var/log/postgresql -name "*.log" -mtime +30 -delete
find /var/log/redis -name "*.log" -mtime +30 -delete
```

5. **Backup Verification**:
```bash
# Verify latest backup exists
ls -lh /backups/postgresql/latest.sql.gz

# Check backup age
find /backups/postgresql -name "*.sql.gz" -mtime -1
```

## Incident Response

### High Database Latency

**Symptoms**:
- Average query latency > 100ms
- User complaints about slow page loads
- Alert: "HighQueryLatency"

**Severity**: P2 (High)

**Response Procedure**:

1. **Assess Impact**:
```bash
# Check current latency
curl http://localhost:8000/metrics/json | jq '.database.avg_latency_ms'

# Check affected users
tail -f /var/log/gunicorn/access.log | grep "response_time"
```

2. **Identify Slow Queries**:
```sql
-- Find currently running slow queries
SELECT
    pid,
    now() - pg_stat_activity.query_start AS duration,
    query,
    state
FROM pg_stat_activity
WHERE state = 'active'
    AND now() - pg_stat_activity.query_start > interval '5 seconds'
ORDER BY duration DESC;
```

3. **Check System Resources**:
```bash
# Check CPU usage
top -bn1 | grep "Cpu(s)"

# Check memory
free -h

# Check disk I/O
iostat -x 1 5
```

4. **Immediate Actions**:

   **If slow query identified**:
   ```sql
   -- Kill slow query (use with caution)
   SELECT pg_terminate_backend(pid);
   ```

   **If high CPU**:
   ```bash
   # Check for missing indexes
   # Review query execution plans
   EXPLAIN ANALYZE <slow_query>;
   ```

   **If high I/O**:
   ```bash
   # Check for table bloat
   # Consider VACUUM FULL during maintenance window
   ```

5. **Mitigation**:
   - Route traffic to replicas if primary overloaded
   - Increase cache TTL temporarily
   - Enable query result caching
   - Scale up database resources if needed

6. **Resolution**:
   - Add missing indexes
   - Optimize slow queries
   - Increase database resources
   - Review and adjust connection pool settings

**Post-Incident**:
- Document root cause
- Update monitoring thresholds if needed
- Schedule follow-up optimization work

### Database Connection Pool Exhaustion

**Symptoms**:
- Connection pool utilization > 95%
- Requests timing out
- Alert: "CriticalConnectionPoolUtilization"

**Severity**: P1 (Critical)

**Response Procedure**:

1. **Assess Impact**:
```bash
# Check pool utilization
curl http://localhost:8000/metrics/json | jq '.connection_pool'

# Check active connections
psql -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';"
```

2. **Immediate Actions**:

   **Option 1: Increase pool size** (temporary):
   ```python
   # In Django shell
   from infrastructure.connection_pool import get_pool_manager
   pool_manager = get_pool_manager()
   pool_manager.max_connections = 100  # Increased from 50
   ```

   **Option 2: Kill idle connections**:
   ```sql
   -- Kill idle connections older than 5 minutes
   SELECT pg_terminate_backend(pid)
   FROM pg_stat_activity
   WHERE state = 'idle'
       AND now() - state_change > interval '5 minutes';
   ```

   **Option 3: Restart application** (last resort):
   ```bash
   sudo systemctl restart gunicorn
   ```

3. **Root Cause Analysis**:
   - Check for connection leaks in code
   - Review slow queries holding connections
   - Check for long-running transactions

4. **Resolution**:
   - Fix connection leaks
   - Optimize slow queries
   - Increase max_connections permanently
   - Add connection timeout

**Post-Incident**:
- Review code for connection management
- Add monitoring for connection leaks
- Update connection pool configuration

### Cache Failure

**Symptoms**:
- Cache hit rate drops to 0%
- Increased database load
- Alert: "RedisInstanceDown"

**Severity**: P2 (High)

**Response Procedure**:

1. **Assess Impact**:
```bash
# Check cache status
curl http://localhost:8000/metrics/json | jq '.cache'

# Check Redis connectivity
redis-cli -h $REDIS_HOST -p $REDIS_PORT -a $REDIS_PASSWORD ping
```

2. **Immediate Actions**:

   **If Redis is down**:
   ```bash
   # Restart Redis
   sudo systemctl restart redis

   # Check Redis logs
   tail -f /var/log/redis/redis-server.log
   ```

   **If Redis is up but not responding**:
   ```bash
   # Check Redis memory
   redis-cli info memory

   # Check Redis connections
   redis-cli info clients

   # Flush cache if corrupted
   redis-cli FLUSHDB
   ```

3. **Mitigation**:
   - Application should fail-open (bypass cache)
   - Database should handle increased load
   - Monitor database metrics closely

4. **Resolution**:
   - Fix Redis issue
   - Warm cache after recovery
   - Review Redis configuration

**Post-Incident**:
- Review Redis monitoring
- Consider Redis cluster for HA
- Update cache failure procedures

### Replication Lag

**Symptoms**:
- Replication lag > 5 seconds
- Stale data on replicas
- Alert: "HighReplicationLag"

**Severity**: P2 (High)

**Response Procedure**:

1. **Assess Impact**:
```sql
-- Check replication lag
SELECT
    client_addr,
    EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp())) AS lag_seconds
FROM pg_stat_replication;
```

2. **Immediate Actions**:

   **If lag < 30 seconds**:
   - Monitor and wait for catch-up
   - Route reads to primary temporarily

   **If lag > 30 seconds**:
   ```python
   # Route all reads to primary
   from infrastructure.workload_isolator import WorkloadIsolator
   isolator = WorkloadIsolator()
   isolator.force_primary_reads = True
   ```

3. **Root Cause Analysis**:
   - Check network bandwidth
   - Check replica CPU/disk I/O
   - Check for long-running transactions on primary
   - Check WAL generation rate

4. **Resolution**:

   **If network issue**:
   - Check network connectivity
   - Increase network bandwidth if needed

   **If replica overloaded**:
   - Scale up replica resources
   - Add more replicas to distribute load

   **If high write volume**:
   - Optimize write operations
   - Batch writes where possible
   - Consider increasing wal_sender processes

**Post-Incident**:
- Review replication configuration
- Add monitoring for replication lag trends
- Consider upgrading replica hardware

## Maintenance Procedures

### Adding a New Read Replica

**Duration**: 30 minutes  
**Downtime**: None

**Procedure**:

1. **Prepare New Server**:
```bash
# Install PostgreSQL
sudo apt-get install postgresql-14

# Stop PostgreSQL
sudo systemctl stop postgresql
```

2. **Create Base Backup**:
```bash
# On new replica
sudo -u postgres pg_basebackup \
    -h <primary-ip> \
    -D /var/lib/postgresql/14/main \
    -U replicator \
    -P -v -R -X stream \
    -C -S replica_4_slot
```

3. **Start Replica**:
```bash
sudo systemctl start postgresql
```

4. **Verify Replication**:
```sql
-- On primary
SELECT * FROM pg_stat_replication;
```

5. **Add to Django Configuration**:
```python
# config/settings.py
DATABASES = {
    # ... existing databases ...
    'replica_4': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': '<new-replica-ip>',
        'PORT': '5432',
    },
}
```

6. **Add to Load Balancer**:
```python
# infrastructure/load_balancer.py
replicas = [
    # ... existing replicas ...
    {'host': '<new-replica-ip>', 'port': 5432, 'weight': 1.0},
]
```

7. **Restart Application**:
```bash
sudo systemctl restart gunicorn
```

8. **Verify**:
```bash
# Check replica is receiving traffic
curl http://localhost:8000/metrics/json | jq '.load_balancer'
```

### Scaling Redis Cluster

**Duration**: 1 hour  
**Downtime**: None (rolling)

**Procedure**:

1. **Add New Redis Nodes**:
```bash
# Start new Redis instances
redis-server /etc/redis/redis-node-7.conf
redis-server /etc/redis/redis-node-8.conf
```

2. **Add Nodes to Cluster**:
```bash
# Add as master
redis-cli --cluster add-node <new-node-ip>:7000 <existing-node-ip>:7000

# Add as replica
redis-cli --cluster add-node <new-node-ip>:7001 <existing-node-ip>:7000 --cluster-slave
```

3. **Rebalance Cluster**:
```bash
redis-cli --cluster rebalance <cluster-ip>:7000 --cluster-use-empty-masters
```

4. **Verify**:
```bash
redis-cli --cluster check <cluster-ip>:7000
```

### Database Schema Migration

**Duration**: Varies  
**Downtime**: Depends on migration

**Procedure**:

1. **Backup Database**:
```bash
pg_dump -h <primary-ip> -U postgres muejam_library > backup_pre_migration.sql
```

2. **Test in Staging**:
```bash
# Apply migration in staging
python manage.py migrate --database=staging

# Verify application works
# Run integration tests
```

3. **Schedule Maintenance Window**:
   - Notify users
   - Plan rollback procedure
   - Prepare monitoring

4. **Apply Migration**:
```bash
# Apply migration
python manage.py migrate

# Verify migration
python manage.py showmigrations
```

5. **Verify Application**:
```bash
# Check health
curl http://localhost:8000/health

# Check metrics
curl http://localhost:8000/metrics/json

# Monitor logs
tail -f /var/log/gunicorn/error.log
```

6. **Rollback if Needed**:
```bash
# Restore from backup
psql -h <primary-ip> -U postgres muejam_library < backup_pre_migration.sql

# Revert code
git revert <commit-hash>
sudo systemctl restart gunicorn
```

## Backup and Recovery

### Daily Backup

**Frequency**: Daily at 2:00 AM  
**Retention**: 30 days

**Procedure**:
```bash
#!/bin/bash
# /usr/local/bin/backup_database.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/postgresql"
BACKUP_FILE="$BACKUP_DIR/muejam_library_$DATE.sql.gz"

# Create backup
pg_dump -h <primary-ip> -U postgres muejam_library | gzip > $BACKUP_FILE

# Upload to S3
aws s3 cp $BACKUP_FILE s3://muejam-backups/postgresql/

# Clean old backups
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

# Verify backup
if [ -f "$BACKUP_FILE" ]; then
    echo "Backup successful: $BACKUP_FILE"
else
    echo "Backup failed!" | mail -s "Backup Failed" ops@example.com
fi
```

### Point-in-Time Recovery

**Procedure**:

1. **Stop Application**:
```bash
sudo systemctl stop gunicorn
```

2. **Restore Base Backup**:
```bash
# Stop PostgreSQL
sudo systemctl stop postgresql

# Clear data directory
sudo rm -rf /var/lib/postgresql/14/main/*

# Restore backup
gunzip -c /backups/postgresql/latest.sql.gz | psql -U postgres muejam_library
```

3. **Apply WAL Files**:
```bash
# Copy WAL files to pg_wal directory
cp /backups/wal/* /var/lib/postgresql/14/main/pg_wal/

# Create recovery.conf
cat > /var/lib/postgresql/14/main/recovery.conf <<EOF
restore_command = 'cp /backups/wal/%f %p'
recovery_target_time = '2026-02-17 10:30:00'
EOF
```

4. **Start PostgreSQL**:
```bash
sudo systemctl start postgresql
```

5. **Verify Recovery**:
```sql
SELECT pg_last_xact_replay_timestamp();
```

6. **Start Application**:
```bash
sudo systemctl start gunicorn
```

## Performance Optimization

### Query Optimization

**Procedure**:

1. **Identify Slow Queries**:
```sql
SELECT
    query,
    calls,
    mean_exec_time,
    max_exec_time,
    stddev_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 20;
```

2. **Analyze Query Plan**:
```sql
EXPLAIN ANALYZE <slow_query>;
```

3. **Add Missing Indexes**:
```sql
-- Example: Add index on frequently queried column
CREATE INDEX CONCURRENTLY idx_stories_user_id ON stories(user_id);
```

4. **Verify Improvement**:
```sql
-- Check query performance after optimization
EXPLAIN ANALYZE <optimized_query>;
```

### Cache Warming

**Procedure**:

```python
# scripts/warm_cache.py
from infrastructure.cache_manager import get_cache_manager
from apps.stories.models import Story

cache_manager = get_cache_manager()

# Warm popular stories
popular_stories = Story.objects.filter(views__gt=1000)[:100]
for story in popular_stories:
    cache_key = f"story:{story.id}"
    cache_manager.set(cache_key, story, ttl=3600)

print(f"Warmed cache with {len(popular_stories)} stories")
```

## Emergency Procedures

### Emergency Database Failover

**When**: Primary database is down and unrecoverable

**Procedure**:

1. **Promote Replica to Primary**:
```bash
# On replica to promote
sudo -u postgres pg_ctl promote -D /var/lib/postgresql/14/main
```

2. **Update Application Configuration**:
```python
# Update primary host in .env
DB_PRIMARY_HOST=<new-primary-ip>
```

3. **Restart Application**:
```bash
sudo systemctl restart gunicorn
```

4. **Reconfigure Remaining Replicas**:
```bash
# On each remaining replica
# Update recovery.conf to point to new primary
primary_conninfo = 'host=<new-primary-ip> port=5432 user=replicator'
```

5. **Verify**:
```sql
-- On new primary
SELECT * FROM pg_stat_replication;
```

### Emergency Cache Flush

**When**: Cache contains corrupted or stale data

**Procedure**:

```bash
# Flush all cache data
redis-cli FLUSHALL

# Warm cache
python scripts/warm_cache.py

# Verify
curl http://localhost:8000/metrics/json | jq '.cache'
```

## Contact Information

- **On-Call Engineer**: +1-555-0100
- **Database Team**: database-team@example.com
- **DevOps Team**: devops@example.com
- **Emergency Hotline**: +1-555-0911
