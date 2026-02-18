# Secrets Management Guide

This document describes the secrets management system for the MueJam Library platform.

## Overview

The platform uses AWS Secrets Manager for secure storage and management of sensitive configuration including:
- Database passwords
- API keys for external services
- Encryption keys
- Other sensitive credentials

**Requirements Implemented:**
- 30.2: Store sensitive configuration in AWS Secrets Manager
- 30.4: Automatic secret rotation for database passwords
- 30.5: API key rotation
- 30.6: Different credentials for each environment
- 30.7: Restrict production secrets to authorized personnel
- 30.8: Audit all secret access
- 30.9: Validate required environment variables on startup
- 30.10: Fail with clear error if variables missing
- 30.11: Document all required variables

## Architecture

### Components

1. **SecretsManager** (`infrastructure/secrets_manager.py`)
   - Core service for interacting with AWS Secrets Manager
   - Handles secret retrieval, creation, and updates
   - Implements caching to reduce API calls
   - Provides automatic rotation for database passwords and API keys
   - Audits all secret access for compliance

2. **ConfigValidator** (`infrastructure/config_validator.py`)
   - Validates required environment variables on startup
   - Fails with clear error messages if configuration is invalid
   - Documents all required variables with descriptions and examples

3. **SecretsLoader** (`infrastructure/secrets_loader.py`)
   - Helper functions to load secrets from Secrets Manager
   - Falls back to environment variables for local development
   - Syncs secrets to environment variables if needed

4. **Management Commands**
   - `rotate_secrets`: Rotate database passwords and API keys

## Setup

### 0. Django SECRET_KEY Configuration

The Django SECRET_KEY is a critical security component used for:
- Session signing and validation
- CSRF token generation and validation
- Password reset token generation
- Cryptographic signing of cookies and data

**Security Requirements:**
- Must be at least 50 characters long
- Must be cryptographically random
- Must be unique per environment
- Must never be committed to version control
- Should be rotated periodically (recommended: annually)

**Generation Methods:**

```bash
# Method 1: Django's built-in generator (RECOMMENDED)
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# Method 2: Python secrets module
python -c 'import secrets; print(secrets.token_urlsafe(50))'

# Method 3: OpenSSL
openssl rand -base64 64
```

**Local Development:**
1. Generate a SECRET_KEY using one of the methods above
2. Add it to your `.env` file:
   ```env
   SECRET_KEY=<your-generated-key>
   ```
3. Never commit the `.env` file to version control

**Production Deployment:**
1. Generate a unique SECRET_KEY for production
2. Store it in AWS Secrets Manager:
   ```bash
   aws secretsmanager create-secret \
     --name production/django/secret-key \
     --secret-string '{"SECRET_KEY":"<your-generated-key>"}'
   ```
3. Configure the application to load from Secrets Manager (see below)

**Validation:**

The application automatically validates SECRET_KEY on startup:
- Checks if SECRET_KEY is set
- Validates minimum length (50 characters)
- Rejects insecure patterns (e.g., 'django-insecure', 'change-this', 'example')
- Fails with clear error message if validation fails

See `apps/backend/config/secure_settings.py` for implementation details.

**Error Messages:**

If SECRET_KEY is not set:
```
ImproperlyConfigured: SECRET_KEY environment variable must be set.
Generate a secure key with:
  python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
Then set it in your .env file or environment:
  SECRET_KEY=<generated_key>
```

If SECRET_KEY is too short:
```
ImproperlyConfigured: SECRET_KEY is too short (X characters).
It should be at least 50 characters for security.
Generate a secure key with:
  python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

If SECRET_KEY contains insecure patterns:
```
ImproperlyConfigured: SECRET_KEY appears to be an example value (contains 'pattern').
Generate a secure key with:
  python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

### 1. AWS Secrets Manager Configuration

Create secrets in AWS Secrets Manager with the following naming convention:
```
{environment}/{secret-type}/{secret-name}
```

Examples:
- `production/database/primary`
- `production/api-keys/resend`
- `staging/database/primary`
- `development/api-keys/clerk`

### 2. Secret Structure

#### Database Secrets
```json
{
  "host": "db.example.com",
  "port": "5432",
  "name": "muejam",
  "user": "muejam_user",
  "password": "secure_password_here",
  "rotated_at": "2024-01-15T10:30:00Z"
}
```

#### API Key Secrets
```json
{
  "api_key": "your_api_key_here",
  "previous_key": "previous_key_for_rollback",
  "rotated_at": "2024-01-15T10:30:00Z"
}
```

### 3. Environment Variables

Set the following environment variables:

```bash
# Enable Secrets Manager
USE_SECRETS_MANAGER=True

# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# Environment
ENVIRONMENT=production  # or staging, development

# Cache TTL for secrets (seconds)
SECRETS_CACHE_TTL=300  # 5 minutes
```

### 4. IAM Permissions

The application requires the following IAM permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret",
        "secretsmanager:ListSecrets"
      ],
      "Resource": "arn:aws:secretsmanager:*:*:secret:production/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:CreateSecret",
        "secretsmanager:UpdateSecret",
        "secretsmanager:PutSecretValue",
        "secretsmanager:RotateSecret"
      ],
      "Resource": "arn:aws:secretsmanager:*:*:secret:production/*",
      "Condition": {
        "StringEquals": {
          "aws:PrincipalTag/Role": "admin"
        }
      }
    }
  ]
}
```

## Usage

### Loading Secrets in Code

```python
from infrastructure.secrets_manager import get_secrets_manager

# Get secrets manager instance
secrets_manager = get_secrets_manager()

# Retrieve a secret
secret_data = secrets_manager.get_secret('database/primary')
db_password = secret_data['password']

# Or use the helper function
from infrastructure.secrets_loader import load_secret_or_env

db_password = load_secret_or_env(
    secret_name='database/primary',
    env_var='DATABASE_PASSWORD',
    secret_key='password'
)
```

### Rotating Secrets

#### Manual Rotation

```bash
# Rotate database password
python manage.py rotate_secrets --type database --name primary

# Rotate API key
python manage.py rotate_secrets --type api-key --name resend

# Rotate all secrets
python manage.py rotate_secrets --all

# Dry run (show what would be rotated)
python manage.py rotate_secrets --all --dry-run
```

#### Automatic Rotation

Set up AWS Secrets Manager automatic rotation:

1. Create a Lambda function for rotation
2. Configure rotation schedule (e.g., every 90 days)
3. Test rotation in non-production environment first

**Database Password Rotation:**
- Quarterly rotation (every 90 days)
- Requires updating database server with new password
- Use blue-green deployment to minimize downtime

**API Key Rotation:**
- Annual rotation
- Store previous key for rollback
- Update service configuration after rotation

### Configuration Validation

The application validates configuration on startup:

```python
# Automatic validation on startup
# Set SKIP_CONFIG_VALIDATION=True to disable

# Manual validation
from infrastructure.config_validator import ConfigValidator

validator = ConfigValidator()
is_valid, errors = validator.validate(fail_on_error=False)

if not is_valid:
    for error in errors:
        print(error)
```

### Generating Documentation

```python
from infrastructure.config_validator import ConfigValidator

validator = ConfigValidator()

# Print documentation
print(validator.get_documentation())

# Export to file
validator.export_documentation('docs/ENVIRONMENT_VARIABLES.md')
```

## Security Best Practices

### 1. Access Control

**Production Secrets:**
- Restrict access to authorized personnel only
- Use IAM roles with least privilege principle
- Enable MFA for users with secret access
- Regularly review access logs

**Non-Production Secrets:**
- Use separate secrets for each environment
- Never use production secrets in staging/development
- Rotate non-production secrets regularly

### 2. Audit Logging

All secret access is automatically logged:
- Retrieval attempts (success and failure)
- Creation and updates
- Rotation events
- Unauthorized access attempts

Audit logs are stored in:
- Application audit log table
- AWS CloudTrail (for AWS API calls)
- Structured application logs

### 3. Alerting

Alerts are triggered for:
- Unauthorized access attempts (critical)
- Failed secret retrievals (high)
- Rotation failures (high)
- Unusual access patterns (medium)

Alerts are sent via:
- Email to administrators
- Slack notifications
- PagerDuty for critical alerts

### 4. Encryption

- All secrets are encrypted at rest in AWS Secrets Manager
- Secrets are encrypted in transit using TLS
- Cache is stored in Redis with encryption enabled
- Never log secret values

## Troubleshooting

### Secret Not Found

```
SecretNotFoundError: Secret not found: database/primary
```

**Solution:**
1. Verify secret exists in AWS Secrets Manager
2. Check secret name matches environment prefix
3. Verify IAM permissions allow GetSecretValue

### Access Denied

```
SecretAccessDeniedError: Access denied to secret: database/primary
```

**Solution:**
1. Verify IAM role has required permissions
2. Check resource ARN in IAM policy
3. Verify environment prefix matches

### Configuration Validation Failed

```
ConfigValidationError: Missing required environment variable: SECRET_KEY
```

**Solution:**
1. Set missing environment variable
2. Or store in AWS Secrets Manager and enable USE_SECRETS_MANAGER
3. Check .env file for local development

### Rotation Failed

```
SecretsManagerError: Password rotation failed
```

**Solution:**
1. Check AWS Secrets Manager service status
2. Verify IAM permissions for UpdateSecret
3. Check application logs for detailed error
4. Verify database server is accessible

## Migration Guide

### Migrating from Environment Variables to Secrets Manager

1. **Audit Current Configuration**
   ```bash
   python manage.py shell
   >>> from infrastructure.config_validator import ConfigValidator
   >>> validator = ConfigValidator()
   >>> print(validator.get_documentation())
   ```

2. **Create Secrets in AWS**
   ```bash
   # For each sensitive variable, create a secret
   aws secretsmanager create-secret \
     --name production/database/primary \
     --secret-string '{"password":"your_password"}'
   ```

3. **Update Application Configuration**
   ```bash
   # Enable Secrets Manager
   export USE_SECRETS_MANAGER=True
   
   # Test secret retrieval
   python manage.py shell
   >>> from infrastructure.secrets_manager import get_secrets_manager
   >>> sm = get_secrets_manager()
   >>> secret = sm.get_secret('database/primary')
   >>> print(secret)
   ```

4. **Deploy and Verify**
   ```bash
   # Deploy to staging first
   # Verify application starts successfully
   # Check logs for any secret retrieval errors
   
   # Deploy to production
   # Monitor error rates and performance
   ```

5. **Remove Environment Variables**
   ```bash
   # After successful deployment, remove sensitive env vars
   # Keep non-sensitive configuration in environment
   ```

## Compliance

This secrets management system helps meet the following compliance requirements:

- **SOC 2:** Secure storage and access control for sensitive data
- **PCI DSS:** Encryption of cardholder data at rest and in transit
- **GDPR:** Protection of personal data and access logging
- **HIPAA:** Secure storage of protected health information (if applicable)

## References

- [AWS Secrets Manager Documentation](https://docs.aws.amazon.com/secretsmanager/)
- [AWS Secrets Manager Best Practices](https://docs.aws.amazon.com/secretsmanager/latest/userguide/best-practices.html)
- [Boto3 Secrets Manager Client](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/secretsmanager.html)
