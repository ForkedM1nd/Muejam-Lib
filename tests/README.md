# Tests

This directory contains all tests for the MueJam Library monorepo.

## Structure

```
tests/
├── backend/              # Backend tests
│   ├── unit/             # Unit tests for backend components
│   ├── integration/      # Backend integration tests
│   ├── e2e/              # End-to-end backend tests
│   ├── infrastructure/   # Infrastructure code tests
│   ├── property/         # Property-based tests
│   ├── performance/      # Performance and load tests
│   └── apps/             # Django app-specific tests
│       ├── core/         # Core app tests
│       ├── moderation/   # Moderation app tests
│       ├── users/        # Users app tests
│       └── ...           # Other app tests
├── frontend/             # Frontend tests
│   ├── integration/      # Frontend integration tests
│   └── e2e/              # End-to-end frontend tests
└── README.md             # This file
```

## Backend Tests

### Unit Tests
Located in `apps/backend/tests/unit`, these test individual components in isolation.

```bash
# Run all backend unit tests
cd apps/backend
pytest ../../../tests/backend/unit/

# Or from root
pytest tests/backend/unit/
```

### Integration Tests
Located in `apps/backend/tests/integration`, these verify interactions between components.

```bash
# Run backend integration tests
pytest tests/backend/integration/
```

### End-to-End Tests
Located in `apps/backend/tests/e2e`, these test complete user workflows and API interactions.

```bash
# Run backend e2e tests
pytest tests/backend/e2e/
```

### Infrastructure Tests
Located in `apps/backend/tests/infrastructure`, these test infrastructure code (caching, monitoring, configuration).

```bash
# Run infrastructure tests
pytest tests/backend/infrastructure/
```

### Property-Based Tests
Located in `apps/backend/tests/property`, these use property-based testing to verify correctness properties.

```bash
# Run property-based tests
pytest tests/backend/property/
```

### Performance Tests
Located in `apps/backend/tests/performance`, these test system performance and load handling.

```bash
# Run performance tests
pytest tests/backend/performance/
```

### Django App Tests
Located in `apps/backend/tests/apps`, these contain Django app-specific tests organized by app name.

```bash
# Run tests for a specific app
pytest tests/backend/apps/users/

# Run all app tests
pytest tests/backend/apps/
```

## Frontend Tests

### Integration Tests
Located in `tests/frontend/integration/`, these verify frontend component interactions.

### End-to-End Tests
Located in `tests/frontend/e2e/`, these test complete user workflows in the browser.

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
- `apps/backend/tests/conftest.py` - Pytest fixtures and configuration
- `apps/backend/pytest.ini` - Pytest settings

## Adding New Tests

1. Choose the appropriate test type:
   - **Unit tests**: Individual component testing → `apps/backend/tests/unit`
   - **Integration tests**: Cross-component testing → `apps/backend/tests/integration` or `tests/frontend/integration/`
   - **E2E tests**: Complete workflow testing → `apps/backend/tests/e2e` or `tests/frontend/e2e/`
   - **Infrastructure tests**: Infrastructure code testing → `apps/backend/tests/infrastructure`
   - **Property tests**: Property-based testing → `apps/backend/tests/property`
   - **Performance tests**: Load and stress testing → `apps/backend/tests/performance`
   - **Django app tests**: App-specific testing → `apps/backend/tests/apps/<app_name>`
2. Create test file in the corresponding directory
3. Follow existing naming conventions: `test_*.py`
4. Use fixtures from `conftest.py` for common setup
5. Run tests to verify they pass

## Test Organization Strategy

**Fully Centralized Tests**: All tests are organized in the top-level `tests/` directory for better discoverability, organization, and separation of concerns. This includes:
- Django app-specific tests in `apps/backend/tests/apps`
- Cross-cutting tests (integration, e2e, infrastructure, property, performance) in their respective directories

This centralized approach provides:
- Clear separation between source code and test code
- Easier test discovery and navigation
- Consistent test organization across the entire monorepo
- Better support for cross-app integration testing

## Best Practices

- Keep unit tests fast and isolated
- Use integration tests for cross-component verification
- Use property-based tests for correctness properties
- Use performance tests for load and stress testing
- Mock external dependencies in unit tests
- Use real dependencies in integration tests
