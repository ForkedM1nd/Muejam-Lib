# Database Backup and Restore Guide

## Overview

This guide covers automated database backups, restore procedures, and disaster recovery for the MueJam platform.

## Backup Strategy

### Backup Types

1. **Full Backup**: Complete database dump
   - Schedule: Daily at 2 AM
   - Retention: 30 days
   - Storage: Cloud storage (S3/Azure/GCS)

2. **Incremental Backup** (Optional):
   - Schedule: Every 6 hours
   - Retention: 7 days
   - Storage: Cloud storage

3. **WAL (Write-Ahead Log) Backup** (Optional):
   - Schedule: Continuous or hourly
   - Retention: 7 days
   - For point-in-time recovery

### Retention Policy

| Backup Type | Retention Period |
|-------------|------------------|
| Daily | 30 days |
| Weekly | 12 weeks (3 months) |
| Monthly | 12 months (1 year) |
| Yearly | 7 years |

## Setup

### Prerequisites

```bash
# Install required tools
sudo apt-get update
sudo apt-get install -y postgresql-client gzip openssl

# For AWS S3
sudo apt-get install -y awscli

# For Azure
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# For Google Cloud
# Follow: https://cloud.google.com/sdk/docs/install
```

### Configuration

1. **Set environment variables**:

```bash
# Database configuration
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=muejam
export DB_USER=muejam_user
export PGPASSWORD=your_password

# Backup configuration
export BACKUP_DIR=/var/backups/postgres
export BACKUP_RETENTION_DAYS=30
export BACKUP_STORAGE_TYPE=s3  # or azure, gcs, local

# Cloud storage (choose one)
export S3_BUCKET=muejam-backups
export AZURE_CONTAINER=muejam-backups
export GCS_BUCKET=muejam-backups

# Encryption
export ENCRYPTION_ENABLED=true
export ENCRYPTION_KEY_FILE=/etc/backup/encryption.key

# Notifications (optional)
export BACKUP_NOTIFICATION_WEBHOOK=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

2. **Generate encryption key**:

```bash
sudo mkdir -p /etc/backup
sudo openssl rand -base64 32 > /etc/backup/encryption.key
sudo chmod 600 /etc/backup/encryption.key
```

3. **Create backup directory**:

```bash
sudo mkdir -p /var/backups/postgres
sudo chown postgres:postgres /var/backups/postgres
sudo chmod 700 /var/backups/postgres
```

### Automated Backups

#### Using Cron

```bash
# Edit crontab
sudo crontab -e

# Add backup schedule
# Daily full backup at 2 AM
0 2 * * * /path/to/infra/backup/postgres-backup.sh >> /var/log/postgres-backup.log 2>&1

# Weekly backup verification at 3 AM on Sundays
0 3 * * 0 /path/to/infra/backup/verify-backup.sh >> /var/log/backup-verify.log 2>&1
```

#### Using Systemd Timer

Create `/etc/systemd/system/postgres-backup.service`:

```ini
[Unit]
Description=PostgreSQL Backup Service
After=network.target postgresql.service

[Service]
Type=oneshot
User=postgres
Group=postgres
EnvironmentFile=/etc/backup/backup.env
ExecStart=/path/to/infra/backup/postgres-backup.sh
StandardOutput=journal
StandardError=journal
```

Create `/etc/systemd/system/postgres-backup.timer`:

```ini
[Unit]
Description=PostgreSQL Backup Timer
Requires=postgres-backup.service

[Timer]
OnCalendar=daily
OnCalendar=02:00
Persistent=true

[Install]
WantedBy=timers.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable postgres-backup.timer
sudo systemctl start postgres-backup.timer
sudo systemctl status postgres-backup.timer
```

## Backup Procedures

### Manual Backup

```bash
# Run backup script
cd infra/backup
./postgres-backup.sh

# Check backup was created
ls -lh /var/backups/postgres/

# Verify backup integrity
gzip -t /var/backups/postgres/muejam_backup_*.sql.gz
```

### Verify Backup

```bash
# List available backups
./postgres-restore.sh --list

# Download and verify specific backup
./postgres-restore.sh --file muejam_backup_20240101_120000.sql.gz --download
```

## Restore Procedures

### Full Restore

**WARNING**: This will replace the entire database!

```bash
# 1. List available backups
./postgres-restore.sh --list

# 2. Restore from backup (with confirmation)
./postgres-restore.sh --file muejam_backup_20240101_120000.sql.gz

# 3. Restore from cloud storage (skip confirmation)
./postgres-restore.sh --file muejam_backup_20240101_120000.sql.gz --download --yes
```

### Point-in-Time Recovery (PITR)

If WAL archiving is enabled:

```bash
# 1. Restore base backup
./postgres-restore.sh --file muejam_backup_20240101_120000.sql.gz --yes

# 2. Configure recovery
cat > /var/lib/postgresql/data/recovery.conf << EOF
restore_command = 'cp /var/backups/postgres/wal/%f %p'
recovery_target_time = '2024-01-01 14:30:00'
EOF

# 3. Restart PostgreSQL
sudo systemctl restart postgresql

# 4. Verify recovery
psql -U muejam_user -d muejam -c "SELECT NOW();"
```

### Partial Restore (Single Table)

```bash
# 1. Extract specific table from backup
gunzip -c muejam_backup_20240101_120000.sql.gz | \
  pg_restore --table=stories --data-only | \
  psql -U muejam_user -d muejam

# 2. Or restore to temporary database first
createdb muejam_temp
gunzip -c muejam_backup_20240101_120000.sql.gz | \
  pg_restore -d muejam_temp

# 3. Copy specific data
pg_dump -U muejam_user -d muejam_temp -t stories | \
  psql -U muejam_user -d muejam
```

## Disaster Recovery

### Scenario 1: Database Corruption

```bash
# 1. Stop application
sudo systemctl stop gunicorn celery

# 2. Restore from latest backup
./postgres-restore.sh --file $(ls -t /var/backups/postgres/muejam_backup_*.sql.gz | head -1) --yes

# 3. Verify data
psql -U muejam_user -d muejam -c "SELECT COUNT(*) FROM stories;"

# 4. Start application
sudo systemctl start gunicorn celery
```

### Scenario 2: Complete Server Loss

```bash
# 1. Provision new server
# 2. Install PostgreSQL and dependencies
# 3. Configure database
# 4. Download backup from cloud storage
aws s3 cp s3://muejam-backups/backups/muejam_backup_latest.sql.gz /tmp/

# 5. Restore
./postgres-restore.sh --file /tmp/muejam_backup_latest.sql.gz --yes

# 6. Deploy application
# 7. Verify functionality
```

### Scenario 3: Accidental Data Deletion

```bash
# If within retention period:
# 1. Find backup before deletion
./postgres-restore.sh --list

# 2. Restore to temporary database
createdb muejam_recovery
./postgres-restore.sh --file muejam_backup_YYYYMMDD_HHMMSS.sql.gz --database muejam_recovery --yes

# 3. Extract deleted data
pg_dump -U muejam_user -d muejam_recovery -t deleted_table | \
  psql -U muejam_user -d muejam

# 4. Verify and clean up
dropdb muejam_recovery
```

## Backup Monitoring

### Check Backup Status

```bash
# View backup logs
tail -f /var/log/postgres-backup.log

# Check last backup
ls -lht /var/backups/postgres/ | head -5

# Verify backup in cloud storage
aws s3 ls s3://muejam-backups/backups/ --recursive | tail -10
```

### Backup Metrics

Monitor these metrics:
- Backup success/failure rate
- Backup duration
- Backup size
- Time since last successful backup
- Storage utilization

### Alerts

Set up alerts for:
- Backup failure
- Backup duration > 1 hour
- No backup in last 25 hours
- Backup size change > 50%
- Storage space < 20%

## Testing

### Test Backup

```bash
# 1. Create test backup
./postgres-backup.sh

# 2. Verify backup file exists
ls -lh /var/backups/postgres/muejam_backup_*.sql.gz

# 3. Check backup integrity
gzip -t /var/backups/postgres/muejam_backup_*.sql.gz

# 4. Verify backup can be read
gunzip -c /var/backups/postgres/muejam_backup_*.sql.gz | head -100
```

### Test Restore

```bash
# 1. Create test database
createdb muejam_test

# 2. Restore to test database
gunzip -c /var/backups/postgres/muejam_backup_*.sql.gz | \
  pg_restore -d muejam_test --no-owner --no-acl

# 3. Verify data
psql -d muejam_test -c "SELECT COUNT(*) FROM stories;"
psql -d muejam_test -c "SELECT COUNT(*) FROM users;"

# 4. Clean up
dropdb muejam_test
```

### Disaster Recovery Drill

Schedule quarterly DR drills:

1. **Preparation**:
   - Notify team
   - Prepare test environment
   - Document start time

2. **Execution**:
   - Simulate failure
   - Execute restore procedure
   - Verify application functionality
   - Document issues

3. **Review**:
   - Calculate RTO (Recovery Time Objective)
   - Calculate RPO (Recovery Point Objective)
   - Update procedures
   - Train team

## Backup Security

### Encryption

All backups are encrypted using AES-256-CBC:

```bash
# Encrypt backup
openssl enc -aes-256-cbc -salt -pbkdf2 \
  -in backup.sql.gz \
  -out backup.sql.gz.enc \
  -pass file:/etc/backup/encryption.key

# Decrypt backup
openssl enc -aes-256-cbc -d -pbkdf2 \
  -in backup.sql.gz.enc \
  -out backup.sql.gz \
  -pass file:/etc/backup/encryption.key
```

### Access Control

- Backup files: `chmod 600` (owner read/write only)
- Encryption key: `chmod 400` (owner read only)
- Backup directory: `chmod 700` (owner access only)
- Cloud storage: Use IAM roles with least privilege

### Key Management

- Store encryption key securely (AWS Secrets Manager, Azure Key Vault, etc.)
- Rotate encryption keys annually
- Keep old keys for decrypting old backups
- Document key rotation procedure

## Troubleshooting

### Backup Fails

```bash
# Check PostgreSQL is running
pg_isready -h localhost -p 5432

# Check disk space
df -h /var/backups/postgres

# Check permissions
ls -la /var/backups/postgres

# Check logs
tail -100 /var/log/postgres-backup.log

# Test database connection
psql -h localhost -U muejam_user -d muejam -c "SELECT 1;"
```

### Restore Fails

```bash
# Check backup integrity
gzip -t backup.sql.gz

# Check PostgreSQL version compatibility
pg_restore --version
psql --version

# Try restore with verbose output
gunzip -c backup.sql.gz | pg_restore -v -d muejam 2>&1 | tee restore.log

# Check for specific errors
grep -i error restore.log
```

### Slow Backup/Restore

```bash
# Use parallel jobs
pg_dump -j 4 ...  # 4 parallel jobs

# Compress less aggressively
gzip -1 ...  # Faster compression

# Use faster storage
# Move BACKUP_DIR to SSD

# Exclude large tables
pg_dump --exclude-table=large_table ...
```

## Best Practices

1. **Test restores regularly** - Monthly restore tests
2. **Monitor backup health** - Set up alerts
3. **Encrypt backups** - Always encrypt sensitive data
4. **Store offsite** - Use cloud storage
5. **Document procedures** - Keep runbooks updated
6. **Automate everything** - Reduce human error
7. **Verify integrity** - Check backups after creation
8. **Rotate encryption keys** - Annual key rotation
9. **Practice DR drills** - Quarterly exercises
10. **Monitor storage costs** - Optimize retention policy

## Backup Checklist

- [ ] Automated backups configured
- [ ] Backup schedule tested
- [ ] Encryption enabled and tested
- [ ] Cloud storage configured
- [ ] Retention policy implemented
- [ ] Restore procedure tested
- [ ] Monitoring and alerts set up
- [ ] Documentation complete
- [ ] Team trained on procedures
- [ ] DR drill scheduled

## Resources

- [PostgreSQL Backup Documentation](https://www.postgresql.org/docs/current/backup.html)
- [pg_dump Documentation](https://www.postgresql.org/docs/current/app-pgdump.html)
- [pg_restore Documentation](https://www.postgresql.org/docs/current/app-pgrestore.html)
- AWS S3 Backup Best Practices
- Azure Backup Best Practices
- Google Cloud Backup Best Practices

## Support

For backup/restore issues:
1. Check this documentation
2. Review backup logs
3. Test backup integrity
4. Contact DevOps team
5. Escalate to DBA if needed
