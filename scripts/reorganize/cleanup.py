"""
Cleanup utilities for removing cache files, compiled files, and logs.

This module provides functions for finding and removing Python cache directories,
compiled files, and log files while preserving important files like .gitignore
and directories with .gitkeep files.
"""

import logging
from pathlib import Path
from typing import List
import shutil

logger = logging.getLogger(__name__)


def find_cache_directories(root: Path) -> List[Path]:
    """
    Recursively find all Python cache directories in the project.
    
    Locates __pycache__, .pytest_cache, and .hypothesis directories.
    
    Args:
        root: Root directory to search from
        
    Returns:
        List of Path objects for cache directories found
        
    Requirements: 7.1, 7.3, 7.4
    """
    root = Path(root).resolve()
    cache_dirs = []
    
    if not root.exists() or not root.is_dir():
        logger.warning(f"Root directory does not exist or is not a directory: {root}")
        return cache_dirs
    
    cache_names = {'__pycache__', '.pytest_cache', '.hypothesis'}
    
    logger.info(f"Searching for cache directories in {root}")
    
    try:
        for path in root.rglob('*'):
            if path.is_dir() and path.name in cache_names:
                cache_dirs.append(path)
                logger.debug(f"Found cache directory: {path}")
    except PermissionError as e:
        logger.warning(f"Permission denied while searching {root}: {e}")
    
    logger.info(f"Found {len(cache_dirs)} cache directories")
    return cache_dirs


def find_compiled_files(root: Path) -> List[Path]:
    """
    Recursively find all compiled Python files in the project.
    
    Locates .pyc and .pyo files.
    
    Args:
        root: Root directory to search from
        
    Returns:
        List of Path objects for compiled files found
        
    Requirements: 7.2
    """
    root = Path(root).resolve()
    compiled_files = []
    
    if not root.exists() or not root.is_dir():
        logger.warning(f"Root directory does not exist or is not a directory: {root}")
        return compiled_files
    
    compiled_extensions = {'.pyc', '.pyo'}
    
    logger.info(f"Searching for compiled files in {root}")
    
    try:
        for path in root.rglob('*'):
            if path.is_file() and path.suffix in compiled_extensions:
                compiled_files.append(path)
                logger.debug(f"Found compiled file: {path}")
    except PermissionError as e:
        logger.warning(f"Permission denied while searching {root}: {e}")
    
    logger.info(f"Found {len(compiled_files)} compiled files")
    return compiled_files


def find_log_files(root: Path) -> List[Path]:
    """
    Recursively find all log files in the project.
    
    Locates .log files.
    
    Args:
        root: Root directory to search from
        
    Returns:
        List of Path objects for log files found
        
    Requirements: 8.1, 8.2
    """
    root = Path(root).resolve()
    log_files = []
    
    if not root.exists() or not root.is_dir():
        logger.warning(f"Root directory does not exist or is not a directory: {root}")
        return log_files
    
    logger.info(f"Searching for log files in {root}")
    
    try:
        for path in root.rglob('*.log'):
            if path.is_file():
                log_files.append(path)
                logger.debug(f"Found log file: {path}")
    except PermissionError as e:
        logger.warning(f"Permission denied while searching {root}: {e}")
    
    logger.info(f"Found {len(log_files)} log files")
    return log_files


def remove_paths(paths: List[Path]) -> None:
    """
    Safely remove all specified files and directories.
    
    Preserves .gitignore files and directories containing .gitkeep files.
    Handles errors gracefully and continues with remaining paths.
    
    Args:
        paths: List of Path objects to remove
        
    Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 8.1, 8.2, 8.3, 8.4, 5.5
    """
    if not paths:
        logger.info("No paths to remove")
        return
    
    logger.info(f"Removing {len(paths)} paths")
    
    removed_count = 0
    skipped_count = 0
    error_count = 0
    
    for path in paths:
        try:
            path = Path(path).resolve()
            
            # Skip if path doesn't exist
            if not path.exists():
                logger.debug(f"Path does not exist, skipping: {path}")
                skipped_count += 1
                continue
            
            # Preserve .gitignore files (Requirement 7.5)
            if path.is_file() and path.name == '.gitignore':
                logger.debug(f"Preserving .gitignore file: {path}")
                skipped_count += 1
                continue
            
            # Preserve directories with .gitkeep files (Requirement 5.5)
            if path.is_dir() and _contains_gitkeep(path):
                logger.debug(f"Preserving directory with .gitkeep: {path}")
                skipped_count += 1
                continue
            
            # Remove file or directory
            if path.is_file():
                path.unlink()
                logger.debug(f"Removed file: {path}")
                removed_count += 1
            elif path.is_dir():
                shutil.rmtree(path)
                logger.debug(f"Removed directory: {path}")
                removed_count += 1
            else:
                logger.warning(f"Path is neither file nor directory: {path}")
                skipped_count += 1
                
        except PermissionError as e:
            logger.error(f"Permission denied when removing {path}: {e}")
            error_count += 1
        except OSError as e:
            logger.error(f"Error removing {path}: {e}")
            error_count += 1
    
    logger.info(
        f"Cleanup complete: {removed_count} removed, "
        f"{skipped_count} skipped, {error_count} errors"
    )


def _contains_gitkeep(directory: Path) -> bool:
    """
    Check if a directory contains a .gitkeep file.
    
    Args:
        directory: Directory path to check
        
    Returns:
        True if directory contains .gitkeep file, False otherwise
    """
    try:
        gitkeep_path = directory / '.gitkeep'
        return gitkeep_path.exists() and gitkeep_path.is_file()
    except (OSError, IOError):
        return False
