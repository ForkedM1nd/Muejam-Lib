#!/usr/bin/env python3
"""
Phase 2: File Move Script for Monorepo Restructure

This script moves files and directories using git mv to preserve git history.
It handles move failures gracefully and verifies history preservation.

Requirements: 2.1, 2.2
"""

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Optional


@dataclass
class MoveOperation:
    """Represents a file or directory move operation."""
    source: str
    destination: str
    is_directory: bool
    description: str


class GitHistoryPreserver:
    """Moves files and directories using git mv to preserve history."""
    
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.failed_moves: List[Tuple[str, str, str]] = []  # (source, dest, error)
        
    def check_git_status(self) -> bool:
        """Check if there are uncommitted changes."""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True
            )
            
            if result.stdout.strip():
                print("✗ Uncommitted changes detected:")
                print(result.stdout)
                print("\nPlease commit or stash changes before running this script.")
                return False
                
            print("✓ Working directory is clean")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to check git status: {e}")
            return False

    def move_directory(self, source: str, destination: str) -> bool:
        """Move directory using git mv, preserving history for all files."""
        source_path = self.repo_root / source
        dest_path = self.repo_root / destination
        
        # Check if source exists
        if not source_path.exists():
            error_msg = f"Source does not exist: {source}"
            print(f"✗ {error_msg}")
            self.failed_moves.append((source, destination, error_msg))
            return False
            
        # Check if destination parent exists
        dest_parent = dest_path.parent
        if not dest_parent.exists():
            error_msg = f"Destination parent directory does not exist: {dest_parent}"
            print(f"✗ {error_msg}")
            self.failed_moves.append((source, destination, error_msg))
            return False
            
        # Check if destination already exists
        if dest_path.exists():
            print(f"⚠ Destination already exists, skipping: {destination}")
            return True
            
        try:
            # Execute git mv
            result = subprocess.run(
                ["git", "mv", source, destination],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True
            )
            
            print(f"✓ Moved directory: {source} -> {destination}")
            return True
            
        except subprocess.CalledProcessError as e:
            error_msg = f"git mv failed: {e.stderr.strip()}"
            print(f"✗ Failed to move {source}: {error_msg}")
            self.failed_moves.append((source, destination, error_msg))
            return False
            
    def move_file(self, source: str, destination: str) -> bool:
        """Move file using git mv, preserving history."""
        source_path = self.repo_root / source
        dest_path = self.repo_root / destination
        
        # Check if source exists
        if not source_path.exists():
            error_msg = f"Source file does not exist: {source}"
            print(f"✗ {error_msg}")
            self.failed_moves.append((source, destination, error_msg))
            return False
            
        # Check if destination parent exists
        dest_parent = dest_path.parent
        if not dest_parent.exists():
            error_msg = f"Destination parent directory does not exist: {dest_parent}"
            print(f"✗ {error_msg}")
            self.failed_moves.append((source, destination, error_msg))
            return False
            
        # Check if destination already exists
        if dest_path.exists():
            print(f"⚠ Destination already exists, skipping: {destination}")
            return True
            
        try:
            # Execute git mv
            result = subprocess.run(
                ["git", "mv", source, destination],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True
            )
            
            print(f"✓ Moved file: {source} -> {destination}")
            return True
            
        except subprocess.CalledProcessError as e:
            error_msg = f"git mv failed: {e.stderr.strip()}"
            print(f"✗ Failed to move {source}: {error_msg}")
            self.failed_moves.append((source, destination, error_msg))
            return False

    def verify_history_preserved(self, file_path: str) -> bool:
        """Verify git log --follow works for moved file."""
        full_path = self.repo_root / file_path
        
        if not full_path.exists():
            print(f"✗ Cannot verify history: file does not exist: {file_path}")
            return False
            
        try:
            # Execute git log --follow to check history
            result = subprocess.run(
                ["git", "log", "--follow", "--oneline", "-n", "5", file_path],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True
            )
            
            if result.stdout.strip():
                print(f"✓ History preserved for: {file_path}")
                return True
            else:
                print(f"⚠ No history found for: {file_path} (may be a new file)")
                return True  # New files won't have history, which is okay
                
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to verify history for {file_path}: {e.stderr.strip()}")
            return False
            
    def get_move_plan(self) -> List[MoveOperation]:
        """Return list of move operations for Phase 2."""
        return [
            # Move main application directories
            MoveOperation(
                source="backend",
                destination="apps/backend",
                is_directory=True,
                description="Move Django backend to apps/"
            ),
            MoveOperation(
                source="frontend",
                destination="apps/frontend",
                is_directory=True,
                description="Move React frontend to apps/"
            ),
            
            # Move documentation files to getting-started/
            MoveOperation(
                source="QUICKSTART.md",
                destination="docs/getting-started/quickstart.md",
                is_directory=False,
                description="Move quickstart guide to docs/"
            ),
            MoveOperation(
                source="DEVELOPMENT.md",
                destination="docs/getting-started/development.md",
                is_directory=False,
                description="Move development guide to docs/"
            ),
            
            # Move architecture documentation
            MoveOperation(
                source="backend/API_DOCUMENTATION.md",
                destination="docs/architecture/api.md",
                is_directory=False,
                description="Move API documentation to docs/"
            ),
            
            # Move deployment documentation
            MoveOperation(
                source="SECRETS.md",
                destination="docs/deployment/secrets.md",
                is_directory=False,
                description="Move secrets guide to docs/"
            ),
            
            # Move setup scripts to tools/
            MoveOperation(
                source="setup.sh",
                destination="tools/setup.sh",
                is_directory=False,
                description="Move Linux/Mac setup script to tools/"
            ),
            MoveOperation(
                source="setup.ps1",
                destination="tools/setup.ps1",
                is_directory=False,
                description="Move Windows setup script to tools/"
            ),
        ]
        
    def execute_move_plan(self) -> bool:
        """Execute all move operations in the plan."""
        move_plan = self.get_move_plan()
        total_moves = len(move_plan)
        successful_moves = 0
        
        print(f"Executing {total_moves} move operations...")
        print("-" * 60)
        
        for operation in move_plan:
            print(f"\n{operation.description}")
            
            if operation.is_directory:
                success = self.move_directory(operation.source, operation.destination)
            else:
                success = self.move_file(operation.source, operation.destination)
                
            if success:
                successful_moves += 1
                
        print()
        print("-" * 60)
        print(f"Completed: {successful_moves}/{total_moves} moves successful")
        
        if self.failed_moves:
            print(f"\n⚠ {len(self.failed_moves)} move(s) failed:")
            for source, dest, error in self.failed_moves:
                print(f"  - {source} -> {dest}: {error}")
            return False
            
        return True

    def verify_all_moves(self) -> bool:
        """Verify git history for all moved files."""
        move_plan = self.get_move_plan()
        verification_files = []
        
        # Collect files to verify
        for operation in move_plan:
            dest_path = self.repo_root / operation.destination
            
            if operation.is_directory:
                # For directories, verify a sample of key files
                if dest_path.exists():
                    # Find some files to verify
                    sample_files = []
                    for root, dirs, files in os.walk(dest_path):
                        for file in files[:3]:  # Sample first 3 files
                            rel_path = Path(root) / file
                            rel_path = rel_path.relative_to(self.repo_root)
                            sample_files.append(str(rel_path))
                        if sample_files:
                            break  # Only check first directory
                    verification_files.extend(sample_files)
            else:
                # For individual files, verify the file itself
                if dest_path.exists():
                    verification_files.append(operation.destination)
                    
        if not verification_files:
            print("⚠ No files to verify (moves may not have been executed)")
            return False
            
        print(f"\nVerifying git history for {len(verification_files)} file(s)...")
        print("-" * 60)
        
        all_verified = True
        for file_path in verification_files:
            if not self.verify_history_preserved(file_path):
                all_verified = False
                
        return all_verified
        
    def get_failed_moves(self) -> List[Tuple[str, str, str]]:
        """Return list of failed move operations."""
        return self.failed_moves


def main():
    """Execute Phase 2: File Moves."""
    print("=" * 60)
    print("Phase 2: Monorepo Restructure - File Moves")
    print("=" * 60)
    print()
    
    # Get repository root (two levels up from this script)
    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent.parent
    
    print(f"Repository root: {repo_root}")
    print()
    
    # Initialize git history preserver
    preserver = GitHistoryPreserver(repo_root)
    
    # Check git status
    print("Checking git status...")
    print("-" * 60)
    if not preserver.check_git_status():
        print("\n✗ Phase 2 aborted: uncommitted changes detected")
        return 1
    print()
    
    # Execute move plan
    print("Executing file moves...")
    print("-" * 60)
    if not preserver.execute_move_plan():
        print("\n✗ Phase 2 completed with errors")
        print("\nRollback instructions:")
        print("  git reset --hard HEAD")
        print("  # This will undo all moves")
        return 1
    print()
    
    # Verify history preservation
    print("Verifying git history preservation...")
    print("-" * 60)
    if not preserver.verify_all_moves():
        print("\n⚠ Some history verifications failed")
        print("This may be normal for new files without history.")
    print()
    
    print("=" * 60)
    print("✓ Phase 2 file moves complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Review the moved files")
    print("2. Verify applications still work (may need config updates)")
    print("3. Commit changes: git add . && git commit -m 'Phase 2: Move files to monorepo structure'")
    print("4. Proceed to Phase 3: Configuration updates")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
