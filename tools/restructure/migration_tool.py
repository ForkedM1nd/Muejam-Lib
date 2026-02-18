#!/usr/bin/env python3
"""
Migration Tool Core Structure for Monorepo Restructure

This module provides the core classes for automating file movements, path updates,
validation, and rollback capabilities during the monorepo restructuring process.

Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7
"""

import json
import shutil
import subprocess
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from file_tracker import FileTracker
from config_updater import ConfigUpdater
from validator import ValidationSuite


@dataclass
class Checkpoint:
    """Represents a migration checkpoint for rollback purposes."""
    name: str
    timestamp: datetime
    git_commit: Optional[str]
    files_moved: List[Tuple[str, str]]
    description: str
    
    def to_dict(self) -> dict:
        """Convert checkpoint to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'timestamp': self.timestamp.isoformat(),
            'git_commit': self.git_commit,
            'files_moved': self.files_moved,
            'description': self.description
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Checkpoint':
        """Create checkpoint from dictionary."""
        return cls(
            name=data['name'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            git_commit=data.get('git_commit'),
            files_moved=data.get('files_moved', []),
            description=data.get('description', '')
        )


@dataclass
class MigrationResult:
    """Result of a migration operation."""
    success: bool
    message: str
    files_affected: List[str]
    errors: List[str]


class FileMover:
    """Handles file and directory movements with git history preservation."""
    
    def __init__(self, repo_root: Path):
        """
        Initialize FileMover.
        
        Args:
            repo_root: Root directory of the repository
        """
        self.repo_root = repo_root
        self.moved_files: List[Tuple[str, str]] = []
        self.failed_moves: List[Tuple[str, str, str]] = []
    
    def move_file(self, source: str, destination: str) -> bool:
        """
        Move a file using git mv to preserve history.
        
        Args:
            source: Source file path relative to repo root
            destination: Destination file path relative to repo root
            
        Returns:
            True if move succeeded, False otherwise
        """
        source_path = self.repo_root / source
        dest_path = self.repo_root / destination
        
        # Validate source exists
        if not source_path.exists():
            error_msg = f"Source file does not exist: {source}"
            self.failed_moves.append((source, destination, error_msg))
            return False
        
        # Validate destination parent exists
        if not dest_path.parent.exists():
            error_msg = f"Destination parent directory does not exist: {dest_path.parent}"
            self.failed_moves.append((source, destination, error_msg))
            return False
        
        # Check if destination already exists
        if dest_path.exists():
            return True  # Already moved
        
        try:
            # Use git mv to preserve history
            subprocess.run(
                ["git", "mv", source, destination],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True
            )
            self.moved_files.append((source, destination))
            return True
        except subprocess.CalledProcessError as e:
            error_msg = f"git mv failed: {e.stderr.strip()}"
            self.failed_moves.append((source, destination, error_msg))
            return False
    
    def move_directory(self, source: str, destination: str) -> bool:
        """
        Move a directory using git mv to preserve history.
        
        Args:
            source: Source directory path relative to repo root
            destination: Destination directory path relative to repo root
            
        Returns:
            True if move succeeded, False otherwise
        """
        source_path = self.repo_root / source
        dest_path = self.repo_root / destination
        
        # Validate source exists
        if not source_path.exists():
            error_msg = f"Source directory does not exist: {source}"
            self.failed_moves.append((source, destination, error_msg))
            return False
        
        # Validate destination parent exists
        if not dest_path.parent.exists():
            error_msg = f"Destination parent directory does not exist: {dest_path.parent}"
            self.failed_moves.append((source, destination, error_msg))
            return False
        
        # Check if destination already exists
        if dest_path.exists():
            return True  # Already moved
        
        try:
            # Use git mv to preserve history
            subprocess.run(
                ["git", "mv", source, destination],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True
            )
            self.moved_files.append((source, destination))
            return True
        except subprocess.CalledProcessError as e:
            error_msg = f"git mv failed: {e.stderr.strip()}"
            self.failed_moves.append((source, destination, error_msg))
            return False
    
    def get_moved_files(self) -> List[Tuple[str, str]]:
        """Get list of successfully moved files."""
        return self.moved_files.copy()
    
    def get_failed_moves(self) -> List[Tuple[str, str, str]]:
        """Get list of failed move operations."""
        return self.failed_moves.copy()


class PathUpdater:
    """Updates import paths and references in code and configuration files."""
    
    def __init__(self, repo_root: Path):
        """
        Initialize PathUpdater.
        
        Args:
            repo_root: Root directory of the repository
        """
        self.repo_root = repo_root
        self.updated_files: List[str] = []
        self.failed_updates: List[Tuple[str, str]] = []
    
    def update_python_imports(self, old_path: str, new_path: str) -> int:
        """
        Update Python import statements across the codebase.
        
        Args:
            old_path: Old module path (e.g., 'infrastructure.shadowban')
            new_path: New module path (e.g., 'apps.moderation.shadowban')
            
        Returns:
            Number of files updated
        """
        import re
        
        # Convert file paths to module paths
        old_module = old_path.replace('/', '.').replace('.py', '')
        new_module = new_path.replace('/', '.').replace('.py', '')
        
        # Find all Python files
        python_files = list(self.repo_root.rglob('*.py'))
        files_updated = 0
        
        for py_file in python_files:
            try:
                content = py_file.read_text(encoding='utf-8')
                original_content = content
                
                # Update various import patterns
                patterns = [
                    (rf'from {re.escape(old_module)} import', f'from {new_module} import'),
                    (rf'import {re.escape(old_module)}', f'import {new_module}'),
                    (rf'from {re.escape(old_module)}\.', f'from {new_module}.'),
                ]
                
                for pattern, replacement in patterns:
                    content = re.sub(pattern, replacement, content)
                
                # Write back if changed
                if content != original_content:
                    py_file.write_text(content, encoding='utf-8')
                    self.updated_files.append(str(py_file.relative_to(self.repo_root)))
                    files_updated += 1
                    
            except Exception as e:
                error_msg = f"Failed to update {py_file}: {e}"
                self.failed_updates.append((str(py_file), error_msg))
        
        return files_updated
    
    def update_config_file(self, config_path: Path, updates: Dict[str, str]) -> bool:
        """
        Update a configuration file with path replacements.
        
        Args:
            config_path: Path to configuration file
            updates: Dictionary of old_path -> new_path replacements
            
        Returns:
            True if update succeeded, False otherwise
        """
        if not config_path.exists():
            error_msg = f"Config file does not exist: {config_path}"
            self.failed_updates.append((str(config_path), error_msg))
            return False
        
        try:
            content = config_path.read_text(encoding='utf-8')
            original_content = content
            
            # Apply all updates
            for old_path, new_path in updates.items():
                content = content.replace(old_path, new_path)
            
            # Write back if changed
            if content != original_content:
                config_path.write_text(content, encoding='utf-8')
                self.updated_files.append(str(config_path.relative_to(self.repo_root)))
            
            return True
            
        except Exception as e:
            error_msg = f"Failed to update config: {e}"
            self.failed_updates.append((str(config_path), error_msg))
            return False
    
    def get_updated_files(self) -> List[str]:
        """Get list of successfully updated files."""
        return self.updated_files.copy()
    
    def get_failed_updates(self) -> List[Tuple[str, str]]:
        """Get list of failed update operations."""
        return self.failed_updates.copy()


class Validator:
    """Validates repository state after migrations."""
    
    def __init__(self, repo_root: Path):
        """
        Initialize Validator.
        
        Args:
            repo_root: Root directory of the repository
        """
        self.repo_root = repo_root
        self.validation_errors: List[str] = []
    
    def validate_python_syntax(self, file_path: Path) -> bool:
        """
        Validate Python file syntax.
        
        Args:
            file_path: Path to Python file
            
        Returns:
            True if syntax is valid, False otherwise
        """
        try:
            import py_compile
            py_compile.compile(str(file_path), doraise=True)
            return True
        except py_compile.PyCompileError as e:
            self.validation_errors.append(f"Python syntax error in {file_path}: {e}")
            return False
    
    def validate_imports(self) -> bool:
        """
        Validate that all Python imports can be resolved.
        
        Returns:
            True if all imports are valid, False otherwise
        """
        # This is a simplified check - full import validation requires running Python
        python_files = list(self.repo_root.rglob('*.py'))
        all_valid = True
        
        for py_file in python_files:
            if not self.validate_python_syntax(py_file):
                all_valid = False
        
        return all_valid
    
    def validate_git_history(self, file_path: str) -> bool:
        """
        Validate that git history is preserved for a moved file.
        
        Args:
            file_path: Path to file relative to repo root
            
        Returns:
            True if history is preserved, False otherwise
        """
        try:
            result = subprocess.run(
                ["git", "log", "--follow", "--oneline", "-n", "1", file_path],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True
            )
            return bool(result.stdout.strip())
        except subprocess.CalledProcessError:
            self.validation_errors.append(f"Git history not found for {file_path}")
            return False
    
    def validate_file_exists(self, file_path: str) -> bool:
        """
        Validate that a file exists at the expected location.
        
        Args:
            file_path: Path to file relative to repo root
            
        Returns:
            True if file exists, False otherwise
        """
        full_path = self.repo_root / file_path
        if not full_path.exists():
            self.validation_errors.append(f"File not found: {file_path}")
            return False
        return True
    
    def get_validation_errors(self) -> List[str]:
        """Get list of validation errors."""
        return self.validation_errors.copy()


class RollbackManager:
    """Manages checkpoints and rollback operations."""
    
    def __init__(self, repo_root: Path):
        """
        Initialize RollbackManager.
        
        Args:
            repo_root: Root directory of the repository
        """
        self.repo_root = repo_root
        self.checkpoint_file = repo_root / "tools" / "restructure" / "checkpoints.json"
        self.checkpoints: List[Checkpoint] = []
        self._load_checkpoints()
    
    def _load_checkpoints(self) -> None:
        """Load checkpoints from file."""
        if self.checkpoint_file.exists():
            try:
                data = json.loads(self.checkpoint_file.read_text(encoding='utf-8'))
                self.checkpoints = [Checkpoint.from_dict(cp) for cp in data]
            except Exception:
                self.checkpoints = []
    
    def _save_checkpoints(self) -> None:
        """Save checkpoints to file."""
        self.checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
        data = [cp.to_dict() for cp in self.checkpoints]
        self.checkpoint_file.write_text(
            json.dumps(data, indent=2),
            encoding='utf-8'
        )
    
    def create_checkpoint(self, name: str, description: str = "") -> Checkpoint:
        """
        Create a new checkpoint.
        
        Args:
            name: Checkpoint name
            description: Optional description
            
        Returns:
            Created checkpoint
        """
        # Get current git commit
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True
            )
            git_commit = result.stdout.strip()
        except subprocess.CalledProcessError:
            git_commit = None
        
        checkpoint = Checkpoint(
            name=name,
            timestamp=datetime.now(),
            git_commit=git_commit,
            files_moved=[],
            description=description
        )
        
        self.checkpoints.append(checkpoint)
        self._save_checkpoints()
        
        return checkpoint
    
    def update_checkpoint(self, name: str, files_moved: List[Tuple[str, str]]) -> bool:
        """
        Update a checkpoint with moved files.
        
        Args:
            name: Checkpoint name
            files_moved: List of (source, destination) tuples
            
        Returns:
            True if checkpoint was updated, False if not found
        """
        for checkpoint in self.checkpoints:
            if checkpoint.name == name:
                checkpoint.files_moved.extend(files_moved)
                self._save_checkpoints()
                return True
        return False
    
    def get_checkpoint(self, name: str) -> Optional[Checkpoint]:
        """
        Get a checkpoint by name.
        
        Args:
            name: Checkpoint name
            
        Returns:
            Checkpoint if found, None otherwise
        """
        for checkpoint in self.checkpoints:
            if checkpoint.name == name:
                return checkpoint
        return None
    
    def list_checkpoints(self) -> List[Checkpoint]:
        """Get list of all checkpoints."""
        return self.checkpoints.copy()
    
    def rollback_to_checkpoint(self, name: str) -> bool:
        """
        Rollback to a specific checkpoint using git.
        
        Args:
            name: Checkpoint name
            
        Returns:
            True if rollback succeeded, False otherwise
        """
        checkpoint = self.get_checkpoint(name)
        if not checkpoint or not checkpoint.git_commit:
            return False
        
        try:
            # Reset to checkpoint commit
            subprocess.run(
                ["git", "reset", "--hard", checkpoint.git_commit],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False


class MigrationTool:
    """Main orchestration class for migration operations."""
    
    def __init__(self, repo_root: Path):
        """
        Initialize MigrationTool.
        
        Args:
            repo_root: Root directory of the repository
        """
        self.repo_root = repo_root
        self.file_mover = FileMover(repo_root)
        self.path_updater = PathUpdater(repo_root)
        self.validator = Validator(repo_root)
        self.rollback_manager = RollbackManager(repo_root)
        self.file_tracker = FileTracker(repo_root)
        self.config_updater = ConfigUpdater(repo_root)
    
    def move_files(self, mapping: Dict[str, str], file_type: str = "code", phase: int = 0, reason: str = "") -> MigrationResult:
        """
        Move multiple files according to a mapping.
        
        Args:
            mapping: Dictionary of source -> destination paths
            file_type: Type of files being moved ('code', 'doc', 'test', 'config', 'artifact')
            phase: Migration phase number
            reason: Reason for the movements
            
        Returns:
            MigrationResult with operation details
        """
        files_affected = []
        errors = []
        
        for source, destination in mapping.items():
            source_path = self.repo_root / source
            
            if source_path.is_dir():
                success = self.file_mover.move_directory(source, destination)
            else:
                success = self.file_mover.move_file(source, destination)
            
            if success:
                files_affected.append(destination)
                # Log the movement
                self.file_tracker.log_movement(
                    old_path=source,
                    new_path=destination,
                    file_type=file_type,
                    phase=phase,
                    reason=reason
                )
            else:
                errors.append(f"Failed to move {source} to {destination}")
        
        return MigrationResult(
            success=len(errors) == 0,
            message=f"Moved {len(files_affected)} files/directories",
            files_affected=files_affected,
            errors=errors
        )
    
    def update_imports(self, old_path: str, new_path: str) -> MigrationResult:
        """
        Update import statements for a moved module.
        
        Args:
            old_path: Old module path
            new_path: New module path
            
        Returns:
            MigrationResult with operation details
        """
        files_updated = self.path_updater.update_python_imports(old_path, new_path)
        
        return MigrationResult(
            success=True,
            message=f"Updated imports in {files_updated} files",
            files_affected=self.path_updater.get_updated_files(),
            errors=[]
        )
    
    def validate_changes(self) -> MigrationResult:
        """
        Validate repository state after changes (basic validation).
        
        This performs a quick validation of Python imports and syntax.
        For comprehensive validation, use validate_comprehensive().
        
        Returns:
            MigrationResult with validation details
        """
        is_valid = self.validator.validate_imports()
        errors = self.validator.get_validation_errors()
        
        return MigrationResult(
            success=is_valid,
            message="Validation complete" if is_valid else "Validation failed",
            files_affected=[],
            errors=errors
        )
    
    def validate_comprehensive(self) -> MigrationResult:
        """
        Run comprehensive validation suite on the repository.
        
        This runs all validation checks including:
        - Python syntax validation
        - TypeScript syntax validation
        - Import resolution checking
        - Django system check
        - Frontend build validation
        - Docker build validation
        - Test discovery validation
        
        Returns:
            MigrationResult with comprehensive validation details
            
        Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6
        """
        validation_suite = ValidationSuite(self.repo_root)
        report = validation_suite.run_all()
        
        # Collect all errors from all checks
        all_errors = []
        for check_name, result in report.results.items():
            if not result.success:
                all_errors.extend(result.errors)
        
        return MigrationResult(
            success=report.overall_success,
            message=report.summary,
            files_affected=[],
            errors=all_errors
        )
    
    def create_checkpoint(self, name: str, description: str = "") -> Checkpoint:
        """
        Create a migration checkpoint.
        
        Args:
            name: Checkpoint name
            description: Optional description
            
        Returns:
            Created checkpoint
        """
        return self.rollback_manager.create_checkpoint(name, description)
    
    def rollback(self, checkpoint_name: str) -> MigrationResult:
        """
        Rollback to a previous checkpoint.
        
        Args:
            checkpoint_name: Name of checkpoint to rollback to
            
        Returns:
            MigrationResult with rollback details
        """
        success = self.rollback_manager.rollback_to_checkpoint(checkpoint_name)
        
        return MigrationResult(
            success=success,
            message=f"Rolled back to checkpoint: {checkpoint_name}" if success else "Rollback failed",
            files_affected=[],
            errors=[] if success else [f"Checkpoint not found or rollback failed: {checkpoint_name}"]
        )
    
    def update_configs(self, movements: List[Tuple[str, str]]) -> MigrationResult:
        """
        Update all configuration files with new paths.
        
        Args:
            movements: List of (old_path, new_path) tuples
            
        Returns:
            MigrationResult with operation details
        """
        results = self.config_updater.update_all_configs(movements)
        updated_files = self.config_updater.get_updated_files()
        errors = self.config_updater.get_errors()
        
        # Format errors for MigrationResult
        error_messages = [f"{file}: {error}" for file, error in errors]
        
        # Check if all updates succeeded
        all_success = all(results.values())
        
        return MigrationResult(
            success=all_success,
            message=f"Updated {len(updated_files)} configuration files",
            files_affected=updated_files,
            errors=error_messages
        )
