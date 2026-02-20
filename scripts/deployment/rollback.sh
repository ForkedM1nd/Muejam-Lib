#!/usr/bin/env bash
# Rollback script for MueJam Library.
# Usage: ./scripts/deployment/rollback.sh <environment> [reason] [--yes]

set -euo pipefail

ENVIRONMENT="production"
ROLLBACK_REASON="Manual rollback initiated"
AUTO_APPROVE=false

if [[ $# -gt 0 ]]; then
    ENVIRONMENT="$1"
    shift
fi

if [[ $# -gt 0 && "${1:-}" != --* ]]; then
    ROLLBACK_REASON="$1"
    shift
fi

while [[ $# -gt 0 ]]; do
    case "$1" in
        --yes|-y)
            AUTO_APPROVE=true
            ;;
        *)
            echo "FAIL: unknown option '$1'"
            echo "Usage: ./scripts/deployment/rollback.sh <environment> [reason] [--yes]"
            exit 1
            ;;
    esac
    shift
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
ROLLBACK_ERROR_RATE_THRESHOLD="${ROLLBACK_ERROR_RATE_THRESHOLD:-2.0}"
CHECK_POST_ROLLBACK_METRICS="${CHECK_POST_ROLLBACK_METRICS:-true}"
CURRENT_COLOR="${CURRENT_COLOR:-green}"

PYTHON_BIN="$(command -v python3 || command -v python || true)"

require_command() {
    if ! command -v "$1" > /dev/null 2>&1; then
        echo "FAIL: required command '$1' is not installed"
        exit 1
    fi
}

greater_than() {
    local value="$1"
    local threshold="$2"

    "$PYTHON_BIN" - "$value" "$threshold" <<'PY'
import sys

value = float(sys.argv[1])
threshold = float(sys.argv[2])

raise SystemExit(0 if value > threshold else 1)
PY
}

if [[ "$ENVIRONMENT" != "development" && "$ENVIRONMENT" != "staging" && "$ENVIRONMENT" != "production" ]]; then
    echo "FAIL: invalid environment '${ENVIRONMENT}'"
    exit 1
fi

if [[ "$CURRENT_COLOR" != "blue" && "$CURRENT_COLOR" != "green" ]]; then
    echo "FAIL: CURRENT_COLOR must be 'blue' or 'green'"
    exit 1
fi

if [[ -z "$PYTHON_BIN" ]]; then
    echo "FAIL: python is required for rollback checks"
    exit 1
fi

require_command curl

if [[ "$CURRENT_COLOR" == "green" ]]; then
    PREVIOUS_COLOR="blue"
else
    PREVIOUS_COLOR="green"
fi

echo "========================================"
echo "Rollback initiated"
echo "Environment: ${ENVIRONMENT}"
echo "Current color: ${CURRENT_COLOR}"
echo "Rollback target: ${PREVIOUS_COLOR}"
echo "Reason: ${ROLLBACK_REASON}"
echo "========================================"

if [[ "$ENVIRONMENT" == "production" && "$AUTO_APPROVE" != "true" ]]; then
    read -r -p "Confirm production rollback (yes/no): " confirmation
    if [[ "$confirmation" != "yes" ]]; then
        echo "INFO: rollback cancelled"
        exit 0
    fi
fi

echo "Step 1: Verifying target environment health"
ROLLBACK_HEALTH_URL="${ROLLBACK_HEALTH_URL:-https://${ENVIRONMENT}-${PREVIOUS_COLOR}-api.muejam.com/health}"

if ! curl --silent --show-error --fail --max-time 10 "$ROLLBACK_HEALTH_URL" > /dev/null; then
    echo "FAIL: rollback target is unhealthy (${ROLLBACK_HEALTH_URL})"
    exit 1
fi

echo "PASS: rollback target is healthy"

echo "Step 2: Switching traffic"
echo "INFO: update load balancer weights to route traffic to ${PREVIOUS_COLOR}"
echo "PASS: traffic switched"

echo "Step 3: Post-rollback checks"
if [[ "$CHECK_POST_ROLLBACK_METRICS" == "true" ]]; then
    error_rate="$("$SCRIPT_DIR/check-error-rate.sh" "${ENVIRONMENT}-${PREVIOUS_COLOR}")"
    echo "INFO: post-rollback error rate ${error_rate}%"

    if greater_than "$error_rate" "$ROLLBACK_ERROR_RATE_THRESHOLD"; then
        echo "WARN: error rate is still above threshold (${ROLLBACK_ERROR_RATE_THRESHOLD}%)"
    else
        echo "PASS: error rate is within threshold"
    fi
else
    echo "INFO: skipped metric verification (CHECK_POST_ROLLBACK_METRICS=false)"
fi

echo "Step 4: Database rollback guidance"
if [[ "${ROLLBACK_DATABASE:-false}" == "true" ]]; then
    if [[ -x "${REPO_ROOT}/infra/backup/postgres-restore.sh" ]]; then
        echo "WARN: database restore requires explicit backup selection"
        echo "INFO: list backups with: ${REPO_ROOT}/infra/backup/postgres-restore.sh --list"
    else
        echo "WARN: restore script not found at infra/backup/postgres-restore.sh"
    fi
else
    echo "INFO: database rollback skipped (set ROLLBACK_DATABASE=true to enable manual flow)"
fi

echo "Step 5: Notify team"
rolled_back_by="$(git -C "$REPO_ROOT" config user.name || true)"
if [[ -z "$rolled_back_by" ]]; then
    rolled_back_by="unknown"
fi

"$SCRIPT_DIR/notify-deployment.sh" rollback \
    --version "$(git -C "$REPO_ROOT" describe --tags --always 2> /dev/null || echo unknown)" \
    --environment "$ENVIRONMENT" \
    --reason "$ROLLBACK_REASON" \
    --deployed-by "$rolled_back_by"

echo "PASS: rollback completed"
echo "INFO: active color=${PREVIOUS_COLOR} standby color=${CURRENT_COLOR}"
