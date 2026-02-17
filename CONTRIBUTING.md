# Contributing to MueJam Library

Thank you for your interest in contributing to MueJam Library! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive feedback
- Respect differing viewpoints and experiences

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone <your-fork-url>`
3. Create a feature branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Test your changes thoroughly
6. Commit with clear messages
7. Push to your fork
8. Open a pull request

## Development Setup

See [Development Guide](docs/getting-started/development.md) for detailed setup instructions.

## Project Structure

```
muejam-library/
├── apps/              # Applications
│   ├── backend/       # Django REST API
│   └── frontend/      # Vite React application
├── packages/          # Shared libraries (future)
├── tools/             # Build tools and scripts
├── docs/              # Documentation
└── tests/             # Integration tests
```

## Adding New Features

### Adding a New Backend App

1. Create a new directory in `apps/backend/apps/`
2. Follow Django app structure conventions
3. Register the app in `apps/backend/config/settings.py`
4. Add URL patterns to `apps/backend/config/urls.py`
5. Write tests in `apps/backend/tests/`
6. Update API documentation

### Adding a New Frontend Feature

1. Create components in `apps/frontend/src/components/`
2. Add routes in `apps/frontend/src/App.tsx`
3. Create API client functions in `apps/frontend/src/api/`
4. Write tests alongside components
5. Update documentation

### Adding a Shared Package

1. Create a new directory in `packages/`
2. Add `package.json` with appropriate configuration
3. Implement the package functionality
4. Write comprehensive tests
5. Document the package API
6. Update dependent apps to use the package

## Coding Standards

### Backend (Python)

- Follow PEP 8 style guide
- Use type hints where appropriate
- Write docstrings for functions and classes
- Keep functions focused and small
- Use meaningful variable names

### Frontend (TypeScript/React)

- Follow TypeScript best practices
- Use functional components with hooks
- Keep components small and focused
- Use meaningful component and variable names
- Avoid prop drilling - use context when needed

## Testing

### Backend Tests

Run backend tests:
```bash
cd apps/backend
pytest
```

Write tests for:
- API endpoints
- Business logic
- Database models
- Authentication and permissions

### Frontend Tests

Run frontend tests:
```bash
cd apps/frontend
npm test
```

Write tests for:
- Components
- User interactions
- API integration
- Routing

## Commit Messages

Use clear, descriptive commit messages:

- `feat: Add user profile page`
- `fix: Resolve authentication token expiry issue`
- `docs: Update API documentation`
- `test: Add tests for whisper creation`
- `refactor: Simplify authentication logic`
- `chore: Update dependencies`

## Pull Request Process

1. Ensure all tests pass
2. Update documentation if needed
3. Add a clear PR description explaining:
   - What changes were made
   - Why the changes were necessary
   - How to test the changes
4. Link related issues
5. Request review from maintainers
6. Address review feedback promptly

## Documentation

- Update relevant documentation when adding features
- Keep API documentation in sync with code
- Add examples for new functionality
- Update the changelog

## Questions?

- Open an issue for bugs or feature requests
- Start a discussion for questions or ideas
- Check existing issues and discussions first

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

Thank you for contributing to MueJam Library!
