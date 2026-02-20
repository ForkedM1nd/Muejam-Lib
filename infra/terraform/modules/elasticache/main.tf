# ElastiCache Redis Module
# Provides Redis cluster for caching, sessions, and rate limiting

# Subnet group for ElastiCache
resource "aws_elasticache_subnet_group" "main" {
  name       = "${var.environment}-muejam-redis-subnet-group"
  subnet_ids = var.private_subnet_ids

  tags = {
    Name        = "${var.environment}-muejam-redis-subnet-group"
    Environment = var.environment
  }
}

# Security group for ElastiCache
resource "aws_security_group" "redis" {
  name        = "${var.environment}-muejam-redis-sg"
  description = "Security group for ElastiCache Redis"
  vpc_id      = var.vpc_id

  # Allow Redis from application servers
  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [var.app_security_group_id]
    description     = "Redis from application servers"
  }

  # Allow all outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = {
    Name        = "${var.environment}-muejam-redis-sg"
    Environment = var.environment
  }
}

# Parameter group for Redis
resource "aws_elasticache_parameter_group" "main" {
  name   = "${var.environment}-muejam-redis-params"
  family = "redis7"

  # Enable cluster mode
  parameter {
    name  = "cluster-enabled"
    value = var.cluster_mode_enabled ? "yes" : "no"
  }

  # Set max memory policy
  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"
  }

  # Enable notifications
  parameter {
    name  = "notify-keyspace-events"
    value = "Ex"
  }

  tags = {
    Name        = "${var.environment}-muejam-redis-params"
    Environment = var.environment
  }
}

# ElastiCache Replication Group (Redis Cluster)
resource "aws_elasticache_replication_group" "main" {
  replication_group_id          = "${var.environment}-muejam-redis"
  replication_group_description = "Redis cluster for MueJam Library"

  # Engine configuration
  engine               = "redis"
  engine_version       = var.redis_version
  port                 = 6379
  parameter_group_name = aws_elasticache_parameter_group.main.name

  # Node configuration
  node_type          = var.node_type
  num_cache_clusters = var.num_cache_nodes

  # Network configuration
  subnet_group_name  = aws_elasticache_subnet_group.main.name
  security_group_ids = [aws_security_group.redis.id]

  # High availability
  automatic_failover_enabled = var.automatic_failover_enabled
  multi_az_enabled           = var.multi_az_enabled

  # Backup configuration
  snapshot_retention_limit = var.snapshot_retention_limit
  snapshot_window          = var.snapshot_window

  # Maintenance
  maintenance_window = var.maintenance_window

  # Encryption
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token_enabled         = var.auth_token_enabled
  auth_token                 = var.auth_token_enabled ? var.auth_token : null

  # Notifications
  notification_topic_arn = var.sns_topic_arn

  # Auto minor version upgrade
  auto_minor_version_upgrade = true

  # Apply changes immediately (set to false for production)
  apply_immediately = var.apply_immediately

  tags = {
    Name        = "${var.environment}-muejam-redis"
    Environment = var.environment
  }
}

# CloudWatch alarms for Redis
resource "aws_cloudwatch_metric_alarm" "redis_cpu" {
  alarm_name          = "${var.environment}-muejam-redis-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ElastiCache"
  period              = "300"
  statistic           = "Average"
  threshold           = "75"
  alarm_description   = "This metric monitors Redis CPU utilization"

  dimensions = {
    ReplicationGroupId = aws_elasticache_replication_group.main.id
  }

  tags = {
    Name        = "${var.environment}-muejam-redis-cpu"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_metric_alarm" "redis_memory" {
  alarm_name          = "${var.environment}-muejam-redis-memory"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "DatabaseMemoryUsagePercentage"
  namespace           = "AWS/ElastiCache"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors Redis memory usage"

  dimensions = {
    ReplicationGroupId = aws_elasticache_replication_group.main.id
  }

  tags = {
    Name        = "${var.environment}-muejam-redis-memory"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_metric_alarm" "redis_evictions" {
  alarm_name          = "${var.environment}-muejam-redis-evictions"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Evictions"
  namespace           = "AWS/ElastiCache"
  period              = "300"
  statistic           = "Sum"
  threshold           = "1000"
  alarm_description   = "This metric monitors Redis evictions"

  dimensions = {
    ReplicationGroupId = aws_elasticache_replication_group.main.id
  }

  tags = {
    Name        = "${var.environment}-muejam-redis-evictions"
    Environment = var.environment
  }
}
