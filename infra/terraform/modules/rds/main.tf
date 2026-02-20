# RDS PostgreSQL with Read Replicas Module
# Implements Requirement 33.5: Database read replicas for read-heavy operations

# DB Subnet Group
resource "aws_db_subnet_group" "main" {
  name       = "${var.environment}-muejam-db-subnet-group"
  subnet_ids = var.private_subnet_ids

  tags = {
    Name        = "${var.environment}-muejam-db-subnet-group"
    Environment = var.environment
  }
}

# Security Group for RDS
resource "aws_security_group" "rds" {
  name        = "${var.environment}-muejam-rds-sg"
  description = "Security group for RDS PostgreSQL"
  vpc_id      = var.vpc_id

  # Allow PostgreSQL from application servers
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [var.app_security_group_id]
    description     = "PostgreSQL from application servers"
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
    Name        = "${var.environment}-muejam-rds-sg"
    Environment = var.environment
  }
}

# Parameter Group for PostgreSQL optimization
resource "aws_db_parameter_group" "main" {
  name   = "${var.environment}-muejam-postgres-params"
  family = "postgres15"

  # Connection pooling parameters
  parameter {
    name  = "max_connections"
    value = var.max_connections
  }

  # Query timeout (30 seconds)
  parameter {
    name  = "statement_timeout"
    value = "30000"
  }

  # Logging for slow queries
  parameter {
    name  = "log_min_duration_statement"
    value = "100" # Log queries > 100ms
  }

  # Enable query plan logging for slow queries
  parameter {
    name  = "log_statement"
    value = "mod" # Log all DDL and DML
  }

  # Shared buffers (25% of instance memory)
  parameter {
    name  = "shared_buffers"
    value = "{DBInstanceClassMemory/32768}"
  }

  # Effective cache size (75% of instance memory)
  parameter {
    name  = "effective_cache_size"
    value = "{DBInstanceClassMemory/10923}"
  }

  # Work memory for sorting and hashing
  parameter {
    name  = "work_mem"
    value = "16384" # 16MB
  }

  # Maintenance work memory
  parameter {
    name  = "maintenance_work_mem"
    value = "524288" # 512MB
  }

  tags = {
    Name        = "${var.environment}-muejam-postgres-params"
    Environment = var.environment
  }
}

# Primary RDS Instance
resource "aws_db_instance" "primary" {
  identifier     = "${var.environment}-muejam-db-primary"
  engine         = "postgres"
  engine_version = var.postgres_version

  # Instance configuration
  instance_class        = var.db_instance_class
  allocated_storage     = var.allocated_storage
  max_allocated_storage = var.max_allocated_storage
  storage_type          = "gp3"
  storage_encrypted     = true

  # Database configuration
  db_name  = var.database_name
  username = var.master_username
  password = var.master_password
  port     = 5432

  # Network configuration
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false

  # Parameter and option groups
  parameter_group_name = aws_db_parameter_group.main.name

  # Backup configuration
  backup_retention_period = var.backup_retention_period
  backup_window           = var.backup_window
  maintenance_window      = var.maintenance_window

  # High availability
  multi_az = var.multi_az

  # Monitoring
  enabled_cloudwatch_logs_exports       = ["postgresql", "upgrade"]
  monitoring_interval                   = 60
  monitoring_role_arn                   = aws_iam_role.rds_monitoring.arn
  performance_insights_enabled          = true
  performance_insights_retention_period = 7

  # Deletion protection
  deletion_protection       = var.deletion_protection
  skip_final_snapshot       = var.skip_final_snapshot
  final_snapshot_identifier = var.skip_final_snapshot ? null : "${var.environment}-muejam-db-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"

  # Auto minor version upgrade
  auto_minor_version_upgrade = true

  tags = {
    Name        = "${var.environment}-muejam-db-primary"
    Environment = var.environment
    Role        = "primary"
  }
}

# Read Replica 1
resource "aws_db_instance" "read_replica_1" {
  count = var.create_read_replicas ? 1 : 0

  identifier          = "${var.environment}-muejam-db-replica-1"
  replicate_source_db = aws_db_instance.primary.identifier
  instance_class      = var.replica_instance_class

  # Storage configuration (inherited from primary)
  storage_encrypted = true

  # Network configuration
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false

  # Parameter group
  parameter_group_name = aws_db_parameter_group.main.name

  # Monitoring
  enabled_cloudwatch_logs_exports       = ["postgresql"]
  monitoring_interval                   = 60
  monitoring_role_arn                   = aws_iam_role.rds_monitoring.arn
  performance_insights_enabled          = true
  performance_insights_retention_period = 7

  # Auto minor version upgrade
  auto_minor_version_upgrade = true

  # Deletion protection
  skip_final_snapshot = true

  tags = {
    Name        = "${var.environment}-muejam-db-replica-1"
    Environment = var.environment
    Role        = "read-replica"
  }
}

# Read Replica 2 (optional, for high-traffic scenarios)
resource "aws_db_instance" "read_replica_2" {
  count = var.create_read_replicas && var.replica_count >= 2 ? 1 : 0

  identifier          = "${var.environment}-muejam-db-replica-2"
  replicate_source_db = aws_db_instance.primary.identifier
  instance_class      = var.replica_instance_class

  # Storage configuration (inherited from primary)
  storage_encrypted = true

  # Network configuration
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false

  # Parameter group
  parameter_group_name = aws_db_parameter_group.main.name

  # Monitoring
  enabled_cloudwatch_logs_exports       = ["postgresql"]
  monitoring_interval                   = 60
  monitoring_role_arn                   = aws_iam_role.rds_monitoring.arn
  performance_insights_enabled          = true
  performance_insights_retention_period = 7

  # Auto minor version upgrade
  auto_minor_version_upgrade = true

  # Deletion protection
  skip_final_snapshot = true

  tags = {
    Name        = "${var.environment}-muejam-db-replica-2"
    Environment = var.environment
    Role        = "read-replica"
  }
}

# IAM Role for Enhanced Monitoring
resource "aws_iam_role" "rds_monitoring" {
  name = "${var.environment}-muejam-rds-monitoring-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.environment}-muejam-rds-monitoring-role"
    Environment = var.environment
  }
}

# Attach Enhanced Monitoring Policy
resource "aws_iam_role_policy_attachment" "rds_monitoring" {
  role       = aws_iam_role.rds_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

# CloudWatch Alarms for Primary Database
resource "aws_cloudwatch_metric_alarm" "database_cpu" {
  alarm_name          = "${var.environment}-muejam-db-primary-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors RDS CPU utilization"

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.primary.id
  }

  tags = {
    Name        = "${var.environment}-muejam-db-primary-cpu"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_metric_alarm" "database_connections" {
  alarm_name          = "${var.environment}-muejam-db-primary-connections"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = var.max_connections * 0.8 # Alert at 80% of max connections
  alarm_description   = "This metric monitors RDS connection count"

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.primary.id
  }

  tags = {
    Name        = "${var.environment}-muejam-db-primary-connections"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_metric_alarm" "replica_lag" {
  count = var.create_read_replicas ? 1 : 0

  alarm_name          = "${var.environment}-muejam-db-replica-1-lag"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "ReplicaLag"
  namespace           = "AWS/RDS"
  period              = "60"
  statistic           = "Average"
  threshold           = "1000" # 1 second lag
  alarm_description   = "This metric monitors read replica lag"

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.read_replica_1[0].id
  }

  tags = {
    Name        = "${var.environment}-muejam-db-replica-1-lag"
    Environment = var.environment
  }
}
