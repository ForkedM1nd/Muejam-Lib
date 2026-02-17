#!/usr/bin/env python3
"""
Phase 4: Cleanup Script for Monorepo Restructure

This script removes build artifacts, AI-generated documentation, and temporary
root-level files from the repository.

Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 4.1, 4.2, 4.3, 4.4, 4.5, 6.1, 6.2, 6.3
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import List, Set


class BuildArtifactCleaner:
    """Removes build artifacts and updates .gitignore."""
    
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.gitignore_path = repo_root / ".gitignore"
        
    def find_artifacts(self) -> List[Path]:
        """Find all build artifacts in repository."""
        artifact_patterns = [
            ".coverage",
            ".hypothesis",
            "htmlcov",
            "venv",
            "node_modules",
            "dist",
            "build",
            "__pycache__",
            "*.pyc",
            ".pytest_cache"
        ]
        
        artifacts = []
        
        # Walk through repository
        for root, dirs, files in os.walk(self.repo_root):
            # Skip .git directory
            if '.git' in root:
                continue
                
            # Check directories
            for dir_name in dirs:
                if dir_name in artifact_patterns or dir_name.startswith('.hypothesis'):
                    artifact_path = Path(root) / dir_name
                    artifacts.append(artifact_path)
                    
            # Check files
            for file_name in files:
                if file_name in artifact_patterns or file_name.endswith('.pyc'):
                    artifact_path = Path(root) / file_name
                    artifacts.append(artifact_path)
                    
        return artifacts
        
    def remove_artifacts(self, artifacts: List[Path]) -> None:
        """Remove artifacts using git rm or regular deletion."""
        if not artifacts:
            print("✓ No build artifacts found")
            return
            
        print(f"Found {len(artifacts)} build artifacts to remove")
        
        for artifact in artifacts:
            try:
                # Try git rm first (for tracked files)
                result = subprocess.run(
                    ["git", "rm", "-rf", str(artifact)],
                    cwd=self.repo_root,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    print(f"  ✓ Removed (git): {artifact.relative_to(self.repo_root)}")
                else:
                    # If git rm fails, try regular deletion (for untracked files)
                    if artifact.is_file():
                        artifact.unlink()
                        print(f"  ✓ Removed (untracked): {artifact.relative_to(self.repo_root)}")
                    elif artifact.is_dir():
                        import shutil
                        shutil.rmtree(artifact)
                        print(f"  ✓ Removed (untracked): {artifact.relative_to(self.repo_root)}")
                        
            except Exception as e:
                print(f"  ✗ Failed to remove {artifact.relative_to(self.repo_root)}: {e}")
                
    def update_gitignore(self) -> None:
        """Ensure .gitignore includes all artifact patterns."""
        required_patterns = {
            ".coverage",
            ".hypothesis/",
            "htmlcov/",
            "venv/",
            "node_modules/",
            "dist/",
            "build/",
            "__pycache__/",
            "*.pyc",
            ".pytest_cache/"
        }
        
        if self.gitignore_path.exists():
            current_content = self.gitignore_path.read_text()
            current_lines = set(line.strip() for line in current_content.splitlines())
        else:
            current_content = ""
            current_lines = set()
            
        missing_patterns = required_patterns - current_lines
        
        if missing_patterns:
            if current_content and not current_content.endswith('\n'):
                current_content += '\n'
            
            current_content += "\n# Build artifacts (updated by cleanup script)\n"
            for pattern in sorted(missing_patterns):
                current_content += f"{pattern}\n"
                
            self.gitignore_path.write_text(current_content)
            print(f"✓ Added {len(missing_patterns)} patterns to .gitignore")
        else:
            print("✓ .gitignore already contains all required patterns")
            
    def verify_artifacts_ignored(self) -> bool:
        """Verify all artifact patterns are in .gitignore."""
        required_patterns = {
            ".coverage",
            ".hypothesis/",
            "htmlcov/",
            "venv/",
            "node_modules/",
            "dist/",
            "build/"
        }
        
        if not self.gitignore_path.exists():
            print("✗ .gitignore file not found")
            return False
            
        content = self.gitignore_path.read_text()
        lines = set(line.strip() for line in content.splitlines())
        
        missing = required_patterns - lines
        if missing:
            print(f"✗ Missing patterns in .gitignore: {missing}")
            return False
            
        print("✓ All artifact patterns present in .gitignore")
        return True


class DocumentationCleaner:
    """Removes AI-generated checkpoint and verification files."""
    
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        
        # Essential documentation files that should be preserved
        self.essential_docs = {
            "API_DOCUMENTATION.md",
            "AUTHENTICATION.md",
            "README.md",
            "CONTRIBUTING.md",
            "LICENSE",
            "QUICKSTART.md",
            "DEVELOPMENT.md",
            "SECRETS.md"
        }
        
        # AI-generated file patterns to remove
        self.ai_patterns = [
            "CHECKPOINT",
            "VERIFICATION",
            "FINAL",
            "IMPLEMENTATION",
            "SUMMARY",
            "AUTH_COMPLETE",
            "AUTH_QUICK_START",
            "AUTH_TEST_CHECKLIST"
        ]
        
    def find_ai_footprints(self) -> List[Path]:
        """Find all AI-generated documentation files."""
        ai_files = []
        
        for root, dirs, files in os.walk(self.repo_root):
            # Skip .git and node_modules
            if '.git' in root or 'node_modules' in root:
                continue
                
            for file_name in files:
                if not file_name.endswith('.md'):
                    continue
                    
                file_path = Path(root) / file_name
                
                # Skip essential documentation
                if file_name in self.essential_docs:
                    continue
                    
                # Check if file matches AI patterns
                if self._is_ai_generated(file_name):
                    ai_files.append(file_path)
                    
        return ai_files
        
    def _is_ai_generated(self, filename: str) -> bool:
        """Check if filename matches AI-generated patterns."""
        filename_upper = filename.upper()
        
        # Check for specific AI-generated file names
        if filename in ["AUTH_COMPLETE.md", "AUTH_QUICK_START.md", "AUTH_TEST_CHECKLIST.md"]:
            return True
            
        # Check for pattern combinations
        for pattern in self.ai_patterns:
            if pattern in filename_upper:
                return True
                
        return False
        
    def is_essential_doc(self, file_path: Path) -> bool:
        """Determine if documentation file should be preserved."""
        return file_path.name in self.essential_docs
        
    def remove_ai_footprints(self, files: List[Path]) -> None:
        """Remove AI-generated files using git rm."""
        if not files:
            print("✓ No AI-generated documentation found")
            return
            
        print(f"Found {len(files)} AI-generated documentation files to remove")
        
        for file_path in files:
            try:
                # Try git rm first
                result = subprocess.run(
                    ["git", "rm", "-f", str(file_path)],
                    cwd=self.repo_root,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    print(f"  ✓ Removed: {file_path.relative_to(self.repo_root)}")
                else:
                    # If git rm fails, try regular deletion
                    if file_path.exists():
                        file_path.unlink()
                        print(f"  ✓ Removed (untracked): {file_path.relative_to(self.repo_root)}")
                        
            except Exception as e:
                print(f"  ✗ Failed to remove {file_path.relative_to(self.repo_root)}: {e}")
                
    def verify_no_footprints(self) -> bool:
        """Verify no checkpoint or verification files remain."""
        remaining = self.find_ai_footprints()
        
        if remaining:
            print(f"✗ Found {len(remaining)} AI-generated files still present:")
            for file_path in remaining:
                print(f"  - {file_path.relative_to(self.repo_root)}")
            return False
            
        print("✓ No AI-generated documentation files remain")
        return True


class RootLevelCleaner:
    """Removes temporary root-level files."""
    
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        
        # Files to remove from root
        self.temp_files = [
            "prompt.txt",
            "doc.txt",
            "PROJECT_STATUS.md"
        ]
        
        # Essential files that must remain at root
        # Note: CONTRIBUTING.md, LICENSE, and .env.example will be created in Phase 5
        self.essential_files = {
            "README.md",
            "docker-compose.yml",
            ".gitignore"
        }
        
    def remove_temp_files(self) -> None:
        """Remove temporary root-level files."""
        removed_count = 0
        
        for file_name in self.temp_files:
            file_path = self.repo_root / file_name
            
            if not file_path.exists():
                continue
                
            try:
                # Try git rm first
                result = subprocess.run(
                    ["git", "rm", "-f", str(file_path)],
                    cwd=self.repo_root,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    print(f"  ✓ Removed: {file_name}")
                    removed_count += 1
                else:
                    # If git rm fails, try regular deletion
                    if file_path.exists():
                        file_path.unlink()
                        print(f"  ✓ Removed (untracked): {file_name}")
                        removed_count += 1
                        
            except Exception as e:
                print(f"  ✗ Failed to remove {file_name}: {e}")
                
        if removed_count == 0:
            print("✓ No temporary files found to remove")
        else:
            print(f"✓ Removed {removed_count} temporary files")
            
    def verify_essential_files(self) -> bool:
        """Verify essential files remain at root level."""
        missing = []
        
        for file_name in self.essential_files:
            file_path = self.repo_root / file_name
            if not file_path.exists():
                missing.append(file_name)
                
        if missing:
            print(f"✗ Missing essential files: {missing}")
            return False
            
        print("✓ All essential root-level files present")
        return True
        
    def verify_cleanup_complete(self) -> bool:
        """Verify cleanup is complete."""
        # Check that temp files are gone
        remaining = []
        for file_name in self.temp_files:
            file_path = self.repo_root / file_name
            if file_path.exists():
                remaining.append(file_name)
                
        if remaining:
            print(f"✗ Temporary files still present: {remaining}")
            return False
            
        print("✓ All temporary files removed")
        return True


def main():
    """Execute Phase 4: Cleanup."""
    print("=" * 60)
    print("Phase 4: Monorepo Restructure - Cleanup")
    print("=" * 60)
    print()
    
    # Get repository root
    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent.parent
    
    print(f"Repository root: {repo_root}")
    print()
    
    # Remove build artifacts
    print("Removing build artifacts...")
    print("-" * 60)
    artifact_cleaner = BuildArtifactCleaner(repo_root)
    artifacts = artifact_cleaner.find_artifacts()
    artifact_cleaner.remove_artifacts(artifacts)
    print()
    
    # Update .gitignore
    print("Updating .gitignore...")
    print("-" * 60)
    artifact_cleaner.update_gitignore()
    print()
    
    # Verify .gitignore
    print("Verifying .gitignore...")
    print("-" * 60)
    if not artifact_cleaner.verify_artifacts_ignored():
        print("\n✗ .gitignore verification failed")
        return 1
    print()
    
    # Remove AI-generated documentation
    print("Removing AI-generated documentation...")
    print("-" * 60)
    doc_cleaner = DocumentationCleaner(repo_root)
    ai_files = doc_cleaner.find_ai_footprints()
    doc_cleaner.remove_ai_footprints(ai_files)
    print()
    
    # Verify no AI footprints remain
    print("Verifying AI documentation removed...")
    print("-" * 60)
    if not doc_cleaner.verify_no_footprints():
        print("\n✗ AI documentation verification failed")
        return 1
    print()
    
    # Remove temporary root-level files
    print("Removing temporary root-level files...")
    print("-" * 60)
    root_cleaner = RootLevelCleaner(repo_root)
    root_cleaner.remove_temp_files()
    print()
    
    # Verify essential files remain
    print("Verifying essential files...")
    print("-" * 60)
    if not root_cleaner.verify_essential_files():
        print("\n✗ Essential files verification failed")
        return 1
    print()
    
    # Verify cleanup complete
    print("Verifying cleanup complete...")
    print("-" * 60)
    if not root_cleaner.verify_cleanup_complete():
        print("\n✗ Cleanup verification failed")
        return 1
    print()
    
    print("=" * 60)
    print("✓ Phase 4 cleanup complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Review the cleanup results")
    print("2. Commit changes: git add . && git commit -m 'Phase 4: Remove build artifacts and AI-generated docs'")
    print("3. Proceed to Phase 5: Documentation updates")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
