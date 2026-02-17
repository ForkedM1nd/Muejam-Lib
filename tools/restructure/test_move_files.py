#!/usr/bin/env python3
"""
Unit tests for move_files.py

Tests the GitHistoryPreserver class functionality.
"""

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from move_files import GitHistoryPreserver, MoveOperation


class TestGitHistoryPreserver:
    """Test suite for GitHistoryPreserver class."""
    
    def test_init(self, tmp_path):
        """Test GitHistoryPreserver initialization."""
        preserver = GitHistoryPreserver(tmp_path)
        assert preserver.repo_root == tmp_path
        assert preserver.failed_moves == []
        
    def test_get_move_plan_returns_correct_operations(self, tmp_path):
        """Test that get_move_plan returns expected move operations."""
        preserver = GitHistoryPreserver(tmp_path)
        move_plan = preserver.get_move_plan()
        
        # Verify we have the expected number of operations
        assert len(move_plan) == 8
        
        # Verify backend move
        backend_move = move_plan[0]
        assert backend_move.source == "backend"
        assert backend_move.destination == "apps/backend"
        assert backend_move.is_directory is True
        
        # Verify frontend move
        frontend_move = move_plan[1]
        assert frontend_move.source == "frontend"
        assert frontend_move.destination == "apps/frontend"
        assert frontend_move.is_directory is True
        
        # Verify documentation moves
        quickstart_move = move_plan[2]
        assert quickstart_move.source == "QUICKSTART.md"
        assert quickstart_move.destination == "docs/getting-started/quickstart.md"
        assert quickstart_move.is_directory is False
        
    @patch('subprocess.run')
    def test_check_git_status_clean(self, mock_run, tmp_path):
        """Test check_git_status with clean working directory."""
        mock_run.return_value = Mock(stdout="", returncode=0)
        
        preserver = GitHistoryPreserver(tmp_path)
        result = preserver.check_git_status()
        
        assert result is True
        mock_run.assert_called_once()
        
    @patch('subprocess.run')
    def test_check_git_status_dirty(self, mock_run, tmp_path):
        """Test check_git_status with uncommitted changes."""
        mock_run.return_value = Mock(stdout="M file.txt\n", returncode=0)
        
        preserver = GitHistoryPreserver(tmp_path)
        result = preserver.check_git_status()
        
        assert result is False
        
    def test_move_file_source_not_exists(self, tmp_path):
        """Test move_file when source file doesn't exist."""
        preserver = GitHistoryPreserver(tmp_path)
        
        result = preserver.move_file("nonexistent.txt", "dest.txt")
        
        assert result is False
        assert len(preserver.failed_moves) == 1
        assert "does not exist" in preserver.failed_moves[0][2]
        
    def test_move_file_destination_parent_not_exists(self, tmp_path):
        """Test move_file when destination parent doesn't exist."""
        # Create source file
        source_file = tmp_path / "source.txt"
        source_file.write_text("test")
        
        preserver = GitHistoryPreserver(tmp_path)
        result = preserver.move_file("source.txt", "nonexistent/dest.txt")
        
        assert result is False
        assert len(preserver.failed_moves) == 1
        assert "parent directory does not exist" in preserver.failed_moves[0][2]
        
    def test_move_file_destination_already_exists(self, tmp_path):
        """Test move_file when destination already exists."""
        # Create source and destination files
        source_file = tmp_path / "source.txt"
        source_file.write_text("source")
        dest_file = tmp_path / "dest.txt"
        dest_file.write_text("dest")
        
        preserver = GitHistoryPreserver(tmp_path)
        result = preserver.move_file("source.txt", "dest.txt")
        
        # Should skip and return True
        assert result is True
        assert len(preserver.failed_moves) == 0
        
    @patch('subprocess.run')
    def test_move_file_success(self, mock_run, tmp_path):
        """Test successful file move."""
        # Create source file and destination parent
        source_file = tmp_path / "source.txt"
        source_file.write_text("test")
        dest_dir = tmp_path / "dest_dir"
        dest_dir.mkdir()
        
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        
        preserver = GitHistoryPreserver(tmp_path)
        result = preserver.move_file("source.txt", "dest_dir/dest.txt")
        
        assert result is True
        assert len(preserver.failed_moves) == 0
        mock_run.assert_called_once()
        
    @patch('subprocess.run')
    def test_move_file_git_mv_fails(self, mock_run, tmp_path):
        """Test move_file when git mv command fails."""
        # Create source file and destination parent
        source_file = tmp_path / "source.txt"
        source_file.write_text("test")
        dest_dir = tmp_path / "dest_dir"
        dest_dir.mkdir()
        
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "git mv", stderr="fatal: not a git repository"
        )
        
        preserver = GitHistoryPreserver(tmp_path)
        result = preserver.move_file("source.txt", "dest_dir/dest.txt")
        
        assert result is False
        assert len(preserver.failed_moves) == 1
        assert "git mv failed" in preserver.failed_moves[0][2]
        
    def test_move_directory_source_not_exists(self, tmp_path):
        """Test move_directory when source doesn't exist."""
        preserver = GitHistoryPreserver(tmp_path)
        
        result = preserver.move_directory("nonexistent", "dest")
        
        assert result is False
        assert len(preserver.failed_moves) == 1
        
    @patch('subprocess.run')
    def test_move_directory_success(self, mock_run, tmp_path):
        """Test successful directory move."""
        # Create source directory and destination parent
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        dest_parent = tmp_path / "dest_parent"
        dest_parent.mkdir()
        
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        
        preserver = GitHistoryPreserver(tmp_path)
        result = preserver.move_directory("source", "dest_parent/dest")
        
        assert result is True
        assert len(preserver.failed_moves) == 0
        
    @patch('subprocess.run')
    def test_verify_history_preserved_success(self, mock_run, tmp_path):
        """Test verify_history_preserved with valid history."""
        # Create a file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        
        mock_run.return_value = Mock(
            returncode=0,
            stdout="abc123 Initial commit\n",
            stderr=""
        )
        
        preserver = GitHistoryPreserver(tmp_path)
        result = preserver.verify_history_preserved("test.txt")
        
        assert result is True
        
    @patch('subprocess.run')
    def test_verify_history_preserved_no_history(self, mock_run, tmp_path):
        """Test verify_history_preserved with no history (new file)."""
        # Create a file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        
        preserver = GitHistoryPreserver(tmp_path)
        result = preserver.verify_history_preserved("test.txt")
        
        # Should return True for new files
        assert result is True
        
    def test_verify_history_preserved_file_not_exists(self, tmp_path):
        """Test verify_history_preserved when file doesn't exist."""
        preserver = GitHistoryPreserver(tmp_path)
        result = preserver.verify_history_preserved("nonexistent.txt")
        
        assert result is False
        
    def test_get_failed_moves(self, tmp_path):
        """Test get_failed_moves returns correct list."""
        preserver = GitHistoryPreserver(tmp_path)
        
        # Simulate some failed moves
        preserver.failed_moves.append(("src1", "dest1", "error1"))
        preserver.failed_moves.append(("src2", "dest2", "error2"))
        
        failed = preserver.get_failed_moves()
        
        assert len(failed) == 2
        assert failed[0] == ("src1", "dest1", "error1")
        assert failed[1] == ("src2", "dest2", "error2")


class TestMoveOperation:
    """Test suite for MoveOperation dataclass."""
    
    def test_move_operation_creation(self):
        """Test MoveOperation can be created with correct attributes."""
        op = MoveOperation(
            source="src",
            destination="dest",
            is_directory=True,
            description="Test move"
        )
        
        assert op.source == "src"
        assert op.destination == "dest"
        assert op.is_directory is True
        assert op.description == "Test move"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
