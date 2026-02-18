# Validation Suite for Monorepo Restructure

## Overview

The validation suite provides comprehensive validation methods to verify the restructured repository is functional. It includes syntax validation, import resolution checking, and wrappers for Django check, frontend build, Docker build, and test discovery.

## Components

### ValidationSuite Class

The main class that orchestrates all validation checks.

**Location**: `tools/restructure/validator.py`

**Key Methods**:

1. **validate_python_syntax(file_path=None)** - Validates Python file syntax using AST parsing
   - Can validate a specific file or all Python files in the repository
   - Skips virtual environments, cache, and build directories
   - Returns ValidationResult with syntax errors

2. **validate_typescript_syntax(file_path=None)** - Validates TypeScript file syntax using tsc compiler
   - Requires TypeScript compiler (tsc) to be installed
   - Can validate a specific file or all TypeScript files
   - Returns ValidationResult with compilation errors

3. **validate_imports()** - Validates that all Python import statements can be resolved
   - Performs syntax validation first
   - Runs Django system check to validate imports
   - Checks for broken relative imports
   - Returns ValidationResult with import resolution errors

4. **validate_django()** - Validates Django configuration by running 'python manage.py check'
   - Checks Django settings are valid
   - Verifies all installed apps can be imported
   - Validates models are properly configured
   - Validates URL configurations
   - Returns ValidationResult with Django check errors

5. **validate_frontend_build()** - Validates frontend can build successfully
   - Runs 'npm run build' in the frontend directory
   - Checks all TypeScript files compile
   - Verifies all imports resolve
   - Validates Vite build completes successfully
   - Returns ValidationResult with build errors

6. **validate_docker_build(service=None)** - Validates Docker images can build successfully
   - Runs 'docker-compose build' to verify all services build
   - Can build a specific service or all services
   - Returns ValidationResult with Docker build errors

7. **validate_test_discovery()** - Validates pytest can discover all tests
   - Runs 'pytest --collect-only' to verify test discovery
   - Returns ValidationResult with test discovery errors

8. **run_all()** - Runs all validation checks and generates a comprehensive report
   - Executes all 7 validation checks
   - Returns ValidationReport with overall success status and detailed results

9. **print_report(report)** - Prints a formatted validation report
   - Displays overall status and summary
   - Shows errors and warnings for each check
   - Limits output to first 5 errors and 3 warnings per check

## Data Classes

### ValidationResult

Represents the result of a single validation check.

**Fields**:
- `success` (bool): Whether the validation passed
- `message` (str): Summary message
- `errors` (List[str]): List of error messages
- `warnings` (List[str]): List of warning messages

### ValidationReport

Represents a comprehensive validation report from running all checks.

**Fields**:
- `overall_success` (bool): Whether all checks passed
- `results` (Dict[str, ValidationResult]): Results for each check
- `summary` (str): Overall summary message

## Usage

### Command Line

Run all validation checks:
```bash
python tools/restructure/validator.py
```

Run a specific check:
```bash
python tools/restructure/validator.py --check python_syntax
python tools/restructure/validator.py --check django
python tools/restructure/validator.py --check frontend_build
```

Specify repository root:
```bash
python tools/restructure/validator.py --repo-root /path/to/repo
```

### Python API

```python
from pathlib import Path
from validator import ValidationSuite

# Initialize validator
repo_root = Path("/path/to/repo")
validator = ValidationSuite(repo_root)

# Run individual checks
result = validator.validate_python_syntax()
if not result.success:
    print(f"Python syntax errors: {result.errors}")

result = validator.validate_django()
if not result.success:
    print(f"Django check errors: {result.errors}")

# Run all checks
report = validator.run_all()
validator.print_report(report)

# Check overall success
if report.overall_success:
    print("All validation checks passed!")
else:
    print("Some validation checks failed")
```

### Integration with MigrationTool

The ValidationSuite is integrated with the MigrationTool for comprehensive validation:

```python
from pathlib import Path
from migration_tool import MigrationTool

# Initialize migration tool
repo_root = Path("/path/to/repo")
tool = MigrationTool(repo_root)

# Run basic validation (quick)
result = tool.validate_changes()
print(result.message)

# Run comprehensive validation (thorough)
result = tool.validate_comprehensive()
if result.success:
    print("All validation checks passed!")
else:
    print(f"Validation failed: {result.errors}")
```

## Requirements Validated

The validation suite validates the following requirements:

- **Requirement 10.1**: Python and TypeScript syntax validation
- **Requirement 10.2**: Frontend build validation
- **Requirement 10.3**: Docker build validation
- **Requirement 10.4**: Test discovery validation
- **Requirement 10.5**: Import resolution validation
- **Requirement 10.6**: Comprehensive verification script

## Testing

The validation suite includes comprehensive unit tests:

**Location**: `tools/restructure/test_validator.py`

**Test Coverage**:
- 25 unit tests covering all validation methods
- Tests for success cases, error cases, and edge cases
- Tests for missing dependencies (tsc, Docker, npm)
- Tests for missing configuration files
- Tests for the complete validation suite

Run tests:
```bash
python -m pytest tools/restructure/test_validator.py -v
```

## Example

See `tools/restructure/example_validation.py` for a complete example of using the validation suite.

## Dependencies

- **Python 3.7+**: Required for AST parsing and subprocess management
- **TypeScript Compiler (tsc)**: Required for TypeScript syntax validation
- **npm**: Required for frontend build validation
- **Docker**: Required for Docker build validation
- **pytest**: Required for test discovery validation
- **Django**: Required for Django system check

## Error Handling

The validation suite handles various error conditions gracefully:

- **Missing files**: Returns ValidationResult with appropriate error message
- **Missing dependencies**: Returns ValidationResult indicating dependency not available
- **Timeouts**: Commands have reasonable timeouts (60s for Django/tests, 5min for frontend, 10min for Docker)
- **Parse errors**: Captures and reports syntax errors with file and line number
- **Build errors**: Captures and reports build errors from stdout/stderr

## Performance

Validation times (approximate):
- Python syntax: 1-5 seconds (depends on number of files)
- TypeScript syntax: 5-15 seconds (depends on project size)
- Import resolution: 5-10 seconds
- Django check: 5-15 seconds
- Frontend build: 30-120 seconds (depends on project size)
- Docker build: 60-300 seconds (depends on image size)
- Test discovery: 5-10 seconds

Total time for complete validation: 2-8 minutes

## Future Enhancements

Potential improvements for future versions:

1. **Parallel execution**: Run independent checks in parallel to reduce total time
2. **Incremental validation**: Only validate changed files
3. **Caching**: Cache validation results for unchanged files
4. **Custom checks**: Allow users to add custom validation checks
5. **HTML reports**: Generate HTML reports for better visualization
6. **CI/CD integration**: Provide GitHub Actions workflow examples
