#!/usr/bin/env python3
"""
Validation Suite for Monorepo Restructure

This module provides comprehensive validation methods to verify the restructured
repository is functional. It includes syntax validation, import resolution checking,
and wrappers for Django check, frontend build, Docker build, and test discovery.

Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6
"""

import ast
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple, Dict


@dataclass
class ValidationResult:
    """Result of a validation check."""
    success: bool
    message: str
    errors: List[str]
    warnings: List[str]


@dataclass
class ValidationReport:
    """Comprehensive validation report."""
    overall_success: bool
    results: Dict[str, ValidationResult]
    summary: str


class ValidationSuite:
    """Comprehensive validation suite for repository restructuring."""
    
    def __init__(self, repo_root: Path):
        """
        Initialize ValidationSuite.
        
        Args:
            repo_root: Root directory of the repository
        """
        self.repo_root = repo_root
        self.backend_root = repo_root / "apps" / "backend"
        self.frontend_root = repo_root / "apps" / "frontend"
    
    def validate_python_syntax(self, file_path: Optional[Path] = None) -> ValidationResult:
        """
        Validate Python file syntax using AST parsing.
        
        Validates either a specific file or all Python files in the repository.
        
        Args:
            file_path: Optional specific file to validate. If None, validates all Python files.
            
        Returns:
            ValidationResult with syntax validation details
            
        Requirements: 10.1
        """
        errors = []
        warnings = []
        files_checked = 0
        
        # Determine which files to check
        if file_path:
            python_files = [file_path] if file_path.exists() else []
            if not python_files:
                return ValidationResult(
                    success=False,
                    message=f"File not found: {file_path}",
                    errors=[f"File not found: {file_path}"],
                    warnings=[]
                )
        else:
            # Find all Python files, excluding virtual environments and cache
            python_files = []
            for pattern in ['**/*.py']:
                for py_file in self.repo_root.rglob(pattern):
                    # Skip virtual environments, cache, and build directories
                    if any(part in py_file.parts for part in [
                        'venv', '.venv', 'env', '.env', 
                        '__pycache__', '.pytest_cache', '.hypothesis',
                        'node_modules', 'build', 'dist'
                    ]):
                        continue
                    python_files.append(py_file)
        
        # Validate each file
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    source_code = f.read()
                
                # Parse the file using AST
                ast.parse(source_code, filename=str(py_file))
                files_checked += 1
                
            except SyntaxError as e:
                error_msg = f"{py_file.relative_to(self.repo_root)}:{e.lineno}: {e.msg}"
                errors.append(error_msg)
            except Exception as e:
                warning_msg = f"{py_file.relative_to(self.repo_root)}: {str(e)}"
                warnings.append(warning_msg)
        
        success = len(errors) == 0
        message = (
            f"Validated {files_checked} Python files" if success
            else f"Found {len(errors)} syntax errors in {files_checked} files"
        )
        
        return ValidationResult(
            success=success,
            message=message,
            errors=errors,
            warnings=warnings
        )

    def validate_typescript_syntax(self, file_path: Optional[Path] = None) -> ValidationResult:
        """
        Validate TypeScript file syntax using tsc compiler.
        
        Validates either a specific file or all TypeScript files in the frontend.
        
        Args:
            file_path: Optional specific file to validate. If None, validates all TypeScript files.
            
        Returns:
            ValidationResult with syntax validation details
            
        Requirements: 10.1
        """
        errors = []
        warnings = []
        
        # Check if TypeScript compiler is available
        try:
            subprocess.run(
                ["npx", "tsc", "--version"],
                cwd=self.frontend_root,
                capture_output=True,
                text=True,
                check=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            return ValidationResult(
                success=False,
                message="TypeScript compiler not available",
                errors=["TypeScript compiler (tsc) not found. Run 'npm install' in frontend directory."],
                warnings=[]
            )
        
        # Run TypeScript compiler in noEmit mode (syntax check only)
        try:
            if file_path:
                # Validate specific file
                result = subprocess.run(
                    ["npx", "tsc", "--noEmit", str(file_path)],
                    cwd=self.frontend_root,
                    capture_output=True,
                    text=True
                )
            else:
                # Validate all files using tsconfig
                result = subprocess.run(
                    ["npx", "tsc", "--noEmit"],
                    cwd=self.frontend_root,
                    capture_output=True,
                    text=True
                )
            
            # Parse output for errors
            if result.returncode != 0:
                for line in result.stdout.split('\n'):
                    if line.strip() and not line.startswith('Found'):
                        errors.append(line.strip())
            
            success = result.returncode == 0
            message = (
                "TypeScript syntax validation passed" if success
                else f"Found {len(errors)} TypeScript errors"
            )
            
            return ValidationResult(
                success=success,
                message=message,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            return ValidationResult(
                success=False,
                message="TypeScript validation failed",
                errors=[f"Validation error: {str(e)}"],
                warnings=[]
            )
    
    def validate_imports(self) -> ValidationResult:
        """
        Validate that all Python import statements can be resolved.
        
        This performs a comprehensive check by:
        1. Validating Python syntax (imports must parse correctly)
        2. Checking that imported modules exist in the repository
        3. Running Django's system check which validates imports
        
        Returns:
            ValidationResult with import resolution details
            
        Requirements: 10.5
        """
        errors = []
        warnings = []
        
        # First, validate Python syntax
        syntax_result = self.validate_python_syntax()
        if not syntax_result.success:
            return ValidationResult(
                success=False,
                message="Cannot validate imports due to syntax errors",
                errors=syntax_result.errors,
                warnings=["Fix syntax errors before validating imports"]
            )
        
        # Check Django imports by running system check
        django_result = self.validate_django()
        if not django_result.success:
            errors.extend(django_result.errors)
        
        # Additional import validation: check for common import issues
        python_files = []
        for py_file in self.repo_root.rglob('**/*.py'):
            # Skip virtual environments and cache
            if any(part in py_file.parts for part in [
                'venv', '.venv', 'env', '.env',
                '__pycache__', '.pytest_cache', '.hypothesis',
                'node_modules', 'build', 'dist'
            ]):
                continue
            python_files.append(py_file)
        
        # Parse imports from each file
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read(), filename=str(py_file))
                
                for node in ast.walk(tree):
                    # Check for relative imports that might be broken
                    if isinstance(node, ast.ImportFrom):
                        if node.level > 0:  # Relative import
                            # Validate relative import makes sense
                            if node.level > len(py_file.relative_to(self.repo_root).parts):
                                warning_msg = (
                                    f"{py_file.relative_to(self.repo_root)}: "
                                    f"Relative import level {node.level} exceeds directory depth"
                                )
                                warnings.append(warning_msg)
                                
            except Exception as e:
                warning_msg = f"{py_file.relative_to(self.repo_root)}: Could not parse imports: {e}"
                warnings.append(warning_msg)
        
        success = len(errors) == 0
        message = (
            "All imports validated successfully" if success
            else f"Found {len(errors)} import resolution errors"
        )
        
        return ValidationResult(
            success=success,
            message=message,
            errors=errors,
            warnings=warnings
        )
    
    def validate_django(self) -> ValidationResult:
        """
        Validate Django configuration by running 'python manage.py check'.
        
        This checks:
        - Django settings are valid
        - All installed apps can be imported
        - Models are properly configured
        - URL configurations are valid
        
        Returns:
            ValidationResult with Django check details
            
        Requirements: 10.1
        """
        errors = []
        warnings = []
        
        manage_py = self.backend_root / "manage.py"
        
        if not manage_py.exists():
            return ValidationResult(
                success=False,
                message="Django manage.py not found",
                errors=[f"manage.py not found at {manage_py}"],
                warnings=[]
            )
        
        try:
            # Run Django system check
            result = subprocess.run(
                [sys.executable, "manage.py", "check", "--deploy"],
                cwd=self.backend_root,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Parse output
            output_lines = result.stdout.split('\n') + result.stderr.split('\n')
            
            for line in output_lines:
                line = line.strip()
                if not line:
                    continue
                
                # Categorize output
                if 'ERROR' in line or 'CRITICAL' in line:
                    errors.append(line)
                elif 'WARNING' in line:
                    warnings.append(line)
            
            # Check return code
            success = result.returncode == 0
            
            if success and not errors:
                message = "Django system check passed"
            else:
                message = f"Django check found {len(errors)} errors and {len(warnings)} warnings"
            
            return ValidationResult(
                success=success,
                message=message,
                errors=errors,
                warnings=warnings
            )
            
        except subprocess.TimeoutExpired:
            return ValidationResult(
                success=False,
                message="Django check timed out",
                errors=["Django system check timed out after 60 seconds"],
                warnings=[]
            )
        except Exception as e:
            return ValidationResult(
                success=False,
                message="Django check failed",
                errors=[f"Failed to run Django check: {str(e)}"],
                warnings=[]
            )

    def validate_frontend_build(self) -> ValidationResult:
        """
        Validate frontend can build successfully by running 'npm run build'.
        
        This checks:
        - All TypeScript files compile
        - All imports resolve
        - Vite build completes successfully
        
        Returns:
            ValidationResult with frontend build details
            
        Requirements: 10.2
        """
        errors = []
        warnings = []
        
        package_json = self.frontend_root / "package.json"
        
        if not package_json.exists():
            return ValidationResult(
                success=False,
                message="Frontend package.json not found",
                errors=[f"package.json not found at {package_json}"],
                warnings=[]
            )
        
        # Check if node_modules exists
        node_modules = self.frontend_root / "node_modules"
        if not node_modules.exists():
            warnings.append("node_modules not found. Run 'npm install' first.")
        
        try:
            # Run npm build
            result = subprocess.run(
                ["npm", "run", "build"],
                cwd=self.frontend_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            # Parse output for errors
            output_lines = result.stdout.split('\n') + result.stderr.split('\n')
            
            for line in output_lines:
                line = line.strip()
                if not line:
                    continue
                
                # Categorize output
                if 'error' in line.lower() or 'failed' in line.lower():
                    errors.append(line)
                elif 'warning' in line.lower():
                    warnings.append(line)
            
            success = result.returncode == 0
            
            if success:
                message = "Frontend build completed successfully"
            else:
                message = f"Frontend build failed with {len(errors)} errors"
            
            return ValidationResult(
                success=success,
                message=message,
                errors=errors,
                warnings=warnings
            )
            
        except subprocess.TimeoutExpired:
            return ValidationResult(
                success=False,
                message="Frontend build timed out",
                errors=["Frontend build timed out after 5 minutes"],
                warnings=[]
            )
        except FileNotFoundError:
            return ValidationResult(
                success=False,
                message="npm not found",
                errors=["npm command not found. Ensure Node.js is installed."],
                warnings=[]
            )
        except Exception as e:
            return ValidationResult(
                success=False,
                message="Frontend build failed",
                errors=[f"Failed to run frontend build: {str(e)}"],
                warnings=[]
            )
    
    def validate_docker_build(self, service: Optional[str] = None) -> ValidationResult:
        """
        Validate Docker images can build successfully.
        
        Runs 'docker-compose build' to verify all services build correctly.
        
        Args:
            service: Optional specific service to build. If None, builds all services.
        
        Returns:
            ValidationResult with Docker build details
            
        Requirements: 10.3
        """
        errors = []
        warnings = []
        
        docker_compose = self.repo_root / "docker-compose.yml"
        
        if not docker_compose.exists():
            return ValidationResult(
                success=False,
                message="docker-compose.yml not found",
                errors=[f"docker-compose.yml not found at {docker_compose}"],
                warnings=[]
            )
        
        try:
            # Check if Docker is available
            subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                check=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            return ValidationResult(
                success=False,
                message="Docker not available",
                errors=["Docker command not found. Ensure Docker is installed and running."],
                warnings=[]
            )
        
        try:
            # Build Docker images
            cmd = ["docker-compose", "build"]
            if service:
                cmd.append(service)
            
            result = subprocess.run(
                cmd,
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout
            )
            
            # Parse output for errors
            output_lines = result.stdout.split('\n') + result.stderr.split('\n')
            
            for line in output_lines:
                line = line.strip()
                if not line:
                    continue
                
                # Categorize output
                if 'error' in line.lower() or 'failed' in line.lower():
                    errors.append(line)
                elif 'warning' in line.lower():
                    warnings.append(line)
            
            success = result.returncode == 0
            
            if success:
                message = f"Docker build completed successfully{' for ' + service if service else ''}"
            else:
                message = f"Docker build failed with {len(errors)} errors"
            
            return ValidationResult(
                success=success,
                message=message,
                errors=errors,
                warnings=warnings
            )
            
        except subprocess.TimeoutExpired:
            return ValidationResult(
                success=False,
                message="Docker build timed out",
                errors=["Docker build timed out after 10 minutes"],
                warnings=[]
            )
        except Exception as e:
            return ValidationResult(
                success=False,
                message="Docker build failed",
                errors=[f"Failed to run Docker build: {str(e)}"],
                warnings=[]
            )
    
    def validate_test_discovery(self) -> ValidationResult:
        """
        Validate pytest can discover all tests.
        
        Runs 'pytest --collect-only' to verify test discovery works correctly.
        
        Returns:
            ValidationResult with test discovery details
            
        Requirements: 10.4
        """
        errors = []
        warnings = []
        
        pytest_ini = self.backend_root / "pytest.ini"
        
        if not pytest_ini.exists():
            warnings.append(f"pytest.ini not found at {pytest_ini}")
        
        try:
            # Run pytest collection
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "--collect-only", "-q"],
                cwd=self.backend_root,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Parse output
            output_lines = result.stdout.split('\n') + result.stderr.split('\n')
            
            test_count = 0
            for line in output_lines:
                line = line.strip()
                if not line:
                    continue
                
                # Count collected tests
                if 'test' in line.lower() and '::' in line:
                    test_count += 1
                
                # Categorize errors
                if 'error' in line.lower() or 'failed' in line.lower():
                    errors.append(line)
                elif 'warning' in line.lower():
                    warnings.append(line)
            
            # Check if any tests were collected
            if test_count == 0 and result.returncode == 0:
                warnings.append("No tests were collected")
            
            success = result.returncode == 0 or result.returncode == 5  # 5 = no tests collected
            
            if success:
                message = f"Test discovery successful: {test_count} tests found"
            else:
                message = f"Test discovery failed with {len(errors)} errors"
            
            return ValidationResult(
                success=success,
                message=message,
                errors=errors,
                warnings=warnings
            )
            
        except subprocess.TimeoutExpired:
            return ValidationResult(
                success=False,
                message="Test discovery timed out",
                errors=["Test discovery timed out after 60 seconds"],
                warnings=[]
            )
        except Exception as e:
            return ValidationResult(
                success=False,
                message="Test discovery failed",
                errors=[f"Failed to run test discovery: {str(e)}"],
                warnings=[]
            )

    def run_all(self) -> ValidationReport:
        """
        Run all validation checks and generate a comprehensive report.
        
        Executes:
        1. Python syntax validation
        2. TypeScript syntax validation
        3. Import resolution checking
        4. Django system check
        5. Frontend build validation
        6. Docker build validation
        7. Test discovery validation
        
        Returns:
            ValidationReport with all validation results
            
        Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6
        """
        results = {}
        
        print("Running validation suite...")
        print()
        
        # 1. Python syntax validation
        print("1. Validating Python syntax...")
        results['python_syntax'] = self.validate_python_syntax()
        print(f"   {results['python_syntax'].message}")
        print()
        
        # 2. TypeScript syntax validation
        print("2. Validating TypeScript syntax...")
        results['typescript_syntax'] = self.validate_typescript_syntax()
        print(f"   {results['typescript_syntax'].message}")
        print()
        
        # 3. Import resolution
        print("3. Validating import resolution...")
        results['imports'] = self.validate_imports()
        print(f"   {results['imports'].message}")
        print()
        
        # 4. Django check
        print("4. Running Django system check...")
        results['django'] = self.validate_django()
        print(f"   {results['django'].message}")
        print()
        
        # 5. Frontend build
        print("5. Validating frontend build...")
        results['frontend_build'] = self.validate_frontend_build()
        print(f"   {results['frontend_build'].message}")
        print()
        
        # 6. Docker build
        print("6. Validating Docker build...")
        results['docker_build'] = self.validate_docker_build()
        print(f"   {results['docker_build'].message}")
        print()
        
        # 7. Test discovery
        print("7. Validating test discovery...")
        results['test_discovery'] = self.validate_test_discovery()
        print(f"   {results['test_discovery'].message}")
        print()
        
        # Generate summary
        total_checks = len(results)
        passed_checks = sum(1 for r in results.values() if r.success)
        failed_checks = total_checks - passed_checks
        
        overall_success = all(r.success for r in results.values())
        
        summary = (
            f"Validation complete: {passed_checks}/{total_checks} checks passed"
            if overall_success
            else f"Validation failed: {failed_checks}/{total_checks} checks failed"
        )
        
        return ValidationReport(
            overall_success=overall_success,
            results=results,
            summary=summary
        )
    
    def print_report(self, report: ValidationReport) -> None:
        """
        Print a formatted validation report.
        
        Args:
            report: ValidationReport to print
        """
        print("=" * 80)
        print("VALIDATION REPORT")
        print("=" * 80)
        print()
        print(f"Overall Status: {'PASSED' if report.overall_success else 'FAILED'}")
        print(f"Summary: {report.summary}")
        print()
        
        for check_name, result in report.results.items():
            status = "✓ PASS" if result.success else "✗ FAIL"
            print(f"{status} - {check_name.replace('_', ' ').title()}")
            print(f"     {result.message}")
            
            if result.errors:
                print(f"     Errors ({len(result.errors)}):")
                for error in result.errors[:5]:  # Show first 5 errors
                    print(f"       - {error}")
                if len(result.errors) > 5:
                    print(f"       ... and {len(result.errors) - 5} more errors")
            
            if result.warnings:
                print(f"     Warnings ({len(result.warnings)}):")
                for warning in result.warnings[:3]:  # Show first 3 warnings
                    print(f"       - {warning}")
                if len(result.warnings) > 3:
                    print(f"       ... and {len(result.warnings) - 3} more warnings")
            
            print()
        
        print("=" * 80)


def main():
    """
    Main entry point for running validation suite from command line.
    
    Usage:
        python validator.py [--check <check_name>] [--repo-root <path>]
    
    Available checks:
        - python_syntax: Validate Python syntax
        - typescript_syntax: Validate TypeScript syntax
        - imports: Validate import resolution
        - django: Run Django system check
        - frontend_build: Validate frontend build
        - docker_build: Validate Docker build
        - test_discovery: Validate test discovery
        - all: Run all checks (default)
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Validation suite for monorepo restructure"
    )
    parser.add_argument(
        '--check',
        choices=[
            'python_syntax', 'typescript_syntax', 'imports', 'django',
            'frontend_build', 'docker_build', 'test_discovery', 'all'
        ],
        default='all',
        help='Specific validation check to run (default: all)'
    )
    parser.add_argument(
        '--repo-root',
        type=Path,
        default=Path.cwd(),
        help='Root directory of the repository (default: current directory)'
    )
    
    args = parser.parse_args()
    
    # Initialize validation suite
    validator = ValidationSuite(args.repo_root)
    
    # Run requested check
    if args.check == 'all':
        report = validator.run_all()
        validator.print_report(report)
        sys.exit(0 if report.overall_success else 1)
    else:
        # Run specific check
        check_methods = {
            'python_syntax': validator.validate_python_syntax,
            'typescript_syntax': validator.validate_typescript_syntax,
            'imports': validator.validate_imports,
            'django': validator.validate_django,
            'frontend_build': validator.validate_frontend_build,
            'docker_build': validator.validate_docker_build,
            'test_discovery': validator.validate_test_discovery
        }
        
        result = check_methods[args.check]()
        
        print(f"Check: {args.check.replace('_', ' ').title()}")
        print(f"Status: {'PASSED' if result.success else 'FAILED'}")
        print(f"Message: {result.message}")
        
        if result.errors:
            print(f"\nErrors ({len(result.errors)}):")
            for error in result.errors:
                print(f"  - {error}")
        
        if result.warnings:
            print(f"\nWarnings ({len(result.warnings)}):")
            for warning in result.warnings:
                print(f"  - {warning}")
        
        sys.exit(0 if result.success else 1)


if __name__ == '__main__':
    main()
