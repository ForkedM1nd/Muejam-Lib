# MueJam Library Documentation

Welcome to the MueJam Library documentation. This directory contains comprehensive documentation for the project.

## Documentation Structure

### Getting Started
- [Quickstart Guide](getting-started/quickstart.md) - Get up and running quickly
- [Development Guide](getting-started/development.md) - Detailed development setup and workflows

### Architecture
- [API Documentation](architecture/api.md) - REST API endpoints and usage

### Backend
#### Infrastructure
- [Infrastructure Overview](backend/infrastructure/overview.md) - Database optimization and caching infrastructure
- [Deployment Guide](backend/infrastructure/deployment-guide.md) - Production deployment instructions
- [Operations Runbook](backend/infrastructure/operations-runbook.md) - Operational procedures and troubleshooting
- [Tuning Guide](backend/infrastructure/tuning-guide.md) - Performance tuning and optimization
- [Database Replication Setup](backend/infrastructure/database-replication-setup.md) - Setting up database replication
- [Query Optimizer Integration](backend/infrastructure/query-optimizer-integration.md) - Query optimization guide
- [Schema Manager Integration](backend/infrastructure/schema-manager-integration.md) - Schema management guide
- [Rate Limiting Guide](backend/infrastructure/rate-limiting-guide.md) - Rate limiting configuration
- [Valkey Configuration](backend/infrastructure/valkey-configuration.md) - Valkey cache configuration
- [Django Integration](backend/infrastructure/django-integration.md) - Django integration guide

#### Monitoring
- [Monitoring Overview](backend/monitoring/overview.md) - Monitoring setup and architecture
- [Configuration Guide](backend/monitoring/configuration-guide.md) - Monitoring configuration details

#### Django Apps
- [Users App](backend/apps/users.md) - User management and authentication
- [Password Reset](backend/apps/password-reset.md) - Password reset functionality

### Frontend
- [Authentication Guide](frontend/authentication.md) - Complete authentication documentation
- [API Client](frontend/api-client.md) - Frontend API integration guide
- [Setup Guide](frontend/setup.md) - Detailed frontend setup instructions

### Deployment
- [Secrets Management](deployment/secrets.md) - Managing secrets and environment variables

## Quick Links

- [Main README](../README.md) - Project overview and quick start
- [Contributing Guidelines](../CONTRIBUTING.md) - How to contribute to the project
- [Docker Compose](../docker-compose.yml) - Container orchestration configuration

## Project Structure

```
muejam-library/
├── apps/              # Applications
│   ├── backend/       # Django REST API
│   └── frontend/      # React frontend
├── packages/          # Shared libraries (future)
├── tools/             # Build tools and scripts
├── docs/              # Documentation (you are here)
└── tests/             # Integration tests
```

## Additional Resources

- Backend API: http://localhost:8000/api/
- Frontend App: http://localhost:5173/
- API Documentation: http://localhost:8000/api/docs/
