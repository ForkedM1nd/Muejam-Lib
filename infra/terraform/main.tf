# MueJam Library Infrastructure - Main Configuration
# This file defines the core infrastructure for production deployment

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  # Backend configuration for state management
  # Uncomment and configure for production use
  # backend "s3" {
  #   bucket         = "muejam-terraform-state"
  #   key            = "production/terraform.tfstate"
  #   region         = "us-east-1"
  #   encrypt        = true
  #   dynamodb_table = "muejam-terraform-locks"
  # }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "MueJam Library"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# VPC and Networking
module "networking" {
  source = "./modules/networking"
  
  environment         = var.environment
  vpc_cidr            = var.vpc_cidr
  availability_zones  = var.availability_zones
  public_subnet_cidrs = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
}

# Application Load Balancer
module "alb" {
  source = "./modules/alb"
  
  environment        = var.environment
  vpc_id             = module.networking.vpc_id
  public_subnet_ids  = module.networking.public_subnet_ids
  certificate_arn    = var.ssl_certificate_arn
  health_check_path  = "/health"
}

# Auto Scaling Group
module "asg" {
  source = "./modules/asg"
  
  environment            = var.environment
  vpc_id                 = module.networking.vpc_id
  private_subnet_ids     = module.networking.private_subnet_ids
  target_group_arn       = module.alb.target_group_arn
  alb_security_group_id  = module.alb.alb_security_group_id
  ami_id                 = var.app_ami_id
  instance_type          = var.instance_type
  min_size               = var.asg_min_size
  max_size               = var.asg_max_size
  desired_capacity       = var.asg_desired_capacity
  key_name               = var.ec2_key_name
}

# RDS PostgreSQL with Read Replicas
module "rds" {
  source = "./modules/rds"
  
  environment            = var.environment
  vpc_id                 = module.networking.vpc_id
  private_subnet_ids     = module.networking.private_subnet_ids
  app_security_group_id  = module.asg.app_security_group_id
  
  # Database configuration
  database_name          = var.db_name
  master_username        = var.db_master_username
  master_password        = var.db_master_password
  postgres_version       = var.db_postgres_version
  
  # Instance configuration
  db_instance_class      = var.db_instance_class
  replica_instance_class = var.db_replica_instance_class
  allocated_storage      = var.db_allocated_storage
  max_allocated_storage  = var.db_max_allocated_storage
  
  # Connection configuration
  max_connections        = var.db_max_connections
  
  # Backup configuration
  backup_retention_period = var.db_backup_retention_period
  backup_window          = var.db_backup_window
  maintenance_window     = var.db_maintenance_window
  
  # High availability
  multi_az               = var.db_multi_az
  
  # Read replicas
  create_read_replicas   = var.db_create_read_replicas
  replica_count          = var.db_replica_count
  
  # Deletion protection
  deletion_protection    = var.db_deletion_protection
  skip_final_snapshot    = var.db_skip_final_snapshot
}

# S3 Storage Buckets
module "s3" {
  source = "./modules/s3"
  
  environment                 = var.environment
  enable_versioning          = var.s3_enable_versioning
  allowed_origins            = var.s3_allowed_origins
  backup_retention_days      = var.s3_backup_retention_days
  bucket_size_alert_threshold = var.s3_bucket_size_alert_threshold
}

# ElastiCache Redis
module "elasticache" {
  source = "./modules/elasticache"
  
  environment            = var.environment
  vpc_id                 = module.networking.vpc_id
  private_subnet_ids     = module.networking.private_subnet_ids
  app_security_group_id  = module.asg.app_security_group_id
  
  # Redis configuration
  redis_version          = var.redis_version
  node_type              = var.redis_node_type
  num_cache_nodes        = var.redis_num_cache_nodes
  
  # High availability
  automatic_failover_enabled = var.redis_automatic_failover_enabled
  multi_az_enabled          = var.redis_multi_az_enabled
  cluster_mode_enabled      = var.redis_cluster_mode_enabled
  
  # Backup configuration
  snapshot_retention_limit = var.redis_snapshot_retention_limit
  snapshot_window         = var.redis_snapshot_window
  maintenance_window      = var.redis_maintenance_window
  
  # Security
  auth_token_enabled = var.redis_auth_token_enabled
  auth_token         = var.redis_auth_token
  
  # Apply changes
  apply_immediately = var.redis_apply_immediately
}
