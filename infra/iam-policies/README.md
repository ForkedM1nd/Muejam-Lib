# IAM Policies for Secrets Management

This directory contains IAM policy templates for secure access control to AWS Secrets Manager.

## Requirements

Implements Requirements 30.7 and 30.8:
- 30.7: Restrict production secrets to authorized personnel
- 30.8: Audit all secret access

## Policies

### secrets_manager_policy.json

This policy provides secure access to AWS Secrets Manager with the following controls:

**Read Access:**
- Allows reading secrets from production environment
- Requires principal to have `Environment=production` tag
- Allows describing secret metadata
- Allows listing all secrets

**Write Access:**
- Allows creating, updating, and rotating secrets
- Restricted to principals with `Role=admin` tag
- Only applies to production secrets

**Deny Rules:**
- Explicitly denies deletion of production secrets
- Prevents accidental or malicious secret deletion

## Usage

### 1. Create IAM Role for Application

```bash
aws iam create-role \
  --role-name muejam-production-app \
  --assume-role-policy-document file://trust-policy.json \
  --tags Key=Environment,Value=production
```

### 2. Attach Policy to Role

```bash
aws iam put-role-policy \
  --role-name muejam-production-app \
  --policy-name SecretsManagerAccess \
  --policy-document file://secrets_manager_policy.json
```

### 3. Create IAM Role for Administrators

```bash
aws iam create-role \
  --role-name muejam-admin \
  --assume-role-policy-document file://admin-trust-policy.json \
  --tags Key=Role,Value=admin Key=Environment,Value=production
```

### 4. Attach Policy to Admin Role

```bash
aws iam put-role-policy \
  --role-name muejam-admin \
  --policy-name SecretsManagerFullAccess \
  --policy-document file://secrets_manager_policy.json
```

## Access Control Matrix

| Role | Read Secrets | Write Secrets | Rotate Secrets | Delete Secrets |
|------|--------------|---------------|----------------|----------------|
| Application (production) | ✅ | ❌ | ❌ | ❌ |
| Application (staging) | ✅ (staging only) | ❌ | ❌ | ❌ |
| Administrator | ✅ | ✅ | ✅ | ❌ |
| Developer | ✅ (dev only) | ✅ (dev only) | ❌ | ❌ |

## Audit Logging

All secret access is automatically logged in:

1. **AWS CloudTrail**
   - All API calls to Secrets Manager
   - Includes principal, timestamp, and action
   - Stored for 90 days by default

2. **Application Audit Logs**
   - Secret retrieval attempts
   - Success and failure events
   - Stored in audit_log table

3. **Structured Application Logs**
   - Detailed context for each access
   - Includes request ID and user context
   - Stored in CloudWatch Logs

## Monitoring and Alerting

### CloudWatch Alarms

Create alarms for:
- Unauthorized access attempts
- Failed secret retrievals
- Unusual access patterns
- Secret rotation failures

Example alarm:
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name secrets-unauthorized-access \
  --alarm-description "Alert on unauthorized secret access" \
  --metric-name UnauthorizedAccess \
  --namespace AWS/SecretsManager \
  --statistic Sum \
  --period 300 \
  --threshold 1 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1
```

### PagerDuty Integration

Critical alerts are sent to PagerDuty:
- Unauthorized access attempts (critical)
- Production secret access by non-production roles (high)
- Failed rotation attempts (high)

## Best Practices

### 1. Principle of Least Privilege
- Grant only necessary permissions
- Use condition keys to restrict access
- Regularly review and audit permissions

### 2. Separation of Duties
- Application roles: read-only access
- Admin roles: write access with MFA
- Separate roles for each environment

### 3. Tag-Based Access Control
- Use tags to enforce environment boundaries
- Require specific tags for sensitive operations
- Regularly audit tag compliance

### 4. MFA for Sensitive Operations
- Require MFA for secret rotation
- Require MFA for production access
- Use hardware MFA devices for admins

### 5. Regular Audits
- Review CloudTrail logs weekly
- Audit IAM permissions monthly
- Review secret access patterns quarterly

## Compliance

This access control system helps meet:

- **SOC 2 Type II:** Access control and audit logging
- **ISO 27001:** Information security management
- **PCI DSS:** Requirement 7 (Restrict access to cardholder data)
- **GDPR:** Article 32 (Security of processing)

## Troubleshooting

### Access Denied Error

```
SecretAccessDeniedError: Access denied to secret: production/database/primary
```

**Check:**
1. IAM role has required permissions
2. Principal has correct tags (Environment, Role)
3. Resource ARN matches policy
4. No explicit deny rules apply

### Audit Log Not Created

**Check:**
1. Application has permissions to write to audit_log table
2. AuditLogService is properly configured
3. Database connection is healthy
4. Check application logs for errors

### Alert Not Triggered

**Check:**
1. CloudWatch alarm is properly configured
2. Metric is being published correctly
3. PagerDuty integration is configured
4. Check alerting service logs

## References

- [AWS Secrets Manager Access Control](https://docs.aws.amazon.com/secretsmanager/latest/userguide/auth-and-access.html)
- [IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [CloudTrail Logging](https://docs.aws.amazon.com/secretsmanager/latest/userguide/monitoring-cloudtrail.html)
