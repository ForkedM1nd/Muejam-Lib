#!/usr/bin/env bash
# Smoke tests for post-deployment verification
# Usage: ./scripts/deployment/smoke-tests.sh <environment-or-base-url>

set -euo pipefail

TARGET="${1:-staging}"
BASE_URL="${DEPLOYMENT_BASE_URL:-}"
HTTP_TIMEOUT_SECONDS="${SMOKE_TEST_TIMEOUT_SECONDS:-10}"

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

check_http_status() {
    local name="$1"
    local path="$2"
    local expected_status="$3"
    local status_code

    status_code="$(curl \
        --silent \
        --show-error \
        --location \
        --max-time "$HTTP_TIMEOUT_SECONDS" \
        --output /dev/null \
        --write-out "%{http_code}" \
        "${BASE_URL}${path}")"

    if [[ "$status_code" != "$expected_status" ]]; then
        echo "FAIL: ${name} returned HTTP ${status_code}, expected ${expected_status}"
        return 1
    fi

    echo "PASS: ${name}"
}

check_dependency_health() {
    local payload
    local python_bin

    payload="$(curl \
        --silent \
        --show-error \
        --location \
        --max-time "$HTTP_TIMEOUT_SECONDS" \
        "${BASE_URL}/health")"

    python_bin="$(command -v python3 || command -v python || true)"
    if [[ -z "$python_bin" ]]; then
        echo "WARN: python is not available; skipping dependency status checks"
        return 0
    fi

    if ! printf '%s' "$payload" | "$python_bin" - <<'PY'
import json
import sys

try:
    data = json.load(sys.stdin)
except Exception as exc:
    print(f"FAIL: /health returned invalid JSON: {exc}")
    raise SystemExit(1)

checks = data.get("checks", {})
database_status = checks.get("database", {}).get("status")
cache_status = checks.get("cache", {}).get("status")

if database_status != "healthy" or cache_status != "healthy":
    print(
        "FAIL: dependency checks unhealthy "
        f"(database={database_status}, cache={cache_status})"
    )
    raise SystemExit(1)

print("PASS: dependency checks healthy")
PY
    then
        return 1
    fi
}

main() {
    require_command curl
    resolve_base_url

    echo "Running smoke tests against ${BASE_URL}"

    check_http_status "platform health endpoint" "/health" "200"
    check_dependency_health
    check_http_status "readiness endpoint" "/health/ready" "200"
    check_http_status "versioned health endpoint" "/v1/health/" "200"

    echo "PASS: all smoke tests passed"
}

main
