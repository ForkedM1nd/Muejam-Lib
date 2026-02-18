#!/usr/bin/env python3
"""
Unit tests for ConfigUpdater

Tests the configuration file update functionality for the monorepo restructure.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from config_updater import ConfigUpdater


@pytest.fixture
def temp_repo():
    """Create a temporary repository structure for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    
    # Create directory structure
    (temp_dir / "apps" / "backend" / "config").mkdir(parents=True)
    (temp_dir / "apps" / "backend" / "apps" / "security").mkdir(parents=True)
    (temp_dir / "apps" / "frontend").mkdir(parents=True)
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)


def test_update_django_settings_installed_apps(temp_repo):
    """Test updating INSTALLED_APPS in Django settings."""
    settings_path = temp_repo / "apps" / "backend" / "config" / "settings.py"
    settings_path.write_text("""
INSTALLED_APPS = [
    'django.contrib.admin',
    'apps.users',
    'apps.moderation',
]
""")
    
    updater = ConfigUpdater(temp_repo)
    movements = [
        ("apps/backend/apps/users", "apps/backend/apps/accounts"),
    ]
    
    result = updater.update_django_settings(movements)
    
    assert result is True
    content = settings_path.read_text()
    assert "'apps.accounts'" in content
    assert "'apps.users'" not in content


def test_update_django_settings_imports(temp_repo):
    """Test updating import statements in Django settings."""
    settings_path = temp_repo / "apps" / "backend" / "config" / "settings.py"
    settings_path.write_text("""
from infrastructure.config_validator import validate_config
from infrastructure.cache import setup_cache
""")
    
    updater = ConfigUpdater(temp_repo)
    movements = [
        ("apps/backend/infrastructure/config_validator.py", "apps/backend/apps/admin/config_validator.py"),
    ]
    
    result = updater.update_django_settings(movements)
    
    assert result is True
    content = settings_path.read_text()
    assert "from apps.admin.config_validator import" in content


def test_update_pytest_ini(temp_repo):
    """Test updating pytest.ini testpaths."""
    pytest_ini_path = temp_repo / "apps" / "backend" / "pytest.ini"
    pytest_ini_path.write_text("""
[pytest]
testpaths = apps infrastructure/tests
""")
    
    updater = ConfigUpdater(temp_repo)
    movements = [
        ("apps/backend/infrastructure/tests", "tests/backend/infrastructure"),
    ]
    
    result = updater.update_pytest_ini(movements)
    
    assert result is True
    content = pytest_ini_path.read_text()
    assert "../../tests/backend/infrastructure" in content or "tests/backend/infrastructure" in content


def test_update_docker_compose(temp_repo):
    """Test updating docker-compose.yml paths."""
    docker_compose_path = temp_repo / "docker-compose.yml"
    docker_compose_path.write_text("""
version: '3.8'
services:
  backend:
    build:
      context: ./apps/backend
    volumes:
      - ./apps/backend:/app
      - ./scripts/database:/scripts
""")
    
    updater = ConfigUpdater(temp_repo)
    movements = [
        ("apps/backend/scripts", "scripts/database"),
    ]
    
    result = updater.update_docker_compose(movements)
    
    assert result is True
    content = docker_compose_path.read_text()
    assert "./scripts/database" in content


def test_update_dockerfile(temp_repo):
    """Test updating Dockerfile COPY and WORKDIR instructions."""
    dockerfile_path = temp_repo / "apps" / "backend" / "Dockerfile"
    dockerfile_path.write_text("""
FROM python:3.11

WORKDIR /app/backend
COPY apps/backend/requirements.txt .
COPY apps/backend/ .

RUN pip install -r requirements.txt
""")
    
    updater = ConfigUpdater(temp_repo)
    movements = [
        ("apps/backend", "backend"),
    ]
    
    result = updater.update_dockerfile(Path("apps/backend/Dockerfile"), movements)
    
    assert result is True
    content = dockerfile_path.read_text()
    assert "COPY backend/requirements.txt" in content
    assert "COPY backend/" in content


def test_update_package_json(temp_repo):
    """Test updating package.json scripts."""
    package_json_path = temp_repo / "apps" / "frontend" / "package.json"
    package_json_path.write_text("""
{
  "name": "frontend",
  "scripts": {
    "test": "vitest run apps/frontend/src/tests"
  }
}
""")
    
    updater = ConfigUpdater(temp_repo)
    movements = [
        ("apps/frontend/src/tests", "tests/frontend"),
    ]
    
    result = updater.update_package_json(movements)
    
    assert result is True
    content = package_json_path.read_text()
    assert "tests/frontend" in content


def test_update_all_configs(temp_repo):
    """Test updating all configuration files at once."""
    # Create all config files
    settings_path = temp_repo / "apps" / "backend" / "config" / "settings.py"
    settings_path.write_text("INSTALLED_APPS = ['apps.users']")
    
    pytest_ini_path = temp_repo / "apps" / "backend" / "pytest.ini"
    pytest_ini_path.write_text("[pytest]\ntestpaths = apps")
    
    docker_compose_path = temp_repo / "docker-compose.yml"
    docker_compose_path.write_text("volumes:\n  - ./apps/backend:/app")
    
    dockerfile_path = temp_repo / "apps" / "backend" / "Dockerfile"
    dockerfile_path.write_text("COPY apps/backend .")
    
    package_json_path = temp_repo / "apps" / "frontend" / "package.json"
    package_json_path.write_text('{"scripts": {"test": "vitest"}}')
    
    updater = ConfigUpdater(temp_repo)
    movements = [
        ("apps/backend/apps/users", "apps/backend/apps/accounts"),
    ]
    
    results = updater.update_all_configs(movements)
    
    assert results['django_settings'] is True
    assert results['pytest_ini'] is True
    assert results['docker_compose'] is True
    assert results['dockerfiles'] is True
    assert results['package_json'] is True


def test_error_handling_missing_file(temp_repo):
    """Test error handling when config file doesn't exist."""
    updater = ConfigUpdater(temp_repo)
    movements = []
    
    result = updater.update_django_settings(movements)
    
    assert result is False
    errors = updater.get_errors()
    assert len(errors) > 0
    assert "not found" in errors[0][1].lower()


def test_get_updated_files(temp_repo):
    """Test tracking of updated files."""
    settings_path = temp_repo / "apps" / "backend" / "config" / "settings.py"
    settings_path.write_text("INSTALLED_APPS = ['apps.users']")
    
    updater = ConfigUpdater(temp_repo)
    movements = [
        ("apps/backend/apps/users", "apps/backend/apps/accounts"),
    ]
    
    updater.update_django_settings(movements)
    updated_files = updater.get_updated_files()
    
    assert len(updated_files) > 0
    assert any("settings.py" in f for f in updated_files)


def test_clear_state(temp_repo):
    """Test clearing updater state."""
    settings_path = temp_repo / "apps" / "backend" / "config" / "settings.py"
    settings_path.write_text("INSTALLED_APPS = ['apps.users']")
    
    updater = ConfigUpdater(temp_repo)
    movements = [
        ("apps/backend/apps/users", "apps/backend/apps/accounts"),
    ]
    
    updater.update_django_settings(movements)
    assert len(updater.get_updated_files()) > 0
    
    updater.clear_state()
    assert len(updater.get_updated_files()) == 0
    assert len(updater.get_errors()) == 0


def test_no_changes_needed(temp_repo):
    """Test when no changes are needed in config files."""
    settings_path = temp_repo / "apps" / "backend" / "config" / "settings.py"
    settings_path.write_text("INSTALLED_APPS = ['apps.users']")
    
    updater = ConfigUpdater(temp_repo)
    movements = [
        ("apps/backend/apps/other", "apps/backend/apps/different"),
    ]
    
    result = updater.update_django_settings(movements)
    
    assert result is True
    # File should not be in updated list since no changes were made
    updated_files = updater.get_updated_files()
    assert len(updated_files) == 0


def test_multiple_movements(temp_repo):
    """Test handling multiple file movements."""
    settings_path = temp_repo / "apps" / "backend" / "config" / "settings.py"
    settings_path.write_text("""
INSTALLED_APPS = [
    'apps.users',
    'apps.moderation',
    'apps.security',
]
""")
    
    updater = ConfigUpdater(temp_repo)
    movements = [
        ("apps/backend/apps/users", "apps/backend/apps/accounts"),
        ("apps/backend/apps/moderation", "apps/backend/apps/content"),
    ]
    
    result = updater.update_django_settings(movements)
    
    assert result is True
    content = settings_path.read_text()
    assert "'apps.accounts'" in content
    assert "'apps.content'" in content
    assert "'apps.users'" not in content
    assert "'apps.moderation'" not in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
