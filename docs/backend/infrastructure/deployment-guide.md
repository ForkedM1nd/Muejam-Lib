# Database and Caching Infrastructure Deployment Guide

This guide provides comprehensive instructions for deploying the database and caching infrastructure optimization components in production environments.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Database Replication Setup](#database-replication-setup)
4. [Redis Cluster Configuration](#redis-cluster-configuration)
5. [Connection Pool Configuration](#connection-pool-configuration)
6. [Rate Limiting Configuration](#rate-limiting-configuration)
7. [Monitoring Setup](#monitoring-setup)
8. [Django Integration](#django-integration)
9. [Production Deployment](#production-deployment)
10. [Troubleshooting](#troubleshooting)

## Overview

The infrastructure optimization includes:

- **Database Replication**: Primary-replica setup with automatic failover
- **Connection Pooling**: Efficient connection management with separate read/write pools
- **Multi-Layer Caching**: L1 (in-memory) and L2 (Redis) caching
- **Workload Isolation**: Automatic routing of reads to replicas, writes to primary
- **Rate Limiting**: Per-user and global rate limits
- **Health Monitoring**: Continuous health checks with automatic failover
- **Load Balancing**: Weighted distribution across replicas
- **Circuit Breaking**: Automatic failure detection and recovery

## Prerequisites

### System Requirements

- **Operating System**: Linux (Ubuntu 20.04+ or CentOS 8+)
- **Python**: 3.9 or higher
- **PostgreSQL**: 14 or higher
- **Redis**: 6.2 or higher (or Valkey)
- **Memory**: Minimum 8GB RAM (16GB+ recommended)
- **CPU**: Minimum 4 cores (8+ recommended)
- **Disk**: SSD storage recommended for database

### Software Dependencies

```bash
# Install system packages
sudo apt-get update
sudo apt-get install -y \
    python3.9 \
    python3-pip \
    postgresql-14 \
    redis-server \
    build-essential \
    libpq-dev

# Install Python packages
pip install -r requirements.txt
```

### Network Requirements

- **Database Ports**: 5432 (PostgreSQL)
- **Cache Ports**: 6379 (Redis/Valkey)
- **Application Ports**: 8000 (Django)
- **Monitoring Ports**: 9090 (Prometheus), 3000 (Grafana)

## Database Replication Setup

### Step 1: Configure Primary Database

Edit PostgreSQL configuration on the primary server:

```bash
# /etc/postgresql/14/main/postgresql.conf

# Replication settings
wal_level = replica
max_wal_senders = 10
max_replication_slots = 10
hot_standby = on
archive_mode = on
archive_command = 'test ! -f /var/lib/postgresql/14/archive/%f && cp %p /var/lib/postgresql/14/archive/%f'

# Performance settings
shared_buffers = 4GB
effective_cache_size = 12GB
maintenance_work_mem = 1GB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 10MB
min_wal_size = 1GB
max_wal_size = 4GB
max_worker_processes = 8
max_parallel_workers_per_gather = 4
max_parallel_workers = 8
max_parallel_maintenance_workers = 4
```

Configure authentication:

```bash
# /etc/postgresql/14/main/pg_hba.conf

# Replication connections
host    replication     replicator      <replica-1-ip>/32       md5
host    replication     replicator      <replica-2-ip>/32       md5
host    replication     replicator      <replica-3-ip>/32       md5

# Application connections
host    all             all             <app-server-ip>/32      md5
```

Create replication user:

```sql
-- On primary database
CREATE USER replicator WITH REPLICATION ENCRYPTED PASSWORD 'strong_password';
```

Restart PostgreSQL:

```bash
sudo systemctl restart postgresql
```

### Step 2: Configure Read Replicas

On each replica server:

```bash
# Stop PostgreSQL
sudo systemctl stop postgresql

# Remove existing data directory
sudo rm -rf /var/lib/postgresql/14/main/*

# Create base backup from primary
sudo -u postgres pg_basebackup \
    -h <primary-ip> \
    -D /var/lib/postgresql/14/main \
    -U replicator \
    -P \
    -v \
    -R \
    -X stream \
    -C -S replica_1_slot

# Start PostgreSQL
sudo systemctl start postgresql
```

Verify replication status on primary:

```sql
-- Check replication slots
SELECT * FROM pg_replication_slots;

-- Check replication status
SELECT * FROM pg_stat_replication;
```

### Step 3: Configure Automatic Failover

Install and configure Patroni for automatic failover:

```bash
# Install Patroni
pip install patroni[etcd]

# Create Patroni configuration
sudo nano /etc/patroni.yml
```

Patroni configuration:

```yaml
scope: muejam-cluster
namespace: /db/
name: postgres-1

restapi:
  listen: 0.0.0.0:8008
  connect_address: <node-ip>:8008

etcd:
  hosts: <etcd-ip>:2379

bootstrap:
  dcs:
    ttl: 30
    loop_wait: 10
    retry_timeout: 10
    maximum_lag_on_failover: 1048576
    postgresql:
      use_pg_rewind: true
      parameters:
        wal_level: replica
        hot_standby: on
        max_wal_senders: 10
        max_replication_slots: 10

postgresql:
  listen: 0.0.0.0:5432
  connect_address: <node-ip>:5432
  data_dir: /var/lib/postgresql/14/main
  pgpass: /tmp/pgpass
  authentication:
    replication:
      username: replicator
      password: strong_password
    superuser:
      username: postgres
      password: postgres_password
  parameters:
    unix_socket_directories: '/var/run/postgresql'

tags:
  nofailover: false
  noloadbalance: false
  clonefrom: false
  nosync: false
```

Start Patroni:

```bash
sudo systemctl enable patroni
sudo systemctl start patroni
```

### Step 4: Verify Replication

Check replication lag:

```sql
-- On primary
SELECT
    client_addr,
    state,
    sent_lsn,
    write_lsn,
    flush_lsn,
    replay_lsn,
    sync_state,
    EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp())) AS lag_seconds
FROM pg_stat_replication;
```

## Redis Cluster Configuration

### Step 1: Install Redis/Valkey

```bash
# Install Redis
sudo apt-get install redis-server

# Or install Valkey (Redis fork)
wget https://github.com/valkey-io/valkey/releases/download/7.2.5/valkey-7.2.5.tar.gz
tar xzf valkey-7.2.5.tar.gz
cd valkey-7.2.5
make
sudo make install
```

### Step 2: Configure Redis Cluster

Create Redis configuration for each node:

```bash
# /etc/redis/redis-node-1.conf

port 7000
cluster-enabled yes
cluster-config-file nodes-7000.conf
cluster-node-timeout 5000
appendonly yes
appendfilename "appendonly-7000.aof"
dbfilename dump-7000.rdb
dir /var/lib/redis/7000

# Memory settings
maxmemory 2gb
maxmemory-policy allkeys-lru

# Security
requirepass strong_redis_password
masterauth strong_redis_password

# Persistence
save 900 1
save 300 10
save 60 10000

# Performance
tcp-backlog 511
timeout 0
tcp-keepalive 300
```

Create cluster with 3 masters and 3 replicas:

```bash
redis-cli --cluster create \
    <node1-ip>:7000 \
    <node2-ip>:7000 \
    <node3-ip>:7000 \
    <node4-ip>:7000 \
    <node5-ip>:7000 \
    <node6-ip>:7000 \
    --cluster-replicas 1 \
    -a strong_redis_password
```

### Step 3: Verify Cluster

```bash
# Check cluster info
redis-cli -c -h <node-ip> -p 7000 -a strong_redis_password cluster info

# Check cluster nodes
redis-cli -c -h <node-ip> -p 7000 -a strong_redis_password cluster nodes
```

## Connection Pool Configuration

### Django Settings

Configure connection pooling in Django settings:

```python
# config/settings.py

# Database configuration with connection pooling
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'muejam_library'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_PRIMARY_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'CONN_MAX_AGE': 600,  # Connection persistence
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c statement_timeout=30000',  # 30 second timeout
        },
    },
    # Read replicas
    'replica_1': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'muejam_library'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_REPLICA_1_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c statement_timeout=30000',
        },
    },
    'replica_2': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'muejam_library'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_REPLICA_2_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c statement_timeout=30000',
        },
    },
    'replica_3': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'muejam_library'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_REPLICA_3_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c statement_timeout=30000',
        },
    },
}

# Database router for read/write splitting
DATABASE_ROUTERS = ['infrastructure.database_router.DatabaseRouter']

# Connection pool settings
CONNECTION_POOL_CONFIG = {
    'min_connections': 10,
    'max_connections': 50,
    'idle_timeout': 300,  # 5 minutes
    'max_lifetime': 3600,  # 1 hour
}
```

### Environment Variables

Create `.env` file:

```bash
# Database Configuration
DB_NAME=muejam_library
DB_USER=postgres
DB_PASSWORD=strong_db_password
DB_PRIMARY_HOST=postgres-primary.example.com
DB_REPLICA_1_HOST=postgres-replica-1.example.com
DB_REPLICA_2_HOST=postgres-replica-2.example.com
DB_REPLICA_3_HOST=postgres-replica-3.example.com
DB_PORT=5432

# Redis Configuration
REDIS_HOST=redis-cluster.example.com
REDIS_PORT=6379
REDIS_PASSWORD=strong_redis_password
REDIS_DB=0

# Cache Configuration
CACHE_TTL_DEFAULT=300
CACHE_TTL_STORIES=600
CACHE_TTL_USERS=1800
CACHE_L1_SIZE=1000
CACHE_L1_TTL=60

# Rate Limiting Configuration
RATE_LIMIT_PER_USER=100
RATE_LIMIT_GLOBAL=10000
RATE_LIMIT_WINDOW=60

# Monitoring Configuration
ENABLE_METRICS=true
METRICS_PORT=8000
```

## Rate Limiting Configuration

### Redis-Based Rate Limiting

Configure rate limiting in Django settings:

```python
# config/settings.py

# Rate limiting configuration
RATE_LIMITING = {
    'enabled': True,
    'backend': 'redis',
    'redis_url': f"redis://:{os.getenv('REDIS_PASSWORD')}@{os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT')}/1",
    
    # Per-user limits
    'per_user': {
        'queries_per_minute': int(os.getenv('RATE_LIMIT_PER_USER', 100)),
        'window_seconds': int(os.getenv('RATE_LIMIT_WINDOW', 60)),
    },
    
    # Global limits
    'global': {
        'queries_per_minute': int(os.getenv('RATE_LIMIT_GLOBAL', 10000)),
        'window_seconds': int(os.getenv('RATE_LIMIT_WINDOW', 60)),
    },
    
    # Admin bypass
    'admin_bypass': True,
    
    # Algorithm
    'algorithm': 'sliding_window',
}

# Add rate limiting middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    # Infrastructure middleware
    'infrastructure.middleware.RateLimitMiddleware',
    'infrastructure.middleware.MetricsMiddleware',
    'infrastructure.middleware.HealthCheckMiddleware',
]
```

### Tuning Rate Limits

Adjust rate limits based on your application needs:

```python
# For high-traffic applications
RATE_LIMITING = {
    'per_user': {
        'queries_per_minute': 200,  # Increased from 100
    },
    'global': {
        'queries_per_minute': 20000,  # Increased from 10000
    },
}

# For API endpoints with different limits
RATE_LIMITING_ENDPOINTS = {
    '/v1/stories/': {
        'queries_per_minute': 50,
    },
    '/v1/search/': {
        'queries_per_minute': 20,
    },
    '/v1/users/': {
        'queries_per_minute': 100,
    },
}
```

## Monitoring Setup

### Prometheus Integration

Configure Prometheus scraping:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'django-app'
    static_configs:
      - targets: ['app-server-1:8000', 'app-server-2:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s
```

### Grafana Dashboards

Import dashboards from `monitoring/grafana/dashboards/`:

1. Login to Grafana
2. Navigate to Dashboards → Import
3. Upload `database_metrics.json`
4. Upload `cache_performance.json`

### Alert Configuration

Configure alerts in `monitoring/prometheus/alerts/`:

```yaml
# Custom alert thresholds
- alert: HighQueryLatency
  expr: db_avg_latency_ms > 150  # Adjust threshold
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "High database query latency"
```

## Django Integration

### Middleware Configuration

Enable infrastructure middleware:

```python
# config/settings.py

MIDDLEWARE = [
    # ... other middleware ...
    'infrastructure.middleware.ConnectionPoolMiddleware',
    'infrastructure.middleware.CacheMiddleware',
    'infrastructure.middleware.RateLimitMiddleware',
    'infrastructure.middleware.MetricsMiddleware',
    'infrastructure.middleware.HealthCheckMiddleware',
]

# Infrastructure settings
INFRASTRUCTURE = {
    'connection_pool': {
        'enabled': True,
        'min_connections': 10,
        'max_connections': 50,
    },
    'cache': {
        'enabled': True,
        'l1_size': 1000,
        'l1_ttl': 60,
        'l2_ttl': 300,
    },
    'rate_limiting': {
        'enabled': True,
    },
    'metrics': {
        'enabled': True,
    },
    'health_checks': {
        'enabled': True,
        'interval': 10,
    },
}
```

### Cache Configuration

Configure Django cache framework:

```python
# config/settings.py

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f"redis://:{os.getenv('REDIS_PASSWORD')}@{os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT')}/0",
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
        },
        'KEY_PREFIX': 'muejam',
        'TIMEOUT': 300,
    },
}

# Cache key versioning
CACHE_MIDDLEWARE_KEY_PREFIX = 'muejam'
CACHE_MIDDLEWARE_SECONDS = 300
```

## Production Deployment

### Step 1: Pre-Deployment Checklist

- [ ] Database replication configured and tested
- [ ] Redis cluster configured and tested
- [ ] Connection pool settings tuned
- [ ] Rate limiting configured
- [ ] Monitoring dashboards created
- [ ] Alert rules configured
- [ ] Notification channels tested
- [ ] Backup procedures in place
- [ ] Rollback plan documented
- [ ] Load testing completed

### Step 2: Deployment Process

```bash
# 1. Backup current database
pg_dump -h <primary-host> -U postgres muejam_library > backup_$(date +%Y%m%d).sql

# 2. Update application code
git pull origin main

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run migrations
python manage.py migrate

# 5. Collect static files
python manage.py collectstatic --noinput

# 6. Restart application
sudo systemctl restart gunicorn

# 7. Verify health
curl http://localhost:8000/health
curl http://localhost:8000/metrics
```

### Step 3: Post-Deployment Verification

```bash
# Check database connections
python manage.py shell
>>> from django.db import connections
>>> connections['default'].cursor()
>>> connections['replica_1'].cursor()

# Check cache connectivity
python manage.py shell
>>> from django.core.cache import cache
>>> cache.set('test', 'value')
>>> cache.get('test')

# Check metrics
curl http://localhost:8000/metrics/json

# Monitor logs
tail -f /var/log/gunicorn/error.log
```

### Step 4: Load Testing

Use locust or similar tool:

```python
# locustfile.py
from locust import HttpUser, task, between

class WebsiteUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def read_stories(self):
        self.client.get("/v1/stories/")
    
    @task(1)
    def search(self):
        self.client.get("/v1/search/?q=test")
```

Run load test:

```bash
locust -f locustfile.py --host=http://localhost:8000 --users=100 --spawn-rate=10
```

## Troubleshooting

### Database Connection Issues

**Problem**: Connection pool exhausted

```bash
# Check active connections
SELECT count(*) FROM pg_stat_activity;

# Check connection pool stats
curl http://localhost:8000/metrics/json | jq '.database.connection_pool'
```

**Solution**: Increase max_connections or optimize queries

```python
CONNECTION_POOL_CONFIG = {
    'max_connections': 100,  # Increased from 50
}
```

### Replication Lag Issues

**Problem**: High replication lag

```sql
-- Check replication lag
SELECT
    client_addr,
    EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp())) AS lag_seconds
FROM pg_stat_replication;
```

**Solution**: 
- Check network bandwidth
- Optimize write workload
- Increase wal_sender processes
- Consider upgrading hardware

### Cache Issues

**Problem**: Low cache hit rate

```bash
# Check cache metrics
curl http://localhost:8000/metrics/json | jq '.cache'
```

**Solution**:
- Increase cache size
- Adjust TTL values
- Review cache invalidation logic
- Add cache warming

### Rate Limiting Issues

**Problem**: Legitimate users being rate limited

```bash
# Check rate limit stats
redis-cli -a password GET rate_limit:user:<user_id>
```

**Solution**:
- Increase per-user limits
- Implement tiered rate limiting
- Add whitelist for trusted IPs

### Performance Issues

**Problem**: Slow query performance

```bash
# Check slow queries
tail -f /var/log/postgresql/postgresql-14-main.log | grep "duration:"
```

**Solution**:
- Add missing indexes
- Optimize query patterns
- Enable query result caching
- Review N+1 queries

## Additional Resources

- [Database replication setup](database-replication-setup.md)
- [Valkey configuration](valkey-configuration.md)
- [Django integration](django-integration.md)
- [Monitoring overview](../monitoring/overview.md)
- [Monitoring configuration guide](../monitoring/configuration-guide.md)

## Support

For deployment assistance:
- Review logs in `/var/log/`
- Check metrics at `/metrics/json`
- Monitor dashboards in Grafana
- Contact DevOps team for infrastructure issues
