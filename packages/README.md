# Packages Directory

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
