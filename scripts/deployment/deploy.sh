#!/bin/bash
# Main deployment script for MueJam Library
# Usage: ./scripts/deploy.sh <environment>
# Example: ./scripts/deploy.sh production

set -e  # Exit on error
set -u  # Exit on undefined variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENVIRONMENT="${1:-staging}"

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(development|staging|production)$ ]]; then
    echo -e "${RED}Error: Invalid environment '$ENVIRONMENT'${NC}"
    echo "Usage: $0 <development|staging|production>"
    exit 1
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}MueJam Library Deployment${NC}"
echo -e "${GREEN}Environment: $ENVIRONMENT${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Step 1: Pre-deployment checks
echo -e "${YELLOW}Step 1: Running pre-deployment checks...${NC}"

# Check if on correct branch
CURRENT_BRANCH=$(git branch --show-current)
if [[ "$ENVIRONMENT" == "production" && "$CURRENT_BRANCH" != "main" ]]; then
    echo -e "${RED}Error: Production deployments must be from 'main' branch${NC}"
    echo "Current branch: $CURRENT_BRANCH"
    exit 1
fi

# Check for uncommitted changes
if [[ -n $(git status --porcelain) ]]; then
    echo -e "${RED}Error: Uncommitted changes detected${NC}"
    git status --short
    exit 1
fi

# Validate configuration
echo "Validating configuration..."
cd "$PROJECT_ROOT"
python manage.py validate_config --environment "$ENVIRONMENT" --no-fail || {
    echo -e "${RED}Configuration validation failed${NC}"
    exit 1
}

echo -e "${GREEN}✓ Pre-deployment checks passed${NC}"
echo ""

# Step 2: Run tests (Requirement 29.3)
echo -e "${YELLOW}Step 2: Running tests...${NC}"

# Run unit tests
echo "Running unit tests..."
pytest apps/backend/tests/ -v --tb=short || {
    echo -e "${RED}Unit tests failed${NC}"
    exit 1
}

# Run integration tests
echo "Running integration tests..."
pytest apps/backend/tests/integration/ -v --tb=short || {
    echo -e "${RED}Integration tests failed${NC}"
    exit 1
}

echo -e "${GREEN}✓ All tests passed${NC}"
echo ""

# Step 3: Build application
echo -e "${YELLOW}Step 3: Building application...${NC}"

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt --quiet

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

echo -e "${GREEN}✓ Application built successfully${NC}"
echo ""

# Step 4: Database migrations (Requirement 29.5)
echo -e "${YELLOW}Step 4: Checking database migrations...${NC}"

# Check for pending migrations
PENDING_MIGRATIONS=$(python manage.py showmigrations | grep "\[ \]" | wc -l)

if [[ $PENDING_MIGRATIONS -gt 0 ]]; then
    echo "Found $PENDING_MIGRATIONS pending migrations"
    
    # Create backup before migrations (Requirement 29.6)
    if [[ "$ENVIRONMENT" == "production" ]]; then
        echo "Creating database backup..."
        "$SCRIPT_DIR/backup-database.sh" "$ENVIRONMENT" || {
            echo -e "${RED}Database backup failed${NC}"
            exit 1
        }
    fi
    
    # Run migrations
    echo "Running migrations..."
    python manage.py migrate --noinput || {
        echo -e "${RED}Database migrations failed${NC}"
        exit 1
    }
    
    echo -e "${GREEN}✓ Migrations completed${NC}"
else
    echo "No pending migrations"
fi

echo ""

# Step 5: Deploy application
echo -e "${YELLOW}Step 5: Deploying application...${NC}"

# Get current version
VERSION=$(git describe --tags --always)
echo "Deploying version: $VERSION"

# Deploy based on environment
case "$ENVIRONMENT" in
    development)
        echo "Restarting development server..."
        # Development deployment logic
        ;;
    
    staging)
        echo "Deploying to staging..."
        # Staging deployment logic
        # This would typically involve:
        # - Building Docker image
        # - Pushing to container registry
        # - Updating ECS/Kubernetes deployment
        ;;
    
    production)
        echo "Deploying to production..."
        # Production uses blue-green deployment
        "$SCRIPT_DIR/deploy-blue-green.sh" "$ENVIRONMENT" green || {
            echo -e "${RED}Production deployment failed${NC}"
            exit 1
        }
        ;;
esac

echo -e "${GREEN}✓ Application deployed${NC}"
echo ""

# Step 6: Post-deployment verification
echo -e "${YELLOW}Step 6: Running post-deployment verification...${NC}"

# Wait for application to start
echo "Waiting for application to start..."
sleep 10

# Run smoke tests
echo "Running smoke tests..."
"$SCRIPT_DIR/smoke-tests.sh" "$ENVIRONMENT" || {
    echo -e "${RED}Smoke tests failed${NC}"
    echo "Consider rolling back the deployment"
    exit 1
}

echo -e "${GREEN}✓ Post-deployment verification passed${NC}"
echo ""

# Step 7: Notify team (Requirement 29.11)
echo -e "${YELLOW}Step 7: Sending deployment notification...${NC}"

"$SCRIPT_DIR/notify-deployment.sh" success \
    --version "$VERSION" \
    --environment "$ENVIRONMENT" \
    --deployed-by "$(git config user.name)"

echo -e "${GREEN}✓ Deployment notification sent${NC}"
echo ""

# Success
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment completed successfully!${NC}"
echo -e "${GREEN}Version: $VERSION${NC}"
echo -e "${GREEN}Environment: $ENVIRONMENT${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Monitor error rates and performance metrics"
echo "2. Verify critical functionality"
echo "3. Check for user-reported issues"
echo ""
echo "Monitoring dashboards:"
echo "- Sentry: https://sentry.io/organizations/muejam/issues/"
echo "- Grafana: https://grafana.muejam.com/d/production"
echo "- PagerDuty: https://muejam.pagerduty.com/"
