"""
Pytest configuration for password reset tests.

Configures hypothesis for property-based testing with minimum 100 iterations.
"""
import pytest
from hypothesis import settings, Verbosity
from django.conf import settings as django_settings

# Configure hypothesis settings for all property tests
settings.register_profile(
    "password_reset",
    max_examples=100,  # Minimum 100 iterations as per design document
    verbosity=Verbosity.normal,
    deadline=None,  # Disable deadline for async tests
)

# Activate the profile
settings.load_profile("password_reset")


@pytest.fixture(scope='session', autouse=True)
def disable_database_router():
    """Disable database router for tests to avoid replica connection issues."""
    original_routers = django_settings.DATABASE_ROUTERS
    django_settings.DATABASE_ROUTERS = []
    yield
    django_settings.DATABASE_ROUTERS = original_routers


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        'id': 'test-user-123',
        'email': 'test@example.com',
        'password_hash': '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS.sC',
    }


@pytest.fixture
def sample_token_data():
    """Sample token data for testing."""
    return {
        'token': 'test-token-abc123',
        'user_id': 'test-user-123',
        'expires_at': None,  # Will be set in tests
    }
