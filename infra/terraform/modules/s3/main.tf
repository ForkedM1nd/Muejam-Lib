# S3 Storage Module
# Provides S3 buckets for file storage with lifecycle policies

# Media Storage Bucket
resource "aws_s3_bucket" "media" {
  bucket = "${var.environment}-muejam-media"

  tags = {
    Name        = "${var.environment}-muejam-media"
    Environment = var.environment
    Purpose     = "User uploaded media files"
  }
}

# Enable versioning for media bucket
resource "aws_s3_bucket_versioning" "media" {
  bucket = aws_s3_bucket.media.id

  versioning_configuration {
    status = var.enable_versioning ? "Enabled" : "Suspended"
  }
}

# Enable encryption for media bucket
resource "aws_s3_bucket_server_side_encryption_configuration" "media" {
  bucket = aws_s3_bucket.media.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block public access for media bucket
resource "aws_s3_bucket_public_access_block" "media" {
  bucket = aws_s3_bucket.media.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lifecycle policy for media bucket
resource "aws_s3_bucket_lifecycle_configuration" "media" {
  bucket = aws_s3_bucket.media.id

  rule {
    id     = "delete-old-versions"
    status = "Enabled"

    noncurrent_version_expiration {
      noncurrent_days = 90
    }
  }

  rule {
    id     = "transition-to-ia"
    status = "Enabled"

    transition {
      days          = 90
      storage_class = "STANDARD_IA"
    }
  }

  rule {
    id     = "transition-to-glacier"
    status = "Enabled"

    transition {
      days          = 180
      storage_class = "GLACIER"
    }
  }
}

# CORS configuration for media bucket
resource "aws_s3_bucket_cors_configuration" "media" {
  bucket = aws_s3_bucket.media.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST", "DELETE", "HEAD"]
    allowed_origins = var.allowed_origins
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}

# Static Assets Bucket (for CloudFront)
resource "aws_s3_bucket" "static" {
  bucket = "${var.environment}-muejam-static"

  tags = {
    Name        = "${var.environment}-muejam-static"
    Environment = var.environment
    Purpose     = "Static assets (CSS, JS, images)"
  }
}

# Enable versioning for static bucket
resource "aws_s3_bucket_versioning" "static" {
  bucket = aws_s3_bucket.static.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Enable encryption for static bucket
resource "aws_s3_bucket_server_side_encryption_configuration" "static" {
  bucket = aws_s3_bucket.static.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block public access for static bucket (served via CloudFront)
resource "aws_s3_bucket_public_access_block" "static" {
  bucket = aws_s3_bucket.static.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Backups Bucket
resource "aws_s3_bucket" "backups" {
  bucket = "${var.environment}-muejam-backups"

  tags = {
    Name        = "${var.environment}-muejam-backups"
    Environment = var.environment
    Purpose     = "Database and application backups"
  }
}

# Enable versioning for backups bucket
resource "aws_s3_bucket_versioning" "backups" {
  bucket = aws_s3_bucket.backups.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Enable encryption for backups bucket
resource "aws_s3_bucket_server_side_encryption_configuration" "backups" {
  bucket = aws_s3_bucket.backups.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block public access for backups bucket
resource "aws_s3_bucket_public_access_block" "backups" {
  bucket = aws_s3_bucket.backups.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lifecycle policy for backups bucket
resource "aws_s3_bucket_lifecycle_configuration" "backups" {
  bucket = aws_s3_bucket.backups.id

  rule {
    id     = "delete-old-backups"
    status = "Enabled"

    expiration {
      days = var.backup_retention_days
    }
  }

  rule {
    id     = "transition-to-glacier"
    status = "Enabled"

    transition {
      days          = 30
      storage_class = "GLACIER"
    }
  }
}

# IAM policy for application access to media bucket
resource "aws_iam_policy" "media_access" {
  name        = "${var.environment}-muejam-media-access"
  description = "Allow application to access media bucket"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.media.arn,
          "${aws_s3_bucket.media.arn}/*"
        ]
      }
    ]
  })

  tags = {
    Name        = "${var.environment}-muejam-media-access"
    Environment = var.environment
  }
}

# CloudWatch metrics for S3 buckets
resource "aws_cloudwatch_metric_alarm" "media_bucket_size" {
  alarm_name          = "${var.environment}-muejam-media-bucket-size"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "BucketSizeBytes"
  namespace           = "AWS/S3"
  period              = "86400" # 1 day
  statistic           = "Average"
  threshold           = var.bucket_size_alert_threshold
  alarm_description   = "This metric monitors media bucket size"

  dimensions = {
    BucketName  = aws_s3_bucket.media.id
    StorageType = "StandardStorage"
  }

  tags = {
    Name        = "${var.environment}-muejam-media-bucket-size"
    Environment = var.environment
  }
}
