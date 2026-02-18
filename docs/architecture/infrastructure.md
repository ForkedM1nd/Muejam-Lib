# Infrastructure Architecture

This document describes the infrastructure organization and deployment architecture for MueJam Library.

## Overview

MueJam Library infrastructure is organized to separate concerns between application code and infrastructure code, with clear boundaries and responsibilities.

## Infrastructure Organization

### Directory Structure

```
infra/
├── terraform/         # Infrastructure as Code
│   ├── environments/
│   │   ├── dev/
│   │   ├── staging/
│   │   └── production/
│   └── modules/
│       └── cloudfront/
├── iam-policies/      # IAM policy documents
│   ├── secrets-manager-policy.json
│   └── README.md
├── monitoring/        # Monitoring configurations
└── README.md
```

### Infrastructure vs Application Code

**Infrastructure Code** (`apps/backend/infrastructure/`):
- Caching layer (Redis/Valkey)
- Database connection pooling
- Monitoring and metrics
- Logging configuration
- Health checks
- Rate limiting
- Query optimization
- Circuit breakers

**Application Code** (Django apps):
- Business logic
- API endpoints
- Database models
- User-facing features

**Infrastructure as Code** (`infra/`):
- Terraform configurations
- IAM policies
- Cloud resource definitions
- Deployment configurations

## Application Infrastructure

Located in `apps/backend/infrastructure/`, this code provides infrastructure services to the application.

### Caching Layer

**Purpose**: Improve performance by caching frequently accessed data

**Components**:
- L1 Cache: In-memory LRU cache
- L2 Cache: Redis/Valkey distributed cache
- Cache manager with automatic failover

**Usage**:
```python
from infrastructure.cache_manager import CacheManager

cache = CacheManager()
cache.set('user:123', user_data, ttl=300)
user_data = cache.get('user:123')
```

### Database Infrastructure

**Purpose**: Manage database connections, pooling, and optimization

**Components**:
- Connection pooling
- Read replica routing
- Query optimization
- Health monitoring
- Failover management

**Features**:
- Automatic read/write splitting
- Connection pool management
- Replication lag monitoring
- Automatic failover

### Monitoring and Metrics

**Purpose**: Track application performance and health

**Components**:
- Metrics collector
- Health monitor
- Alert manager
- Performance profiler

**Metrics Tracked**:
- Request latency
- Error rates
- Database query performance
- Cache hit rates
- Resource utilization

### Logging

**Purpose**: Structured logging with automatic PII redaction

**Features**:
- JSON-formatted logs
- Automatic PII detection and redaction
- Request/response logging
- Error tracking
- Audit logging

**Configuration**:
```python
# apps/backend/infrastructure/logging_config.py
LOGGING = {
    'version': 1,
    'formatters': {
        'json': {
            'class': 'pythonjsonlogger.jsonlogger.JsonFormatter',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
```

### Rate Limiting

**Purpose**: Protect API from abuse and ensure fair usage

**Implementation**:
- User-based rate limits
- IP-based rate limits
- Sliding window algorithm
- Redis-backed for distributed systems

**Configuration**:
```python
RATE_LIMIT_USER = 100  # requests per minute
RATE_LIMIT_GLOBAL = 1000  # requests per minute
```

## Infrastructure as Code

Located in `infra/`, this defines cloud resources and deployment configuration.

### Terraform Structure

```
infra/terraform/
├── environments/
│   ├── dev/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── terraform.tfvars
│   ├── staging/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── terraform.tfvars
│   └── production/
│       ├── main.tf
│       ├── variables.tf
│       └── terraform.tfvars
└── modules/
    └── cloudfront/
        ├── main.tf
        ├── variables.tf
        └── outputs.tf
```

### Environment Configuration

**Development**:
- Single instance
- Minimal resources
- Debug logging enabled
- No CDN

**Staging**:
- Production-like setup
- Reduced capacity
- Full monitoring
- CDN enabled

**Production**:
- High availability
- Auto-scaling
- Full monitoring and alerting
- CDN with edge caching
- Multi-region backup

### IAM Policies

Located in `infra/iam-policies/`, these define AWS permissions.

**Secrets Manager Policy**:
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
      "Resource": "arn:aws:secretsmanager:*:*:secret:muejam/*"
    }
  ]
}
```

## Deployment Architecture

### Local Development

```
┌─────────────┐
│  Developer  │
│   Machine   │
└──────┬──────┘
       │
       ├─── Backend (Django) :8000
       ├─── Frontend (Vite) :3000
       ├─── PostgreSQL :5432
       └─── Valkey :6379
```

### Staging Environment

```
┌──────────────┐
│   Internet   │
└──────┬───────┘
       │
┌──────▼───────┐
│  CloudFront  │
│     CDN      │
└──────┬───────┘
       │
┌──────▼───────┐
│ Load Balancer│
└──────┬───────┘
       │
       ├─── Backend (ECS) x2
       ├─── Frontend (S3 + CloudFront)
       ├─── PostgreSQL (RDS)
       └─── Valkey (ElastiCache)
```

### Production Environment

```
┌──────────────┐
│   Internet   │
└──────┬───────┘
       │
┌──────▼───────┐
│  CloudFront  │
│     CDN      │
│  (Multi-AZ)  │
└──────┬───────┘
       │
┌──────▼───────┐
│ Load Balancer│
│  (Multi-AZ)  │
└──────┬───────┘
       │
       ├─── Backend (ECS) x4+ (Auto-scaling)
       ├─── Frontend (S3 + CloudFront)
       ├─── PostgreSQL (RDS Multi-AZ)
       │    ├─── Primary
       │    └─── Read Replicas x2
       ├─── Valkey (ElastiCache Cluster)
       └─── Monitoring (CloudWatch, Sentry, New Relic)
```

## Deployment Process

### Continuous Integration

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: |
          cd apps/backend
          python -m pytest
      - name: Run frontend tests
        run: |
          cd apps/frontend
          npm test
```

### Continuous Deployment

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to staging
        run: ./scripts/deployment/deploy.sh staging
        
  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to production
        run: ./scripts/deployment/deploy.sh production
```

### Deployment Scripts

Located in `scripts/deployment/`:

**deploy.sh**: Main deployment script
```bash
#!/bin/bash
ENVIRONMENT=$1

# Build Docker images
docker build -t muejam-backend:$VERSION apps/backend
docker build -t muejam-frontend:$VERSION apps/frontend

# Push to registry
docker push muejam-backend:$VERSION
docker push muejam-frontend:$VERSION

# Update ECS service
aws ecs update-service \
  --cluster muejam-$ENVIRONMENT \
  --service backend \
  --force-new-deployment

# Run smoke tests
./scripts/deployment/smoke-tests.sh $ENVIRONMENT
```

**rollback.sh**: Rollback to previous version
```bash
#!/bin/bash
ENVIRONMENT=$1
PREVIOUS_VERSION=$2

aws ecs update-service \
  --cluster muejam-$ENVIRONMENT \
  --service backend \
  --task-definition muejam-backend:$PREVIOUS_VERSION
```

## Monitoring and Alerting

### Metrics Collection

**Application Metrics**:
- Request rate
- Response time
- Error rate
- Database query performance
- Cache hit rate

**Infrastructure Metrics**:
- CPU utilization
- Memory usage
- Disk I/O
- Network traffic
- Database connections

### Alerting Rules

**Critical Alerts** (Page on-call):
- Error rate > 5%
- Response time > 2s (p95)
- Database down
- Service unavailable

**Warning Alerts** (Email/Slack):
- Error rate > 1%
- Response time > 1s (p95)
- High CPU usage (>80%)
- High memory usage (>80%)
- Replication lag > 10s

### Monitoring Tools

**Sentry**: Error tracking and performance monitoring
**New Relic**: Application performance monitoring
**CloudWatch**: AWS infrastructure monitoring
**Datadog**: Unified monitoring and alerting

## Security

### Secrets Management

All secrets stored in AWS Secrets Manager:
- Database credentials
- API keys
- Encryption keys
- Third-party service credentials

**Access**:
```python
from infrastructure.secrets_manager import SecretsManager

secrets = SecretsManager()
db_password = secrets.get_secret('database/password')
```

### Network Security

- VPC with private subnets
- Security groups restrict access
- WAF for DDoS protection
- SSL/TLS for all connections

### IAM Roles

- Least privilege principle
- Service-specific roles
- No long-lived credentials
- Regular rotation

## Disaster Recovery

### Backup Strategy

**Database**:
- Automated daily backups
- Point-in-time recovery
- Cross-region replication
- 30-day retention

**Files**:
- S3 versioning enabled
- Cross-region replication
- Lifecycle policies

### Recovery Procedures

See [Disaster Recovery Runbook](../deployment/disaster-recovery.md) for detailed procedures.

**RTO** (Recovery Time Objective): 1 hour
**RPO** (Recovery Point Objective): 5 minutes

## Scaling Strategy

### Horizontal Scaling

**Backend**:
- Auto-scaling based on CPU/memory
- Min: 2 instances
- Max: 20 instances
- Target: 70% CPU utilization

**Database**:
- Read replicas for read-heavy workloads
- Connection pooling
- Query optimization

### Vertical Scaling

Increase instance sizes during:
- High traffic events
- Data migrations
- Batch processing

### Caching Strategy

- CDN for static assets
- Redis for session data
- Application-level caching
- Database query caching

## Cost Optimization

### Strategies

- Right-size instances
- Use spot instances for non-critical workloads
- S3 lifecycle policies
- Reserved instances for baseline capacity
- Auto-scaling to match demand

### Monitoring

- Cost alerts
- Resource utilization tracking
- Unused resource identification
- Regular cost reviews

## Resources

- [Terraform Documentation](https://www.terraform.io/docs)
- [AWS Best Practices](https://aws.amazon.com/architecture/well-architected/)
- [12-Factor App](https://12factor.net/)
- [Infrastructure as Code](https://www.oreilly.com/library/view/infrastructure-as-code/9781491924358/)
