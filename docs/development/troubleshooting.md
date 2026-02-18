# Troubleshooting Guide

Common issues and solutions for MueJam Library development.

## Backend Issues

### Database Connection Errors

**Problem**: `django.db.utils.OperationalError: could not connect to server`

**Solutions**:
```bash
# Check if PostgreSQL is running
pg_isready

# Start PostgreSQL
# macOS:
brew services start postgresql
# Linux:
sudo systemctl start postgresql
# Windows:
net start postgresql-x64-15

# Verify connection manually
psql -U muejam_user -d muejam -h localhost

# Check DATABASE_URL in .env
echo $DATABASE_URL
```

### Migration Errors

**Problem**: `django.db.migrations.exceptions.InconsistentMigrationHistory`

**Solutions**:
```bash
# Option 1: Fake the migration
python manage.py migrate --fake app_name migration_name

# Option 2: Reset migrations (development only!)
python manage.py migrate app_name zero
python manage.py migrate app_name

# Option 3: Drop and recreate database (development only!)
dropdb muejam
createdb muejam
python manage.py migrate
```

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'apps.security'`

**Solutions**:
```bash
# Verify INSTALLED_APPS in settings.py
grep "apps.security" apps/backend/config/settings.py

# Check if __init__.py exists
ls apps/backend/apps/security/__init__.py

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Clear Python cache
find . -type d -name __pycache__ -exec rm -r {} +
find . -type f -name "*.pyc" -delete
```

### Test Failures

**Problem**: Tests fail with `django.db.utils.ProgrammingError: relation does not exist`

**Solutions**:
```bash
# Run migrations in test database
python manage.py migrate --run-syncdb

# Use --create-db flag
python -m pytest --create-db

# Drop test database and recreate
dropdb test_muejam
python -m pytest --create-db
```

### Port Already in Use

**Problem**: `Error: That port is already in use`

**Solutions**:
```bash
# Find process using port 8000
# macOS/Linux:
lsof -i :8000
# Windows:
netstat -ano | findstr :8000

# Kill the process
# macOS/Linux:
kill -9 <PID>
# Windows:
taskkill /PID <PID> /F

# Or use a different port
python manage.py runserver 8001
```

### Valkey/Redis Connection Errors

**Problem**: `redis.exceptions.ConnectionError: Error connecting to Redis`

**Solutions**:
```bash
# Check if Valkey is running
valkey-cli ping
# Should return: PONG

# Start Valkey
# macOS:
brew services start valkey
# Linux:
sudo systemctl start valkey
# Windows: Use Docker or WSL

# Check VALKEY_URL in .env
echo $VALKEY_URL

# Test connection
valkey-cli -h localhost -p 6379
```

### Static Files Not Loading

**Problem**: Static files (CSS, JS) not loading in development

**Solutions**:
```bash
# Collect static files
python manage.py collectstatic --noinput

# Check STATIC_URL and STATIC_ROOT in settings.py
python manage.py diffsettings | grep STATIC

# Ensure DEBUG=True in development
grep DEBUG apps/backend/.env

# Clear browser cache
# Chrome: Ctrl+Shift+Delete
# Firefox: Ctrl+Shift+Delete
```

## Frontend Issues

### Build Errors

**Problem**: `npm run build` fails with syntax errors

**Solutions**:
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Check Node version
node --version
# Should be 18+

# Clear build cache
rm -rf .next dist

# Check for TypeScript errors
npm run type-check

# Run linter
npm run lint
```

### Module Not Found Errors

**Problem**: `Module not found: Can't resolve './Component'`

**Solutions**:
```bash
# Check file path and casing (case-sensitive!)
ls src/components/Component.tsx

# Check import statement
# ❌ Bad: import Component from './component'
# ✅ Good: import Component from './Component'

# Restart dev server
# Ctrl+C, then npm run dev

# Clear cache
rm -rf node_modules/.cache
```

### API Connection Errors

**Problem**: `Network Error` or `CORS error` when calling API

**Solutions**:
```bash
# Check VITE_API_URL in .env.local
cat apps/frontend/.env.local

# Verify backend is running
curl http://localhost:8000/api/health

# Check CORS settings in backend
# apps/backend/config/settings.py
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
]

# Check browser console for specific error
# Open DevTools (F12) and check Console tab
```

### Hot Reload Not Working

**Problem**: Changes not reflected in browser

**Solutions**:
```bash
# Restart dev server
# Ctrl+C, then npm run dev

# Clear browser cache
# Hard refresh: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)

# Check if file is being watched
# Look for "File change detected" in terminal

# Increase file watcher limit (Linux)
echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

## Docker Issues

### Container Won't Start

**Problem**: `docker-compose up` fails

**Solutions**:
```bash
# Check Docker is running
docker ps

# View container logs
docker-compose logs backend
docker-compose logs frontend

# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up

# Remove volumes and rebuild
docker-compose down -v
docker-compose up --build
```

### Database Connection in Docker

**Problem**: Backend can't connect to PostgreSQL in Docker

**Solutions**:
```bash
# Check DATABASE_URL uses service name
# In .env:
DATABASE_URL=postgresql://muejam_user:muejam_password@postgres:5432/muejam
# Note: "postgres" is the service name, not "localhost"

# Wait for database to be ready
# Add healthcheck in docker-compose.yml
depends_on:
  postgres:
    condition: service_healthy

# Check if containers are on same network
docker network ls
docker network inspect muejam-library_default
```

### Permission Errors in Docker

**Problem**: Permission denied errors in Docker volumes

**Solutions**:
```bash
# Fix file permissions
sudo chown -R $USER:$USER .

# Or run as current user
# In docker-compose.yml:
services:
  backend:
    user: "${UID}:${GID}"

# Set UID and GID in .env
echo "UID=$(id -u)" >> .env
echo "GID=$(id -g)" >> .env
```

## Git Issues

### Merge Conflicts

**Problem**: Merge conflicts when pulling or merging

**Solutions**:
```bash
# View conflicted files
git status

# Open file and resolve conflicts
# Look for:
# <<<<<<< HEAD
# Your changes
# =======
# Their changes
# >>>>>>> branch-name

# After resolving, mark as resolved
git add path/to/file

# Continue merge
git merge --continue
# Or for rebase:
git rebase --continue

# Abort if needed
git merge --abort
# Or:
git rebase --abort
```

### Accidentally Committed to Wrong Branch

**Problem**: Made commits on main instead of feature branch

**Solutions**:
```bash
# Create new branch with current changes
git branch feature/my-feature

# Reset main to remote
git checkout main
git reset --hard origin/main

# Switch to feature branch
git checkout feature/my-feature
```

### Need to Undo Last Commit

**Problem**: Need to undo the last commit

**Solutions**:
```bash
# Undo commit but keep changes
git reset --soft HEAD~1

# Undo commit and discard changes
git reset --hard HEAD~1

# Undo commit and create new commit
git revert HEAD
```

## Performance Issues

### Slow API Responses

**Problem**: API endpoints taking too long to respond

**Solutions**:
```python
# Check for N+1 queries
from django.db import connection
from django.test.utils import override_settings

with override_settings(DEBUG=True):
    # Your code
    print(f"Queries: {len(connection.queries)}")
    for query in connection.queries:
        print(query['sql'])

# Use select_related for foreign keys
users = User.objects.select_related('profile').all()

# Use prefetch_related for many-to-many
posts = Post.objects.prefetch_related('tags').all()

# Add database indexes
class Meta:
    indexes = [
        models.Index(fields=['created_at']),
        models.Index(fields=['user', 'created_at']),
    ]
```

### Slow Frontend Rendering

**Problem**: React components rendering slowly

**Solutions**:
```typescript
// Use React.memo for expensive components
export const ExpensiveComponent = React.memo(({ data }) => {
  // Component code
});

// Use useMemo for expensive calculations
const sortedData = useMemo(() => {
  return data.sort((a, b) => a.value - b.value);
}, [data]);

// Use useCallback for event handlers
const handleClick = useCallback(() => {
  // Handler code
}, [dependencies]);

// Check React DevTools Profiler
// Open DevTools > Profiler tab > Record
```

## Environment Issues

### Environment Variables Not Loading

**Problem**: Environment variables not available

**Solutions**:
```bash
# Backend: Check .env file exists
ls apps/backend/.env

# Backend: Verify python-dotenv is installed
pip list | grep python-dotenv

# Backend: Load manually in shell
python manage.py shell
from django.conf import settings
print(settings.SECRET_KEY)

# Frontend: Check .env.local exists
ls apps/frontend/.env.local

# Frontend: Restart dev server after changing .env
# Ctrl+C, then npm run dev

# Frontend: Verify variable name starts with VITE_
# ❌ Bad: API_URL=...
# ✅ Good: VITE_API_URL=...
```

### Python Version Issues

**Problem**: Code fails with Python version errors

**Solutions**:
```bash
# Check Python version
python --version
# Should be 3.11+

# Use pyenv to manage versions
pyenv install 3.11.0
pyenv local 3.11.0

# Recreate virtual environment
rm -rf venv
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Testing Issues

### Tests Pass Locally But Fail in CI

**Problem**: Tests pass on your machine but fail in CI/CD

**Solutions**:
```bash
# Check for hardcoded paths
# ❌ Bad: /Users/you/project/file.txt
# ✅ Good: Path(__file__).parent / 'file.txt'

# Check for timezone issues
# Use UTC in tests
from django.utils import timezone
now = timezone.now()

# Check for race conditions
# Add proper waits in async tests
await asyncio.sleep(0.1)

# Check for database state dependencies
# Use fixtures to ensure clean state
@pytest.fixture(autouse=True)
def reset_db():
    # Reset database state
    pass
```

### Flaky Tests

**Problem**: Tests sometimes pass, sometimes fail

**Solutions**:
```python
# Add explicit waits
import time
time.sleep(0.1)

# Use proper async/await
async def test_async_function():
    result = await async_function()
    assert result is not None

# Avoid time-dependent tests
# ❌ Bad:
assert user.created_at == datetime.now()
# ✅ Good:
assert user.created_at <= datetime.now()

# Use freezegun for time-dependent code
from freezegun import freeze_time

@freeze_time("2024-01-15")
def test_with_fixed_time():
    # Test code
    pass
```

## Getting More Help

### Check Logs

```bash
# Backend logs
tail -f apps/backend/logs/django.log

# Frontend logs
# Check browser console (F12)

# Docker logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Enable Debug Mode

```python
# Backend: settings.py
DEBUG = True
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}
```

### Search for Similar Issues

- Check [GitHub Issues](https://github.com/your-org/muejam-library/issues)
- Search [Stack Overflow](https://stackoverflow.com/)
- Check Django/React documentation

### Ask for Help

- Create a GitHub Issue with:
  - Clear description of the problem
  - Steps to reproduce
  - Expected vs actual behavior
  - Error messages and logs
  - Environment details (OS, Python version, etc.)

## Resources

- [Django Troubleshooting](https://docs.djangoproject.com/en/stable/faq/)
- [React Debugging](https://react.dev/learn/debugging)
- [Docker Troubleshooting](https://docs.docker.com/config/daemon/)
- [PostgreSQL Common Errors](https://www.postgresql.org/docs/current/errcodes-appendix.html)
