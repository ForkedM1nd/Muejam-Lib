# Development Workflows

Common development workflows and tasks for the MueJam Library project.

## Daily Development Workflow

### 1. Start Your Day

```bash
# Pull latest changes
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/your-feature-name

# Start services
docker-compose up
# Or manually:
# Terminal 1: cd apps/backend && python manage.py runserver
# Terminal 2: cd apps/frontend && npm run dev
```

### 2. Make Changes

- Write code following [conventions](conventions.md)
- Write tests for new functionality
- Run tests frequently
- Commit changes regularly

### 3. End Your Day

```bash
# Run full test suite
cd apps/backend && python -m pytest
cd apps/frontend && npm test

# Commit your work
git add .
git commit -m "feat: description of changes"

# Push to remote
git push origin feature/your-feature-name
```

## Feature Development Workflow

### 1. Plan the Feature

- Review requirements and design
- Break down into small tasks
- Identify affected components
- Plan testing strategy

### 2. Create Branch

```bash
git checkout main
git pull origin main
git checkout -b feature/feature-name
```

### 3. Implement Backend

```bash
cd apps/backend

# Create models
# Edit apps/your_app/models.py

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create serializers
# Edit apps/your_app/serializers.py

# Create views
# Edit apps/your_app/views.py

# Add URL routes
# Edit apps/your_app/urls.py

# Write tests
# Edit apps/your_app/tests/test_feature.py

# Run tests
python -m pytest apps/your_app/tests/
```

### 4. Implement Frontend

```bash
cd apps/frontend

# Create component
# Edit src/components/FeatureName.tsx

# Create hooks (if needed)
# Edit src/hooks/useFeature.ts

# Add API calls
# Edit src/api/featureApi.ts

# Write tests
# Edit src/components/__tests__/FeatureName.test.tsx

# Run tests
npm test -- FeatureName
```

### 5. Test Integration

```bash
# Start both servers
docker-compose up

# Manual testing
# - Test happy path
# - Test error cases
# - Test edge cases
# - Test on different browsers

# Run full test suite
cd apps/backend && python -m pytest
cd apps/frontend && npm test
```

### 6. Create Pull Request

```bash
# Commit all changes
git add .
git commit -m "feat: implement feature name"

# Push to remote
git push origin feature/feature-name

# Create PR on GitHub
# - Add description
# - Link related issues
# - Add screenshots
# - Request reviewers
```

## Bug Fix Workflow

### 1. Reproduce the Bug

```bash
# Create bug fix branch
git checkout -b fix/bug-description

# Write failing test that reproduces the bug
# This ensures the bug is fixed and won't regress
```

### 2. Fix the Bug

```bash
# Make minimal changes to fix the issue
# Avoid scope creep - fix only this bug

# Verify the test now passes
python -m pytest path/to/test.py
```

### 3. Test Thoroughly

```bash
# Run related tests
python -m pytest apps/affected_app/

# Run full test suite
python -m pytest

# Manual testing
# - Verify fix works
# - Check for side effects
# - Test edge cases
```

### 4. Submit Fix

```bash
git add .
git commit -m "fix: description of bug fix"
git push origin fix/bug-description

# Create PR with:
# - Description of bug
# - Root cause analysis
# - How the fix works
# - Link to issue
```

## Database Migration Workflow

### Creating Migrations

```bash
cd apps/backend

# After modifying models
python manage.py makemigrations

# Review the generated migration
cat apps/your_app/migrations/0001_initial.py

# Test the migration
python manage.py migrate

# Test rollback
python manage.py migrate your_app 0000_previous_migration
python manage.py migrate your_app 0001_new_migration
```

### Migration Best Practices

```python
# ✅ Good: Reversible migration
class Migration(migrations.Migration):
    operations = [
        migrations.AddField(
            model_name='user',
            name='bio',
            field=models.TextField(blank=True, default=''),
        ),
    ]

# ❌ Bad: Data loss on rollback
class Migration(migrations.Migration):
    operations = [
        migrations.RemoveField(
            model_name='user',
            name='old_field',
        ),
    ]
```

### Complex Migrations

```python
# Split into multiple migrations for safety
# Migration 1: Add new field
class Migration(migrations.Migration):
    operations = [
        migrations.AddField(
            model_name='user',
            name='new_field',
            field=models.CharField(max_length=100, null=True),
        ),
    ]

# Migration 2: Populate data
def populate_new_field(apps, schema_editor):
    User = apps.get_model('users', 'User')
    for user in User.objects.all():
        user.new_field = calculate_value(user)
        user.save()

class Migration(migrations.Migration):
    dependencies = [
        ('users', '0001_add_new_field'),
    ]
    operations = [
        migrations.RunPython(populate_new_field),
    ]

# Migration 3: Make field non-nullable
class Migration(migrations.Migration):
    dependencies = [
        ('users', '0002_populate_new_field'),
    ]
    operations = [
        migrations.AlterField(
            model_name='user',
            name='new_field',
            field=models.CharField(max_length=100),
        ),
    ]
```

## Code Review Workflow

### As Author

1. **Before Requesting Review**:
   - Run all tests
   - Review your own code
   - Update documentation
   - Add screenshots for UI changes
   - Write clear PR description

2. **During Review**:
   - Respond to comments promptly
   - Ask questions if feedback is unclear
   - Make requested changes
   - Mark conversations as resolved

3. **After Approval**:
   - Squash commits if needed
   - Merge when CI passes
   - Delete feature branch

### As Reviewer

1. **Review Checklist**:
   - [ ] Code follows conventions
   - [ ] Tests are adequate
   - [ ] No obvious bugs
   - [ ] Performance is acceptable
   - [ ] Security is considered
   - [ ] Documentation is updated

2. **Providing Feedback**:
   ```
   # ✅ Good: Specific and constructive
   "Consider using a dictionary here for O(1) lookup instead of 
   iterating through the list. This will improve performance when 
   the list is large."
   
   # ❌ Bad: Vague or demanding
   "This is slow, fix it"
   ```

3. **Approval**:
   - Approve when code meets standards
   - Request changes if issues found
   - Comment for minor suggestions

## Deployment Workflow

### Staging Deployment

```bash
# Ensure all tests pass
python -m pytest
npm test

# Create release branch
git checkout -b release/v1.2.0

# Update version numbers
# Edit package.json, __init__.py, etc.

# Tag release
git tag -a v1.2.0 -m "Release version 1.2.0"

# Push to staging
git push origin release/v1.2.0
git push origin v1.2.0

# Deploy to staging (automated via CI/CD)
# Or manually:
./scripts/deployment/deploy.sh staging
```

### Production Deployment

```bash
# After staging verification
git checkout main
git merge release/v1.2.0

# Deploy to production
./scripts/deployment/deploy.sh production

# Monitor deployment
./scripts/deployment/check-error-rate.sh
./scripts/deployment/check-latency.sh

# Run smoke tests
./scripts/deployment/smoke-tests.sh
```

### Rollback

```bash
# If issues are detected
./scripts/deployment/rollback.sh

# Or manual rollback
git revert HEAD
git push origin main
./scripts/deployment/deploy.sh production
```

## Debugging Workflow

### Backend Debugging

```bash
# Add breakpoint in code
import pdb; pdb.set_trace()

# Run server
python manage.py runserver

# Or run specific test with debugger
python -m pytest --pdb apps/users/tests/test_auth.py::test_login
```

### Frontend Debugging

```typescript
// Add debugger statement
function handleSubmit() {
  debugger;
  // Your code
}

// Or use console.log
console.log('User data:', user);

// Use React DevTools
// Install browser extension and inspect components
```

### Database Debugging

```bash
# Django shell
python manage.py shell

# Query data
from apps.users.models import User
users = User.objects.all()
user = User.objects.get(id=1)

# Check SQL queries
from django.db import connection
print(connection.queries)
```

## Performance Optimization Workflow

### 1. Identify Bottleneck

```bash
# Profile backend
python -m cProfile -o profile.stats manage.py runserver

# Analyze profile
python -m pstats profile.stats

# Check database queries
python manage.py shell
from django.db import connection
from django.test.utils import override_settings

with override_settings(DEBUG=True):
    # Run your code
    print(len(connection.queries))
    print(connection.queries)
```

### 2. Optimize

```python
# ❌ Bad: N+1 query problem
users = User.objects.all()
for user in users:
    print(user.profile.bio)  # Separate query for each user

# ✅ Good: Use select_related
users = User.objects.select_related('profile').all()
for user in users:
    print(user.profile.bio)  # Single query with JOIN
```

### 3. Measure Improvement

```bash
# Run performance tests
python -m pytest -m performance

# Compare before/after metrics
```

## Documentation Workflow

### Updating Documentation

```bash
# Edit relevant docs
vim docs/features/your-feature.md

# Preview locally (if using static site generator)
cd docs
mkdocs serve

# Commit with docs prefix
git commit -m "docs: update feature documentation"
```

### API Documentation

```python
# Update OpenAPI schema
from drf_spectacular.utils import extend_schema

@extend_schema(
    summary="Create a new post",
    description="Creates a new post for the authenticated user",
    request=PostSerializer,
    responses={201: PostSerializer}
)
@api_view(['POST'])
def create_post(request):
    pass

# Generate schema
python manage.py spectacular --file schema.yml

# View in Swagger UI
# Navigate to http://localhost:8000/api/schema/swagger-ui/
```

## Useful Commands

### Backend

```bash
# Create new Django app
python manage.py startapp app_name

# Create superuser
python manage.py createsuperuser

# Run shell
python manage.py shell

# Check for issues
python manage.py check

# Collect static files
python manage.py collectstatic

# Clear cache
python manage.py clear_cache
```

### Frontend

```bash
# Add dependency
npm install package-name

# Remove dependency
npm uninstall package-name

# Update dependencies
npm update

# Check for outdated packages
npm outdated

# Lint code
npm run lint

# Format code
npm run format
```

### Git

```bash
# Stash changes
git stash
git stash pop

# Amend last commit
git commit --amend

# Interactive rebase
git rebase -i HEAD~3

# Cherry-pick commit
git cherry-pick <commit-hash>

# View file history
git log --follow path/to/file
```

## Resources

- [Git Workflow](https://www.atlassian.com/git/tutorials/comparing-workflows)
- [Django Best Practices](https://docs.djangoproject.com/en/stable/misc/design-philosophies/)
- [React Patterns](https://reactpatterns.com/)
- [Code Review Best Practices](https://google.github.io/eng-practices/review/)
