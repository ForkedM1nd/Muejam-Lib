# Quick Start Guide

Get MueJam Library running in 5 minutes!

## Prerequisites

- Docker Desktop installed and running
- Git installed
- Text editor (VS Code recommended)

## Step 1: Clone or Navigate to Project

```bash
cd muejam-library
```

## Step 2: Set Up Environment Variables

### Option A: Automated Setup (Recommended)

**Linux/Mac:**
```bash
chmod +x setup.sh
./setup.sh
```

**Windows (PowerShell):**
```powershell
.\setup.ps1
```

### Option B: Manual Setup

```bash
# Copy environment files
cp apps/backend/.env.example apps/backend/.env
cp apps/frontend/.env.example apps/frontend/.env.local
```

## Step 3: Configure Credentials

Edit `apps/backend/.env` and add your credentials:

```env
# Required for authentication
CLERK_SECRET_KEY=sk_test_your_key_here
CLERK_PUBLISHABLE_KEY=pk_test_your_key_here

# Required for media uploads
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_S3_BUCKET=your-bucket-name

# Required for email notifications
RESEND_API_KEY=re_your_key_here
```

Edit `apps/frontend/.env.local`:

```env
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_your_key_here
CLERK_SECRET_KEY=sk_test_your_key_here
```

### Getting Credentials

#### Clerk (Free for development)
1. Go to https://clerk.com
2. Sign up and create a new application
3. Copy the keys from the dashboard

#### AWS S3 (Free tier available)
1. Create AWS account at https://aws.amazon.com
2. Create an S3 bucket
3. Create IAM user with S3 permissions
4. Generate access keys

#### Resend (Free tier: 100 emails/day)
1. Go to https://resend.com
2. Sign up and verify your email
3. Create an API key

## Step 4: Start Services

```bash
docker-compose up -d
```

This will start:
- PostgreSQL database (port 5432)
- Valkey cache (port 6379)
- Django backend (port 8000)
- Next.js frontend (port 3000)
- Celery worker (background jobs)
- Celery beat (scheduled tasks)

## Step 5: Initialize Database

```bash
docker-compose exec backend python manage.py migrate
```

## Step 6: Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/v1/docs

## Step 7: Create Test User

1. Go to http://localhost:3000
2. Click "Sign Up"
3. Create an account through Clerk
4. You'll be redirected to the discover page

## Verify Everything Works

### Check Services Status

```bash
docker-compose ps
```

All services should show "Up" status.

### Check Backend Health

```bash
curl http://localhost:8000/v1/health
```

Should return:
```json
{
  "status": "healthy",
  "database": "connected",
  "cache": "connected"
}
```

### Check Frontend

Open http://localhost:3000 in your browser. You should see the MueJam Library homepage.

## Common Issues

### Port Already in Use

If you get "port already in use" errors:

1. Check what's using the port:
```bash
# Windows
netstat -ano | findstr :3000

# Linux/Mac
lsof -i :3000
```

2. Either stop the conflicting service or change ports in `docker-compose.yml`

### Docker Not Running

Make sure Docker Desktop is running:
- Windows/Mac: Check system tray for Docker icon
- Linux: `sudo systemctl status docker`

### Database Connection Failed

1. Check PostgreSQL is running:
```bash
docker-compose ps postgres
```

2. Check logs:
```bash
docker-compose logs postgres
```

3. Restart services:
```bash
docker-compose restart
```

### Frontend Can't Connect to Backend

1. Verify backend is running:
```bash
curl http://localhost:8000/v1/health
```

2. Check `apps/frontend/.env.local` has correct API URL:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/v1
```

## Next Steps

### Development

- Read [Development Guide](development.md) for detailed development guide
- Check [Secrets Management](../deployment/secrets.md) for secrets management
- Review the API docs at http://localhost:8000/v1/docs

### Create Your First Story

1. Sign in at http://localhost:3000
2. Go to "Write" section
3. Click "New Story"
4. Fill in title, blurb, and upload a cover
5. Add chapters
6. Publish!

### Explore Features

- **Discover**: Browse trending and new stories
- **Library**: Create shelves and organize stories
- **Whispers**: Post micro-updates and engage with content
- **Reader**: Enjoy distraction-free reading with customizable settings
- **Highlights**: Save and annotate passages

## Stopping Services

```bash
# Stop services but keep data
docker-compose stop

# Stop and remove containers (data persists in volumes)
docker-compose down

# Stop and remove everything including data
docker-compose down -v
```

## Getting Help

- Check [Development Guide](development.md) for detailed documentation
- Review [Project Overview](../../README.md) for project overview
- Check Docker logs: `docker-compose logs -f [service-name]`
- Verify environment variables are set correctly

## Success! 🎉

You now have MueJam Library running locally. Happy coding!

For more detailed information, see:
- [Project Overview](../../README.md) - Project overview
- [Development Guide](development.md) - Development guide
- [Secrets Management](../deployment/secrets.md) - Secrets management
