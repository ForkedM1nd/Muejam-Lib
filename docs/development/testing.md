# Testing Guide

This guide covers testing practices and strategies for the MueJam Library project.

## Test Organization

### Backend Tests

```
apps/backend/
├── apps/
│   ├── users/
│   │   └── tests/          # Colocated unit tests
│   ├── moderation/
│   │   └── tests/
│   └── ...
tests/backend/
├── integration/             # Integration tests
├── e2e/                     # End-to-end tests
└── infrastructure/          # Infrastructure tests
```

### Frontend Tests

```
apps/frontend/
├── src/
│   ├── components/
│   │   └── __tests__/      # Component tests
│   └── hooks/
│       └── __tests__/      # Hook tests
tests/frontend/
├── integration/             # Integration tests
└── e2e/                     # End-to-end tests
```

## Test Types

### Unit Tests

Test individual functions, classes, and components in isolation.

**Backend (pytest)**:
```python
def test_calculate_user_score():
    """Test score calculation with various inputs."""
    assert calculate_user_score(posts=10, likes=50) == 150
    assert calculate_user_score(posts=0, likes=0) == 0
```

**Frontend (Jest)**:
```typescript
test('formatDate formats dates correctly', () => {
  const date = new Date('2024-01-15');
  expect(formatDate(date)).toBe('January 15, 2024');
});
```

### Integration Tests

Test interactions between components.

```python
def test_user_registration_flow():
    """Test complete user registration process."""
    response = client.post('/api/auth/register/', {
        'email': 'test@example.com',
        'password': 'SecurePass123!',
        'username': 'testuser'
    })
    
    assert response.status_code == 201
    assert User.objects.filter(email='test@example.com').exists()
    assert len(mail.outbox) == 1  # Verification email sent
```

### End-to-End Tests

Test complete user workflows.

```typescript
test('user can create and publish a story', async () => {
  await login('author@example.com', 'password');
  await navigateTo('/stories/new');
  
  await fillIn('title', 'My Test Story');
  await fillIn('content', 'Story content here...');
  await click('Publish');
  
  expect(await findByText('Story published successfully')).toBeVisible();
});
```

### Property-Based Tests

Test properties that should hold for all inputs.

```python
from hypothesis import given, strategies as st

@given(st.integers(min_value=0), st.integers(min_value=0))
def test_score_is_non_negative(posts, likes):
    """Score should always be non-negative."""
    score = calculate_user_score(posts=posts, likes=likes)
    assert score >= 0
```

## Running Tests

### Backend

```bash
cd apps/backend

# Run all tests
python -m pytest

# Run specific test file
python -m pytest apps/users/tests/test_authentication.py

# Run tests matching pattern
python -m pytest -k "test_login"

# Run with coverage
python -m pytest --cov=apps --cov-report=html

# Run in parallel
python -m pytest -n auto

# Run only failed tests
python -m pytest --lf

# Run with verbose output
python -m pytest -v
```

### Frontend

```bash
cd apps/frontend

# Run all tests
npm test

# Run in watch mode
npm test -- --watch

# Run with coverage
npm test -- --coverage

# Run specific test file
npm test -- UserProfile.test.tsx

# Update snapshots
npm test -- -u
```

## Writing Good Tests

### Test Structure (AAA Pattern)

```python
def test_user_can_update_bio():
    # Arrange: Set up test data
    user = create_test_user()
    client = APIClient()
    client.force_authenticate(user=user)
    
    # Act: Perform the action
    response = client.patch('/api/users/me/', {'bio': 'New bio'})
    
    # Assert: Verify the result
    assert response.status_code == 200
    assert response.data['bio'] == 'New bio'
    user.refresh_from_db()
    assert user.profile.bio == 'New bio'
```

### Test Naming

Be descriptive and specific:

```python
# ✅ Good
def test_login_fails_with_invalid_password():
    pass

def test_user_cannot_delete_others_posts():
    pass

# ❌ Bad
def test_login():
    pass

def test_delete():
    pass
```

### Test Independence

Each test should be independent:

```python
# ✅ Good: Each test creates its own data
def test_user_creation():
    user = User.objects.create(username='test1')
    assert user.username == 'test1'

def test_user_deletion():
    user = User.objects.create(username='test2')
    user.delete()
    assert not User.objects.filter(username='test2').exists()

# ❌ Bad: Tests depend on each other
user = None

def test_user_creation():
    global user
    user = User.objects.create(username='test')

def test_user_deletion():
    global user
    user.delete()  # Fails if first test didn't run
```

### Use Fixtures

```python
import pytest

@pytest.fixture
def authenticated_client(db):
    """Provide an authenticated API client."""
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    client = APIClient()
    client.force_authenticate(user=user)
    return client

def test_get_profile(authenticated_client):
    response = authenticated_client.get('/api/users/me/')
    assert response.status_code == 200
```

### Mock External Services

```python
from unittest.mock import patch, Mock

@patch('apps.notifications.email_service.send_email')
def test_user_registration_sends_email(mock_send_email):
    """Test that registration sends verification email."""
    response = client.post('/api/auth/register/', {
        'email': 'test@example.com',
        'password': 'SecurePass123!',
        'username': 'testuser'
    })
    
    assert response.status_code == 201
    mock_send_email.assert_called_once()
    assert 'verify' in mock_send_email.call_args[0][0].lower()
```

## Test Coverage

### Measuring Coverage

```bash
# Backend
cd apps/backend
python -m pytest --cov=apps --cov-report=html
open htmlcov/index.html

# Frontend
cd apps/frontend
npm test -- --coverage
open coverage/lcov-report/index.html
```

### Coverage Goals

- **Overall**: Aim for 80%+ coverage
- **Critical paths**: 100% coverage (authentication, payments, data integrity)
- **Utility functions**: 90%+ coverage
- **UI components**: 70%+ coverage

### What to Test

**High Priority**:
- Authentication and authorization
- Data validation and sanitization
- Business logic
- API endpoints
- Database operations
- Security features

**Medium Priority**:
- UI components
- Form handling
- Error handling
- Edge cases

**Low Priority**:
- Simple getters/setters
- Configuration files
- Third-party library wrappers

## Testing Best Practices

### Do's

- ✅ Write tests before or alongside code (TDD)
- ✅ Test behavior, not implementation
- ✅ Use descriptive test names
- ✅ Keep tests simple and focused
- ✅ Test edge cases and error conditions
- ✅ Use fixtures and factories for test data
- ✅ Mock external dependencies
- ✅ Run tests frequently during development

### Don'ts

- ❌ Don't test framework code
- ❌ Don't write tests that depend on each other
- ❌ Don't test private methods directly
- ❌ Don't use real external services in tests
- ❌ Don't commit failing tests
- ❌ Don't skip writing tests for "simple" code
- ❌ Don't test implementation details

## Continuous Integration

Tests run automatically on every pull request:

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run backend tests
        run: |
          cd apps/backend
          pip install -r requirements.txt
          python -m pytest --cov=apps
          
  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run frontend tests
        run: |
          cd apps/frontend
          npm install
          npm test -- --coverage
```

## Debugging Tests

### Backend

```bash
# Run with pdb debugger
python -m pytest --pdb

# Run with print statements visible
python -m pytest -s

# Run with detailed output
python -m pytest -vv

# Run specific test with debugging
python -m pytest apps/users/tests/test_auth.py::test_login -vv -s
```

### Frontend

```bash
# Run with debugging
node --inspect-brk node_modules/.bin/jest --runInBand

# Run specific test
npm test -- UserProfile.test.tsx --watch
```

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [Jest Documentation](https://jestjs.io/)
- [React Testing Library](https://testing-library.com/react)
- [Hypothesis (Property Testing)](https://hypothesis.readthedocs.io/)
- [Testing Best Practices](https://testingjavascript.com/)
