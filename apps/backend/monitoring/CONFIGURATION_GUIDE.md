# Monitoring Configuration Guide

This guide provides detailed instructions for configuring the monitoring infrastructure for different environments and use cases.

## Table of Contents

1. [Environment Configuration](#environment-configuration)
2. [Email Notifications](#email-notifications)
3. [Slack Integration](#slack-integration)
4. [PagerDuty Integration](#pagerduty-integration)
5. [Custom Alert Rules](#custom-alert-rules)
6. [Dashboard Customization](#dashboard-customization)
7. [Metric Thresholds](#metric-thresholds)
8. [Production Best Practices](#production-best-practices)

## Environment Configuration

### Development Environment

For local development, minimal configuration is needed:

```bash
# .env
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=admin

DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
DB_NAME=muejam_library

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
```

### Staging Environment

For staging, configure basic alerting:

```bash
# .env
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=<strong-password>

DB_USER=postgres
DB_PASSWORD=<db-password>
DB_HOST=postgres-staging
DB_PORT=5432
DB_NAME=muejam_library_staging

REDIS_HOST=redis-staging
REDIS_PORT=6379
REDIS_PASSWORD=<redis-password>

# Email notifications only
SMTP_PASSWORD=<smtp-password>
```

### Production Environment

For production, configure all notification channels:

```bash
# .env
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=<strong-password>

DB_USER=postgres
DB_PASSWORD=<db-password>
DB_HOST=postgres-primary
DB_PORT=5432
DB_NAME=muejam_library

REDIS_HOST=redis-cluster
REDIS_PORT=6379
REDIS_PASSWORD=<redis-password>

# All notification channels
SMTP_PASSWORD=<smtp-password>
SLACK_WEBHOOK_URL=<slack-webhook>
PAGERDUTY_SERVICE_KEY=<pagerduty-key>
```

## Email Notifications

### Gmail Configuration

1. Enable 2-factor authentication on your Gmail account
2. Generate an app-specific password:
   - Go to Google Account → Security → App passwords
   - Select "Mail" and "Other (Custom name)"
   - Copy the generated password

3. Configure in `.env`:
```bash
SMTP_PASSWORD=<app-specific-password>
```

4. Update `alertmanager/alertmanager.yml`:
```yaml
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alerts@yourdomain.com'
  smtp_auth_username: 'your-email@gmail.com'
  smtp_auth_password: '${SMTP_PASSWORD}'
  smtp_require_tls: true
```

### Custom SMTP Server

For custom SMTP servers:

```yaml
global:
  smtp_smarthost: 'smtp.yourserver.com:587'
  smtp_from: 'alerts@yourdomain.com'
  smtp_auth_username: 'smtp-user'
  smtp_auth_password: '${SMTP_PASSWORD}'
  smtp_require_tls: true
```

### Email Recipients

Configure recipients in `alertmanager/alertmanager.yml`:

```yaml
receivers:
  - name: 'ops-team'
    email_configs:
      - to: 'ops@yourdomain.com'
        headers:
          Subject: '[{{ .Status | toUpper }}] {{ .GroupLabels.alertname }}'
```

## Slack Integration

### Create Slack Webhook

1. Go to https://api.slack.com/apps
2. Create a new app or select existing
3. Enable "Incoming Webhooks"
4. Add webhook to workspace
5. Copy webhook URL

### Configure Slack Notifications

1. Set webhook in `.env`:
```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

2. Configure channels in `alertmanager/alertmanager.yml`:
```yaml
receivers:
  - name: 'critical-alerts'
    slack_configs:
      - api_url: '${SLACK_WEBHOOK_URL}'
        channel: '#critical-alerts'
        title: ':fire: Critical Alert'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
        color: 'danger'
```

### Custom Slack Messages

Customize message format:

```yaml
slack_configs:
  - api_url: '${SLACK_WEBHOOK_URL}'
    channel: '#alerts'
    title: 'Alert: {{ .GroupLabels.alertname }}'
    text: |
      *Summary:* {{ .CommonAnnotations.summary }}
      *Description:* {{ .CommonAnnotations.description }}
      *Severity:* {{ .CommonLabels.severity }}
      *Component:* {{ .CommonLabels.component }}
    color: '{{ if eq .Status "firing" }}danger{{ else }}good{{ end }}'
    fields:
      - title: 'Environment'
        value: '{{ .CommonLabels.cluster }}'
        short: true
      - title: 'Instance'
        value: '{{ .CommonLabels.instance }}'
        short: true
```

## PagerDuty Integration

### Create PagerDuty Service

1. Go to PagerDuty → Services
2. Create new service or select existing
3. Add integration → Prometheus
4. Copy integration key

### Configure PagerDuty

1. Set key in `.env`:
```bash
PAGERDUTY_SERVICE_KEY=your-integration-key
```

2. Configure in `alertmanager/alertmanager.yml`:
```yaml
receivers:
  - name: 'critical-alerts'
    pagerduty_configs:
      - service_key: '${PAGERDUTY_SERVICE_KEY}'
        description: '{{ .GroupLabels.alertname }}: {{ .CommonAnnotations.summary }}'
        severity: '{{ .CommonLabels.severity }}'
        details:
          firing: '{{ template "pagerduty.default.instances" .Alerts.Firing }}'
          resolved: '{{ template "pagerduty.default.instances" .Alerts.Resolved }}'
```

### PagerDuty Escalation Policies

Configure escalation in PagerDuty dashboard:
1. Services → Your Service → Escalation Policy
2. Set escalation levels and timeouts
3. Configure on-call schedules

## Custom Alert Rules

### Adding New Alert Rules

1. Create new file in `prometheus/alerts/`:

```yaml
# prometheus/alerts/custom_alerts.yml
groups:
  - name: custom_alerts
    interval: 30s
    rules:
      - alert: CustomMetricHigh
        expr: custom_metric > 100
        for: 5m
        labels:
          severity: warning
          component: custom
        annotations:
          summary: "Custom metric is high"
          description: "Custom metric value is {{ $value }}"
```

2. Reload Prometheus:
```bash
curl -X POST http://localhost:9090/-/reload
```

### Modifying Existing Alerts

Edit alert files in `prometheus/alerts/`:

```yaml
# Change threshold
- alert: HighQueryLatency
  expr: db_avg_latency_ms > 200  # Changed from 100
  for: 5m
```

### Alert Severity Levels

Use consistent severity levels:

- **critical**: Immediate action required, service degradation
- **warning**: Attention needed, potential issues
- **info**: Informational, no action required

## Dashboard Customization

### Modifying Existing Dashboards

1. Edit JSON files in `grafana/dashboards/`
2. Restart Grafana:
```bash
docker-compose -f docker-compose.monitoring.yml restart grafana
```

### Adding New Panels

Add panel to dashboard JSON:

```json
{
  "id": 10,
  "title": "Custom Metric",
  "type": "graph",
  "gridPos": {"x": 0, "y": 24, "w": 12, "h": 8},
  "targets": [
    {
      "expr": "custom_metric",
      "legendFormat": "Custom Metric",
      "refId": "A"
    }
  ]
}
```

### Creating New Dashboards

1. Create in Grafana UI
2. Export JSON
3. Save to `grafana/dashboards/`
4. Add to provisioning config

## Metric Thresholds

### Database Thresholds

Recommended thresholds for database metrics:

| Metric | Warning | Critical | Notes |
|--------|---------|----------|-------|
| Query Latency | 100ms | 500ms | Average over 5 minutes |
| Error Rate | 5% | 10% | Percentage of failed queries |
| Throughput | 10,000 QPS | 15,000 QPS | Queries per second |
| Pool Utilization | 80% | 95% | Connection pool usage |
| Replication Lag | 5s | 30s | Lag behind primary |

### Cache Thresholds

Recommended thresholds for cache metrics:

| Metric | Warning | Critical | Notes |
|--------|---------|----------|-------|
| Hit Rate | <70% | <50% | Percentage of cache hits |
| Miss Rate | >30% | >50% | Percentage of cache misses |
| Eviction Rate | >20% | >50% | Percentage of evictions |
| Memory Usage | >80% | >95% | Redis memory usage |

### Adjusting Thresholds

Edit alert rules in `prometheus/alerts/*.yml`:

```yaml
- alert: HighQueryLatency
  expr: db_avg_latency_ms > 150  # Adjust threshold
  for: 10m  # Adjust duration
```

## Production Best Practices

### Security

1. **Use strong passwords**:
```bash
GRAFANA_ADMIN_PASSWORD=$(openssl rand -base64 32)
```

2. **Enable HTTPS**:
   - Use reverse proxy (nginx, Traefik)
   - Configure SSL certificates
   - Redirect HTTP to HTTPS

3. **Restrict network access**:
   - Use firewall rules
   - Configure Docker networks
   - Use VPN for remote access

4. **Secrets management**:
   - Use AWS Secrets Manager, Vault, or similar
   - Rotate credentials regularly
   - Never commit secrets to version control

### High Availability

1. **Prometheus HA**:
   - Run multiple Prometheus instances
   - Use Thanos for long-term storage
   - Configure federation

2. **Grafana HA**:
   - Use external database (PostgreSQL)
   - Run multiple Grafana instances
   - Use load balancer

3. **Alertmanager HA**:
   - Run multiple Alertmanager instances
   - Configure clustering
   - Use gossip protocol

### Data Retention

Configure retention policies:

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

# Command line flags
--storage.tsdb.retention.time=90d
--storage.tsdb.retention.size=100GB
```

### Backup and Recovery

1. **Prometheus snapshots**:
```bash
curl -X POST http://localhost:9090/api/v1/admin/tsdb/snapshot
```

2. **Grafana backup**:
```bash
docker exec muejam-grafana grafana-cli admin export-dashboard > backup.json
```

3. **Automated backups**:
   - Schedule daily backups
   - Store in S3 or similar
   - Test recovery procedures

### Performance Optimization

1. **Reduce scrape frequency** for non-critical metrics
2. **Use recording rules** for expensive queries
3. **Configure retention** based on storage capacity
4. **Use remote storage** for long-term data
5. **Optimize dashboard queries** to reduce load

### Monitoring the Monitors

Monitor the monitoring stack itself:

```yaml
# prometheus/alerts/meta_alerts.yml
groups:
  - name: meta_alerts
    rules:
      - alert: PrometheusDown
        expr: up{job="prometheus"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Prometheus is down"
      
      - alert: GrafanaDown
        expr: up{job="grafana"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Grafana is down"
```

## Troubleshooting

### Common Issues

1. **Metrics not appearing**:
   - Check Django app is exposing metrics
   - Verify Prometheus scrape config
   - Check network connectivity

2. **Alerts not firing**:
   - Verify alert rules syntax
   - Check Prometheus evaluation
   - Verify Alertmanager routing

3. **Notifications not sending**:
   - Check credentials in `.env`
   - Verify Alertmanager config
   - Test notification channels manually

### Debug Commands

```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check alert rules
curl http://localhost:9090/api/v1/rules

# Check Alertmanager status
curl http://localhost:9093/api/v1/status

# Test alert
curl -X POST http://localhost:9093/api/v1/alerts \
  -H "Content-Type: application/json" \
  -d '[{"labels":{"alertname":"TestAlert","severity":"warning"}}]'
```

## Support

For additional help:
- Prometheus: https://prometheus.io/docs/
- Grafana: https://grafana.com/docs/
- Alertmanager: https://prometheus.io/docs/alerting/
