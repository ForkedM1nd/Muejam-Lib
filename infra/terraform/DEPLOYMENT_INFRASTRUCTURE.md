# Deployment Infrastructure

This document describes the complete Terraform infrastructure for deploying MueJam Library to AWS.

## Overview

The infrastructure is defined using Terraform and includes all AWS resources needed for production deployment:
- VPC and networking
- Application Load Balancer (ALB)
- Auto Scaling Group (ASG) with EC2 instances
- RDS PostgreSQL with read replicas
- ElastiCache Redis cluster
- S3 storage buckets
- CloudWatch monitoring and alarms

## Requirements

Implements:
- **Requirement 30.12**: Infrastructure as code (Terraform)
- **Requirement 30.6, 30.13**: Environment separation (dev, staging, prod)

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Internet Gateway                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────────┐
│                   Application Load Balancer                      │
│                  (Public Subnets, Multi-AZ)                      │
└────────────┬────────────────────────────────┬───────────────────┘
             │                                │
    ┌────────┴────────┐              ┌───────┴────────┐
    │   Django App    │              │   Django App   │
    │   Instance 1    │              │   Instance 2   │
    │  (Private AZ-A) │              │  (Private AZ-B)│
    └────────┬────────┘              └───────┬────────┘
             │                                │
             └────────────┬───────────────────┘
                          │
         ┌────────────────┼────────────────┬──────────────┬──────────────┐
         │                │                │              │              │
    ┌────┴─────┐    ┌────┴─────┐    ┌────┴─────┐   ┌───┴────┐    ┌───┴────┐
    │PostgreSQL│    │PostgreSQL│    │  Redis   │   │  S3    │    │  S3    │
    │ Primary  │    │  Replica │    │  Cluster │   │ Media  │    │ Static │
    │(Private) │    │(Private) │    │(Private) │   │        │    │        │
    └──────────┘    └──────────┘    └──────────┘   └────────┘    └────────┘
```

## Modules

### 1. Networking Module (`modules/networking/`)

Creates VPC, subnets, route tables, and internet gateway.

**Resources**:
- VPC with configurable CIDR block
- 3 public subnets (one per AZ)
- 3 private subnets (one per AZ)
- Internet Gateway
- NAT Gateways (one per AZ)
- Route tables

**Configuration**:
```hcl
module "networking" {
  source = "./modules/networking"
  
  environment          = "production"
  vpc_cidr             = "10.0.0.0/16"
  availability_zones   = ["us-east-1a", "us-east-1b", "us-east-1c"]
  public_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  private_subnet_cidrs = ["10.0.11.0/24", "10.0.12.0/24", "10.0.13.0/24"]
}
```

### 2. ALB Module (`modules/alb/`)

Creates Application Load Balancer with SSL termination.

**Resources**:
- Application Load Balancer
- Target Group
- HTTPS Listener (port 443)
- HTTP Listener (port 80, redirects to HTTPS)
- Security Group

**Configuration**:
```hcl
module "alb" {
  source = "./modules/alb"
  
  environment        = "production"
  vpc_id             = module.networking.vpc_id
  public_subnet_ids  = module.networking.public_subnet_ids
  certificate_arn    = "arn:aws:acm:us-east-1:123456789012:certificate/your-cert-id"
  health_check_path  = "/health"
}
```

### 3. ASG Module (`modules/asg/`)

Creates Auto Scaling Group with EC2 instances.

**Resources**:
- Launch Template
- Auto Scaling Group
- Auto Scaling Policies (CPU-based)
- CloudWatch Alarms
- Security Group

**Configuration**:
```hcl
module "asg" {
  source = "./modules/asg"
  
  environment            = "production"
  vpc_id                 = module.networking.vpc_id
  private_subnet_ids     = module.networking.private_subnet_ids
  target_group_arn       = module.alb.target_group_arn
  alb_security_group_id  = module.alb.alb_security_group_id
  ami_id                 = "ami-0c55b159cbfafe1f0"
  instance_type          = "t3.medium"
  min_size               = 2
  max_size               = 10
  desired_capacity       = 2
  key_name               = "muejam-production-key"
}
```

### 4. RDS Module (`modules/rds/`)

Creates PostgreSQL database with read replicas.

**Resources**:
- RDS Primary Instance
- RDS Read Replicas (1-2)
- DB Subnet Group
- DB Parameter Group
- Security Group
- CloudWatch Alarms
- IAM Role for Enhanced Monitoring

**Configuration**:
```hcl
module "rds" {
  source = "./modules/rds"
  
  environment            = "production"
  vpc_id                 = module.networking.vpc_id
  private_subnet_ids     = module.networking.private_subnet_ids
  app_security_group_id  = module.asg.app_security_group_id
  
  database_name          = "muejam"
  master_username        = "muejam_admin"
  master_password        = var.db_master_password
  postgres_version       = "15.4"
  
  db_instance_class      = "db.t3.medium"
  replica_instance_class = "db.t3.medium"
  allocated_storage      = 100
  max_allocated_storage  = 500
  
  create_read_replicas   = true
  replica_count          = 1
  multi_az               = true
}
```

### 5. S3 Module (`modules/s3/`)

Creates S3 buckets for storage.

**Resources**:
- Media Bucket (user uploads)
- Static Assets Bucket (CSS, JS, images)
- Backups Bucket (database backups)
- Bucket Policies
- Lifecycle Policies
- CloudWatch Alarms

**Configuration**:
```hcl
module "s3" {
  source = "./modules/s3"
  
  environment                 = "production"
  enable_versioning          = true
  allowed_origins            = ["https://muejam.com"]
  backup_retention_days      = 90
  bucket_size_alert_threshold = 107374182400  # 100 GB
}
```

### 6. ElastiCache Module (`modules/elasticache/`)

Creates Redis cluster for caching.

**Resources**:
- ElastiCache Replication Group
- Subnet Group
- Parameter Group
- Security Group
- CloudWatch Alarms

**Configuration**:
```hcl
module "elasticache" {
  source = "./modules/elasticache"
  
  environment            = "production"
  vpc_id                 = module.networking.vpc_id
  private_subnet_ids     = module.networking.private_subnet_ids
  app_security_group_id  = module.asg.app_security_group_id
  
  redis_version          = "7.0"
  node_type              = "cache.t3.medium"
  num_cache_nodes        = 2
  
  automatic_failover_enabled = true
  multi_az_enabled          = true
  auth_token_enabled        = true
  auth_token                = var.redis_auth_token
}
```

## Environment Separation

### Development Environment

```hcl
# dev.tfvars
environment = "dev"
instance_type = "t3.small"
asg_min_size = 1
asg_max_size = 2
db_instance_class = "db.t3.small"
db_create_read_replicas = false
db_multi_az = false
redis_node_type = "cache.t3.small"
redis_num_cache_nodes = 1
redis_multi_az_enabled = false
```

### Staging Environment

```hcl
# staging.tfvars
environment = "staging"
instance_type = "t3.medium"
asg_min_size = 2
asg_max_size = 5
db_instance_class = "db.t3.medium"
db_create_read_replicas = true
db_replica_count = 1
db_multi_az = true
redis_node_type = "cache.t3.medium"
redis_num_cache_nodes = 2
redis_multi_az_enabled = true
```

### Production Environment

```hcl
# production.tfvars
environment = "production"
instance_type = "t3.large"
asg_min_size = 2
asg_max_size = 10
db_instance_class = "db.r6g.xlarge"
db_replica_instance_class = "db.r6g.large"
db_create_read_replicas = true
db_replica_count = 2
db_multi_az = true
redis_node_type = "cache.r6g.large"
redis_num_cache_nodes = 3
redis_multi_az_enabled = true
```

## Deployment

### Prerequisites

1. **Install Terraform**:
   ```bash
   # macOS
   brew install terraform
   
   # Linux
   wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
   unzip terraform_1.6.0_linux_amd64.zip
   sudo mv terraform /usr/local/bin/
   ```

2. **Configure AWS Credentials**:
   ```bash
   aws configure
   # Enter AWS Access Key ID
   # Enter AWS Secret Access Key
   # Enter Default region (e.g., us-east-1)
   ```

3. **Create SSL Certificate**:
   ```bash
   # Request certificate in AWS Certificate Manager
   aws acm request-certificate \
     --domain-name muejam.com \
     --subject-alternative-names www.muejam.com \
     --validation-method DNS
   ```

4. **Create EC2 Key Pair**:
   ```bash
   aws ec2 create-key-pair \
     --key-name muejam-production-key \
     --query 'KeyMaterial' \
     --output text > muejam-production-key.pem
   chmod 400 muejam-production-key.pem
   ```

### Initial Deployment

1. **Initialize Terraform**:
   ```bash
   cd infra/terraform
   terraform init
   ```

2. **Create terraform.tfvars**:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your values
   ```

3. **Plan Deployment**:
   ```bash
   terraform plan -out=tfplan
   ```

4. **Apply Deployment**:
   ```bash
   terraform apply tfplan
   ```

5. **Get Outputs**:
   ```bash
   terraform output
   ```

### Environment-Specific Deployment

```bash
# Deploy to development
terraform apply -var-file="dev.tfvars"

# Deploy to staging
terraform apply -var-file="staging.tfvars"

# Deploy to production
terraform apply -var-file="production.tfvars"
```

## State Management

### Remote State (Recommended for Production)

```hcl
# backend.tf
terraform {
  backend "s3" {
    bucket         = "muejam-terraform-state"
    key            = "production/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "muejam-terraform-locks"
  }
}
```

### Create State Backend

```bash
# Create S3 bucket for state
aws s3 mb s3://muejam-terraform-state --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket muejam-terraform-state \
  --versioning-configuration Status=Enabled

# Create DynamoDB table for locking
aws dynamodb create-table \
  --table-name muejam-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

## Outputs

After deployment, Terraform provides these outputs:

```bash
# Network
vpc_id                    = "vpc-xxxxx"

# Load Balancer
alb_dns_name             = "muejam-alb-xxxxx.us-east-1.elb.amazonaws.com"
alb_zone_id              = "Z35SXDOTRQ7X7K"

# Auto Scaling
asg_name                 = "production-muejam-asg"

# Database
db_primary_endpoint      = "production-muejam-db-primary.xxxxx.us-east-1.rds.amazonaws.com:5432"
db_replica_1_endpoint    = "production-muejam-db-replica-1.xxxxx.us-east-1.rds.amazonaws.com:5432"

# Redis
redis_endpoint           = "production-muejam-redis.xxxxx.cache.amazonaws.com:6379"

# S3
s3_media_bucket_id       = "production-muejam-media"
s3_static_bucket_id      = "production-muejam-static"
s3_backups_bucket_id     = "production-muejam-backups"
```

## Cost Estimation

### Development Environment

- EC2 (1x t3.small): ~$15/month
- RDS (1x db.t3.small): ~$25/month
- ElastiCache (1x cache.t3.small): ~$15/month
- S3: ~$5/month
- **Total**: ~$60/month

### Staging Environment

- EC2 (2x t3.medium): ~$60/month
- RDS (1x db.t3.medium + 1 replica): ~$100/month
- ElastiCache (2x cache.t3.medium): ~$60/month
- S3: ~$10/month
- **Total**: ~$230/month

### Production Environment

- EC2 (2-10x t3.large): ~$120-600/month
- RDS (1x db.r6g.xlarge + 2 replicas): ~$600/month
- ElastiCache (3x cache.r6g.large): ~$300/month
- S3: ~$50/month
- ALB: ~$20/month
- Data Transfer: ~$100/month
- **Total**: ~$1,190-1,670/month

## Monitoring

### CloudWatch Alarms

The infrastructure includes CloudWatch alarms for:

**ALB**:
- Unhealthy target count
- High response time

**ASG**:
- CPU utilization > 70%

**RDS**:
- CPU utilization > 80%
- Database connections > 80%
- Replica lag > 1 second

**ElastiCache**:
- CPU utilization > 75%
- Memory usage > 80%
- Evictions > 1000

**S3**:
- Bucket size > threshold

### Viewing Metrics

```bash
# View ALB metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApplicationELB \
  --metric-name TargetResponseTime \
  --dimensions Name=LoadBalancer,Value=app/production-muejam-alb/xxxxx \
  --start-time 2026-02-17T00:00:00Z \
  --end-time 2026-02-18T00:00:00Z \
  --period 3600 \
  --statistics Average

# View RDS metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name CPUUtilization \
  --dimensions Name=DBInstanceIdentifier,Value=production-muejam-db-primary \
  --start-time 2026-02-17T00:00:00Z \
  --end-time 2026-02-18T00:00:00Z \
  --period 3600 \
  --statistics Average
```

## Maintenance

### Updating Infrastructure

```bash
# Update Terraform modules
terraform get -update

# Plan changes
terraform plan -out=tfplan

# Apply changes
terraform apply tfplan
```

### Scaling

**Vertical Scaling** (increase instance size):
```hcl
# Update variables
instance_type = "t3.xlarge"
db_instance_class = "db.r6g.2xlarge"
redis_node_type = "cache.r6g.xlarge"

# Apply changes
terraform apply
```

**Horizontal Scaling** (increase instance count):
```hcl
# Update variables
asg_max_size = 20
db_replica_count = 3
redis_num_cache_nodes = 4

# Apply changes
terraform apply
```

### Disaster Recovery

**Backup State**:
```bash
# Download current state
terraform state pull > terraform.tfstate.backup

# Upload to S3
aws s3 cp terraform.tfstate.backup s3://muejam-terraform-state/backups/
```

**Restore from Backup**:
```bash
# Download backup
aws s3 cp s3://muejam-terraform-state/backups/terraform.tfstate.backup .

# Push to Terraform
terraform state push terraform.tfstate.backup
```

## Troubleshooting

### Common Issues

**1. State Lock Error**:
```bash
# Force unlock (use with caution)
terraform force-unlock <lock-id>
```

**2. Resource Already Exists**:
```bash
# Import existing resource
terraform import aws_instance.app i-xxxxx
```

**3. Plan Shows Unexpected Changes**:
```bash
# Refresh state
terraform refresh

# Show current state
terraform show
```

## Security Best Practices

1. **Use Remote State**: Store state in S3 with encryption
2. **Enable State Locking**: Use DynamoDB for state locking
3. **Separate Environments**: Use different AWS accounts or VPCs
4. **Restrict Access**: Use IAM policies to limit who can apply changes
5. **Enable MFA**: Require MFA for production deployments
6. **Audit Changes**: Enable CloudTrail for all Terraform operations
7. **Encrypt Secrets**: Use AWS Secrets Manager for sensitive values
8. **Review Plans**: Always review `terraform plan` before applying

## Related Documentation

- [Auto Scaling](./AUTO_SCALING.md)
- [RDS Module](./modules/rds/README.md)
- [Database Configuration](../../apps/backend/infrastructure/README_DATABASE_CONFIG.md)
- [Read Replicas](../../apps/backend/infrastructure/README_READ_REPLICAS.md)

## Support

For issues or questions:
1. Review Terraform plan output
2. Check CloudWatch logs
3. Verify AWS credentials and permissions
4. Review module documentation
5. Check Terraform state for inconsistencies
