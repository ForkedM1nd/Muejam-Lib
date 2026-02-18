#!/usr/bin/env python3
"""
Reverse reorganization script - moves tests and docs back to their original locations.

This script reverses the reorganization by:
- Moving backend tests from apps/backend/tests/ back to tests/backend/
- Moving frontend tests from apps/frontend/src/test/ to tests/frontend/
- Moving backend docs from docs/backend/ back to apps/backend/docs/
- Moving frontend docs from docs/frontend/ back to apps/frontend/docs/
- Updating all import statements and file references
- Committing changes to git

Usage:
    python scripts/reorganize/reverse_reorganize.py [--dry-run] [--verbose] [--skip-commit]
"""

import argparse
import logging
import sys
from pathlib import Path

# Import utility modules
try:
    from file_mover import move_directory, move_file, remove_empty_directory
    from import_updater import rewrite_file_imports
    from reference_updater import find_file_references, update_reference, update_pytest_config
    from cleanup import find_cache_directories, find_compiled_files, find_log_files, remove_paths
    from git_integration import stage_changes, create_commit, verify_clean_state, get_repository_root
except ImportError:
    # Add parent directory to path
    sys.path.insert(0, str(Path(__file__).parent))
    from file_mover import move_directory, move_file, remove_empty_directory
    from import_updater import rewrite_file_imports
    from reference_updater import find_file_references, update_reference, update_pytest_config
    from cleanup import find_cache_directories, find_compiled_files, find_log_files, remove_paths
    from git_integration import stage_changes, create_commit, verify_clean_state, get_repository_root

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


def reverse_backend_tests(repo_root: Path, dry_run: bool = False) -> bool:
    """Move backend tests from apps/backend/tests/ back to tests/backend/."""
    logger.info(f"{'[DRY RUN] ' if dry_run else ''}Moving backend tests back to tests/backend/...")
    
    source_dir = repo_root / "apps" / "backend" / "tests"
    dest_dir = repo_root / "tests" / "backend"
    
    if not source_dir.exists():
        logger.warning(f"Source directory does not exist: {source_dir}")
        return False
    
    if dry_run:
        test_files = list(source_dir.rglob("*.py"))
        logger.info(f"  Would move {len(test_files)} Python files")
        return True
    
    try:
        # Move the directory
        move_directory(source_dir, dest_dir)
        logger.info(f"✓ Moved tests to {dest_dir}")
        
        # Update import statements
        import_updates = {
            "apps.backend.tests": "tests.backend"
        }
        
        python_files = list(dest_dir.rglob("*.py"))
        logger.info(f"Updating imports in {len(python_files)} files...")
        
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if "apps.backend.tests" in content:
                    rewrite_file_imports(py_file, import_updates)
            except Exception as e:
                logger.warning(f"Failed to update {py_file}: {e}")
        
        # Update conftest.py files
        conftest_files = list(repo_root.rglob("conftest.py"))
        for conftest in conftest_files:
            try:
                with open(conftest, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if "apps.backend.tests" in content or "apps/backend/tests" in content:
                    rewrite_file_imports(conftest, import_updates)
                    
                    with open(conftest, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    updated = False
                    for i, line in enumerate(lines):
                        if "apps/backend/tests" in line:
                            lines[i] = line.replace("apps/backend/tests", "tests/backend")
                            updated = True
                    
                    if updated:
                        with open(conftest, 'w', encoding='utf-8') as f:
                            f.writelines(lines)
            except Exception as e:
                logger.warning(f"Failed to update conftest {conftest}: {e}")
        
        logger.info("✓ Backend tests moved successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error moving backend tests: {e}", exc_info=True)
        return False


def reverse_backend_docs(repo_root: Path, dry_run: bool = False) -> bool:
    """Move backend docs from docs/backend/ back to apps/backend/docs/."""
    logger.info(f"{'[DRY RUN] ' if dry_run else ''}Moving backend docs back to apps/backend/docs/...")
    
    source_dir = repo_root / "docs" / "backend"
    dest_dir = repo_root / "apps" / "backend" / "docs"
    
    if not source_dir.exists():
        logger.warning(f"Source directory does not exist: {source_dir}")
        return False
    
    if dry_run:
        doc_files = list(source_dir.rglob("*.md"))
        logger.info(f"  Would move {len(doc_files)} markdown files")
        return True
    
    try:
        # Move the directory
        move_directory(source_dir, dest_dir)
        logger.info(f"✓ Moved docs to {dest_dir}")
        
        # Update documentation references
        path_mapping = {
            "docs/backend": "apps/backend/docs",
            "../../": "../../../",  # Adjust relative paths
        }
        
        md_files = list(dest_dir.rglob("*.md"))
        logger.info(f"Updating references in {len(md_files)} files...")
        
        for md_file in md_files:
            try:
                refs = find_file_references(md_file)
                if refs:
                    with open(md_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    lines = content.split('\n')
                    
                    for ref in refs:
                        updated_ref = update_reference(ref, path_mapping)
                        if updated_ref and updated_ref.original_text != ref.original_text:
                            line_idx = ref.line_number - 1
                            if 0 <= line_idx < len(lines):
                                lines[line_idx] = lines[line_idx].replace(
                                    ref.original_text, updated_ref.original_text
                                )
                    
                    with open(md_file, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(lines))
            except Exception as e:
                logger.warning(f"Failed to update {md_file}: {e}")
        
        logger.info("✓ Backend docs moved successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error moving backend docs: {e}", exc_info=True)
        return False


def update_pytest_configs(repo_root: Path, dry_run: bool = False) -> bool:
    """Update pytest configuration files."""
    if dry_run:
        logger.info("[DRY RUN] Would update pytest configurations")
        return True
    
    logger.info("Updating pytest configurations...")
    
    pytest_configs = [
        repo_root / "apps" / "backend" / "pytest.ini",
        repo_root / "pytest.ini",
    ]
    
    for config_file in pytest_configs:
        if config_file.exists():
            try:
                update_pytest_config(config_file, "tests/backend")
                logger.info(f"✓ Updated {config_file}")
            except Exception as e:
                logger.warning(f"Failed to update {config_file}: {e}")
    
    return True


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Reverse reorganization - move tests and docs back to original locations"
    )
    
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without executing')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--skip-commit', action='store_true', help='Skip git commit')
    
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    
    logger.info("=" * 70)
    logger.info("Reverse Reorganization Script")
    logger.info("=" * 70)
    
    try:
        # Find repository root
        repo_root = get_repository_root()
        logger.info(f"Repository root: {repo_root}")
        
        # Check for uncommitted changes
        if not args.dry_run and not args.skip_commit:
            if not verify_clean_state(repo_root):
                logger.error("Repository has uncommitted changes. Please commit or stash them first.")
                return 1
        
        # Reverse backend tests
        if not reverse_backend_tests(repo_root, args.dry_run):
            logger.error("Failed to reverse backend tests")
            return 1
        
        # Reverse backend docs
        if not reverse_backend_docs(repo_root, args.dry_run):
            logger.warning("Failed to reverse backend docs (may not exist)")
        
        # Update pytest configs
        if not update_pytest_configs(repo_root, args.dry_run):
            logger.warning("Failed to update pytest configs")
        
        # Commit changes
        if not args.dry_run and not args.skip_commit:
            logger.info("Committing changes to git...")
            try:
                stage_changes(repo_root)
                commit_sha = create_commit(
                    repo_root,
                    "Reverse reorganization: move tests back to tests/ and docs back to apps/"
                )
                logger.info(f"✓ Changes committed: {commit_sha}")
            except Exception as e:
                logger.error(f"Failed to commit changes: {e}")
                return 1
        
        logger.info("=" * 70)
        logger.info("Reverse reorganization completed successfully!")
        logger.info("=" * 70)
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("\nReverse reorganization cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
