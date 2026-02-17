# Development Guide

## Quick Start

### Using Setup Scripts

**Linux/Mac:**
```bash
chmod +x setup.sh
./setup.sh
```

**Windows (PowerShell):**
```powershell
.\setup.ps1
```

### Manual Setup

1. **Copy environment files:**
```bash
cp apps/backend/.env.example apps/backend/.env
cp apps/frontend/.env.example apps/frontend/.env.local
```

2. **Update credentials in `.env` files:**
   - Add your Clerk API keys
   - Add AWS S3 credentials
   - Add Resend API key

3. **Start services:**
```bash
docker-compose up -d
```

4. **Run database migrations:**
```bash
docker-compose exec backend python manage.py migrate
```

## Development Workflow

### Starting Services

Start all services:
```bash
docker-compose up -d
```

View logs:
```bash
docker-compose logs -f
```

Stop services:
```bash
docker-compose down
```

### Backend Development

#### Running Django Commands

```bash
# Run migrations
docker-compose exec backend python manage.py migrate

# Create superuser
docker-compose exec backend python manage.py createsuperuser

# Generate Prisma client
docker-compose exec backend prisma generate

# Run tests
docker-compose exec backend pytest

# Run specific test
docker-compose exec backend pytest apps/users/tests/test_profile.py
```

#### Local Backend Development (without Docker)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Update .env to use localhost instead of container names
# DATABASE_URL=postgresql://muejam_user:muejam_password@localhost:5432/muejam
# VALKEY_URL=redis://localhost:6379/0

python manage.py runserver
```

#### Running Celery Locally

```bash
# Worker
celery -A config worker --loglevel=info

# Beat scheduler
celery -A config beat --loglevel=info
```

### Frontend Development

#### Running Next.js Commands

```bash
# Install dependencies
docker-compose exec frontend npm install

# Run linter
docker-compose exec frontend npm run lint

# Build for production
docker-compose exec frontend npm run build
```

#### Local Frontend Development (without Docker)

```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at http://localhost:3000

### Database Management

#### Accessing PostgreSQL

```bash
docker-compose exec postgres psql -U muejam_user -d muejam
```

#### Backup Database

```bash
docker-compose exec postgres pg_dump -U muejam_user muejam > backup.sql
```

#### Restore Database

```bash
cat backup.sql | docker-compose exec -T postgres psql -U muejam_user -d muejam
```

### Valkey/Redis Management

#### Accessing Valkey CLI

```bash
docker-compose exec valkey valkey-cli
```

#### Clear Cache

```bash
docker-compose exec valkey valkey-cli FLUSHALL
```

## Testing

### Backend Tests

Run all tests:
```bash
docker-compose exec backend pytest
```

Run with coverage:
```bash
docker-compose exec backend pytest --cov=apps --cov-report=html
```

Run property-based tests:
```bash
docker-compose exec backend pytest -m property
```

Run specific test file:
```bash
docker-compose exec backend pytest apps/users/tests/test_profile.py
```

### Frontend Tests

```bash
docker-compose exec frontend npm test
```

## Debugging

### Backend Debugging

Add breakpoints using `import pdb; pdb.set_trace()` in your code.

View Django logs:
```bash
docker-compose logs -f backend
```

### Frontend Debugging

View Next.js logs:
```bash
docker-compose logs -f frontend
```

### Celery Debugging

View worker logs:
```bash
docker-compose logs -f celery-worker
```

View beat logs:
```bash
docker-compose logs -f celery-beat
```

## Common Issues

### Port Already in Use

If ports 3000, 5432, 6379, or 8000 are already in use, update `docker-compose.yml` to use different ports.

### Database Connection Issues

Ensure PostgreSQL is healthy:
```bash
docker-compose ps
```

Check PostgreSQL logs:
```bash
docker-compose logs postgres
```

### Prisma Client Not Generated

Generate Prisma client:
```bash
docker-compose exec backend prisma generate
```

### Frontend Build Errors

Clear Next.js cache:
```bash
docker-compose exec frontend rm -rf .next
docker-compose restart frontend
```

## Project Structure

```
muejam-library/
├── apps/backend/
│   ├── apps/              # Django apps
│   │   ├── users/         # User profiles
│   │   ├── stories/       # Stories and chapters
│   │   ├── library/       # Shelves and library
│   │   ├── whispers/      # Whispers system
│   │   ├── highlights/    # Text highlights
│   │   ├── social/        # Follow/block
│   │   ├── notifications/ # Notifications
│   │   ├── discovery/     # Feeds and personalization
│   │   ├── search/        # Search and autocomplete
│   │   ├── uploads/       # S3 uploads
│   │   ├── moderation/    # Content reports
│   │   └── core/          # Shared utilities
│   ├── config/            # Django settings
│   ├── prisma/            # Prisma schema
│   ├── requirements.txt   # Python dependencies
│   └── Dockerfile
├── apps/frontend/
│   ├── app/               # Next.js App Router
│   │   ├── (auth)/        # Auth pages
│   │   ├── (main)/        # Main app pages
│   │   └── api/           # API routes
│   ├── components/        # React components
│   ├── lib/               # Utilities
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## API Documentation

The MueJam Library API is fully documented using OpenAPI 3.0 specification with interactive Swagger UI.

### Accessing Documentation

Once the backend is running, visit:
- **Swagger UI** (Interactive): http://localhost:8000/v1/docs/
- **OpenAPI Schema** (YAML): http://localhost:8000/v1/schema/

### Features

The API documentation includes:
- Complete list of all endpoints with descriptions
- Request/response schemas and examples
- Authentication requirements
- Interactive "Try it out" functionality
- Rate limit information
- Error response formats

### Generating Static Schema

To generate a static OpenAPI schema file:

```bash
# Using Docker
docker-compose exec backend python manage.py spectacular --color --file schema.yml

# Local development
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
python manage.py spectacular --color --file schema.yml
```

For detailed API documentation and usage examples, see [API Documentation](../architecture/api.md).

## Environment Variables

### Backend (.env)

| Variable | Description | Required |
|----------|-------------|----------|
| SECRET_KEY | Django secret key | Yes |
| DEBUG | Debug mode (True/False) | Yes |
| DATABASE_URL | PostgreSQL connection string | Yes |
| VALKEY_URL | Valkey/Redis connection string | Yes |
| CLERK_SECRET_KEY | Clerk secret key | Yes |
| AWS_ACCESS_KEY_ID | AWS access key | Yes |
| AWS_SECRET_ACCESS_KEY | AWS secret key | Yes |
| AWS_S3_BUCKET | S3 bucket name | Yes |
| RESEND_API_KEY | Resend API key | Yes |
| FRONTEND_URL | Frontend URL for emails | Yes |

### Frontend (.env.local)

| Variable | Description | Required |
|----------|-------------|----------|
| NEXT_PUBLIC_API_URL | Backend API URL | Yes |
| NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY | Clerk publishable key | Yes |
| CLERK_SECRET_KEY | Clerk secret key | Yes |

## Contributing

1. Create a feature branch from `main`
2. Make your changes
3. Write tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## Code Style

### Backend (Python)

- Follow PEP 8
- Use type hints
- Write docstrings for functions and classes
- Maximum line length: 100 characters

### Frontend (TypeScript)

- Follow ESLint configuration
- Use TypeScript for type safety
- Use functional components with hooks
- Maximum line length: 100 characters

## Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Next.js Documentation](https://nextjs.org/docs)
- [Prisma Documentation](https://www.prisma.io/docs)
- [Clerk Documentation](https://clerk.com/docs)
- [Celery Documentation](https://docs.celeryq.dev/)
