# Production Deployment Checklist

This document provides a comprehensive checklist for deploying the MueJam Library platform to production.

**Requirements Implemented:**
- 29.1: Deployment checklist with all steps
- 29.2: Code review approval from 2 engineers
- 29.3: All tests must pass
- 29.4: Database migration review
- 29.8: Blue-green deployment strategy
- 29.14: Rollback procedures

## Pre-Deployment Checklist

### Code Quality and Testing

- [ ] **Code Review Completed**
  - [ ] At least 2 engineers have approved the pull request (Requirement 29.2)
  - [ ] All review comments have been addressed
  - [ ] Code follows project style guidelines
  - [ ] No security vulnerabilities identified

- [ ] **All Tests Pass** (Requirement 29.3)
  - [ ] Unit tests: `pytest apps/backend/tests/ -v`
  - [ ] Integration tests: `pytest apps/backend/tests/integration/ -v`
  - [ ] Property-based tests: `pytest apps/backend/tests/ -k property -v`
  - [ ] Test coverage meets minimum threshold (80%)
  - [ ] No flaky tests

- [ ] **Static Analysis**
  - [ ] Linting passes: `flake8 apps/backend/`
  - [ ] Type checking passes: `mypy apps/backend/`
  - [ ] Security scan passes: `bandit -r apps/backend/`
  - [ ] Dependency vulnerabilities checked: `safety check`

### Database Changes

- [ ] **Database Migrations** (Requirement 29.4)
  - [ ] Migrations have been reviewed and approved
  - [ ] Migrations are backward compatible (if possible)
  - [ ] Migration rollback plan documented
  - [ ] Estimated migration time calculated
  - [ ] Large data migrations tested on production-sized dataset
  - [ ] Indexes created with `CONCURRENTLY` option (PostgreSQL)

- [ ] **Database Backup**
  - [ ] Pre-deployment backup scheduled
  - [ ] Backup verification completed
  - [ ] Backup restoration tested in staging
  - [ ] Backup retention policy confirmed

### Configuration and Secrets

- [ ] **Environment Configuration**
  - [ ] All required environment variables documented
  - [ ] Configuration validated: `python manage.py validate_config --environment production`
  - [ ] Secrets stored in AWS Secrets Manager
  - [ ] No secrets in version control
  - [ ] Different credentials for production vs staging

- [ ] **SECRET_KEY Configuration** (CRITICAL)
  - [ ] Unique SECRET_KEY generated for production (minimum 50 characters)
  - [ ] SECRET_KEY stored in AWS Secrets Manager or secure environment variable
  - [ ] SECRET_KEY is NOT the example value from .env.example
  - [ ] SECRET_KEY is NOT committed to version control
  - [ ] SECRET_KEY validation passes: `python manage.py check`
  - [ ] Different SECRET_KEY used for each environment (dev, staging, production)

- [ ] **Feature Flags**
  - [ ] New features behind feature flags (if applicable)
  - [ ] Feature flag configuration reviewed
  - [ ] Rollback plan via feature flags documented

### Infrastructure

- [ ] **Infrastructure as Code**
  - [ ] Terraform/CloudFormation changes reviewed
  - [ ] Infrastructure changes tested in staging
  - [ ] Resource capacity verified (CPU, memory, disk)
  - [ ] Auto-scaling configuration reviewed

- [ ] **Dependencies**
  - [ ] All external service dependencies identified
  - [ ] External service health verified
  - [ ] API rate limits confirmed
  - [ ] Third-party service status checked

### Monitoring and Alerting

- [ ] **Observability**
  - [ ] Sentry error tracking configured
  - [ ] APM (New Relic/DataDog) configured
  - [ ] CloudWatch Logs configured
  - [ ] Custom metrics defined and tracked

- [ ] **Alerting**
  - [ ] PagerDuty integration configured
  - [ ] Alert rules reviewed and tested
  - [ ] On-call schedule confirmed
  - [ ] Escalation paths documented

### Documentation

- [ ] **Deployment Documentation**
  - [ ] Deployment steps documented
  - [ ] Rollback procedures documented
  - [ ] Known issues and workarounds documented
  - [ ] Post-deployment verification steps documented

- [ ] **Changelog**
  - [ ] CHANGELOG.md updated with version and changes
  - [ ] Breaking changes clearly documented
  - [ ] Migration guide provided (if needed)

## Deployment Window Planning

### Timing

- [ ] **Deployment Schedule**
  - [ ] Deployment window scheduled during low-traffic period
  - [ ] Maintenance window announced 48 hours in advance (if downtime expected)
  - [ ] Team availability confirmed (engineers, on-call, stakeholders)
  - [ ] Backup deployment window identified

### Communication

- [ ] **Stakeholder Communication**
  - [ ] Engineering team notified
  - [ ] Product team notified
  - [ ] Customer support team notified
  - [ ] Status page updated (if maintenance required)

## Deployment Procedure

### Step 1: Pre-Deployment Verification

```bash
# 1. Verify you're on the correct branch
git branch --show-current
# Should show: main or release/vX.Y.Z

# 2. Verify all tests pass
pytest apps/backend/tests/ -v

# 3. Validate configuration
python manage.py validate_config --environment production

# 4. Check for pending migrations
python manage.py showmigrations | grep "\[ \]"
```

### Step 2: Database Backup (Requirement 29.6)

```bash
# 1. Create pre-deployment backup
aws rds create-db-snapshot \
  --db-instance-identifier muejam-production \
  --db-snapshot-identifier muejam-pre-deploy-$(date +%Y%m%d-%H%M%S)

# 2. Wait for backup to complete
aws rds wait db-snapshot-completed \
  --db-snapshot-identifier muejam-pre-deploy-$(date +%Y%m%d-%H%M%S)

# 3. Verify backup
aws rds describe-db-snapshots \
  --db-snapshot-identifier muejam-pre-deploy-$(date +%Y%m%d-%H%M%S)
```

### Step 3: Deploy to Staging (Requirement 29.7)

```bash
# 1. Deploy to staging environment
./scripts/deploy.sh staging

# 2. Run smoke tests
./scripts/smoke-tests.sh staging

# 3. Verify functionality
# - Test critical user flows
# - Verify database migrations
# - Check error rates
# - Verify external integrations

# 4. Get approval to proceed to production
```

### Step 4: Blue-Green Deployment (Requirement 29.8)

```bash
# 1. Deploy to green environment (new version)
./scripts/deploy-blue-green.sh production green

# 2. Run database migrations (if any)
# Migrations run on green environment before traffic switch
python manage.py migrate --database=production

# 3. Warm up green environment
# Send test traffic to green environment
./scripts/warmup.sh green

# 4. Verify green environment health
./scripts/health-check.sh green

# 5. Switch traffic to green environment
# Gradual traffic shift: 10% -> 50% -> 100%
./scripts/switch-traffic.sh green --gradual

# 6. Monitor metrics for 30 minutes (Requirement 29.9)
# - Error rate
# - Response time (p95, p99)
# - Database performance
# - External service calls
# - User-reported issues

# 7. If all metrics are healthy, complete the switch
./scripts/switch-traffic.sh green --complete

# 8. Keep blue environment running for quick rollback
# Blue environment remains available for 24 hours
```

### Step 5: Post-Deployment Verification

```bash
# 1. Verify application health
curl https://api.muejam.com/health

# 2. Check error rates in Sentry
# Should be < 1% error rate

# 3. Verify database migrations
python manage.py showmigrations

# 4. Check APM metrics
# - Response times within thresholds
# - No slow queries
# - No N+1 query issues

# 5. Verify external integrations
# - Clerk authentication
# - AWS S3 uploads
# - Resend emails
# - Sentry error tracking

# 6. Test critical user flows
# - User registration and login
# - Story creation and reading
# - Whisper posting
# - Content moderation

# 7. Monitor for 30 minutes (Requirement 29.9)
# Watch dashboards for anomalies
```

### Step 6: Notification (Requirement 29.11)

```bash
# Send deployment notification to Slack
./scripts/notify-deployment.sh success \
  --version v1.2.3 \
  --environment production \
  --deployed-by "John Doe"
```

## Rollback Procedure (Requirement 29.14)

### Automatic Rollback (Requirement 29.10)

The system automatically rolls back if:
- Error rate exceeds 2%
- Response time degrades by 50%
- Health checks fail
- Critical alerts triggered

### Manual Rollback

If issues are detected after deployment:

```bash
# 1. Initiate rollback
./scripts/rollback.sh production

# This will:
# - Switch traffic back to blue environment (previous version)
# - Restore database from backup (if migrations were run)
# - Notify team of rollback

# 2. Verify rollback successful
curl https://api.muejam.com/health

# 3. Check error rates return to normal
# Monitor Sentry and APM dashboards

# 4. Investigate root cause
# - Review logs
# - Check error reports
# - Analyze metrics

# 5. Notify stakeholders
./scripts/notify-deployment.sh rollback \
  --version v1.2.3 \
  --reason "High error rate detected"
```

### Database Rollback

If database migrations need to be rolled back:

```bash
# 1. Stop application traffic
./scripts/maintenance-mode.sh enable

# 2. Restore database from backup
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier muejam-production-rollback \
  --db-snapshot-identifier muejam-pre-deploy-YYYYMMDD-HHMMSS

# 3. Update DNS to point to restored database
# Or update application configuration

# 4. Verify data integrity
python manage.py check --database=production

# 5. Resume application traffic
./scripts/maintenance-mode.sh disable

# 6. Monitor for issues
```

## Post-Deployment Tasks

### Immediate (Within 1 Hour)

- [ ] Monitor error rates and performance metrics
- [ ] Verify all critical functionality working
- [ ] Check for user-reported issues
- [ ] Review deployment logs for warnings
- [ ] Confirm backup completed successfully

### Short-term (Within 24 Hours)

- [ ] Review deployment metrics and identify improvements
- [ ] Update documentation with any lessons learned
- [ ] Close deployment ticket/issue
- [ ] Decommission blue environment (if rollback not needed)
- [ ] Archive deployment logs

### Long-term (Within 1 Week)

- [ ] Conduct deployment retrospective
- [ ] Update deployment procedures based on learnings
- [ ] Review and optimize monitoring/alerting
- [ ] Plan next deployment

## Deployment Metrics to Monitor (Requirement 29.9)

### Application Metrics

- **Error Rate**: Should be < 1% (rollback if > 2%)
- **Response Time**: 
  - p95 < 500ms
  - p99 < 1000ms
  - Rollback if degrades by 50%
- **Request Rate**: Monitor for unexpected drops or spikes
- **Active Users**: Verify user activity continues normally

### Database Metrics

- **Query Performance**: No queries > 100ms
- **Connection Pool**: Utilization < 80%
- **Replication Lag**: < 5 seconds
- **Lock Waits**: No significant increase

### Infrastructure Metrics

- **CPU Usage**: < 70% average
- **Memory Usage**: < 80%
- **Disk I/O**: No saturation
- **Network**: No packet loss

### External Services

- **Clerk API**: Response time < 200ms
- **AWS S3**: Upload success rate > 99%
- **Resend**: Email delivery rate > 95%
- **Sentry**: Error tracking operational

## Deployment Environments

### Development
- **Purpose**: Local development and testing
- **Database**: Local PostgreSQL
- **Secrets**: Environment variables
- **Deployment**: Manual

### Staging
- **Purpose**: Pre-production testing
- **Database**: Staging PostgreSQL (production-like data)
- **Secrets**: AWS Secrets Manager (staging/)
- **Deployment**: Automated via CI/CD
- **URL**: https://staging-api.muejam.com

### Production
- **Purpose**: Live user traffic
- **Database**: Production PostgreSQL with replicas
- **Secrets**: AWS Secrets Manager (production/)
- **Deployment**: Blue-green with manual approval
- **URL**: https://api.muejam.com

## Emergency Procedures

### Critical Bug in Production

1. **Assess Severity**
   - Is it affecting all users or subset?
   - Is data at risk?
   - Is security compromised?

2. **Immediate Actions**
   - If critical: Initiate rollback immediately
   - If high: Deploy hotfix within 1 hour
   - If medium: Schedule fix in next deployment

3. **Hotfix Procedure**
   ```bash
   # 1. Create hotfix branch
   git checkout -b hotfix/critical-bug main
   
   # 2. Fix the bug
   # Make minimal changes
   
   # 3. Test thoroughly
   pytest apps/backend/tests/ -v
   
   # 4. Fast-track review
   # Get approval from 1 senior engineer
   
   # 5. Deploy to staging
   ./scripts/deploy.sh staging
   
   # 6. Deploy to production
   ./scripts/deploy-blue-green.sh production green
   
   # 7. Monitor closely
   ```

### Database Emergency

1. **Database Corruption**
   - Restore from most recent backup
   - Verify data integrity
   - Investigate root cause

2. **Performance Degradation**
   - Check for long-running queries
   - Verify connection pool not exhausted
   - Check for missing indexes
   - Scale up resources if needed

3. **Replication Lag**
   - Check network connectivity
   - Verify replica health
   - Consider promoting replica to primary

## Compliance and Audit

### Deployment Audit Trail

All deployments are logged with:
- Timestamp
- Version deployed
- Engineer who deployed
- Approval chain
- Test results
- Deployment duration
- Rollback events (if any)

### Compliance Requirements

- **SOC 2**: Deployment procedures documented and followed
- **ISO 27001**: Change management process
- **PCI DSS**: Secure deployment practices
- **GDPR**: Data protection during deployments

## Tools and Scripts

### Deployment Scripts

- `scripts/deploy.sh`: Main deployment script
- `scripts/deploy-blue-green.sh`: Blue-green deployment
- `scripts/rollback.sh`: Rollback to previous version
- `scripts/smoke-tests.sh`: Post-deployment smoke tests
- `scripts/health-check.sh`: Health check verification
- `scripts/switch-traffic.sh`: Traffic switching
- `scripts/notify-deployment.sh`: Slack notifications
- `scripts/maintenance-mode.sh`: Enable/disable maintenance mode

### Monitoring Dashboards

- **Grafana**: Real-time metrics and alerts
- **Sentry**: Error tracking and trends
- **New Relic/DataDog**: APM and performance
- **CloudWatch**: Infrastructure metrics
- **PagerDuty**: Alert management

## Version Control

### Semantic Versioning (Requirement 29.13)

Format: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

Example: `v1.2.3`

### Git Tagging (Requirement 29.12)

```bash
# Create release tag
git tag -a v1.2.3 -m "Release version 1.2.3"

# Push tag to remote
git push origin v1.2.3

# List all tags
git tag -l
```

### Changelog (Requirement 29.12)

Update `CHANGELOG.md` with:
- Version number and date
- New features
- Bug fixes
- Breaking changes
- Migration notes

## Contact Information

### On-Call Engineers
- Primary: [Name] - [Phone] - [Email]
- Secondary: [Name] - [Phone] - [Email]
- Escalation: [Name] - [Phone] - [Email]

### External Services
- **AWS Support**: [Account ID] - [Support Plan]
- **Clerk Support**: [Email] - [Slack Channel]
- **Sentry Support**: [Email]
- **PagerDuty**: [Account URL]

## References

- [Deployment Scripts Repository](./scripts/)
- [Infrastructure as Code](./terraform/)
- [Disaster Recovery Runbook](./DISASTER_RECOVERY_RUNBOOK.md)
- [Secrets Management Guide](./SECRETS_MANAGEMENT.md)
- [Monitoring and Alerting Guide](./MONITORING.md)
