# Run Guide

This guide is the fastest reliable way to run MueJam Library locally.

It uses:
- Docker for infrastructure services (PostgreSQL, PgBouncer, Valkey)
- Native local processes for backend and frontend development servers

## Prerequisites

- Docker Desktop (or Docker Engine + Compose plugin)
- Python 3.11+
- Node.js 18+

## 1) Prepare environment files

From the repository root:

```bash
cp apps/backend/.env.example apps/backend/.env
cp apps/frontend/.env.example apps/frontend/.env.local
```

Generate a backend secret key:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Update `apps/backend/.env` with at least:

```env
SECRET_KEY=<paste-generated-key>
DEBUG=True

# Use local infra started by Docker
DATABASE_URL=postgresql://muejam_user:muejam_password@localhost:6432/muejam
VALKEY_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Frontend origin
FRONTEND_URL=http://localhost:8080
CORS_ALLOWED_ORIGINS=http://localhost:8080
```

Update `apps/frontend/.env.local`:

```env
VITE_API_BASE_URL=http://localhost:8000/v1
```

## 2) Start infrastructure services

```bash
docker compose up -d postgres pgbouncer valkey
```

Optional health check:

```bash
docker compose ps
```

## 3) Run backend (terminal 1)

```bash
cd apps/backend
python -m venv .venv
```

Activate virtual environment:

- PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

- Bash:

```bash
source .venv/bin/activate
```

Install dependencies and run:

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

## 4) Run frontend (terminal 2)

```bash
cd apps/frontend
npm install
npm run dev
```

The Vite dev server runs on:

- Frontend: `http://localhost:8080`

## 5) Verify everything is up

Check backend endpoints:

```bash
curl http://localhost:8000/health/live
curl http://localhost:8000/v1/health/live/
curl http://localhost:8000/api/v1/health/live/
```

Open in browser:

- Frontend: `http://localhost:8080`
- Backend API docs: `http://localhost:8000/v1/docs/`

## Stop services

- Stop app servers: `Ctrl+C` in each terminal
- Stop infra containers:

```bash
docker compose down
```

## Troubleshooting

- **Backend cannot connect to DB**: confirm `DATABASE_URL` uses `localhost:6432` and run `docker compose ps`
- **Frontend cannot reach backend**: confirm `VITE_API_BASE_URL=http://localhost:8000/v1`
- **Port already in use**: free the port or change it in your local config

For deeper setup and workflow details, see:
- [Quickstart Guide](./quickstart.md)
- [Development Guide](./development.md)
