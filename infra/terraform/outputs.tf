# Outputs for MueJam Library Infrastructure

output "vpc_id" {
  description = "ID of the VPC"
  value       = module.networking.vpc_id
}

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = module.alb.alb_dns_name
}

output "alb_zone_id" {
  description = "Zone ID of the Application Load Balancer"
  value       = module.alb.alb_zone_id
}

output "alb_arn" {
  description = "ARN of the Application Load Balancer"
  value       = module.alb.alb_arn
}

output "target_group_arn" {
  description = "ARN of the target group"
  value       = module.alb.target_group_arn
}

output "asg_name" {
  description = "Name of the auto-scaling group"
  value       = module.asg.asg_name
}

output "asg_arn" {
  description = "ARN of the auto-scaling group"
  value       = module.asg.asg_arn
}

# RDS Database Outputs

output "db_primary_endpoint" {
  description = "Primary database endpoint"
  value       = module.rds.primary_endpoint
}

output "db_primary_address" {
  description = "Primary database address"
  value       = module.rds.primary_address
}

output "db_replica_1_endpoint" {
  description = "Read replica 1 endpoint"
  value       = module.rds.replica_1_endpoint
}

output "db_replica_1_address" {
  description = "Read replica 1 address"
  value       = module.rds.replica_1_address
}

output "db_replica_2_endpoint" {
  description = "Read replica 2 endpoint"
  value       = module.rds.replica_2_endpoint
}

output "db_database_name" {
  description = "Database name"
  value       = module.rds.database_name
}

output "db_master_username" {
  description = "Master username"
  value       = module.rds.master_username
  sensitive   = true
}

output "db_primary_connection_string" {
  description = "Primary database connection string (without password)"
  value       = module.rds.primary_connection_string
  sensitive   = true
}

output "db_replica_1_connection_string" {
  description = "Read replica 1 connection string (without password)"
  value       = module.rds.replica_1_connection_string
  sensitive   = true
}

# S3 Storage Outputs

output "s3_media_bucket_id" {
  description = "ID of the media bucket"
  value       = module.s3.media_bucket_id
}

output "s3_media_bucket_arn" {
  description = "ARN of the media bucket"
  value       = module.s3.media_bucket_arn
}

output "s3_static_bucket_id" {
  description = "ID of the static assets bucket"
  value       = module.s3.static_bucket_id
}

output "s3_backups_bucket_id" {
  description = "ID of the backups bucket"
  value       = module.s3.backups_bucket_id
}

# ElastiCache Redis Outputs

output "redis_endpoint" {
  description = "Redis primary endpoint"
  value       = module.elasticache.redis_endpoint
}

output "redis_port" {
  description = "Redis port"
  value       = module.elasticache.redis_port
}

output "redis_reader_endpoint" {
  description = "Redis reader endpoint"
  value       = module.elasticache.redis_reader_endpoint
}

output "redis_connection_string" {
  description = "Redis connection string"
  value       = module.elasticache.redis_connection_string
  sensitive   = true
}
