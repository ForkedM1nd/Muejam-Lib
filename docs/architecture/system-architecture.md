# MueJam System Architecture

## Overview

MueJam is a creative writing platform built with Django (Python) backend and modern web technologies. This document describes the system architecture, components, and design decisions.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Load Balancer                        │
│                    (AWS ALB / Nginx)                         │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
┌────────▼────────┐ ┌───▼────────┐ ┌───▼────────┐
│   Web Server 1  │ │ Web Server 2│ │ Web Server N│
│   (Gunicorn)    │ │  (Gunicorn) │ │  (Gunicorn) │
│   Django App    │ │  Django App │ │  Django App │
└────────┬────────┘ └───┬────────┘ └───┬────────┘
         │              │              │
         └──────────────┼──────────────┘
                        │
         ┌──────────────┼──────────────┐
         │              │              │
┌────────▼────────┐ ┌──▼─────────┐ ┌─▼──────────┐
│   PostgreSQL    │ │   Redis    │ │   Celery   │
│   (Primary)     │ │   Cache    │ │   Workers  │
└─────────────────┘ └────────────┘ └────────────┘
```

## Components

### 1. Application Layer

**Technology**: Django 4.x + Python 3.13

**Components**:
- **Web Server**: Gunicorn with multiple workers
- **ASGI Server**: For async operations
- **Middleware Stack**: Security, rate limiting, timeout, logging
- **API Framework**: Django REST Framework

**Responsibilities**:
- HTTP request handling
- Business logic execution
- Authentication & authorization
- API endpoints
- Admin interface

### 2. Database Layer

**Technology**: PostgreSQL 15+

**Configuration**:
- Connection pooling via pgbouncer
- Read replicas for scaling
- Automated backups
- Point-in-time recovery

**Schema**:
- Users and authentication
- Stories and chapters
- Social features (follows, likes)
- Moderation and reports
- Audit logs

### 3. Cache Layer

**Technology**: Redis 7+

**Usage**:
- L1: In-memory cache (per instance)
- L2: Redis (shared across instances)
- Session storage
- Rate limiting counters
- Celery message broker

**Cache Strategy**:
- User profiles: 5 minutes TTL
- Story metadata: 10 minutes TTL
- Trending data: 15 minutes TTL
- Tag-based invalidation

### 4. Background Jobs

**Technology**: Celery + Redis

**Workers**:
- Default queue: General tasks
- Priority queue: Time-sensitive tasks
- Slow queue: Long-running tasks

**Tasks**:
- Email notifications
- Trending score calculation
- Data exports
- Image processing
- Analytics aggregation

### 5. External Services

**Authentication**: Clerk
- JWT token verification
- User management
- OAuth providers

**Email**: Resend
- Transactional emails
- Notification emails

**Storage**: AWS S3 / Azure Blob
- User uploads
- Story covers
- Backups

**Monitoring**:
- Sentry: Error tracking
- New Relic/DataDog: APM
- CloudWatch/Azure Monitor: Infrastructure

## Data Flow

### Read Request Flow

```
1. User Request → Load Balancer
2. Load Balancer → Web Server (round-robin)
3. Web Server → Middleware Stack
   - Rate limiting check (Redis)
   - Authentication (JWT verification)
   - Request logging
4. Web Server → Cache Check (L1 → L2)
5. If cache miss → Database Query
6. Response → Cache Update
7. Response → User
```

### Write Request Flow

```
1. User Request → Load Balancer
2. Load Balancer → Web Server
3. Web Server → Middleware Stack
   - Rate limiting
   - Authentication
   - Authorization
4. Web Server → Database Transaction
   - Write data
   - Audit log
5. Web Server → Cache Invalidation
6. Web Server → Background Job (if needed)
7. Response → User
```

## Security Architecture

### Authentication Flow

```
1. User logs in via Clerk
2. Clerk returns JWT token
3. Frontend stores token
4. Each request includes JWT in Authorization header
5. Middleware verifies JWT signature with Clerk JWKS
6. Middleware loads user profile
7. Request proceeds with authenticated user
```

### Authorization

- Role-based access control (RBAC)
- Resource-level permissions
- Middleware enforcement
- Audit logging for sensitive operations

### Security Layers

1. **Network**: TLS 1.3, HTTPS only
2. **Application**: Rate limiting, input validation, CSRF protection
3. **Data**: Encryption at rest, encrypted backups
4. **Access**: JWT authentication, role-based authorization
5. **Monitoring**: Audit logs, security alerts

## Scalability

### Horizontal Scaling

**Application Tier**:
- Stateless web servers
- Auto-scaling based on CPU/memory
- Session storage in Redis
- Shared cache layer

**Database Tier**:
- Read replicas for read-heavy workload
- Connection pooling (pgbouncer)
- Query optimization
- Indexes on common queries

**Cache Tier**:
- Redis Cluster for high availability
- Separate cache instances per environment
- Cache warming for hot data

### Vertical Scaling

- Increase instance sizes for database
- More CPU/memory for web servers
- Larger Redis instances

### Current Capacity

- **Concurrent Users**: 500-1000
- **Requests/Second**: 100-200
- **Database Connections**: 50 per instance
- **Cache Hit Rate**: 80%+

## High Availability

### Redundancy

- Multiple web server instances
- Database with read replicas
- Redis with replication
- Multi-AZ deployment

### Failover

- Load balancer health checks
- Automatic instance replacement
- Database automatic failover
- Redis Sentinel for HA

### Backup & Recovery

- **Database**: Daily backups, 30-day retention
- **Files**: S3 versioning, cross-region replication
- **Configuration**: Version controlled
- **RTO**: < 1 hour
- **RPO**: < 15 minutes

## Performance

### Optimization Strategies

1. **Database**:
   - Connection pooling
   - Query optimization (select_related, prefetch_related)
   - Indexes on foreign keys and common queries
   - Slow query monitoring

2. **Caching**:
   - Two-tier cache (L1 + L2)
   - Cache warming for hot data
   - Tag-based invalidation
   - Cache hit rate monitoring

3. **Application**:
   - Async operations for I/O
   - Background jobs for heavy tasks
   - Request timeout protection
   - Pagination for large datasets

4. **Frontend**:
   - CDN for static assets
   - Image optimization
   - Lazy loading
   - Code splitting

### Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| P95 Latency | < 500ms | TBD |
| P99 Latency | < 1000ms | TBD |
| Error Rate | < 0.5% | TBD |
| Cache Hit Rate | > 80% | TBD |
| DB Query Time | < 50ms | TBD |

## Monitoring & Observability

### Metrics

- **Application**: Request rate, error rate, latency
- **Database**: Query time, connection pool, slow queries
- **Cache**: Hit rate, memory usage, eviction rate
- **System**: CPU, memory, disk, network

### Logging

- **Application Logs**: Structured JSON logs
- **Access Logs**: Request/response logging
- **Audit Logs**: Security and compliance
- **Error Logs**: Sentry integration

### Alerting

- High error rate (> 1%)
- Slow response time (P95 > 500ms)
- Database pool exhaustion (> 80%)
- Cache hit rate low (< 60%)
- Disk space low (> 80%)

## Deployment

### Environments

1. **Development**: Local development
2. **Staging**: Pre-production testing
3. **Production**: Live environment

### CI/CD Pipeline

```
1. Code Push → GitHub
2. GitHub Actions → Run Tests
3. Tests Pass → Build Docker Image
4. Push Image → Container Registry
5. Deploy to Staging → Smoke Tests
6. Manual Approval → Deploy to Production
7. Health Checks → Monitor
```

### Deployment Strategy

- **Blue-Green Deployment**: Zero-downtime deployments
- **Rolling Updates**: Gradual instance replacement
- **Canary Releases**: Test with small percentage of traffic
- **Rollback**: Automated rollback on health check failure

## Technology Stack

### Backend

- **Language**: Python 3.13
- **Framework**: Django 4.x
- **API**: Django REST Framework
- **ORM**: Prisma (with Django integration)
- **Task Queue**: Celery
- **Web Server**: Gunicorn

### Database

- **Primary**: PostgreSQL 15+
- **Cache**: Redis 7+
- **Search**: PostgreSQL Full-Text Search

### Infrastructure

- **Cloud**: AWS / Azure / GCP
- **Containers**: Docker
- **Orchestration**: Kubernetes / ECS
- **Load Balancer**: AWS ALB / Nginx
- **CDN**: CloudFront / Azure CDN

### Monitoring

- **APM**: New Relic / DataDog
- **Errors**: Sentry
- **Logs**: CloudWatch / ELK Stack
- **Metrics**: Prometheus + Grafana

## Design Decisions

### Why Django?

- Mature framework with large ecosystem
- Built-in admin interface
- Strong ORM and migration system
- Excellent security features
- Large community and documentation

### Why PostgreSQL?

- ACID compliance
- JSON support for flexible data
- Full-text search capabilities
- Mature replication and backup tools
- Excellent performance

### Why Redis?

- Fast in-memory cache
- Pub/sub for real-time features
- Celery message broker
- Session storage
- Rate limiting counters

### Why Celery?

- Mature task queue system
- Django integration
- Flexible routing and priorities
- Monitoring tools (Flower)
- Retry and error handling

## Future Improvements

### Short-term (3-6 months)

- [ ] Implement read replicas
- [ ] Add CDN for static assets
- [ ] Optimize database queries
- [ ] Improve cache hit rate
- [ ] Add more monitoring

### Medium-term (6-12 months)

- [ ] Microservices for specific features
- [ ] GraphQL API
- [ ] Real-time notifications (WebSockets)
- [ ] Advanced search (Elasticsearch)
- [ ] Multi-region deployment

### Long-term (12+ months)

- [ ] Event-driven architecture
- [ ] Service mesh
- [ ] Machine learning features
- [ ] Global CDN
- [ ] Edge computing

## References

- [Django Documentation](https://docs.djangoproject.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/documentation)
- [Celery Documentation](https://docs.celeryproject.org/)
- [AWS Best Practices](https://aws.amazon.com/architecture/well-architected/)
