#!/usr/bin/env bash
# Main deployment script for MueJam Library.
# Usage: ./scripts/deployment/deploy.sh <environment> [target-color]

set -euo pipefail

ENVIRONMENT="${1:-staging}"
TARGET_COLOR="${2:-green}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
BACKEND_DIR="${REPO_ROOT}/apps/backend"
FRONTEND_DIR="${REPO_ROOT}/apps/frontend"

RUN_CONFIG_VALIDATION="${RUN_CONFIG_VALIDATION:-true}"
RUN_BACKEND_TESTS="${RUN_BACKEND_TESTS:-true}"
RUN_FRONTEND_BUILD="${RUN_FRONTEND_BUILD:-true}"
RUN_MIGRATIONS="${RUN_MIGRATIONS:-true}"

require_command() {
    if ! command -v "$1" > /dev/null 2>&1; then
        echo "FAIL: required command '$1' is not installed"
        exit 1
    fi
}

if [[ "$ENVIRONMENT" != "development" && "$ENVIRONMENT" != "staging" && "$ENVIRONMENT" != "production" ]]; then
    echo "FAIL: invalid environment '${ENVIRONMENT}'"
    echo "Usage: ./scripts/deployment/deploy.sh <development|staging|production> [blue|green]"
    exit 1
fi

if [[ "$TARGET_COLOR" != "blue" && "$TARGET_COLOR" != "green" ]]; then
    echo "FAIL: target color must be 'blue' or 'green'"
    exit 1
fi

require_command git
require_command python
require_command curl

if [[ "$RUN_FRONTEND_BUILD" == "true" ]]; then
    require_command npm
fi

echo "========================================"
echo "MueJam deployment"
echo "Environment: ${ENVIRONMENT}"
echo "Target color: ${TARGET_COLOR}"
echo "========================================"

echo "Step 1: Pre-deployment checks"
current_branch="$(git -C "$REPO_ROOT" branch --show-current)"

if [[ "$ENVIRONMENT" == "production" && "$current_branch" != "master" && "$current_branch" != "main" ]]; then
    echo "FAIL: production deployments must run from 'master' or 'main'"
    echo "INFO: current branch is '${current_branch}'"
    exit 1
fi

if [[ -n "$(git -C "$REPO_ROOT" status --porcelain)" ]]; then
    echo "FAIL: uncommitted changes detected"
    git -C "$REPO_ROOT" status --short
    exit 1
fi

echo "PASS: repository checks passed"

if [[ "$RUN_CONFIG_VALIDATION" == "true" ]]; then
    echo "Step 2: Configuration validation"
    (cd "$BACKEND_DIR" && python manage.py validate_config --environment "$ENVIRONMENT" --no-fail)
    echo "PASS: configuration validation completed"
else
    echo "Step 2: Skipped configuration validation"
fi

echo "Step 3: Quality gates"
if [[ "$RUN_BACKEND_TESTS" == "true" ]]; then
    (cd "$BACKEND_DIR" && python -m pytest ../../tests/backend/unit ../../tests/backend/integration -q)
    echo "PASS: backend unit/integration tests passed"
else
    echo "INFO: skipped backend tests (RUN_BACKEND_TESTS=false)"
fi

if [[ "$RUN_FRONTEND_BUILD" == "true" ]]; then
    (cd "$FRONTEND_DIR" && npm run build)
    echo "PASS: frontend build passed"
else
    echo "INFO: skipped frontend build (RUN_FRONTEND_BUILD=false)"
fi

(cd "$BACKEND_DIR" && python manage.py check)
(cd "$BACKEND_DIR" && python manage.py collectstatic --noinput --dry-run)
echo "PASS: backend runtime checks passed"

echo "Step 4: Database migration checks"
if [[ "$RUN_MIGRATIONS" == "true" ]]; then
    pending_migrations="$(cd "$BACKEND_DIR" && python manage.py showmigrations | grep "\[ \]" | wc -l)"

    if [[ "$pending_migrations" -gt 0 ]]; then
        echo "INFO: found ${pending_migrations} pending migrations"

        if [[ "$ENVIRONMENT" == "production" ]]; then
            "$SCRIPT_DIR/backup-database.sh" "$ENVIRONMENT"
        fi

        (cd "$BACKEND_DIR" && python manage.py migrate --noinput)
        echo "PASS: migrations completed"
    else
        echo "PASS: no pending migrations"
    fi
else
    echo "INFO: skipped migrations (RUN_MIGRATIONS=false)"
fi

echo "Step 5: Deploying application"
if [[ "$ENVIRONMENT" == "development" ]]; then
    echo "INFO: development deploy keeps current local workflow"
    echo "INFO: run docker compose up -d if you want containerized local services"
else
    "$SCRIPT_DIR/deploy-blue-green.sh" "$ENVIRONMENT" "$TARGET_COLOR"
fi

echo "Step 6: Post-deployment smoke tests"
smoke_target="${SMOKE_TEST_TARGET:-${ENVIRONMENT}-${TARGET_COLOR}}"
if [[ "$ENVIRONMENT" == "development" ]]; then
    smoke_target="${SMOKE_TEST_TARGET:-development}"
fi
"$SCRIPT_DIR/smoke-tests.sh" "$smoke_target"

echo "Step 7: Notifications"
deployed_by="$(git -C "$REPO_ROOT" config user.name || true)"
if [[ -z "$deployed_by" ]]; then
    deployed_by="unknown"
fi

"$SCRIPT_DIR/notify-deployment.sh" success \
    --version "$(git -C "$REPO_ROOT" describe --tags --always)" \
    --environment "$ENVIRONMENT" \
    --deployed-by "$deployed_by"

echo "PASS: deployment completed successfully"
