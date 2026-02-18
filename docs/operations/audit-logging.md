# Audit Logging Guide

## Overview

Comprehensive audit logging for compliance, security, and debugging. All sensitive operations are logged with immutable audit trails.

## What is Logged

### Authentication Events (Requirement 32.1)
- Login success/failure
- Logout
- Password changes
- 2FA enabled/disabled
- Session creation/termination

### Moderation Actions (Requirement 32.2)
- Content takedowns
- User suspensions
- Report resolutions
- Role assignments
- Content flags

### Administrative Actions (Requirement 32.3)
- Configuration changes
- User role changes
- System settings updates
- Feature flag changes
- Database migrations

### Data Access (Requirement 32.4)
- Data export requests
- Account deletion requests
- Privacy settings changes
- Consent recorded/withdrawn
- PII access

### API Operations
- API key creation/revocation
- Rate limit violations
- Authentication failures
- Authorization failures

## Audit Log Format

Each audit log entry contains (Requirement 32.5):

```json
{
  "id": "uuid",
  "user_id": "user-123",
  "action_type": "LOGIN_SUCCESS",
  "resource_type": "USER",
  "resource_id": "user-123",
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0...",
  "result": "SUCCESS",
  "metadata": {
    "additional": "context"
  },
  "created_at": "2024-01-01T12:00:00Z"
}
```

### Required Fields

| Field | Description | Example |
|-------|-------------|---------|
| id | Unique identifier | uuid |
| user_id | User performing action | user-123 |
| action_type | Type of action | LOGIN_SUCCESS |
| resource_type | Type of resource | USER, STORY, etc. |
| resource_id | ID of resource | resource-123 |
| ip_address | Client IP address | 192.168.1.1 |
| user_agent | Client user agent | Mozilla/5.0... |
| result | Action result | SUCCESS, FAILURE |
| metadata | Additional context | JSON object |
| created_at | Timestamp | ISO 8601 |

## Usage

### In Views

```python
from apps.admin.audit_log_service import AuditLogService, get_client_ip, get_user_agent

async def login_view(request):
    # ... authentication logic ...
    
    if authentication_successful:
        await AuditLogService.log_login_success(
            user_id=user.id,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            metadata={'method': 'password'}
        )
    else:
        await AuditLogService.log_login_failed(
            user_id=email,  # Use email if user not found
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            reason='Invalid credentials'
        )
```

### Authentication Events

```python
# Login success
await AuditLogService.log_login_success(
    user_id=user.id,
    ip_address=ip,
    user_agent=ua
)

# Login failure
await AuditLogService.log_login_failed(
    user_id=email,
    ip_address=ip,
    user_agent=ua,
    reason='Invalid password'
)

# Password change
await AuditLogService.log_password_change(
    user_id=user.id,
    ip_address=ip,
    user_agent=ua
)

# 2FA enabled
await AuditLogService.log_2fa_enabled(
    user_id=user.id,
    ip_address=ip,
    user_agent=ua
)
```

### Moderation Actions

```python
# Content takedown
await AuditLogService.log_content_takedown(
    moderator_id=moderator.id,
    resource_type=AuditResourceType.STORY,
    resource_id=story.id,
    ip_address=ip,
    user_agent=ua,
    reason='Violates community guidelines',
    metadata={'violation_type': 'spam'}
)

# User suspension
await AuditLogService.log_user_suspension(
    moderator_id=moderator.id,
    suspended_user_id=user.id,
    ip_address=ip,
    user_agent=ua,
    reason='Repeated violations',
    duration='7 days'
)
```

### Administrative Actions

```python
# Configuration change
await AuditLogService.log_config_change(
    admin_id=admin.id,
    ip_address=ip,
    user_agent=ua,
    config_key='MAX_UPLOAD_SIZE',
    old_value='10MB',
    new_value='20MB'
)

# Role assignment
await AuditLogService.log_role_assignment(
    admin_id=admin.id,
    target_user_id=user.id,
    ip_address=ip,
    user_agent=ua,
    role='moderator'
)
```

### Data Access

```python
# Data export request
await AuditLogService.log_data_export_request(
    user_id=user.id,
    ip_address=ip,
    user_agent=ua,
    export_id=export.id
)

# Privacy settings change
await AuditLogService.log_privacy_settings_change(
    user_id=user.id,
    ip_address=ip,
    user_agent=ua,
    changes={'profile_visibility': 'private'}
)
```

## Log Retention

### Retention Policy

| Log Type | Retention Period | Storage |
|----------|------------------|---------|
| Authentication | 90 days | Hot storage |
| Moderation | 2 years | Warm storage |
| Administrative | 7 years | Cold storage |
| Data Access | 7 years | Cold storage |
| API Operations | 90 days | Hot storage |

### Configuration

```python
# In settings.py or environment
AUDIT_LOG_RETENTION = {
    'authentication': 90,  # days
    'moderation': 730,  # 2 years
    'administrative': 2555,  # 7 years
    'data_access': 2555,  # 7 years
    'api_operations': 90
}
```

### Automated Cleanup

```bash
# Run cleanup script
python manage.py cleanup_audit_logs --older-than 90 --type authentication

# Or use cron
0 2 * * * python manage.py cleanup_audit_logs --older-than 90 --type authentication
```

## Querying Audit Logs

### By User

```python
from prisma import Prisma

db = Prisma()
await db.connect()

logs = await db.auditlog.find_many(
    where={'user_id': 'user-123'},
    order={'created_at': 'desc'},
    take=100
)
```

### By Action Type

```python
logs = await db.auditlog.find_many(
    where={'action_type': 'LOGIN_FAILED'},
    order={'created_at': 'desc'},
    take=100
)
```

### By Date Range

```python
from datetime import datetime, timedelta

start_date = datetime.now() - timedelta(days=7)

logs = await db.auditlog.find_many(
    where={
        'created_at': {'gte': start_date}
    },
    order={'created_at': 'desc'}
)
```

### By Resource

```python
logs = await db.auditlog.find_many(
    where={
        'resource_type': 'STORY',
        'resource_id': 'story-123'
    },
    order={'created_at': 'desc'}
)
```

### Complex Queries

```python
# Failed login attempts from specific IP
logs = await db.auditlog.find_many(
    where={
        'action_type': 'LOGIN_FAILED',
        'ip_address': '192.168.1.1',
        'created_at': {'gte': datetime.now() - timedelta(hours=1)}
    },
    order={'created_at': 'desc'}
)

# All moderation actions by specific moderator
logs = await db.auditlog.find_many(
    where={
        'user_id': 'moderator-123',
        'action_type': {'in': ['CONTENT_TAKEDOWN', 'USER_SUSPENSION', 'REPORT_RESOLUTION']}
    },
    order={'created_at': 'desc'}
)
```

## Monitoring and Alerts

### Key Metrics

Monitor these patterns:
- Failed login attempts (> 5 in 5 minutes)
- Unusual moderation activity
- Administrative changes outside business hours
- Data export requests
- API key creation/revocation

### Alert Rules

```python
# Example: Alert on multiple failed logins
failed_logins = await db.auditlog.count(
    where={
        'action_type': 'LOGIN_FAILED',
        'ip_address': ip_address,
        'created_at': {'gte': datetime.now() - timedelta(minutes=5)}
    }
)

if failed_logins >= 5:
    send_alert('Multiple failed login attempts', {
        'ip_address': ip_address,
        'count': failed_logins
    })
```

### Suspicious Patterns

- Multiple failed logins from same IP
- Login from unusual location
- Rapid role changes
- Mass content takedowns
- Unusual data export requests
- API key creation outside business hours

## Compliance

### GDPR Compliance

Audit logs support GDPR requirements:
- Right to access: Query logs by user_id
- Right to erasure: Pseudonymize user_id after account deletion
- Data breach notification: Track all data access

### SOC 2 Compliance

Audit logs support SOC 2 requirements:
- Access controls: Log all authentication events
- Change management: Log all configuration changes
- Monitoring: Track all administrative actions

### HIPAA Compliance (if applicable)

- Log all PHI access
- Track data exports
- Monitor unusual access patterns
- Retain logs for 6 years

## Security

### Immutability

Audit logs are immutable (Requirement 32.6):
- No update operations allowed
- No delete operations (only archival)
- Stored in append-only table
- Backed up to immutable storage

### Access Control

- Read access: Administrators and compliance team only
- Write access: System only (via AuditLogService)
- No direct database access
- All access logged

### Encryption

- At rest: Database encryption enabled
- In transit: TLS 1.3
- Backups: Encrypted with separate key

## Troubleshooting

### Audit Log Not Created

```python
# Check if service is working
try:
    result = await AuditLogService.log_event(
        action_type=AuditActionType.LOGIN_SUCCESS,
        user_id='test-user',
        ip_address='127.0.0.1',
        user_agent='Test'
    )
    print(f"Audit log created: {result}")
except Exception as e:
    print(f"Error: {e}")
```

### Query Performance Issues

```sql
-- Add indexes for common queries
CREATE INDEX idx_auditlog_user_id ON auditlog(user_id);
CREATE INDEX idx_auditlog_action_type ON auditlog(action_type);
CREATE INDEX idx_auditlog_created_at ON auditlog(created_at);
CREATE INDEX idx_auditlog_ip_address ON auditlog(ip_address);
```

### Storage Growth

```bash
# Check audit log size
SELECT 
    pg_size_pretty(pg_total_relation_size('auditlog')) as total_size,
    COUNT(*) as row_count
FROM auditlog;

# Archive old logs
python manage.py archive_audit_logs --older-than 365 --destination s3://audit-archive/
```

## Best Practices

1. **Log all sensitive operations** - Authentication, authorization, data access
2. **Include context** - IP address, user agent, metadata
3. **Don't log sensitive data** - Passwords, tokens, PII in metadata
4. **Use structured logging** - JSON format for easy parsing
5. **Monitor for anomalies** - Set up alerts for suspicious patterns
6. **Regular audits** - Review logs monthly
7. **Test retention** - Verify cleanup scripts work
8. **Backup logs** - Store in immutable storage
9. **Document procedures** - Keep runbooks updated
10. **Train team** - Ensure everyone knows what to log

## Audit Log Checklist

- [ ] All authentication events logged
- [ ] All moderation actions logged
- [ ] All administrative actions logged
- [ ] All data access logged
- [ ] Retention policy configured
- [ ] Cleanup scripts scheduled
- [ ] Monitoring alerts set up
- [ ] Backup strategy implemented
- [ ] Access controls configured
- [ ] Documentation complete
- [ ] Team trained

## Resources

- Audit Log Service: `apps/backend/apps/admin/audit_log_service.py`
- Prisma Schema: `apps/backend/prisma/schema.prisma`
- Tests: `apps/backend/tests/infrastructure/test_audit_log_integration.py`
- GDPR Compliance: `docs/legal/gdpr-compliance.md`
- SOC 2 Compliance: `docs/legal/soc2-compliance.md`
