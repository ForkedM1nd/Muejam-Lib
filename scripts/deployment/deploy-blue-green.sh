#!/usr/bin/env bash
# Blue-green deployment script for MueJam Library.
# Usage: ./scripts/deployment/deploy-blue-green.sh <environment> <target-color>

set -euo pipefail

ENVIRONMENT="${1:-production}"
TARGET_COLOR="${2:-green}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
BACKEND_DIR="${REPO_ROOT}/apps/backend"

ERROR_RATE_THRESHOLD="${ERROR_RATE_THRESHOLD:-2.0}"
P99_LATENCY_THRESHOLD_MS="${P99_LATENCY_THRESHOLD_MS:-2000}"
MONITORING_DURATION_SECONDS="${MONITORING_DURATION_SECONDS:-300}"
MONITORING_POLL_INTERVAL_SECONDS="${MONITORING_POLL_INTERVAL_SECONDS:-30}"
TRAFFIC_SHIFT_STEPS="${TRAFFIC_SHIFT_STEPS:-10 25 50 75 100}"
HEALTH_CHECK_RETRIES="${HEALTH_CHECK_RETRIES:-30}"
HEALTH_CHECK_RETRY_INTERVAL_SECONDS="${HEALTH_CHECK_RETRY_INTERVAL_SECONDS:-10}"

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

rollback_and_exit() {
    local reason="$1"

    echo "FAIL: ${reason}"
    echo "INFO: triggering rollback"
    "$SCRIPT_DIR/rollback.sh" "$ENVIRONMENT" "$reason" --yes
    exit 1
}

if [[ "$ENVIRONMENT" != "staging" && "$ENVIRONMENT" != "production" ]]; then
    echo "FAIL: invalid environment '${ENVIRONMENT}' (expected staging or production)"
    exit 1
fi

if [[ "$TARGET_COLOR" != "blue" && "$TARGET_COLOR" != "green" ]]; then
    echo "FAIL: invalid target color '${TARGET_COLOR}' (expected blue or green)"
    exit 1
fi

if [[ -z "$PYTHON_BIN" ]]; then
    echo "FAIL: python is required for threshold comparisons"
    exit 1
fi

require_command git
require_command curl
require_command docker

if [[ "$TARGET_COLOR" == "green" ]]; then
    CURRENT_COLOR="blue"
else
    CURRENT_COLOR="green"
fi

TARGET_ENVIRONMENT_KEY="${ENVIRONMENT}-${TARGET_COLOR}"

echo "========================================"
echo "Blue-Green Deployment"
echo "Environment: ${ENVIRONMENT}"
echo "Current color: ${CURRENT_COLOR}"
echo "Target color: ${TARGET_COLOR}"
echo "========================================"

VERSION="$(git -C "$REPO_ROOT" describe --tags --always)"

echo "Step 1: Building target image"
echo "INFO: version ${VERSION}"
docker build \
    -t "muejam-backend:${VERSION}" \
    -f "${BACKEND_DIR}/Dockerfile" \
    "${BACKEND_DIR}"

TARGET_IMAGE="muejam-backend:${ENVIRONMENT}-${TARGET_COLOR}"
docker tag "muejam-backend:${VERSION}" "$TARGET_IMAGE"

if [[ -n "${CONTAINER_REGISTRY:-}" ]]; then
    REGISTRY_IMAGE="${CONTAINER_REGISTRY}/muejam-backend:${ENVIRONMENT}-${TARGET_COLOR}"
    docker tag "$TARGET_IMAGE" "$REGISTRY_IMAGE"
    docker push "$REGISTRY_IMAGE"
    echo "PASS: pushed image to ${REGISTRY_IMAGE}"
else
    echo "INFO: CONTAINER_REGISTRY not set; skipping image push"
fi

echo "Step 2: Database migrations"
if [[ "${RUN_MIGRATIONS:-false}" == "true" ]]; then
    (cd "$BACKEND_DIR" && python manage.py migrate --noinput)
    echo "PASS: migrations completed"
else
    echo "INFO: skipping migrations (set RUN_MIGRATIONS=true to enable)"
fi

echo "Step 3: Warm-up"
"$SCRIPT_DIR/warmup.sh" "$TARGET_ENVIRONMENT_KEY"

echo "Step 4: Health checks"
HEALTH_CHECK_URL="${HEALTH_CHECK_URL:-https://${TARGET_ENVIRONMENT_KEY}-api.muejam.com/health}"

for ((attempt = 1; attempt <= HEALTH_CHECK_RETRIES; attempt += 1)); do
    if curl --silent --show-error --fail --max-time 10 "$HEALTH_CHECK_URL" > /dev/null; then
        echo "PASS: health check succeeded (${HEALTH_CHECK_URL})"
        break
    fi

    if [[ "$attempt" -eq "$HEALTH_CHECK_RETRIES" ]]; then
        rollback_and_exit "health checks failed after ${HEALTH_CHECK_RETRIES} attempts"
    fi

    echo "INFO: health check attempt ${attempt}/${HEALTH_CHECK_RETRIES} failed, retrying"
    sleep "$HEALTH_CHECK_RETRY_INTERVAL_SECONDS"
done

echo "Step 5: Gradual traffic shift"
read -r -a traffic_percentages <<< "$TRAFFIC_SHIFT_STEPS"

for percentage in "${traffic_percentages[@]}"; do
    echo "INFO: shifting ${percentage}% traffic to ${TARGET_COLOR}"
    echo "INFO: apply weighted routing in ALB/ingress here"

    start_time="$(date +%s)"

    while true; do
        current_time="$(date +%s)"
        elapsed="$((current_time - start_time))"

        if (( elapsed >= MONITORING_DURATION_SECONDS )); then
            break
        fi

        error_rate="$("$SCRIPT_DIR/check-error-rate.sh" "$TARGET_ENVIRONMENT_KEY")"
        p99_latency="$("$SCRIPT_DIR/check-latency.sh" "$TARGET_ENVIRONMENT_KEY")"

        if greater_than "$error_rate" "$ERROR_RATE_THRESHOLD"; then
            rollback_and_exit "error rate ${error_rate}% exceeded ${ERROR_RATE_THRESHOLD}% at ${percentage}% traffic"
        fi

        if greater_than "$p99_latency" "$P99_LATENCY_THRESHOLD_MS"; then
            rollback_and_exit "p99 latency ${p99_latency}ms exceeded ${P99_LATENCY_THRESHOLD_MS}ms at ${percentage}% traffic"
        fi

        echo "INFO: metrics error_rate=${error_rate}% p99_latency=${p99_latency}ms elapsed=${elapsed}s/${MONITORING_DURATION_SECONDS}s"
        sleep "$MONITORING_POLL_INTERVAL_SECONDS"
    done

    echo "PASS: ${percentage}% traffic shift completed"
done

echo "Step 6: Final verification"
if ! "$SCRIPT_DIR/smoke-tests.sh" "$TARGET_ENVIRONMENT_KEY"; then
    rollback_and_exit "final smoke tests failed"
fi

echo "Step 7: Post-cutover state"
echo "INFO: keep ${CURRENT_COLOR} as standby for fast rollback"
echo "PASS: deployment completed"
echo "INFO: active color=${TARGET_COLOR} standby color=${CURRENT_COLOR}"
