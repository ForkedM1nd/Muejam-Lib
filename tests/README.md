# Integration Tests

This directory contains integration tests that verify interactions between
multiple components or services.

## Purpose

Integration tests complement unit tests by verifying that different parts
of the system work together correctly. These tests may:

- Test API endpoints with real database connections
- Verify frontend-backend integration
- Test authentication flows end-to-end
- Validate data consistency across services

## Running Integration Tests

```bash
# Run all integration tests
pytest tests/

# Run specific integration test
pytest tests/test_auth_flow.py
```

## Organization

- `test_*.py` - Integration test files
- `fixtures/` - Shared test fixtures and data
- `conftest.py` - Pytest configuration for integration tests
