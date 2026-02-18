# Scripts

This directory contains automation and utility scripts for the MueJam Library project.

## Directory Structure

- **database/** - Database utilities (seeding, migrations, backups)
- **deployment/** - Deployment automation scripts
- **verification/** - System verification and health check scripts

## Database Scripts

### seed-data.py
Seeds the database with initial test data for development.

**Usage:**
```bash
cd apps/backend
python ../../scripts/database/seed-data.py
```

### seed-legal-documents.py
Seeds the database with legal documents (terms of service, privacy policy, etc.).

**Usage:**
```bash
cd apps/backend
python ../../scripts/database/seed-legal-documents.py
```

## Deployment Scripts

### deploy.sh
Main deployment script for production deployments.

### deploy-blue-green.sh
Blue-green deployment script for zero-downtime deployments.

### rollback.sh
Rollback script to revert to previous deployment.

### backup-database.sh
Creates a backup of the production database.

### smoke-tests.sh
Runs smoke tests after deployment to verify basic functionality.

### warmup.sh
Warms up the application cache after deployment.

### maintenance-mode.sh
Toggles maintenance mode on/off.

### create-release.sh
Creates a new release tag and prepares release notes.

### notify-deployment.sh
Sends deployment notifications to team channels.

### check-error-rate.sh
Monitors error rates during deployment.

### check-latency.sh
Monitors API latency during deployment.

## Verification Scripts

### check-db.py
Verifies database connectivity and schema integrity.

**Usage:**
```bash
cd apps/backend
python ../../scripts/verification/check-db.py
```

### verify-ratelimit-setup.py
Verifies rate limiting configuration is correct.

**Usage:**
```bash
cd apps/backend
python ../../scripts/verification/verify-ratelimit-setup.py
```

### verify-security-headers.py
Verifies security headers are properly configured.

**Usage:**
```bash
cd apps/backend
python ../../scripts/verification/verify-security-headers.py
```

## Running Scripts

Most Python scripts need to be run from the `apps/backend` directory to ensure proper Django settings and import paths:

```bash
cd apps/backend
python ../../scripts/<category>/<script-name>.py
```

Shell scripts can typically be run from anywhere:

```bash
./scripts/deployment/deploy.sh
```

## Adding New Scripts

When adding new scripts:

1. Place them in the appropriate category directory
2. Use kebab-case for script names (e.g., `my-new-script.py`)
3. Add a shebang line for Python scripts: `#!/usr/bin/env python`
4. Make shell scripts executable: `chmod +x script-name.sh`
5. Update this README with usage instructions
6. Document any environment variables or prerequisites
