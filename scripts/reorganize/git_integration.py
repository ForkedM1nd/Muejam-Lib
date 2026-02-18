"""
Git integration utilities for version control operations.

This module provides functions for staging changes, creating commits, and verifying
the state of the git repository during reorganization operations.
"""

import logging
from pathlib import Path
from typing import List, Optional
import git
from git import Repo, GitCommandError

logger = logging.getLogger(__name__)


def stage_changes(repo_path: Path, paths: Optional[List[Path]] = None) -> None:
    """
    Stage moved and deleted files for git commit.
    
    This function stages all changes including:
    - New files (moved to new locations)
    - Modified files (updated imports/references)
    - Deleted files (removed from old locations)
    
    Args:
        repo_path: Path to the git repository root
        paths: Optional list of specific paths to stage. If None, stages all changes.
        
    Raises:
        GitCommandError: If git operations fail
        ValueError: If repo_path is not a git repository
        
    Requirements: 9.1, 9.3
    """
    repo_path = Path(repo_path).resolve()
    
    try:
        repo = Repo(repo_path)
        
        if repo.bare:
            raise ValueError(f"Repository is bare: {repo_path}")
        
        logger.info(f"Staging changes in repository: {repo_path}")
        
        if paths is None:
            # Stage all changes (new, modified, and deleted files)
            repo.git.add(A=True)
            logger.info("Staged all changes (new, modified, and deleted files)")
        else:
            # Stage specific paths
            # Separate existing and deleted files
            existing_paths = []
            deleted_paths = []
            
            for p in paths:
                full_path = repo_path / p
                if full_path.exists():
                    existing_paths.append(str(p))
                else:
                    # Check if file was tracked (exists in HEAD)
                    try:
                        repo.git.ls_files(str(p), error_unmatch=True)
                        deleted_paths.append(str(p))
                    except git.GitCommandError:
                        # File was never tracked, skip it
                        logger.warning(f"File not found and not tracked: {p}")
            
            # Stage existing files
            if existing_paths:
                repo.index.add(existing_paths)
                logger.info(f"Staged {len(existing_paths)} existing files")
            
            # Stage deleted files
            if deleted_paths:
                repo.index.remove(deleted_paths, working_tree=False)
                logger.info(f"Staged {len(deleted_paths)} deleted files")
        
        # Log summary of staged changes
        staged_files = [item.a_path for item in repo.index.diff("HEAD")]
        logger.info(f"Total staged changes: {len(staged_files)}")
        
    except GitCommandError as e:
        logger.error(f"Git command failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Error staging changes: {e}")
        raise


def create_commit(repo_path: Path, message: str) -> str:
    """
    Create git commit with descriptive message.
    
    Args:
        repo_path: Path to the git repository root
        message: Commit message describing the changes
        
    Returns:
        The SHA hash of the created commit
        
    Raises:
        GitCommandError: If git operations fail
        ValueError: If repo_path is not a git repository or no changes to commit
        
    Requirements: 9.2, 9.3
    """
    repo_path = Path(repo_path).resolve()
    
    try:
        repo = Repo(repo_path)
        
        if repo.bare:
            raise ValueError(f"Repository is bare: {repo_path}")
        
        # Check if there are staged changes
        if not repo.index.diff("HEAD"):
            raise ValueError("No changes staged for commit")
        
        logger.info(f"Creating commit with message: {message}")
        
        # Create the commit
        commit = repo.index.commit(message)
        commit_sha = commit.hexsha
        
        logger.info(f"Successfully created commit: {commit_sha}")
        logger.info(f"Commit message: {message}")
        
        return commit_sha
        
    except GitCommandError as e:
        logger.error(f"Git command failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Error creating commit: {e}")
        raise


def verify_clean_state(repo_path: Path) -> bool:
    """
    Check for uncommitted changes in the working directory.
    
    This function verifies that:
    - There are no unstaged changes
    - There are no staged but uncommitted changes
    - There are no untracked files (except those in .gitignore)
    
    Args:
        repo_path: Path to the git repository root
        
    Returns:
        True if working directory is clean, False otherwise
        
    Raises:
        GitCommandError: If git operations fail
        ValueError: If repo_path is not a git repository
        
    Requirements: 9.4
    """
    repo_path = Path(repo_path).resolve()
    
    try:
        repo = Repo(repo_path)
        
        if repo.bare:
            raise ValueError(f"Repository is bare: {repo_path}")
        
        logger.info(f"Verifying clean state of repository: {repo_path}")
        
        # Check for unstaged changes
        if repo.is_dirty(untracked_files=False):
            logger.warning("Repository has unstaged changes")
            unstaged = [item.a_path for item in repo.index.diff(None)]
            logger.warning(f"Unstaged files: {unstaged}")
            return False
        
        # Check for staged but uncommitted changes
        if repo.index.diff("HEAD"):
            logger.warning("Repository has staged but uncommitted changes")
            staged = [item.a_path for item in repo.index.diff("HEAD")]
            logger.warning(f"Staged files: {staged}")
            return False
        
        # Check for untracked files
        untracked = repo.untracked_files
        if untracked:
            logger.warning(f"Repository has {len(untracked)} untracked files")
            logger.warning(f"Untracked files: {untracked}")
            return False
        
        logger.info("Repository is in clean state")
        return True
        
    except GitCommandError as e:
        logger.error(f"Git command failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Error verifying repository state: {e}")
        raise


def get_repository_root(start_path: Optional[Path] = None) -> Path:
    """
    Find the root directory of the git repository.
    
    Args:
        start_path: Path to start searching from. If None, uses current directory.
        
    Returns:
        Path to the repository root
        
    Raises:
        ValueError: If not inside a git repository
    """
    if start_path is None:
        start_path = Path.cwd()
    else:
        start_path = Path(start_path).resolve()
    
    try:
        repo = Repo(start_path, search_parent_directories=True)
        repo_root = Path(repo.working_dir)
        logger.debug(f"Found repository root: {repo_root}")
        return repo_root
    except Exception as e:
        raise ValueError(f"Not inside a git repository: {e}")
