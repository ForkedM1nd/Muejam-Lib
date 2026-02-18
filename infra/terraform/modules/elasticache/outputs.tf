# ElastiCache Module Outputs

output "redis_endpoint" {
  description = "Redis primary endpoint"
  value       = aws_elasticache_replication_group.main.primary_endpoint_address
}

output "redis_port" {
  description = "Redis port"
  value       = aws_elasticache_replication_group.main.port
}

output "redis_reader_endpoint" {
  description = "Redis reader endpoint"
  value       = aws_elasticache_replication_group.main.reader_endpoint_address
}

output "redis_configuration_endpoint" {
  description = "Redis configuration endpoint (for cluster mode)"
  value       = aws_elasticache_replication_group.main.configuration_endpoint_address
}

output "redis_id" {
  description = "Redis replication group ID"
  value       = aws_elasticache_replication_group.main.id
}

output "redis_arn" {
  description = "Redis replication group ARN"
  value       = aws_elasticache_replication_group.main.arn
}

output "redis_security_group_id" {
  description = "Redis security group ID"
  value       = aws_security_group.redis.id
}

output "redis_connection_string" {
  description = "Redis connection string"
  value       = "redis://${aws_elasticache_replication_group.main.primary_endpoint_address}:${aws_elasticache_replication_group.main.port}"
  sensitive   = true
}
