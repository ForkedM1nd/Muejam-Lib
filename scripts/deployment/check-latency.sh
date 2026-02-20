#!/usr/bin/env bash
# Check current P99 latency from monitoring system.
# Usage: ./scripts/deployment/check-latency.sh <environment>

set -euo pipefail

ENVIRONMENT="${1:-production}"
FALLBACK_P99_MS="${LATENCY_FALLBACK_MS:-10000}"
HTTP_TIMEOUT_SECONDS="${MONITORING_TIMEOUT_SECONDS:-10}"
NEW_RELIC_API_KEY="${NEW_RELIC_API_KEY:-}"
NEW_RELIC_LATENCY_URL="${NEW_RELIC_LATENCY_URL:-https://api.newrelic.com/v2/applications/metrics.json}"

if [[ -z "$NEW_RELIC_API_KEY" ]]; then
    echo "$FALLBACK_P99_MS"
    exit 0
fi

if ! command -v curl > /dev/null 2>&1; then
    echo "$FALLBACK_P99_MS"
    exit 0
fi

payload="$(curl \
    --silent \
    --show-error \
    --fail \
    --max-time "$HTTP_TIMEOUT_SECONDS" \
    -H "X-Api-Key: ${NEW_RELIC_API_KEY}" \
    -H "Accept: application/json" \
    "${NEW_RELIC_LATENCY_URL}?environment=${ENVIRONMENT}" 2> /dev/null || true)"

if [[ -z "$payload" ]]; then
    echo "$FALLBACK_P99_MS"
    exit 0
fi

python_bin="$(command -v python3 || command -v python || true)"
if [[ -z "$python_bin" ]]; then
    echo "$FALLBACK_P99_MS"
    exit 0
fi

printf '%s' "$payload" | "$python_bin" - "$FALLBACK_P99_MS" <<'PY'
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


def pick_latency(obj):
    candidates = []

    if isinstance(obj, dict):
        candidates.extend([
            obj.get("p99"),
            obj.get("p99_latency"),
            obj.get("p99_latency_ms"),
        ])

        latency = obj.get("latency")
        if isinstance(latency, dict):
            candidates.extend([
                latency.get("p99"),
                latency.get("p95"),
            ])

        metric_data = obj.get("metric_data")
        if isinstance(metric_data, dict):
            metrics = metric_data.get("metrics")
            if isinstance(metrics, list) and metrics:
                first_metric = metrics[0]
                if isinstance(first_metric, dict):
                    timeslices = first_metric.get("timeslices")
                    if isinstance(timeslices, list) and timeslices:
                        values = timeslices[0].get("values", {})
                        if isinstance(values, dict):
                            candidates.extend([
                                values.get("p99"),
                                values.get("p95"),
                                values.get("average_response_time"),
                            ])

        series = obj.get("data")
        if isinstance(series, list) and series:
            last = series[-1]
            if isinstance(last, (list, tuple)) and len(last) >= 2:
                candidates.append(last[1])
            elif isinstance(last, dict):
                candidates.extend([
                    last.get("p99"),
                    last.get("value"),
                ])

    for candidate in candidates:
        number = as_float(candidate)
        if number is not None:
            print(f"{number:.2f}".rstrip("0").rstrip("."))
            return

    print(fallback)


pick_latency(data)
PY
