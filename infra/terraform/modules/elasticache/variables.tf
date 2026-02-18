# ElastiCache Module Variables

variable "environment" {
  description = "Environment name (dev, staging, production)"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID where ElastiCache will be deployed"
  type        = string
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs for ElastiCache"
  type        = list(string)
}

variable "app_security_group_id" {
  description = "Security group ID of application servers"
  type        = string
}

# Redis Configuration
variable "redis_version" {
  description = "Redis version"
  type        = string
  default     = "7.0"
}

variable "node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t3.medium"
}

variable "num_cache_nodes" {
  description = "Number of cache nodes"
  type        = number
  default     = 2
}

# High Availability
variable "automatic_failover_enabled" {
  description = "Enable automatic failover"
  type        = bool
  default     = true
}

variable "multi_az_enabled" {
  description = "Enable Multi-AZ deployment"
  type        = bool
  default     = true
}

# Cluster Mode
variable "cluster_mode_enabled" {
  description = "Enable cluster mode"
  type        = bool
  default     = false
}

# Backup Configuration
variable "snapshot_retention_limit" {
  description = "Number of days to retain snapshots"
  type        = number
  default     = 7
}

variable "snapshot_window" {
  description = "Snapshot window (UTC)"
  type        = string
  default     = "03:00-05:00"
}

# Maintenance
variable "maintenance_window" {
  description = "Maintenance window (UTC)"
  type        = string
  default     = "sun:05:00-sun:07:00"
}

# Security
variable "auth_token_enabled" {
  description = "Enable auth token (password)"
  type        = bool
  default     = true
}

variable "auth_token" {
  description = "Auth token for Redis (if enabled)"
  type        = string
  sensitive   = true
  default     = null
}

# Notifications
variable "sns_topic_arn" {
  description = "SNS topic ARN for notifications"
  type        = string
  default     = null
}

# Apply Changes
variable "apply_immediately" {
  description = "Apply changes immediately (use false for production)"
  type        = bool
  default     = false
}
