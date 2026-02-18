#!/bin/bash
# Send deployment notifications to Slack
# Usage: ./scripts/notify-deployment.sh <status> --version <version> --environment <env>

STATUS="${1:-success}"
VERSION=""
ENVIRONMENT=""
DEPLOYED_BY=""
REASON=""

# Parse arguments
shift
while [[ $# -gt 0 ]]; do
    case $1 in
        --version)
            VERSION="$2"
            shift 2
            ;;
        --environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --deployed-by)
            DEPLOYED_BY="$2"
            shift 2
            ;;
        --reason)
            REASON="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

# Slack webhook URL (should be in environment variable)
SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL:-}"

if [ -z "$SLACK_WEBHOOK_URL" ]; then
    echo "Warning: SLACK_WEBHOOK_URL not set, skipping notification"
    exit 0
fi

# Build message based on status
case "$STATUS" in
    success)
        COLOR="good"
        TITLE="✅ Deployment Successful"
        MESSAGE="Version $VERSION has been deployed to $ENVIRONMENT by $DEPLOYED_BY"
        ;;
    rollback)
        COLOR="danger"
        TITLE="⚠️ Deployment Rolled Back"
        MESSAGE="Deployment to $ENVIRONMENT has been rolled back. Reason: $REASON"
        ;;
    failed)
        COLOR="danger"
        TITLE="❌ Deployment Failed"
        MESSAGE="Deployment of version $VERSION to $ENVIRONMENT failed. Reason: $REASON"
        ;;
    *)
        COLOR="warning"
        TITLE="ℹ️ Deployment Status"
        MESSAGE="Deployment status: $STATUS"
        ;;
esac

# Send to Slack
curl -X POST "$SLACK_WEBHOOK_URL" \
    -H 'Content-Type: application/json' \
    -d "{
        \"attachments\": [{
            \"color\": \"$COLOR\",
            \"title\": \"$TITLE\",
            \"text\": \"$MESSAGE\",
            \"fields\": [
                {\"title\": \"Environment\", \"value\": \"$ENVIRONMENT\", \"short\": true},
                {\"title\": \"Version\", \"value\": \"$VERSION\", \"short\": true}
            ],
            \"footer\": \"MueJam Library Deployment\",
            \"ts\": $(date +%s)
        }]
    }"

echo "Notification sent to Slack"
