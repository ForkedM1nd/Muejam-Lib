# MueJam Library

A minimal digital library platform for serial stories with an integrated micro-posting system called "Whispers".

## Project Structure

This is a monorepo containing multiple applications, shared packages, documentation, and infrastructure:

```
muejam-library/
├── apps/              # Deployable applications
│   ├── backend/       # Django REST API
│   └── frontend/      # React application
├── packages/          # Shared libraries (future use)
├── docs/              # All documentation
│   ├── architecture/  # System design
│   ├── features/      # Feature documentation
│   ├── development/   # Developer guides
│   └── deployment/    # Deployment guides
├── tests/             # Centralized test suites
│   ├── backend/       # Backend integration tests
│   └── frontend/      # Frontend integration tests
├── scripts/           # Automation scripts
│   ├── database/      # Database utilities
│   ├── deployment/    # Deployment scripts
│   └── verification/  # Verification scripts
├── infra/             # Infrastructure as code
│   ├── terraform/     # Terraform configurations
│   └── iam-policies/  # IAM policies
└── tools/             # Development tools
```

For detailed structure documentation, see [Monorepo Structure](docs/architecture/monorepo-structure.md).

## Quick Start

### Prerequisites

- Docker and Docker Compose V2
- Git

### Running the Application

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd muejam-library
   ```

2. Start all services with Docker Compose:
   ```bash
   docker-compose up
   ```

3. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000/api
   - API Documentation: http://localhost:8000/api/schema/swagger-ui/

### Development Setup

For detailed development setup instructions, see:
- [Development Setup Guide](docs/development/setup.md)
- [Contributing Guidelines](CONTRIBUTING.md)

## Features

- **Serial Fiction Library**: Browse, read, and manage serial stories
- **Whispers**: Micro-posting system for short updates and thoughts
- **User Authentication**: Secure authentication with Clerk
- **Content Moderation**: Automated and manual content moderation
- **GDPR Compliance**: Data export, deletion, and privacy controls
- **Two-Factor Authentication**: Enhanced security with TOTP
- **Responsive Design**: Works on desktop and mobile devices
- **RESTful API**: Clean API design with comprehensive documentation

## Technology Stack

### Backend
- Django 5.0.1 with Django REST Framework
- PostgreSQL 15 database
- Prisma ORM
- Valkey (Redis-compatible) for caching
- Celery for background tasks
- Clerk for authentication

### Frontend
- React 18 with TypeScript
- Vite build tool
- TanStack Query for data fetching
- React Router for navigation
- Tailwind CSS + shadcn/ui for styling

### Infrastructure
- Docker & Docker Compose
- AWS (ECS, RDS, S3, CloudFront)
- Terraform for IaC
- GitHub Actions for CI/CD

## Documentation

### Getting Started
- [Development Setup](docs/development/setup.md)
- [Coding Conventions](docs/development/conventions.md)
- [Testing Guide](docs/development/testing.md)
- [Development Workflows](docs/development/workflows.md)
- [Troubleshooting](docs/development/troubleshooting.md)

### Architecture
- [Monorepo Structure](docs/architecture/monorepo-structure.md)
- [Infrastructure Architecture](docs/architecture/infrastructure.md)

### Features
- [Authentication](docs/features/authentication/)
- [Moderation](docs/features/moderation/)
- [GDPR Compliance](docs/features/gdpr/)
- [Security Features](docs/features/security/)

### Deployment
- [Migration Guide](docs/deployment/migration-guide.md)
- [Deployment Verification](docs/deployment/verification.md)
- [CI/CD Pipeline](docs/deployment/ci-cd.md)

## Development

### Backend Development

```bash
cd apps/backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your configuration
python manage.py migrate
python manage.py runserver
```

### Frontend Development

```bash
cd apps/frontend
npm install
cp .env.example .env.local
# Edit .env.local with your configuration
npm run dev
```

### Running Tests

Backend tests:
```bash
cd apps/backend
python -m pytest
```

Frontend tests:
```bash
cd apps/frontend
npm test
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Key points:
- Follow our [coding conventions](docs/development/conventions.md)
- Write tests for new features
- Update documentation as needed
- Submit pull requests with clear descriptions

## License

See [LICENSE](LICENSE) for details.
