"""
File movement utilities for reorganizing project structure.

This module provides functions for moving files and directories while preserving
structure, and for cleaning up empty directories after moves.
"""

import shutil
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def move_directory(source: Path, destination: Path) -> None:
    """
    Move entire directory tree from source to destination while preserving structure.
    
    Args:
        source: Source directory path to move
        destination: Destination directory path
        
    Raises:
        FileNotFoundError: If source directory doesn't exist
        PermissionError: If lacking permissions to move files
        OSError: For other file system errors
        
    Requirements: 1.1, 1.2, 2.1, 2.2
    """
    source = Path(source).resolve()
    destination = Path(destination).resolve()
    
    # Validate source exists
    if not source.exists():
        raise FileNotFoundError(f"Source directory does not exist: {source}")
    
    if not source.is_dir():
        raise ValueError(f"Source is not a directory: {source}")
    
    logger.info(f"Moving directory from {source} to {destination}")
    
    try:
        # Create parent directories if needed
        destination.parent.mkdir(parents=True, exist_ok=True)
        
        # If destination exists, we need to merge contents
        if destination.exists():
            logger.warning(f"Destination already exists: {destination}")
            # Move contents individually to merge
            for item in source.iterdir():
                dest_item = destination / item.name
                if item.is_dir():
                    move_directory(item, dest_item)
                else:
                    move_file(item, dest_item)
        else:
            # Move entire directory tree
            shutil.move(str(source), str(destination))
            logger.info(f"Successfully moved directory to {destination}")
            
    except PermissionError as e:
        logger.error(f"Permission denied when moving {source} to {destination}: {e}")
        raise
    except OSError as e:
        logger.error(f"Error moving directory {source} to {destination}: {e}")
        raise


def move_file(source: Path, destination: Path) -> None:
    """
    Move individual file to new location, creating destination directory if needed.
    
    Args:
        source: Source file path to move
        destination: Destination file path
        
    Raises:
        FileNotFoundError: If source file doesn't exist
        PermissionError: If lacking permissions to move file
        OSError: For other file system errors
        
    Requirements: 1.1, 2.1
    """
    source = Path(source).resolve()
    destination = Path(destination).resolve()
    
    # Validate source exists
    if not source.exists():
        raise FileNotFoundError(f"Source file does not exist: {source}")
    
    if not source.is_file():
        raise ValueError(f"Source is not a file: {source}")
    
    logger.info(f"Moving file from {source} to {destination}")
    
    try:
        # Create destination directory if needed
        destination.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if destination exists and compare content
        if destination.exists():
            if _files_are_identical(source, destination):
                logger.info(f"File already exists with identical content: {destination}")
                # Remove source since destination is identical
                source.unlink()
                return
            else:
                raise FileExistsError(
                    f"Destination file exists with different content: {destination}"
                )
        
        # Move the file
        shutil.move(str(source), str(destination))
        logger.info(f"Successfully moved file to {destination}")
        
    except PermissionError as e:
        logger.error(f"Permission denied when moving {source} to {destination}: {e}")
        raise
    except OSError as e:
        logger.error(f"Error moving file {source} to {destination}: {e}")
        raise


def remove_empty_directory(path: Path, recursive: bool = True) -> None:
    """
    Remove directory if empty, optionally checking parent directories recursively.
    
    Args:
        path: Directory path to remove if empty
        recursive: If True, recursively check and remove empty parent directories
        
    Raises:
        PermissionError: If lacking permissions to remove directory
        OSError: For other file system errors
        
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
    """
    path = Path(path).resolve()
    
    if not path.exists():
        logger.debug(f"Directory does not exist: {path}")
        return
    
    if not path.is_dir():
        logger.warning(f"Path is not a directory: {path}")
        return
    
    try:
        # Check if directory is empty (no files or subdirectories)
        contents = list(path.iterdir())
        
        if not contents:
            # Directory is empty, remove it
            logger.info(f"Removing empty directory: {path}")
            path.rmdir()
            
            # Recursively check parent directory
            if recursive and path.parent != path:
                remove_empty_directory(path.parent, recursive=True)
        else:
            # Check if directory only contains placeholder files like .gitkeep
            non_placeholder_items = [
                item for item in contents 
                if item.name not in {'.gitkeep', '.gitignore'}
            ]
            
            if not non_placeholder_items:
                logger.info(f"Directory contains only placeholder files: {path}")
                # Don't remove directories with placeholders (Requirement 5.5)
            else:
                logger.debug(f"Directory is not empty: {path} (contains {len(contents)} items)")
                
    except PermissionError as e:
        logger.error(f"Permission denied when removing directory {path}: {e}")
        raise
    except OSError as e:
        logger.error(f"Error removing directory {path}: {e}")
        raise


def _files_are_identical(file1: Path, file2: Path) -> bool:
    """
    Check if two files have identical content (byte-for-byte comparison).
    
    Args:
        file1: First file path
        file2: Second file path
        
    Returns:
        True if files have identical content, False otherwise
    """
    try:
        # Compare file sizes first (quick check)
        if file1.stat().st_size != file2.stat().st_size:
            return False
        
        # Compare content byte-by-byte
        with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
            chunk_size = 8192
            while True:
                chunk1 = f1.read(chunk_size)
                chunk2 = f2.read(chunk_size)
                
                if chunk1 != chunk2:
                    return False
                
                if not chunk1:  # End of file
                    return True
                    
    except (OSError, IOError) as e:
        logger.error(f"Error comparing files {file1} and {file2}: {e}")
        return False
