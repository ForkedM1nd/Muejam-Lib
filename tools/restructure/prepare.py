#!/usr/bin/env python3
"""
Phase 1: Preparation Script for Monorepo Restructure

This script creates the new monorepo directory structure and updates .gitignore
to ensure build artifacts remain ignored.

Requirements: 1.1, 1.2, 1.3, 1.4, 3.7
"""

import os
import sys
from pathlib import Path


class DirectoryStructureManager:
    """Creates and validates monorepo directory structure."""
    
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        
    def create_apps_directory(self) -> None:
        """Create apps/ with backend/ and frontend/ subdirectories."""
        apps_dir = self.repo_root / "apps"
        apps_dir.mkdir(exist_ok=True)
        
        # Create subdirectories (empty for now, files will be moved in Phase 2)
        (apps_dir / "backend").mkdir(exist_ok=True)
        (apps_dir / "frontend").mkdir(exist_ok=True)
        
        # Create placeholder README
        readme_content = """# Apps Directory

This directory contains all deployable applications in the monorepo.

## Structure

- `backend/` - Django REST API
- `frontend/` - Vite React application

Each app is independently deployable and may have its own dependencies,
configuration, and build process.
"""
        (apps_dir / "README.md").write_text(readme_content)
        print("✓ Created apps/ directory with backend/ and frontend/ subdirectories")
        
    def create_packages_directory(self) -> None:
        """Create packages/ with README.md."""
        packages_dir = self.repo_root / "packages"
        packages_dir.mkdir(exist_ok=True)
        
        readme_content = """# Packages Directory

This directory contains shared libraries and utilities used by multiple apps.

## Purpose

Shared packages promote code reuse and consistency across the monorepo.
Examples of shared packages might include:

- `@muejam/types` - Shared TypeScript type definitions
- `@muejam/utils` - Common utility functions
- `@muejam/ui-components` - Reusable React components

## Adding a New Package

To add a new shared package:

1. Create a new directory in `packages/`
2. Initialize with `package.json` or `setup.py`
3. Add package documentation
4. Update dependent apps to use the shared package
"""
        (packages_dir / "README.md").write_text(readme_content)
        print("✓ Created packages/ directory with README.md")
        
    def create_tools_directory(self) -> None:
        """Create tools/ with README.md."""
        tools_dir = self.repo_root / "tools"
        tools_dir.mkdir(exist_ok=True)
        
        readme_content = """# Tools Directory

This directory contains build tools, scripts, and utilities for repository management.

## Contents

- `setup.sh` - Linux/Mac setup script
- `setup.ps1` - Windows setup script
- `restructure/` - Monorepo restructure scripts

## Usage

Run the appropriate setup script for your platform to configure the development environment.
"""
        (tools_dir / "README.md").write_text(readme_content)
        print("✓ Created tools/ directory with README.md")
        
    def create_docs_directory(self) -> None:
        """Create docs/ with subdirectories for getting-started/, architecture/, deployment/, and specs/."""
        docs_dir = self.repo_root / "docs"
        docs_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (docs_dir / "getting-started").mkdir(exist_ok=True)
        (docs_dir / "architecture").mkdir(exist_ok=True)
        (docs_dir / "deployment").mkdir(exist_ok=True)
        
        # Create main docs README
        readme_content = """# Documentation

Welcome to the MueJam Library documentation.

## Contents

- [Getting Started](getting-started/) - Setup and development guides
- [Architecture](architecture/) - System architecture and API documentation
- [Deployment](deployment/) - Deployment guides and secrets management

## Quick Links

- [Quickstart Guide](getting-started/quickstart.md)
- [Development Guide](getting-started/development.md)
- [API Documentation](architecture/api.md)
- [Secrets Management](deployment/secrets.md)
"""
        (docs_dir / "README.md").write_text(readme_content)
        print("✓ Created docs/ directory with subdirectories")
        
    def create_tests_directory(self) -> None:
        """Create tests/ with README.md for integration tests."""
        tests_dir = self.repo_root / "tests"
        tests_dir.mkdir(exist_ok=True)
        
        readme_content = """# Integration Tests

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
"""
        (tests_dir / "README.md").write_text(readme_content)
        print("✓ Created tests/ directory with README.md")
        
    def validate_structure(self) -> bool:
        """Verify all required directories exist."""
        required_dirs = [
            "apps",
            "apps/backend",
            "apps/frontend",
            "packages",
            "tools",
            "docs",
            "docs/getting-started",
            "docs/architecture",
            "docs/deployment",
            "tests"
        ]
        
        all_exist = True
        for dir_path in required_dirs:
            full_path = self.repo_root / dir_path
            if not full_path.exists():
                print(f"✗ Missing directory: {dir_path}")
                all_exist = False
                
        if all_exist:
            print("✓ All required directories exist")
        return all_exist


class GitignoreUpdater:
    """Updates .gitignore to ensure build artifacts stay ignored."""
    
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.gitignore_path = repo_root / ".gitignore"
        
    def update_gitignore(self) -> None:
        """Ensure .gitignore includes all artifact patterns."""
        # Patterns that should be in .gitignore
        required_patterns = {
            ".coverage",
            ".hypothesis/",
            "htmlcov/",
            "venv/",
            "node_modules/",
            "dist/",
            "build/"
        }
        
        # Read current .gitignore
        if self.gitignore_path.exists():
            current_content = self.gitignore_path.read_text()
            current_lines = set(line.strip() for line in current_content.splitlines())
        else:
            current_content = ""
            current_lines = set()
            
        # Find missing patterns
        missing_patterns = required_patterns - current_lines
        
        if missing_patterns:
            # Add missing patterns
            if current_content and not current_content.endswith('\n'):
                current_content += '\n'
            
            current_content += "\n# Build artifacts (added by monorepo restructure)\n"
            for pattern in sorted(missing_patterns):
                current_content += f"{pattern}\n"
                
            self.gitignore_path.write_text(current_content)
            print(f"✓ Added {len(missing_patterns)} patterns to .gitignore")
        else:
            print("✓ .gitignore already contains all required patterns")
            
    def verify_artifacts_ignored(self) -> bool:
        """Verify all artifact patterns are in .gitignore."""
        required_patterns = {
            ".coverage",
            ".hypothesis/",
            "htmlcov/",
            "venv/",
            "node_modules/",
            "dist/",
            "build/"
        }
        
        if not self.gitignore_path.exists():
            print("✗ .gitignore file not found")
            return False
            
        content = self.gitignore_path.read_text()
        lines = set(line.strip() for line in content.splitlines())
        
        missing = required_patterns - lines
        if missing:
            print(f"✗ Missing patterns in .gitignore: {missing}")
            return False
            
        print("✓ All artifact patterns present in .gitignore")
        return True


def main():
    """Execute Phase 1: Preparation."""
    print("=" * 60)
    print("Phase 1: Monorepo Restructure - Preparation")
    print("=" * 60)
    print()
    
    # Get repository root (two levels up from this script)
    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent.parent
    
    print(f"Repository root: {repo_root}")
    print()
    
    # Create directory structure
    print("Creating directory structure...")
    print("-" * 60)
    manager = DirectoryStructureManager(repo_root)
    manager.create_apps_directory()
    manager.create_packages_directory()
    manager.create_tools_directory()
    manager.create_docs_directory()
    manager.create_tests_directory()
    print()
    
    # Validate structure
    print("Validating directory structure...")
    print("-" * 60)
    if not manager.validate_structure():
        print("\n✗ Directory structure validation failed")
        return 1
    print()
    
    # Update .gitignore
    print("Updating .gitignore...")
    print("-" * 60)
    gitignore_updater = GitignoreUpdater(repo_root)
    gitignore_updater.update_gitignore()
    print()
    
    # Verify .gitignore
    print("Verifying .gitignore...")
    print("-" * 60)
    if not gitignore_updater.verify_artifacts_ignored():
        print("\n✗ .gitignore verification failed")
        return 1
    print()
    
    print("=" * 60)
    print("✓ Phase 1 preparation complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Review the created directory structure")
    print("2. Commit changes: git add . && git commit -m 'Phase 1: Create monorepo directory structure'")
    print("3. Proceed to Phase 2: File moves")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
