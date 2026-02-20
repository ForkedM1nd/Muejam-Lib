# Database Read Replicas

This document describes the read replica configuration and usage for scaling read-heavy database operations.

## Overview

Read replicas provide horizontal scaling for read-heavy database workloads by distributing read queries across multiple database instances while maintaining a single primary instance for write operations.

## Requirements

Implements:
- **Requirement 33.5**: Use database read replicas for read-heavy operations (story listings, user profiles, search)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  (Django with ReadWriteRouter)                              │
└─────────────────────────────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
                ▼                       ▼
┌───────────────────────┐   ┌───────────────────────┐
│   Primary Database    │   │   Read Replicas       │
│   (Write Operations)  │──>│   (Read Operations)   │
│   Multi-AZ            │   │   Replica 1, 2        │
│   db.t3.medium        │   │   db.t3.medium        │
└───────────────────────┘   └───────────────────────┘
```

## Infrastructure Setup

### Terraform Configuration

Read replicas are configured in the RDS Terraform module:

```hcl
# infra/terraform/main.tf

module "rds" {
  source = "./modules/rds"
  
  # ... other configuration ...
  
  # Enable read replicas
  create_read_replicas = true
  replica_count        = 1  # or 2 for high-traffic scenarios
}
```

See [RDS Module README](../../infra/terraform/modules/rds/README.md) for detailed Terraform configuration.

## Application Configuration

### Django Settings

Configure Django to use read replicas:

```python
# settings.py

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'muejam'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'CONN_MAX_AGE': 0,
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c statement_timeout=30000',
        },
    },
    'read_replica': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_READ_NAME', os.getenv('DB_NAME', 'muejam')),
        'USER': os.getenv('DB_READ_USER', os.getenv('DB_USER', 'postgres')),
        'PASSWORD': os.getenv('DB_READ_PASSWORD', os.getenv('DB_PASSWORD', '')),
        'HOST': os.getenv('DB_READ_HOST', os.getenv('DB_HOST', 'localhost')),
        'PORT': os.getenv('DB_READ_PORT', os.getenv('DB_PORT', '5432')),
        'CONN_MAX_AGE': 0,
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c statement_timeout=30000',
        },
    }
}

# Enable read/write splitting
DATABASE_ROUTERS = ['infrastructure.database_config.ReadWriteRouter']

# Enable read replica usage
USE_READ_REPLICA = os.getenv('USE_READ_REPLICA', 'false').lower() == 'true'
```

### Environment Variables

```bash
# Primary database (write operations)
DB_HOST=production-muejam-db-primary.xxxxx.us-east-1.rds.amazonaws.com
DB_NAME=muejam
DB_USER=muejam_admin
DB_PASSWORD=<secure_password>
DB_PORT=5432

# Read replica (read operations)
USE_READ_REPLICA=true
DB_READ_HOST=production-muejam-db-replica-1.xxxxx.us-east-1.rds.amazonaws.com
DB_READ_PORT=5432
```

## Read/Write Routing

### Automatic Routing

The `ReadWriteRouter` automatically routes queries:

```python
# infrastructure/database_config.py

class ReadWriteRouter:
    """
    Database router that directs read queries to read replicas 
    and write queries to primary.
    """
    
    def db_for_read(self, model, **hints):
        """Route read operations to read replica if available."""
        if USE_READ_REPLICA:
            return 'read_replica'
        return 'default'
    
    def db_for_write(self, model, **hints):
        """Route write operations to primary database."""
        return 'default'
```

### Usage Examples

#### Automatic Routing (Recommended)

```python
# Read operations - automatically routed to read replica
stories = Story.objects.filter(published=True)
user_profile = UserProfile.objects.get(user_id=123)
comments = Comment.objects.filter(story_id=456)

# Write operations - automatically routed to primary
story = Story.objects.create(title='New Story', author=user)
user_profile.bio = 'Updated bio'
user_profile.save()
```

#### Explicit Routing

```python
# Force read from primary (for consistency)
story = Story.objects.using('default').get(id=123)

# Force read from replica
stories = Story.objects.using('read_replica').filter(published=True)
```

## Read-Heavy Operations

The following operations are optimized for read replicas:

### 1. Story Listings

```python
# Get published stories - reads from replica
def get_published_stories(limit=50):
    return Story.objects.filter(
        published=True
    ).select_related('author').prefetch_related('tags')[:limit]

# Get trending stories - reads from replica
def get_trending_stories(limit=10):
    return Story.objects.filter(
        published=True
    ).order_by('-view_count')[:limit]
```

### 2. User Profiles

```python
# Get user profile - reads from replica
def get_user_profile(user_id):
    return UserProfile.objects.select_related('user').get(user_id=user_id)

# Get user statistics - reads from replica
def get_user_stats(user_id):
    return {
        'story_count': Story.objects.filter(author_id=user_id).count(),
        'follower_count': Follow.objects.filter(following_id=user_id).count(),
    }
```

### 3. Search Operations

```python
# Search stories - reads from replica
def search_stories(query, filters=None):
    qs = Story.objects.filter(
        published=True,
        title__icontains=query
    )
    
    if filters:
        if 'genre' in filters:
            qs = qs.filter(genre=filters['genre'])
        if 'author' in filters:
            qs = qs.filter(author_id=filters['author'])
    
    return qs.select_related('author')[:100]
```

### 4. Feed Generation

```python
# Get user feed - reads from replica
def get_user_feed(user_id, limit=50):
    following_ids = Follow.objects.filter(
        follower_id=user_id
    ).values_list('following_id', flat=True)
    
    return Story.objects.filter(
        author_id__in=following_ids,
        published=True
    ).order_by('-published_at')[:limit]
```

## Consistency Considerations

### Replication Lag

Read replicas have asynchronous replication, which means there can be a small delay (typically < 1 second) between writes to the primary and reads from replicas.

#### Handling Replication Lag

**1. Read-After-Write Consistency**

For operations that require immediate consistency, read from primary:

```python
# Write to primary
story = Story.objects.create(title='New Story', author=user)

# Read from primary to ensure consistency
story = Story.objects.using('default').get(id=story.id)
```

**2. Session Consistency**

For user-specific data that was just modified, read from primary:

```python
def update_user_profile(user_id, **updates):
    # Write to primary
    profile = UserProfile.objects.get(user_id=user_id)
    for key, value in updates.items():
        setattr(profile, key, value)
    profile.save()
    
    # Read from primary for immediate consistency
    return UserProfile.objects.using('default').get(user_id=user_id)
```

**3. Eventual Consistency**

For operations where slight delays are acceptable, use replicas:

```python
# Acceptable for public listings, search results, etc.
stories = Story.objects.filter(published=True)
```

### Monitoring Replication Lag

CloudWatch alarms monitor replica lag:

```python
# Check replica lag metric
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name ReplicaLag \
  --dimensions Name=DBInstanceIdentifier,Value=production-muejam-db-replica-1 \
  --start-time 2026-02-18T00:00:00Z \
  --end-time 2026-02-18T23:59:59Z \
  --period 300 \
  --statistics Average
```

## Performance Benefits

### Load Distribution

With read replicas, read load is distributed:

```
Without Replicas:
Primary: 100% reads + 100% writes = 200% load

With 1 Replica:
Primary: 0% reads + 100% writes = 100% load
Replica: 100% reads + 0% writes = 100% load

With 2 Replicas:
Primary: 0% reads + 100% writes = 100% load
Replica 1: 50% reads + 0% writes = 50% load
Replica 2: 50% reads + 0% writes = 50% load
```

### Query Performance

Read replicas improve query performance by:

1. **Reduced contention**: Reads don't compete with writes
2. **Dedicated resources**: Each replica has its own CPU, memory, and I/O
3. **Geographic distribution**: Replicas can be placed closer to users (future enhancement)

## Best Practices

### 1. Use Replicas for Read-Heavy Operations

```python
# Good: Use replica for listings
stories = Story.objects.filter(published=True)

# Good: Use replica for search
results = Story.objects.filter(title__icontains=query)

# Good: Use replica for statistics
count = Story.objects.filter(author_id=user_id).count()
```

### 2. Use Primary for Write Operations

```python
# Always use primary for writes
story = Story.objects.create(title='New Story')
story.published = True
story.save()
```

### 3. Use Primary for Read-After-Write

```python
# Write to primary
story = Story.objects.create(title='New Story')

# Read from primary for consistency
story = Story.objects.using('default').get(id=story.id)
```

### 4. Cache Frequently Accessed Data

Combine read replicas with caching for optimal performance:

```python
from infrastructure.database_cache import cache_queryset

@cache_queryset(ttl=300, tags=['story', 'featured'])
def get_featured_stories():
    # Reads from replica, cached for 5 minutes
    return Story.objects.filter(featured=True, published=True)
```

### 5. Monitor Replica Health

```python
from infrastructure.database_config import ConnectionPoolMonitor

# Monitor connection pool health
monitor = ConnectionPoolMonitor(pool_manager)
health = monitor.check_pool_health()

if not health['healthy']:
    for alert in health['alerts']:
        logger.warning(f"Database alert: {alert['message']}")
```

## Scaling Strategies

### Vertical Scaling

Increase instance size for better performance:

```hcl
# Upgrade replica instance class
db_replica_instance_class = "db.r6g.xlarge"
```

### Horizontal Scaling

Add more read replicas for higher read capacity:

```hcl
# Add second read replica
replica_count = 2
```

### Load Balancing

For multiple replicas, implement load balancing:

```python
import random

class LoadBalancedReadRouter:
    """Router that load balances across multiple read replicas."""
    
    def db_for_read(self, model, **hints):
        if USE_READ_REPLICA:
            # Randomly select a replica
            replicas = ['read_replica_1', 'read_replica_2']
            return random.choice(replicas)
        return 'default'
```

## Troubleshooting

### High Replica Lag

**Symptoms**: Replica lag > 1 second

**Solutions**:
1. Check primary database load
2. Upgrade replica instance class
3. Reduce write load on primary
4. Add more replicas to distribute read load

### Connection Errors

**Symptoms**: Connection timeouts to replica

**Solutions**:
1. Check security group rules
2. Verify network connectivity
3. Check connection pool configuration
4. Review CloudWatch metrics

### Inconsistent Data

**Symptoms**: Stale data from replicas

**Solutions**:
1. Use primary for read-after-write operations
2. Implement retry logic with primary fallback
3. Monitor replica lag
4. Consider using primary for critical reads

## Monitoring

### Key Metrics

Monitor these metrics in CloudWatch:

- **ReplicaLag**: Should be < 1 second
- **DatabaseConnections**: Monitor connection usage
- **CPUUtilization**: Should be < 80%
- **ReadLatency**: Monitor read performance
- **ReadThroughput**: Monitor read volume

### Alerts

CloudWatch alarms are configured for:

- Replica lag > 1 second
- CPU utilization > 80%
- Connection count > 80% of max

## Related Documentation

- [Django integration](../backend/infrastructure/django-integration.md)
- [Database caching](./database-cache.md)
- [Search and indexing architecture](./search.md)
- [Connection pooling](../../apps/backend/infrastructure/connection_pool.py)
- [RDS Terraform module](../../infra/terraform/modules/rds/README.md)

## Support

For issues or questions:
1. Check CloudWatch metrics for replica lag
2. Verify security group rules
3. Test connectivity from application servers
4. Review application logs for database errors
5. Check connection pool statistics
