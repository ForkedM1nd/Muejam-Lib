# Tests

This directory contains all tests for the MueJam Library monorepo.

## Structure

```
tests/
├── backend/           # Backend tests
│   ├── unit/          # Unit tests for backend components
│   ├── integration/   # Backend integration tests
│   ├── property/      # Property-based tests
│   └── performance/   # Performance and load tests
└── README.md          # This file
```

## Backend Tests

### Unit Tests
Located in `tests/backend/unit/`, these test individual components in isolation.

```bash
# Run all backend unit tests
cd apps/backend
pytest ../../../tests/backend/unit/

# Or from root
pytest tests/backend/unit/
```

### Integration Tests
Located in `tests/backend/integration/`, these verify interactions between components.

```bash
# Run backend integration tests
pytest tests/backend/integration/
```

### Property-Based Tests
Located in `tests/backend/property/`, these use property-based testing to verify correctness properties.

```bash
# Run property-based tests
pytest tests/backend/property/
```

### Performance Tests
Located in `tests/backend/performance/`, these test system performance and load handling.

```bash
# Run performance tests
pytest tests/backend/performance/
```

## Running All Tests

```bash
# Run all tests from root
pytest tests/

# Run with coverage
pytest tests/ --cov=apps/backend --cov-report=html

# Run specific test file
pytest tests/backend/unit/test_cache_manager.py
```

## Test Configuration

Test configuration is managed in:
- `tests/backend/conftest.py` - Pytest fixtures and configuration
- `apps/backend/pytest.ini` - Pytest settings

## Adding New Tests

1. Choose the appropriate test type (unit, integration, property, performance)
2. Create test file in the corresponding directory
3. Follow existing naming conventions: `test_*.py`
4. Use fixtures from `conftest.py` for common setup
5. Run tests to verify they pass

## Best Practices

- Keep unit tests fast and isolated
- Use integration tests for cross-component verification
- Use property-based tests for correctness properties
- Use performance tests for load and stress testing
- Mock external dependencies in unit tests
- Use real dependencies in integration tests
