"""
Unit tests for git_integration module.

Tests cover:
- Staging moved files
- Staging deleted files
- Creating commits with descriptive messages
- Verifying clean repository state
- Error handling for git operations
"""

import tempfile
from pathlib import Path
import pytest
import git
from git import Repo

from scripts.reorganize.git_integration import (
    stage_changes,
    create_commit,
    verify_clean_state,
    get_repository_root
)


@pytest.fixture
def git_repo(tmp_path):
    """Create a temporary git repository for testing."""
    repo = Repo.init(tmp_path)
    
    # Configure git user for commits
    with repo.config_writer() as config:
        config.set_value("user", "name", "Test User")
        config.set_value("user", "email", "test@example.com")
    
    # Create initial commit
    initial_file = tmp_path / "README.md"
    initial_file.write_text("# Test Repository")
    repo.index.add([str(initial_file)])
    repo.index.commit("Initial commit")
    
    return tmp_path


class TestStageChanges:
    """Test cases for stage_changes function."""
    
    def test_stage_new_file(self, git_repo):
        """Test staging a newly created file."""
        # Create new file
        new_file = git_repo / "new_file.txt"
        new_file.write_text("new content")
        
        # Stage the change
        stage_changes(git_repo, [Path("new_file.txt")])
        
        # Verify file is staged
        repo = Repo(git_repo)
        staged_files = [item.a_path for item in repo.index.diff("HEAD")]
        assert "new_file.txt" in staged_files
    
    def test_stage_modified_file(self, git_repo):
        """Test staging a modified file."""
        # Modify existing file
        readme = git_repo / "README.md"
        readme.write_text("# Modified Repository")
        
        # Stage the change
        stage_changes(git_repo, [Path("README.md")])
        
        # Verify file is staged
        repo = Repo(git_repo)
        staged_files = [item.a_path for item in repo.index.diff("HEAD")]
        assert "README.md" in staged_files
    
    def test_stage_deleted_file(self, git_repo):
        """Test staging a deleted file."""
        # Delete existing file
        readme = git_repo / "README.md"
        readme.unlink()
        
        # Stage the deletion
        stage_changes(git_repo, [Path("README.md")])
        
        # Verify deletion is staged
        repo = Repo(git_repo)
        staged_files = [item.a_path for item in repo.index.diff("HEAD")]
        assert "README.md" in staged_files
    
    def test_stage_all_changes(self, git_repo):
        """Test staging all changes when no specific paths provided."""
        # Create multiple changes
        (git_repo / "new_file.txt").write_text("new")
        (git_repo / "README.md").write_text("modified")
        (git_repo / "another.txt").write_text("another new file")
        
        # Stage all changes
        stage_changes(git_repo)
        
        # Verify all files are staged
        repo = Repo(git_repo)
        staged_files = [item.a_path for item in repo.index.diff("HEAD")]
        assert len(staged_files) >= 2  # At least README.md and new files
    
    def test_stage_multiple_files(self, git_repo):
        """Test staging multiple specific files."""
        # Create multiple files
        file1 = git_repo / "file1.txt"
        file1.write_text("content1")
        file2 = git_repo / "file2.txt"
        file2.write_text("content2")
        file3 = git_repo / "file3.txt"
        file3.write_text("content3")
        
        # Stage only file1 and file2
        stage_changes(git_repo, [Path("file1.txt"), Path("file2.txt")])
        
        # Verify correct files are staged
        repo = Repo(git_repo)
        staged_files = [item.a_path for item in repo.index.diff("HEAD")]
        assert "file1.txt" in staged_files
        assert "file2.txt" in staged_files
        # file3.txt should not be staged
    
    def test_stage_changes_in_subdirectory(self, git_repo):
        """Test staging files in subdirectories."""
        # Create subdirectory with files
        subdir = git_repo / "subdir"
        subdir.mkdir()
        (subdir / "file.txt").write_text("content")
        
        # Stage the file
        stage_changes(git_repo, [Path("subdir/file.txt")])
        
        # Verify file is staged
        repo = Repo(git_repo)
        staged_files = [item.a_path for item in repo.index.diff("HEAD")]
        assert "subdir/file.txt" in staged_files
    
    def test_stage_changes_not_a_repo(self, tmp_path):
        """Test error handling when path is not a git repository."""
        non_repo = tmp_path / "not_a_repo"
        non_repo.mkdir()
        
        with pytest.raises(Exception):  # Should raise git.InvalidGitRepositoryError
            stage_changes(non_repo)


class TestCreateCommit:
    """Test cases for create_commit function."""
    
    def test_create_commit_with_staged_changes(self, git_repo):
        """Test creating a commit with staged changes."""
        # Create and stage a change
        new_file = git_repo / "new_file.txt"
        new_file.write_text("content")
        stage_changes(git_repo, [Path("new_file.txt")])
        
        # Create commit
        commit_message = "Add new file"
        commit_sha = create_commit(git_repo, commit_message)
        
        # Verify commit was created
        assert commit_sha is not None
        assert len(commit_sha) == 40  # SHA-1 hash length
        
        # Verify commit message
        repo = Repo(git_repo)
        latest_commit = repo.head.commit
        assert latest_commit.message.strip() == commit_message
    
    def test_create_commit_with_descriptive_message(self, git_repo):
        """Test creating a commit with a descriptive message."""
        # Create and stage changes
        (git_repo / "file1.txt").write_text("content1")
        (git_repo / "file2.txt").write_text("content2")
        stage_changes(git_repo)
        
        # Create commit with descriptive message
        message = "Reorganize tests and docs: move backend tests to apps/backend/tests"
        commit_sha = create_commit(git_repo, message)
        
        # Verify commit message
        repo = Repo(git_repo)
        latest_commit = repo.head.commit
        assert latest_commit.message.strip() == message
    
    def test_create_commit_no_staged_changes(self, git_repo):
        """Test error handling when no changes are staged."""
        # Try to commit without staging anything
        with pytest.raises(ValueError, match="No changes staged"):
            create_commit(git_repo, "Empty commit")
    
    def test_create_commit_not_a_repo(self, tmp_path):
        """Test error handling when path is not a git repository."""
        non_repo = tmp_path / "not_a_repo"
        non_repo.mkdir()
        
        with pytest.raises(Exception):
            create_commit(non_repo, "Test commit")
    
    def test_create_commit_includes_all_staged_files(self, git_repo):
        """Test that commit includes all staged files."""
        # Create and stage multiple files
        files = ["file1.txt", "file2.txt", "file3.txt"]
        for filename in files:
            (git_repo / filename).write_text(f"content of {filename}")
        stage_changes(git_repo)
        
        # Create commit
        create_commit(git_repo, "Add multiple files")
        
        # Verify all files are in the commit
        repo = Repo(git_repo)
        latest_commit = repo.head.commit
        committed_files = list(latest_commit.stats.files.keys())
        
        for filename in files:
            assert filename in committed_files


class TestVerifyCleanState:
    """Test cases for verify_clean_state function."""
    
    def test_verify_clean_state_clean_repo(self, git_repo):
        """Test verifying a clean repository state."""
        # Repository should be clean after initial setup
        assert verify_clean_state(git_repo) is True
    
    def test_verify_clean_state_with_unstaged_changes(self, git_repo):
        """Test detecting unstaged changes."""
        # Modify file without staging
        readme = git_repo / "README.md"
        readme.write_text("# Modified")
        
        # Should detect unstaged changes
        assert verify_clean_state(git_repo) is False
    
    def test_verify_clean_state_with_staged_changes(self, git_repo):
        """Test detecting staged but uncommitted changes."""
        # Create and stage a file
        new_file = git_repo / "new_file.txt"
        new_file.write_text("content")
        stage_changes(git_repo, [Path("new_file.txt")])
        
        # Should detect staged changes
        assert verify_clean_state(git_repo) is False
    
    def test_verify_clean_state_with_untracked_files(self, git_repo):
        """Test detecting untracked files."""
        # Create untracked file
        untracked = git_repo / "untracked.txt"
        untracked.write_text("untracked content")
        
        # Should detect untracked files
        assert verify_clean_state(git_repo) is False
    
    def test_verify_clean_state_after_commit(self, git_repo):
        """Test that state is clean after committing all changes."""
        # Create, stage, and commit a file
        new_file = git_repo / "new_file.txt"
        new_file.write_text("content")
        stage_changes(git_repo, [Path("new_file.txt")])
        create_commit(git_repo, "Add new file")
        
        # Should be clean after commit
        assert verify_clean_state(git_repo) is True
    
    def test_verify_clean_state_not_a_repo(self, tmp_path):
        """Test error handling when path is not a git repository."""
        non_repo = tmp_path / "not_a_repo"
        non_repo.mkdir()
        
        with pytest.raises(Exception):
            verify_clean_state(non_repo)
    
    def test_verify_clean_state_with_deleted_file(self, git_repo):
        """Test detecting deleted but unstaged files."""
        # Delete file without staging
        readme = git_repo / "README.md"
        readme.unlink()
        
        # Should detect unstaged deletion
        assert verify_clean_state(git_repo) is False


class TestGetRepositoryRoot:
    """Test cases for get_repository_root function."""
    
    def test_get_repository_root_from_root(self, git_repo):
        """Test getting repository root from the root directory."""
        root = get_repository_root(git_repo)
        assert root == git_repo
    
    def test_get_repository_root_from_subdirectory(self, git_repo):
        """Test getting repository root from a subdirectory."""
        # Create subdirectory
        subdir = git_repo / "subdir" / "nested"
        subdir.mkdir(parents=True)
        
        # Get root from subdirectory
        root = get_repository_root(subdir)
        assert root == git_repo
    
    def test_get_repository_root_not_a_repo(self, tmp_path):
        """Test error handling when not in a git repository."""
        non_repo = tmp_path / "not_a_repo"
        non_repo.mkdir()
        
        with pytest.raises(ValueError, match="Not inside a git repository"):
            get_repository_root(non_repo)
    
    def test_get_repository_root_current_directory(self, git_repo, monkeypatch):
        """Test getting repository root from current directory."""
        # Change to git repo directory
        monkeypatch.chdir(git_repo)
        
        # Get root without specifying path
        root = get_repository_root()
        assert root == git_repo


class TestIntegrationScenarios:
    """Integration test scenarios combining multiple operations."""
    
    def test_complete_workflow(self, git_repo):
        """Test complete workflow: stage, commit, verify clean."""
        # Create multiple changes
        (git_repo / "file1.txt").write_text("content1")
        (git_repo / "file2.txt").write_text("content2")
        (git_repo / "README.md").write_text("# Updated")
        
        # Stage all changes
        stage_changes(git_repo)
        
        # Create commit
        commit_sha = create_commit(git_repo, "Update multiple files")
        assert commit_sha is not None
        
        # Verify clean state
        assert verify_clean_state(git_repo) is True
    
    def test_stage_moved_and_deleted_files(self, git_repo):
        """Test staging both moved (new) and deleted files."""
        # Create a file and commit it
        old_file = git_repo / "old_location.txt"
        old_file.write_text("content")
        stage_changes(git_repo, [Path("old_location.txt")])
        create_commit(git_repo, "Add file")
        
        # Simulate move: create new file and delete old
        new_file = git_repo / "new_location.txt"
        new_file.write_text("content")
        old_file.unlink()
        
        # Stage both changes
        stage_changes(git_repo, [Path("new_location.txt"), Path("old_location.txt")])
        
        # Verify both are staged
        repo = Repo(git_repo)
        diff = repo.index.diff("HEAD")
        
        # Get all changed files (additions, modifications, deletions)
        staged_files = set()
        for item in diff:
            staged_files.add(item.a_path)
            if item.b_path:
                staged_files.add(item.b_path)
        
        assert "new_location.txt" in staged_files
        assert "old_location.txt" in staged_files
    
    def test_reorganization_commit_message(self, git_repo):
        """Test creating commit with reorganization-specific message."""
        # Simulate reorganization changes
        (git_repo / "apps" / "backend" / "tests").mkdir(parents=True)
        (git_repo / "apps" / "backend" / "tests" / "test_file.py").write_text("# test")
        
        # Stage and commit
        stage_changes(git_repo)
        message = "Reorganize tests and docs: move backend tests to apps/backend/tests, move backend docs to docs/backend, cleanup cache and log files"
        commit_sha = create_commit(git_repo, message)
        
        # Verify commit message
        repo = Repo(git_repo)
        latest_commit = repo.head.commit
        assert "Reorganize tests and docs" in latest_commit.message
        assert "backend tests" in latest_commit.message
