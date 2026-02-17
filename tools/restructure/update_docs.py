#!/usr/bin/env python3
"""
Phase 5: Documentation Update Script for Monorepo Restructure

This script rewrites README.md for monorepo structure, creates CONTRIBUTING.md,
creates docs/README.md as documentation index, updates cross-references in all docs,
removes AI-generated language from docs, and validates all documentation links.

Requirements: 10.1, 10.2, 10.4, 10.5, 10.6
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Set, Tuple


class DocumentationConsolidator:
    """Moves and organizes documentation into docs/ directory."""
    
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.docs_dir = repo_root / "docs"
        
    def create_docs_index(self) -> None:
        """Create docs/README.md as documentation index."""
        index_content = """# MueJam Library Documentation

Welcome to the MueJam Library documentation. This directory contains comprehensive documentation for the project.

## Documentation Structure

### Getting Started
- [Quickstart Guide](getting-started/quickstart.md) - Get up and running quickly
- [Development Guide](getting-started/development.md) - Detailed development setup and workflows

### Architecture
- [Architecture Overview](architecture/overview.md) - System architecture and design decisions
- [API Documentation](architecture/api.md) - REST API endpoints and usage

### Deployment
- [Secrets Management](deployment/secrets.md) - Managing secrets and environment variables

### Specifications
- [Project Specifications](specs/) - Detailed feature specifications and design documents

## Quick Links

- [Main README](../README.md) - Project overview and quick start
- [Contributing Guidelines](../CONTRIBUTING.md) - How to contribute to the project
- [Docker Compose](../docker-compose.yml) - Container orchestration configuration

## Project Structure

```
muejam-library/
├── apps/              # Applications
│   ├── backend/       # Django REST API
│   └── frontend/      # React frontend
├── packages/          # Shared libraries (future)
├── tools/             # Build tools and scripts
├── docs/              # Documentation (you are here)
└── tests/             # Integration tests
```

## Additional Resources

- Backend API: http://localhost:8000/api/
- Frontend App: http://localhost:5173/
- API Documentation: http://localhost:8000/api/docs/
"""
        
        index_path = self.docs_dir / "README.md"
        index_path.write_text(index_content, encoding='utf-8')
        print(f"✓ Created documentation index: {index_path.relative_to(self.repo_root)}")
        
    def update_cross_references(self) -> None:
        """Update all internal documentation links."""
        # Path mappings for documentation moves
        path_mappings = {
            "QUICKSTART.md": "docs/getting-started/quickstart.md",
            "DEVELOPMENT.md": "docs/getting-started/development.md",
            "backend/API_DOCUMENTATION.md": "docs/architecture/api.md",
            "API_DOCUMENTATION.md": "docs/architecture/api.md",
            "SECRETS.md": "docs/deployment/secrets.md",
            "backend/": "apps/backend/",
            "frontend/": "apps/frontend/",
            ".kiro/specs/": "docs/specs/",
        }
        
        # Find all markdown files
        md_files = list(self.docs_dir.rglob("*.md"))
        md_files.append(self.repo_root / "README.md")
        
        # Check if CONTRIBUTING.md exists
        contributing_path = self.repo_root / "CONTRIBUTING.md"
        if contributing_path.exists():
            md_files.append(contributing_path)
        
        updated_count = 0
        
        for md_file in md_files:
            if not md_file.exists():
                continue
                
            content = md_file.read_text(encoding='utf-8')
            original_content = content
            
            # Update markdown links [text](path)
            for old_path, new_path in path_mappings.items():
                # Match markdown links
                pattern = r'\[([^\]]+)\]\(([^\)]*' + re.escape(old_path) + r'[^\)]*)\)'
                
                def replace_link(match):
                    text = match.group(1)
                    full_path = match.group(2)
                    # Replace the old path with new path
                    updated_path = full_path.replace(old_path, new_path)
                    # Adjust relative paths based on file location
                    updated_path = self._adjust_relative_path(md_file, updated_path)
                    return f'[{text}]({updated_path})'
                
                content = re.sub(pattern, replace_link, content)
            
            # Write back if changed
            if content != original_content:
                md_file.write_text(content, encoding='utf-8')
                print(f"  ✓ Updated links in: {md_file.relative_to(self.repo_root)}")
                updated_count += 1
        
        if updated_count == 0:
            print("✓ No cross-references needed updating")
        else:
            print(f"✓ Updated cross-references in {updated_count} files")
    
    def _adjust_relative_path(self, source_file: Path, target_path: str) -> str:
        """Adjust relative path based on source file location."""
        # If path is absolute or URL, don't adjust
        if target_path.startswith(('http://', 'https://', '/', '#')):
            return target_path
        
        # Calculate relative path from source to target
        try:
            source_dir = source_file.parent
            target_full = self.repo_root / target_path
            
            # If target doesn't exist, return as-is
            if not target_full.exists():
                return target_path
            
            # Calculate relative path
            rel_path = os.path.relpath(target_full, source_dir)
            return rel_path.replace('\\', '/')
        except:
            # If calculation fails, return original
            return target_path


class DocumentationRewriter:
    """Rewrites documentation to be professional and accurate."""
    
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        
        # AI-generated phrases to remove
        self.ai_phrases = [
            r"verification report",
            r"checkpoint",
            r"implementation summary",
            r"final verification",
            r"AI-generated",
            r"this document was generated",
            r"auto-generated",
            r"generated by AI",
        ]
        
    def rewrite_readme(self) -> None:
        """Rewrite README.md for monorepo structure."""
        readme_path = self.repo_root / "README.md"
        
        if not readme_path.exists():
            print("✗ README.md not found")
            return
        
        # Read current README
        content = readme_path.read_text(encoding='utf-8')
        
        # Check if already updated for monorepo
        if "monorepo" in content.lower() and "apps/" in content:
            print("✓ README.md already reflects monorepo structure")
            return
        
        # Create new README content
        new_content = """# MueJam Library

A minimal digital library platform for serial stories with an integrated micro-posting system called "Whispers".

## Project Structure

This is a monorepo containing multiple applications and shared packages:

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

## Quick Start

### Prerequisites

- Docker and Docker Compose V2
- Git

### Running the Application

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd muejam-library
   ```

2. Start all services with Docker Compose:
   ```bash
   docker-compose up
   ```

3. Access the application:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000/api
   - API Documentation: http://localhost:8000/api/docs

### Development Setup

For detailed development setup instructions, see:
- [Quickstart Guide](docs/getting-started/quickstart.md)
- [Development Guide](docs/getting-started/development.md)

## Features

- **Serial Fiction Library**: Browse, read, and manage serial stories
- **Whispers**: Micro-posting system for short updates and thoughts
- **User Authentication**: Secure registration and login with JWT tokens
- **Responsive Design**: Works on desktop and mobile devices
- **RESTful API**: Clean API design with comprehensive documentation

## Technology Stack

### Backend
- Django 5.1 with Django REST Framework
- PostgreSQL database
- Prisma ORM
- JWT authentication

### Frontend
- React 18 with TypeScript
- Vite build tool
- TanStack Query for data fetching
- React Router for navigation
- Tailwind CSS for styling

## Documentation

- [Documentation Index](docs/README.md)
- [API Documentation](docs/architecture/api.md)
- [Architecture Overview](docs/architecture/overview.md)
- [Contributing Guidelines](CONTRIBUTING.md)

## Development

### Backend Development

```bash
cd apps/backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Frontend Development

```bash
cd apps/frontend
npm install
npm run dev
```

### Running Tests

Backend tests:
```bash
cd apps/backend
pytest
```

Frontend tests:
```bash
cd apps/frontend
npm test
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

See [LICENSE](LICENSE) for details.
"""
        
        # Write new README
        readme_path.write_text(new_content, encoding='utf-8')
        print(f"✓ Rewrote README.md for monorepo structure")
    
    def create_contributing_guide(self) -> None:
        """Create CONTRIBUTING.md with contribution guidelines."""
        contributing_path = self.repo_root / "CONTRIBUTING.md"
        
        if contributing_path.exists():
            print("✓ CONTRIBUTING.md already exists")
            return
        
        contributing_content = """# Contributing to MueJam Library

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
"""
        
        contributing_path.write_text(contributing_content, encoding='utf-8')
        print(f"✓ Created CONTRIBUTING.md")
    
    def remove_ai_language(self, content: str) -> str:
        """Remove AI-generated phrases from documentation."""
        cleaned = content
        
        for phrase_pattern in self.ai_phrases:
            # Case-insensitive replacement
            cleaned = re.sub(phrase_pattern, "", cleaned, flags=re.IGNORECASE)
        
        # Clean up multiple blank lines
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        
        return cleaned
    
    def update_structure_references(self, content: str) -> str:
        """Update references to old directory structure."""
        # Update path references
        replacements = {
            r'\bbackend/': 'apps/backend/',
            r'\bfrontend/': 'apps/frontend/',
            r'\.kiro/specs/': 'docs/specs/',
        }
        
        updated = content
        for old, new in replacements.items():
            updated = re.sub(old, new, updated)
        
        return updated
    
    def process_all_docs(self) -> None:
        """Process all documentation files to remove AI language and update references."""
        docs_dir = self.repo_root / "docs"
        
        # Find all markdown files in docs/
        md_files = list(docs_dir.rglob("*.md"))
        
        processed_count = 0
        
        for md_file in md_files:
            if not md_file.exists():
                continue
            
            content = md_file.read_text(encoding='utf-8')
            original_content = content
            
            # Remove AI language
            content = self.remove_ai_language(content)
            
            # Update structure references
            content = self.update_structure_references(content)
            
            # Write back if changed
            if content != original_content:
                md_file.write_text(content, encoding='utf-8')
                print(f"  ✓ Processed: {md_file.relative_to(self.repo_root)}")
                processed_count += 1
        
        if processed_count == 0:
            print("✓ No documentation files needed processing")
        else:
            print(f"✓ Processed {processed_count} documentation files")
    
    def validate_links(self) -> bool:
        """Verify all documentation links are valid."""
        docs_dir = self.repo_root / "docs"
        
        # Find all markdown files
        md_files = list(docs_dir.rglob("*.md"))
        md_files.append(self.repo_root / "README.md")
        
        contributing_path = self.repo_root / "CONTRIBUTING.md"
        if contributing_path.exists():
            md_files.append(contributing_path)
        
        broken_links = []
        
        for md_file in md_files:
            if not md_file.exists():
                continue
            
            content = md_file.read_text(encoding='utf-8')
            
            # Find all markdown links [text](path)
            link_pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
            matches = re.finditer(link_pattern, content)
            
            for match in matches:
                link_text = match.group(1)
                link_path = match.group(2)
                
                # Skip external URLs and anchors
                if link_path.startswith(('http://', 'https://', '#', 'mailto:')):
                    continue
                
                # Remove anchor from path
                link_path = link_path.split('#')[0]
                
                if not link_path:
                    continue
                
                # Resolve relative path
                if link_path.startswith('/'):
                    target_path = self.repo_root / link_path.lstrip('/')
                else:
                    target_path = md_file.parent / link_path
                
                # Normalize path
                try:
                    target_path = target_path.resolve()
                except:
                    broken_links.append((md_file, link_text, link_path))
                    continue
                
                # Check if target exists
                if not target_path.exists():
                    broken_links.append((md_file, link_text, link_path))
        
        if broken_links:
            print(f"✗ Found {len(broken_links)} broken links:")
            for source, text, link in broken_links:
                print(f"  - In {source.relative_to(self.repo_root)}: [{text}]({link})")
            return False
        
        print("✓ All documentation links are valid")
        return True


def main():
    """Execute Phase 5: Documentation Updates."""
    print("=" * 60)
    print("Phase 5: Monorepo Restructure - Documentation Updates")
    print("=" * 60)
    print()
    
    # Get repository root
    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent.parent
    
    print(f"Repository root: {repo_root}")
    print()
    
    # Create documentation index
    print("Creating documentation index...")
    print("-" * 60)
    consolidator = DocumentationConsolidator(repo_root)
    consolidator.create_docs_index()
    print()
    
    # Rewrite README.md
    print("Rewriting README.md...")
    print("-" * 60)
    rewriter = DocumentationRewriter(repo_root)
    rewriter.rewrite_readme()
    print()
    
    # Create CONTRIBUTING.md
    print("Creating CONTRIBUTING.md...")
    print("-" * 60)
    rewriter.create_contributing_guide()
    print()
    
    # Process all documentation files
    print("Processing documentation files...")
    print("-" * 60)
    rewriter.process_all_docs()
    print()
    
    # Update cross-references
    print("Updating cross-references...")
    print("-" * 60)
    consolidator.update_cross_references()
    print()
    
    # Validate links
    print("Validating documentation links...")
    print("-" * 60)
    if not rewriter.validate_links():
        print("\n⚠ Warning: Some documentation links are broken")
        print("Please review and fix broken links manually")
    print()
    
    print("=" * 60)
    print("✓ Phase 5 documentation updates complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Review the updated documentation")
    print("2. Fix any broken links if reported")
    print("3. Commit changes: git add . && git commit -m 'Phase 5: Update documentation for monorepo structure'")
    print("4. Proceed to Phase 6: Validation")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
