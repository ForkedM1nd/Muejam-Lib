# Design Document: Test and Documentation Reorganization

## Overview

This design outlines the approach for reorganizing the MueJam Library project structure by:
1. Moving all backend tests from `tests/backend/` to `apps/backend/tests/`
2. Moving all backend documentation from `apps/backend/docs/` to `docs/backend/`
3. Cleaning up Python cache files, temporary directories, and log files
4. Updating all import statements and references to reflect new locations
5. Committing all changes to version control

The reorganization will improve project structure by colocating tests with application code and centralizing documentation at the root level for better discoverability.

## Architecture

### Current Structure
```
project-root/
├── tests/
│   ├── backend/          # Backend tests (to be moved)
│   │   ├── apps/
│   │   ├── infrastructure/
│   │   ├── integration/
│   │   ├── property/
│   │   ├── unit/
│   │   └── conftest.py
│   └── frontend/         # Frontend tests (stays)
├── apps/
│   └── backend/
│       ├── tests/        # Some tests already here
│       └── docs/         # Backend docs (to be moved)
└── docs/                 # Root documentation
    └── backend/          # Target for backend docs
```

### Target Structure
```
project-root/
├── tests/
│   └── frontend/         # Frontend tests only
├── apps/
│   └── backend/
│       └── tests/        # All backend tests consolidated here
└── docs/
    └── backend/          # All backend documentation here
```

### Design Principles

1. **Colocation**: Tests should live near the code they test
2. **Discoverability**: Documentation should be centralized and easy to find
3. **Consistency**: Follow standard Python project conventions
4. **Safety**: Preserve all test functionality and documentation content
5. **Cleanliness**: Remove generated files and caches from version control

## Components and Interfaces

### File Movement Component

**Responsibility**: Move files and directories while preserving structure

**Operations**:
- `move_directory(source: Path, destination: Path) -> None`
  - Moves entire directory tree from source to destination
  - Creates destination parent directories if needed
  - Preserves relative structure within moved directory

- `move_file(source: Path, destination: Path) -> None`
  - Moves individual file to new location
  - Creates destination directory if needed

- `remove_empty_directory(path: Path) -> None`
  - Removes directory if empty
  - Recursively checks parent directories

### Import Update Component

**Responsibility**: Update Python import statements to reflect new file locations

**Operations**:
- `find_import_statements(file: Path) -> List[ImportStatement]`
  - Parses Python file to find all import statements
  - Returns list of import statements with line numbers

- `update_import_path(import_stmt: ImportStatement, old_path: str, new_path: str) -> ImportStatement`
  - Updates import statement to use new module path
  - Handles both absolute and relative imports

- `rewrite_file_imports(file: Path, updates: Dict[str, str]) -> None`
  - Rewrites file with updated import statements
  - Preserves all other file content

### Reference Update Component

**Responsibility**: Update documentation references and configuration files

**Operations**:
- `find_file_references(file: Path) -> List[FileReference]`
  - Finds all file path references in documentation
  - Identifies relative and absolute paths

- `update_reference(ref: FileReference, path_mapping: Dict[str, str]) -> FileReference`
  - Updates file reference to new location
  - Validates that new path exists

- `update_pytest_config(config_file: Path, new_test_path: str) -> None`
  - Updates pytest.ini or pyproject.toml with new test directory
  - Preserves other configuration settings

### Cleanup Component

**Responsibility**: Remove Python cache files, temporary directories, and logs

**Operations**:
- `find_cache_directories(root: Path) -> List[Path]`
  - Recursively finds all `__pycache__`, `.pytest_cache`, `.hypothesis` directories
  - Returns list of directories to remove

- `find_compiled_files(root: Path) -> List[Path]`
  - Finds all `.pyc` and `.pyo` files
  - Returns list of files to remove

- `find_log_files(root: Path) -> List[Path]`
  - Finds all `.log` files
  - Returns list of files to remove

- `remove_paths(paths: List[Path]) -> None`
  - Removes all specified files and directories
  - Handles errors gracefully

### Git Integration Component

**Responsibility**: Stage and commit changes to version control

**Operations**:
- `stage_changes(paths: List[Path]) -> None`
  - Stages all moved, deleted, and modified files
  - Uses `git add` for new locations and `git rm` for old locations

- `create_commit(message: str) -> None`
  - Creates git commit with descriptive message
  - Includes all staged changes

- `verify_clean_state() -> bool`
  - Checks if working directory is clean after commit
  - Returns true if no untracked or modified files remain

## Data Models

### Path Mapping
```python
class PathMapping:
    old_path: Path
    new_path: Path
    is_directory: bool
```

### Import Statement
```python
class ImportStatement:
    line_number: int
    original_text: str
    module_path: str
    is_relative: bool
    import_type: str  # "import" or "from"
```

### File Reference
```python
class FileReference:
    file: Path
    line_number: int
    original_text: str
    referenced_path: str
    is_relative: bool
```

### Reorganization Plan
```python
class ReorganizationPlan:
    test_moves: List[PathMapping]
    doc_moves: List[PathMapping]
    import_updates: Dict[Path, List[ImportStatement]]
    reference_updates: Dict[Path, List[FileReference]]
    cleanup_paths: List[Path]
```


## Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.

### File Movement Properties

Property 1: File content preservation during moves
*For any* file moved from source to destination, the file content at the destination SHALL be identical to the content at the source (byte-for-byte equality).
**Validates: Requirements 1.1, 2.1, 2.4, 4.1**

Property 2: Directory structure preservation
*For any* file at relative path `X/Y/file.ext` within the source directory, after moving the source directory to destination, the file SHALL exist at `destination/X/Y/file.ext` with the same relative path structure.
**Validates: Requirements 1.2, 1.5**

Property 3: Configuration file preservation
*For any* configuration file (conftest.py, __init__.py, pytest.ini) in the source directory tree, after the move operation, a corresponding file SHALL exist in the destination directory tree at the same relative position.
**Validates: Requirements 1.5, 3.4**

### Import and Reference Update Properties

Property 4: Import statement updates
*For any* Python file that is moved, all import statements referencing the old module path SHALL be updated to reference the new module path, maintaining correct module resolution.
**Validates: Requirements 1.3, 4.2, 4.3**

Property 5: Documentation reference updates
*For any* documentation file that is moved, all relative path references to other files SHALL be updated to reflect the new location, maintaining valid references.
**Validates: Requirements 2.5, 6.1, 6.2, 6.4**

Property 6: Reference validity after updates
*For any* file path reference in documentation after the reorganization, the referenced file SHALL exist at the specified location.
**Validates: Requirements 6.4**

### Cleanup Properties

Property 7: Cache artifact removal
*For any* Python cache artifact (__pycache__ directories, .pyc files, .pyo files, .pytest_cache directories, .hypothesis directories), after cleanup, the artifact SHALL not exist in the project directory tree.
**Validates: Requirements 7.1, 7.2, 7.3, 7.4**

Property 8: Log file removal
*For any* .log file in the project directory tree, after cleanup, the file SHALL not exist.
**Validates: Requirements 8.1, 8.2**

Property 9: Gitignore preservation
*For any* .gitignore file in the project, after cleanup operations, the file content SHALL remain unchanged.
**Validates: Requirements 7.5**

Property 10: Directory preservation with placeholders
*For any* directory containing a .gitkeep file or other placeholder, after cleanup operations, the directory SHALL still exist.
**Validates: Requirements 5.5**

### Post-Move Verification Properties

Property 11: Empty directory removal
*For any* source directory after all files have been moved, if the directory is empty, it SHALL be removed from the file system.
**Validates: Requirements 5.1, 5.2**

Property 12: Directory preservation with content
*For any* directory that contains files or non-empty subdirectories after the move operation, the directory SHALL be preserved.
**Validates: Requirements 5.4**

## Error Handling

### File System Errors

**Permission Errors**:
- If a file or directory cannot be moved due to permissions, log the error with the specific path
- Continue with other operations and report all failures at the end
- Provide clear error messages indicating which files failed to move

**File Not Found Errors**:
- If a source file doesn't exist when attempting to move, log a warning
- Skip the operation for that file and continue
- Report missing files in the final summary

**Destination Already Exists**:
- If destination file already exists, compare content
- If content is identical, skip the move and log as already complete
- If content differs, log an error and require manual resolution

### Import Update Errors

**Parse Errors**:
- If a Python file cannot be parsed, log the error with file path
- Skip import updates for that file
- Report parse errors in the final summary

**Ambiguous Imports**:
- If an import statement could refer to multiple modules, log a warning
- Attempt best-effort update based on file location
- Flag for manual review

### Git Errors

**Uncommitted Changes**:
- Before starting reorganization, check for uncommitted changes
- If found, prompt user to commit or stash changes
- Abort reorganization if working directory is not clean

**Commit Failures**:
- If git commit fails, log the error
- Provide instructions for manual commit
- Ensure all file operations are complete even if commit fails

## Testing Strategy

### Unit Tests

Unit tests will focus on specific examples and edge cases:

1. **File Movement Tests**:
   - Test moving a single file
   - Test moving an empty directory
   - Test moving a directory with nested structure
   - Test handling of symbolic links
   - Test error handling for permission denied

2. **Import Update Tests**:
   - Test updating absolute imports
   - Test updating relative imports
   - Test handling of multi-line imports
   - Test handling of import aliases
   - Test handling of from...import statements

3. **Reference Update Tests**:
   - Test updating markdown links
   - Test updating relative paths in documentation
   - Test handling of absolute paths
   - Test handling of URLs (should not be modified)

4. **Cleanup Tests**:
   - Test removal of __pycache__ directories
   - Test removal of .pyc files
   - Test preservation of .gitignore
   - Test removal of .log files
   - Test preservation of directories with .gitkeep

5. **Git Integration Tests**:
   - Test staging moved files
   - Test staging deleted files
   - Test commit creation
   - Test verification of clean state

### Property-Based Tests

Property-based tests will verify universal properties across all inputs using a property-based testing library (Hypothesis for Python). Each test will run a minimum of 100 iterations.

1. **Property 1: File content preservation**
   - Generate random file content and paths
   - Move files and verify content is identical
   - **Feature: test-docs-reorganization, Property 1: File content preservation during moves**

2. **Property 2: Directory structure preservation**
   - Generate random directory structures
   - Move directories and verify relative paths are preserved
   - **Feature: test-docs-reorganization, Property 2: Directory structure preservation**

3. **Property 3: Configuration file preservation**
   - Generate random directory trees with config files
   - Move directories and verify config files are in correct relative positions
   - **Feature: test-docs-reorganization, Property 3: Configuration file preservation**

4. **Property 4: Import statement updates**
   - Generate random Python files with various import styles
   - Move files and verify imports are correctly updated
   - **Feature: test-docs-reorganization, Property 4: Import statement updates**

5. **Property 5: Documentation reference updates**
   - Generate random markdown files with relative path references
   - Move files and verify references are correctly updated
   - **Feature: test-docs-reorganization, Property 5: Documentation reference updates**

6. **Property 6: Reference validity**
   - Generate random documentation with file references
   - After reorganization, verify all references point to existing files
   - **Feature: test-docs-reorganization, Property 6: Reference validity after updates**

7. **Property 7: Cache artifact removal**
   - Generate random project structures with cache files
   - Run cleanup and verify no cache artifacts remain
   - **Feature: test-docs-reorganization, Property 7: Cache artifact removal**

8. **Property 8: Log file removal**
   - Generate random project structures with log files
   - Run cleanup and verify no log files remain
   - **Feature: test-docs-reorganization, Property 8: Log file removal**

9. **Property 9: Gitignore preservation**
   - Generate random .gitignore content
   - Run cleanup and verify .gitignore is unchanged
   - **Feature: test-docs-reorganization, Property 9: Gitignore preservation**

10. **Property 10: Directory preservation with placeholders**
    - Generate random directory structures with .gitkeep files
    - Run cleanup and verify directories with placeholders still exist
    - **Feature: test-docs-reorganization, Property 10: Directory preservation with placeholders**

11. **Property 11: Empty directory removal**
    - Generate random directory structures
    - Move all files and verify empty directories are removed
    - **Feature: test-docs-reorganization, Property 11: Empty directory removal**

12. **Property 12: Directory preservation with content**
    - Generate random directory structures with varying content
    - Move some files and verify directories with remaining content are preserved
    - **Feature: test-docs-reorganization, Property 12: Directory preservation with content**

### Integration Tests

Integration tests will verify the complete reorganization workflow:

1. **End-to-End Reorganization Test**:
   - Create a test project structure mimicking the current state
   - Run the complete reorganization process
   - Verify all files are in correct locations
   - Verify all imports are updated
   - Verify all references are updated
   - Verify cleanup is complete
   - Verify git commit is created

2. **Rollback Test**:
   - Run reorganization on a test project
   - Verify ability to rollback using git
   - Verify project returns to original state

3. **Idempotency Test**:
   - Run reorganization twice on the same project
   - Verify second run detects no changes needed
   - Verify no errors or duplicate operations

### Test Configuration

- Use pytest as the test runner
- Configure Hypothesis for property-based tests with minimum 100 iterations
- Use temporary directories for all file system tests
- Mock git operations in unit tests, use real git in integration tests
- Run tests in isolated environments to prevent interference
