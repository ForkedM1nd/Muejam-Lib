# MueJam Library Infrastructure

This directory contains Terraform configurations for deploying the MueJam Library platform infrastructure on AWS.

## Architecture Overview

The infrastructure includes:

- **VPC**: Multi-AZ VPC with public and private subnets
- **Application Load Balancer (ALB)**: Distributes traffic across application servers with SSL termination
- **Auto Scaling Group (ASG)**: Automatically scales application servers based on CPU utilization
- **NAT Gateways**: Enable private subnet instances to access the internet
- **Security Groups**: Control network access to resources
- **CloudWatch Alarms**: Monitor CPU and trigger auto-scaling

## Prerequisites

1. **AWS Account**: Active AWS account with appropriate permissions
2. **Terraform**: Install Terraform >= 1.0 ([Installation Guide](https://learn.hashicorp.com/tutorials/terraform/install-cli))
3. **AWS CLI**: Configure AWS credentials ([Configuration Guide](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html))
4. **SSL Certificate**: Create an SSL certificate in AWS Certificate Manager for HTTPS
5. **AMI**: Build or identify an AMI for your application servers
6. **EC2 Key Pair**: Create an EC2 key pair for SSH access

## Quick Start

### 1. Configure Variables

Copy the example variables file and update with your values:

```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` and update:
- `ssl_certificate_arn`: Your ACM certificate ARN
- `app_ami_id`: Your application AMI ID
- `ec2_key_name`: Your EC2 key pair name
- Other values as needed

### 2. Initialize Terraform

```bash
terraform init
```

### 3. Review the Plan

```bash
terraform plan
```

Review the resources that will be created.

### 4. Apply the Configuration

```bash
terraform apply
```

Type `yes` when prompted to create the resources.

### 5. Get Outputs

After successful deployment:

```bash
terraform output
```

This will show:
- ALB DNS name (use this for your domain's CNAME record)
- VPC ID
- Auto Scaling Group name
- Other resource identifiers

## Configuration

### Auto Scaling

The auto-scaling configuration:
- **Minimum instances**: 2 (for high availability)
- **Maximum instances**: 10 (handles up to 10,000 concurrent users)
- **Scale up trigger**: CPU > 70% for 2 consecutive periods (2 minutes)
- **Scale down trigger**: CPU < 30% for 2 consecutive periods (2 minutes)
- **Cooldown period**: 5 minutes between scaling actions

### Health Checks

The ALB performs health checks on the `/health` endpoint:
- **Interval**: 30 seconds
- **Timeout**: 5 seconds
- **Healthy threshold**: 2 consecutive successes
- **Unhealthy threshold**: 3 consecutive failures

Instances failing health checks are automatically removed from the load balancer.

### Connection Draining

When instances are terminated:
- **Deregistration delay**: 60 seconds
- Existing connections are allowed to complete
- New connections are routed to healthy instances

## Modules

### networking

Creates VPC, subnets, internet gateway, NAT gateways, and route tables.

**Outputs:**
- `vpc_id`: VPC identifier
- `public_subnet_ids`: Public subnet identifiers
- `private_subnet_ids`: Private subnet identifiers

### alb

Creates Application Load Balancer, target group, listeners, and security groups.

**Outputs:**
- `alb_dns_name`: DNS name for the load balancer
- `alb_arn`: ARN of the load balancer
- `target_group_arn`: ARN of the target group

### asg

Creates Auto Scaling Group, launch template, scaling policies, and CloudWatch alarms.

**Outputs:**
- `asg_name`: Name of the auto-scaling group
- `asg_arn`: ARN of the auto-scaling group

## State Management

For production use, configure remote state storage:

1. Create an S3 bucket for state storage:
```bash
aws s3 mb s3://muejam-terraform-state
aws s3api put-bucket-versioning --bucket muejam-terraform-state --versioning-configuration Status=Enabled
```

2. Create a DynamoDB table for state locking:
```bash
aws dynamodb create-table \
  --table-name muejam-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

3. Uncomment the backend configuration in `main.tf`:
```hcl
backend "s3" {
  bucket         = "muejam-terraform-state"
  key            = "production/terraform.tfstate"
  region         = "us-east-1"
  encrypt        = true
  dynamodb_table = "muejam-terraform-locks"
}
```

4. Initialize with the backend:
```bash
terraform init -migrate-state
```

## Security Considerations

1. **SSL/TLS**: HTTPS is enforced with TLS 1.2 minimum
2. **Security Groups**: Restrictive ingress rules, only necessary ports open
3. **Private Subnets**: Application servers run in private subnets
4. **IAM Roles**: EC2 instances use IAM roles instead of access keys
5. **Secrets**: Never commit `terraform.tfvars` or state files to version control

## Monitoring

CloudWatch metrics are automatically collected:
- CPU utilization
- Network traffic
- Target health
- Request count
- Response times

Access metrics in the AWS CloudWatch console.

## Troubleshooting

### Instances failing health checks

1. Check application logs on the instance
2. Verify the `/health` endpoint returns 200 status
3. Check security group rules allow traffic from ALB
4. Verify application is listening on port 8000

### Auto-scaling not working

1. Check CloudWatch alarms are in "OK" or "ALARM" state
2. Verify scaling policies are attached to the ASG
3. Check ASG activity history in AWS console
4. Ensure cooldown periods have elapsed

### Cannot access application

1. Verify ALB DNS name resolves
2. Check target group has healthy instances
3. Verify security groups allow inbound traffic
4. Check SSL certificate is valid and matches domain

## Cleanup

To destroy all resources:

```bash
terraform destroy
```

**Warning**: This will delete all infrastructure. Ensure you have backups of any important data.

## Cost Estimation

Approximate monthly costs (us-east-1):
- ALB: ~$20
- NAT Gateways (3): ~$100
- EC2 instances (2 x t3.medium): ~$60
- Data transfer: Variable
- **Total**: ~$180/month minimum

Costs increase with:
- More instances (auto-scaling)
- Higher data transfer
- Additional services (RDS, ElastiCache, etc.)

## Next Steps

After infrastructure deployment:

1. **DNS Configuration**: Point your domain to the ALB DNS name
2. **Application Deployment**: Deploy your application to the instances
3. **Database Setup**: Configure RDS or other database services
4. **Monitoring**: Set up additional CloudWatch dashboards and alarms
5. **Backup**: Configure automated backups for databases and critical data
6. **CI/CD**: Integrate with your deployment pipeline

## Support

For issues or questions:
- Check AWS documentation
- Review Terraform documentation
- Consult the MueJam Library development team
