#!/usr/bin/env python3
"""
Main reorganization orchestrator for test and documentation restructuring.

This script orchestrates the complete reorganization process including:
- Moving backend tests from tests/backend/ to apps/backend/tests/
- Moving backend documentation from apps/backend/docs/ to docs/backend/
- Updating all import statements and file references
- Cleaning up cache files and logs
- Committing changes to git

Usage:
    python reorganize.py [--dry-run] [--verbose] [--skip-commit]
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

# Import utility modules - try relative imports first, then absolute
try:
    from .file_mover import move_directory, move_file, remove_empty_directory
    from .import_updater import find_import_statements, rewrite_file_imports
    from .reference_updater import find_file_references, update_reference, update_pytest_config
    from .cleanup import find_cache_directories, find_compiled_files, find_log_files, remove_paths
    from .git_integration import stage_changes, create_commit, verify_clean_state, get_repository_root
except ImportError:
    # Fallback to direct imports when run as script
    from file_mover import move_directory, move_file, remove_empty_directory
    from import_updater import find_import_statements, rewrite_file_imports
    from reference_updater import find_file_references, update_reference, update_pytest_config
    from cleanup import find_cache_directories, find_compiled_files, find_log_files, remove_paths
    from git_integration import stage_changes, create_commit, verify_clean_state, get_repository_root


# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class PathMapping:
    """Represents a file or directory move operation."""
    old_path: Path
    new_path: Path
    is_directory: bool


@dataclass
class ReorganizationPlan:
    """Complete plan for reorganization operations."""
    test_moves: List[PathMapping] = field(default_factory=list)
    doc_moves: List[PathMapping] = field(default_factory=list)
    import_updates: Dict[Path, Dict[str, str]] = field(default_factory=dict)
    reference_updates: Dict[Path, List] = field(default_factory=dict)
    cleanup_paths: List[Path] = field(default_factory=list)
    empty_dirs_to_remove: List[Path] = field(default_factory=list)


def move_backend_tests(repo_root: Path, dry_run: bool = False) -> bool:
    """
    Move all backend tests from tests/backend/ to apps/backend/tests/.
    
    This function:
    1. Moves all contents from tests/backend/ to apps/backend/tests/
    2. Preserves directory structure within backend tests
    3. Updates all import statements in moved test files
    4. Updates conftest.py references
    5. Removes empty tests/backend/ directory after move
    
    Args:
        repo_root: Path to the repository root directory
        dry_run: If True, only log operations without executing them
        
    Returns:
        True if operation was successful, False otherwise
        
    Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 4.1, 4.2, 4.3, 5.1
    """
    logger.info(f"{'[DRY RUN] ' if dry_run else ''}Moving backend tests...")
    
    source_dir = repo_root / "tests" / "backend"
    dest_dir = repo_root / "apps" / "backend" / "tests"
    
    # Check if source directory exists
    if not source_dir.exists():
        logger.warning(f"Source directory does not exist: {source_dir}")
        return False
    
    if not source_dir.is_dir():
        logger.error(f"Source path is not a directory: {source_dir}")
        return False
    
    logger.info(f"  Source: {source_dir}")
    logger.info(f"  Destination: {dest_dir}")
    
    if dry_run:
        # In dry-run mode, just log what would be done
        test_files = list(source_dir.rglob("*.py"))
        logger.info(f"  Would move {len(test_files)} Python files")
        return True
    
    try:
        # Step 1: Move the directory tree
        logger.info("Step 1: Moving directory tree...")
        move_directory(source_dir, dest_dir)
        logger.info(f"✓ Moved directory tree to {dest_dir}")
        
        # Step 2: Update import statements in all moved test files
        logger.info("Step 2: Updating import statements in moved test files...")
        
        # Define import path mappings
        import_updates = {
            "tests.backend": "apps.backend.tests"
        }
        
        # Find all Python files in the new location
        python_files = list(dest_dir.rglob("*.py"))
        logger.info(f"Found {len(python_files)} Python files to update")
        
        updated_count = 0
        for py_file in python_files:
            try:
                # Read file to check if it has imports to update
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check if file contains imports that need updating
                needs_update = any(
                    old_path in content for old_path in import_updates.keys()
                )
                
                if needs_update:
                    rewrite_file_imports(py_file, import_updates)
                    updated_count += 1
                    logger.debug(f"Updated imports in {py_file.relative_to(repo_root)}")
                    
            except Exception as e:
                logger.warning(f"Failed to update imports in {py_file}: {e}")
        
        logger.info(f"✓ Updated imports in {updated_count} files")
        
        # Step 3: Update conftest.py references
        logger.info("Step 3: Updating conftest.py references...")
        
        # Find all conftest.py files in the repository
        conftest_files = list(repo_root.rglob("conftest.py"))
        
        conftest_updated = 0
        for conftest in conftest_files:
            try:
                with open(conftest, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check if conftest references the old test path
                if "tests.backend" in content or "tests/backend" in content:
                    # Update import statements
                    rewrite_file_imports(conftest, import_updates)
                    
                    # Also update any string references to the path
                    with open(conftest, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    updated = False
                    for i, line in enumerate(lines):
                        if "tests/backend" in line:
                            lines[i] = line.replace("tests/backend", "apps/backend/tests")
                            updated = True
                    
                    if updated:
                        with open(conftest, 'w', encoding='utf-8') as f:
                            f.writelines(lines)
                    
                    conftest_updated += 1
                    logger.debug(f"Updated conftest.py: {conftest.relative_to(repo_root)}")
                    
            except Exception as e:
                logger.warning(f"Failed to update conftest.py {conftest}: {e}")
        
        logger.info(f"✓ Updated {conftest_updated} conftest.py files")
        
        # Step 4: Remove empty source directory
        logger.info("Step 4: Removing empty source directory...")
        
        # Remove tests/backend/ directory (should be empty now)
        if source_dir.exists():
            logger.warning(f"Source directory still exists after move: {source_dir}")
            # It should have been removed by move_directory, but let's be safe
        
        # Remove tests/ directory if it's empty
        tests_dir = repo_root / "tests"
        if tests_dir.exists():
            try:
                remove_empty_directory(tests_dir, recursive=True)
                logger.info(f"✓ Removed empty directory: {tests_dir}")
            except Exception as e:
                logger.debug(f"Tests directory not empty or couldn't be removed: {e}")
        
        logger.info("✓ Backend test move operation completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error during backend test move: {e}", exc_info=True)
        return False


def move_backend_docs(repo_root: Path, dry_run: bool = False) -> bool:
    """
    Move all backend documentation from apps/backend/docs/ to docs/backend/.
    
    This function:
    1. Creates docs/backend/ directory if it doesn't exist
    2. Moves all files from apps/backend/docs/ to docs/backend/
    3. Updates relative path references in moved documentation
    4. Removes empty apps/backend/docs/ directory after move
    
    Args:
        repo_root: Path to the repository root directory
        dry_run: If True, only log operations without executing them
        
    Returns:
        True if operation was successful, False otherwise
        
    Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 5.2
    """
    logger.info(f"{'[DRY RUN] ' if dry_run else ''}Moving backend documentation...")
    
    source_dir = repo_root / "apps" / "backend" / "docs"
    dest_dir = repo_root / "docs" / "backend"
    
    # Check if source directory exists
    if not source_dir.exists():
        logger.warning(f"Source directory does not exist: {source_dir}")
        return False
    
    if not source_dir.is_dir():
        logger.error(f"Source path is not a directory: {source_dir}")
        return False
    
    logger.info(f"  Source: {source_dir}")
    logger.info(f"  Destination: {dest_dir}")
    
    if dry_run:
        # In dry-run mode, just log what would be done
        doc_files = list(source_dir.rglob("*.md"))
        logger.info(f"  Would move {len(doc_files)} markdown files")
        return True
    
    try:
        # Step 1: Create destination directory if it doesn't exist
        logger.info("Step 1: Creating destination directory...")
        dest_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"✓ Destination directory ready: {dest_dir}")
        
        # Step 2: Move the directory tree
        logger.info("Step 2: Moving directory tree...")
        move_directory(source_dir, dest_dir)
        logger.info(f"✓ Moved directory tree to {dest_dir}")
        
        # Step 3: Update relative path references in moved documentation
        logger.info("Step 3: Updating relative path references in documentation...")
        
        # Find all markdown files in the new location
        md_files = list(dest_dir.rglob("*.md"))
        logger.info(f"Found {len(md_files)} markdown files to update")
        
        # Build path mapping for reference updates
        # Documentation moved from apps/backend/docs/ to docs/backend/
        # So references need to be adjusted accordingly
        path_mapping = {
            "apps/backend/docs": "docs/backend",
            "../../../": "../../",  # Adjust relative paths up from backend app
        }
        
        updated_count = 0
        for md_file in md_files:
            try:
                # Read file content
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check if file contains paths that need updating
                needs_update = any(
                    old_path in content for old_path in path_mapping.keys()
                )
                
                if needs_update:
                    # Find and update file references
                    refs = find_file_references(md_file)
                    if refs:
                        lines = content.split('\n')
                        
                        for ref in refs:
                            # Update the reference based on path mapping
                            updated_ref = update_reference(ref, path_mapping)
                            if updated_ref and updated_ref.original_text != ref.original_text:
                                # Replace in the line
                                line_idx = ref.line_number - 1
                                if 0 <= line_idx < len(lines):
                                    lines[line_idx] = lines[line_idx].replace(
                                        ref.original_text, updated_ref.original_text
                                    )
                        
                        # Write back updated content
                        with open(md_file, 'w', encoding='utf-8') as f:
                            f.write('\n'.join(lines))
                        
                        updated_count += 1
                        logger.debug(f"Updated references in {md_file.relative_to(repo_root)}")
                        
            except Exception as e:
                logger.warning(f"Failed to update references in {md_file}: {e}")
        
        logger.info(f"✓ Updated references in {updated_count} files")
        
        # Step 4: Remove empty source directory
        logger.info("Step 4: Removing empty source directory...")
        
        # Remove apps/backend/docs/ directory (should be empty now)
        if source_dir.exists():
            try:
                remove_empty_directory(source_dir, recursive=True)
                logger.info(f"✓ Removed empty directory: {source_dir}")
            except Exception as e:
                logger.warning(f"Source directory not empty or couldn't be removed: {e}")
        
        logger.info("✓ Backend documentation move operation completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error during backend documentation move: {e}", exc_info=True)
        return False


def create_reorganization_plan(repo_root: Path) -> ReorganizationPlan:
    """
    Analyze current project structure and create reorganization plan.
    
    This function examines the current state of the project and determines:
    - Which files and directories need to be moved
    - Which import statements need updating
    - Which documentation references need updating
    - Which cache and log files need cleanup
    
    Args:
        repo_root: Path to the repository root directory
        
    Returns:
        ReorganizationPlan with all planned operations
        
    Requirements: All requirements
    """
    logger.info("Creating reorganization plan...")
    plan = ReorganizationPlan()
    
    # Plan backend test moves
    backend_tests_src = repo_root / "tests" / "backend"
    backend_tests_dst = repo_root / "apps" / "backend" / "tests"
    
    if backend_tests_src.exists():
        logger.info(f"Planning to move backend tests: {backend_tests_src} -> {backend_tests_dst}")
        plan.test_moves.append(PathMapping(
            old_path=backend_tests_src,
            new_path=backend_tests_dst,
            is_directory=True
        ))
        plan.empty_dirs_to_remove.append(backend_tests_src.parent)  # tests/ directory
    else:
        logger.info(f"Backend tests directory not found: {backend_tests_src}")
    
    # Plan backend documentation moves
    backend_docs_src = repo_root / "apps" / "backend" / "docs"
    backend_docs_dst = repo_root / "docs" / "backend"
    
    if backend_docs_src.exists():
        logger.info(f"Planning to move backend docs: {backend_docs_src} -> {backend_docs_dst}")
        plan.doc_moves.append(PathMapping(
            old_path=backend_docs_src,
            new_path=backend_docs_dst,
            is_directory=True
        ))
        plan.empty_dirs_to_remove.append(backend_docs_src)
    else:
        logger.info(f"Backend docs directory not found: {backend_docs_src}")
    
    # Plan import updates for moved test files
    if plan.test_moves:
        logger.info("Planning import updates for moved test files...")
        # Map old module paths to new module paths
        plan.import_updates = {
            # Update imports from tests.backend.* to apps.backend.tests.*
            repo_root: {
                "tests.backend": "apps.backend.tests"
            }
        }
    
    # Plan cleanup operations
    logger.info("Planning cleanup operations...")
    plan.cleanup_paths.extend(find_cache_directories(repo_root))
    plan.cleanup_paths.extend(find_compiled_files(repo_root))
    plan.cleanup_paths.extend(find_log_files(repo_root))
    
    logger.info(f"Plan created:")
    logger.info(f"  - Test moves: {len(plan.test_moves)}")
    logger.info(f"  - Doc moves: {len(plan.doc_moves)}")
    logger.info(f"  - Import updates: {len(plan.import_updates)}")
    logger.info(f"  - Cleanup paths: {len(plan.cleanup_paths)}")
    logger.info(f"  - Empty dirs to remove: {len(plan.empty_dirs_to_remove)}")
    
    return plan
def move_backend_tests(repo_root: Path, dry_run: bool = False) -> bool:
    """
    Move all backend tests from tests/backend/ to apps/backend/tests/.

    This function:
    1. Moves all contents from tests/backend/ to apps/backend/tests/
    2. Preserves directory structure within backend tests
    3. Updates all import statements in moved test files
    4. Updates conftest.py references
    5. Removes empty tests/backend/ directory after move

    Args:
        repo_root: Path to the repository root directory
        dry_run: If True, only log operations without executing them

    Returns:
        True if operation was successful, False otherwise

    Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 4.1, 4.2, 4.3, 5.1
    """
    logger.info(f"{'[DRY RUN] ' if dry_run else ''}Moving backend tests...")

    source_dir = repo_root / "tests" / "backend"
    dest_dir = repo_root / "apps" / "backend" / "tests"

    # Check if source directory exists
    if not source_dir.exists():
        logger.warning(f"Source directory does not exist: {source_dir}")
        return False

    if not source_dir.is_dir():
        logger.error(f"Source path is not a directory: {source_dir}")
        return False

    logger.info(f"  Source: {source_dir}")
    logger.info(f"  Destination: {dest_dir}")

    if dry_run:
        # In dry-run mode, just log what would be done
        test_files = list(source_dir.rglob("*.py"))
        logger.info(f"  Would move {len(test_files)} Python files")
        return True

    try:
        # Step 1: Move the directory tree
        logger.info("Step 1: Moving directory tree...")
        move_directory(source_dir, dest_dir)
        logger.info(f"✓ Moved directory tree to {dest_dir}")

        # Step 2: Update import statements in all moved test files
        logger.info("Step 2: Updating import statements in moved test files...")

        # Define import path mappings
        import_updates = {
            "tests.backend": "apps.backend.tests"
        }

        # Find all Python files in the new location
        python_files = list(dest_dir.rglob("*.py"))
        logger.info(f"Found {len(python_files)} Python files to update")

        updated_count = 0
        for py_file in python_files:
            try:
                # Read file to check if it has imports to update
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Check if file contains imports that need updating
                needs_update = any(
                    old_path in content for old_path in import_updates.keys()
                )

                if needs_update:
                    rewrite_file_imports(py_file, import_updates)
                    updated_count += 1
                    logger.debug(f"Updated imports in {py_file.relative_to(repo_root)}")

            except Exception as e:
                logger.warning(f"Failed to update imports in {py_file}: {e}")

        logger.info(f"✓ Updated imports in {updated_count} files")

        # Step 3: Update conftest.py references
        logger.info("Step 3: Updating conftest.py references...")

        # Find all conftest.py files in the repository
        conftest_files = list(repo_root.rglob("conftest.py"))

        conftest_updated = 0
        for conftest in conftest_files:
            try:
                with open(conftest, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Check if conftest references the old test path
                if "tests.backend" in content or "tests/backend" in content:
                    # Update import statements
                    rewrite_file_imports(conftest, import_updates)

                    # Also update any string references to the path
                    with open(conftest, 'r', encoding='utf-8') as f:
                        lines = f.readlines()

                    updated = False
                    for i, line in enumerate(lines):
                        if "tests/backend" in line:
                            lines[i] = line.replace("tests/backend", "apps/backend/tests")
                            updated = True

                    if updated:
                        with open(conftest, 'w', encoding='utf-8') as f:
                            f.writelines(lines)

                    conftest_updated += 1
                    logger.debug(f"Updated conftest.py: {conftest.relative_to(repo_root)}")

            except Exception as e:
                logger.warning(f"Failed to update conftest.py {conftest}: {e}")

        logger.info(f"✓ Updated {conftest_updated} conftest.py files")

        # Step 4: Remove empty source directory
        logger.info("Step 4: Removing empty source directory...")

        # Remove tests/backend/ directory (should be empty now)
        if source_dir.exists():
            logger.warning(f"Source directory still exists after move: {source_dir}")
            # It should have been removed by move_directory, but let's be safe

        # Remove tests/ directory if it's empty
        tests_dir = repo_root / "tests"
        if tests_dir.exists():
            try:
                remove_empty_directory(tests_dir, recursive=True)
                logger.info(f"✓ Removed empty directory: {tests_dir}")
            except Exception as e:
                logger.debug(f"Tests directory not empty or couldn't be removed: {e}")

        logger.info("✓ Backend test move operation completed successfully")
        return True

    except Exception as e:
        logger.error(f"Error during backend test move: {e}", exc_info=True)
        return False





def execute_plan(plan: ReorganizationPlan, repo_root: Path, dry_run: bool = False, 
                 skip_tests: bool = False, skip_docs: bool = False, 
                 skip_cleanup: bool = False) -> bool:
    """
    Execute the reorganization plan.
    
    This function performs all planned operations in the correct order:
    1. Move test files
    2. Move documentation files
    3. Update import statements
    4. Update documentation references
    5. Clean up cache and log files
    6. Remove empty directories
    
    Args:
        plan: ReorganizationPlan to execute
        repo_root: Path to the repository root directory
        dry_run: If True, only log operations without executing them
        
    Returns:
        True if execution was successful, False otherwise
        
    Requirements: All requirements
    """
    logger.info(f"{'[DRY RUN] ' if dry_run else ''}Executing reorganization plan...")
    
    try:
        # Step 1: Move backend tests using dedicated function
        if plan.test_moves and not skip_tests:
            if not move_backend_tests(repo_root, dry_run):
                logger.error("Failed to move backend tests")
                return False
        elif skip_tests:
            logger.info("Skipping backend test move (--skip-tests)")
        
        # Step 2: Move backend documentation using dedicated function
        if plan.doc_moves and not skip_docs:
            if not move_backend_docs(repo_root, dry_run):
                logger.warning("Failed to move backend documentation (may not exist)")
                # Don't fail the entire operation if docs don't exist
        elif skip_docs:
            logger.info("Skipping backend documentation move (--skip-docs)")
        
        # Step 3: Update import statements (handled by move_backend_tests for test files)
        # Additional import updates for other files if needed
        if plan.import_updates and not dry_run and not plan.test_moves:
            logger.info("Updating import statements in non-test files...")
            for base_path, updates in plan.import_updates.items():
                # Find all Python files in the repository (excluding already processed test files)
                python_files = list(repo_root.rglob("*.py"))
                backend_tests_dir = repo_root / "apps" / "backend" / "tests"
                python_files = [f for f in python_files if not f.is_relative_to(backend_tests_dir)]
                logger.info(f"Found {len(python_files)} Python files to check")
                
                for py_file in python_files:
                    try:
                        rewrite_file_imports(py_file, updates)
                    except Exception as e:
                        logger.warning(f"Failed to update imports in {py_file}: {e}")
        
        # Step 4: Update documentation references
        if (plan.test_moves or plan.doc_moves) and not dry_run:
            logger.info("Updating documentation references...")
            # Build path mapping for reference updates
            path_mapping = {}
            for mapping in plan.test_moves + plan.doc_moves:
                old_rel = mapping.old_path.relative_to(repo_root)
                new_rel = mapping.new_path.relative_to(repo_root)
                path_mapping[str(old_rel)] = str(new_rel)
            
            # Find and update references in markdown files
            md_files = list(repo_root.rglob("*.md"))
            logger.info(f"Found {len(md_files)} markdown files to check")
            
            for md_file in md_files:
                try:
                    refs = find_file_references(md_file)
                    if refs:
                        # Read file content
                        with open(md_file, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                        
                        # Update references
                        updated = False
                        for ref in refs:
                            new_ref = update_reference(ref, path_mapping)
                            if new_ref:
                                # Replace the line
                                line_idx = ref.line_number - 1
                                if line_idx < len(lines):
                                    lines[line_idx] = lines[line_idx].replace(
                                        ref.original_text, new_ref.original_text
                                    )
                                    updated = True
                        
                        # Write back if updated
                        if updated:
                            with open(md_file, 'w', encoding='utf-8') as f:
                                f.writelines(lines)
                            logger.info(f"Updated references in {md_file}")
                except Exception as e:
                    logger.warning(f"Failed to update references in {md_file}: {e}")
            
            # Update pytest configuration
            pytest_configs = [
                repo_root / "apps" / "backend" / "pytest.ini",
                repo_root / "apps" / "backend" / "pyproject.toml",
                repo_root / "pytest.ini",
                repo_root / "pyproject.toml"
            ]
            
            for config_file in pytest_configs:
                if config_file.exists():
                    try:
                        update_pytest_config(config_file, "apps/backend/tests")
                        logger.info(f"Updated pytest config: {config_file}")
                    except Exception as e:
                        logger.warning(f"Failed to update pytest config {config_file}: {e}")
        
        # Step 5: Clean up cache and log files
        if plan.cleanup_paths and not skip_cleanup:
            logger.info(f"{'[DRY RUN] ' if dry_run else ''}Cleaning up {len(plan.cleanup_paths)} cache and log files...")
            if not dry_run:
                remove_paths(plan.cleanup_paths)
        elif skip_cleanup:
            logger.info("Skipping cleanup operations (--skip-cleanup)")
        
        # Step 6: Remove empty directories
        if plan.empty_dirs_to_remove and not dry_run:
            logger.info("Removing empty directories...")
            for empty_dir in plan.empty_dirs_to_remove:
                try:
                    remove_empty_directory(empty_dir, recursive=True)
                except Exception as e:
                    logger.warning(f"Failed to remove empty directory {empty_dir}: {e}")
        
        logger.info(f"{'[DRY RUN] ' if dry_run else ''}Reorganization execution completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error during reorganization execution: {e}", exc_info=True)
        return False


def verify_reorganization(repo_root: Path) -> bool:
    """
    Verify that reorganization was successful.
    
    This function checks:
    - Backend tests are in apps/backend/tests/
    - Backend docs are in docs/backend/
    - Old directories are removed or empty
    - No cache or log files remain
    
    Args:
        repo_root: Path to the repository root directory
        
    Returns:
        True if verification passes, False otherwise
        
    Requirements: All requirements
    """
    logger.info("Verifying reorganization results...")
    
    success = True
    
    # Check backend tests location
    backend_tests = repo_root / "apps" / "backend" / "tests"
    if backend_tests.exists():
        test_files = list(backend_tests.rglob("*.py"))
        logger.info(f"✓ Backend tests directory exists with {len(test_files)} Python files")
    else:
        logger.warning("✗ Backend tests directory not found")
        success = False
    
    # Check backend docs location
    backend_docs = repo_root / "docs" / "backend"
    if backend_docs.exists():
        doc_files = list(backend_docs.rglob("*.md"))
        logger.info(f"✓ Backend docs directory exists with {len(doc_files)} markdown files")
    else:
        logger.info("ℹ Backend docs directory not found (may not have existed)")
    
    # Check old test directory is removed
    old_backend_tests = repo_root / "tests" / "backend"
    if not old_backend_tests.exists():
        logger.info("✓ Old backend tests directory removed")
    else:
        logger.warning(f"✗ Old backend tests directory still exists: {old_backend_tests}")
        success = False
    
    # Check old docs directory is removed
    old_backend_docs = repo_root / "apps" / "backend" / "docs"
    if not old_backend_docs.exists():
        logger.info("✓ Old backend docs directory removed")
    else:
        logger.warning(f"✗ Old backend docs directory still exists: {old_backend_docs}")
        success = False
    
    # Check for remaining cache directories
    cache_dirs = find_cache_directories(repo_root)
    if not cache_dirs:
        logger.info("✓ No cache directories found")
    else:
        logger.warning(f"✗ Found {len(cache_dirs)} cache directories still present")
        success = False
    
    # Check for remaining log files
    log_files = find_log_files(repo_root)
    if not log_files:
        logger.info("✓ No log files found")
    else:
        logger.warning(f"✗ Found {len(log_files)} log files still present")
        success = False
    
    if success:
        logger.info("✓ Verification passed - reorganization successful!")
    else:
        logger.warning("✗ Verification failed - some issues detected")
    
    return success


def setup_logging(verbose: bool = False) -> None:
    """
    Configure logging for the reorganization script.
    
    Args:
        verbose: If True, set log level to DEBUG, otherwise INFO
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Set level for our modules
    for module in ['file_mover', 'import_updater', 'reference_updater', 'cleanup', 'git_integration']:
        logging.getLogger(module).setLevel(log_level)


def main() -> int:
    """
    Main entry point for the reorganization script.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    parser = argparse.ArgumentParser(
        description="Reorganize test and documentation structure",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview changes without executing
  python reorganize.py --dry-run
  
  # Execute reorganization with verbose logging
  python reorganize.py --verbose
  
  # Execute without creating git commit
  python reorganize.py --skip-commit
        """
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without executing them'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--skip-commit',
        action='store_true',
        help='Skip git commit after reorganization'
    )
    
    parser.add_argument(
        '--skip-tests',
        action='store_true',
        help='Skip moving backend tests'
    )
    
    parser.add_argument(
        '--skip-docs',
        action='store_true',
        help='Skip moving backend documentation'
    )
    
    parser.add_argument(
        '--skip-cleanup',
        action='store_true',
        help='Skip cleanup of cache and log files'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    logger.info("=" * 70)
    logger.info("Test and Documentation Reorganization Script")
    logger.info("=" * 70)
    
    try:
        # Find repository root
        repo_root = get_repository_root()
        logger.info(f"Repository root: {repo_root}")
        
        # Check for uncommitted changes (unless dry-run)
        if not args.dry_run and not args.skip_commit:
            if not verify_clean_state(repo_root):
                logger.error("Repository has uncommitted changes. Please commit or stash them first.")
                return 1
        
        # Create reorganization plan
        plan = create_reorganization_plan(repo_root)
        
        # Execute plan
        if not execute_plan(plan, repo_root, dry_run=args.dry_run, 
                           skip_tests=args.skip_tests, skip_docs=args.skip_docs,
                           skip_cleanup=args.skip_cleanup):
            logger.error("Reorganization execution failed")
            return 1
        
        # Verify results (skip in dry-run mode)
        if not args.dry_run:
            if not verify_reorganization(repo_root):
                logger.warning("Verification detected issues, but reorganization completed")
            
            # Commit changes to git
            if not args.skip_commit:
                logger.info("Committing changes to git...")
                try:
                    stage_changes(repo_root)
                    commit_sha = create_commit(
                        repo_root,
                        "Reorganize tests and docs: move backend tests to apps/backend/tests, "
                        "move backend docs to docs/backend, cleanup cache and log files"
                    )
                    logger.info(f"✓ Changes committed: {commit_sha}")
                except Exception as e:
                    logger.error(f"Failed to commit changes: {e}")
                    logger.info("You can manually commit the changes using git")
                    return 1
        
        logger.info("=" * 70)
        logger.info("Reorganization completed successfully!")
        logger.info("=" * 70)
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("\nReorganization cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
