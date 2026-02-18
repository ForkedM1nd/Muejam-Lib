"""
Documentation reference update utilities for reorganizing project structure.

This module provides functions for finding and updating file path references in
markdown documentation files, and for updating pytest configuration with new test paths.
"""

import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class FileReference:
    """Represents a file path reference in a documentation file."""
    
    def __init__(
        self,
        file: Path,
        line_number: int,
        original_text: str,
        referenced_path: str,
        is_relative: bool,
        reference_type: str
    ):
        """
        Initialize a FileReference.
        
        Args:
            file: Path to the file containing the reference
            line_number: Line number in the file (1-indexed)
            original_text: Original text containing the reference
            referenced_path: The file path being referenced
            is_relative: True if this is a relative path
            reference_type: Type of reference (markdown_link, inline_path, code_block)
        """
        self.file = file
        self.line_number = line_number
        self.original_text = original_text
        self.referenced_path = referenced_path
        self.is_relative = is_relative
        self.reference_type = reference_type
    
    def __repr__(self) -> str:
        return (
            f"FileReference(file={self.file.name}, "
            f"line={self.line_number}, "
            f"path='{self.referenced_path}', "
            f"type='{self.reference_type}')"
        )


def find_file_references(file: Path) -> List[FileReference]:
    """
    Find all file path references in a markdown file.
    
    Args:
        file: Path to markdown file to parse
        
    Returns:
        List of FileReference objects found in the file
        
    Raises:
        FileNotFoundError: If file doesn't exist
        
    Requirements: 2.5, 6.1, 6.2, 6.4
    """
    file = Path(file).resolve()
    
    if not file.exists():
        raise FileNotFoundError(f"File does not exist: {file}")
    
    logger.debug(f"Finding file references in {file}")
    
    references = []
    
    try:
        with open(file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for line_num, line in enumerate(lines, start=1):
            # Find markdown links: [text](path)
            markdown_links = _find_markdown_links(line)
            for link_text, link_path in markdown_links:
                if _is_file_path(link_path):
                    ref = FileReference(
                        file=file,
                        line_number=line_num,
                        original_text=f"[{link_text}]({link_path})",
                        referenced_path=link_path,
                        is_relative=_is_relative_path(link_path),
                        reference_type="markdown_link"
                    )
                    references.append(ref)
            
            # Find inline code paths: `path/to/file`
            inline_paths = _find_inline_code_paths(line)
            for path in inline_paths:
                if _is_file_path(path):
                    ref = FileReference(
                        file=file,
                        line_number=line_num,
                        original_text=f"`{path}`",
                        referenced_path=path,
                        is_relative=_is_relative_path(path),
                        reference_type="inline_path"
                    )
                    references.append(ref)
        
        logger.info(f"Found {len(references)} file references in {file}")
        return references
        
    except Exception as e:
        logger.error(f"Error finding references in {file}: {e}")
        raise


def _find_markdown_links(line: str) -> List[Tuple[str, str]]:
    """
    Find markdown links in a line.
    
    Returns:
        List of (link_text, link_path) tuples
    """
    # Pattern: [text](path)
    pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
    matches = re.findall(pattern, line)
    return matches


def _find_inline_code_paths(line: str) -> List[str]:
    """
    Find inline code that looks like file paths.
    
    Returns:
        List of potential file paths
    """
    # Pattern: `text`
    pattern = r'`([^`]+)`'
    matches = re.findall(pattern, line)
    
    # Filter to only paths (contain / or \)
    paths = [m for m in matches if '/' in m or '\\' in m]
    return paths


def _is_file_path(text: str) -> bool:
    """
    Check if text looks like a file path (not a URL).
    
    Args:
        text: Text to check
        
    Returns:
        True if text appears to be a file path, False if it's a URL or other reference
    """
    # Exclude URLs
    if text.startswith(('http://', 'https://', 'ftp://', 'mailto:')):
        return False
    
    # Exclude anchors
    if text.startswith('#'):
        return False
    
    # Must contain path separators or file extensions
    if '/' in text or '\\' in text:
        return True
    
    # Check for file extensions
    if '.' in text and text.split('.')[-1] in {'py', 'md', 'txt', 'ini', 'toml', 'yaml', 'yml', 'json'}:
        return True
    
    return False


def _is_relative_path(path: str) -> bool:
    """
    Check if path is relative (not absolute).
    
    Args:
        path: Path string to check
        
    Returns:
        True if path is relative
    """
    # Absolute paths start with / or drive letter (Windows)
    if path.startswith('/'):
        return False
    
    # Windows absolute paths: C:\ or C:/
    if len(path) >= 3 and path[1] == ':' and path[2] in ('/', '\\'):
        return False
    
    return True


def update_reference(
    ref: FileReference,
    path_mapping: Dict[str, str]
) -> Optional[FileReference]:
    """
    Update file reference to new location based on path mapping.
    
    Args:
        ref: FileReference to update
        path_mapping: Dict mapping old paths to new paths
        
    Returns:
        New FileReference with updated path, or None if no update needed
        
    Requirements: 2.5, 6.1, 6.2, 6.4
    """
    logger.debug(f"Checking reference for update: {ref.referenced_path}")
    
    # Try to find matching path in mapping
    updated_path = None
    
    for old_path, new_path in path_mapping.items():
        if _path_matches(ref.referenced_path, old_path):
            updated_path = _replace_path(ref.referenced_path, old_path, new_path)
            logger.info(f"Updating reference: '{ref.referenced_path}' -> '{updated_path}'")
            break
    
    if not updated_path:
        logger.debug(f"No update needed for reference: {ref.referenced_path}")
        return None
    
    # Generate new reference text
    if ref.reference_type == "markdown_link":
        # Extract link text from original
        match = re.match(r'\[([^\]]+)\]\([^\)]+\)', ref.original_text)
        if match:
            link_text = match.group(1)
            new_text = f"[{link_text}]({updated_path})"
        else:
            new_text = f"[]({updated_path})"
    elif ref.reference_type == "inline_path":
        new_text = f"`{updated_path}`"
    else:
        new_text = updated_path
    
    return FileReference(
        file=ref.file,
        line_number=ref.line_number,
        original_text=new_text,
        referenced_path=updated_path,
        is_relative=ref.is_relative,
        reference_type=ref.reference_type
    )


def _path_matches(ref_path: str, old_path: str) -> bool:
    """
    Check if reference path matches old path.
    
    Args:
        ref_path: Path from reference
        old_path: Old path to match against
        
    Returns:
        True if paths match
    """
    # Normalize paths for comparison
    ref_normalized = Path(ref_path).as_posix()
    old_normalized = Path(old_path).as_posix()
    
    # Exact match
    if ref_normalized == old_normalized:
        return True
    
    # Check if ref_path ends with old_path (for relative references)
    if ref_normalized.endswith(old_normalized):
        return True
    
    # Check if old_path is a prefix of ref_path
    if ref_normalized.startswith(old_normalized + '/'):
        return True
    
    return False


def _replace_path(ref_path: str, old_path: str, new_path: str) -> str:
    """
    Replace old path with new path in reference.
    
    Args:
        ref_path: Current reference path
        old_path: Old path to replace
        new_path: New path to use
        
    Returns:
        Updated reference path
    """
    # Normalize paths
    ref_normalized = Path(ref_path).as_posix()
    old_normalized = Path(old_path).as_posix()
    new_normalized = Path(new_path).as_posix()
    
    # Exact match
    if ref_normalized == old_normalized:
        return new_normalized
    
    # Replace prefix
    if ref_normalized.startswith(old_normalized + '/'):
        return new_normalized + ref_normalized[len(old_normalized):]
    
    # Replace suffix (for relative paths)
    if ref_normalized.endswith(old_normalized):
        prefix = ref_normalized[:-len(old_normalized)]
        return prefix + new_normalized
    
    return ref_path


def update_pytest_config(config_file: Path, new_test_path: str) -> None:
    """
    Update pytest configuration file with new test directory path.
    
    Args:
        config_file: Path to pytest.ini or pyproject.toml
        new_test_path: New test directory path to configure
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        
    Requirements: 3.1, 3.2
    """
    config_file = Path(config_file).resolve()
    
    if not config_file.exists():
        raise FileNotFoundError(f"Config file does not exist: {config_file}")
    
    logger.info(f"Updating pytest config in {config_file}")
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        updated = False
        
        if config_file.name == 'pytest.ini':
            updated = _update_pytest_ini(lines, new_test_path)
        elif config_file.name == 'pyproject.toml':
            updated = _update_pyproject_toml(lines, new_test_path)
        else:
            logger.warning(f"Unknown config file type: {config_file.name}")
            return
        
        if updated:
            with open(config_file, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            logger.info(f"Updated pytest config with test path: {new_test_path}")
        else:
            logger.debug(f"No updates needed in {config_file}")
            
    except Exception as e:
        logger.error(f"Error updating pytest config {config_file}: {e}")
        raise


def _update_pytest_ini(lines: List[str], new_test_path: str) -> bool:
    """
    Update pytest.ini file with new test path.
    
    Args:
        lines: Lines from pytest.ini file (modified in place)
        new_test_path: New test directory path
        
    Returns:
        True if any updates were made
    """
    updated = False
    
    for i, line in enumerate(lines):
        # Update testpaths setting
        if line.strip().startswith('testpaths'):
            # Replace the value
            lines[i] = f"testpaths = {new_test_path}\n"
            updated = True
            logger.debug(f"Updated testpaths to: {new_test_path}")
        
        # Update python_files pattern if it references old path
        elif line.strip().startswith('python_files'):
            # Keep the pattern but note the change
            logger.debug(f"Found python_files setting: {line.strip()}")
    
    return updated


def _update_pyproject_toml(lines: List[str], new_test_path: str) -> bool:
    """
    Update pyproject.toml file with new test path.
    
    Args:
        lines: Lines from pyproject.toml file (modified in place)
        new_test_path: New test directory path
        
    Returns:
        True if any updates were made
    """
    updated = False
    in_pytest_section = False
    
    for i, line in enumerate(lines):
        # Check if we're in the pytest section
        if line.strip().startswith('[tool.pytest'):
            in_pytest_section = True
            continue
        
        # Check if we've left the pytest section
        if in_pytest_section and line.strip().startswith('['):
            in_pytest_section = False
        
        # Update testpaths in pytest section
        if in_pytest_section and 'testpaths' in line:
            # Replace the value
            indent = len(line) - len(line.lstrip())
            lines[i] = ' ' * indent + f'testpaths = ["{new_test_path}"]\n'
            updated = True
            logger.debug(f"Updated testpaths to: {new_test_path}")
    
    return updated
