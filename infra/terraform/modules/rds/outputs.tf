# RDS Module Outputs

# Primary Database
output "primary_endpoint" {
  description = "Primary database endpoint"
  value       = aws_db_instance.primary.endpoint
}

output "primary_address" {
  description = "Primary database address"
  value       = aws_db_instance.primary.address
}

output "primary_port" {
  description = "Primary database port"
  value       = aws_db_instance.primary.port
}

output "primary_id" {
  description = "Primary database instance ID"
  value       = aws_db_instance.primary.id
}

output "primary_arn" {
  description = "Primary database ARN"
  value       = aws_db_instance.primary.arn
}

# Read Replica 1
output "replica_1_endpoint" {
  description = "Read replica 1 endpoint"
  value       = var.create_read_replicas ? aws_db_instance.read_replica_1[0].endpoint : null
}

output "replica_1_address" {
  description = "Read replica 1 address"
  value       = var.create_read_replicas ? aws_db_instance.read_replica_1[0].address : null
}

# Read Replica 2
output "replica_2_endpoint" {
  description = "Read replica 2 endpoint"
  value       = var.create_read_replicas && var.replica_count >= 2 ? aws_db_instance.read_replica_2[0].endpoint : null
}

output "replica_2_address" {
  description = "Read replica 2 address"
  value       = var.create_read_replicas && var.replica_count >= 2 ? aws_db_instance.read_replica_2[0].address : null
}

# Database Configuration
output "database_name" {
  description = "Database name"
  value       = aws_db_instance.primary.db_name
}

output "master_username" {
  description = "Master username"
  value       = aws_db_instance.primary.username
  sensitive   = true
}

# Security Group
output "rds_security_group_id" {
  description = "RDS security group ID"
  value       = aws_security_group.rds.id
}

# Monitoring
output "monitoring_role_arn" {
  description = "IAM role ARN for RDS monitoring"
  value       = aws_iam_role.rds_monitoring.arn
}

# Connection String Examples
output "primary_connection_string" {
  description = "Primary database connection string (without password)"
  value       = "postgresql://${aws_db_instance.primary.username}@${aws_db_instance.primary.endpoint}/${aws_db_instance.primary.db_name}"
  sensitive   = true
}

output "replica_1_connection_string" {
  description = "Read replica 1 connection string (without password)"
  value       = var.create_read_replicas ? "postgresql://${aws_db_instance.primary.username}@${aws_db_instance.read_replica_1[0].endpoint}/${aws_db_instance.primary.db_name}" : null
  sensitive   = true
}
