#!/usr/bin/env python3
"""
Complete cleanup script - moves ALL remaining tests and docs to proper locations.

This script finds and moves:
- All test files from apps/backend subdirectories to tests/backend
- All .md files from apps/backend subdirectories to docs/backend
"""

import argparse
import logging
import sys
from pathlib import Path

# Import utility modules
sys.path.insert(0, str(Path(__file__).parent))
from file_mover import move_file
from git_integration import stage_changes, create_commit, get_repository_root

# Configure logging
logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for the script."""
    log_level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def find_all_test_files(backend_dir: Path) -> list:
    """Find all test files in apps/backend subdirectories."""
    test_files = []
    
    # Find all Python test files
    for pattern in ['test_*.py', '*_test.py', '*_tests.py']:
        test_files.extend(backend_dir.rglob(pattern))
    
    # Exclude files already in tests/ directory
    test_files = [f for f in test_files if 'tests' not in f.parts or f.parts[f.parts.index('backend') + 1] != 'tests']
    
    return test_files


def find_all_md_files(backend_dir: Path) -> list:
    """Find all .md files in apps/backend subdirectories."""
    md_files = []
    
    # Find all markdown files
    md_files.extend(backend_dir.rglob('*.md'))
    
    # Exclude README.md files in root directories
    md_files = [f for f in md_files if f.name != 'README.md' or f.parent != backend_dir]
    
    return md_files


def move_test_files(repo_root: Path, dry_run: bool = False) -> int:
    """Move all test files to tests/backend."""
    backend_dir = repo_root / "apps" / "backend"
    tests_dir = repo_root / "tests" / "backend"
    
    logger.info("Finding all test files in apps/backend...")
    test_files = find_all_test_files(backend_dir)
    
    logger.info(f"Found {len(test_files)} test files to move")
    
    if dry_run:
        for test_file in test_files:
            logger.info(f"  Would move: {test_file.relative_to(repo_root)}")
        return len(test_files)
    
    moved_count = 0
    for test_file in test_files:
        try:
            # Determine destination path
            # Keep the subdirectory structure relative to apps/backend
            rel_path = test_file.relative_to(backend_dir)
            
            # Map infrastructure/tests -> tests/backend/infrastructure
            # Map apps/users/test_*.py -> tests/backend/apps/users
            if 'tests' in rel_path.parts:
                # Remove 'tests' from the path
                parts = list(rel_path.parts)
                parts.remove('tests')
                rel_path = Path(*parts) if parts else Path(rel_path.name)
            
            dest_file = tests_dir / rel_path
            
            logger.info(f"Moving: {test_file.relative_to(repo_root)} -> {dest_file.relative_to(repo_root)}")
            move_file(test_file, dest_file)
            moved_count += 1
            
        except Exception as e:
            logger.error(f"Failed to move {test_file}: {e}")
    
    logger.info(f"✓ Moved {moved_count} test files")
    return moved_count


def move_md_files(repo_root: Path, dry_run: bool = False) -> int:
    """Move all .md files to docs/backend."""
    backend_dir = repo_root / "apps" / "backend"
    docs_dir = repo_root / "docs" / "backend"
    
    logger.info("Finding all .md files in apps/backend...")
    md_files = find_all_md_files(backend_dir)
    
    # Filter to only docs directory
    md_files = [f for f in md_files if 'docs' in f.parts]
    
    logger.info(f"Found {len(md_files)} markdown files to move")
    
    if dry_run:
        for md_file in md_files:
            logger.info(f"  Would move: {md_file.relative_to(repo_root)}")
        return len(md_files)
    
    moved_count = 0
    for md_file in md_files:
        try:
            # Determine destination path
            # Keep the subdirectory structure relative to apps/backend/docs
            backend_docs_dir = backend_dir / "docs"
            rel_path = md_file.relative_to(backend_docs_dir)
            
            dest_file = docs_dir / rel_path
            
            logger.info(f"Moving: {md_file.relative_to(repo_root)} -> {dest_file.relative_to(repo_root)}")
            move_file(md_file, dest_file)
            moved_count += 1
            
        except Exception as e:
            logger.error(f"Failed to move {md_file}: {e}")
    
    logger.info(f"✓ Moved {moved_count} markdown files")
    return moved_count


def cleanup_empty_dirs(repo_root: Path, dry_run: bool = False) -> None:
    """Remove empty directories."""
    if dry_run:
        logger.info("[DRY RUN] Would clean up empty directories")
        return
    
    backend_dir = repo_root / "apps" / "backend"
    
    # Remove empty test directories
    for tests_dir in backend_dir.rglob('tests'):
        if tests_dir.is_dir() and not any(tests_dir.iterdir()):
            logger.info(f"Removing empty directory: {tests_dir.relative_to(repo_root)}")
            tests_dir.rmdir()
    
    # Remove empty docs subdirectories
    docs_dir = backend_dir / "docs"
    if docs_dir.exists():
        for subdir in docs_dir.iterdir():
            if subdir.is_dir() and not any(subdir.iterdir()):
                logger.info(f"Removing empty directory: {subdir.relative_to(repo_root)}")
                subdir.rmdir()


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Complete cleanup - move ALL remaining tests and docs"
    )
    
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without executing')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--skip-commit', action='store_true', help='Skip git commit')
    
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    
    logger.info("=" * 70)
    logger.info("Complete Cleanup Script")
    logger.info("=" * 70)
    
    try:
        # Find repository root
        repo_root = get_repository_root()
        logger.info(f"Repository root: {repo_root}")
        
        # Move test files
        test_count = move_test_files(repo_root, args.dry_run)
        
        # Move markdown files
        md_count = move_md_files(repo_root, args.dry_run)
        
        # Cleanup empty directories
        cleanup_empty_dirs(repo_root, args.dry_run)
        
        # Commit changes
        if not args.dry_run and not args.skip_commit and (test_count > 0 or md_count > 0):
            logger.info("Committing changes to git...")
            try:
                stage_changes(repo_root)
                commit_sha = create_commit(
                    repo_root,
                    f"Complete cleanup: move {test_count} test files and {md_count} docs to proper locations"
                )
                logger.info(f"✓ Changes committed: {commit_sha}")
            except Exception as e:
                logger.error(f"Failed to commit changes: {e}")
                return 1
        
        logger.info("=" * 70)
        logger.info("Complete cleanup finished successfully!")
        logger.info(f"Moved {test_count} test files and {md_count} markdown files")
        logger.info("=" * 70)
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("\nCleanup cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
