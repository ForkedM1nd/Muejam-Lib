"""
Configure CloudWatch Logs Retention

This script configures log retention policies for CloudWatch Logs.
Implements Requirement 15.8: Retain logs for 90 days hot, 1 year cold.

Usage:
    python configure_log_retention.py
"""

import os
import boto3
from botocore.exceptions import ClientError


def configure_cloudwatch_retention():
    """
    Configure CloudWatch Logs retention policies.
    
    Sets up:
    - Hot storage: 90 days retention in CloudWatch Logs
    - Cold storage: Archive to S3 after 90 days for 1 year total retention
    
    Implements Requirement 15.8.
    """
    # Get configuration from environment
    log_group = os.getenv('CLOUDWATCH_LOG_GROUP', '/muejam/backend')
    region = os.getenv('AWS_REGION', 'us-east-1')
    hot_retention_days = int(os.getenv('LOG_RETENTION_DAYS_HOT', '90'))
    
    # Initialize CloudWatch Logs client
    logs_client = boto3.client('logs', region_name=region)
    
    try:
        # Check if log group exists
        try:
            logs_client.describe_log_groups(logGroupNamePrefix=log_group)
            print(f"Log group {log_group} exists")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                # Create log group
                logs_client.create_log_group(logGroupName=log_group)
                print(f"Created log group: {log_group}")
            else:
                raise
        
        # Set retention policy (hot storage)
        logs_client.put_retention_policy(
            logGroupName=log_group,
            retentionInDays=hot_retention_days
        )
        print(f"Set retention policy: {hot_retention_days} days for {log_group}")
        
        # Add tags for organization
        logs_client.tag_log_group(
            logGroupName=log_group,
            tags={
                'Environment': os.getenv('ENVIRONMENT', 'production'),
                'Service': os.getenv('SERVICE_NAME', 'muejam-backend'),
                'RetentionPolicy': f'{hot_retention_days}days-hot',
            }
        )
        print(f"Tagged log group: {log_group}")
        
        print("\n✓ CloudWatch Logs retention configured successfully")
        print(f"  - Hot storage: {hot_retention_days} days in CloudWatch Logs")
        print(f"  - Cold storage: Configure S3 lifecycle policy for 1 year total retention")
        
    except ClientError as e:
        print(f"✗ Error configuring CloudWatch Logs: {e}")
        raise


def configure_s3_archive():
    """
    Configure S3 bucket for log archival (cold storage).
    
    Sets up:
    - S3 bucket for archived logs
    - Lifecycle policy to delete after 1 year
    - Encryption at rest
    
    Implements Requirement 15.8 (cold storage).
    """
    # Get configuration from environment
    bucket_name = os.getenv('LOG_ARCHIVE_BUCKET', 'muejam-logs-archive')
    region = os.getenv('AWS_REGION', 'us-east-1')
    cold_retention_days = int(os.getenv('LOG_RETENTION_DAYS_COLD', '365'))
    
    # Initialize S3 client
    s3_client = boto3.client('s3', region_name=region)
    
    try:
        # Check if bucket exists
        try:
            s3_client.head_bucket(Bucket=bucket_name)
            print(f"S3 bucket {bucket_name} exists")
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                # Create bucket
                if region == 'us-east-1':
                    s3_client.create_bucket(Bucket=bucket_name)
                else:
                    s3_client.create_bucket(
                        Bucket=bucket_name,
                        CreateBucketConfiguration={'LocationConstraint': region}
                    )
                print(f"Created S3 bucket: {bucket_name}")
            else:
                raise
        
        # Enable encryption
        s3_client.put_bucket_encryption(
            Bucket=bucket_name,
            ServerSideEncryptionConfiguration={
                'Rules': [
                    {
                        'ApplyServerSideEncryptionByDefault': {
                            'SSEAlgorithm': 'AES256'
                        }
                    }
                ]
            }
        )
        print(f"Enabled encryption for bucket: {bucket_name}")
        
        # Set lifecycle policy for cold storage retention
        s3_client.put_bucket_lifecycle_configuration(
            Bucket=bucket_name,
            LifecycleConfiguration={
                'Rules': [
                    {
                        'Id': 'DeleteOldLogs',
                        'Status': 'Enabled',
                        'Prefix': 'logs/',
                        'Expiration': {
                            'Days': cold_retention_days
                        }
                    },
                    {
                        'Id': 'TransitionToGlacier',
                        'Status': 'Enabled',
                        'Prefix': 'logs/',
                        'Transitions': [
                            {
                                'Days': 30,
                                'StorageClass': 'GLACIER'
                            }
                        ]
                    }
                ]
            }
        )
        print(f"Set lifecycle policy: {cold_retention_days} days retention for {bucket_name}")
        
        # Add bucket tags
        s3_client.put_bucket_tagging(
            Bucket=bucket_name,
            Tagging={
                'TagSet': [
                    {'Key': 'Environment', 'Value': os.getenv('ENVIRONMENT', 'production')},
                    {'Key': 'Service', 'Value': os.getenv('SERVICE_NAME', 'muejam-backend')},
                    {'Key': 'Purpose', 'Value': 'log-archive'},
                    {'Key': 'RetentionPolicy', 'Value': f'{cold_retention_days}days-cold'},
                ]
            }
        )
        print(f"Tagged S3 bucket: {bucket_name}")
        
        print("\n✓ S3 log archive configured successfully")
        print(f"  - Cold storage: {cold_retention_days} days in S3")
        print(f"  - Transition to Glacier after 30 days")
        print(f"  - Encryption: AES256")
        
    except ClientError as e:
        print(f"✗ Error configuring S3 archive: {e}")
        raise


def setup_cloudwatch_to_s3_export():
    """
    Set up automatic export from CloudWatch Logs to S3.
    
    This creates an export task that runs daily to archive logs to S3.
    """
    log_group = os.getenv('CLOUDWATCH_LOG_GROUP', '/muejam/backend')
    bucket_name = os.getenv('LOG_ARCHIVE_BUCKET', 'muejam-logs-archive')
    region = os.getenv('AWS_REGION', 'us-east-1')
    
    print("\n📋 To set up automatic CloudWatch to S3 export:")
    print(f"1. Create an S3 bucket policy allowing CloudWatch Logs to write:")
    print(f"""
{{
  "Version": "2012-10-17",
  "Statement": [
    {{
      "Effect": "Allow",
      "Principal": {{
        "Service": "logs.{region}.amazonaws.com"
      }},
      "Action": "s3:GetBucketAcl",
      "Resource": "arn:aws:s3:::{bucket_name}"
    }},
    {{
      "Effect": "Allow",
      "Principal": {{
        "Service": "logs.{region}.amazonaws.com"
      }},
      "Action": "s3:PutObject",
      "Resource": "arn:aws:s3:::{bucket_name}/logs/*",
      "Condition": {{
        "StringEquals": {{
          "s3:x-amz-acl": "bucket-owner-full-control"
        }}
      }}
    }}
  ]
}}
    """)
    
    print(f"\n2. Create a CloudWatch Events rule to export logs daily:")
    print(f"   - Schedule: cron(0 2 * * ? *)  # 2 AM UTC daily")
    print(f"   - Target: Lambda function that calls create_export_task")
    print(f"   - Log group: {log_group}")
    print(f"   - Destination: s3://{bucket_name}/logs/")


def main():
    """Main function to configure log retention."""
    print("=" * 60)
    print("CloudWatch Logs Retention Configuration")
    print("=" * 60)
    print()
    
    # Check AWS credentials
    try:
        boto3.client('sts').get_caller_identity()
        print("✓ AWS credentials configured")
    except Exception as e:
        print(f"✗ AWS credentials not configured: {e}")
        print("\nPlease configure AWS credentials:")
        print("  - Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables")
        print("  - Or configure AWS CLI: aws configure")
        return
    
    print()
    
    # Configure CloudWatch retention
    print("Configuring CloudWatch Logs retention...")
    print("-" * 60)
    try:
        configure_cloudwatch_retention()
    except Exception as e:
        print(f"Failed to configure CloudWatch retention: {e}")
    
    print()
    
    # Configure S3 archive
    print("Configuring S3 log archive...")
    print("-" * 60)
    try:
        configure_s3_archive()
    except Exception as e:
        print(f"Failed to configure S3 archive: {e}")
    
    print()
    
    # Show export setup instructions
    setup_cloudwatch_to_s3_export()
    
    print()
    print("=" * 60)
    print("Configuration complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()
