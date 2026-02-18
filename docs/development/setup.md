# Development Setup Guide

This guide walks you through setting up the MueJam Library development environment on your local machine.

## Prerequisites

### Required Software

- **Python 3.11 or higher** - [Download](https://www.python.org/downloads/)
- **Node.js 18 or higher** - [Download](https://nodejs.org/)
- **PostgreSQL 15 or higher** - [Download](https://www.postgresql.org/download/)
- **Valkey 7 or higher** (Redis-compatible) - [Download](https://valkey.io/)
- **Git** - [Download](https://git-scm.com/downloads)

### Optional Software

- **Docker & Docker Compose** - For containerized development
- **VS Code** - Recommended IDE with Python and TypeScript extensions
- **Postman** or **Insomnia** - For API testing

## Quick Start (Docker)

The fastest way to get started is using Docker Compose:

```bash
# Clone the repository
git clone https://github.com/your-org/muejam-library.git
cd muejam-library

# Start all services
docker-compose up

# Backend will be available at http://localhost:8000
# Frontend will be available at http://localhost:3000
```

## Manual Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/muejam-library.git
cd muejam-library
```

### 2. Backend Setup

#### Create Virtual Environment

```bash
cd apps/backend
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

#### Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and configure the following required variables:

**CRITICAL: Generate a Secure SECRET_KEY**

The SECRET_KEY is required for Django's cryptographic signing. Generate one using:

```bash
# Recommended method - Django's built-in generator
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# Alternative - Python secrets module
python -c 'import secrets; print(secrets.token_urlsafe(50))'

# Alternative - OpenSSL
openssl rand -base64 64
```

Copy the generated key and paste it into your `.env` file:

```env
# Database
DATABASE_URL=postgresql://muejam_user:muejam_password@localhost:5432/muejam

# Valkey (Redis)
VALKEY_URL=redis://localhost:6379/0

# Django
SECRET_KEY=<paste-your-generated-key-here>  # REQUIRED - Generate using command above
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Clerk Authentication
CLERK_SECRET_KEY=your-clerk-secret-key
CLERK_PUBLISHABLE_KEY=your-clerk-publishable-key

# AWS (for file uploads)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=us-east-1
```

**Important Notes:**
- Never use the example value `your-secret-key-here-change-in-production`
- Never commit your actual SECRET_KEY to version control
- Generate a different SECRET_KEY for each environment (dev, staging, production)
- The application will fail to start if SECRET_KEY is missing or insecure

#### Setup Database

```bash
# Create database (if not using Docker)
createdb muejam

# Run migrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser

# Load initial data (optional)
python ../../scripts/database/seed-data.py
```

#### Start Development Server

```bash
python manage.py runserver
```

Backend will be available at http://localhost:8000

### 3. Frontend Setup

Open a new terminal:

```bash
cd apps/frontend
```

#### Install Dependencies

```bash
npm install
```

#### Configure Environment Variables

```bash
cp .env.example .env.local
```

Edit `.env.local`:

```env
VITE_API_URL=http://localhost:8000
VITE_CLERK_PUBLISHABLE_KEY=your-clerk-publishable-key
```

#### Start Development Server

```bash
npm run dev
```

Frontend will be available at http://localhost:3000

### 4. Verify Setup

#### Check Backend

```bash
# In apps/backend directory
python manage.py check

# Run tests
python -m pytest

# Access admin panel
# Navigate to http://localhost:8000/admin
```

#### Check Frontend

```bash
# In apps/frontend directory
npm run build

# Run tests
npm test
```

## Database Setup

### PostgreSQL Configuration

#### Create Database and User

```sql
-- Connect to PostgreSQL
psql postgres

-- Create user
CREATE USER muejam_user WITH PASSWORD 'muejam_password';

-- Create database
CREATE DATABASE muejam OWNER muejam_user;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE muejam TO muejam_user;
```

#### Apply Migrations

```bash
cd apps/backend
python manage.py migrate
```

#### Seed Data (Optional)

```bash
# From repository root
python scripts/database/seed-data.py
python scripts/database/seed-legal-documents.py
```

### Valkey (Redis) Setup

#### Install Valkey

**macOS (Homebrew)**:
```bash
brew install valkey
brew services start valkey
```

**Ubuntu/Debian**:
```bash
sudo apt-get install valkey
sudo systemctl start valkey
```

**Windows**:
Download from [valkey.io](https://valkey.io/) or use Docker

#### Verify Valkey

```bash
valkey-cli ping
# Should return: PONG
```

## IDE Setup

### VS Code (Recommended)

#### Install Extensions

- Python (Microsoft)
- Pylance (Microsoft)
- ESLint (Microsoft)
- Prettier (Prettier)
- TypeScript Vue Plugin (Vue)
- Django (Baptiste Darthenay)
- Docker (Microsoft)

#### Workspace Settings

Create `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/apps/backend/venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": [
    "apps/backend"
  ],
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter"
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

#### Launch Configuration

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Django",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/apps/backend/manage.py",
      "args": ["runserver"],
      "django": true,
      "justMyCode": true
    },
    {
      "name": "Pytest",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["-v"],
      "cwd": "${workspaceFolder}/apps/backend"
    }
  ]
}
```

## Common Issues

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill the process
kill -9 <PID>  # macOS/Linux
taskkill /PID <PID> /F  # Windows
```

### Database Connection Error

- Verify PostgreSQL is running
- Check DATABASE_URL in .env
- Ensure database exists: `psql -l`
- Check user permissions

### Valkey Connection Error

- Verify Valkey is running: `valkey-cli ping`
- Check VALKEY_URL in .env
- Try connecting manually: `valkey-cli`

### Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Clear Python cache
find . -type d -name __pycache__ -exec rm -r {} +
find . -type f -name "*.pyc" -delete
```

### Migration Errors

```bash
# Reset migrations (development only!)
python manage.py migrate --fake-initial

# Or drop and recreate database
dropdb muejam
createdb muejam
python manage.py migrate
```

## Next Steps

- Read [Coding Conventions](conventions.md)
- Review [Testing Guide](testing.md)
- Explore [Development Workflows](workflows.md)
- Check [Architecture Documentation](../architecture/monorepo-structure.md)

## Getting Help

- Check [Troubleshooting Guide](troubleshooting.md)
- Search [GitHub Issues](https://github.com/your-org/muejam-library/issues)
- Ask in [GitHub Discussions](https://github.com/your-org/muejam-library/discussions)
