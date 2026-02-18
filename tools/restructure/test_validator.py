#!/usr/bin/env python3
"""
Unit Tests for Validation Suite

Tests the validation methods for the monorepo restructure validation suite.
"""

import ast
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import subprocess

from validator import ValidationSuite, ValidationResult, ValidationReport


class TestValidationSuite(unittest.TestCase):
    """Test cases for ValidationSuite class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.repo_root = Path(self.temp_dir)
        
        # Create directory structure
        (self.repo_root / "apps" / "backend").mkdir(parents=True)
        (self.repo_root / "apps" / "frontend").mkdir(parents=True)
        
        self.validator = ValidationSuite(self.repo_root)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_init(self):
        """Test ValidationSuite initialization."""
        self.assertEqual(self.validator.repo_root, self.repo_root)
        self.assertEqual(self.validator.backend_root, self.repo_root / "apps" / "backend")
        self.assertEqual(self.validator.frontend_root, self.repo_root / "apps" / "frontend")
    
    def test_validate_python_syntax_valid_file(self):
        """Test Python syntax validation with valid file."""
        # Create a valid Python file
        test_file = self.repo_root / "test.py"
        test_file.write_text("def hello():\n    return 'world'\n")
        
        result = self.validator.validate_python_syntax(test_file)
        
        self.assertTrue(result.success)
        self.assertIn("Validated", result.message)
        self.assertEqual(len(result.errors), 0)
    
    def test_validate_python_syntax_invalid_file(self):
        """Test Python syntax validation with invalid file."""
        # Create an invalid Python file
        test_file = self.repo_root / "test_invalid.py"
        test_file.write_text("def hello(\n    return 'world'\n")  # Missing closing paren
        
        result = self.validator.validate_python_syntax(test_file)
        
        self.assertFalse(result.success)
        self.assertGreater(len(result.errors), 0)
    
    def test_validate_python_syntax_nonexistent_file(self):
        """Test Python syntax validation with nonexistent file."""
        test_file = self.repo_root / "nonexistent.py"
        
        result = self.validator.validate_python_syntax(test_file)
        
        self.assertFalse(result.success)
        self.assertIn("not found", result.message.lower())
    
    def test_validate_python_syntax_all_files(self):
        """Test Python syntax validation for all files."""
        # Create multiple Python files
        (self.repo_root / "file1.py").write_text("x = 1\n")
        (self.repo_root / "file2.py").write_text("y = 2\n")
        
        result = self.validator.validate_python_syntax()
        
        self.assertTrue(result.success)
        self.assertIn("Validated", result.message)
    
    @patch('subprocess.run')
    def test_validate_typescript_syntax_success(self, mock_run):
        """Test TypeScript syntax validation success."""
        # Mock successful tsc execution
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        
        result = self.validator.validate_typescript_syntax()
        
        self.assertTrue(result.success)
        self.assertIn("passed", result.message.lower())
    
    @patch('subprocess.run')
    def test_validate_typescript_syntax_errors(self, mock_run):
        """Test TypeScript syntax validation with errors."""
        # Mock tsc with errors
        mock_run.side_effect = [
            Mock(returncode=0, stdout="", stderr=""),  # tsc --version
            Mock(returncode=1, stdout="error TS2304: Cannot find name 'foo'.\n", stderr="")
        ]
        
        result = self.validator.validate_typescript_syntax()
        
        self.assertFalse(result.success)
        self.assertGreater(len(result.errors), 0)
    
    @patch('subprocess.run')
    def test_validate_typescript_syntax_no_compiler(self, mock_run):
        """Test TypeScript syntax validation when compiler not available."""
        # Mock tsc not found
        mock_run.side_effect = FileNotFoundError()
        
        result = self.validator.validate_typescript_syntax()
        
        self.assertFalse(result.success)
        self.assertIn("not available", result.message.lower())
    
    @patch('subprocess.run')
    def test_validate_django_success(self, mock_run):
        """Test Django validation success."""
        # Create manage.py
        manage_py = self.validator.backend_root / "manage.py"
        manage_py.write_text("#!/usr/bin/env python\n")
        
        # Mock successful Django check
        mock_run.return_value = Mock(
            returncode=0,
            stdout="System check identified no issues (0 silenced).\n",
            stderr=""
        )
        
        result = self.validator.validate_django()
        
        self.assertTrue(result.success)
        self.assertIn("passed", result.message.lower())
    
    @patch('subprocess.run')
    def test_validate_django_errors(self, mock_run):
        """Test Django validation with errors."""
        # Create manage.py
        manage_py = self.validator.backend_root / "manage.py"
        manage_py.write_text("#!/usr/bin/env python\n")
        
        # Mock Django check with errors
        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="ERROR: INSTALLED_APPS contains 'nonexistent.app'\n"
        )
        
        result = self.validator.validate_django()
        
        self.assertFalse(result.success)
        self.assertGreater(len(result.errors), 0)
    
    def test_validate_django_no_manage_py(self):
        """Test Django validation when manage.py doesn't exist."""
        result = self.validator.validate_django()
        
        self.assertFalse(result.success)
        self.assertIn("not found", result.message.lower())
    
    @patch('subprocess.run')
    def test_validate_frontend_build_success(self, mock_run):
        """Test frontend build validation success."""
        # Create package.json
        package_json = self.validator.frontend_root / "package.json"
        package_json.write_text('{"name": "test"}')
        
        # Mock successful build
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Build completed successfully\n",
            stderr=""
        )
        
        result = self.validator.validate_frontend_build()
        
        self.assertTrue(result.success)
        self.assertIn("success", result.message.lower())
    
    @patch('subprocess.run')
    def test_validate_frontend_build_errors(self, mock_run):
        """Test frontend build validation with errors."""
        # Create package.json
        package_json = self.validator.frontend_root / "package.json"
        package_json.write_text('{"name": "test"}')
        
        # Mock build with errors
        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="Error: Build failed\n"
        )
        
        result = self.validator.validate_frontend_build()
        
        self.assertFalse(result.success)
        self.assertGreater(len(result.errors), 0)
    
    def test_validate_frontend_build_no_package_json(self):
        """Test frontend build validation when package.json doesn't exist."""
        result = self.validator.validate_frontend_build()
        
        self.assertFalse(result.success)
        self.assertIn("not found", result.message.lower())
    
    @patch('subprocess.run')
    def test_validate_docker_build_success(self, mock_run):
        """Test Docker build validation success."""
        # Create docker-compose.yml
        docker_compose = self.repo_root / "docker-compose.yml"
        docker_compose.write_text("version: '3'\nservices:\n  test:\n    image: test\n")
        
        # Mock successful Docker commands
        mock_run.side_effect = [
            Mock(returncode=0, stdout="Docker version 20.10.0\n", stderr=""),  # docker --version
            Mock(returncode=0, stdout="Building test\n", stderr="")  # docker-compose build
        ]
        
        result = self.validator.validate_docker_build()
        
        self.assertTrue(result.success)
        self.assertIn("success", result.message.lower())
    
    @patch('subprocess.run')
    def test_validate_docker_build_errors(self, mock_run):
        """Test Docker build validation with errors."""
        # Create docker-compose.yml
        docker_compose = self.repo_root / "docker-compose.yml"
        docker_compose.write_text("version: '3'\nservices:\n  test:\n    image: test\n")
        
        # Mock Docker commands with errors
        mock_run.side_effect = [
            Mock(returncode=0, stdout="Docker version 20.10.0\n", stderr=""),
            Mock(returncode=1, stdout="", stderr="Error: Build failed\n")
        ]
        
        result = self.validator.validate_docker_build()
        
        self.assertFalse(result.success)
        self.assertGreater(len(result.errors), 0)
    
    @patch('subprocess.run')
    def test_validate_docker_build_no_docker(self, mock_run):
        """Test Docker build validation when Docker not available."""
        # Create docker-compose.yml
        docker_compose = self.repo_root / "docker-compose.yml"
        docker_compose.write_text("version: '3'\nservices:\n  test:\n    image: test\n")
        
        # Mock Docker not found
        mock_run.side_effect = FileNotFoundError()
        
        result = self.validator.validate_docker_build()
        
        self.assertFalse(result.success)
        self.assertIn("not available", result.message.lower())
    
    def test_validate_docker_build_no_compose_file(self):
        """Test Docker build validation when docker-compose.yml doesn't exist."""
        result = self.validator.validate_docker_build()
        
        self.assertFalse(result.success)
        self.assertIn("not found", result.message.lower())
    
    @patch('subprocess.run')
    def test_validate_test_discovery_success(self, mock_run):
        """Test test discovery validation success."""
        # Mock successful pytest collection
        mock_run.return_value = Mock(
            returncode=0,
            stdout="test_example.py::test_function\n1 test collected\n",
            stderr=""
        )
        
        result = self.validator.validate_test_discovery()
        
        self.assertTrue(result.success)
        self.assertIn("successful", result.message.lower())
    
    @patch('subprocess.run')
    def test_validate_test_discovery_errors(self, mock_run):
        """Test test discovery validation with errors."""
        # Mock pytest with errors
        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="ERROR: Import error\n"
        )
        
        result = self.validator.validate_test_discovery()
        
        self.assertFalse(result.success)
        self.assertGreater(len(result.errors), 0)
    
    @patch('subprocess.run')
    def test_validate_test_discovery_no_tests(self, mock_run):
        """Test test discovery validation when no tests found."""
        # Mock pytest with no tests
        mock_run.return_value = Mock(
            returncode=5,  # pytest exit code for no tests collected
            stdout="no tests collected\n",
            stderr=""
        )
        
        result = self.validator.validate_test_discovery()
        
        self.assertTrue(result.success)  # No tests is not an error
        self.assertGreater(len(result.warnings), 0)
    
    @patch.object(ValidationSuite, 'validate_python_syntax')
    @patch.object(ValidationSuite, 'validate_typescript_syntax')
    @patch.object(ValidationSuite, 'validate_imports')
    @patch.object(ValidationSuite, 'validate_django')
    @patch.object(ValidationSuite, 'validate_frontend_build')
    @patch.object(ValidationSuite, 'validate_docker_build')
    @patch.object(ValidationSuite, 'validate_test_discovery')
    def test_run_all_success(self, mock_test_disc, mock_docker, mock_frontend,
                            mock_django, mock_imports, mock_ts, mock_py):
        """Test run_all with all checks passing."""
        # Mock all checks to pass
        success_result = ValidationResult(
            success=True,
            message="Check passed",
            errors=[],
            warnings=[]
        )
        
        mock_py.return_value = success_result
        mock_ts.return_value = success_result
        mock_imports.return_value = success_result
        mock_django.return_value = success_result
        mock_frontend.return_value = success_result
        mock_docker.return_value = success_result
        mock_test_disc.return_value = success_result
        
        report = self.validator.run_all()
        
        self.assertTrue(report.overall_success)
        self.assertEqual(len(report.results), 7)
        self.assertIn("passed", report.summary.lower())
    
    @patch.object(ValidationSuite, 'validate_python_syntax')
    @patch.object(ValidationSuite, 'validate_typescript_syntax')
    @patch.object(ValidationSuite, 'validate_imports')
    @patch.object(ValidationSuite, 'validate_django')
    @patch.object(ValidationSuite, 'validate_frontend_build')
    @patch.object(ValidationSuite, 'validate_docker_build')
    @patch.object(ValidationSuite, 'validate_test_discovery')
    def test_run_all_with_failures(self, mock_test_disc, mock_docker, mock_frontend,
                                   mock_django, mock_imports, mock_ts, mock_py):
        """Test run_all with some checks failing."""
        # Mock some checks to fail
        success_result = ValidationResult(
            success=True,
            message="Check passed",
            errors=[],
            warnings=[]
        )
        
        failure_result = ValidationResult(
            success=False,
            message="Check failed",
            errors=["Error 1", "Error 2"],
            warnings=[]
        )
        
        mock_py.return_value = success_result
        mock_ts.return_value = failure_result  # TypeScript fails
        mock_imports.return_value = success_result
        mock_django.return_value = failure_result  # Django fails
        mock_frontend.return_value = success_result
        mock_docker.return_value = success_result
        mock_test_disc.return_value = success_result
        
        report = self.validator.run_all()
        
        self.assertFalse(report.overall_success)
        self.assertEqual(len(report.results), 7)
        self.assertIn("failed", report.summary.lower())


class TestValidationResult(unittest.TestCase):
    """Test cases for ValidationResult dataclass."""
    
    def test_validation_result_creation(self):
        """Test ValidationResult creation."""
        result = ValidationResult(
            success=True,
            message="Test passed",
            errors=[],
            warnings=["Warning 1"]
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.message, "Test passed")
        self.assertEqual(len(result.errors), 0)
        self.assertEqual(len(result.warnings), 1)


class TestValidationReport(unittest.TestCase):
    """Test cases for ValidationReport dataclass."""
    
    def test_validation_report_creation(self):
        """Test ValidationReport creation."""
        results = {
            'check1': ValidationResult(True, "Pass", [], []),
            'check2': ValidationResult(False, "Fail", ["Error"], [])
        }
        
        report = ValidationReport(
            overall_success=False,
            results=results,
            summary="1/2 checks passed"
        )
        
        self.assertFalse(report.overall_success)
        self.assertEqual(len(report.results), 2)
        self.assertIn("1/2", report.summary)


if __name__ == '__main__':
    unittest.main()
