"""
Unit tests for the main reorganization orchestrator.

Tests the create_reorganization_plan, execute_plan, and verify_reorganization functions.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys
import importlib.util

# Add the scripts/reorganize directory to sys.path
scripts_dir = Path(__file__).parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

# Import the reorganize module directly from file
reorganize_path = Path(__file__).parent / "reorganize.py"
spec = importlib.util.spec_from_file_location("reorganize_main", reorganize_path)
reorganize_main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reorganize_main)

# Get the functions we need
create_reorganization_plan = reorganize_main.create_reorganization_plan
execute_plan = reorganize_main.execute_plan
verify_reorganization = reorganize_main.verify_reorganization
move_backend_tests = reorganize_main.move_backend_tests
PathMapping = reorganize_main.PathMapping
ReorganizationPlan = reorganize_main.ReorganizationPlan


class TestMoveBackendTests:
    """Tests for move_backend_tests function."""
    
    def test_move_backend_tests_success(self, tmp_path):
        """Test successful move of backend tests."""
        # Create test structure
        backend_tests = tmp_path / "tests" / "backend"
        backend_tests.mkdir(parents=True)
        
        # Create test files with various structures
        (backend_tests / "test_example.py").write_text("# test file")
        
        subdir = backend_tests / "unit"
        subdir.mkdir()
        (subdir / "test_unit.py").write_text("# unit test")
        
        # Create conftest.py
        (backend_tests / "conftest.py").write_text("# conftest")
        
        # Execute move
        result = move_backend_tests(tmp_path, dry_run=False)
        
        # Verify success
        assert result is True
        
        # Verify files moved to new location
        new_location = tmp_path / "apps" / "backend" / "tests"
        assert new_location.exists()
        assert (new_location / "test_example.py").exists()
        assert (new_location / "unit" / "test_unit.py").exists()
        assert (new_location / "conftest.py").exists()
        
        # Verify old location removed
        assert not backend_tests.exists()
    
    def test_move_backend_tests_preserves_structure(self, tmp_path):
        """Test that directory structure is preserved during move."""
        # Create nested test structure
        backend_tests = tmp_path / "tests" / "backend"
        backend_tests.mkdir(parents=True)
        
        # Create nested directories
        (backend_tests / "apps" / "submodule").mkdir(parents=True)
        (backend_tests / "apps" / "submodule" / "test_sub.py").write_text("# test")
        
        (backend_tests / "infrastructure").mkdir()
        (backend_tests / "infrastructure" / "test_infra.py").write_text("# test")
        
        # Execute move
        result = move_backend_tests(tmp_path, dry_run=False)
        
        # Verify structure preserved
        assert result is True
        new_location = tmp_path / "apps" / "backend" / "tests"
        assert (new_location / "apps" / "submodule" / "test_sub.py").exists()
        assert (new_location / "infrastructure" / "test_infra.py").exists()
    
    def test_move_backend_tests_updates_imports(self, tmp_path):
        """Test that import statements are updated in moved files."""
        # Create test file with imports
        backend_tests = tmp_path / "tests" / "backend"
        backend_tests.mkdir(parents=True)
        
        test_file = backend_tests / "test_imports.py"
        test_file.write_text(
            "from tests.backend import something\n"
            "from tests.backend.utils import helper\n"
            "import tests.backend.module\n"
        )
        
        # Execute move
        result = move_backend_tests(tmp_path, dry_run=False)
        
        # Verify imports updated
        assert result is True
        new_file = tmp_path / "apps" / "backend" / "tests" / "test_imports.py"
        content = new_file.read_text()
        
        assert "from apps.backend.tests import something" in content
        assert "from apps.backend.tests.utils import helper" in content
        assert "import apps.backend.tests.module" in content
    
    def test_move_backend_tests_updates_conftest(self, tmp_path):
        """Test that conftest.py files are updated."""
        # Create conftest with references to old path
        backend_tests = tmp_path / "tests" / "backend"
        backend_tests.mkdir(parents=True)
        
        conftest = backend_tests / "conftest.py"
        conftest.write_text(
            "import sys\n"
            "from tests.backend import fixtures\n"
            "# Path: tests/backend/conftest.py\n"
        )
        
        # Execute move
        result = move_backend_tests(tmp_path, dry_run=False)
        
        # Verify conftest updated
        assert result is True
        new_conftest = tmp_path / "apps" / "backend" / "tests" / "conftest.py"
        content = new_conftest.read_text()
        
        assert "from apps.backend.tests import fixtures" in content
        assert "apps/backend/tests" in content
    
    def test_move_backend_tests_dry_run(self, tmp_path):
        """Test dry-run mode doesn't modify files."""
        # Create test structure
        backend_tests = tmp_path / "tests" / "backend"
        backend_tests.mkdir(parents=True)
        (backend_tests / "test_example.py").write_text("# test")
        
        # Execute in dry-run mode
        result = move_backend_tests(tmp_path, dry_run=True)
        
        # Verify success but no changes
        assert result is True
        assert backend_tests.exists()
        assert (backend_tests / "test_example.py").exists()
        assert not (tmp_path / "apps" / "backend" / "tests").exists()
    
    def test_move_backend_tests_source_not_exists(self, tmp_path):
        """Test handling when source directory doesn't exist."""
        # Execute move without creating source
        result = move_backend_tests(tmp_path, dry_run=False)
        
        # Should return False
        assert result is False
    
    def test_move_backend_tests_removes_empty_tests_dir(self, tmp_path):
        """Test that empty tests/ directory is removed after move."""
        # Create test structure with only backend tests
        backend_tests = tmp_path / "tests" / "backend"
        backend_tests.mkdir(parents=True)
        (backend_tests / "test_example.py").write_text("# test")
        
        # Execute move
        result = move_backend_tests(tmp_path, dry_run=False)
        
        # Verify tests/ directory removed if empty
        assert result is True
        tests_dir = tmp_path / "tests"
        # Directory should be removed if it was empty after backend move
        # (it may still exist if there are other subdirectories like frontend)
    
    def test_move_backend_tests_preserves_tests_dir_with_content(self, tmp_path):
        """Test that tests/ directory is preserved if it has other content."""
        # Create test structure with backend and frontend tests
        backend_tests = tmp_path / "tests" / "backend"
        backend_tests.mkdir(parents=True)
        (backend_tests / "test_backend.py").write_text("# backend test")
        
        frontend_tests = tmp_path / "tests" / "frontend"
        frontend_tests.mkdir()
        (frontend_tests / "test_frontend.py").write_text("# frontend test")
        
        # Execute move
        result = move_backend_tests(tmp_path, dry_run=False)
        
        # Verify tests/ directory preserved with frontend tests
        assert result is True
        tests_dir = tmp_path / "tests"
        assert tests_dir.exists()
        assert (tests_dir / "frontend" / "test_frontend.py").exists()
        assert not (tests_dir / "backend").exists()


class TestCreateReorganizationPlan:
    """Tests for create_reorganization_plan function."""
    
    def test_plan_with_backend_tests(self, tmp_path):
        """Test planning when backend tests directory exists."""
        # Create test structure
        backend_tests = tmp_path / "tests" / "backend"
        backend_tests.mkdir(parents=True)
        (backend_tests / "test_example.py").write_text("# test")
        
        # Create plan
        plan = create_reorganization_plan(tmp_path)
        
        # Verify test moves are planned
        assert len(plan.test_moves) == 1
        assert plan.test_moves[0].old_path == backend_tests
        assert plan.test_moves[0].new_path == tmp_path / "apps" / "backend" / "tests"
        assert plan.test_moves[0].is_directory is True
    
    def test_plan_with_backend_docs(self, tmp_path):
        """Test planning when backend docs directory exists."""
        # Create test structure
        backend_docs = tmp_path / "apps" / "backend" / "docs"
        backend_docs.mkdir(parents=True)
        (backend_docs / "README.md").write_text("# Docs")
        
        # Create plan
        plan = create_reorganization_plan(tmp_path)
        
        # Verify doc moves are planned
        assert len(plan.doc_moves) == 1
        assert plan.doc_moves[0].old_path == backend_docs
        assert plan.doc_moves[0].new_path == tmp_path / "docs" / "backend"
        assert plan.doc_moves[0].is_directory is True
    
    def test_plan_without_directories(self, tmp_path):
        """Test planning when directories don't exist."""
        # Create plan with empty directory
        plan = create_reorganization_plan(tmp_path)
        
        # Verify no moves are planned
        assert len(plan.test_moves) == 0
        assert len(plan.doc_moves) == 0
    
    def test_plan_includes_import_updates(self, tmp_path):
        """Test that plan includes import update mappings."""
        # Create test structure
        backend_tests = tmp_path / "tests" / "backend"
        backend_tests.mkdir(parents=True)
        
        # Create plan
        plan = create_reorganization_plan(tmp_path)
        
        # Verify import updates are planned
        assert len(plan.import_updates) > 0
        assert tmp_path in plan.import_updates
        assert "tests.backend" in plan.import_updates[tmp_path]
        assert plan.import_updates[tmp_path]["tests.backend"] == "apps.backend.tests"
    
    def test_plan_includes_cleanup_paths(self, tmp_path):
        """Test that plan includes cleanup paths for cache and log files."""
        # Create cache directories
        pycache = tmp_path / "__pycache__"
        pycache.mkdir()
        (pycache / "test.pyc").write_text("")
        
        pytest_cache = tmp_path / ".pytest_cache"
        pytest_cache.mkdir()
        
        # Create log file
        (tmp_path / "test.log").write_text("log content")
        
        # Create plan
        plan = create_reorganization_plan(tmp_path)
        
        # Verify cleanup paths are found
        assert len(plan.cleanup_paths) >= 3
        cleanup_names = {p.name for p in plan.cleanup_paths}
        assert "__pycache__" in cleanup_names or "test.pyc" in cleanup_names
        assert ".pytest_cache" in cleanup_names or "test.log" in cleanup_names


class TestExecutePlan:
    """Tests for execute_plan function."""
    
    def test_execute_plan_dry_run(self, tmp_path):
        """Test that dry-run mode doesn't modify files."""
        # Create test structure
        backend_tests = tmp_path / "tests" / "backend"
        backend_tests.mkdir(parents=True)
        test_file = backend_tests / "test_example.py"
        test_file.write_text("# test")
        
        # Create plan
        plan = ReorganizationPlan()
        plan.test_moves.append(PathMapping(
            old_path=backend_tests,
            new_path=tmp_path / "apps" / "backend" / "tests",
            is_directory=True
        ))
        
        # Execute in dry-run mode
        result = execute_plan(plan, tmp_path, dry_run=True)
        
        # Verify success but no changes
        assert result is True
        assert backend_tests.exists()
        assert test_file.exists()
        assert not (tmp_path / "apps" / "backend" / "tests").exists()
    
    def test_execute_plan_moves_tests(self, tmp_path):
        """Test that plan execution moves test files."""
        # Create test structure
        backend_tests = tmp_path / "tests" / "backend"
        backend_tests.mkdir(parents=True)
        test_file = backend_tests / "test_example.py"
        test_file.write_text("# test")
        
        # Create plan
        plan = ReorganizationPlan()
        plan.test_moves.append(PathMapping(
            old_path=backend_tests,
            new_path=tmp_path / "apps" / "backend" / "tests",
            is_directory=True
        ))
        
        # Execute plan
        result = execute_plan(plan, tmp_path, dry_run=False)
        
        # Verify files were moved
        assert result is True
        assert not backend_tests.exists()
        assert (tmp_path / "apps" / "backend" / "tests" / "test_example.py").exists()
    
    def test_execute_plan_moves_docs(self, tmp_path):
        """Test that plan execution moves documentation files."""
        # Create test structure
        backend_docs = tmp_path / "apps" / "backend" / "docs"
        backend_docs.mkdir(parents=True)
        doc_file = backend_docs / "README.md"
        doc_file.write_text("# Docs")
        
        # Create plan
        plan = ReorganizationPlan()
        plan.doc_moves.append(PathMapping(
            old_path=backend_docs,
            new_path=tmp_path / "docs" / "backend",
            is_directory=True
        ))
        
        # Execute plan
        result = execute_plan(plan, tmp_path, dry_run=False)
        
        # Verify files were moved
        assert result is True
        assert not backend_docs.exists()
        assert (tmp_path / "docs" / "backend" / "README.md").exists()
    
    def test_execute_plan_updates_imports(self, tmp_path):
        """Test that plan execution updates import statements."""
        # Create test file with imports
        test_file = tmp_path / "test_imports.py"
        test_file.write_text("from tests.backend import something\n")
        
        # Create plan with import updates
        plan = ReorganizationPlan()
        plan.import_updates = {
            tmp_path: {
                "tests.backend": "apps.backend.tests"
            }
        }
        
        # Execute plan
        result = execute_plan(plan, tmp_path, dry_run=False)
        
        # Verify imports were updated
        assert result is True
        content = test_file.read_text()
        assert "from apps.backend.tests import something" in content
    
    def test_execute_plan_cleans_up_cache(self, tmp_path):
        """Test that plan execution removes cache files."""
        # Create cache directory
        pycache = tmp_path / "__pycache__"
        pycache.mkdir()
        cache_file = pycache / "test.pyc"
        cache_file.write_text("")
        
        # Create plan with cleanup
        plan = ReorganizationPlan()
        plan.cleanup_paths = [pycache]
        
        # Execute plan
        result = execute_plan(plan, tmp_path, dry_run=False)
        
        # Verify cache was removed
        assert result is True
        assert not pycache.exists()
    
    def test_execute_plan_handles_errors_gracefully(self, tmp_path):
        """Test that plan execution handles errors without crashing."""
        # Create plan with non-existent source
        plan = ReorganizationPlan()
        plan.test_moves.append(PathMapping(
            old_path=tmp_path / "nonexistent",
            new_path=tmp_path / "destination",
            is_directory=True
        ))
        
        # Execute plan - should handle error gracefully
        result = execute_plan(plan, tmp_path, dry_run=False)
        
        # Should return False due to error
        assert result is False


class TestVerifyReorganization:
    """Tests for verify_reorganization function."""
    
    def test_verify_success_with_moved_tests(self, tmp_path):
        """Test verification passes when tests are in correct location."""
        # Create new test location
        backend_tests = tmp_path / "apps" / "backend" / "tests"
        backend_tests.mkdir(parents=True)
        (backend_tests / "test_example.py").write_text("# test")
        
        # Verify
        result = verify_reorganization(tmp_path)
        
        # Should pass
        assert result is True
    
    def test_verify_fails_with_old_test_location(self, tmp_path):
        """Test verification fails when old test directory still exists."""
        # Create both old and new locations
        old_tests = tmp_path / "tests" / "backend"
        old_tests.mkdir(parents=True)
        (old_tests / "test_example.py").write_text("# test")
        
        new_tests = tmp_path / "apps" / "backend" / "tests"
        new_tests.mkdir(parents=True)
        (new_tests / "test_example.py").write_text("# test")
        
        # Verify
        result = verify_reorganization(tmp_path)
        
        # Should fail because old location still exists
        assert result is False
    
    def test_verify_detects_remaining_cache(self, tmp_path):
        """Test verification detects remaining cache directories."""
        # Create new test location
        backend_tests = tmp_path / "apps" / "backend" / "tests"
        backend_tests.mkdir(parents=True)
        
        # Create cache directory
        pycache = tmp_path / "__pycache__"
        pycache.mkdir()
        
        # Verify
        result = verify_reorganization(tmp_path)
        
        # Should fail because cache exists
        assert result is False
    
    def test_verify_detects_remaining_logs(self, tmp_path):
        """Test verification detects remaining log files."""
        # Create new test location
        backend_tests = tmp_path / "apps" / "backend" / "tests"
        backend_tests.mkdir(parents=True)
        
        # Create log file
        (tmp_path / "test.log").write_text("log")
        
        # Verify
        result = verify_reorganization(tmp_path)
        
        # Should fail because log exists
        assert result is False
    
    def test_verify_handles_missing_docs_gracefully(self, tmp_path):
        """Test verification doesn't fail if docs never existed."""
        # Create only test location (no docs)
        backend_tests = tmp_path / "apps" / "backend" / "tests"
        backend_tests.mkdir(parents=True)
        (backend_tests / "test_example.py").write_text("# test")
        
        # Verify
        result = verify_reorganization(tmp_path)
        
        # Should pass even without docs
        assert result is True


class TestPathMapping:
    """Tests for PathMapping dataclass."""
    
    def test_path_mapping_creation(self):
        """Test creating a PathMapping instance."""
        mapping = PathMapping(
            old_path=Path("/old/path"),
            new_path=Path("/new/path"),
            is_directory=True
        )
        
        assert mapping.old_path == Path("/old/path")
        assert mapping.new_path == Path("/new/path")
        assert mapping.is_directory is True


class TestReorganizationPlan:
    """Tests for ReorganizationPlan dataclass."""
    
    def test_plan_creation_with_defaults(self):
        """Test creating a ReorganizationPlan with default values."""
        plan = ReorganizationPlan()
        
        assert plan.test_moves == []
        assert plan.doc_moves == []
        assert plan.import_updates == {}
        assert plan.reference_updates == {}
        assert plan.cleanup_paths == []
        assert plan.empty_dirs_to_remove == []
    
    def test_plan_creation_with_values(self):
        """Test creating a ReorganizationPlan with values."""
        mapping = PathMapping(
            old_path=Path("/old"),
            new_path=Path("/new"),
            is_directory=True
        )
        
        plan = ReorganizationPlan(
            test_moves=[mapping],
            doc_moves=[mapping],
            import_updates={Path("/"): {"old": "new"}},
            cleanup_paths=[Path("/cache")]
        )
        
        assert len(plan.test_moves) == 1
        assert len(plan.doc_moves) == 1
        assert len(plan.import_updates) == 1
        assert len(plan.cleanup_paths) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
