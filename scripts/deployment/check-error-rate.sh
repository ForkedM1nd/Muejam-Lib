#!/usr/bin/env bash
# Check current error rate from monitoring system.
# Usage: ./scripts/deployment/check-error-rate.sh <environment>

set -euo pipefail

ENVIRONMENT="${1:-production}"
FALLBACK_ERROR_RATE="${ERROR_RATE_FALLBACK:-100}"
HTTP_TIMEOUT_SECONDS="${MONITORING_TIMEOUT_SECONDS:-10}"
SENTRY_API_TOKEN="${SENTRY_API_TOKEN:-}"
SENTRY_ERROR_RATE_URL="${SENTRY_ERROR_RATE_URL:-https://api.sentry.io/api/0/organizations/muejam/stats/}"

if [[ -z "$SENTRY_API_TOKEN" ]]; then
    echo "$FALLBACK_ERROR_RATE"
    exit 0
fi

if ! command -v curl > /dev/null 2>&1; then
    echo "$FALLBACK_ERROR_RATE"
    exit 0
fi

payload="$(curl \
    --silent \
    --show-error \
    --fail \
    --max-time "$HTTP_TIMEOUT_SECONDS" \
    -H "Authorization: Bearer ${SENTRY_API_TOKEN}" \
    -H "Accept: application/json" \
    "${SENTRY_ERROR_RATE_URL}?environment=${ENVIRONMENT}" 2> /dev/null || true)"

if [[ -z "$payload" ]]; then
    echo "$FALLBACK_ERROR_RATE"
    exit 0
fi

python_bin="$(command -v python3 || command -v python || true)"
if [[ -z "$python_bin" ]]; then
    echo "$FALLBACK_ERROR_RATE"
    exit 0
fi

printf '%s' "$payload" | "$python_bin" - "$FALLBACK_ERROR_RATE" <<'PY'
import json
import sys

fallback = sys.argv[1]

try:
    data = json.load(sys.stdin)
except Exception:
    print(fallback)
    raise SystemExit(0)


def as_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def pick_rate(obj):
    candidates = []

    if isinstance(obj, dict):
        candidates.extend([
            obj.get("error_rate"),
            obj.get("rate"),
            obj.get("value"),
        ])

        errors = obj.get("errors")
        if isinstance(errors, dict):
            candidates.extend([
                errors.get("rate"),
                errors.get("error_rate"),
            ])

        stats = obj.get("stats")
        if isinstance(stats, dict):
            candidates.extend([
                stats.get("error_rate"),
                stats.get("rate"),
            ])

        metric_data = obj.get("metric_data")
        if isinstance(metric_data, dict):
            candidates.extend([
                metric_data.get("error_rate"),
                metric_data.get("rate"),
            ])

        series = obj.get("data")
        if isinstance(series, list) and series:
            last = series[-1]
            if isinstance(last, (list, tuple)) and len(last) >= 2:
                candidates.append(last[1])
            elif isinstance(last, dict):
                candidates.extend([
                    last.get("error_rate"),
                    last.get("rate"),
                    last.get("value"),
                ])

    for candidate in candidates:
        number = as_float(candidate)
        if number is not None:
            if 0 <= number <= 1:
                number *= 100
            print(f"{number:.4f}".rstrip("0").rstrip("."))
            return

    print(fallback)


pick_rate(data)
PY
