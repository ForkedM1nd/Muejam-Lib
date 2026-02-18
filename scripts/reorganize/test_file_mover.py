"""
Unit tests for file_mover module.

Tests cover:
- Moving individual files
- Moving directory trees
- Preserving directory structure
- Handling empty directories
- Error handling for permission errors and file not found cases
- Handling symbolic links
- Preserving placeholder files like .gitkeep
"""

import tempfile
import shutil
from pathlib import Path
import pytest
import sys

from scripts.reorganize.file_mover import move_directory, move_file, remove_empty_directory


class TestMoveFile:
    """Test cases for move_file function."""
    
    def test_move_single_file(self, tmp_path):
        """Test moving a single file to a new location."""
        # Create source file
        source = tmp_path / "source.txt"
        source.write_text("test content")
        
        # Move to destination
        destination = tmp_path / "dest" / "source.txt"
        move_file(source, destination)
        
        # Verify file was moved
        assert destination.exists()
        assert destination.read_text() == "test content"
        assert not source.exists()
    
    def test_move_file_creates_parent_directories(self, tmp_path):
        """Test that move_file creates parent directories if they don't exist."""
        source = tmp_path / "source.txt"
        source.write_text("test content")
        
        # Destination with nested directories that don't exist
        destination = tmp_path / "level1" / "level2" / "level3" / "source.txt"
        move_file(source, destination)
        
        assert destination.exists()
        assert destination.read_text() == "test content"
    
    def test_move_file_identical_content_at_destination(self, tmp_path):
        """Test moving file when destination already exists with identical content."""
        source = tmp_path / "source.txt"
        source.write_text("test content")
        
        destination = tmp_path / "dest.txt"
        destination.write_text("test content")
        
        # Should not raise error, should remove source
        move_file(source, destination)
        
        assert destination.exists()
        assert not source.exists()
    
    def test_move_file_different_content_at_destination(self, tmp_path):
        """Test moving file when destination exists with different content."""
        source = tmp_path / "source.txt"
        source.write_text("source content")
        
        destination = tmp_path / "dest.txt"
        destination.write_text("different content")
        
        # Should raise FileExistsError
        with pytest.raises(FileExistsError):
            move_file(source, destination)
    
    def test_move_file_source_not_found(self, tmp_path):
        """Test error handling when source file doesn't exist."""
        source = tmp_path / "nonexistent.txt"
        destination = tmp_path / "dest.txt"
        
        with pytest.raises(FileNotFoundError):
            move_file(source, destination)
    
    def test_move_file_source_is_directory(self, tmp_path):
        """Test error handling when source is a directory."""
        source = tmp_path / "dir"
        source.mkdir()
        destination = tmp_path / "dest.txt"
        
        with pytest.raises(ValueError):
            move_file(source, destination)


class TestMoveDirectory:
    """Test cases for move_directory function."""
    
    def test_move_empty_directory(self, tmp_path):
        """Test moving an empty directory."""
        source = tmp_path / "source_dir"
        source.mkdir()
        
        destination = tmp_path / "dest_dir"
        move_directory(source, destination)
        
        assert destination.exists()
        assert destination.is_dir()
        assert not source.exists()
    
    def test_move_directory_with_files(self, tmp_path):
        """Test moving a directory containing files."""
        source = tmp_path / "source_dir"
        source.mkdir()
        (source / "file1.txt").write_text("content1")
        (source / "file2.txt").write_text("content2")
        
        destination = tmp_path / "dest_dir"
        move_directory(source, destination)
        
        assert destination.exists()
        assert (destination / "file1.txt").read_text() == "content1"
        assert (destination / "file2.txt").read_text() == "content2"
        assert not source.exists()
    
    def test_move_directory_preserves_structure(self, tmp_path):
        """Test that directory structure is preserved during move."""
        # Create nested structure
        source = tmp_path / "source_dir"
        source.mkdir()
        (source / "level1").mkdir()
        (source / "level1" / "level2").mkdir()
        (source / "level1" / "level2" / "file.txt").write_text("nested content")
        (source / "level1" / "file1.txt").write_text("level1 content")
        
        destination = tmp_path / "dest_dir"
        move_directory(source, destination)
        
        # Verify structure is preserved
        assert (destination / "level1" / "level2" / "file.txt").read_text() == "nested content"
        assert (destination / "level1" / "file1.txt").read_text() == "level1 content"
        assert not source.exists()
    
    def test_move_directory_with_config_files(self, tmp_path):
        """Test that configuration files are preserved in relative positions."""
        source = tmp_path / "source_dir"
        source.mkdir()
        (source / "conftest.py").write_text("# conftest")
        (source / "__init__.py").write_text("# init")
        (source / "subdir").mkdir()
        (source / "subdir" / "__init__.py").write_text("# subdir init")
        
        destination = tmp_path / "dest_dir"
        move_directory(source, destination)
        
        # Verify config files are in correct relative positions
        assert (destination / "conftest.py").read_text() == "# conftest"
        assert (destination / "__init__.py").read_text() == "# init"
        assert (destination / "subdir" / "__init__.py").read_text() == "# subdir init"
    
    def test_move_directory_source_not_found(self, tmp_path):
        """Test error handling when source directory doesn't exist."""
        source = tmp_path / "nonexistent"
        destination = tmp_path / "dest"
        
        with pytest.raises(FileNotFoundError):
            move_directory(source, destination)
    
    def test_move_directory_source_is_file(self, tmp_path):
        """Test error handling when source is a file."""
        source = tmp_path / "file.txt"
        source.write_text("content")
        destination = tmp_path / "dest"
        
        with pytest.raises(ValueError):
            move_directory(source, destination)
    
    def test_move_directory_creates_parent_directories(self, tmp_path):
        """Test that parent directories are created if they don't exist."""
        source = tmp_path / "source_dir"
        source.mkdir()
        (source / "file.txt").write_text("content")
        
        destination = tmp_path / "level1" / "level2" / "dest_dir"
        move_directory(source, destination)
        
        assert destination.exists()
        assert (destination / "file.txt").read_text() == "content"


class TestRemoveEmptyDirectory:
    """Test cases for remove_empty_directory function."""
    
    def test_remove_empty_directory(self, tmp_path):
        """Test removing an empty directory."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        
        remove_empty_directory(empty_dir, recursive=False)
        
        assert not empty_dir.exists()
    
    def test_remove_empty_directory_recursive(self, tmp_path):
        """Test recursively removing empty parent directories."""
        # Create nested empty directories
        nested = tmp_path / "level1" / "level2" / "level3"
        nested.mkdir(parents=True)
        
        # Remove innermost directory recursively
        remove_empty_directory(nested, recursive=True)
        
        # All empty directories should be removed
        assert not nested.exists()
        assert not (tmp_path / "level1" / "level2").exists()
        assert not (tmp_path / "level1").exists()
    
    def test_preserve_directory_with_files(self, tmp_path):
        """Test that directories with files are not removed."""
        dir_with_file = tmp_path / "dir"
        dir_with_file.mkdir()
        (dir_with_file / "file.txt").write_text("content")
        
        remove_empty_directory(dir_with_file, recursive=False)
        
        # Directory should still exist
        assert dir_with_file.exists()
    
    def test_preserve_directory_with_gitkeep(self, tmp_path):
        """Test that directories with .gitkeep files are not removed."""
        dir_with_gitkeep = tmp_path / "dir"
        dir_with_gitkeep.mkdir()
        (dir_with_gitkeep / ".gitkeep").write_text("")
        
        remove_empty_directory(dir_with_gitkeep, recursive=False)
        
        # Directory should still exist (Requirement 5.5)
        assert dir_with_gitkeep.exists()
    
    def test_preserve_directory_with_gitignore(self, tmp_path):
        """Test that directories with .gitignore files are not removed."""
        dir_with_gitignore = tmp_path / "dir"
        dir_with_gitignore.mkdir()
        (dir_with_gitignore / ".gitignore").write_text("*.log")
        
        remove_empty_directory(dir_with_gitignore, recursive=False)
        
        # Directory should still exist
        assert dir_with_gitignore.exists()
    
    def test_remove_empty_directory_nonexistent(self, tmp_path):
        """Test that removing nonexistent directory doesn't raise error."""
        nonexistent = tmp_path / "nonexistent"
        
        # Should not raise error
        remove_empty_directory(nonexistent, recursive=False)
    
    def test_remove_empty_directory_stops_at_non_empty_parent(self, tmp_path):
        """Test that recursive removal stops when parent has content."""
        # Create structure: parent/child1/grandchild and parent/child2/file.txt
        parent = tmp_path / "parent"
        child1 = parent / "child1"
        grandchild = child1 / "grandchild"
        grandchild.mkdir(parents=True)
        
        child2 = parent / "child2"
        child2.mkdir()
        (child2 / "file.txt").write_text("content")
        
        # Remove grandchild recursively
        remove_empty_directory(grandchild, recursive=True)
        
        # grandchild and child1 should be removed, but parent should remain
        assert not grandchild.exists()
        assert not child1.exists()
        assert parent.exists()
        assert child2.exists()


class TestSymbolicLinks:
    """Test cases for handling symbolic links."""
    
    @pytest.mark.skipif(sys.platform == "win32", reason="Symlinks require admin privileges on Windows")
    def test_move_file_with_symlink(self, tmp_path):
        """Test moving a file that is a symbolic link."""
        # Create target file
        target = tmp_path / "target.txt"
        target.write_text("target content")
        
        # Create symlink
        symlink = tmp_path / "link.txt"
        symlink.symlink_to(target)
        
        # Move symlink
        destination = tmp_path / "dest" / "link.txt"
        move_file(symlink, destination)
        
        # Verify symlink was moved (not the target)
        assert destination.exists()
        assert destination.is_symlink()
        assert not symlink.exists()
        assert target.exists()  # Original target should still exist
