#!/bin/bash
# Check current error rate from monitoring system
# Usage: ./scripts/check-error-rate.sh <environment>

ENVIRONMENT="${1:-production}"

# Query Sentry or APM for error rate
# This is a placeholder - actual implementation would query your monitoring system
# For example, using Sentry API or CloudWatch metrics

# Simulated error rate (replace with actual query)
ERROR_RATE=$(curl -s "https://api.sentry.io/api/0/organizations/muejam/stats/" \
    -H "Authorization: Bearer $SENTRY_API_TOKEN" \
    | jq '.error_rate // 0.5')

echo "$ERROR_RATE"
