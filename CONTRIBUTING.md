# Contributing to MueJam Library

Thank you for your interest in contributing to MueJam Library! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Code Standards](#code-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Getting Help](#getting-help)

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Valkey (Redis-compatible) 7+
- Docker & Docker Compose (optional, for containerized development)

### Development Setup

See [docs/development/setup.md](docs/development/setup.md) for detailed setup instructions.

Quick start:

```bash
# Clone the repository
git clone https://github.com/your-org/muejam-library.git
cd muejam-library

# Backend setup
cd apps/backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your configuration
python manage.py migrate
python manage.py runserver

# Frontend setup (in a new terminal)
cd apps/frontend
npm install
cp .env.example .env.local
# Edit .env.local with your configuration
npm run dev
```

## Project Structure

MueJam Library is organized as a monorepo:

```
muejam-library/
├── apps/              # Deployable applications
│   ├── backend/       # Django backend
│   └── frontend/      # React frontend
├── docs/              # All documentation
├── tests/             # Centralized test suites
├── scripts/           # Automation scripts
├── infra/             # Infrastructure as code
└── packages/          # Shared libraries
```

See [docs/architecture/monorepo-structure.md](docs/architecture/monorepo-structure.md) for detailed structure documentation.

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions or updates

### 2. Make Changes

- Follow our [coding conventions](docs/development/conventions.md)
- Write tests for new functionality
- Update documentation as needed
- Keep commits focused and atomic

### 3. Test Your Changes

```bash
# Backend tests
cd apps/backend
python -m pytest

# Frontend tests
cd apps/frontend
npm test

# Run specific tests
python -m pytest apps/users/tests/
npm test -- --testPathPattern=components
```

### 4. Commit Your Changes

We follow conventional commit messages:

```bash
git commit -m "feat: add user profile editing"
git commit -m "fix: resolve login redirect issue"
git commit -m "docs: update API documentation"
git commit -m "test: add tests for authentication flow"
```

Commit message format:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Test additions or updates
- `chore:` - Build process or auxiliary tool changes

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub with:
- Clear description of changes
- Link to related issues
- Screenshots (for UI changes)
- Test results

## Code Standards

### Python (Backend)

- Follow PEP 8 style guide
- Use type hints where appropriate
- Maximum line length: 100 characters
- Use meaningful variable and function names
- Write docstrings for classes and functions

```python
def calculate_user_score(user_id: int, include_bonus: bool = False) -> float:
    """
    Calculate the total score for a user.
    
    Args:
        user_id: The ID of the user
        include_bonus: Whether to include bonus points
        
    Returns:
        The calculated score as a float
    """
    # Implementation
```

### TypeScript (Frontend)

- Follow the project's ESLint configuration
- Use TypeScript strict mode
- Prefer functional components with hooks
- Use meaningful component and variable names
- Write JSDoc comments for complex functions

```typescript
/**
 * Fetches user profile data from the API
 * @param userId - The ID of the user to fetch
 * @returns Promise resolving to user profile data
 */
async function fetchUserProfile(userId: string): Promise<UserProfile> {
  // Implementation
}
```

### General Guidelines

- Keep functions small and focused
- Avoid deep nesting (max 3-4 levels)
- Use early returns to reduce complexity
- Write self-documenting code
- Add comments for complex logic only
- Remove commented-out code before committing

See [docs/development/conventions.md](docs/development/conventions.md) for complete coding standards.

## Testing

### Test Organization

- **Unit Tests**: Test individual functions and classes
- **Integration Tests**: Test component interactions
- **End-to-End Tests**: Test complete user workflows
- **Property-Based Tests**: Test properties across many inputs

### Writing Tests

**Backend (pytest)**:
```python
def test_user_can_update_profile():
    """Test that authenticated users can update their profile."""
    user = create_test_user()
    client = APIClient()
    client.force_authenticate(user=user)
    
    response = client.patch('/api/users/me/', {'bio': 'New bio'})
    
    assert response.status_code == 200
    assert response.data['bio'] == 'New bio'
```

**Frontend (Jest/React Testing Library)**:
```typescript
test('user can submit login form', async () => {
  render(<LoginForm />);
  
  await userEvent.type(screen.getByLabelText(/email/i), 'user@example.com');
  await userEvent.type(screen.getByLabelText(/password/i), 'password123');
  await userEvent.click(screen.getByRole('button', { name: /log in/i }));
  
  expect(await screen.findByText(/welcome/i)).toBeInTheDocument();
});
```

### Running Tests

```bash
# Run all backend tests
cd apps/backend
python -m pytest

# Run with coverage
python -m pytest --cov=apps --cov-report=html

# Run specific test file
python -m pytest apps/users/tests/test_authentication.py

# Run tests matching pattern
python -m pytest -k "test_login"

# Run all frontend tests
cd apps/frontend
npm test

# Run in watch mode
npm test -- --watch

# Run with coverage
npm test -- --coverage
```

See [docs/development/testing.md](docs/development/testing.md) for comprehensive testing guidelines.

## Submitting Changes

### Pull Request Checklist

Before submitting a pull request, ensure:

- [ ] Code follows project conventions
- [ ] All tests pass
- [ ] New tests added for new functionality
- [ ] Documentation updated (if applicable)
- [ ] No console errors or warnings
- [ ] Commit messages follow conventional format
- [ ] Branch is up to date with main
- [ ] PR description clearly explains changes

### Code Review Process

1. Submit pull request with clear description
2. Automated tests run via CI/CD
3. Team members review code
4. Address review feedback
5. Maintainer approves and merges

### Review Guidelines

When reviewing code:
- Be respectful and constructive
- Focus on code quality and maintainability
- Suggest improvements, don't demand perfection
- Approve when code meets standards
- Ask questions if something is unclear

## Getting Help

### Documentation

- [Setup Guide](docs/development/setup.md)
- [Coding Conventions](docs/development/conventions.md)
- [Testing Guide](docs/development/testing.md)
- [Workflows](docs/development/workflows.md)
- [Troubleshooting](docs/development/troubleshooting.md)
- [Architecture](docs/architecture/monorepo-structure.md)

### Communication

- GitHub Issues: Bug reports and feature requests
- GitHub Discussions: Questions and general discussion
- Pull Requests: Code review and feedback

### Common Questions

**Q: How do I run the project locally?**  
A: See [docs/development/setup.md](docs/development/setup.md)

**Q: Where should I put my code?**  
A: See [docs/architecture/monorepo-structure.md](docs/architecture/monorepo-structure.md)

**Q: How do I write tests?**  
A: See [docs/development/testing.md](docs/development/testing.md)

**Q: My tests are failing, what should I do?**  
A: See [docs/development/troubleshooting.md](docs/development/troubleshooting.md)

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Assume good intentions
- Report unacceptable behavior to maintainers

## License

By contributing to MueJam Library, you agree that your contributions will be licensed under the project's license.

## Thank You!

Your contributions make MueJam Library better for everyone. We appreciate your time and effort!
