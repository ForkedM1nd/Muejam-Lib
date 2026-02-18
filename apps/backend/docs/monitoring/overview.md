# Monitoring and Alerting Setup

This directory contains the complete monitoring infrastructure for the MueJam Library backend, including Grafana dashboards, Prometheus configuration, and Alertmanager setup for notifications.

## Overview

The monitoring stack consists of:

- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards
- **Alertmanager**: Alert routing and notifications
- **PostgreSQL Exporter**: Database metrics
- **Redis Exporter**: Cache metrics

## Architecture

```
┌─────────────────┐
│  Django App     │──┐
│  (Port 8000)    │  │
└─────────────────┘  │
                     │ /metrics endpoint
┌─────────────────┐  │
│  PostgreSQL     │──┤
│  Exporter       │  │
│  (Port 9187)    │  │
└─────────────────┘  │
                     │
┌─────────────────┐  │
│  Redis          │──┤
│  Exporter       │  │
│  (Port 9121)    │  │
└─────────────────┘  │
                     ▼
              ┌─────────────┐
              │ Prometheus  │
              │ (Port 9090) │
              └──────┬──────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
   ┌─────────┐  ┌─────────┐  ┌──────────────┐
   │ Grafana │  │  Alert  │  │ Alert Rules  │
   │ (3000)  │  │ Manager │  │              │
   └─────────┘  │ (9093)  │  └──────────────┘
                └────┬────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
    ┌──────┐    ┌───────┐    ┌──────────┐
    │Email │    │ Slack │    │PagerDuty │
    └──────┘    └───────┘    └──────────┘
```

## Quick Start

### 1. Configuration

Copy the example environment file and configure your settings:

```bash
cd backend/monitoring
cp .env.example .env
```

Edit `.env` and set:
- Database credentials
- Redis credentials
- SMTP password for email alerts
- Slack webhook URL
- PagerDuty service key

### 2. Start Monitoring Stack

```bash
docker-compose -f docker-compose.monitoring.yml up -d
```

This will start:
- Prometheus on http://localhost:9090
- Grafana on http://localhost:3000
- Alertmanager on http://localhost:9093

### 3. Access Grafana

1. Open http://localhost:3000
2. Login with credentials from `.env` (default: admin/admin)
3. Navigate to Dashboards → Infrastructure
4. View "Database Performance Metrics" and "Cache Performance Metrics"

## Dashboards

### Database Performance Metrics

Located at: `grafana/dashboards/database_metrics.json`

**Panels:**
- Query Throughput (QPS)
- Average Query Latency
- Database Error Rate
- Slow Query Count
- Total Query Count
- Connection Pool Utilization
- Replication Lag

**Alerts:**
- High Query Throughput (>10,000 QPS)
- High Query Latency (>100ms)
- High Database Error Rate (>5%)
- High Connection Pool Utilization (>80%)
- High Replication Lag (>5s)

### Cache Performance Metrics

Located at: `grafana/dashboards/cache_performance.json`

**Panels:**
- Cache Hit Rate
- Cache Miss Rate
- Cache Operations (hits/misses per second)
- Cache Eviction Rate
- Total Cache Hits/Misses/Evictions
- L1 vs L2 Cache Performance

**Alerts:**
- Low Cache Hit Rate (<70%)
- High Cache Miss Rate (>30%)
- High Cache Eviction Rate (>20%)

## Alert Rules

### Database Alerts

Located at: `prometheus/alerts/database_alerts.yml`

**Warning Alerts (5-minute threshold):**
- HighQueryLatency: >100ms average
- HighDatabaseErrorRate: >5%
- HighQueryThroughput: >10,000 QPS
- HighConnectionPoolUtilization: >80%
- HighReplicationLag: >5s
- HighSlowQueryCount: >10 queries/sec

**Critical Alerts (2-minute threshold):**
- CriticalQueryLatency: >500ms average
- CriticalDatabaseErrorRate: >10%
- CriticalConnectionPoolUtilization: >95%
- CriticalReplicationLag: >30s
- DatabaseInstanceDown: Instance not responding

### Cache Alerts

Located at: `prometheus/alerts/cache_alerts.yml`

**Warning Alerts (5-minute threshold):**
- LowCacheHitRate: <70%
- HighCacheMissRate: >30%
- HighCacheEvictionRate: >20%
- HighRedisMemoryUsage: >90%
- HighRedisConnectionCount: >1000 clients

**Critical Alerts (2-minute threshold):**
- CriticalCacheHitRate: <50%
- CriticalCacheEvictionRate: >50%
- RedisInstanceDown: Instance not responding

## Notification Channels

### Email Notifications

Configured in `alertmanager/alertmanager.yml`

**Recipients:**
- `ops-team@muejam-library.com`: All alerts
- `oncall@muejam-library.com`: Critical alerts only
- `database-team@muejam-library.com`: Database-specific alerts
- `cache-team@muejam-library.com`: Cache-specific alerts

**Configuration:**
```yaml
smtp_smarthost: 'smtp.gmail.com:587'
smtp_from: 'alerts@muejam-library.com'
smtp_auth_username: 'alerts@muejam-library.com'
smtp_auth_password: '${SMTP_PASSWORD}'
```

### Slack Notifications

**Channels:**
- `#critical-alerts`: Critical severity alerts
- `#alerts`: Warning severity alerts
- `#database-alerts`: Database component alerts
- `#cache-alerts`: Cache component alerts

**Configuration:**
Set `SLACK_WEBHOOK_URL` in `.env` file.

### PagerDuty Integration

Critical alerts are sent to PagerDuty for on-call escalation.

**Configuration:**
Set `PAGERDUTY_SERVICE_KEY` in `.env` file.

## Metrics Endpoints

### Prometheus Format

**Endpoint:** `http://localhost:8000/metrics`

Returns metrics in Prometheus text format for scraping.

**Example:**
```
# HELP db_query_count Total number of database queries
# TYPE db_query_count counter
db_query_count 12345

# HELP db_avg_latency_ms Average query latency in milliseconds
# TYPE db_avg_latency_ms gauge
db_avg_latency_ms 45.23
```

### JSON Format

**Endpoint:** `http://localhost:8000/metrics/json`

Returns metrics in JSON format for debugging and custom integrations.

**Example:**
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
  "timestamp": "2026-02-17T10:30:00Z"
}
```

### Health Check

**Endpoint:** `http://localhost:8000/health`

Simple health check for load balancers and monitoring.

## Prometheus Configuration

Located at: `prometheus/prometheus.yml`

**Scrape Intervals:**
- Django app: 10s
- PostgreSQL: 10s
- Redis: 10s

**Retention:**
- Time-series data: 30 days

**Alert Evaluation:**
- Interval: 10s

## Customization

### Adding New Dashboards

1. Create JSON file in `grafana/dashboards/`
2. Restart Grafana: `docker-compose -f docker-compose.monitoring.yml restart grafana`
3. Dashboard will auto-load via provisioning

### Adding New Alerts

1. Create/edit YAML file in `prometheus/alerts/`
2. Reload Prometheus: `curl -X POST http://localhost:9090/-/reload`

### Modifying Alert Routes

1. Edit `alertmanager/alertmanager.yml`
2. Reload Alertmanager: `curl -X POST http://localhost:9093/-/reload`

## Troubleshooting

### Prometheus Not Scraping Metrics

1. Check Django app is running: `curl http://localhost:8000/health`
2. Check metrics endpoint: `curl http://localhost:8000/metrics`
3. Check Prometheus targets: http://localhost:9090/targets

### Alerts Not Firing

1. Check alert rules: http://localhost:9090/alerts
2. Check Alertmanager: http://localhost:9093
3. Verify alert conditions in `prometheus/alerts/*.yml`

### Grafana Dashboards Not Loading

1. Check provisioning config: `grafana/provisioning/dashboards.yml`
2. Check dashboard files exist in `grafana/dashboards/`
3. Check Grafana logs: `docker logs muejam-grafana`

### Notifications Not Sending

1. Verify environment variables in `.env`
2. Check Alertmanager config: `alertmanager/alertmanager.yml`
3. Check Alertmanager logs: `docker logs muejam-alertmanager`
4. Test notification channels manually

## Maintenance

### Backup Grafana Dashboards

```bash
docker exec muejam-grafana grafana-cli admin export-dashboard > backup.json
```

### Backup Prometheus Data

```bash
docker exec muejam-prometheus promtool tsdb snapshot /prometheus
```

### Clean Old Data

Prometheus automatically removes data older than retention period (30 days).

To manually clean:
```bash
docker exec muejam-prometheus promtool tsdb clean /prometheus
```

## Requirements Validation

This monitoring setup validates the following requirements:

- **Requirement 10.1**: Database metrics exposure (latency, throughput, error rates)
- **Requirement 10.2**: Cache metrics exposure (hit rate, miss rate, eviction rate)
- **Requirement 10.3**: Slow query logging and monitoring
- **Requirement 10.4**: Threshold breach alerts
- **Requirement 10.5**: Monitoring dashboards with connection pool, replication lag, and query performance

## Security Considerations

1. **Credentials**: Store all credentials in `.env` file (not in version control)
2. **Network**: Use Docker networks to isolate monitoring stack
3. **Access Control**: Configure Grafana authentication and user roles
4. **HTTPS**: Use reverse proxy (nginx) with SSL for production
5. **Firewall**: Restrict access to monitoring ports (9090, 3000, 9093)

## Production Deployment

For production deployment:

1. Use external Prometheus/Grafana instances (managed services)
2. Configure persistent volumes for data retention
3. Set up high availability for Alertmanager
4. Use secrets management (Vault, AWS Secrets Manager)
5. Configure backup and disaster recovery
6. Set up log aggregation (ELK, Loki)
7. Enable authentication and authorization
8. Use HTTPS with valid certificates
9. Configure rate limiting on metrics endpoints
10. Set up monitoring for the monitoring stack itself

## Support

For issues or questions:
- Check logs: `docker-compose -f docker-compose.monitoring.yml logs`
- Prometheus documentation: https://prometheus.io/docs/
- Grafana documentation: https://grafana.com/docs/
- Alertmanager documentation: https://prometheus.io/docs/alerting/latest/alertmanager/
