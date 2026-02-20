#!/usr/bin/env bash
# Warm up application by sending test traffic
# Usage: ./scripts/deployment/warmup.sh <environment-or-base-url>

set -euo pipefail

TARGET="${1:-staging}"
BASE_URL="${DEPLOYMENT_BASE_URL:-}"
REQUESTS_PER_ENDPOINT="${WARMUP_REQUESTS_PER_ENDPOINT:-10}"
HTTP_TIMEOUT_SECONDS="${WARMUP_TIMEOUT_SECONDS:-8}"

require_command() {
    if ! command -v "$1" > /dev/null 2>&1; then
        echo "FAIL: required command '$1' is not installed"
        exit 1
    fi
}

resolve_base_url() {
    if [[ -n "$BASE_URL" ]]; then
        return
    fi

    if [[ "$TARGET" =~ ^https?:// ]]; then
        BASE_URL="$TARGET"
        return
    fi

    case "$TARGET" in
        production)
            BASE_URL="https://api.muejam.com"
            ;;
        staging)
            BASE_URL="https://staging-api.muejam.com"
            ;;
        development|dev|local)
            BASE_URL="http://localhost:8000"
            ;;
        *)
            BASE_URL="https://${TARGET}-api.muejam.com"
            ;;
    esac
}

main() {
    local health_code
    local endpoint
    local i

    require_command curl
    resolve_base_url

    if [[ ! "$REQUESTS_PER_ENDPOINT" =~ ^[0-9]+$ ]] || [[ "$REQUESTS_PER_ENDPOINT" -lt 1 ]]; then
        echo "FAIL: WARMUP_REQUESTS_PER_ENDPOINT must be a positive integer"
        exit 1
    fi

    health_code="$(curl \
        --silent \
        --show-error \
        --location \
        --max-time "$HTTP_TIMEOUT_SECONDS" \
        --output /dev/null \
        --write-out "%{http_code}" \
        "${BASE_URL}/health")"

    if [[ "$health_code" != "200" ]]; then
        echo "FAIL: cannot warm up ${BASE_URL} (health returned HTTP ${health_code})"
        exit 1
    fi

    echo "Warming up ${BASE_URL} with ${REQUESTS_PER_ENDPOINT} requests per endpoint"

    for endpoint in "/health" "/health/ready" "/v1/health/" "/v1/stories/" "/v1/whispers/"; do
        echo "Warming endpoint ${endpoint}"
        for ((i = 1; i <= REQUESTS_PER_ENDPOINT; i += 1)); do
            curl \
                --silent \
                --show-error \
                --location \
                --max-time "$HTTP_TIMEOUT_SECONDS" \
                --output /dev/null \
                "${BASE_URL}${endpoint}" > /dev/null 2>&1 || true &
        done
    done

    wait

    echo "PASS: warm-up completed"
}

main
