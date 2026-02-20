# Database and Caching Infrastructure

Comprehensive database and caching infrastructure optimization for high availability, reliability, and performance.

## Overview

This infrastructure provides:

- **Database Replication**: Primary-replica setup with automatic failover
- **Connection Pooling**: Efficient connection management (10-50 connections per instance)
- **Multi-Layer Caching**: L1 (in-memory LRU) and L2 (Redis) caching
- **Workload Isolation**: Automatic read/write routing
- **Rate Limiting**: Per-user (100 req/min) and global (10,000 req/min) limits
- **Health Monitoring**: Continuous health checks every 10 seconds
- **Load Balancing**: Weighted distribution across replicas
- **Circuit Breaking**: Automatic failure detection and recovery
- **Query Optimization**: Automatic query analysis and slow query detection
- **Schema Management**: Safe, transactional migrations with rollback support

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Set Up Database Replication

Follow the [database replication setup guide](database-replication-setup.md).

### 4. Configure Redis/Valkey

Follow the [Valkey configuration guide](valkey-configuration.md).

### 5. Enable Django Integration

Follow the [Django integration guide](django-integration.md).

### 6. Start Monitoring

```bash
cd ../monitoring
./setup.sh  # or setup.ps1 on Windows
```

### 7. Verify Installation

```bash
# Check health
curl http://localhost:8000/health

# Check metrics
curl http://localhost:8000/metrics/json

# View dashboards
open http://localhost:3000  # Grafana
```

## Documentation

### Getting Started

- [Deployment guide](deployment-guide.md) - Complete deployment instructions
- [Django integration](django-integration.md) - Integrate with Django application
- [Quick start section](deployment-guide.md#quick-start) - Get up and running in 15 minutes

### Configuration

- [Connection pool tuning](tuning-guide.md) - Optimize connection pool parameters
- [Rate limiting configuration](rate-limiting-guide.md) - Configure rate limits
- [Database replication setup](database-replication-setup.md) - Set up replication
- [Valkey configuration](valkey-configuration.md) - Configure Redis/Valkey
- [Monitoring configuration](../monitoring/configuration-guide.md) - Set up monitoring

### Operations

- [Operations runbook](operations-runbook.md) - Daily operations and incident response
- [Monitoring overview](../monitoring/overview.md) - Monitoring and alerting
- [Troubleshooting section](operations-runbook.md#troubleshooting) - Common issues and solutions

### Architecture

- [Architecture overview](../../architecture/infrastructure.md) - High-level infrastructure design
- [Production readiness review](../../operations/PRODUCTION_READINESS_REVIEW.md) - Operational requirements status
- [API documentation](../../architecture/api.md) - Endpoint and contract details

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Django Application                       │
├─────────────────────────────────────────────────────────────┤
│  Query Optimizer  │  Cache Manager  │  Rate Limiter         │
├─────────────────────────────────────────────────────────────┤
│  Connection Pool  │  Workload Isolator  │  Circuit Breaker  │
├─────────────────────────────────────────────────────────────┤
│  Health Monitor   │  Load Balancer      │  Metrics          │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐     ┌──────────────┐
│   Primary    │      │  Replica 1   │     │  Replica 2   │
│   Database   │─────▶│  Database    │     │  Database    │
└──────────────┘      └──────────────┘     └──────────────┘
        │
        │ Replication
        ▼
┌──────────────┐
│  Replica 3   │
│  Database    │
└──────────────┘

        ┌─────────────────────┐
        │   Redis Cluster     │
        │  (L2 Cache + Rate   │
        │   Limiting State)   │
        └─────────────────────┘
```

## Components

### Connection Pool Manager

Manages database connections with separate read/write pools.

**Features**:
- Min/max connection bounds (10-50)
- Idle connection cleanup (300s timeout)
- Connection lifetime management
- Pool statistics tracking

**Configuration**:
```python
CONNECTION_POOL_CONFIG = {
    'min_connections': 10,
    'max_connections': 50,
    'idle_timeout': 300,
    'max_lifetime': 3600,
}
```

**Documentation**: [Tuning guide](tuning-guide.md)

### Workload Isolator

Routes queries to appropriate database instances.

**Features**:
- Writes to primary, reads to replicas
- Priority-based routing for critical operations
- Replica lag checking (5s threshold)
- Automatic fallback to primary

**Configuration**:
```python
WORKLOAD_ISOLATION = {
    'enabled': True,
    'replica_lag_threshold': 5,
    'critical_operations_to_primary': True,
}
```

**Documentation**: [Django integration](django-integration.md)

### Cache Manager

Multi-layer caching with L1 (in-memory) and L2 (Redis).

**Features**:
- LRU cache for L1 (1000 entries, 60s TTL)
- Redis for L2 (configurable TTL)
- Tag-based invalidation
- Cache warming support
- Fail-open on Redis failure

**Configuration**:
```python
CACHE_CONFIG = {
    'l1_size': 1000,
    'l1_ttl': 60,
    'l2_ttl': 300,
    'tags_enabled': True,
}
```

**Documentation**: [Valkey configuration](valkey-configuration.md)

### Rate Limiter

Multi-layer rate limiting with sliding window algorithm.

**Features**:
- Per-user limits (100 queries/minute)
- Global limits (10,000 queries/minute)
- Admin bypass capability
- Distributed state via Redis

**Configuration**:
```python
RATE_LIMITING = {
    'per_user': {'queries_per_minute': 100},
    'global': {'queries_per_minute': 10000},
    'algorithm': 'sliding_window',
}
```

**Documentation**: [Rate limiting guide](rate-limiting-guide.md)

### Health Monitor

Monitors database instance health and triggers failover.

**Features**:
- Health checks every 10 seconds
- Monitors connectivity, lag, CPU, memory, disk
- Automatic failover within 30 seconds
- Alert notifications (email, Slack, PagerDuty)

**Configuration**:
```python
HEALTH_MONITORING = {
    'enabled': True,
    'interval': 10,
    'failover_timeout': 30,
}
```

**Documentation**: [Operations runbook](operations-runbook.md)

### Load Balancer

Distributes queries across healthy replicas.

**Features**:
- Weighted round-robin distribution
- CPU and response time based weighting
- Traffic reduction at 80% CPU
- Fallback to primary when all replicas unhealthy

**Configuration**:
```python
LOAD_BALANCING = {
    'algorithm': 'weighted_round_robin',
    'cpu_threshold': 80,
    'health_check_interval': 10,
}
```

**Documentation**: [Deployment guide](deployment-guide.md)

### Query Optimizer

Analyzes and optimizes database queries.

**Features**:
- Query execution plan analysis
- Slow query detection (100ms threshold)
- N+1 query pattern detection
- Index suggestion based on patterns

**Configuration**:
```python
QUERY_OPTIMIZATION = {
    'enabled': True,
    'slow_query_threshold': 100,
    'n_plus_one_detection': True,
}
```

**Documentation**: [Query optimizer integration](query-optimizer-integration.md)

### Circuit Breaker

Prevents cascading failures with automatic circuit breaking.

**Features**:
- Opens at 50% failure rate over 60s
- Half-open state after 30s for test connection
- Exponential backoff (1s, 2s, 4s)
- Separate circuits for read/write pools

**Configuration**:
```python
CIRCUIT_BREAKER = {
    'failure_threshold': 0.5,
    'timeout': 30,
    'backoff_multiplier': 2,
}
```

**Documentation**: [Django integration](django-integration.md)

### Metrics Collector

Collects and exposes metrics for monitoring.

**Features**:
- Database metrics (latency, throughput, errors)
- Cache metrics (hit rate, miss rate, evictions)
- Prometheus format export
- JSON format for debugging

**Endpoints**:
- `/metrics` - Prometheus format
- `/metrics/json` - JSON format
- `/health` - Health check

**Documentation**: [Monitoring overview](../monitoring/overview.md)

## Monitoring

### Dashboards

Access Grafana dashboards at http://localhost:3000:

- **Database Performance Metrics**: Query throughput, latency, error rates, connection pool, replication lag
- **Cache Performance Metrics**: Hit/miss rates, eviction rates, L1/L2 performance

### Alerts

Configured alerts for:

- High query latency (>100ms)
- High error rate (>5%)
- High connection pool utilization (>80%)
- High replication lag (>5s)
- Low cache hit rate (<70%)
- Instance health issues

### Metrics

Key metrics exposed:

```json
{
  "database": {
    "query_count": 12345,
    "avg_latency_ms": 45.23,
    "error_rate_percent": 0.5,
    "throughput_qps": 150.5
  },
  "cache": {
    "hits": 8900,
    "misses": 1100,
    "hit_rate_percent": 89.0,
    "eviction_rate_percent": 5.2
  },
  "connection_pool": {
    "total_connections": 45,
    "active_connections": 32,
    "utilization_percent": 71.1
  }
}
```

## Performance Characteristics

### Throughput

- **Database**: 10,000+ queries/second
- **Cache**: 50,000+ operations/second
- **Rate Limiting**: 100,000+ checks/second

### Latency

- **Cache Hit**: < 1ms (L1), < 5ms (L2)
- **Database Query**: < 50ms (average)
- **Connection Acquisition**: < 10ms

### Availability

- **Target**: 99.9% uptime
- **Failover Time**: < 30 seconds
- **Recovery Time Objective (RTO)**: < 5 minutes
- **Recovery Point Objective (RPO)**: < 1 minute

## Requirements Validation

This infrastructure validates all 12 requirements:

1. ✅ Query Performance Optimization (1.1-1.5)
2. ✅ High Availability Configuration (2.1-2.5)
3. ✅ Workload Isolation (3.1-3.5)
4. ✅ Connection Pool Management (4.1-4.5)
5. ✅ Multi-Layer Caching Strategy (5.1-5.5)
6. ✅ Cascading Replication Setup (6.1-6.5)
7. ✅ Multi-Layer Rate Limiting (7.1-7.5)
8. ✅ Schema Management and Versioning (8.1-8.5)
9. ✅ Load Balancing Across Replicas (9.1-9.5)
10. ✅ Monitoring and Observability (10.1-10.5)
11. ✅ Connection Retry and Circuit Breaking (11.1-11.5)
12. ✅ Cache Consistency and Invalidation (12.1-12.5)

## Testing

### Unit Tests

```bash
# Run all tests
pytest backend/tests/

# Run specific component tests
pytest backend/tests/test_connection_pool.py
pytest backend/tests/test_cache_manager.py
pytest backend/tests/test_rate_limiter.py
```

### Property-Based Tests

```bash
# Run property tests
pytest backend/tests/ -m property

# Run with more iterations
pytest backend/tests/ -m property --hypothesis-iterations=1000
```

### Integration Tests

```bash
# Run integration tests
pytest backend/tests/integration/
```

### Load Tests

```bash
# Run load tests
locust -f tests/locustfile.py --host=http://localhost:8000
```

## Troubleshooting

### Common Issues

1. **Connection Pool Exhausted**: See [Tuning guide](tuning-guide.md)
2. **High Replication Lag**: See [Operations runbook](operations-runbook.md#replication-lag)
3. **Low Cache Hit Rate**: See [Operations runbook](operations-runbook.md#cache-issues)
4. **Rate Limiting Issues**: See [Rate limiting guide](rate-limiting-guide.md#troubleshooting)

### Debug Commands

```bash
# Check system health
curl http://localhost:8000/health

# Check metrics
curl http://localhost:8000/metrics/json | jq

# Check database connections
psql -c "SELECT count(*) FROM pg_stat_activity;"

# Check Redis connectivity
redis-cli ping

# Check replication status
psql -c "SELECT * FROM pg_stat_replication;"

# View logs
tail -f /var/log/gunicorn/error.log
```

## Support

### Documentation

- [Deployment guide](deployment-guide.md)
- [Operations runbook](operations-runbook.md)
- [Troubleshooting section](operations-runbook.md#troubleshooting)
- [API documentation](../../architecture/api.md)

### Contact

- **Issues**: Create issue in repository
- **Questions**: Contact DevOps team
- **Emergency**: Follow [Operations runbook](operations-runbook.md)

## Contributing

See [CONTRIBUTING.md](../../../CONTRIBUTING.md) for guidelines.

## License

See [README license section](../../../README.md#license) for repository licensing details.

## Changelog

Release history is tracked in Git commit history.
