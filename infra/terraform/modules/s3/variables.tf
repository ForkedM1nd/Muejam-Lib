# S3 Module Variables

variable "environment" {
  description = "Environment name (dev, staging, production)"
  type        = string
}

variable "enable_versioning" {
  description = "Enable versioning for media bucket"
  type        = bool
  default     = true
}

variable "allowed_origins" {
  description = "Allowed origins for CORS"
  type        = list(string)
  default     = ["*"]
}

variable "backup_retention_days" {
  description = "Number of days to retain backups"
  type        = number
  default     = 90
}

variable "bucket_size_alert_threshold" {
  description = "Alert threshold for bucket size in bytes"
  type        = number
  default     = 107374182400  # 100 GB
}
