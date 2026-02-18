# S3 Module Outputs

output "media_bucket_id" {
  description = "ID of the media bucket"
  value       = aws_s3_bucket.media.id
}

output "media_bucket_arn" {
  description = "ARN of the media bucket"
  value       = aws_s3_bucket.media.arn
}

output "media_bucket_domain_name" {
  description = "Domain name of the media bucket"
  value       = aws_s3_bucket.media.bucket_domain_name
}

output "static_bucket_id" {
  description = "ID of the static assets bucket"
  value       = aws_s3_bucket.static.id
}

output "static_bucket_arn" {
  description = "ARN of the static assets bucket"
  value       = aws_s3_bucket.static.arn
}

output "static_bucket_domain_name" {
  description = "Domain name of the static assets bucket"
  value       = aws_s3_bucket.static.bucket_domain_name
}

output "backups_bucket_id" {
  description = "ID of the backups bucket"
  value       = aws_s3_bucket.backups.id
}

output "backups_bucket_arn" {
  description = "ARN of the backups bucket"
  value       = aws_s3_bucket.backups.arn
}

output "media_access_policy_arn" {
  description = "ARN of the media access IAM policy"
  value       = aws_iam_policy.media_access.arn
}
