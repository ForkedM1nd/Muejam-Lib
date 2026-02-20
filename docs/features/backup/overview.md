# Backup and Disaster Recovery

This module provides automated backup and disaster recovery functionality for the MueJam Library platform.

## Requirements

Implements Requirements 19.1-19.13 and 20.1-20.13:

### Backup Requirements (19.x)
- 19.1: Automated PostgreSQL backups every 6 hours
- 19.2: Retain 30 daily + 90 weekly backups
- 19.3: Store backups in separate AWS region
- 19.4: AES-256 encryption at rest
- 19.5: Automated backup integrity verification
- 19.6: Alert on verification failure
- 19.7: Daily Redis backups
- 19.11: Track backup metrics
- 19.12: Point-in-time recovery within 6-hour windows
- 19.13: Complete restoration within 4 hours for databases up to 100GB

### Disaster Recovery Requirements (20.x)
- 20.2: RTO (Recovery Time Objective): 4 hours
- 20.3: RPO (Recovery Point Objective): 6 hours
- 20.9: Maintain secondary database replica in different AZ
- 20.10: Automated failover to replica database

## Components

### BackupService

Manages automated backups and retention.

**Methods:**
- `create_database_backup(db_instance_id)`: Create RDS snapshot with cross-region replication
- `verify_backup(snapshot_id)`: Verify backup integrity and encryption
- `cleanup_old_backups(db_instance_id)`: Delete old backups per retention policy
- `backup_redis_data()`: Create Redis/Valkey backup
- `get_backup_metrics(days)`: Get backup success rates and metrics

**Features:**
- Automated RDS snapshot creation
- Cross-region snapshot copying for disaster recovery
- AES-256 encryption at rest
- Backup verification with alerting
- Retention policy enforcement (30 daily, 90 weekly)
- Metrics tracking

### DisasterRecoveryService

Manages disaster recovery and failover operations.

**Methods:**
- `restore_from_backup(snapshot_id, target_instance_id)`: Restore database from snapshot
- `restore_point_in_time(source_instance_id, target_instance_id, restore_time)`: Point-in-time recovery
- `failover_to_replica(primary_instance_id)`: Automated failover to read replica
- `check_replica_health(primary_instance_id)`: Monitor replica health
- `create_read_replica(source_instance_id, replica_id)`: Create read replica in different AZ
- `test_disaster_recovery()`: Test DR procedures

**Features:**
- Automated failover to read replicas
- Point-in-time recovery within 6-hour windows
- Replica health monitoring
- DR testing automation
- RTO/RPO compliance tracking

## Celery Tasks

### Automated Backup Tasks

#### `perform_database_backup`
Runs every 6 hours. Creates encrypted RDS snapshot and copies to backup region.

```python
from apps.backup.tasks import perform_database_backup

# Manual trigger
result = perform_database_backup.delay('muejam-db-prod')
```

#### `verify_backup`
Automatically triggered 5 minutes after backup creation. Verifies snapshot integrity.

```python
from apps.backup.tasks import verify_backup

result = verify_backup.delay('snapshot-id')
```

#### `cleanup_old_backups`
Runs daily at 3 AM. Deletes backups older than retention policy.

```python
from apps.backup.tasks import cleanup_old_backups

result = cleanup_old_backups.delay('muejam-db-prod')
```

#### `backup_redis_data`
Runs daily at 2 AM. Creates Redis/Valkey backup.

```python
from apps.backup.tasks import backup_redis_data

result = backup_redis_data.delay()
```

#### `weekly_backup_verification`
Runs weekly on Sundays at 4 AM. Performs full backup verification by restoring to test environment.

```python
from apps.backup.tasks import weekly_backup_verification

result = weekly_backup_verification.delay()
```

### Celery Beat Schedule

Add to `settings.py`:

```python
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # Database backup every 6 hours
    'database-backup': {
        'task': 'apps.backup.tasks.perform_database_backup',
        'schedule': 21600.0,  # 6 hours
    },
    
    # Redis backup daily at 2 AM
    'redis-backup': {
        'task': 'apps.backup.tasks.backup_redis_data',
        'schedule': crontab(hour=2, minute=0),
    },
    
    # Cleanup old backups daily at 3 AM
    'backup-cleanup': {
        'task': 'apps.backup.tasks.cleanup_old_backups',
        'schedule': crontab(hour=3, minute=0),
    },
    
    # Weekly backup verification on Sundays at 4 AM
    'weekly-backup-verification': {
        'task': 'apps.backup.tasks.weekly_backup_verification',
        'schedule': crontab(hour=4, minute=0, day_of_week=0),
    },
}
```

## Disaster Recovery Procedures

See [disaster recovery runbook](../../deployment/disaster-recovery.md) for detailed procedures.

### Quick Reference

#### Database Failover

```python
from apps.backup.disaster_recovery_service import DisasterRecoveryService

dr_service = DisasterRecoveryService()

# Failover to read replica
result = dr_service.failover_to_replica('muejam-db-prod')
print(f"New endpoint: {result['endpoint']}")
```

#### Restore from Backup

```python
from apps.backup.disaster_recovery_service import DisasterRecoveryService

dr_service = DisasterRecoveryService()

# Restore from snapshot
result = dr_service.restore_from_backup(
    snapshot_id='snapshot-20240115-120000',
    target_instance_id='muejam-db-restored'
)
```

#### Point-in-Time Recovery

```python
from apps.backup.disaster_recovery_service import DisasterRecoveryService
from datetime import datetime, timedelta

dr_service = DisasterRecoveryService()

# Restore to 2 hours ago
restore_time = datetime.now() - timedelta(hours=2)

result = dr_service.restore_point_in_time(
    source_instance_id='muejam-db-prod',
    target_instance_id='muejam-db-pitr',
    restore_time=restore_time
)
```

## Configuration

### Required Settings

```python
# settings.py

# AWS Configuration
AWS_REGION = 'us-east-1'
AWS_BACKUP_REGION = 'us-west-2'  # Separate region for DR

# RDS Configuration
RDS_INSTANCE_ID = 'muejam-db-prod'

# Backup Configuration
BACKUP_RETENTION_DAILY = 30  # days
BACKUP_RETENTION_WEEKLY = 90  # days

# Recovery Objectives
RTO_HOURS = 4  # Recovery Time Objective
RPO_HOURS = 6  # Recovery Point Objective
```

### AWS IAM Permissions

Required IAM permissions for backup operations:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "rds:CreateDBSnapshot",
        "rds:CopyDBSnapshot",
        "rds:DeleteDBSnapshot",
        "rds:DescribeDBSnapshots",
        "rds:DescribeDBInstances",
        "rds:RestoreDBInstanceFromDBSnapshot",
        "rds:RestoreDBInstanceToPointInTime",
        "rds:PromoteReadReplica",
        "rds:CreateDBInstanceReadReplica",
        "rds:ModifyDBInstance"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "kms:CreateGrant",
        "kms:Decrypt",
        "kms:DescribeKey",
        "kms:Encrypt",
        "kms:GenerateDataKey"
      ],
      "Resource": "*"
    }
  ]
}
```

## Monitoring

### Backup Metrics

```python
from apps.backup.backup_service import BackupService

backup_service = BackupService()
metrics = backup_service.get_backup_metrics(days=30)

print(f"Success Rate: {metrics['success_rate']}%")
print(f"Total Backups: {metrics['total_backups']}")
print(f"Failed Backups: {metrics['failed_backups']}")
```

### Replica Health

```python
from apps.backup.disaster_recovery_service import DisasterRecoveryService

dr_service = DisasterRecoveryService()
health = dr_service.check_replica_health('muejam-db-prod')

print(f"Healthy: {health['healthy']}")
print(f"Replica Count: {health['replica_count']}")
```

## Testing

### Test Disaster Recovery

```python
from apps.backup.disaster_recovery_service import DisasterRecoveryService

dr_service = DisasterRecoveryService()
results = dr_service.test_disaster_recovery()

print(f"Overall Status: {results['overall_status']}")
for test in results['tests']:
    print(f"  {test['name']}: {test['status']}")
```

### Manual Backup Test

```python
from apps.backup.backup_service import BackupService

backup_service = BackupService()

# Create backup
backup = backup_service.create_database_backup('muejam-db-prod')
print(f"Backup created: {backup['snapshot_id']}")

# Verify backup
verification = backup_service.verify_backup(backup['snapshot_id'])
print(f"Backup valid: {verification['is_valid']}")
```

## Alerting

The system sends critical alerts for:

- Backup creation failures
- Backup verification failures
- Failover events
- Restoration operations
- Replica health issues

Alerts are sent via PagerDuty to on-call engineers.

## Integration

To integrate this module:

1. Add 'apps.backup' to INSTALLED_APPS
2. Configure AWS credentials and regions
3. Set up Celery Beat schedule
4. Configure PagerDuty integration
5. Create read replicas in different AZs
6. Test disaster recovery procedures

## Quarterly Testing

Disaster recovery procedures must be tested quarterly:

1. Verify all backups exist and are valid
2. Test restore to test environment
3. Test failover to read replica
4. Measure RTO/RPO compliance
5. Document results and update procedures

See [disaster recovery runbook](../../deployment/disaster-recovery.md) for detailed testing procedures.

## Compliance

This module ensures compliance with:

- **RTO**: 4 hours for complete system restoration
- **RPO**: 6 hours for maximum acceptable data loss
- **Backup Retention**: 30 days daily, 90 days weekly
- **Encryption**: AES-256 at rest
- **Geographic Redundancy**: Cross-region backup storage
- **High Availability**: Multi-AZ read replicas

## Support

For issues or questions:

- Check logs: `aws logs tail /aws/backup/muejam --follow`
- Review metrics in CloudWatch
- Check PagerDuty for alerts
- Consult disaster recovery runbook
- Contact on-call engineer via PagerDuty
