# Secrets Management Guide

This document outlines how to manage secrets and sensitive configuration for the MueJam Library platform.

## Development Environment

### Local Development

For local development, secrets are stored in `.env` files:

- `backend/.env` - Backend secrets
- `frontend/.env.local` - Frontend secrets

**Important:** These files are gitignored and should never be committed to version control.

### Required Secrets

#### Backend Secrets

1. **Django Secret Key**
   ```bash
   # Generate a new secret key
   python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
   ```

2. **Clerk Authentication**
   - Sign up at https://clerk.com
   - Create a new application
   - Copy the Secret Key and Publishable Key from the dashboard

3. **AWS S3**
   - Create an AWS account
   - Create an S3 bucket for media storage
   - Create an IAM user with S3 access
   - Generate access keys for the IAM user
   - Required permissions: `s3:PutObject`, `s3:GetObject`, `s3:DeleteObject`

4. **Resend Email**
   - Sign up at https://resend.com
   - Create an API key from the dashboard
   - Verify your sending domain

#### Frontend Secrets

1. **Clerk Publishable Key**
   - Same as backend, but use the publishable key (safe for client-side)

2. **API URL**
   - For local development: `http://localhost:8000/v1`
   - For production: Your production API URL

## Production Environment

### Environment Variables

For production deployments, use your hosting platform's secrets management:

#### Vercel (Frontend)

1. Go to Project Settings → Environment Variables
2. Add all variables from `frontend/.env.example`
3. Set different values for Production, Preview, and Development

#### Railway/Render/Heroku (Backend)

1. Use the platform's environment variables UI
2. Add all variables from `backend/.env.example`
3. Ensure `DEBUG=False` in production

### Docker Secrets (Docker Swarm)

If deploying with Docker Swarm:

```bash
# Create secrets
echo "your-secret-key" | docker secret create django_secret_key -
echo "your-clerk-key" | docker secret create clerk_secret_key -
echo "your-aws-key" | docker secret create aws_access_key -
echo "your-aws-secret" | docker secret create aws_secret_key -
echo "your-resend-key" | docker secret create resend_api_key -
```

Update `docker-compose.yml` to use secrets:

```yaml
services:
  backend:
    secrets:
      - django_secret_key
      - clerk_secret_key
      - aws_access_key
      - aws_secret_key
      - resend_api_key

secrets:
  django_secret_key:
    external: true
  clerk_secret_key:
    external: true
  aws_access_key:
    external: true
  aws_secret_key:
    external: true
  resend_api_key:
    external: true
```

### Kubernetes Secrets

If deploying to Kubernetes:

```bash
# Create secrets
kubectl create secret generic muejam-backend-secrets \
  --from-literal=SECRET_KEY='your-secret-key' \
  --from-literal=CLERK_SECRET_KEY='your-clerk-key' \
  --from-literal=AWS_ACCESS_KEY_ID='your-aws-key' \
  --from-literal=AWS_SECRET_ACCESS_KEY='your-aws-secret' \
  --from-literal=RESEND_API_KEY='your-resend-key'
```

Reference in deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: muejam-backend
spec:
  template:
    spec:
      containers:
      - name: backend
        envFrom:
        - secretRef:
            name: muejam-backend-secrets
```

## Secret Rotation

### Regular Rotation Schedule

- **Django Secret Key**: Rotate every 90 days
- **API Keys**: Rotate every 90 days
- **AWS Access Keys**: Rotate every 90 days
- **Database Passwords**: Rotate every 90 days

### Rotation Process

1. Generate new secret
2. Update in secrets management system
3. Deploy new version
4. Verify functionality
5. Revoke old secret

### Emergency Rotation

If a secret is compromised:

1. Immediately generate new secret
2. Update in all environments
3. Deploy emergency update
4. Revoke compromised secret
5. Audit access logs
6. Document incident

## Security Best Practices

### Development

- ✅ Use `.env` files for local secrets
- ✅ Never commit `.env` files to git
- ✅ Use different secrets for dev/staging/prod
- ✅ Rotate secrets regularly
- ❌ Never hardcode secrets in code
- ❌ Never share secrets via email/chat
- ❌ Never log secrets

### Production

- ✅ Use platform-specific secrets management
- ✅ Enable secret encryption at rest
- ✅ Restrict access to secrets (principle of least privilege)
- ✅ Monitor secret access
- ✅ Use separate AWS IAM users per environment
- ✅ Enable MFA for AWS root account
- ❌ Never use root AWS credentials
- ❌ Never expose secrets in error messages
- ❌ Never include secrets in logs

## Secrets Checklist

Before deploying to production:

- [ ] All secrets are stored in secure secrets management
- [ ] No secrets are committed to git
- [ ] `DEBUG=False` in production
- [ ] Different secrets for each environment
- [ ] AWS IAM user has minimal required permissions
- [ ] S3 bucket has appropriate access policies
- [ ] Clerk webhook secret is configured
- [ ] Database uses strong password
- [ ] Redis/Valkey requires authentication
- [ ] CORS is configured for production domain only
- [ ] HTTPS is enforced
- [ ] Secret rotation schedule is documented

## Troubleshooting

### Secret Not Found

If you get "secret not found" errors:

1. Verify the secret exists in your secrets management system
2. Check the secret name matches exactly (case-sensitive)
3. Ensure the application has permission to access the secret
4. Restart the application after adding secrets

### Invalid Secret Format

If you get "invalid secret" errors:

1. Check for extra whitespace or newlines
2. Verify the secret format matches requirements
3. Ensure special characters are properly escaped
4. Test the secret in isolation

### Permission Denied

If you get permission errors:

1. Verify IAM policies grant required permissions
2. Check security group rules
3. Ensure the application role has access
4. Review audit logs for denied requests

## Support

For questions about secrets management:

1. Check this documentation
2. Review platform-specific docs (Vercel, Railway, etc.)
3. Contact the development team
4. For security incidents, follow the incident response plan

## References

- [Django Security Best Practices](https://docs.djangoproject.com/en/stable/topics/security/)
- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [AWS IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [Clerk Security](https://clerk.com/docs/security)
