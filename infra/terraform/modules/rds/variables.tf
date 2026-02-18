# RDS Module Variables

variable "environment" {
  description = "Environment name (dev, staging, production)"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID where RDS will be deployed"
  type        = string
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs for RDS"
  type        = list(string)
}

variable "app_security_group_id" {
  description = "Security group ID of application servers"
  type        = string
}

# Database Configuration
variable "database_name" {
  description = "Name of the database to create"
  type        = string
  default     = "muejam"
}

variable "master_username" {
  description = "Master username for the database"
  type        = string
  default     = "muejam_admin"
  sensitive   = true
}

variable "master_password" {
  description = "Master password for the database"
  type        = string
  sensitive   = true
}

variable "postgres_version" {
  description = "PostgreSQL version"
  type        = string
  default     = "15.4"
}

# Instance Configuration
variable "db_instance_class" {
  description = "Instance class for primary database"
  type        = string
  default     = "db.t3.medium"
}

variable "replica_instance_class" {
  description = "Instance class for read replicas"
  type        = string
  default     = "db.t3.medium"
}

variable "allocated_storage" {
  description = "Initial allocated storage in GB"
  type        = number
  default     = 100
}

variable "max_allocated_storage" {
  description = "Maximum allocated storage for autoscaling in GB"
  type        = number
  default     = 500
}

# Connection Configuration
variable "max_connections" {
  description = "Maximum number of database connections"
  type        = string
  default     = "100"
}

# Backup Configuration
variable "backup_retention_period" {
  description = "Number of days to retain backups"
  type        = number
  default     = 7
}

variable "backup_window" {
  description = "Preferred backup window (UTC)"
  type        = string
  default     = "03:00-04:00"
}

variable "maintenance_window" {
  description = "Preferred maintenance window (UTC)"
  type        = string
  default     = "sun:04:00-sun:05:00"
}

# High Availability
variable "multi_az" {
  description = "Enable Multi-AZ deployment for primary database"
  type        = bool
  default     = true
}

# Read Replicas
variable "create_read_replicas" {
  description = "Whether to create read replicas"
  type        = bool
  default     = true
}

variable "replica_count" {
  description = "Number of read replicas to create (1 or 2)"
  type        = number
  default     = 1
  
  validation {
    condition     = var.replica_count >= 1 && var.replica_count <= 2
    error_message = "Replica count must be 1 or 2"
  }
}

# Deletion Protection
variable "deletion_protection" {
  description = "Enable deletion protection"
  type        = bool
  default     = true
}

variable "skip_final_snapshot" {
  description = "Skip final snapshot on deletion (not recommended for production)"
  type        = bool
  default     = false
}
