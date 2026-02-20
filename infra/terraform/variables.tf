# Variables for MueJam Library Infrastructure

variable "aws_region" {
  description = "AWS region for infrastructure deployment"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, staging, production)"
  type        = string
  default     = "production"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.11.0/24", "10.0.12.0/24", "10.0.13.0/24"]
}

variable "ssl_certificate_arn" {
  description = "ARN of SSL certificate for HTTPS"
  type        = string
}

variable "app_ami_id" {
  description = "AMI ID for application servers"
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type for application servers"
  type        = string
  default     = "t3.medium"
}

variable "asg_min_size" {
  description = "Minimum number of instances in auto-scaling group"
  type        = number
  default     = 2
}

variable "asg_max_size" {
  description = "Maximum number of instances in auto-scaling group"
  type        = number
  default     = 10
}

variable "asg_desired_capacity" {
  description = "Desired number of instances in auto-scaling group"
  type        = number
  default     = 2
}

variable "ec2_key_name" {
  description = "EC2 key pair name for SSH access"
  type        = string
}

# RDS Database Variables

variable "db_name" {
  description = "Name of the database to create"
  type        = string
  default     = "muejam"
}

variable "db_master_username" {
  description = "Master username for the database"
  type        = string
  default     = "muejam_admin"
  sensitive   = true
}

variable "db_master_password" {
  description = "Master password for the database"
  type        = string
  sensitive   = true
}

variable "db_postgres_version" {
  description = "PostgreSQL version"
  type        = string
  default     = "15.4"
}

variable "db_instance_class" {
  description = "Instance class for primary database"
  type        = string
  default     = "db.t3.medium"
}

variable "db_replica_instance_class" {
  description = "Instance class for read replicas"
  type        = string
  default     = "db.t3.medium"
}

variable "db_allocated_storage" {
  description = "Initial allocated storage in GB"
  type        = number
  default     = 100
}

variable "db_max_allocated_storage" {
  description = "Maximum allocated storage for autoscaling in GB"
  type        = number
  default     = 500
}

variable "db_max_connections" {
  description = "Maximum number of database connections"
  type        = string
  default     = "100"
}

variable "db_backup_retention_period" {
  description = "Number of days to retain backups"
  type        = number
  default     = 7
}

variable "db_backup_window" {
  description = "Preferred backup window (UTC)"
  type        = string
  default     = "03:00-04:00"
}

variable "db_maintenance_window" {
  description = "Preferred maintenance window (UTC)"
  type        = string
  default     = "sun:04:00-sun:05:00"
}

variable "db_multi_az" {
  description = "Enable Multi-AZ deployment for primary database"
  type        = bool
  default     = true
}

variable "db_create_read_replicas" {
  description = "Whether to create read replicas"
  type        = bool
  default     = true
}

variable "db_replica_count" {
  description = "Number of read replicas to create (1 or 2)"
  type        = number
  default     = 1
}

variable "db_deletion_protection" {
  description = "Enable deletion protection"
  type        = bool
  default     = true
}

variable "db_skip_final_snapshot" {
  description = "Skip final snapshot on deletion (not recommended for production)"
  type        = bool
  default     = false
}

# S3 Storage Variables

variable "s3_enable_versioning" {
  description = "Enable versioning for S3 buckets"
  type        = bool
  default     = true
}

variable "s3_allowed_origins" {
  description = "Allowed origins for CORS"
  type        = list(string)
  default     = ["*"]
}

variable "s3_backup_retention_days" {
  description = "Number of days to retain backups in S3"
  type        = number
  default     = 90
}

variable "s3_bucket_size_alert_threshold" {
  description = "Alert threshold for bucket size in bytes"
  type        = number
  default     = 107374182400 # 100 GB
}

# ElastiCache Redis Variables

variable "redis_version" {
  description = "Redis version"
  type        = string
  default     = "7.0"
}

variable "redis_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t3.medium"
}

variable "redis_num_cache_nodes" {
  description = "Number of cache nodes"
  type        = number
  default     = 2
}

variable "redis_automatic_failover_enabled" {
  description = "Enable automatic failover for Redis"
  type        = bool
  default     = true
}

variable "redis_multi_az_enabled" {
  description = "Enable Multi-AZ deployment for Redis"
  type        = bool
  default     = true
}

variable "redis_cluster_mode_enabled" {
  description = "Enable cluster mode for Redis"
  type        = bool
  default     = false
}

variable "redis_snapshot_retention_limit" {
  description = "Number of days to retain Redis snapshots"
  type        = number
  default     = 7
}

variable "redis_snapshot_window" {
  description = "Redis snapshot window (UTC)"
  type        = string
  default     = "03:00-05:00"
}

variable "redis_maintenance_window" {
  description = "Redis maintenance window (UTC)"
  type        = string
  default     = "sun:05:00-sun:07:00"
}

variable "redis_auth_token_enabled" {
  description = "Enable auth token for Redis"
  type        = bool
  default     = true
}

variable "redis_auth_token" {
  description = "Auth token for Redis (if enabled)"
  type        = string
  sensitive   = true
  default     = null
}

variable "redis_apply_immediately" {
  description = "Apply Redis changes immediately"
  type        = bool
  default     = false
}
