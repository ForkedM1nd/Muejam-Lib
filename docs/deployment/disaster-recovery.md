# Disaster Recovery Runbook

## Overview

This runbook provides step-by-step procedures for recovering from various disaster scenarios affecting the MueJam Library platform.

**Recovery Objectives:**
- **RTO (Recovery Time Objective)**: 4 hours
- **RPO (Recovery Point Objective)**: 6 hours

## Table of Contents

1. [Emergency Contacts](#emergency-contacts)
2. [Database Failure](#database-failure)
3. [Application Server Failure](#application-server-failure)
4. [Complete AWS Region Failure](#complete-aws-region-failure)
5. [Data Corruption](#data-corruption)
6. [Security Breach](#security-breach)
7. [Rollback Procedures](#rollback-procedures)
8. [Testing Procedures](#testing-procedures)

---

## Emergency Contacts

### On-Call Engineers

**Primary On-Call:**
- Name: [Engineer Name]
- Phone: [Phone Number]
- Email: [Email]
- PagerDuty: [PagerDuty Handle]

**Backup On-Call:**
- Name: [Engineer Name]
- Phone: [Phone Number]
- Email: [Email]
- PagerDuty: [PagerDuty Handle]

**Escalation Path:**
1. Primary On-Call Engineer (15 min response)
2. Backup On-Call Engineer (30 min response)
3. Engineering Manager (1 hour response)
4. CTO (2 hour response)

### External Dependencies

**AWS Support:**
- Account ID: [AWS Account ID]
- Support Plan: Enterprise
- Phone: 1-800-AWS-SUPPORT
- Case Portal: https://console.aws.amazon.com/support

**Clerk (Authentication):**
- Support Email: support@clerk.dev
- Status Page: https://status.clerk.dev
- Emergency Contact: [Emergency Contact]

**Resend (Email):**
- Support Email: support@resend.com
- Status Page: https://status.resend.com
- API Status: https://resend.com/status

---

## Database Failure

### Scenario: Primary Database Unavailable

**Symptoms:**
- Application cannot connect to database
- Database connection timeouts
- 500 errors on all API endpoints

**Recovery Procedure:**

#### Step 1: Verify Failure (5 minutes)

```bash
# Check database connectivity
psql -h [DB_ENDPOINT] -U [DB_USER] -d [DB_NAME]

# Check RDS instance status
aws rds describe-db-instances --db-instance-identifier [INSTANCE_ID]

# Check CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name DatabaseConnections \
  --dimensions Name=DBInstanceIdentifier,Value=[INSTANCE_ID] \
  --start-time [START_TIME] \
  --end-time [END_TIME] \
  --period 300 \
  --statistics Average
```

#### Step 2: Initiate Failover (15 minutes)

**Option A: Automated Failover to Read Replica**

```python
from apps.backup.disaster_recovery_service import DisasterRecoveryService

dr_service = DisasterRecoveryService()
result = dr_service.failover_to_replica('[PRIMARY_INSTANCE_ID]')

print(f"New primary endpoint: {result['endpoint']}")
```

**Option B: Manual Failover via AWS Console**

1. Navigate to RDS Console
2. Select read replica instance
3. Click "Actions" → "Promote"
4. Confirm promotion
5. Wait for status to change to "available" (10-15 minutes)
6. Update application configuration with new endpoint

#### Step 3: Update Application Configuration (10 minutes)

```bash
# Update environment variables
export DATABASE_URL="postgresql://[USER]:[PASSWORD]@[NEW_ENDPOINT]:5432/[DB_NAME]"

# Restart application servers
kubectl rollout restart deployment/muejam-backend

# Verify connectivity
python manage.py dbshell
```

#### Step 4: Verify Recovery (10 minutes)

```bash
# Test database queries
python manage.py shell
>>> from django.db import connection
>>> connection.cursor().execute("SELECT 1")

# Check application health
curl https://api.muejam.com/health

# Monitor error rates
# Check Sentry dashboard for errors
```

#### Step 5: Create New Read Replica (30 minutes)

```python
from apps.backup.disaster_recovery_service import DisasterRecoveryService

dr_service = DisasterRecoveryService()
result = dr_service.create_read_replica(
    source_instance_id='[NEW_PRIMARY_ID]',
    replica_id='[REPLICA_ID]',
    availability_zone='us-east-1b'  # Different AZ
)
```

**Total Recovery Time: ~70 minutes (within 4-hour RTO)**

---

## Application Server Failure

### Scenario: All Application Servers Down

**Symptoms:**
- Website returns 502/503 errors
- Load balancer health checks failing
- No application logs being generated

**Recovery Procedure:**

#### Step 1: Verify Failure (5 minutes)

```bash
# Check EC2 instances
aws ec2 describe-instances --filters "Name=tag:Application,Values=muejam-backend"

# Check Auto Scaling Group
aws autoscaling describe-auto-scaling-groups --auto-scaling-group-names [ASG_NAME]

# Check load balancer targets
aws elbv2 describe-target-health --target-group-arn [TARGET_GROUP_ARN]
```

#### Step 2: Scale Up Auto Scaling Group (10 minutes)

```bash
# Increase desired capacity
aws autoscaling set-desired-capacity \
  --auto-scaling-group-name [ASG_NAME] \
  --desired-capacity 4

# Force new instances
aws autoscaling start-instance-refresh \
  --auto-scaling-group-name [ASG_NAME]
```

#### Step 3: Deploy from Infrastructure as Code (20 minutes)

```bash
# Navigate to Terraform directory
cd infrastructure/terraform

# Initialize Terraform
terraform init

# Apply configuration
terraform apply -target=aws_autoscaling_group.app_servers

# Verify deployment
terraform show
```

#### Step 4: Verify Recovery (10 minutes)

```bash
# Check instance health
aws ec2 describe-instance-status --instance-ids [INSTANCE_IDS]

# Test application
curl https://api.muejam.com/health

# Monitor logs
aws logs tail /aws/ec2/muejam-backend --follow
```

**Total Recovery Time: ~45 minutes (within 4-hour RTO)**

---

## Complete AWS Region Failure

### Scenario: Entire AWS Region Unavailable

**Symptoms:**
- All AWS services in primary region unavailable
- Cannot access AWS Console for primary region
- DNS resolution failing for primary region endpoints

**Recovery Procedure:**

#### Step 1: Verify Region Failure (10 minutes)

```bash
# Check AWS Service Health Dashboard
# https://status.aws.amazon.com/

# Test connectivity to backup region
aws rds describe-db-instances --region us-west-2

# Verify backup snapshots exist
aws rds describe-db-snapshots --region us-west-2
```

#### Step 2: Restore Database in Backup Region (60 minutes)

```python
from apps.backup.disaster_recovery_service import DisasterRecoveryService

dr_service = DisasterRecoveryService()

# Get latest snapshot from backup region
# Find most recent snapshot with tag BackupRegion=us-west-2

result = dr_service.restore_from_backup(
    snapshot_id='[LATEST_SNAPSHOT_ID]',
    target_instance_id='muejam-db-prod-dr',
    instance_class='db.t3.large'
)

print(f"Restoration started. Endpoint will be: {result['endpoint']}")
```

#### Step 3: Deploy Application Infrastructure (90 minutes)

```bash
# Switch to backup region
export AWS_REGION=us-west-2

# Deploy infrastructure
cd infrastructure/terraform
terraform workspace select dr
terraform apply

# Deploy application
kubectl config use-context muejam-dr
kubectl apply -f k8s/

# Update DNS to point to new region
aws route53 change-resource-record-sets \
  --hosted-zone-id [ZONE_ID] \
  --change-batch file://dns-failover.json
```

#### Step 4: Verify Recovery (20 minutes)

```bash
# Test all endpoints
curl https://api.muejam.com/health
curl https://api.muejam.com/status

# Check database connectivity
python manage.py dbshell

# Monitor error rates
# Check Sentry for errors
```

**Total Recovery Time: ~180 minutes (3 hours, within 4-hour RTO)**

---

## Data Corruption

### Scenario: Database Data Corrupted

**Symptoms:**
- Inconsistent data in database
- Foreign key constraint violations
- Application errors related to data integrity

**Recovery Procedure:**

#### Step 1: Identify Corruption Scope (15 minutes)

```sql
-- Check for orphaned records
SELECT COUNT(*) FROM stories WHERE author_id NOT IN (SELECT id FROM users);

-- Check for constraint violations
SELECT * FROM pg_constraint WHERE contype = 'f';

-- Identify affected tables
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

#### Step 2: Stop Write Operations (5 minutes)

```bash
# Put application in read-only mode
kubectl set env deployment/muejam-backend READ_ONLY_MODE=true

# Verify no writes occurring
# Monitor database write metrics in CloudWatch
```

#### Step 3: Restore from Point-in-Time (45 minutes)

```python
from apps.backup.disaster_recovery_service import DisasterRecoveryService
from datetime import datetime, timedelta

dr_service = DisasterRecoveryService()

# Restore to point before corruption
restore_time = datetime.now() - timedelta(hours=2)

result = dr_service.restore_point_in_time(
    source_instance_id='muejam-db-prod',
    target_instance_id='muejam-db-restored',
    restore_time=restore_time
)
```

#### Step 4: Verify Data Integrity (20 minutes)

```sql
-- Run integrity checks on restored database
SELECT * FROM pg_constraint WHERE contype = 'f' AND convalidated = false;

-- Verify critical data
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM stories;
SELECT COUNT(*) FROM chapters;

-- Check for corruption
VACUUM ANALYZE;
```

#### Step 5: Switch to Restored Database (15 minutes)

```bash
# Update application configuration
export DATABASE_URL="postgresql://[USER]:[PASSWORD]@[RESTORED_ENDPOINT]:5432/[DB_NAME]"

# Restart application
kubectl rollout restart deployment/muejam-backend

# Remove read-only mode
kubectl set env deployment/muejam-backend READ_ONLY_MODE-
```

**Total Recovery Time: ~100 minutes (within 4-hour RTO)**

---

## Security Breach

### Scenario: Unauthorized Access Detected

**Symptoms:**
- Suspicious database queries in logs
- Unauthorized API access
- Data exfiltration detected
- Compromised credentials

**Response Procedure:**

#### Step 1: Immediate Containment (10 minutes)

```bash
# Revoke all API keys
python manage.py shell
>>> from apps.core.models import APIKey
>>> APIKey.objects.update(is_active=False)

# Rotate database credentials
aws rds modify-db-instance \
  --db-instance-identifier [INSTANCE_ID] \
  --master-user-password [NEW_PASSWORD] \
  --apply-immediately

# Block suspicious IP addresses
aws wafv2 update-ip-set \
  --scope REGIONAL \
  --id [IP_SET_ID] \
  --addresses [SUSPICIOUS_IPS]
```

#### Step 2: Assess Impact (30 minutes)

```sql
-- Check audit logs for unauthorized access
SELECT * FROM audit_logs
WHERE created_at > NOW() - INTERVAL '24 hours'
AND action_type IN ('data_export', 'admin_action', 'user_deletion')
ORDER BY created_at DESC;

-- Identify affected users
SELECT DISTINCT user_id FROM audit_logs
WHERE ip_address IN ([SUSPICIOUS_IPS]);
```

#### Step 3: Notify Affected Users (60 minutes)

```python
# Send security breach notifications
from apps.notifications.email_service import EmailNotificationService

email_service = EmailNotificationService()

for user_id in affected_users:
    email_service.send_security_breach_notification(
        user_id=user_id,
        breach_type='unauthorized_access',
        recommended_actions=['change_password', 'enable_2fa']
    )
```

#### Step 4: Restore from Clean Backup (if needed) (120 minutes)

```python
# If data was modified, restore from backup before breach
from apps.backup.disaster_recovery_service import DisasterRecoveryService

dr_service = DisasterRecoveryService()

# Restore to point before breach
result = dr_service.restore_point_in_time(
    source_instance_id='muejam-db-prod',
    target_instance_id='muejam-db-clean',
    restore_time=time_before_breach
)
```

#### Step 5: Implement Additional Security (ongoing)

- Force password reset for all affected users
- Enable mandatory 2FA for all accounts
- Review and update security policies
- Conduct security audit
- Update incident response procedures

**Total Response Time: ~220 minutes (within 4-hour RTO for containment)**

---

## Rollback Procedures

### Failed Deployment Rollback

**Scenario:** New deployment causing errors

#### Quick Rollback (5 minutes)

```bash
# Kubernetes rollback
kubectl rollout undo deployment/muejam-backend

# Verify rollback
kubectl rollout status deployment/muejam-backend

# Check application health
curl https://api.muejam.com/health
```

#### Database Migration Rollback (15 minutes)

```bash
# Rollback last migration
python manage.py migrate [app_name] [previous_migration]

# Verify database state
python manage.py showmigrations

# Test application
python manage.py test
```

---

## Testing Procedures

### Quarterly Disaster Recovery Test

**Schedule:** First Sunday of each quarter at 2 AM

#### Test Checklist

1. **Backup Verification** (30 minutes)
   - Verify all backups exist
   - Check backup encryption
   - Validate backup integrity

2. **Restore Test** (60 minutes)
   - Restore latest backup to test environment
   - Verify data integrity
   - Test application connectivity

3. **Failover Test** (45 minutes)
   - Test failover to read replica
   - Measure failover time
   - Verify application functionality

4. **Documentation Review** (30 minutes)
   - Review and update runbook
   - Verify contact information
   - Update procedures based on changes

5. **Report Generation** (15 minutes)
   - Document test results
   - Identify improvements
   - Update RTO/RPO metrics

**Total Test Time:** ~180 minutes

### Test Execution

```python
from apps.backup.disaster_recovery_service import DisasterRecoveryService

dr_service = DisasterRecoveryService()
test_results = dr_service.test_disaster_recovery()

print(f"Test Status: {test_results['overall_status']}")
for test in test_results['tests']:
    print(f"  {test['name']}: {test['status']}")
```

---

## Post-Incident Procedures

After any disaster recovery event:

1. **Document the Incident**
   - Timeline of events
   - Actions taken
   - Recovery time achieved
   - Lessons learned

2. **Conduct Post-Mortem**
   - Schedule within 48 hours
   - Include all involved parties
   - Identify root cause
   - Create action items

3. **Update Procedures**
   - Update runbook based on learnings
   - Improve automation
   - Update contact information

4. **Communicate**
   - Notify stakeholders
   - Update status page
   - Send user communications if needed

---

## Appendix

### Infrastructure as Code Locations

- Terraform: `infrastructure/terraform/`
- Kubernetes: `infrastructure/k8s/`
- Ansible: `infrastructure/ansible/`

### Configuration Backups

- Environment variables: `infrastructure/config/env/`
- Secrets: AWS Secrets Manager
- Application config: `config/settings/`

### Monitoring Dashboards

- Sentry: https://sentry.io/muejam
- CloudWatch: https://console.aws.amazon.com/cloudwatch
- PagerDuty: https://muejam.pagerduty.com

### Last Updated

- Date: [Current Date]
- Updated By: [Name]
- Next Review: [Date + 3 months]
