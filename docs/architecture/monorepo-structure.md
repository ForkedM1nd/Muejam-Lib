# Monorepo Structure

This document describes the organization and structure of the MueJam Library monorepo.

## Overview

MueJam Library is organized as a monorepo containing multiple related projects (backend, frontend) with shared documentation, tests, scripts, and infrastructure code. This structure provides clear separation of concerns while maintaining cohesion.

## Top-Level Structure

```
muejam-library/
├── apps/              # Deployable applications
├── packages/          # Shared libraries
├── docs/              # All documentation
├── tests/             # Centralized test suites
├── scripts/           # Automation and utility scripts
├── infra/             # Infrastructure as code
├── tools/             # Development tools
├── .github/           # GitHub configuration
├── docker-compose.yml # Local development orchestration
├── .gitignore         # Git ignore patterns
├── README.md          # Project overview
└── CONTRIBUTING.md    # Contribution guidelines
```

## Apps Directory

Contains deployable applications.

```
apps/
├── backend/           # Django REST API
│   ├── apps/          # Django applications
│   ├── config/        # Django settings
│   ├── infrastructure/# Infrastructure code
│   ├── prisma/        # Prisma schema
│   ├── manage.py      # Django management
│   ├── requirements.txt
│   ├── pytest.ini
│   ├── Dockerfile
│   └── .env.example
└── frontend/          # React application
    ├── src/           # Source code
    ├── public/        # Static assets
    ├── package.json
    ├── vite.config.ts
    ├── Dockerfile
    └── .env.example
```

### Backend Structure

```
apps/backend/
├── apps/              # Django apps (feature modules)
│   ├── admin/         # Admin features
│   ├── analytics/     # Analytics and metrics
│   ├── backup/        # Backup and recovery
│   ├── core/          # Core functionality
│   ├── discovery/     # Content discovery
│   ├── gdpr/          # GDPR compliance
│   ├── help/          # Help system
│   ├── highlights/    # Text highlights
│   ├── legal/         # Legal documents
│   ├── library/       # User libraries
│   ├── moderation/    # Content moderation
│   ├── notifications/ # Notifications
│   ├── onboarding/    # User onboarding
│   ├── search/        # Search functionality
│   ├── security/      # Security features
│   ├── social/        # Social features
│   ├── status/        # System status
│   ├── stories/       # Story management
│   ├── uploads/       # File uploads
│   ├── users/         # User management
│   └── whispers/      # Comments system
├── config/            # Django configuration
│   ├── settings.py    # Main settings
│   ├── urls.py        # URL routing
│   └── wsgi.py        # WSGI config
└── infrastructure/    # Infrastructure code
    ├── caching/       # Cache management
    ├── monitoring/    # Monitoring and metrics
    ├── database/      # Database utilities
    ├── logging/       # Logging configuration
    └── health/        # Health checks
```

Each Django app follows this structure:

```
apps/backend/apps/example/
├── __init__.py
├── apps.py            # App configuration
├── models.py          # Database models
├── serializers.py     # API serializers
├── views.py           # API views
├── urls.py            # URL routing
├── admin.py           # Django admin
├── permissions.py     # Permissions
├── services.py        # Business logic
├── tasks.py           # Celery tasks
├── migrations/        # Database migrations
└── tests/             # Colocated tests
    ├── __init__.py
    ├── test_models.py
    ├── test_views.py
    └── test_services.py
```

### Frontend Structure

```
apps/frontend/
├── src/
│   ├── components/    # React components
│   │   ├── auth/
│   │   ├── legal/
│   │   ├── stories/
│   │   └── ...
│   ├── hooks/         # Custom React hooks
│   ├── api/           # API client code
│   ├── utils/         # Utility functions
│   ├── types/         # TypeScript types
│   ├── styles/        # Global styles
│   ├── App.tsx        # Root component
│   └── main.tsx       # Entry point
├── public/            # Static assets
│   ├── index.html
│   └── favicon.ico
└── __tests__/         # Test files
```

## Packages Directory

Shared libraries and reusable code (future use).

```
packages/
├── shared-types/      # Shared TypeScript types
├── shared-utils/      # Shared utility functions
└── README.md          # Package organization guide
```

## Docs Directory

All project documentation organized by domain.

```
docs/
├── architecture/      # System design and architecture
│   ├── monorepo-structure.md
│   ├── infrastructure.md
│   ├── alerting.md
│   ├── apm.md
│   ├── cdn.md
│   ├── database-cache.md
│   ├── image-optimization.md
│   ├── logging.md
│   ├── read-replicas.md
│   ├── search.md
│   └── sentry.md
├── backend/           # Backend-specific docs
│   └── rate-limiting.md
├── frontend/          # Frontend-specific docs
├── features/          # Feature documentation
│   ├── authentication/
│   ├── gdpr/
│   ├── moderation/
│   ├── security/
│   └── ...
├── development/       # Developer guides
│   ├── setup.md
│   ├── conventions.md
│   ├── testing.md
│   ├── workflows.md
│   └── troubleshooting.md
├── deployment/        # Deployment and operations
│   ├── migration-guide.md
│   ├── verification.md
│   ├── ci-cd.md
│   ├── checklist.md
│   ├── disaster-recovery.md
│   ├── infrastructure.md
│   └── secrets-management.md
├── archive/           # Historical artifacts
│   ├── ai-artifacts/  # AI-generated docs
│   ├── INDEX.md       # Archive index
│   └── README.md      # Archive purpose
└── README.md          # Documentation index
```

## Tests Directory

Centralized test suites for integration and end-to-end tests.

```
tests/
├── backend/
│   ├── integration/   # Integration tests
│   ├── e2e/           # End-to-end tests
│   └── infrastructure/# Infrastructure tests
│       ├── test_config_validator.py
│       ├── test_secrets_manager.py
│       └── test_audit_log_integration.py
├── frontend/
│   ├── integration/   # Integration tests
│   └── e2e/           # End-to-end tests
└── README.md          # Test organization guide
```

Note: Unit tests are colocated with the code they test (e.g., `apps/backend/apps/users/tests/`).

## Scripts Directory

Automation and utility scripts organized by purpose.

```
scripts/
├── database/          # Database utilities
│   ├── seed-data.py
│   └── seed-legal-documents.py
├── deployment/        # Deployment scripts
│   ├── backup-database.sh
│   ├── check-error-rate.sh
│   ├── check-latency.sh
│   ├── create-release.sh
│   ├── deploy-blue-green.sh
│   ├── deploy.sh
│   ├── maintenance-mode.sh
│   ├── notify-deployment.sh
│   ├── rollback.sh
│   ├── smoke-tests.sh
│   └── warmup.sh
├── verification/      # Verification scripts
│   ├── check-db.py
│   ├── verify-ratelimit-setup.py
│   ├── verify-security-headers.py
│   └── verify-restructure.py
└── README.md          # Scripts documentation
```

## Infra Directory

Infrastructure as code and configuration.

```
infra/
├── terraform/         # Terraform configurations
│   ├── environments/
│   │   ├── dev/
│   │   ├── staging/
│   │   └── production/
│   └── modules/
│       └── cloudfront/
├── iam-policies/      # IAM policy documents
│   ├── secrets-manager-policy.json
│   └── README.md
├── monitoring/        # Monitoring configurations
└── README.md          # Infrastructure docs
```

## Tools Directory

Development tools and utilities.

```
tools/
├── restructure/       # Restructuring automation
│   ├── migration_tool.py
│   ├── file_tracker.py
│   ├── config_updater.py
│   └── validator.py
└── README.md
```

## Design Principles

### 1. Separation of Concerns

- **Apps**: Deployable applications
- **Docs**: All documentation
- **Tests**: Test suites
- **Scripts**: Automation
- **Infra**: Infrastructure code

Each directory has a single, clear purpose.

### 2. Colocated Tests

Django app tests are colocated within the app directory:
- Easier to find tests for specific code
- Clear ownership
- Follows Django conventions

Integration and E2E tests are centralized in `tests/` directory.

### 3. Feature-Based Organization

Backend apps are organized by feature/domain:
- `apps/users/` - User management
- `apps/moderation/` - Content moderation
- `apps/gdpr/` - GDPR compliance

This makes it easy to understand what each app does.

### 4. Infrastructure Separation

True infrastructure code (caching, monitoring, database config) stays in `apps/backend/infrastructure/`.

Feature code that was mistakenly in infrastructure has been moved to appropriate apps:
- Account suspension → `apps/users/`
- Shadowban → `apps/moderation/`
- Audit logs → `apps/admin/`
- Suspicious activity → `apps/security/`

### 5. Documentation Consolidation

All documentation in one place (`docs/`) with clear hierarchy:
- Easy to find information
- Single source of truth
- Better for documentation tools

### 6. Naming Conventions

- **Top-level directories**: kebab-case (`docs/`, `scripts/`)
- **Django apps**: snake_case (`apps/users/`, `apps/two_factor_auth/`)
- **Python modules**: snake_case (`user_service.py`)
- **TypeScript components**: PascalCase (`UserProfile.tsx`)

## Benefits of This Structure

### For Developers

- **Clear organization**: Easy to find code and documentation
- **Consistent patterns**: Similar structure across apps
- **Easier onboarding**: New developers can navigate quickly
- **Better tooling**: IDEs work better with clear structure

### For Operations

- **Deployment independence**: Apps can be deployed separately
- **Clear infrastructure**: IaC in dedicated directory
- **Automation**: Scripts organized by purpose
- **Monitoring**: Clear separation of concerns

### For Maintenance

- **Easier refactoring**: Clear boundaries between components
- **Better testing**: Tests organized by type and scope
- **Documentation**: Easy to keep docs up to date
- **Scalability**: Structure supports growth

## Migration from Old Structure

The repository was restructured from an organic growth state. See [Migration Guide](../deployment/migration-guide.md) for complete details of what changed.

Key changes:
- AI artifacts archived
- Documentation consolidated
- Scripts organized by purpose
- Infrastructure code separated
- Tests organized by type

## Future Considerations

### Packages

As shared code emerges, extract it to `packages/`:
- Shared TypeScript types
- Common utility functions
- Reusable components

### Microservices

If the monolith needs to be split:
- Each service becomes a new app in `apps/`
- Shared code moves to `packages/`
- Infrastructure remains in `infra/`

### Monorepo Tools

Consider adopting monorepo tools as the project grows:
- **Nx**: Build system and monorepo tools
- **Turborepo**: High-performance build system
- **Lerna**: Multi-package repository management

## Resources

- [Monorepo Best Practices](https://monorepo.tools/)
- [Django Project Structure](https://docs.djangoproject.com/en/stable/intro/reusable-apps/)
- [React Project Structure](https://react.dev/learn/thinking-in-react)
- [Infrastructure as Code](https://www.terraform.io/docs)
