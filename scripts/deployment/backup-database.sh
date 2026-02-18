#!/bin/bash
# Database backup script
# Usage: ./scripts/backup-database.sh <environment>

set -e

ENVIRONMENT="${1:-production}"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
SNAPSHOT_ID="muejam-${ENVIRONMENT}-backup-${TIMESTAMP}"

echo "Creating database backup for $ENVIRONMENT..."
echo "Snapshot ID: $SNAPSHOT_ID"

# Create RDS snapshot
aws rds create-db-snapshot \
    --db-instance-identifier "muejam-${ENVIRONMENT}" \
    --db-snapshot-identifier "$SNAPSHOT_ID" \
    --tags Key=Environment,Value="$ENVIRONMENT" Key=Type,Value=manual Key=Timestamp,Value="$TIMESTAMP"

echo "Waiting for snapshot to complete..."
aws rds wait db-snapshot-completed \
    --db-snapshot-identifier "$SNAPSHOT_ID"

echo "✓ Backup completed: $SNAPSHOT_ID"
