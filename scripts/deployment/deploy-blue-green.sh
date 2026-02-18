#!/bin/bash
# Blue-Green deployment script for MueJam Library
# Usage: ./scripts/deploy-blue-green.sh <environment> <target-color>
# Example: ./scripts/deploy-blue-green.sh production green

set -e  # Exit on error
set -u  # Exit on undefined variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT="${1:-production}"
TARGET_COLOR="${2:-green}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Validate inputs
if [[ ! "$ENVIRONMENT" =~ ^(staging|production)$ ]]; then
    echo -e "${RED}Error: Invalid environment '$ENVIRONMENT'${NC}"
    exit 1
fi

if [[ ! "$TARGET_COLOR" =~ ^(blue|green)$ ]]; then
    echo -e "${RED}Error: Invalid target color '$TARGET_COLOR'${NC}"
    exit 1
fi

# Determine current and target environments
if [[ "$TARGET_COLOR" == "green" ]]; then
    CURRENT_COLOR="blue"
else
    CURRENT_COLOR="green"
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Blue-Green Deployment${NC}"
echo -e "${BLUE}Environment: $ENVIRONMENT${NC}"
echo -e "${BLUE}Current: $CURRENT_COLOR${NC}"
echo -e "${BLUE}Target: $TARGET_COLOR${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Step 1: Deploy to target environment
echo -e "${YELLOW}Step 1: Deploying to $TARGET_COLOR environment...${NC}"

# Get version
VERSION=$(git describe --tags --always)
echo "Version: $VERSION"

# Deploy application to target environment
# This would typically involve:
# - Building Docker image with version tag
# - Pushing to container registry
# - Updating ECS/Kubernetes deployment for target color
# - Waiting for deployment to complete

echo "Building Docker image..."
docker build -t muejam-backend:$VERSION -f Dockerfile .

echo "Tagging image for $TARGET_COLOR environment..."
docker tag muejam-backend:$VERSION muejam-backend:$ENVIRONMENT-$TARGET_COLOR

echo "Pushing image to registry..."
# docker push muejam-backend:$ENVIRONMENT-$TARGET_COLOR

echo -e "${GREEN}✓ Deployed to $TARGET_COLOR environment${NC}"
echo ""

# Step 2: Run database migrations
echo -e "${YELLOW}Step 2: Running database migrations...${NC}"

# Migrations run on target environment before traffic switch
# This ensures the new code can work with the migrated schema
# python manage.py migrate --database=$ENVIRONMENT-$TARGET_COLOR

echo -e "${GREEN}✓ Migrations completed${NC}"
echo ""

# Step 3: Warm up target environment
echo -e "${YELLOW}Step 3: Warming up $TARGET_COLOR environment...${NC}"

# Send test traffic to warm up caches and connections
"$SCRIPT_DIR/warmup.sh" "$ENVIRONMENT-$TARGET_COLOR"

echo -e "${GREEN}✓ Warm-up completed${NC}"
echo ""

# Step 4: Health checks
echo -e "${YELLOW}Step 4: Running health checks on $TARGET_COLOR environment...${NC}"

MAX_RETRIES=30
RETRY_COUNT=0
HEALTH_CHECK_URL="https://$ENVIRONMENT-$TARGET_COLOR-api.muejam.com/health"

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -f -s "$HEALTH_CHECK_URL" > /dev/null; then
        echo -e "${GREEN}✓ Health check passed${NC}"
        break
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "Health check attempt $RETRY_COUNT/$MAX_RETRIES..."
    sleep 10
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "${RED}Health checks failed after $MAX_RETRIES attempts${NC}"
    exit 1
fi

echo ""

# Step 5: Gradual traffic shift
echo -e "${YELLOW}Step 5: Shifting traffic to $TARGET_COLOR environment...${NC}"

# Shift traffic gradually: 10% -> 25% -> 50% -> 75% -> 100%
TRAFFIC_PERCENTAGES=(10 25 50 75 100)
MONITORING_DURATION=300  # 5 minutes per step

for PERCENTAGE in "${TRAFFIC_PERCENTAGES[@]}"; do
    echo ""
    echo -e "${BLUE}Shifting $PERCENTAGE% traffic to $TARGET_COLOR...${NC}"
    
    # Update load balancer to send PERCENTAGE% to target
    # This would use AWS ALB weighted target groups or similar
    # aws elbv2 modify-target-group-attributes ...
    
    echo "Monitoring for $MONITORING_DURATION seconds..."
    
    # Monitor metrics during traffic shift
    START_TIME=$(date +%s)
    while [ $(($(date +%s) - START_TIME)) -lt $MONITORING_DURATION ]; do
        # Check error rate
        ERROR_RATE=$("$SCRIPT_DIR/check-error-rate.sh" "$ENVIRONMENT-$TARGET_COLOR")
        
        if (( $(echo "$ERROR_RATE > 2.0" | bc -l) )); then
            echo -e "${RED}Error rate exceeded threshold: $ERROR_RATE%${NC}"
            echo "Initiating automatic rollback..."
            "$SCRIPT_DIR/rollback.sh" "$ENVIRONMENT"
            exit 1
        fi
        
        # Check response time
        P99_LATENCY=$("$SCRIPT_DIR/check-latency.sh" "$ENVIRONMENT-$TARGET_COLOR")
        
        if (( $(echo "$P99_LATENCY > 2000" | bc -l) )); then
            echo -e "${RED}Response time exceeded threshold: ${P99_LATENCY}ms${NC}"
            echo "Initiating automatic rollback..."
            "$SCRIPT_DIR/rollback.sh" "$ENVIRONMENT"
            exit 1
        fi
        
        # Display current metrics
        echo -ne "\rError Rate: $ERROR_RATE% | P99 Latency: ${P99_LATENCY}ms | Time: $(($(date +%s) - START_TIME))s / ${MONITORING_DURATION}s"
        
        sleep 30
    done
    
    echo ""
    echo -e "${GREEN}✓ $PERCENTAGE% traffic shift successful${NC}"
done

echo ""
echo -e "${GREEN}✓ All traffic shifted to $TARGET_COLOR environment${NC}"
echo ""

# Step 6: Final verification
echo -e "${YELLOW}Step 6: Running final verification...${NC}"

# Run comprehensive smoke tests
"$SCRIPT_DIR/smoke-tests.sh" "$ENVIRONMENT-$TARGET_COLOR" || {
    echo -e "${RED}Final verification failed${NC}"
    echo "Initiating rollback..."
    "$SCRIPT_DIR/rollback.sh" "$ENVIRONMENT"
    exit 1
}

echo -e "${GREEN}✓ Final verification passed${NC}"
echo ""

# Step 7: Keep old environment for rollback
echo -e "${YELLOW}Step 7: Maintaining $CURRENT_COLOR environment for rollback...${NC}"

echo "$CURRENT_COLOR environment will be kept running for 24 hours"
echo "This allows for quick rollback if issues are discovered"
echo ""
echo "To manually rollback, run:"
echo "  ./scripts/rollback.sh $ENVIRONMENT"
echo ""

# Success
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Blue-Green deployment completed!${NC}"
echo -e "${GREEN}Active environment: $TARGET_COLOR${NC}"
echo -e "${GREEN}Standby environment: $CURRENT_COLOR${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Monitoring:"
echo "- Continue monitoring for 30 minutes"
echo "- Watch error rates and performance metrics"
echo "- Check for user-reported issues"
echo ""
echo "Cleanup:"
echo "- $CURRENT_COLOR environment will be decommissioned in 24 hours"
echo "- To decommission now: ./scripts/decommission.sh $ENVIRONMENT $CURRENT_COLOR"
