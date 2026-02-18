#!/bin/bash
# Smoke tests for post-deployment verification
# Usage: ./scripts/smoke-tests.sh <environment>

set -e

ENVIRONMENT="${1:-staging}"
BASE_URL="https://${ENVIRONMENT}-api.muejam.com"

echo "Running smoke tests against $BASE_URL"
echo ""

# Test 1: Health check
echo "Test 1: Health check..."
HEALTH_RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null "$BASE_URL/health")
if [ "$HEALTH_RESPONSE" -eq 200 ]; then
    echo "✓ Health check passed"
else
    echo "✗ Health check failed (HTTP $HEALTH_RESPONSE)"
    exit 1
fi

# Test 2: API root
echo "Test 2: API root..."
API_RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null "$BASE_URL/api/v1/")
if [ "$API_RESPONSE" -eq 200 ]; then
    echo "✓ API root accessible"
else
    echo "✗ API root failed (HTTP $API_RESPONSE)"
    exit 1
fi

# Test 3: Database connectivity
echo "Test 3: Database connectivity..."
# This would call a test endpoint that verifies database connection
DB_RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null "$BASE_URL/api/v1/health/database")
if [ "$DB_RESPONSE" -eq 200 ]; then
    echo "✓ Database connectivity verified"
else
    echo "✗ Database connectivity failed (HTTP $DB_RESPONSE)"
    exit 1
fi

# Test 4: Cache connectivity
echo "Test 4: Cache connectivity..."
CACHE_RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null "$BASE_URL/api/v1/health/cache")
if [ "$CACHE_RESPONSE" -eq 200 ]; then
    echo "✓ Cache connectivity verified"
else
    echo "✗ Cache connectivity failed (HTTP $CACHE_RESPONSE)"
    exit 1
fi

echo ""
echo "All smoke tests passed!"
