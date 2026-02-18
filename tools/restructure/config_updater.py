#!/usr/bin/env python3
"""
Configuration Updater for Monorepo Restructure

This module provides methods to update various configuration files to reflect
new paths after file movements during the monorepo restructuring process.

Requirements: 9.2, 9.3, 9.4, 9.5, 9.6
"""

import re
import yaml
from pathlib import Path
from typing import List, Dict, Optional, Tuple


class ConfigUpdater:
    """Updates configuration files to reflect new paths after file movements."""
    
    def __init__(self, repo_root: Path):
        """
        Initialize ConfigUpdater.
        
        Args:
            repo_root: Root directory of the repository
        """
        self.repo_root = repo_root
        self.updated_files: List[str] = []
        self.errors: List[Tuple[str, str]] = []
    
    def update_django_settings(self, movements: List[Tuple[str, str]]) -> bool:
        """
        Update Django settings.py file with new paths.
        
        Updates:
        - INSTALLED_APPS for moved Django apps
        - Import statements for moved modules
        
        Args:
            movements: List of (old_path, new_path) tuples
            
        Returns:
            True if update succeeded, False otherwise
        """
        settings_path = self.repo_root / "apps" / "backend" / "config" / "settings.py"
        
        if not settings_path.exists():
            self.errors.append((str(settings_path), "Settings file not found"))
            return False
        
        try:
            content = settings_path.read_text(encoding='utf-8')
            original_content = content
            
            # Update INSTALLED_APPS entries
            for old_path, new_path in movements:
                # Convert file paths to Django app names
                # e.g., apps/backend/apps/security/ -> apps.security
                if 'apps/backend/apps/' in old_path:
                    old_app = old_path.replace('apps/backend/apps/', '').replace('/', '.').rstrip('.')
                    new_app = new_path.replace('apps/backend/apps/', '').replace('/', '.').rstrip('.')
                    
                    # Update in INSTALLED_APPS
                    content = re.sub(
                        rf"['\"]apps\.{re.escape(old_app)}['\"]",
                        f"'apps.{new_app}'",
                        content
                    )
            
            # Update import statements
            for old_path, new_path in movements:
                # Convert file paths to module paths
                old_module = old_path.replace('apps/backend/', '').replace('/', '.').replace('.py', '')
                new_module = new_path.replace('apps/backend/', '').replace('/', '.').replace('.py', '')
                
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
                settings_path.write_text(content, encoding='utf-8')
                self.updated_files.append(str(settings_path.relative_to(self.repo_root)))
                return True
            
            return True
            
        except Exception as e:
            self.errors.append((str(settings_path), f"Failed to update: {e}"))
            return False
    
    def update_pytest_ini(self, movements: List[Tuple[str, str]]) -> bool:
        """
        Update pytest.ini configuration file with new test paths.
        
        Updates:
        - testpaths configuration
        
        Args:
            movements: List of (old_path, new_path) tuples
            
        Returns:
            True if update succeeded, False otherwise
        """
        pytest_ini_path = self.repo_root / "apps" / "backend" / "pytest.ini"
        
        if not pytest_ini_path.exists():
            self.errors.append((str(pytest_ini_path), "pytest.ini not found"))
            return False
        
        try:
            content = pytest_ini_path.read_text(encoding='utf-8')
            original_content = content
            
            # Update testpaths
            for old_path, new_path in movements:
                # Only update if it's a test directory
                if 'test' in old_path.lower():
                    # Convert absolute paths to relative paths from backend directory
                    old_rel = old_path.replace('apps/backend/', '')
                    new_rel = new_path.replace('apps/backend/', '')
                    
                    # Update in testpaths line
                    content = re.sub(
                        rf'\b{re.escape(old_rel)}\b',
                        new_rel,
                        content
                    )
            
            # Write back if changed
            if content != original_content:
                pytest_ini_path.write_text(content, encoding='utf-8')
                self.updated_files.append(str(pytest_ini_path.relative_to(self.repo_root)))
                return True
            
            return True
            
        except Exception as e:
            self.errors.append((str(pytest_ini_path), f"Failed to update: {e}"))
            return False
    
    def update_docker_compose(self, movements: List[Tuple[str, str]]) -> bool:
        """
        Update docker-compose.yml with new paths.
        
        Updates:
        - Volume mounts
        - Build contexts
        - Command paths
        
        Args:
            movements: List of (old_path, new_path) tuples
            
        Returns:
            True if update succeeded, False otherwise
        """
        docker_compose_path = self.repo_root / "docker-compose.yml"
        
        if not docker_compose_path.exists():
            self.errors.append((str(docker_compose_path), "docker-compose.yml not found"))
            return False
        
        try:
            content = docker_compose_path.read_text(encoding='utf-8')
            original_content = content
            
            # Update paths in the file
            for old_path, new_path in movements:
                # Update volume mounts and context paths
                content = content.replace(f"./{old_path}", f"./{new_path}")
                content = content.replace(f"/{old_path}", f"/{new_path}")
                content = content.replace(old_path, new_path)
            
            # Write back if changed
            if content != original_content:
                docker_compose_path.write_text(content, encoding='utf-8')
                self.updated_files.append(str(docker_compose_path.relative_to(self.repo_root)))
                return True
            
            return True
            
        except Exception as e:
            self.errors.append((str(docker_compose_path), f"Failed to update: {e}"))
            return False
    
    def update_dockerfile(self, dockerfile_path: Path, movements: List[Tuple[str, str]]) -> bool:
        """
        Update a Dockerfile with new paths.
        
        Updates:
        - COPY instructions
        - WORKDIR instructions
        - RUN commands with paths
        
        Args:
            dockerfile_path: Path to Dockerfile (relative to repo root)
            movements: List of (old_path, new_path) tuples
            
        Returns:
            True if update succeeded, False otherwise
        """
        full_path = self.repo_root / dockerfile_path
        
        if not full_path.exists():
            self.errors.append((str(dockerfile_path), "Dockerfile not found"))
            return False
        
        try:
            content = full_path.read_text(encoding='utf-8')
            original_content = content
            
            # Update paths in COPY, WORKDIR, and RUN instructions
            for old_path, new_path in movements:
                # Update COPY instructions
                content = re.sub(
                    rf'COPY\s+{re.escape(old_path)}',
                    f'COPY {new_path}',
                    content
                )
                
                # Update WORKDIR instructions
                content = re.sub(
                    rf'WORKDIR\s+{re.escape(old_path)}',
                    f'WORKDIR {new_path}',
                    content
                )
                
                # Update paths in RUN commands
                content = content.replace(old_path, new_path)
            
            # Write back if changed
            if content != original_content:
                full_path.write_text(content, encoding='utf-8')
                self.updated_files.append(str(dockerfile_path))
                return True
            
            return True
            
        except Exception as e:
            self.errors.append((str(dockerfile_path), f"Failed to update: {e}"))
            return False
    
    def update_all_dockerfiles(self, movements: List[Tuple[str, str]]) -> bool:
        """
        Update all Dockerfiles in the repository.
        
        Args:
            movements: List of (old_path, new_path) tuples
            
        Returns:
            True if all updates succeeded, False otherwise
        """
        # Find all Dockerfiles
        dockerfiles = list(self.repo_root.rglob("Dockerfile*"))
        
        all_success = True
        for dockerfile in dockerfiles:
            rel_path = dockerfile.relative_to(self.repo_root)
            if not self.update_dockerfile(rel_path, movements):
                all_success = False
        
        return all_success
    
    def update_package_json(self, movements: List[Tuple[str, str]]) -> bool:
        """
        Update package.json scripts with new paths.
        
        Updates:
        - Script commands that reference file paths
        
        Args:
            movements: List of (old_path, new_path) tuples
            
        Returns:
            True if update succeeded, False otherwise
        """
        package_json_path = self.repo_root / "apps" / "frontend" / "package.json"
        
        if not package_json_path.exists():
            self.errors.append((str(package_json_path), "package.json not found"))
            return False
        
        try:
            import json
            
            content = package_json_path.read_text(encoding='utf-8')
            original_content = content
            
            # Update paths in the content
            for old_path, new_path in movements:
                content = content.replace(old_path, new_path)
            
            # Validate JSON is still valid
            try:
                json.loads(content)
            except json.JSONDecodeError as e:
                self.errors.append((str(package_json_path), f"Invalid JSON after update: {e}"))
                return False
            
            # Write back if changed
            if content != original_content:
                package_json_path.write_text(content, encoding='utf-8')
                self.updated_files.append(str(package_json_path.relative_to(self.repo_root)))
                return True
            
            return True
            
        except Exception as e:
            self.errors.append((str(package_json_path), f"Failed to update: {e}"))
            return False
    
    def update_all_configs(self, movements: List[Tuple[str, str]]) -> Dict[str, bool]:
        """
        Update all configuration files with new paths.
        
        Args:
            movements: List of (old_path, new_path) tuples
            
        Returns:
            Dictionary mapping config file type to success status
        """
        results = {
            'django_settings': self.update_django_settings(movements),
            'pytest_ini': self.update_pytest_ini(movements),
            'docker_compose': self.update_docker_compose(movements),
            'dockerfiles': self.update_all_dockerfiles(movements),
            'package_json': self.update_package_json(movements)
        }
        
        return results
    
    def get_updated_files(self) -> List[str]:
        """
        Get list of files that were updated.
        
        Returns:
            List of file paths that were modified
        """
        return self.updated_files.copy()
    
    def get_errors(self) -> List[Tuple[str, str]]:
        """
        Get list of errors encountered during updates.
        
        Returns:
            List of (file_path, error_message) tuples
        """
        return self.errors.copy()
    
    def clear_state(self) -> None:
        """Clear the updated files and errors lists."""
        self.updated_files = []
        self.errors = []
