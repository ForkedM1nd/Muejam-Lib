# Infrastructure

This directory contains all infrastructure-as-code (IaC) and infrastructure configuration for the MueJam Library platform.

## Directory Structure

```
infra/
├── terraform/          # Terraform infrastructure definitions
│   ├── modules/        # Reusable Terraform modules
│   ├── main.tf         # Main infrastructure configuration
│   ├── variables.tf    # Variable definitions
│   └── outputs.tf      # Output definitions
├── iam-policies/       # IAM policy documents
├── monitoring/         # Monitoring and observability configurations
│   ├── prometheus/     # Prometheus configuration
│   ├── grafana/        # Grafana dashboards and datasources
│   └── alertmanager/   # Alert manager configuration
└── README.md           # This file
```

## Components

### Terraform

Contains all Terraform configurations for provisioning and managing cloud infrastructure:
- **modules/**: Reusable Terraform modules for common infrastructure patterns
- Main configuration files for infrastructure deployment
- Environment-specific configurations (dev, staging, production)

See [terraform/README.md](terraform/README.md) for detailed documentation.

### IAM Policies

Contains IAM policy documents for AWS services:
- Secrets Manager access policies
- Service-specific access policies
- Role definitions and permissions

### Monitoring

Contains monitoring and observability configurations:
- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization dashboards
- **Alertmanager**: Alert routing and notification

See [monitoring/README.md](monitoring/) for setup instructions.

## Usage

### Terraform Deployment

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

### Monitoring Setup

```bash
cd monitoring
./setup.sh  # Linux/Mac
# or
./setup.ps1  # Windows
```

## Documentation

- [Deployment Infrastructure](terraform/DEPLOYMENT_INFRASTRUCTURE.md)
- [Auto Scaling](terraform/AUTO_SCALING.md)
- [Architecture Documentation](../docs/architecture/)

## Related Documentation

- [Deployment Guide](../docs/deployment/)
- [Architecture Overview](../docs/architecture/infrastructure.md)
