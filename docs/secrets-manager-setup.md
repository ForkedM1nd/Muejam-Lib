# AWS Secrets Manager Setup Guide

This guide explains how to configure AWS Secrets Manager for the MueJam Library application.

## Overview

The application uses AWS Secrets Manager to securely store sensitive configuration in production:
- Database connection strings
- API keys (Clerk, AWS, Resend, Google)
- Other sensitive credentials

In development, the application falls back to environment variables for convenience.

## Prerequisites

1. AWS account with Secrets Manager access
2. AWS CLI configured with appropriate credentials
3. IAM permissions to create and read secrets

## Environment Variables

Set these environment variables to enable Secrets Manager:

```bash
# Enable Secrets Manager integration
USE_SECRETS_MANAGER=True
ENVIRONMENT=production

# AWS Configuration
AWS_REGION=us-east-1  # or your preferred region
```

## Secret Structure

### Database Secrets

**Secret Name**: `production/database/primary`

**Secret Value** (JSON):
```json
{
  "connection_string": "postgresql://username:password@host:5432/database",
  "host": "your-db-host.rds.amazonaws.com",
  "port": "5432",
  "database": "muejam",
  "username": "muejam_user",
  "password": "your-secure-password",
  "rotated_at": "2024-01-01T00:00:00Z"
}
```

### Clerk API Keys

**Secret Name**: `production/api-keys/clerk`

**Secret Value** (JSON):
```json
{
  "secret_key": "sk_live_xxxxxxxxxxxxx",
  "publishable_key": "pk_live_xxxxxxxxxxxxx",
  "rotated_at": "2024-01-01T00:00:00Z"
}
```

### AWS API Keys

**Secret Name**: `production/api-keys/aws`

**Secret Value** (JSON):
```json
{
  "access_key_id": "AKIAXXXXXXXXXXXXX",
  "secret_access_key": "your-secret-access-key",
  "rotated_at": "2024-01-01T00:00:00Z"
}
```

### Resend API Key

**Secret Name**: `production/api-keys/resend`

**Secret Value** (JSON):
```json
{
  "api_key": "re_xxxxxxxxxxxxx",
  "rotated_at": "2024-01-01T00:00:00Z"
}
```

### Google API Keys

**Secret Name**: `production/api-keys/google`

**Secret Value** (JSON):
```json
{
  "safe_browsing_api_key": "AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
  "recaptcha_secret_key": "6LeXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
  "rotated_at": "2024-01-01T00:00:00Z"
}
```

## Creating Secrets via AWS CLI

### 1. Create Database Secret

```bash
aws secretsmanager create-secret \
  --name production/database/primary \
  --description "Primary database connection for MueJam Library" \
  --secret-string '{
    "connection_string": "postgresql://username:password@host:5432/database",
    "host": "your-db-host.rds.amazonaws.com",
    "port": "5432",
    "database": "muejam",
    "username": "muejam_user",
    "password": "your-secure-password",
    "rotated_at": "2024-01-01T00:00:00Z"
  }' \
  --region us-east-1
```

### 2. Create Clerk API Keys Secret

```bash
aws secretsmanager create-secret \
  --name production/api-keys/clerk \
  --description "Clerk authentication API keys" \
  --secret-string '{
    "secret_key": "sk_live_xxxxxxxxxxxxx",
    "publishable_key": "pk_live_xxxxxxxxxxxxx",
    "rotated_at": "2024-01-01T00:00:00Z"
  }' \
  --region us-east-1
```

### 3. Create AWS API Keys Secret

```bash
aws secretsmanager create-secret \
  --name production/api-keys/aws \
  --description "AWS S3 access credentials" \
  --secret-string '{
    "access_key_id": "AKIAXXXXXXXXXXXXX",
    "secret_access_key": "your-secret-access-key",
    "rotated_at": "2024-01-01T00:00:00Z"
  }' \
  --region us-east-1
```

### 4. Create Resend API Key Secret

```bash
aws secretsmanager create-secret \
  --name production/api-keys/resend \
  --description "Resend email service API key" \
  --secret-string '{
    "api_key": "re_xxxxxxxxxxxxx",
    "rotated_at": "2024-01-01T00:00:00Z"
  }' \
  --region us-east-1
```

### 5. Create Google API Keys Secret

```bash
aws secretsmanager create-secret \
  --name production/api-keys/google \
  --description "Google API keys for Safe Browsing and reCAPTCHA" \
  --secret-string '{
    "safe_browsing_api_key": "AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "recaptcha_secret_key": "6LeXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "rotated_at": "2024-01-01T00:00:00Z"
  }' \
  --region us-east-1
```

## IAM Permissions

The application's IAM role needs the following permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": [
        "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:production/database/*",
        "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:production/api-keys/*"
      ]
    }
  ]
}
```

## Secret Rotation

The application includes automatic secret rotation functionality:

### Rotate Database Password

```python
from infrastructure.secrets_manager import get_secrets_manager

secrets_manager = get_secrets_manager()
new_password = secrets_manager.rotate_database_password('primary')
print(f"New password: {new_password}")
```

### Rotate API Key

```python
from infrastructure.secrets_manager import get_secrets_manager

secrets_manager = get_secrets_manager()
new_api_key = secrets_manager.rotate_api_key('resend')
print(f"New API key: {new_api_key}")
```

## Caching

Secrets are cached for 5 minutes by default to reduce API calls. Configure caching:

```bash
# Cache TTL in seconds (default: 300)
SECRETS_CACHE_TTL=300
```

## Development vs Production

### Development (Local)

```bash
# Use environment variables
USE_SECRETS_MANAGER=False
ENVIRONMENT=development

# Set secrets in .env file
DATABASE_URL=postgresql://user:password@localhost:5432/muejam
CLERK_SECRET_KEY=sk_test_xxxxxxxxxxxxx
CLERK_PUBLISHABLE_KEY=pk_test_xxxxxxxxxxxxx
# ... other secrets
```

### Production

```bash
# Use AWS Secrets Manager
USE_SECRETS_MANAGER=True
ENVIRONMENT=production

# AWS configuration
AWS_REGION=us-east-1

# Secrets are loaded from AWS Secrets Manager
# No need to set individual secret environment variables
```

## Troubleshooting

### Secret Not Found

If you see "Secret not found" errors:

1. Verify the secret exists in AWS Secrets Manager
2. Check the secret name matches the expected format: `{environment}/{category}/{name}`
3. Verify IAM permissions allow reading the secret

### Access Denied

If you see "Access denied" errors:

1. Check IAM role has `secretsmanager:GetSecretValue` permission
2. Verify the resource ARN in IAM policy matches your secrets
3. Check AWS credentials are configured correctly

### Fallback to Environment Variables

If Secrets Manager fails, the application falls back to environment variables:

```bash
# These will be used if Secrets Manager is unavailable
DATABASE_URL=postgresql://user:password@localhost:5432/muejam
CLERK_SECRET_KEY=sk_live_xxxxxxxxxxxxx
# ... other secrets
```

## Security Best Practices

1. **Never commit secrets to version control**
2. **Use different secrets for each environment** (development, staging, production)
3. **Rotate secrets regularly** (every 90 days recommended)
4. **Monitor secret access** via CloudTrail and audit logs
5. **Use least privilege IAM policies** - only grant access to required secrets
6. **Enable secret versioning** for rollback capability
7. **Set up alerts** for unauthorized access attempts

## Monitoring

The application logs all secret access for audit purposes:

- Secret retrieval attempts (success/failure)
- Unauthorized access attempts (triggers alerts)
- Secret rotation events

Check application logs and CloudTrail for secret access history.

## References

- [AWS Secrets Manager Documentation](https://docs.aws.amazon.com/secretsmanager/)
- [Boto3 Secrets Manager API](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/secretsmanager.html)
- [IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
