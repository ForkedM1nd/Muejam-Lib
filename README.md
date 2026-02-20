# MueJam Library

MueJam Library is a production-focused monorepo for a serial fiction platform with integrated short-form social content (Whispers), moderation tooling, privacy controls, and mobile-ready API compatibility.

It combines:
- a Django + DRF backend API
- a React + Vite frontend
- centralized tests, docs, deployment scripts, and Terraform infrastructure

## At a Glance

- **Backend**: Django 5, DRF, PostgreSQL, Valkey, Celery
- **Frontend**: React 18, TypeScript, Vite, TanStack Query, Tailwind/shadcn
- **Infra/DevOps**: Docker Compose, Terraform, GitHub Actions
- **Security**: Clerk auth, 2FA support, rate limiting, content sanitization
- **Compatibility**: stable API under `/v1/...` with `/api/v1/...` compatibility routing

## Repository Layout

```text
muejam-library/
|- apps/
|  |- backend/            # Django API service
|  |- frontend/           # React web app (Vite)
|- docs/                  # Architecture, feature, dev, and ops docs
|- infra/                 # Terraform, IAM policies, infra assets
|- scripts/               # Deployment, database, verification automation
|- tests/                 # Centralized backend/frontend test suites
|- tools/                 # Engineering utilities
|- docker-compose.yml
`- pytest.ini
```

For deeper structure details, see [docs/architecture/monorepo-structure.md](docs/architecture/monorepo-structure.md).

## Quick Start (Recommended)

Use the dedicated run guide for the most reliable local setup:

- [Run Guide](docs/getting-started/run-guide.md)

In short, the recommended flow is:
1. Copy env templates for backend and frontend.
2. Start infra with Docker (`postgres`, `pgbouncer`, `valkey`).
3. Run backend locally on port `8000`.
4. Run frontend locally on port `8080`.

### Minimal command sequence

```bash
# from repo root
cp apps/backend/.env.example apps/backend/.env
cp apps/frontend/.env.example apps/frontend/.env.local
docker compose up -d postgres pgbouncer valkey
```

Then run backend and frontend in separate terminals:

```bash
# terminal 1
cd apps/backend
python -m venv .venv
# activate venv, then:
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

```bash
# terminal 2
cd apps/frontend
npm install
npm run dev
```

## Local Endpoints

- **Frontend**: `http://localhost:8080`
- **Backend health**: `http://localhost:8000/health/live`
- **API docs (Swagger)**: `http://localhost:8000/v1/docs/`
- **OpenAPI schema**: `http://localhost:8000/v1/schema/`

API compatibility note:
- canonical routes: `/v1/...`
- compatibility routes: `/api/v1/...`

## Common Development Commands

### Backend

```bash
cd apps/backend
python manage.py check
python manage.py collectstatic --noinput --dry-run
python -m pytest ../../tests/backend -q
```

### Frontend

```bash
cd apps/frontend
npm run lint
npm test
npm run build
```

### Infrastructure scripts

```bash
# examples
scripts/deployment/smoke-tests.sh staging
scripts/deployment/check-latency.sh production
scripts/deployment/check-error-rate.sh production
```

## Documentation Map

### Getting Started
- [docs/getting-started/run-guide.md](docs/getting-started/run-guide.md)
- [docs/getting-started/quickstart.md](docs/getting-started/quickstart.md)
- [docs/getting-started/development.md](docs/getting-started/development.md)

### Engineering Workflow
- [docs/development/setup.md](docs/development/setup.md)
- [docs/development/workflows.md](docs/development/workflows.md)
- [docs/development/testing.md](docs/development/testing.md)
- [docs/development/troubleshooting.md](docs/development/troubleshooting.md)

### Architecture and APIs
- [docs/architecture/system-architecture.md](docs/architecture/system-architecture.md)
- [docs/architecture/infrastructure.md](docs/architecture/infrastructure.md)
- [docs/architecture/api.md](docs/architecture/api.md)
- [docs/backend/mobile-api.md](docs/backend/mobile-api.md)

### Feature Documentation
- [Authentication](docs/features/authentication/two-factor-auth.md)
- [Moderation](docs/features/moderation/dashboard.md)
- [GDPR and Privacy](docs/features/gdpr/overview.md)
- [Security](docs/features/security/content-sanitizer.md)
- [Notifications](docs/features/notifications/overview.md)

### Deployment and Operations
- [docs/deployment/ci-cd.md](docs/deployment/ci-cd.md)
- [docs/deployment/verification.md](docs/deployment/verification.md)
- [docs/deployment/disaster-recovery.md](docs/deployment/disaster-recovery.md)
- [docs/operations/PRODUCTION_READINESS_REVIEW.md](docs/operations/PRODUCTION_READINESS_REVIEW.md)

## Quality and Production Readiness

The repository includes:
- deployment smoke tests and rollback automation in `scripts/deployment/`
- verification scripts in `scripts/verification/`
- infrastructure validation workflow in `.github/workflows/infra-devops.yml`

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a PR.

Expectations:
- keep changes scoped and atomic
- add/update tests with behavioral changes
- update docs when behavior, commands, or contracts change

## License

This repository currently does not publish a standalone license file.
Contact maintainers for usage and distribution permissions.
