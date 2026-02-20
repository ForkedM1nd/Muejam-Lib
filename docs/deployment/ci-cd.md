# CI/CD Pipeline Documentation

This document describes the Continuous Integration and Continuous Deployment (CI/CD) pipeline for MueJam Library.

## Overview

The CI/CD pipeline automates testing, building, and deploying the application to ensure code quality and rapid, reliable deployments.

## Pipeline Architecture

```
┌─────────────┐
│  Developer  │
│   Commits   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   GitHub    │
│  Repository │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   GitHub    │
│   Actions   │
│   (CI/CD)   │
└──────┬──────┘
       │
       ├─── Lint & Test
       ├─── Build
       ├─── Security Scan
       └─── Deploy
              │
              ├─── Staging (auto)
              └─── Production (manual approval)
```

## GitHub Actions Workflows

### Current Implemented Baseline

The repository currently ships with a baseline infrastructure workflow:

- **File**: `.github/workflows/infra-devops.yml`
- **Purpose**: Validate Terraform configuration, deployment shell script syntax, and Docker Compose configuration on push/PR.

This baseline acts as a guardrail while the broader CI and CD flows below are incrementally rolled out.

### CI Workflow (Test & Build)

**Trigger**: On every push and pull request

**File**: `.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  backend-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: |
          cd apps/backend
          pip install -r requirements.txt
          pip install flake8 black
          
      - name: Run linters
        run: |
          cd apps/backend
          flake8 apps/
          black --check apps/

  backend-test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: test_muejam
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_password
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      valkey:
        image: valkey/valkey:7-alpine
        options: >-
          --health-cmd "valkey-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: |
          cd apps/backend
          pip install -r requirements.txt
          
      - name: Run tests
        env:
          DATABASE_URL: postgresql://test_user:test_password@localhost:5432/test_muejam
          VALKEY_URL: redis://localhost:6379/0
          SECRET_KEY: test-secret-key
        run: |
          cd apps/backend
          python -m pytest --cov=apps --cov-report=xml
          
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./apps/backend/coverage.xml

  frontend-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          
      - name: Install dependencies
        run: |
          cd apps/frontend
          npm ci
          
      - name: Run linter
        run: |
          cd apps/frontend
          npm run lint

  frontend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          
      - name: Install dependencies
        run: |
          cd apps/frontend
          npm ci
          
      - name: Run tests
        run: |
          cd apps/frontend
          npm test -- --coverage
          
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./apps/frontend/coverage/lcov.info

  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'
          
      - name: Upload Trivy results to GitHub Security
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'
```

### CD Workflow (Deploy)

**Trigger**: On push to main (after CI passes)

**File**: `.github/workflows/deploy.yml`

```yaml
name: Deploy

on:
  push:
    branches: [main]
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to deploy to'
        required: true
        type: choice
        options:
          - staging
          - production

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
          
      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v1
        
      - name: Build and push backend image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          ECR_REPOSITORY: muejam-backend
          IMAGE_TAG: ${{ github.sha }}
        run: |
          cd apps/backend
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
          
      - name: Build frontend
        run: |
          cd apps/frontend
          npm ci
          npm run build
          
      - name: Deploy frontend to S3
        run: |
          aws s3 sync apps/frontend/dist s3://muejam-frontend-${{ github.event.inputs.environment || 'staging' }}/ --delete

  deploy-staging:
    needs: build
    runs-on: ubuntu-latest
    if: github.event.inputs.environment == 'staging' || github.ref == 'refs/heads/main'
    environment:
      name: staging
      url: https://staging.muejam.com
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
          
      - name: Deploy to ECS
        run: |
          ./scripts/deployment/deploy.sh staging ${{ github.sha }}
          
      - name: Run smoke tests
        run: |
          ./scripts/deployment/smoke-tests.sh staging
          
      - name: Notify deployment
        run: |
          ./scripts/deployment/notify-deployment.sh staging success

  deploy-production:
    needs: [build, deploy-staging]
    runs-on: ubuntu-latest
    if: github.event.inputs.environment == 'production'
    environment:
      name: production
      url: https://muejam.com
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
          
      - name: Deploy to ECS (Blue/Green)
        run: |
          ./scripts/deployment/deploy-blue-green.sh production ${{ github.sha }}
          
      - name: Run smoke tests
        run: |
          ./scripts/deployment/smoke-tests.sh production
          
      - name: Monitor deployment
        run: |
          ./scripts/deployment/check-error-rate.sh production
          ./scripts/deployment/check-latency.sh production
          
      - name: Notify deployment
        run: |
          ./scripts/deployment/notify-deployment.sh production success
```

## Environment Configuration

### Staging Environment

**Purpose**: Pre-production testing

**Configuration**:
- Auto-deploy on merge to main
- Production-like setup
- Reduced capacity
- Test data

**Access**:
- URL: https://staging.muejam.com
- API: https://api-staging.muejam.com

### Production Environment

**Purpose**: Live user-facing application

**Configuration**:
- Manual approval required
- Blue/green deployment
- Full capacity
- Real data

**Access**:
- URL: https://muejam.com
- API: https://api.muejam.com

## Deployment Process

### Automatic Deployment (Staging)

1. Developer pushes to main branch
2. CI workflow runs (tests, linting, security scan)
3. If CI passes, CD workflow starts
4. Build Docker images
5. Push images to ECR
6. Deploy to staging ECS
7. Run smoke tests
8. Send notification

### Manual Deployment (Production)

1. Navigate to GitHub Actions
2. Select "Deploy" workflow
3. Click "Run workflow"
4. Select "production" environment
5. Click "Run workflow" button
6. Approve deployment (if required)
7. Monitor deployment progress
8. Verify deployment success

## Rollback Procedure

### Automatic Rollback

If smoke tests fail after deployment:

```yaml
- name: Rollback on failure
  if: failure()
  run: |
    ./scripts/deployment/rollback.sh ${{ github.event.inputs.environment }}
```

### Manual Rollback

```bash
# Via GitHub Actions
# 1. Go to Actions tab
# 2. Select "Deploy" workflow
# 3. Run workflow with previous commit SHA

# Via CLI
./scripts/deployment/rollback.sh production
```

## Secrets Management

### Required Secrets

Configure in GitHub Settings > Secrets:

**AWS**:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

**Database**:
- `DATABASE_URL_STAGING`
- `DATABASE_URL_PRODUCTION`

**Application**:
- `SECRET_KEY_STAGING`
- `SECRET_KEY_PRODUCTION`
- `CLERK_SECRET_KEY`

**Monitoring**:
- `SENTRY_DSN`
- `NEW_RELIC_LICENSE_KEY`

**Notifications**:
- `SLACK_WEBHOOK_URL`

## Monitoring and Notifications

### Deployment Notifications

Sent to Slack on:
- Deployment start
- Deployment success
- Deployment failure
- Rollback

**Format**:
```
🚀 Deployment to production started
   Commit: abc123 - "feat: add user profiles"
   Author: @developer
   Environment: production
   
✅ Deployment to production succeeded
   Duration: 5m 23s
   Version: v1.2.0
   URL: https://muejam.com
```

### Deployment Metrics

Track in monitoring dashboard:
- Deployment frequency
- Deployment duration
- Success rate
- Rollback rate
- Time to recovery

## Best Practices

### Branch Strategy

```
main (production)
  ↑
develop (staging)
  ↑
feature/* (development)
```

**Rules**:
- Feature branches merge to develop
- Develop merges to main after testing
- Hotfixes can go directly to main

### Commit Messages

Follow conventional commits:

```
feat: add user profile editing
fix: resolve login redirect issue
docs: update API documentation
chore: update dependencies
```

### Pull Request Checks

Required before merge:
- [ ] All tests pass
- [ ] Code review approved
- [ ] No merge conflicts
- [ ] Branch up to date
- [ ] Security scan passed

### Deployment Checklist

Before deploying to production:
- [ ] All tests pass in staging
- [ ] Manual testing completed
- [ ] Performance acceptable
- [ ] No critical bugs
- [ ] Database migrations tested
- [ ] Rollback plan ready
- [ ] Team notified

## Troubleshooting

### CI Failing

**Problem**: Tests fail in CI but pass locally

**Solutions**:
- Check environment variables
- Verify service versions match
- Check for race conditions
- Review CI logs

### Deployment Failing

**Problem**: Deployment fails during CD

**Solutions**:
- Check AWS credentials
- Verify ECR permissions
- Check ECS task definition
- Review CloudWatch logs

### Smoke Tests Failing

**Problem**: Smoke tests fail after deployment

**Solutions**:
- Check application logs
- Verify database migrations
- Check environment variables
- Test endpoints manually

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [AWS ECS Deployment](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-types.html)
- [Blue/Green Deployment](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-type-bluegreen.html)
- [Deployment Scripts](../../scripts/deployment/)
