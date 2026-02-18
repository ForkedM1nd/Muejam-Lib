"""
Unit tests for reference_updater module.

Tests the functionality of finding and updating file references in documentation
and updating pytest configuration files.
"""

import pytest
from pathlib import Path
import tempfile
import shutil
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from reference_updater import (
    FileReference,
    find_file_references,
    update_reference,
    update_pytest_config,
    _is_file_path,
    _is_relative_path,
    _path_matches,
    _replace_path
)


class TestFileReference:
    """Tests for FileReference class."""
    
    def test_file_reference_creation(self):
        """Test creating a FileReference object."""
        ref = FileReference(
            file=Path("test.md"),
            line_number=5,
            original_text="[link](path/to/file.py)",
            referenced_path="path/to/file.py",
            is_relative=True,
            reference_type="markdown_link"
        )
        
        assert ref.line_number == 5
        assert ref.referenced_path == "path/to/file.py"
        assert ref.is_relative is True
        assert ref.reference_type == "markdown_link"
    
    def test_file_reference_repr(self):
        """Test FileReference string representation."""
        ref = FileReference(
            file=Path("test.md"),
            line_number=5,
            original_text="[link](path/to/file.py)",
            referenced_path="path/to/file.py",
            is_relative=True,
            reference_type="markdown_link"
        )
        
        repr_str = repr(ref)
        assert "test.md" in repr_str
        assert "line=5" in repr_str
        assert "path/to/file.py" in repr_str


class TestIsFilePath:
    """Tests for _is_file_path helper function."""
    
    def test_url_not_file_path(self):
        """Test that URLs are not considered file paths."""
        assert _is_file_path("http://example.com") is False
        assert _is_file_path("https://example.com/path") is False
        assert _is_file_path("ftp://server.com") is False
        assert _is_file_path("mailto:test@example.com") is False
    
    def test_anchor_not_file_path(self):
        """Test that anchors are not considered file paths."""
        assert _is_file_path("#section") is False
        assert _is_file_path("#heading-1") is False
    
    def test_path_with_slash_is_file_path(self):
        """Test that paths with slashes are considered file paths."""
        assert _is_file_path("path/to/file.py") is True
        assert _is_file_path("./relative/path.md") is True
        assert _is_file_path("../parent/file.txt") is True
    
    def test_path_with_extension_is_file_path(self):
        """Test that paths with file extensions are considered file paths."""
        assert _is_file_path("file.py") is True
        assert _is_file_path("config.ini") is True
        assert _is_file_path("data.json") is True


class TestIsRelativePath:
    """Tests for _is_relative_path helper function."""
    
    def test_relative_paths(self):
        """Test that relative paths are identified correctly."""
        assert _is_relative_path("path/to/file.py") is True
        assert _is_relative_path("./file.py") is True
        assert _is_relative_path("../parent/file.py") is True
        assert _is_relative_path("file.py") is True
    
    def test_absolute_unix_paths(self):
        """Test that absolute Unix paths are identified correctly."""
        assert _is_relative_path("/absolute/path/file.py") is False
        assert _is_relative_path("/usr/local/bin") is False
    
    def test_absolute_windows_paths(self):
        """Test that absolute Windows paths are identified correctly."""
        assert _is_relative_path("C:/path/file.py") is False
        assert _is_relative_path("C:\\path\\file.py") is False
        assert _is_relative_path("D:/data/file.txt") is False


class TestFindFileReferences:
    """Tests for find_file_references function."""
    
    def setup_method(self):
        """Create temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)
    
    def test_find_markdown_links(self):
        """Test finding markdown link references."""
        test_file = self.temp_path / "test.md"
        test_file.write_text(
            "# Test\n"
            "[Link to file](path/to/file.py)\n"
            "[Another link](../other/file.md)\n"
        )
        
        refs = find_file_references(test_file)
        
        assert len(refs) == 2
        assert refs[0].referenced_path == "path/to/file.py"
        assert refs[0].reference_type == "markdown_link"
        assert refs[1].referenced_path == "../other/file.md"
    
    def test_find_inline_code_paths(self):
        """Test finding inline code path references."""
        test_file = self.temp_path / "test.md"
        test_file.write_text(
            "# Test\n"
            "See `path/to/file.py` for details.\n"
            "Config in `config/settings.ini`.\n"
        )
        
        refs = find_file_references(test_file)
        
        assert len(refs) == 2
        assert refs[0].referenced_path == "path/to/file.py"
        assert refs[0].reference_type == "inline_path"
        assert refs[1].referenced_path == "config/settings.ini"
    
    def test_ignore_urls(self):
        """Test that URLs are not included in references."""
        test_file = self.temp_path / "test.md"
        test_file.write_text(
            "# Test\n"
            "[External link](https://example.com)\n"
            "[File link](path/to/file.py)\n"
        )
        
        refs = find_file_references(test_file)
        
        assert len(refs) == 1
        assert refs[0].referenced_path == "path/to/file.py"
    
    def test_ignore_anchors(self):
        """Test that anchor links are not included in references."""
        test_file = self.temp_path / "test.md"
        test_file.write_text(
            "# Test\n"
            "[Section link](#section)\n"
            "[File link](path/to/file.py)\n"
        )
        
        refs = find_file_references(test_file)
        
        assert len(refs) == 1
        assert refs[0].referenced_path == "path/to/file.py"
    
    def test_file_not_found(self):
        """Test that FileNotFoundError is raised for non-existent files."""
        non_existent = self.temp_path / "nonexistent.md"
        
        with pytest.raises(FileNotFoundError):
            find_file_references(non_existent)


class TestPathMatches:
    """Tests for _path_matches helper function."""
    
    def test_exact_match(self):
        """Test exact path matching."""
        assert _path_matches("path/to/file.py", "path/to/file.py") is True
    
    def test_prefix_match(self):
        """Test prefix path matching."""
        assert _path_matches("path/to/file.py", "path/to") is True
        assert _path_matches("path/to/subdir/file.py", "path/to") is True
    
    def test_suffix_match(self):
        """Test suffix path matching."""
        assert _path_matches("../path/to/file.py", "path/to/file.py") is True
        assert _path_matches("./path/to/file.py", "path/to/file.py") is True
    
    def test_no_match(self):
        """Test paths that don't match."""
        assert _path_matches("path/to/file.py", "other/path") is False
        assert _path_matches("file.py", "path/to/file.py") is False


class TestReplacePath:
    """Tests for _replace_path helper function."""
    
    def test_exact_replacement(self):
        """Test exact path replacement."""
        result = _replace_path("path/to/file.py", "path/to/file.py", "new/path/file.py")
        assert result == "new/path/file.py"
    
    def test_prefix_replacement(self):
        """Test prefix path replacement."""
        result = _replace_path("path/to/subdir/file.py", "path/to", "new/location")
        assert result == "new/location/subdir/file.py"
    
    def test_suffix_replacement(self):
        """Test suffix path replacement."""
        result = _replace_path("../path/to/file.py", "path/to/file.py", "new/file.py")
        assert result == "../new/file.py"
    
    def test_no_replacement(self):
        """Test that non-matching paths are not replaced."""
        result = _replace_path("path/to/file.py", "other/path", "new/path")
        assert result == "path/to/file.py"


class TestUpdateReference:
    """Tests for update_reference function."""
    
    def test_update_markdown_link(self):
        """Test updating a markdown link reference."""
        ref = FileReference(
            file=Path("test.md"),
            line_number=5,
            original_text="[Link](path/to/file.py)",
            referenced_path="path/to/file.py",
            is_relative=True,
            reference_type="markdown_link"
        )
        
        path_mapping = {"path/to": "new/location"}
        updated = update_reference(ref, path_mapping)
        
        assert updated is not None
        assert updated.referenced_path == "new/location/file.py"
        assert "[Link]" in updated.original_text
        assert "new/location/file.py" in updated.original_text
    
    def test_update_inline_path(self):
        """Test updating an inline code path reference."""
        ref = FileReference(
            file=Path("test.md"),
            line_number=5,
            original_text="`path/to/file.py`",
            referenced_path="path/to/file.py",
            is_relative=True,
            reference_type="inline_path"
        )
        
        path_mapping = {"path/to": "new/location"}
        updated = update_reference(ref, path_mapping)
        
        assert updated is not None
        assert updated.referenced_path == "new/location/file.py"
        assert updated.original_text == "`new/location/file.py`"
    
    def test_no_update_needed(self):
        """Test that None is returned when no update is needed."""
        ref = FileReference(
            file=Path("test.md"),
            line_number=5,
            original_text="[Link](path/to/file.py)",
            referenced_path="path/to/file.py",
            is_relative=True,
            reference_type="markdown_link"
        )
        
        path_mapping = {"other/path": "new/location"}
        updated = update_reference(ref, path_mapping)
        
        assert updated is None


class TestUpdatePytestConfig:
    """Tests for update_pytest_config function."""
    
    def setup_method(self):
        """Create temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)
    
    def test_update_pytest_ini(self):
        """Test updating pytest.ini file."""
        config_file = self.temp_path / "pytest.ini"
        config_file.write_text(
            "[pytest]\n"
            "testpaths = tests\n"
            "python_files = test_*.py\n"
        )
        
        update_pytest_config(config_file, "apps/backend/tests")
        
        content = config_file.read_text()
        assert "testpaths = apps/backend/tests" in content
        assert "python_files = test_*.py" in content
    
    def test_update_pyproject_toml(self):
        """Test updating pyproject.toml file."""
        config_file = self.temp_path / "pyproject.toml"
        config_file.write_text(
            "[tool.pytest.ini_options]\n"
            'testpaths = ["tests"]\n'
            'python_files = ["test_*.py"]\n'
        )
        
        update_pytest_config(config_file, "apps/backend/tests")
        
        content = config_file.read_text()
        assert 'testpaths = ["apps/backend/tests"]' in content
    
    def test_file_not_found(self):
        """Test that FileNotFoundError is raised for non-existent config."""
        non_existent = self.temp_path / "nonexistent.ini"
        
        with pytest.raises(FileNotFoundError):
            update_pytest_config(non_existent, "apps/backend/tests")
    
    def test_unknown_config_type(self):
        """Test handling of unknown config file types."""
        config_file = self.temp_path / "unknown.cfg"
        config_file.write_text("some config")
        
        # Should not raise an error, just log a warning
        update_pytest_config(config_file, "apps/backend/tests")
        
        # Content should be unchanged
        assert config_file.read_text() == "some config"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
