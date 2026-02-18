# Monitoring Alert Rules

## Overview

This document defines alert rules for production monitoring. Alerts are configured in Sentry, APM provider (New Relic/DataDog), and custom monitoring systems.

## Alert Severity Levels

| Level | Response Time | Notification Channels |
|-------|--------------|----------------------|
| Critical | Immediate | Email + Slack + PagerDuty |
| High | < 15 minutes | Email + Slack |
| Medium | < 1 hour | Slack |
| Low | < 4 hours | Slack (optional) |

## Critical Alerts (P0)

### 1. High Error Rate
**Condition**: Error rate > 5% for 5 minutes
**Severity**: Critical
**Channels**: Email + Slack + PagerDuty
**Action**: Immediate investigation required

### 2. Service Down
**Condition**: Health check fails for 2 consecutive checks
**Severity**: Critical
**Channels**: Email + Slack + PagerDuty
**Action**: Immediate investigation and recovery

### 3. Database Connection Pool Exhausted
**Condition**: Pool utilization > 90% for 5 minutes
**Severity**: Critical
**Channels**: Email + Slack + PagerDuty
**Action**: Scale database connections or investigate connection leaks

### 4. Extreme Latency
**Condition**: P99 response time > 2000ms for 10 minutes
**Severity**: Critical
**Channels**: Email + Slack
**Action**: Investigate performance bottleneck

## High Priority Alerts (P1)

### 5. Elevated Error Rate
**Condition**: Error rate > 1% for 10 minutes
**Severity**: High
**Channels**: Email + Slack
**Action**: Investigate error cause

### 6. Slow API Endpoints
**Condition**: P95 response time > 500ms for 10 minutes
**Severity**: High
**Channels**: Email + Slack
**Action**: Optimize slow endpoints

### 7. Database Pool High Utilization
**Condition**: Pool utilization > 80% for 10 minutes
**Severity**: High
**Channels**: Email + Slack
**Action**: Monitor and prepare to scale

### 8. Slow Database Queries
**Condition**: > 20 slow queries (>100ms) per minute for 10 minutes
**Severity**: High
**Channels**: Slack
**Action**: Optimize queries or add indexes

### 9. Cache Hit Rate Low
**Condition**: Cache hit rate < 60% for 15 minutes
**Severity**: High
**Channels**: Slack
**Action**: Investigate cache configuration

### 10. Celery Queue Backlog
**Condition**: Queue length > 1000 tasks for 10 minutes
**Severity**: High
**Channels**: Slack
**Action**: Scale workers or investigate slow tasks

## Medium Priority Alerts (P2)

### 11. Moderate Latency
**Condition**: P95 response time > 750ms for 15 minutes
**Severity**: Medium
**Channels**: Slack
**Action**: Monitor and investigate if persists

### 12. Disk Space Warning
**Condition**: Disk usage > 80%
**Severity**: Medium
**Channels**: Slack
**Action**: Clean up or expand storage

### 13. Memory Usage High
**Condition**: Memory usage > 85% for 15 minutes
**Severity**: Medium
**Channels**: Slack
**Action**: Investigate memory leaks

### 14. External Service Slow
**Condition**: External service P95 > 1000ms for 15 minutes
**Severity**: Medium
**Channels**: Slack
**Action**: Check external service status

### 15. Rate Limiting Active
**Condition**: > 100 rate limit hits per minute for 10 minutes
**Severity**: Medium
**Channels**: Slack
**Action**: Investigate if legitimate traffic or attack

## Low Priority Alerts (P3)

### 16. New Error Type
**Condition**: First occurrence of new error
**Severity**: Low
**Channels**: Slack
**Action**: Review and categorize

### 17. Deployment Notification
**Condition**: New deployment detected
**Severity**: Low
**Channels**: Slack
**Action**: Monitor for issues

### 18. Capacity Warning
**Condition**: Approaching capacity limits (70% of max)
**Severity**: Low
**Channels**: Slack
**Action**: Plan for scaling

## Alert Configuration Examples

### Sentry Alert Rules

```python
# In Sentry dashboard: Settings → Alerts → Create Alert Rule

# High Error Rate Alert
{
    "name": "High Error Rate",
    "conditions": [
        {
            "id": "sentry.rules.conditions.event_frequency.EventFrequencyCondition",
            "value": 100,
            "interval": "5m"
        }
    ],
    "actions": [
        {
            "id": "sentry.mail.actions.NotifyEmailAction",
            "targetType": "Team",
            "targetIdentifier": "engineering"
        },
        {
            "id": "sentry.integrations.slack.notify_action.SlackNotifyServiceAction",
            "workspace": "your-workspace",
            "channel": "#engineering-alerts"
        }
    ]
}
```

### New Relic Alert Conditions

```sql
-- API Response Time Alert
SELECT percentile(duration, 95) 
FROM Transaction 
WHERE appName = 'MueJam Backend' 
FACET name

-- Threshold: > 500ms for 5 minutes
-- Severity: Warning
```

```sql
-- Database Pool Utilization
SELECT average(database.pool.utilization) 
FROM Metric 
WHERE appName = 'MueJam Backend'

-- Threshold: > 0.8 for 5 minutes
-- Severity: Critical
```

### DataDog Monitor Queries

```
# Slow API Endpoints
avg(last_5m):avg:trace.django.request.duration{env:production} by {resource_name} > 0.5

# High Error Rate
sum(last_5m):sum:trace.django.request.errors{env:production}.as_count() > 100

# Database Connection Pool
avg(last_5m):avg:database.pool.utilization{env:production} > 0.8
```

## Alert Notification Templates

### Email Template

```
Subject: [{{ severity }}] {{ alert_name }} - MueJam Production

Alert: {{ alert_name }}
Severity: {{ severity }}
Time: {{ timestamp }}
Environment: {{ environment }}

Condition: {{ condition }}
Current Value: {{ current_value }}
Threshold: {{ threshold }}

Details:
{{ details }}

Dashboard: {{ dashboard_url }}
Runbook: {{ runbook_url }}

---
This is an automated alert from MueJam Monitoring
```

### Slack Template

```
:rotating_light: *{{ severity }} Alert*

*{{ alert_name }}*
Environment: `{{ environment }}`
Time: {{ timestamp }}

*Condition:* {{ condition }}
*Current Value:* {{ current_value }}
*Threshold:* {{ threshold }}

<{{ dashboard_url }}|View Dashboard> | <{{ runbook_url }}|View Runbook>
```

## Alert Response Procedures

### Critical Alerts

1. **Acknowledge** alert immediately
2. **Assess** impact and scope
3. **Communicate** to team via Slack
4. **Investigate** root cause
5. **Mitigate** issue (rollback, scale, fix)
6. **Monitor** for resolution
7. **Document** incident
8. **Post-mortem** within 48 hours

### High Priority Alerts

1. **Acknowledge** within 15 minutes
2. **Investigate** root cause
3. **Create** ticket if not immediate fix
4. **Monitor** for escalation
5. **Resolve** within SLA
6. **Document** resolution

### Medium/Low Priority Alerts

1. **Review** during business hours
2. **Create** ticket for tracking
3. **Prioritize** in backlog
4. **Resolve** based on priority

## Alert Tuning

### Reducing False Positives

1. **Adjust thresholds** based on baseline
2. **Increase time windows** for transient issues
3. **Add conditions** to filter noise
4. **Use anomaly detection** instead of static thresholds

### Preventing Alert Fatigue

1. **Consolidate** similar alerts
2. **Use alert dependencies** (don't alert on downstream effects)
3. **Implement** alert suppression during maintenance
4. **Review** and disable noisy alerts
5. **Set** appropriate severity levels

## Alert Testing

### Test Alert Delivery

```bash
# Test email alerts
python apps/backend/scripts/test_alerts.py --type email --severity critical

# Test Slack alerts
python apps/backend/scripts/test_alerts.py --type slack --severity high

# Test PagerDuty
python apps/backend/scripts/test_alerts.py --type pagerduty --severity critical
```

### Trigger Test Alerts

```python
# Trigger high error rate
for i in range(200):
    raise Exception(f"Test error {i}")

# Trigger slow endpoint
import time
def slow_endpoint(request):
    time.sleep(2)
    return JsonResponse({'status': 'ok'})
```

## Alert Metrics

Track alert effectiveness:
- **MTTA** (Mean Time To Acknowledge): < 5 minutes for critical
- **MTTR** (Mean Time To Resolve): < 30 minutes for critical
- **False Positive Rate**: < 10%
- **Alert Volume**: < 50 alerts/day
- **Alert Fatigue Score**: Monitor team response times

## Runbooks

Each alert should have a runbook:
- **Symptoms**: What the alert indicates
- **Impact**: User/business impact
- **Diagnosis**: How to investigate
- **Resolution**: Steps to fix
- **Prevention**: How to prevent recurrence

See `docs/operations/runbooks/` for specific runbooks.

## On-Call Rotation

- **Primary**: Responds to critical/high alerts
- **Secondary**: Backup for primary
- **Escalation**: Manager/senior engineer
- **Rotation**: Weekly rotation
- **Handoff**: Monday 9 AM

## Alert Review

- **Daily**: Review critical/high alerts
- **Weekly**: Review all alerts, tune thresholds
- **Monthly**: Alert effectiveness metrics
- **Quarterly**: Alert strategy review

## Resources

- Alert dashboard: [Link to dashboard]
- Runbooks: `docs/operations/runbooks/`
- Incident response: `docs/operations/incident-response.md`
- On-call schedule: [Link to PagerDuty/schedule]
