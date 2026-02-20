# RDS PostgreSQL with Read Replicas Module

This Terraform module creates an Amazon RDS PostgreSQL database with read replicas for high availability and read scalability.

## Requirements

Implements:
- **Requirement 33.5**: Use database read replicas for read-heavy operations

## Features

- PostgreSQL 15.4 with optimized parameters
- Multi-AZ deployment for high availability
- Up to 2 read replicas for read scalability
- Automated backups with configurable retention
- Enhanced monitoring with CloudWatch
- Performance Insights enabled
- Encryption at rest
- Security group with restricted access
- CloudWatch alarms for monitoring

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Tier                          │
│  (Auto Scaling Group with EC2 instances)                    │
└─────────────────────────────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
                ▼                       ▼
┌───────────────────────┐   ┌───────────────────────┐
│   Primary Database    │   │   Read Replicas       │
│   (Write Operations)  │   │   (Read Operations)   │
│   Multi-AZ            │   │   Replica 1, 2        │
│   db.t3.medium        │   │   db.t3.medium        │
└───────────────────────┘   └───────────────────────┘
```

## Usage

### Basic Configuration

```hcl
module "rds" {
  source = "./modules/rds"
  
  environment            = "production"
  vpc_id                 = module.networking.vpc_id
  private_subnet_ids     = module.networking.private_subnet_ids
  app_security_group_id  = module.asg.app_security_group_id
  
  # Database configuration
  database_name          = "muejam"
  master_username        = "muejam_admin"
  master_password        = var.db_master_password
  
  # Enable read replicas
  create_read_replicas   = true
  replica_count          = 1
}
```

### Production Configuration

```hcl
module "rds" {
  source = "./modules/rds"
  
  environment            = "production"
  vpc_id                 = module.networking.vpc_id
  private_subnet_ids     = module.networking.private_subnet_ids
  app_security_group_id  = module.asg.app_security_group_id
  
  # Database configuration
  database_name          = "muejam"
  master_username        = "muejam_admin"
  master_password        = var.db_master_password
  postgres_version       = "15.4"
  
  # Instance configuration
  db_instance_class      = "db.r6g.xlarge"
  replica_instance_class = "db.r6g.large"
  allocated_storage      = 500
  max_allocated_storage  = 2000
  
  # Connection configuration
  max_connections        = "200"
  
  # Backup configuration
  backup_retention_period = 30
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  # High availability
  multi_az               = true
  
  # Read replicas
  create_read_replicas   = true
  replica_count          = 2
  
  # Deletion protection
  deletion_protection    = true
  skip_final_snapshot    = false
}
```

## Variables

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|----------|
| environment | Environment name | string | - | yes |
| vpc_id | VPC ID | string | - | yes |
| private_subnet_ids | Private subnet IDs | list(string) | - | yes |
| app_security_group_id | Application security group ID | string | - | yes |
| database_name | Database name | string | "muejam" | no |
| master_username | Master username | string | "muejam_admin" | no |
| master_password | Master password | string | - | yes |
| postgres_version | PostgreSQL version | string | "15.4" | no |
| db_instance_class | Primary instance class | string | "db.t3.medium" | no |
| replica_instance_class | Replica instance class | string | "db.t3.medium" | no |
| allocated_storage | Initial storage (GB) | number | 100 | no |
| max_allocated_storage | Max storage (GB) | number | 500 | no |
| max_connections | Max connections | string | "100" | no |
| backup_retention_period | Backup retention (days) | number | 7 | no |
| backup_window | Backup window (UTC) | string | "03:00-04:00" | no |
| maintenance_window | Maintenance window (UTC) | string | "sun:04:00-sun:05:00" | no |
| multi_az | Enable Multi-AZ | bool | true | no |
| create_read_replicas | Create read replicas | bool | true | no |
| replica_count | Number of replicas (1-2) | number | 1 | no |
| deletion_protection | Enable deletion protection | bool | true | no |
| skip_final_snapshot | Skip final snapshot | bool | false | no |

## Outputs

| Name | Description |
|------|-------------|
| primary_endpoint | Primary database endpoint |
| primary_address | Primary database address |
| primary_port | Primary database port |
| replica_1_endpoint | Read replica 1 endpoint |
| replica_1_address | Read replica 1 address |
| replica_2_endpoint | Read replica 2 endpoint |
| replica_2_address | Read replica 2 address |
| database_name | Database name |
| master_username | Master username |
| rds_security_group_id | RDS security group ID |
| primary_connection_string | Primary connection string |
| replica_1_connection_string | Replica 1 connection string |

## Database Configuration

### PostgreSQL Parameters

The module configures PostgreSQL with optimized parameters:

- **max_connections**: Configurable (default: 100)
- **statement_timeout**: 30 seconds
- **log_min_duration_statement**: 100ms (logs slow queries)
- **shared_buffers**: 25% of instance memory
- **effective_cache_size**: 75% of instance memory
- **work_mem**: 16MB
- **maintenance_work_mem**: 512MB

### Monitoring

The module enables:

- **Enhanced Monitoring**: 60-second granularity
- **Performance Insights**: 7-day retention
- **CloudWatch Logs**: PostgreSQL logs and upgrade logs
- **CloudWatch Alarms**:
  - CPU utilization > 80%
  - Database connections > 80% of max
  - Replica lag > 1 second

## Application Integration

### Django Configuration

Update your Django settings to use the RDS endpoints:

```python
# settings.py

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'muejam',
        'USER': 'muejam_admin',
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),  # Primary endpoint
        'PORT': '5432',
        'CONN_MAX_AGE': 0,
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c statement_timeout=30000',
        },
    },
    'read_replica': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'muejam',
        'USER': 'muejam_admin',
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_READ_HOST'),  # Replica endpoint
        'PORT': '5432',
        'CONN_MAX_AGE': 0,
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c statement_timeout=30000',
        },
    }
}

# Database router for read/write splitting
DATABASE_ROUTERS = ['infrastructure.database_config.ReadWriteRouter']
```

### Environment Variables

Set these environment variables in your application:

```bash
# Primary database (write operations)
DB_HOST=<primary_endpoint>
DB_NAME=muejam
DB_USER=muejam_admin
DB_PASSWORD=<master_password>
DB_PORT=5432

# Read replica (read operations)
USE_READ_REPLICA=true
DB_READ_HOST=<replica_1_endpoint>
DB_READ_PORT=5432

# Connection pool configuration
DB_POOL_MIN_CONNECTIONS=10
DB_POOL_MAX_CONNECTIONS=50
```

### Read/Write Splitting

The application uses the `ReadWriteRouter` from `database_config.py` to automatically route:

- **Write operations** → Primary database
- **Read operations** → Read replica

Example:

```python
# Write operation - goes to primary
user = User.objects.create(username='john')

# Read operation - goes to read replica
users = User.objects.filter(active=True)

# Explicit routing
User.objects.using('default').create(username='jane')  # Primary
User.objects.using('read_replica').filter(active=True)  # Replica
```

## Deployment

### Initial Deployment

```bash
# Initialize Terraform
terraform init

# Plan the deployment
terraform plan -var="db_master_password=<secure_password>"

# Apply the configuration
terraform apply -var="db_master_password=<secure_password>"
```

### Get Database Endpoints

```bash
# Get primary endpoint
terraform output db_primary_endpoint

# Get read replica endpoint
terraform output db_replica_1_endpoint

# Get connection strings
terraform output -json | jq '.db_primary_connection_string.value'
```

## Monitoring

### CloudWatch Metrics

Monitor these key metrics:

- **CPUUtilization**: Should stay below 80%
- **DatabaseConnections**: Should stay below 80% of max_connections
- **ReplicaLag**: Should stay below 1 second
- **ReadLatency**: Monitor read performance
- **WriteLatency**: Monitor write performance
- **FreeStorageSpace**: Monitor available storage

### Performance Insights

Access Performance Insights in the AWS Console to:

- Identify slow queries
- Analyze query patterns
- Optimize database performance

### Slow Query Logs

Queries exceeding 100ms are logged to CloudWatch Logs. Review these logs to identify optimization opportunities.

## Backup and Recovery

### Automated Backups

- **Retention**: 7 days (configurable)
- **Backup Window**: 03:00-04:00 UTC (configurable)
- **Point-in-Time Recovery**: Enabled

### Manual Snapshots

Create manual snapshots for important milestones:

```bash
aws rds create-db-snapshot \
  --db-instance-identifier production-muejam-db-primary \
  --db-snapshot-identifier production-muejam-snapshot-$(date +%Y%m%d)
```

### Restore from Snapshot

```bash
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier production-muejam-db-restored \
  --db-snapshot-identifier production-muejam-snapshot-20260218
```

## Scaling

### Vertical Scaling

Update instance class:

```hcl
db_instance_class = "db.r6g.2xlarge"
```

Apply changes:

```bash
terraform apply
```

### Horizontal Scaling

Add more read replicas:

```hcl
replica_count = 2
```

Apply changes:

```bash
terraform apply
```

### Storage Scaling

Storage auto-scales up to `max_allocated_storage`. To increase the limit:

```hcl
max_allocated_storage = 1000
```

## Security

### Network Security

- Database is deployed in private subnets
- Security group restricts access to application servers only
- No public access

### Encryption

- **At Rest**: Enabled using AWS KMS
- **In Transit**: SSL/TLS enforced

### Access Control

- Master credentials stored securely
- Use IAM database authentication for enhanced security (optional)

## Cost Optimization

### Development Environment

```hcl
db_instance_class      = "db.t3.small"
replica_instance_class = "db.t3.small"
create_read_replicas   = false
multi_az               = false
backup_retention_period = 1
```

### Production Environment

```hcl
db_instance_class      = "db.r6g.xlarge"
replica_instance_class = "db.r6g.large"
create_read_replicas   = true
replica_count          = 2
multi_az               = true
backup_retention_period = 30
```

## Troubleshooting

### High CPU Usage

1. Check Performance Insights for slow queries
2. Review CloudWatch Logs for query patterns
3. Optimize queries or add indexes
4. Consider vertical scaling

### High Connection Count

1. Check application connection pooling configuration
2. Increase `max_connections` parameter
3. Consider vertical scaling

### High Replica Lag

1. Check primary database load
2. Verify network connectivity
3. Consider upgrading replica instance class
4. Review write-heavy operations

## Related Documentation

- [Database and cache architecture](../../../../docs/architecture/database-cache.md)
- [Search and indexing architecture](../../../../docs/architecture/search.md)
- [Read replicas architecture](../../../../docs/architecture/read-replicas.md)
- [Connection pooling implementation](../../../../apps/backend/infrastructure/connection_pool.py)

## Support

For issues or questions:
1. Check CloudWatch metrics and alarms
2. Review Performance Insights
3. Check CloudWatch Logs for errors
4. Verify security group rules
5. Test connectivity from application servers
