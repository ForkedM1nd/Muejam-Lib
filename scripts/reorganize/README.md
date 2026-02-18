# Test and Documentation Reorganization Script

This script reorganizes the MueJam Library project structure by moving backend tests and documentation to their proper locations, updating all references, and cleaning up cache files.

## What It Does

The reorganization script performs the following operations:

1. **Moves Backend Tests**: Relocates all backend tests from `apps/backend/tests` to `apps/backend/tests/`
2. **Moves Backend Documentation**: Relocates all backend documentation from `docs/backend` to `docs/backend/`
3. **Updates Import Statements**: Automatically updates all Python import statements to reflect new file locations
4. **Updates Documentation References**: Updates all file path references in markdown files
5. **Updates Test Configuration**: Updates pytest.ini and other test configuration files
6. **Cleans Up Cache Files**: Removes `__pycache__`, `.pyc`, `.pyo`, `.pytest_cache`, and `.hypothesis` directories
7. **Cleans Up Log Files**: Removes all `.log` files from the project
8. **Commits Changes**: Creates a git commit with all reorganization changes

## Usage

### Basic Usage

Run the script from the repository root:

```bash
python scripts/reorganize/reorganize.py
```

### Command-Line Options

#### Preview Changes (Dry Run)

Preview what the script will do without making any changes:

```bash
python scripts/reorganize/reorganize.py --dry-run
```

#### Verbose Logging

Enable detailed logging to see exactly what the script is doing:

```bash
python scripts/reorganize/reorganize.py --verbose
```

#### Skip Operations

You can skip specific operations using these flags:

```bash
# Skip moving backend tests
python scripts/reorganize/reorganize.py --skip-tests

# Skip moving backend documentation
python scripts/reorganize/reorganize.py --skip-docs

# Skip cleanup of cache and log files
python scripts/reorganize/reorganize.py --skip-cleanup

# Skip git commit (useful for manual review before committing)
python scripts/reorganize/reorganize.py --skip-commit
```

#### Combine Options

You can combine multiple options:

```bash
# Preview with verbose logging
python scripts/reorganize/reorganize.py --dry-run --verbose

# Execute without committing, with verbose logging
python scripts/reorganize/reorganize.py --skip-commit --verbose
```

## Common Usage Patterns

### 1. Safe Preview Before Execution

Always preview changes first to ensure the script will do what you expect:

```bash
# Step 1: Preview changes
python scripts/reorganize/reorganize.py --dry-run --verbose

# Step 2: Review the output

# Step 3: Execute if everything looks good
python scripts/reorganize/reorganize.py
```

### 2. Execute Without Auto-Commit

If you want to review changes before committing:

```bash
# Execute reorganization but don't commit
python scripts/reorganize/reorganize.py --skip-commit

# Review the changes
git status
git diff

# Commit manually if satisfied
git add .
git commit -m "Reorganize tests and docs"
```

### 3. Partial Reorganization

If you only want to move tests or docs:

```bash
# Only move tests, skip docs and cleanup
python scripts/reorganize/reorganize.py --skip-docs --skip-cleanup

# Only move docs, skip tests and cleanup
python scripts/reorganize/reorganize.py --skip-tests --skip-cleanup
```

### 4. Cleanup Only

If you only want to clean up cache and log files:

```bash
python scripts/reorganize/reorganize.py --skip-tests --skip-docs
```

## How to Rollback

If you need to undo the reorganization, you can use git to rollback:

### If Changes Are Not Yet Committed

```bash
# Discard all changes
git reset --hard HEAD

# Or restore specific files/directories
git restore .
```

### If Changes Are Already Committed

```bash
# Find the commit hash before reorganization
git log --oneline

# Revert to the previous commit (replace <commit-hash> with actual hash)
git reset --hard <commit-hash>

# Or create a new commit that undoes the changes
git revert HEAD
```

### Using Git Reflog

If you've lost track of commits:

```bash
# View recent HEAD positions
git reflog

# Reset to a previous position (replace HEAD@{n} with desired position)
git reset --hard HEAD@{1}
```

## Requirements

- Python 3.7 or higher
- Git repository (for commit operations)
- Required Python packages:
  - pathlib (standard library)
  - argparse (standard library)
  - logging (standard library)

## Project Structure Changes

### Before Reorganization

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

### After Reorganization

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

## Troubleshooting

### Script Reports Uncommitted Changes

The script checks for uncommitted changes before running. If you have uncommitted changes:

1. Commit or stash your changes first
2. Or use `--skip-commit` to run without the clean state check

### Import Updates Not Working

If import statements aren't being updated correctly:

1. Check that the files are valid Python syntax
2. Review the verbose output with `--verbose` flag
3. Manually fix any imports that weren't caught

### Documentation References Not Updated

If documentation references aren't being updated:

1. Check that references use relative paths (not absolute URLs)
2. Review the verbose output with `--verbose` flag
3. Manually fix any references that weren't caught

### Permission Errors

If you encounter permission errors:

1. Ensure you have write permissions to all directories
2. Check that no files are open in other applications
3. On Windows, ensure no processes are locking the files

## Safety Features

The script includes several safety features:

1. **Dry Run Mode**: Preview changes without executing them
2. **Clean State Check**: Verifies no uncommitted changes before running (unless `--skip-commit` is used)
3. **Error Handling**: Continues with other operations if one fails
4. **Logging**: Detailed logging of all operations
5. **Verification**: Validates results after execution
6. **Git Integration**: All changes are tracked in version control

## Exit Codes

- `0`: Success
- `1`: Failure or user cancellation

## Support

For issues or questions:

1. Review the verbose output with `--verbose` flag
2. Check the troubleshooting section above
3. Review the git history to understand what changed
4. Use `--dry-run` to preview operations before executing
