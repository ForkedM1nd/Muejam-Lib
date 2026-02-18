#!/bin/bash
# Warm up application by sending test traffic
# Usage: ./scripts/warmup.sh <environment>

set -e

ENVIRONMENT="${1:-production}"
BASE_URL="https://${ENVIRONMENT}-api.muejam.com"

echo "Warming up $ENVIRONMENT environment..."

# Send requests to common endpoints to warm up caches
ENDPOINTS=(
    "/health"
    "/api/v1/"
    "/api/v1/stories/"
    "/api/v1/whispers/"
    "/api/v1/discovery/trending"
)

for ENDPOINT in "${ENDPOINTS[@]}"; do
    echo "Warming up $ENDPOINT..."
    for i in {1..10}; do
        curl -s "$BASE_URL$ENDPOINT" > /dev/null &
    done
done

# Wait for all requests to complete
wait

echo "✓ Warm-up completed"
