# Packages Directory

This directory is reserved for shared libraries and utilities that are used across multiple applications in the monorepo.

## Current Status

**Empty** - No shared packages yet.

## When to Create a Shared Package

Create a shared package when you have code that:

1. **Is used by multiple apps** - The same code is needed in 2+ applications (e.g., frontend + mobile app)
2. **Is framework-agnostic** - Not tightly coupled to a specific framework (React, Django, etc.)
3. **Has a clear purpose** - Solves a specific, well-defined problem
4. **Is stable** - The API is unlikely to change frequently

## Current Code Organization

### Frontend-Specific Code
Location: `apps/frontend/src/lib/` and `apps/frontend/src/types/`
- Utilities: React/Tailwind-specific helpers
- Types: API response interfaces for MueJam
- **Why not shared?** These are tightly coupled to the React frontend

### Backend-Specific Code
Location: `apps/backend/apps/core/`
- Utilities: Django-specific helpers (pagination, caching, rate limiting)
- **Why not shared?** These are tightly coupled to Django/Python

## Examples of Future Shared Packages

When the monorepo grows, you might create:

- `@muejam/types` - Shared TypeScript type definitions (when adding mobile app)
- `@muejam/api-client` - Shared API client logic (when adding admin dashboard)
- `@muejam/validation` - Shared validation rules (when frontend and backend need same rules)
- `@muejam/constants` - Shared constants (when multiple apps need same values)

## Creating a New Package

When you're ready to create a shared package:

1. Create a new directory: `packages/{package-name}/`
2. Initialize with `package.json` (TypeScript) or `setup.py` (Python)
3. Add a README.md explaining the package purpose
4. Configure build/transpilation if needed
5. Update dependent apps to import from the shared package

## Documentation

For more information about the monorepo structure, see [docs/packages.md](../docs/packages.md).
