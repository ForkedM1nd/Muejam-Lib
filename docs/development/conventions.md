# Coding Conventions

This document outlines the coding standards and conventions used in the MueJam Library project.

## General Principles

- **Readability**: Code is read more often than written
- **Consistency**: Follow established patterns
- **Simplicity**: Prefer simple solutions over clever ones
- **Maintainability**: Write code that's easy to change
- **Documentation**: Document complex logic and public APIs

## Directory Naming

### Top-Level Directories

Use **kebab-case** (lowercase with hyphens):
- ✅ `docs/`, `scripts/`, `infra/`
- ❌ `Docs/`, `Scripts/`, `Infrastructure/`

### Django Apps

Use **snake_case** (Django convention):
- ✅ `apps/users/`, `apps/two_factor_auth/`
- ❌ `apps/Users/`, `apps/two-factor-auth/`

### Python Modules

Use **snake_case**:
- ✅ `user_service.py`, `content_filter.py`
- ❌ `UserService.py`, `contentFilter.py`

### TypeScript/React

Use **PascalCase** for components, **camelCase** for files:
- ✅ `UserProfile.tsx`, `useAuth.ts`
- ❌ `user-profile.tsx`, `use_auth.ts`

## Python Conventions

### Style Guide

Follow **PEP 8** with these specifics:

- **Line length**: 100 characters (not 79)
- **Indentation**: 4 spaces
- **Quotes**: Single quotes for strings, double for docstrings
- **Imports**: Organized in groups (stdlib, third-party, local)

### Naming Conventions

```python
# Classes: PascalCase
class UserProfile:
    pass

# Functions and methods: snake_case
def calculate_user_score():
    pass

# Constants: UPPER_SNAKE_CASE
MAX_LOGIN_ATTEMPTS = 5

# Private methods: leading underscore
def _internal_helper():
    pass

# Variables: snake_case
user_count = 0
is_active = True
```

### Type Hints

Use type hints for function signatures:

```python
from typing import List, Optional, Dict

def get_user_posts(
    user_id: int,
    limit: int = 10,
    include_drafts: bool = False
) -> List[Dict[str, any]]:
    """
    Retrieve posts for a user.
    
    Args:
        user_id: The ID of the user
        limit: Maximum number of posts to return
        include_drafts: Whether to include draft posts
        
    Returns:
        List of post dictionaries
    """
    pass
```

### Docstrings

Use Google-style docstrings:

```python
def complex_function(param1: str, param2: int) -> bool:
    """
    Brief description of what the function does.
    
    Longer description if needed, explaining the purpose,
    behavior, and any important details.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When param2 is negative
        
    Example:
        >>> complex_function("test", 5)
        True
    """
    pass
```

### Django Models

```python
from django.db import models

class UserProfile(models.Model):
    """User profile information."""
    
    user = models.OneToOneField(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='profile'
    )
    bio = models.TextField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_profiles'
        ordering = ['-created_at']
        
    def __str__(self) -> str:
        return f"Profile for {self.user.username}"
```

### Django Views

```python
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """
    Get or update user profile.
    
    GET: Returns the authenticated user's profile
    PATCH: Updates the authenticated user's profile
    """
    if request.method == 'GET':
        serializer = UserProfileSerializer(request.user.profile)
        return Response(serializer.data)
        
    elif request.method == 'PATCH':
        serializer = UserProfileSerializer(
            request.user.profile,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
```

### Error Handling

```python
# Use specific exceptions
try:
    user = User.objects.get(id=user_id)
except User.DoesNotExist:
    raise NotFound(f"User {user_id} not found")
except MultipleObjectsReturned:
    logger.error(f"Multiple users found for ID {user_id}")
    raise InternalServerError("Data integrity error")

# Use early returns
def process_user(user_id: int) -> Optional[User]:
    if not user_id:
        return None
        
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return None
        
    if not user.is_active:
        return None
        
    return user
```

## TypeScript Conventions

### Style Guide

Follow the project's ESLint configuration:

- **Line length**: 100 characters
- **Indentation**: 2 spaces
- **Quotes**: Single quotes
- **Semicolons**: Required

### Naming Conventions

```typescript
// Interfaces: PascalCase with 'I' prefix (optional)
interface UserProfile {
  id: string;
  username: string;
}

// Types: PascalCase
type UserRole = 'admin' | 'moderator' | 'user';

// Functions: camelCase
function calculateUserScore(): number {
  return 0;
}

// Constants: UPPER_SNAKE_CASE
const MAX_LOGIN_ATTEMPTS = 5;

// Variables: camelCase
const userCount = 0;
const isActive = true;
```

### React Components

```typescript
import React, { useState, useEffect } from 'react';

interface UserProfileProps {
  userId: string;
  onUpdate?: (profile: UserProfile) => void;
}

/**
 * Displays and allows editing of user profile information.
 */
export function UserProfile({ userId, onUpdate }: UserProfileProps) {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    fetchUserProfile(userId)
      .then(setProfile)
      .finally(() => setLoading(false));
  }, [userId]);
  
  if (loading) {
    return <LoadingSpinner />;
  }
  
  if (!profile) {
    return <ErrorMessage message="Profile not found" />;
  }
  
  return (
    <div className="user-profile">
      {/* Component content */}
    </div>
  );
}
```

### Custom Hooks

```typescript
import { useState, useEffect } from 'react';

/**
 * Hook for fetching and managing user data.
 */
export function useUser(userId: string) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  
  useEffect(() => {
    setLoading(true);
    setError(null);
    
    fetchUser(userId)
      .then(setUser)
      .catch(setError)
      .finally(() => setLoading(false));
  }, [userId]);
  
  return { user, loading, error };
}
```

### Type Safety

```typescript
// Use strict types, avoid 'any'
// ❌ Bad
function processData(data: any) {
  return data.value;
}

// ✅ Good
interface DataInput {
  value: string;
}

function processData(data: DataInput): string {
  return data.value;
}

// Use type guards
function isUser(obj: unknown): obj is User {
  return (
    typeof obj === 'object' &&
    obj !== null &&
    'id' in obj &&
    'username' in obj
  );
}
```

## Testing Conventions

### Test File Naming

- Python: `test_*.py` or `*_tests.py`
- TypeScript: `*.test.ts` or `*.test.tsx`

### Test Function Naming

```python
# Python: descriptive names with test_ prefix
def test_user_can_update_profile():
    pass

def test_invalid_email_raises_validation_error():
    pass
```

```typescript
// TypeScript: descriptive strings
test('user can update profile', () => {
  // ...
});

test('invalid email raises validation error', () => {
  // ...
});
```

### Test Organization

```python
# Group related tests in classes
class TestUserAuthentication:
    def test_login_with_valid_credentials(self):
        pass
        
    def test_login_with_invalid_credentials(self):
        pass
        
    def test_login_with_inactive_account(self):
        pass
```

## Git Conventions

### Commit Messages

Follow conventional commits:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Test additions or updates
- `chore`: Build process or tooling changes

**Examples**:
```
feat(auth): add two-factor authentication

Implements TOTP-based 2FA with backup codes.
Users can enable 2FA in their security settings.

Closes #123
```

```
fix(api): resolve race condition in user creation

Adds database-level unique constraint and handles
IntegrityError to prevent duplicate users.

Fixes #456
```

### Branch Naming

```
<type>/<short-description>

Examples:
feature/user-profile-editing
fix/login-redirect-bug
docs/api-documentation
refactor/authentication-service
```

## Documentation Conventions

### Markdown Files

- Use ATX-style headers (`#` not underlines)
- One blank line before and after headers
- Use fenced code blocks with language identifiers
- Keep line length reasonable (80-100 characters)
- Use relative links for internal documentation

### Code Comments

```python
# Good: Explain WHY, not WHAT
# Calculate score using weighted average to prioritize recent activity
score = sum(w * v for w, v in zip(weights, values))

# Bad: Obvious comment
# Loop through users
for user in users:
    pass
```

### API Documentation

Use OpenAPI/Swagger for REST APIs:

```python
from drf_spectacular.utils import extend_schema, OpenApiParameter

@extend_schema(
    summary="Get user profile",
    description="Retrieves the profile for the authenticated user",
    responses={
        200: UserProfileSerializer,
        401: "Unauthorized"
    }
)
@api_view(['GET'])
def get_profile(request):
    pass
```

## Code Review Guidelines

### What to Look For

- **Correctness**: Does the code work as intended?
- **Readability**: Is the code easy to understand?
- **Maintainability**: Will this be easy to change later?
- **Performance**: Are there obvious performance issues?
- **Security**: Are there security vulnerabilities?
- **Tests**: Are there adequate tests?

### Review Comments

```
# Good: Specific and constructive
"Consider using a set instead of a list here for O(1) lookup time"

# Bad: Vague or demanding
"This is wrong, fix it"
```

## Resources

- [PEP 8 - Python Style Guide](https://pep8.org/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [TypeScript Style Guide](https://google.github.io/styleguide/tsguide.html)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Django Coding Style](https://docs.djangoproject.com/en/stable/internals/contributing/writing-code/coding-style/)
