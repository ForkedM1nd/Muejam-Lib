#!/usr/bin/env python3
"""
Verification script for monorepo restructure.

This script verifies that the monorepo restructuring was completed successfully
by checking directory structure, file movements, import paths, and system health.

Usage:
    python scripts/verification/verify-restructure.py
    python scripts/verification/verify-restructure.py --checks health,api,database
    python scripts/verification/verify-restructure.py --verbose
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple, Dict

# Colors for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


class VerificationResult:
    """Result of a verification check."""
    
    def __init__(self, name: str, passed: bool, message: str = ""):
        self.name = name
        self.passed = passed
        self.message = message
    
    def __str__(self) -> str:
        status = f"{GREEN}✓ PASS{RESET}" if self.passed else f"{RED}✗ FAIL{RESET}"
        msg = f": {self.message}" if self.message else ""
        return f"{status} {self.name}{msg}"


class RestructureVerifier:
    """Verifies monorepo restructure completion."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.root = Path(__file__).parent.parent.parent
        self.results: List[VerificationResult] = []
    
    def log(self, message: str, level: str = "info"):
        """Log a message if verbose mode is enabled."""
        if self.verbose:
            prefix = {
                "info": f"{BLUE}ℹ{RESET}",
                "success": f"{GREEN}✓{RESET}",
                "error": f"{RED}✗{RESET}",
                "warning": f"{YELLOW}⚠{RESET}",
            }.get(level, "")
            print(f"{prefix} {message}")
    
    def add_result(self, name: str, passed: bool, message: str = ""):
        """Add a verification result."""
        result = VerificationResult(name, passed, message)
        self.results.append(result)
        if self.verbose:
            print(result)
    
    def check_directory_structure(self) -> bool:
        """Verify top-level directory structure."""
        self.log("Checking directory structure...", "info")
        
        required_dirs = [
            "apps",
            "apps/backend",
            "apps/frontend",
            "docs",
            "docs/architecture",
            "docs/features",
            "docs/development",
            "docs/deployment",
            "docs/archive",
            "tests",
            "tests/backend",
            "scripts",
            "scripts/database",
            "scripts/deployment",
            "scripts/verification",
            "infra",
            "packages",
        ]
        
        all_exist = True
        for dir_path in required_dirs:
            full_path = self.root / dir_path
            exists = full_path.exists() and full_path.is_dir()
            if not exists:
                self.log(f"Missing directory: {dir_path}", "error")
                all_exist = False
            else:
                self.log(f"Found directory: {dir_path}", "success")
        
        self.add_result(
            "Directory Structure",
            all_exist,
            "All required directories exist" if all_exist else "Some directories missing"
        )
        return all_exist
    
    def check_file_movements(self) -> bool:
        """Verify key files were moved correctly."""
        self.log("Checking file movements...", "info")
        
        # Check that files exist in new locations
        expected_files = [
            "docs/archive/ai-artifacts/BACKEND_TEST_SUMMARY.md",
            "docs/features/authentication/api-key-auth.md",
            "docs/features/gdpr/overview.md",
            "docs/features/moderation/content-filters.md",
            "scripts/database/seed-data.py",
            "scripts/deployment/deploy.sh",
            "scripts/verification/verify-ratelimit-setup.py",
            "infra/iam-policies/secrets-manager-policy.json",
            "tests/backend/infrastructure/test_config_validator.py",
            "apps/backend/apps/security/suspicious_activity_detector.py",
            "apps/backend/apps/moderation/shadowban.py",
            "apps/backend/apps/users/account_suspension.py",
        ]
        
        all_exist = True
        for file_path in expected_files:
            full_path = self.root / file_path
            exists = full_path.exists() and full_path.is_file()
            if not exists:
                self.log(f"Missing file: {file_path}", "error")
                all_exist = False
            else:
                self.log(f"Found file: {file_path}", "success")
        
        self.add_result(
            "File Movements",
            all_exist,
            "All key files in correct locations" if all_exist else "Some files missing"
        )
        return all_exist
    
    def check_django_config(self) -> bool:
        """Verify Django configuration is correct."""
        self.log("Checking Django configuration...", "info")
        
        settings_file = self.root / "apps/backend/config/settings.py"
        if not settings_file.exists():
            self.add_result("Django Config", False, "settings.py not found")
            return False
        
        content = settings_file.read_text()
        
        # Check for apps.security in INSTALLED_APPS
        has_security_app = "'apps.security'" in content or '"apps.security"' in content
        
        if not has_security_app:
            self.log("apps.security not in INSTALLED_APPS", "error")
        else:
            self.log("apps.security found in INSTALLED_APPS", "success")
        
        self.add_result(
            "Django Config",
            has_security_app,
            "apps.security in INSTALLED_APPS" if has_security_app else "apps.security missing"
        )
        return has_security_app
    
    def check_pytest_config(self) -> bool:
        """Verify pytest configuration is correct."""
        self.log("Checking pytest configuration...", "info")
        
        pytest_ini = self.root / "apps/backend/pytest.ini"
        if not pytest_ini.exists():
            self.add_result("Pytest Config", False, "pytest.ini not found")
            return False
        
        content = pytest_ini.read_text()
        
        # Check for correct testpaths
        has_testpaths = "testpaths = apps ../../tests/backend" in content
        
        if not has_testpaths:
            self.log("testpaths not configured correctly", "error")
        else:
            self.log("testpaths configured correctly", "success")
        
        self.add_result(
            "Pytest Config",
            has_testpaths,
            "testpaths configured correctly" if has_testpaths else "testpaths incorrect"
        )
        return has_testpaths
    
    def check_gitignore(self) -> bool:
        """Verify .gitignore has required patterns."""
        self.log("Checking .gitignore...", "info")
        
        gitignore = self.root / ".gitignore"
        if not gitignore.exists():
            self.add_result("Gitignore", False, ".gitignore not found")
            return False
        
        content = gitignore.read_text()
        
        required_patterns = [
            ".hypothesis/",
            ".pytest_cache/",
            "__pycache__/",
            "node_modules/",
        ]
        
        all_present = True
        for pattern in required_patterns:
            if pattern not in content:
                self.log(f"Missing pattern: {pattern}", "error")
                all_present = False
            else:
                self.log(f"Found pattern: {pattern}", "success")
        
        self.add_result(
            "Gitignore",
            all_present,
            "All patterns present" if all_present else "Some patterns missing"
        )
        return all_present
    
    def check_django_health(self) -> bool:
        """Run Django check command."""
        self.log("Running Django check...", "info")
        
        try:
            result = subprocess.run(
                ["python", "manage.py", "check"],
                cwd=self.root / "apps/backend",
                capture_output=True,
                text=True,
                timeout=30
            )
            
            passed = result.returncode == 0
            message = "Django check passed" if passed else f"Django check failed: {result.stderr}"
            
            if passed:
                self.log("Django check passed", "success")
            else:
                self.log(f"Django check failed: {result.stderr}", "error")
            
            self.add_result("Django Health", passed, message)
            return passed
        except Exception as e:
            self.log(f"Error running Django check: {e}", "error")
            self.add_result("Django Health", False, f"Error: {e}")
            return False
    
    def check_test_discovery(self) -> bool:
        """Verify pytest can discover tests."""
        self.log("Checking test discovery...", "info")
        
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "--collect-only", "-q"],
                cwd=self.root / "apps/backend",
                capture_output=True,
                text=True,
                timeout=30
            )
            
            passed = result.returncode == 0 and "tests collected" in result.stdout
            
            if passed:
                # Extract number of tests
                for line in result.stdout.split('\n'):
                    if "tests collected" in line:
                        self.log(f"Test discovery: {line.strip()}", "success")
                        break
            else:
                self.log(f"Test discovery failed: {result.stderr}", "error")
            
            self.add_result(
                "Test Discovery",
                passed,
                "Tests discovered successfully" if passed else "Test discovery failed"
            )
            return passed
        except Exception as e:
            self.log(f"Error checking test discovery: {e}", "error")
            self.add_result("Test Discovery", False, f"Error: {e}")
            return False
    
    def check_documentation(self) -> bool:
        """Verify key documentation files exist."""
        self.log("Checking documentation...", "info")
        
        required_docs = [
            "CONTRIBUTING.md",
            "docs/development/setup.md",
            "docs/development/conventions.md",
            "docs/development/testing.md",
            "docs/development/workflows.md",
            "docs/development/troubleshooting.md",
            "docs/architecture/monorepo-structure.md",
            "docs/architecture/infrastructure.md",
            "docs/deployment/migration-guide.md",
            "docs/deployment/verification.md",
            "docs/deployment/ci-cd.md",
        ]
        
        all_exist = True
        for doc_path in required_docs:
            full_path = self.root / doc_path
            exists = full_path.exists() and full_path.is_file()
            if not exists:
                self.log(f"Missing documentation: {doc_path}", "error")
                all_exist = False
            else:
                self.log(f"Found documentation: {doc_path}", "success")
        
        self.add_result(
            "Documentation",
            all_exist,
            "All documentation present" if all_exist else "Some documentation missing"
        )
        return all_exist
    
    def run_all_checks(self, checks: List[str] = None) -> bool:
        """Run all verification checks."""
        available_checks = {
            "structure": self.check_directory_structure,
            "files": self.check_file_movements,
            "django": self.check_django_config,
            "pytest": self.check_pytest_config,
            "gitignore": self.check_gitignore,
            "health": self.check_django_health,
            "tests": self.check_test_discovery,
            "docs": self.check_documentation,
        }
        
        if checks:
            checks_to_run = {k: v for k, v in available_checks.items() if k in checks}
        else:
            checks_to_run = available_checks
        
        print(f"\n{BLUE}Running {len(checks_to_run)} verification checks...{RESET}\n")
        
        for check_name, check_func in checks_to_run.items():
            try:
                check_func()
            except Exception as e:
                self.log(f"Error in {check_name} check: {e}", "error")
                self.add_result(check_name, False, f"Error: {e}")
        
        return all(r.passed for r in self.results)
    
    def print_summary(self):
        """Print verification summary."""
        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}Verification Summary{RESET}")
        print(f"{BLUE}{'='*60}{RESET}\n")
        
        for result in self.results:
            print(result)
        
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        
        print(f"\n{BLUE}{'='*60}{RESET}")
        if passed == total:
            print(f"{GREEN}✓ All checks passed ({passed}/{total}){RESET}")
        else:
            print(f"{RED}✗ Some checks failed ({passed}/{total} passed){RESET}")
        print(f"{BLUE}{'='*60}{RESET}\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Verify monorepo restructure completion"
    )
    parser.add_argument(
        "--checks",
        help="Comma-separated list of checks to run (structure,files,django,pytest,gitignore,health,tests,docs)",
        type=str
    )
    parser.add_argument(
        "--verbose",
        "-v",
        help="Enable verbose output",
        action="store_true"
    )
    
    args = parser.parse_args()
    
    checks = args.checks.split(",") if args.checks else None
    
    verifier = RestructureVerifier(verbose=args.verbose)
    success = verifier.run_all_checks(checks)
    verifier.print_summary()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
