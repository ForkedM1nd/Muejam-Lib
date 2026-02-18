"""
Unit tests for cleanup module.

Tests cover:
- Finding cache directories (__pycache__, .pytest_cache, .hypothesis)
- Finding compiled Python files (.pyc, .pyo)
- Finding log files (.log)
- Safely removing files and directories
- Preserving .gitignore files
- Preserving directories with .gitkeep files
"""

import tempfile
from pathlib import Path
import pytest

from scripts.reorganize.cleanup import (
    find_cache_directories,
    find_compiled_files,
    find_log_files,
    remove_paths
)


class TestFindCacheDirectories:
    """Test cases for find_cache_directories function."""
    
    def test_find_pycache_directories(self, tmp_path):
        """Test finding __pycache__ directories."""
        # Create __pycache__ directories
        (tmp_path / "module1" / "__pycache__").mkdir(parents=True)
        (tmp_path / "module2" / "submodule" / "__pycache__").mkdir(parents=True)
        
        cache_dirs = find_cache_directories(tmp_path)
        
        assert len(cache_dirs) == 2
        cache_names = {d.name for d in cache_dirs}
        assert cache_names == {"__pycache__"}
    
    def test_find_pytest_cache_directories(self, tmp_path):
        """Test finding .pytest_cache directories."""
        # Create .pytest_cache directories
        (tmp_path / ".pytest_cache").mkdir()
        (tmp_path / "tests" / ".pytest_cache").mkdir(parents=True)
        
        cache_dirs = find_cache_directories(tmp_path)
        
        assert len(cache_dirs) == 2
        cache_names = {d.name for d in cache_dirs}
        assert cache_names == {".pytest_cache"}
    
    def test_find_hypothesis_directories(self, tmp_path):
        """Test finding .hypothesis directories."""
        # Create .hypothesis directories
        (tmp_path / ".hypothesis").mkdir()
        (tmp_path / "tests" / ".hypothesis").mkdir(parents=True)
        
        cache_dirs = find_cache_directories(tmp_path)
        
        assert len(cache_dirs) == 2
        cache_names = {d.name for d in cache_dirs}
        assert cache_names == {".hypothesis"}
    
    def test_find_all_cache_types(self, tmp_path):
        """Test finding all types of cache directories."""
        # Create various cache directories
        (tmp_path / "module" / "__pycache__").mkdir(parents=True)
        (tmp_path / ".pytest_cache").mkdir()
        (tmp_path / "tests" / ".hypothesis").mkdir(parents=True)
        
        cache_dirs = find_cache_directories(tmp_path)
        
        assert len(cache_dirs) == 3
        cache_names = {d.name for d in cache_dirs}
        assert cache_names == {"__pycache__", ".pytest_cache", ".hypothesis"}
    
    def test_find_cache_directories_empty_project(self, tmp_path):
        """Test finding cache directories in empty project."""
        cache_dirs = find_cache_directories(tmp_path)
        
        assert len(cache_dirs) == 0
    
    def test_find_cache_directories_nested(self, tmp_path):
        """Test finding cache directories in deeply nested structure."""
        # Create deeply nested cache directories
        nested = tmp_path / "level1" / "level2" / "level3" / "__pycache__"
        nested.mkdir(parents=True)
        
        cache_dirs = find_cache_directories(tmp_path)
        
        assert len(cache_dirs) == 1
        assert cache_dirs[0].name == "__pycache__"
    
    def test_find_cache_directories_nonexistent_root(self, tmp_path):
        """Test handling of nonexistent root directory."""
        nonexistent = tmp_path / "nonexistent"
        
        cache_dirs = find_cache_directories(nonexistent)
        
        assert len(cache_dirs) == 0


class TestFindCompiledFiles:
    """Test cases for find_compiled_files function."""
    
    def test_find_pyc_files(self, tmp_path):
        """Test finding .pyc files."""
        # Create .pyc files
        (tmp_path / "module.pyc").write_bytes(b"compiled")
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "another.pyc").write_bytes(b"compiled")
        
        compiled_files = find_compiled_files(tmp_path)
        
        assert len(compiled_files) == 2
        extensions = {f.suffix for f in compiled_files}
        assert extensions == {".pyc"}
    
    def test_find_pyo_files(self, tmp_path):
        """Test finding .pyo files."""
        # Create .pyo files
        (tmp_path / "module.pyo").write_bytes(b"optimized")
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "another.pyo").write_bytes(b"optimized")
        
        compiled_files = find_compiled_files(tmp_path)
        
        assert len(compiled_files) == 2
        extensions = {f.suffix for f in compiled_files}
        assert extensions == {".pyo"}
    
    def test_find_both_pyc_and_pyo(self, tmp_path):
        """Test finding both .pyc and .pyo files."""
        # Create both types
        (tmp_path / "module.pyc").write_bytes(b"compiled")
        (tmp_path / "module.pyo").write_bytes(b"optimized")
        
        compiled_files = find_compiled_files(tmp_path)
        
        assert len(compiled_files) == 2
        extensions = {f.suffix for f in compiled_files}
        assert extensions == {".pyc", ".pyo"}
    
    def test_find_compiled_files_in_pycache(self, tmp_path):
        """Test finding compiled files inside __pycache__ directories."""
        # Create __pycache__ with compiled files
        pycache = tmp_path / "module" / "__pycache__"
        pycache.mkdir(parents=True)
        (pycache / "module.cpython-39.pyc").write_bytes(b"compiled")
        (pycache / "module.cpython-310.pyc").write_bytes(b"compiled")
        
        compiled_files = find_compiled_files(tmp_path)
        
        assert len(compiled_files) == 2
    
    def test_find_compiled_files_empty_project(self, tmp_path):
        """Test finding compiled files in empty project."""
        compiled_files = find_compiled_files(tmp_path)
        
        assert len(compiled_files) == 0
    
    def test_find_compiled_files_ignores_py_files(self, tmp_path):
        """Test that .py source files are not included."""
        # Create .py files
        (tmp_path / "module.py").write_text("# source")
        (tmp_path / "test.py").write_text("# test")
        
        compiled_files = find_compiled_files(tmp_path)
        
        assert len(compiled_files) == 0


class TestFindLogFiles:
    """Test cases for find_log_files function."""
    
    def test_find_log_files(self, tmp_path):
        """Test finding .log files."""
        # Create log files
        (tmp_path / "app.log").write_text("log content")
        (tmp_path / "logs").mkdir()
        (tmp_path / "logs" / "error.log").write_text("error log")
        
        log_files = find_log_files(tmp_path)
        
        assert len(log_files) == 2
        extensions = {f.suffix for f in log_files}
        assert extensions == {".log"}
    
    def test_find_log_files_nested(self, tmp_path):
        """Test finding log files in nested directories."""
        # Create nested log files
        nested = tmp_path / "level1" / "level2" / "level3"
        nested.mkdir(parents=True)
        (nested / "debug.log").write_text("debug log")
        
        log_files = find_log_files(tmp_path)
        
        assert len(log_files) == 1
        assert log_files[0].name == "debug.log"
    
    def test_find_log_files_empty_project(self, tmp_path):
        """Test finding log files in empty project."""
        log_files = find_log_files(tmp_path)
        
        assert len(log_files) == 0
    
    def test_find_log_files_ignores_other_extensions(self, tmp_path):
        """Test that non-.log files are not included."""
        # Create various files
        (tmp_path / "readme.txt").write_text("readme")
        (tmp_path / "config.json").write_text("{}")
        (tmp_path / "data.csv").write_text("data")
        
        log_files = find_log_files(tmp_path)
        
        assert len(log_files) == 0


class TestRemovePaths:
    """Test cases for remove_paths function."""
    
    def test_remove_single_file(self, tmp_path):
        """Test removing a single file."""
        file = tmp_path / "file.txt"
        file.write_text("content")
        
        remove_paths([file])
        
        assert not file.exists()
    
    def test_remove_multiple_files(self, tmp_path):
        """Test removing multiple files."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("content1")
        file2.write_text("content2")
        
        remove_paths([file1, file2])
        
        assert not file1.exists()
        assert not file2.exists()
    
    def test_remove_directory(self, tmp_path):
        """Test removing a directory."""
        directory = tmp_path / "dir"
        directory.mkdir()
        (directory / "file.txt").write_text("content")
        
        remove_paths([directory])
        
        assert not directory.exists()
    
    def test_remove_cache_directory(self, tmp_path):
        """Test removing __pycache__ directory."""
        pycache = tmp_path / "__pycache__"
        pycache.mkdir()
        (pycache / "module.pyc").write_bytes(b"compiled")
        
        remove_paths([pycache])
        
        assert not pycache.exists()
    
    def test_preserve_gitignore(self, tmp_path):
        """Test that .gitignore files are preserved."""
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("*.log\n*.pyc")
        
        remove_paths([gitignore])
        
        # .gitignore should still exist (Requirement 7.5)
        assert gitignore.exists()
    
    def test_preserve_directory_with_gitkeep(self, tmp_path):
        """Test that directories with .gitkeep files are preserved."""
        directory = tmp_path / "logs"
        directory.mkdir()
        (directory / ".gitkeep").write_text("")
        
        remove_paths([directory])
        
        # Directory should still exist (Requirement 5.5)
        assert directory.exists()
        assert (directory / ".gitkeep").exists()
    
    def test_remove_empty_list(self, tmp_path):
        """Test removing empty list of paths."""
        # Should not raise error
        remove_paths([])
    
    def test_remove_nonexistent_path(self, tmp_path):
        """Test removing nonexistent path doesn't raise error."""
        nonexistent = tmp_path / "nonexistent.txt"
        
        # Should not raise error
        remove_paths([nonexistent])
    
    def test_remove_mixed_paths(self, tmp_path):
        """Test removing mix of files and directories."""
        file = tmp_path / "file.txt"
        file.write_text("content")
        
        directory = tmp_path / "dir"
        directory.mkdir()
        (directory / "nested.txt").write_text("nested")
        
        remove_paths([file, directory])
        
        assert not file.exists()
        assert not directory.exists()
    
    def test_remove_compiled_files(self, tmp_path):
        """Test removing compiled Python files."""
        pyc_file = tmp_path / "module.pyc"
        pyo_file = tmp_path / "module.pyo"
        pyc_file.write_bytes(b"compiled")
        pyo_file.write_bytes(b"optimized")
        
        remove_paths([pyc_file, pyo_file])
        
        assert not pyc_file.exists()
        assert not pyo_file.exists()
    
    def test_remove_log_files(self, tmp_path):
        """Test removing log files."""
        log_file = tmp_path / "app.log"
        log_file.write_text("log content")
        
        remove_paths([log_file])
        
        assert not log_file.exists()
    
    def test_remove_continues_on_error(self, tmp_path):
        """Test that removal continues even if one path fails."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        nonexistent = tmp_path / "nonexistent.txt"
        
        file1.write_text("content1")
        file2.write_text("content2")
        
        # Should not raise error, should remove existing files
        remove_paths([file1, nonexistent, file2])
        
        assert not file1.exists()
        assert not file2.exists()


class TestIntegration:
    """Integration tests for cleanup workflow."""
    
    def test_complete_cleanup_workflow(self, tmp_path):
        """Test complete cleanup workflow: find and remove all artifacts."""
        # Create project structure with cache, compiled files, and logs
        (tmp_path / "module" / "__pycache__").mkdir(parents=True)
        (tmp_path / "module" / "__pycache__" / "module.pyc").write_bytes(b"compiled")
        (tmp_path / ".pytest_cache").mkdir()
        (tmp_path / ".hypothesis").mkdir()
        (tmp_path / "app.log").write_text("log")
        (tmp_path / "module.pyo").write_bytes(b"optimized")
        
        # Also create files that should be preserved
        (tmp_path / ".gitignore").write_text("*.log")
        (tmp_path / "logs").mkdir()
        (tmp_path / "logs" / ".gitkeep").write_text("")
        (tmp_path / "module" / "source.py").write_text("# source")
        
        # Find all artifacts
        cache_dirs = find_cache_directories(tmp_path)
        compiled_files = find_compiled_files(tmp_path)
        log_files = find_log_files(tmp_path)
        
        # Remove all artifacts
        all_paths = cache_dirs + compiled_files + log_files
        remove_paths(all_paths)
        
        # Verify artifacts are removed
        assert not (tmp_path / "module" / "__pycache__").exists()
        assert not (tmp_path / ".pytest_cache").exists()
        assert not (tmp_path / ".hypothesis").exists()
        assert not (tmp_path / "app.log").exists()
        assert not (tmp_path / "module.pyo").exists()
        
        # Verify preserved files still exist
        assert (tmp_path / ".gitignore").exists()
        assert (tmp_path / "logs").exists()
        assert (tmp_path / "logs" / ".gitkeep").exists()
        assert (tmp_path / "module" / "source.py").exists()
    
    def test_cleanup_preserves_log_directory_structure(self, tmp_path):
        """Test that log directory structure is preserved after cleanup."""
        # Create log directory with .gitkeep
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()
        (logs_dir / ".gitkeep").write_text("")
        (logs_dir / "app.log").write_text("log content")
        
        # Find and remove log files
        log_files = find_log_files(tmp_path)
        remove_paths(log_files)
        
        # Log file should be removed, but directory should remain (Requirement 8.3)
        assert not (logs_dir / "app.log").exists()
        assert logs_dir.exists()
        assert (logs_dir / ".gitkeep").exists()
