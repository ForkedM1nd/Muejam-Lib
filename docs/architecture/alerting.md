# Alerting System with PagerDuty Integration

This document describes the intelligent alerting system with PagerDuty integration for the MueJam Library platform.

## Overview

The platform uses PagerDuty for on-call management and intelligent alerting. The system includes alert severity levels, deduplication, maintenance window suppression, and automatic escalation.

**Implements Requirements:** 16.1-16.13 from production-readiness spec

## Features

- **PagerDuty Integration** (Requirement 16.1)
- **Alert Severity Levels** (Requirement 16.2): critical, high, medium, low
- **Critical Alert Rules** (Requirement 16.3): service downtime, database failures, high error rate, slow API
- **High Alert Rules** (Requirement 16.4): disk space, memory usage, cache failures, external service degradation
- **Medium Alert Rules** (Requirement 16.5): elevated error rate, slow queries, rate limiting, suspicious activity
- **Multi-Channel Paging** (Requirement 16.6): phone, SMS, push notifications for critical alerts
- **Acknowledgment Tracking** (Requirement 16.7): track time to acknowledgment
- **Resolution Tracking** (Requirement 16.8): record resolution time and require notes
- **Alert Deduplication** (Requirement 16.9): prevent duplicate alerts
- **Maintenance Window Suppression** (Requirement 16.10): suppress alerts during maintenance
- **Alert Dashboards** (Requirement 16.11): MTTR, MTTA, alert history
- **Daily Summary Reports** (Requirement 16.12): system health and alert activity
- **Automatic Escalation** (Requirement 16.13): escalate unacknowledged critical alerts after 15 minutes

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Django Application                        │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         AlertingService                                │ │
│  │  - Send alerts                                         │ │
│  │  - Acknowledge/resolve alerts                          │ │
│  │  - Track incidents                                     │ │
│  │  - Deduplication                                       │ │
│  │  - Maintenance window suppression                      │ │
│  └────────────────────────────────────────────────────────┘ │
│                           │                                  │
└───────────────────────────┼──────────────────────────────────┘
                            │
                            │ HTTPS
                            │
                    ┌───────▼────────┐
                    │   PagerDuty    │
                    │  Events API    │
                    └───────┬────────┘
                            │
            ┌───────────────┼───────────────┐
            │               │               │
    ┌───────▼────────┐ ┌───▼────┐ ┌───────▼────────┐
    │  Phone Call    │ │  SMS   │ │ Push Notification│
    └────────────────┘ └────────┘ └─────────────────┘
```

## Configuration

### Environment Variables

```bash
# PagerDuty Configuration (Requirement 16.1)
PAGERDUTY_ENABLED=True                          # Enable PagerDuty integration
PAGERDUTY_INTEGRATION_KEY=your_integration_key  # PagerDuty integration key
PAGERDUTY_API_KEY=your_api_key                  # PagerDuty API key (for REST API)

# Alert Escalation (Requirement 16.13)
ALERT_ESCALATION_TIMEOUT=15                     # Escalation timeout (minutes)

# Maintenance Windows (Requirement 16.10)
MAINTENANCE_MODE=False                          # Enable maintenance mode
MAINTENANCE_START=2024-02-17T02:00:00Z         # Maintenance start time (ISO 8601)
MAINTENANCE_END=2024-02-17T04:00:00Z           # Maintenance end time (ISO 8601)

# Alert Deduplication (Requirement 16.9)
ALERT_DEDUP_WINDOW=300                          # Deduplication window (seconds)

# Daily Summary (Requirement 16.12)
ALERT_SUMMARY_EMAIL_ENABLED=True                # Enable daily summary emails
ALERT_SUMMARY_EMAIL_RECIPIENTS=ops@muejam.com,eng@muejam.com
ALERT_SUMMARY_EMAIL_TIME=09:00                  # Summary email time (HH:MM)
```

### PagerDuty Setup

1. **Create a PagerDuty account**: https://www.pagerduty.com/

2. **Create a service**:
   - Go to Services → Service Directory
   - Click "New Service"
   - Name: "MueJam Library Backend"
   - Integration: Events API v2
   - Escalation Policy: Create or select existing
   - Save the Integration Key

3. **Configure escalation policy**:
   - Level 1: Primary on-call engineer (immediate)
   - Level 2: Backup on-call engineer (after 15 minutes)
   - Level 3: Engineering manager (after 30 minutes)

4. **Set up notification rules**:
   - Phone call for critical alerts
   - SMS for high alerts
   - Push notification for all alerts

## Usage

### Sending Alerts

```python
from infrastructure.alerting_service import get_alerting_service, AlertSeverity

# Get alerting service
alerting = get_alerting_service()

# Send a critical alert
incident_id = alerting.send_alert(
    severity=AlertSeverity.CRITICAL,
    title='Database Connection Failure',
    description='Unable to connect to PostgreSQL database',
    source='database',
    metadata={
        'host': 'db.muejam.com',
        'error': 'Connection timeout',
    },
)

# Send a high alert
alerting.send_alert(
    severity=AlertSeverity.HIGH,
    title='High Memory Usage',
    description='Memory usage at 92%',
    source='system',
    metadata={
        'memory_usage': 0.92,
        'threshold': 0.90,
    },
)

# Send a medium alert
alerting.send_alert(
    severity=AlertSeverity.MEDIUM,
    title='Slow Database Queries',
    description='Multiple queries exceeding 100ms threshold',
    source='database',
    metadata={
        'slow_query_count': 15,
        'avg_duration_ms': 150,
    },
)
```

### Acknowledging Alerts

```python
from infrastructure.alerting_service import get_alerting_service

alerting = get_alerting_service()

# Acknowledge an alert
success = alerting.acknowledge_alert(incident_id='incident_123')

if success:
    print("Alert acknowledged")
```

### Resolving Alerts

```python
from infrastructure.alerting_service import get_alerting_service

alerting = get_alerting_service()

# Resolve an alert (resolution notes required)
success = alerting.resolve_alert(
    incident_id='incident_123',
    resolution_notes='Database connection restored after restarting connection pool',
)

if success:
    print("Alert resolved")
```

### Using Alert Rules

```python
from infrastructure.alerting_service import get_alerting_service, AlertRules

alerting = get_alerting_service()

# Use predefined alert rules
rule = AlertRules.CRITICAL_RULES['database_connection_failure']

alerting.send_alert(
    severity=rule['severity'],
    title=rule['title'],
    description=rule['description'],
    source='database',
)
```

## Alert Severity Levels

### Critical (Immediate Response)

**Response Time:** Immediate

**Notification:** Phone call, SMS, push notification

**Examples:**
- Service downtime
- Database connection failures
- Error rate > 5%
- API p99 response time > 2000ms

**Usage:**
```python
alerting.send_alert(
    severity=AlertSeverity.CRITICAL,
    title='Service Downtime',
    description='Health check failing',
    source='health_check',
)
```

### High (1 Hour Response)

**Response Time:** 1 hour

**Notification:** SMS, push notification

**Examples:**
- Disk space > 85%
- Memory usage > 90%
- Cache failures
- External service degradation

**Usage:**
```python
alerting.send_alert(
    severity=AlertSeverity.HIGH,
    title='High Disk Space Usage',
    description='Disk usage at 87%',
    source='system',
    metadata={'disk_usage': 0.87},
)
```

### Medium (4 Hour Response)

**Response Time:** 4 hours

**Notification:** Push notification, email

**Examples:**
- Error rate > 1%
- Slow queries
- Elevated rate limiting
- Suspicious activity patterns

**Usage:**
```python
alerting.send_alert(
    severity=AlertSeverity.MEDIUM,
    title='Elevated Error Rate',
    description='Error rate at 2.5%',
    source='api',
    metadata={'error_rate': 0.025},
)
```

### Low (Next Business Day)

**Response Time:** Next business day

**Notification:** Email

**Examples:**
- Non-critical warnings
- Informational alerts
- Scheduled maintenance reminders

**Usage:**
```python
alerting.send_alert(
    severity=AlertSeverity.LOW,
    title='Scheduled Maintenance Reminder',
    description='Maintenance window in 24 hours',
    source='scheduler',
)
```

## Alert Deduplication

The system automatically deduplicates alerts within a 5-minute window (configurable).

**How it works:**
1. Each alert has a deduplication key (auto-generated or custom)
2. If an alert with the same dedup key is sent within the window, it's suppressed
3. After the window expires, new alerts are allowed

**Example:**
```python
# First alert - sent
alerting.send_alert(
    severity=AlertSeverity.CRITICAL,
    title='Database Connection Failure',
    description='Connection timeout',
    source='database',
    dedup_key='db_connection_failure',
)

# Second alert within 5 minutes - suppressed
alerting.send_alert(
    severity=AlertSeverity.CRITICAL,
    title='Database Connection Failure',
    description='Connection timeout',
    source='database',
    dedup_key='db_connection_failure',  # Same key
)

# After 5 minutes - sent
alerting.send_alert(
    severity=AlertSeverity.CRITICAL,
    title='Database Connection Failure',
    description='Connection timeout',
    source='database',
    dedup_key='db_connection_failure',
)
```

## Maintenance Windows

Suppress alerts during planned maintenance windows.

**Configuration:**
```bash
MAINTENANCE_MODE=True
MAINTENANCE_START=2024-02-17T02:00:00Z
MAINTENANCE_END=2024-02-17T04:00:00Z
```

**During maintenance:**
- All alerts are suppressed
- Alerts are logged but not sent to PagerDuty
- Maintenance mode can be enabled/disabled dynamically

**Example:**
```python
from infrastructure.alerting_service import get_alerting_service

alerting = get_alerting_service()

# This alert will be suppressed during maintenance
alerting.send_alert(
    severity=AlertSeverity.CRITICAL,
    title='Database Connection Failure',
    description='Expected during maintenance',
    source='database',
)
# Output: "Alert suppressed during maintenance: Database Connection Failure"
```

## Alert Escalation

Unacknowledged critical alerts are automatically escalated after 15 minutes.

**How it works:**
1. Critical alert is triggered
2. Primary on-call engineer is paged
3. If not acknowledged within 15 minutes, escalate to backup
4. Continue escalation per PagerDuty escalation policy

**Checking for escalation:**
```python
from infrastructure.alerting_service import get_alerting_service

alerting = get_alerting_service()

# Check for incidents needing escalation
incidents_to_escalate = alerting.check_escalation()

for incident_id in incidents_to_escalate:
    print(f"Incident {incident_id} needs escalation")
    # PagerDuty handles escalation automatically
```

## Alert Metrics and Dashboards

Track alert metrics for performance monitoring.

**Get incident metrics:**
```python
from infrastructure.alerting_service import get_alerting_service

alerting = get_alerting_service()

metrics = alerting.get_incident_metrics()

print(f"Total incidents: {metrics['total_incidents']}")
print(f"Active incidents: {metrics['active_incidents']}")
print(f"Resolved incidents: {metrics['resolved_incidents']}")
print(f"MTTR: {metrics['mttr_minutes']:.2f} minutes")
print(f"MTTA: {metrics['mtta_minutes']:.2f} minutes")
```

**Metrics:**
- **Total Incidents**: Total number of incidents
- **Active Incidents**: Currently unresolved incidents
- **Resolved Incidents**: Successfully resolved incidents
- **MTTR** (Mean Time To Resolution): Average time to resolve incidents
- **MTTA** (Mean Time To Acknowledgment): Average time to acknowledge incidents

## Integration with Monitoring

### Sentry Integration

```python
from infrastructure.alerting_service import get_alerting_service, AlertSeverity

def sentry_before_send(event, hint):
    """Send critical errors to PagerDuty."""
    if event.get('level') == 'error':
        error_rate = calculate_error_rate()
        
        if error_rate > 0.05:  # 5% threshold
            alerting = get_alerting_service()
            alerting.send_alert(
                severity=AlertSeverity.CRITICAL,
                title='High Error Rate',
                description=f'Error rate at {error_rate:.2%}',
                source='sentry',
                metadata={
                    'error_rate': error_rate,
                    'event_id': event.get('event_id'),
                },
            )
    
    return event
```

### APM Integration

```python
from infrastructure.alerting_service import get_alerting_service, AlertSeverity
from infrastructure.apm_config import PerformanceMonitor

def check_api_performance():
    """Check API performance and alert if slow."""
    # Get p99 response time from APM
    p99_ms = get_p99_response_time()
    
    if p99_ms > 2000:  # 2000ms threshold
        alerting = get_alerting_service()
        alerting.send_alert(
            severity=AlertSeverity.CRITICAL,
            title='Slow API Response Time',
            description=f'API p99 at {p99_ms}ms',
            source='apm',
            metadata={
                'p99_ms': p99_ms,
                'threshold_ms': 2000,
            },
        )
```

### Database Monitoring

```python
from infrastructure.alerting_service import get_alerting_service, AlertSeverity

def check_database_health():
    """Check database health and alert if issues."""
    try:
        # Test database connection
        db.execute('SELECT 1')
    except Exception as e:
        alerting = get_alerting_service()
        alerting.send_alert(
            severity=AlertSeverity.CRITICAL,
            title='Database Connection Failure',
            description=f'Unable to connect: {str(e)}',
            source='database',
            metadata={
                'error': str(e),
                'host': settings.DATABASE_HOST,
            },
        )
```

## Daily Summary Reports

Automated daily summary emails with system health and alert activity.

**Configuration:**
```bash
ALERT_SUMMARY_EMAIL_ENABLED=True
ALERT_SUMMARY_EMAIL_RECIPIENTS=ops@muejam.com,eng@muejam.com
ALERT_SUMMARY_EMAIL_TIME=09:00
```

**Summary includes:**
- Total alerts in last 24 hours
- Alerts by severity
- MTTR and MTTA
- Top alert sources
- Unresolved incidents
- System health status

**Implementation:**
```python
from infrastructure.alerting_service import get_alerting_service

def send_daily_summary():
    """Send daily alert summary email."""
    alerting = get_alerting_service()
    metrics = alerting.get_incident_metrics()
    
    # Generate summary
    summary = f"""
    Daily Alert Summary - {datetime.now().strftime('%Y-%m-%d')}
    
    Incidents:
    - Total: {metrics['total_incidents']}
    - Active: {metrics['active_incidents']}
    - Resolved: {metrics['resolved_incidents']}
    
    Performance:
    - MTTR: {metrics['mttr_minutes']:.2f} minutes
    - MTTA: {metrics['mtta_minutes']:.2f} minutes
    """
    
    # Send email
    send_email(
        to=AlertingConfig.SUMMARY_EMAIL_RECIPIENTS,
        subject='Daily Alert Summary',
        body=summary,
    )
```

## Testing

### Unit Tests

```python
from infrastructure.alerting_service import AlertingService, AlertSeverity

def test_send_alert():
    """Test sending an alert."""
    alerting = AlertingService()
    
    incident_id = alerting.send_alert(
        severity=AlertSeverity.CRITICAL,
        title='Test Alert',
        description='Test description',
        source='test',
    )
    
    assert incident_id is not None

def test_alert_deduplication():
    """Test alert deduplication."""
    alerting = AlertingService()
    
    # First alert
    id1 = alerting.send_alert(
        severity=AlertSeverity.CRITICAL,
        title='Test Alert',
        description='Test',
        source='test',
        dedup_key='test_key',
    )
    
    # Duplicate alert (should be suppressed)
    id2 = alerting.send_alert(
        severity=AlertSeverity.CRITICAL,
        title='Test Alert',
        description='Test',
        source='test',
        dedup_key='test_key',
    )
    
    assert id1 is not None
    assert id2 is None  # Suppressed

def test_maintenance_window():
    """Test maintenance window suppression."""
    alerting = AlertingService()
    alerting.config.MAINTENANCE_MODE = True
    
    incident_id = alerting.send_alert(
        severity=AlertSeverity.CRITICAL,
        title='Test Alert',
        description='Test',
        source='test',
    )
    
    assert incident_id is None  # Suppressed during maintenance
```

## Troubleshooting

### Alerts Not Reaching PagerDuty

1. Check `PAGERDUTY_ENABLED=True`
2. Verify `PAGERDUTY_INTEGRATION_KEY` is correct
3. Check PagerDuty service status
4. Review application logs for errors
5. Test with PagerDuty Events API directly

### Duplicate Alerts

1. Check deduplication window setting
2. Verify dedup keys are consistent
3. Review alert sending logic
4. Check for multiple alert sources

### Alerts During Maintenance

1. Verify `MAINTENANCE_MODE=True`
2. Check maintenance window times
3. Ensure times are in UTC
4. Review maintenance window logic

### Escalation Not Working

1. Check PagerDuty escalation policy
2. Verify escalation timeout setting
3. Ensure alerts are not being acknowledged
4. Review PagerDuty notification rules

## Best Practices

1. **Use appropriate severity levels**: Don't over-alert with critical severity
2. **Provide context**: Include relevant metadata in alerts
3. **Use dedup keys**: Prevent alert storms with consistent dedup keys
4. **Test escalation**: Regularly test escalation policies
5. **Monitor MTTR**: Track and improve mean time to resolution
6. **Review alerts**: Regularly review and tune alert rules
7. **Document runbooks**: Link alerts to runbooks for faster resolution
8. **Use maintenance windows**: Suppress alerts during planned maintenance
9. **Acknowledge promptly**: Acknowledge alerts to stop escalation
10. **Require resolution notes**: Always document how issues were resolved

## References

- [Requirements 16.1-16.13](../../.kiro/specs/production-readiness/requirements.md#requirement-16-alerting-system)
- [PagerDuty Events API Documentation](https://developer.pagerduty.com/docs/ZG9jOjExMDI5NTgw-events-api-v2-overview)
- [PagerDuty REST API Documentation](https://developer.pagerduty.com/api-reference/)
