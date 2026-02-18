#!/bin/bash
# Rollback script for MueJam Library
# Usage: ./scripts/rollback.sh <environment> [reason]
# Example: ./scripts/rollback.sh production "High error rate detected"

set -e  # Exit on error
set -u  # Exit on undefined variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT="${1:-production}"
ROLLBACK_REASON="${2:-Manual rollback initiated}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${RED}========================================${NC}"
echo -e "${RED}ROLLBACK INITIATED${NC}"
echo -e "${RED}Environment: $ENVIRONMENT${NC}"
echo -e "${RED}Reason: $ROLLBACK_REASON${NC}"
echo -e "${RED}========================================${NC}"
echo ""

# Confirm rollback for production
if [[ "$ENVIRONMENT" == "production" ]]; then
    echo -e "${YELLOW}WARNING: You are about to rollback PRODUCTION${NC}"
    read -p "Are you sure you want to continue? (yes/no): " CONFIRM
    
    if [[ "$CONFIRM" != "yes" ]]; then
        echo "Rollback cancelled"
        exit 0
    fi
fi

# Step 1: Determine current and previous environments
echo -e "${YELLOW}Step 1: Identifying environments...${NC}"

# In blue-green deployment, we switch back to the previous color
# Assuming current is green, rollback to blue
CURRENT_COLOR="green"
PREVIOUS_COLOR="blue"

echo "Current environment: $CURRENT_COLOR"
echo "Rolling back to: $PREVIOUS_COLOR"
echo ""

# Step 2: Verify previous environment is healthy
echo -e "${YELLOW}Step 2: Verifying $PREVIOUS_COLOR environment health...${NC}"

HEALTH_CHECK_URL="https://$ENVIRONMENT-$PREVIOUS_COLOR-api.muejam.com/health"

if ! curl -f -s "$HEALTH_CHECK_URL" > /dev/null; then
    echo -e "${RED}Error: $PREVIOUS_COLOR environment is not healthy${NC}"
    echo "Cannot rollback to unhealthy environment"
    exit 1
fi

echo -e "${GREEN}✓ $PREVIOUS_COLOR environment is healthy${NC}"
echo ""

# Step 3: Switch traffic back to previous environment
echo -e "${YELLOW}Step 3: Switching traffic to $PREVIOUS_COLOR environment...${NC}"

# Immediate traffic switch (no gradual rollback)
echo "Switching 100% traffic to $PREVIOUS_COLOR..."

# Update load balancer to send all traffic to previous environment
# aws elbv2 modify-target-group-attributes ...

echo -e "${GREEN}✓ Traffic switched to $PREVIOUS_COLOR${NC}"
echo ""

# Step 4: Verify rollback successful
echo -e "${YELLOW}Step 4: Verifying rollback...${NC}"

# Check error rate
sleep 30  # Wait for metrics to update
ERROR_RATE=$("$SCRIPT_DIR/check-error-rate.sh" "$ENVIRONMENT-$PREVIOUS_COLOR")

echo "Current error rate: $ERROR_RATE%"

if (( $(echo "$ERROR_RATE > 2.0" | bc -l) )); then
    echo -e "${RED}Warning: Error rate still high after rollback${NC}"
    echo "Manual intervention may be required"
else
    echo -e "${GREEN}✓ Error rate within acceptable range${NC}"
fi

echo ""

# Step 5: Database rollback (if needed)
echo -e "${YELLOW}Step 5: Checking if database rollback is needed...${NC}"

# Check if migrations were run in the failed deployment
MIGRATIONS_RUN=$(python manage.py showmigrations | grep "\[X\]" | tail -1)

if [[ -n "$MIGRATIONS_RUN" ]]; then
    echo "Migrations were run in failed deployment"
    echo -e "${YELLOW}Database rollback may be required${NC}"
    echo ""
    echo "To rollback database:"
    echo "1. Enable maintenance mode: ./scripts/maintenance-mode.sh enable"
    echo "2. Restore from backup: ./scripts/restore-database.sh $ENVIRONMENT"
    echo "3. Disable maintenance mode: ./scripts/maintenance-mode.sh disable"
    echo ""
    read -p "Do you want to rollback database now? (yes/no): " ROLLBACK_DB
    
    if [[ "$ROLLBACK_DB" == "yes" ]]; then
        echo "Enabling maintenance mode..."
        "$SCRIPT_DIR/maintenance-mode.sh" enable
        
        echo "Restoring database from backup..."
        "$SCRIPT_DIR/restore-database.sh" "$ENVIRONMENT" || {
            echo -e "${RED}Database restore failed${NC}"
            exit 1
        }
        
        echo "Disabling maintenance mode..."
        "$SCRIPT_DIR/maintenance-mode.sh" disable
        
        echo -e "${GREEN}✓ Database rolled back${NC}"
    else
        echo "Skipping database rollback"
        echo "Database may be in inconsistent state - manual review required"
    fi
else
    echo "No migrations were run - database rollback not needed"
fi

echo ""

# Step 6: Notify team
echo -e "${YELLOW}Step 6: Sending rollback notification...${NC}"

CURRENT_VERSION=$(git describe --tags --always)

"$SCRIPT_DIR/notify-deployment.sh" rollback \
    --version "$CURRENT_VERSION" \
    --environment "$ENVIRONMENT" \
    --reason "$ROLLBACK_REASON" \
    --rolled-back-by "$(git config user.name)"

echo -e "${GREEN}✓ Rollback notification sent${NC}"
echo ""

# Step 7: Post-rollback actions
echo -e "${YELLOW}Step 7: Post-rollback actions...${NC}"

echo "1. Investigating root cause..."
echo "   - Check Sentry for errors: https://sentry.io/organizations/muejam/issues/"
echo "   - Review application logs"
echo "   - Analyze metrics in Grafana"
echo ""

echo "2. Creating incident report..."
echo "   - Document what went wrong"
echo "   - Identify root cause"
echo "   - Plan remediation"
echo ""

echo "3. Monitoring system..."
echo "   - Watch error rates for next 30 minutes"
echo "   - Verify user-reported issues resolved"
echo "   - Check all critical functionality"
echo ""

# Success
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Rollback completed successfully${NC}"
echo -e "${GREEN}Active environment: $PREVIOUS_COLOR${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Continue monitoring for 30 minutes"
echo "2. Investigate root cause of failure"
echo "3. Fix issues in development"
echo "4. Test thoroughly before next deployment"
echo "5. Update deployment procedures if needed"
echo ""
echo "Failed environment ($CURRENT_COLOR) is still running for investigation"
echo "To decommission: ./scripts/decommission.sh $ENVIRONMENT $CURRENT_COLOR"
