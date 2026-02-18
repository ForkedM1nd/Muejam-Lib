# Implementation Plan: Test and Documentation Reorganization

## Overview

This implementation plan outlines the steps to reorganize the MueJam Library project structure by moving backend tests and documentation, updating all references, cleaning up cache files, and committing changes to git. The implementation will be done in Python using the pathlib library for file operations and gitpython for version control integration.

## Tasks

- [x] 1. Create core file movement utilities
  - Create `scripts/reorganize/file_mover.py` with functions for moving files and directories
  - Implement `move_directory()` to move entire directory trees while preserving structure
  - Implement `move_file()` to move individual files with directory creation
  - Implement `remove_empty_directory()` to recursively remove empty directories
  - Add error handling for permission errors and file not found cases
  - _Requirements: 1.1, 1.2, 2.1, 2.2, 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ]* 1.1 Write property test for file content preservation
  - **Property 1: File content preservation during moves**
  - **Validates: Requirements 1.1, 2.1, 2.4, 4.1**

- [ ]* 1.2 Write property test for directory structure preservation
  - **Property 2: Directory structure preservation**
  - **Validates: Requirements 1.2, 1.5**

- [ ]* 1.3 Write unit tests for file movement edge cases
  - Test moving empty directories
  - Test handling symbolic links
  - Test permission denied errors
  - _Requirements: 1.1, 1.2, 2.1_

- [x] 2. Create Python import update utilities
  - Create `scripts/reorganize/import_updater.py` with AST-based import parsing
  - Implement `find_import_statements()` to parse Python files and extract imports
  - Implement `update_import_path()` to rewrite import statements with new paths
  - Implement `rewrite_file_imports()` to update all imports in a file
  - Handle both absolute and relative imports
  - Handle from...import statements and import aliases
  - _Requirements: 1.3, 4.2, 4.3_

- [ ]* 2.1 Write property test for import statement updates
  - **Property 4: Import statement updates**
  - **Validates: Requirements 1.3, 4.2, 4.3**

- [ ]* 2.2 Write unit tests for import update edge cases
  - Test absolute imports
  - Test relative imports
  - Test multi-line imports
  - Test import aliases
  - Test from...import statements
  - _Requirements: 1.3, 4.2_

- [x] 3. Create documentation reference update utilities
  - Create `scripts/reorganize/reference_updater.py` for updating file references
  - Implement `find_file_references()` to find path references in markdown files
  - Implement `update_reference()` to update file paths based on new locations
  - Implement `update_pytest_config()` to update pytest.ini with new test paths
  - Handle relative and absolute paths
  - Preserve URLs and external references
  - _Requirements: 2.5, 3.1, 3.2, 6.1, 6.2, 6.4_

- [ ]* 3.1 Write property test for documentation reference updates
  - **Property 5: Documentation reference updates**
  - **Validates: Requirements 2.5, 6.1, 6.2, 6.4**

- [ ]* 3.2 Write property test for reference validity
  - **Property 6: Reference validity after updates**
  - **Validates: Requirements 6.4**

- [ ]* 3.3 Write unit tests for reference update edge cases
  - Test markdown links
  - Test relative paths
  - Test absolute paths
  - Test URLs (should not be modified)
  - _Requirements: 2.5, 6.1, 6.2_

- [x] 4. Create cleanup utilities
  - Create `scripts/reorganize/cleanup.py` for removing cache and log files
  - Implement `find_cache_directories()` to locate __pycache__, .pytest_cache, .hypothesis
  - Implement `find_compiled_files()` to locate .pyc and .pyo files
  - Implement `find_log_files()` to locate .log files
  - Implement `remove_paths()` to safely remove files and directories
  - Preserve .gitignore and directories with .gitkeep files
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 8.1, 8.2, 8.3, 8.4, 5.5_

- [ ]* 4.1 Write property test for cache artifact removal
  - **Property 7: Cache artifact removal**
  - **Validates: Requirements 7.1, 7.2, 7.3, 7.4**

- [ ]* 4.2 Write property test for log file removal
  - **Property 8: Log file removal**
  - **Validates: Requirements 8.1, 8.2**

- [ ]* 4.3 Write property test for gitignore preservation
  - **Property 9: Gitignore preservation**
  - **Validates: Requirements 7.5**

- [ ]* 4.4 Write property test for directory preservation with placeholders
  - **Property 10: Directory preservation with placeholders**
  - **Validates: Requirements 5.5**

- [ ]* 4.5 Write unit tests for cleanup edge cases
  - Test removal of __pycache__ directories
  - Test removal of .pyc files
  - Test preservation of .gitignore
  - Test removal of .log files
  - Test preservation of directories with .gitkeep
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 8.1, 8.2_

- [x] 5. Create git integration utilities
  - Create `scripts/reorganize/git_integration.py` for version control operations
  - Implement `stage_changes()` to stage moved and deleted files
  - Implement `create_commit()` to create commit with descriptive message
  - Implement `verify_clean_state()` to check for uncommitted changes
  - Use gitpython library for git operations
  - _Requirements: 9.1, 9.2, 9.3, 9.4_

- [ ]* 5.1 Write unit tests for git integration
  - Test staging moved files
  - Test staging deleted files
  - Test commit creation
  - Test verification of clean state
  - _Requirements: 9.1, 9.2, 9.3, 9.4_

- [x] 6. Checkpoint - Ensure all utility tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Create main reorganization orchestrator
  - Create `scripts/reorganize/reorganize.py` as the main entry point
  - Implement `create_reorganization_plan()` to analyze current structure
  - Implement `execute_plan()` to orchestrate all reorganization steps
  - Implement `verify_reorganization()` to validate results
  - Add dry-run mode to preview changes without executing
  - Add verbose logging for all operations
  - _Requirements: All requirements_

- [ ]* 7.1 Write property test for empty directory removal
  - **Property 11: Empty directory removal**
  - **Validates: Requirements 5.1, 5.2**

- [ ]* 7.2 Write property test for directory preservation with content
  - **Property 12: Directory preservation with content**
  - **Validates: Requirements 5.4**

- [x] 8. Implement backend test move operation
  - In `reorganize.py`, implement `move_backend_tests()` function
  - Move all contents from `tests/backend/` to `apps/backend/tests/`
  - Preserve directory structure within backend tests
  - Update all import statements in moved test files
  - Update conftest.py references
  - Remove empty `tests/backend/` directory after move
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 4.1, 4.2, 4.3, 5.1_

- [x] 9. Implement backend documentation move operation
  - In `reorganize.py`, implement `move_backend_docs()` function
  - Create `docs/backend/` directory if it doesn't exist
  - Move all files from `apps/backend/docs/` to `docs/backend/`
  - Update relative path references in moved documentation
  - Remove empty `apps/backend/docs/` directory after move
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 5.2_

- [x] 10. Implement test configuration updates
  - In `reorganize.py`, implement `update_test_config()` function
  - Update `apps/backend/pytest.ini` to reference new test location
  - Ensure all __init__.py files exist in new test directory structure
  - Update any README files that reference test locations
  - _Requirements: 3.1, 3.2, 3.4, 6.2_

- [x] 11. Implement documentation reference updates
  - In `reorganize.py`, implement `update_all_references()` function
  - Update cross-references between documentation files
  - Update README files that reference test or doc locations
  - Verify all file references point to existing files
  - _Requirements: 6.1, 6.2, 6.4_

- [x] 12. Implement cleanup operations
  - In `reorganize.py`, implement `cleanup_project()` function
  - Remove all __pycache__ directories
  - Remove all .pyc and .pyo files
  - Remove all .pytest_cache directories
  - Remove all .hypothesis directories
  - Remove all .log files
  - Preserve .gitignore files
  - Preserve directories with .gitkeep files
  - Preserve log directory structure
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 8.1, 8.2, 8.3, 5.5_

- [x] 13. Implement git commit operation
  - In `reorganize.py`, implement `commit_changes()` function
  - Check for uncommitted changes before starting
  - Stage all moved files
  - Stage all deleted files
  - Stage all updated files
  - Create commit with message: "Reorganize tests and docs: move backend tests to apps/backend/tests, move backend docs to docs/backend, cleanup cache and log files"
  - Verify clean state after commit
  - _Requirements: 9.1, 9.2, 9.3, 9.4_

- [x] 14. Add command-line interface
  - Add argparse CLI to `reorganize.py`
  - Add `--dry-run` flag to preview changes
  - Add `--verbose` flag for detailed logging
  - Add `--skip-tests` flag to skip test moves
  - Add `--skip-docs` flag to skip doc moves
  - Add `--skip-cleanup` flag to skip cleanup
  - Add `--skip-commit` flag to skip git commit
  - Print summary of all operations performed

- [ ]* 14.1 Write integration test for end-to-end reorganization
  - Create test project structure
  - Run complete reorganization
  - Verify all files in correct locations
  - Verify all imports updated
  - Verify all references updated
  - Verify cleanup complete
  - Verify git commit created
  - _Requirements: All requirements_

- [ ]* 14.2 Write integration test for idempotency
  - Run reorganization twice
  - Verify second run detects no changes needed
  - Verify no errors or duplicate operations
  - _Requirements: All requirements_

- [x] 15. Create documentation for reorganization script
  - Create `scripts/reorganize/README.md`
  - Document usage and command-line options
  - Document what the script does
  - Document how to run in dry-run mode
  - Document how to rollback using git
  - Add examples of common usage patterns

- [-] 16. Final checkpoint - Run reorganization script
  - Run `python scripts/reorganize/reorganize.py --dry-run` to preview changes
  - Review dry-run output with user
  - Run `python scripts/reorganize/reorganize.py` to execute reorganization
  - Verify all tests still pass in new locations
  - Verify git commit was created successfully
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster execution
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- The reorganization script includes a dry-run mode for safety
- All file operations preserve content and structure
- Git integration ensures all changes are tracked in version control
