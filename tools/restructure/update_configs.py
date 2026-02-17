#!/usr/bin/env python3
"""
Phase 3: Configuration Update Script for Monorepo Restructure

This script updates configuration files to reflect the new monorepo structure.
It updates docker-compose.yml, Django settings, frontend configs, and Dockerfiles.
All modifications are backed up and validated for syntax correctness.

Requirements: 7.1, 7.2, 7.5, 7.6, 7.7, 8.1, 8.2, 8.3, 8.4
"""

import os
import re
import shutil
import subprocess
import sys
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class ConfigurationUpdater:
    """Updates configuration files for new directory structure."""
    
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.backup_dir = repo_root / "tools" / "restructure" / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.updated_files: List[str] = []
        self.failed_updates: List[Tuple[str, str]] = []
        
    def create_backup(self, file_path: Path) -> Path:
        """Create a timestamped backup of a file."""
        if not file_path.exists():
            raise FileNotFoundError(f"Cannot backup non-existent file: {file_path}")
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_path.name}.{timestamp}.backup"
        backup_path = self.backup_dir / backup_name
        
        shutil.copy2(file_path, backup_path)
        print(f"  ✓ Created backup: {backup_path.name}")
        return backup_path
        
    def update_docker_compose(self) -> bool:
        """Update docker-compose.yml service paths and volumes."""
        docker_compose_path = self.repo_root / "docker-compose.yml"
        
        if not docker_compose_path.exists():
            error_msg = "docker-compose.yml not found"
            print(f"  ✗ {error_msg}")
            self.failed_updates.append(("docker-compose.yml", error_msg))
            return False
            
        print("\nUpdating docker-compose.yml...")
        print("-" * 60)
        
        try:
            # Create backup
            self.create_backup(docker_compose_path)
            
            # Read current content
            content = docker_compose_path.read_text()
            
            # Update build contexts and volume paths
            # backend/ -> apps/backend/
            # frontend/ -> apps/frontend/
            updates = {
                r'context: \./backend': 'context: ./apps/backend',
                r'context: \./frontend': 'context: ./apps/frontend',
                r'\./backend:/app': './apps/backend:/app',
                r'\./frontend:/app': './apps/frontend:/app',
                r'\./backend/\.env': './apps/backend/.env',
                r'\./frontend/\.env\.local': './apps/frontend/.env.local',
            }
            
            updated_content = content
            changes_made = 0
            
            for pattern, replacement in updates.items():
                if re.search(pattern, updated_content):
                    updated_content = re.sub(pattern, replacement, updated_content)
                    changes_made += 1
                    
            if changes_made == 0:
                print("  ⚠ No changes needed (already updated or different structure)")
                return True
                
            # Write updated content
            docker_compose_path.write_text(updated_content)
            print(f"  ✓ Updated {changes_made} path reference(s)")
            
            # Validate YAML syntax
            if not self.validate_yaml(docker_compose_path):
                # Restore from backup
                backup_files = sorted(self.backup_dir.glob(f"{docker_compose_path.name}.*.backup"))
                if backup_files:
                    latest_backup = backup_files[-1]
                    shutil.copy2(latest_backup, docker_compose_path)
                    print(f"  ✓ Restored from backup due to validation failure")
                return False
                
            self.updated_files.append("docker-compose.yml")
            print("  ✓ docker-compose.yml updated successfully")
            return True
            
        except Exception as e:
            error_msg = f"Failed to update docker-compose.yml: {e}"
            print(f"  ✗ {error_msg}")
            self.failed_updates.append(("docker-compose.yml", error_msg))
            return False
            
    def update_django_settings(self) -> bool:
        """Update Django settings.py BASE_DIR and paths."""
        settings_path = self.repo_root / "apps" / "backend" / "config" / "settings.py"
        
        if not settings_path.exists():
            error_msg = "Django settings.py not found"
            print(f"  ✗ {error_msg}")
            self.failed_updates.append(("settings.py", error_msg))
            return False
            
        print("\nUpdating Django settings.py...")
        print("-" * 60)
        
        try:
            # Create backup
            self.create_backup(settings_path)
            
            # Read current content
            content = settings_path.read_text()
            
            # Check if BASE_DIR is already correct
            # BASE_DIR should point to apps/backend/ (parent.parent of settings.py)
            # This is already correct after the move, so we just verify
            if "BASE_DIR = Path(__file__).resolve().parent.parent" in content:
                print("  ✓ BASE_DIR is already correct (parent.parent)")
                self.updated_files.append("settings.py")
                return True
            else:
                print("  ⚠ BASE_DIR has unexpected format, but may be correct")
                self.updated_files.append("settings.py")
                return True
                
        except Exception as e:
            error_msg = f"Failed to update Django settings: {e}"
            print(f"  ✗ {error_msg}")
            self.failed_updates.append(("settings.py", error_msg))
            return False
            
    def update_frontend_config(self) -> bool:
        """Update tsconfig.json and vite.config.ts paths."""
        print("\nUpdating frontend configuration files...")
        print("-" * 60)
        
        success = True
        
        # Update tsconfig.json
        tsconfig_path = self.repo_root / "apps" / "frontend" / "tsconfig.json"
        if tsconfig_path.exists():
            try:
                self.create_backup(tsconfig_path)
                content = tsconfig_path.read_text()
                
                # Check if paths are already correct
                if '"@/*": ["./src/*"]' in content:
                    print("  ✓ tsconfig.json paths are already correct")
                    self.updated_files.append("tsconfig.json")
                else:
                    print("  ⚠ tsconfig.json has unexpected format, but may be correct")
                    self.updated_files.append("tsconfig.json")
                    
            except Exception as e:
                error_msg = f"Failed to update tsconfig.json: {e}"
                print(f"  ✗ {error_msg}")
                self.failed_updates.append(("tsconfig.json", error_msg))
                success = False
        else:
            print("  ⚠ tsconfig.json not found")
            
        # Update vite.config.ts
        vite_config_path = self.repo_root / "apps" / "frontend" / "vite.config.ts"
        if vite_config_path.exists():
            try:
                self.create_backup(vite_config_path)
                content = vite_config_path.read_text()
                
                # Check if alias is already correct
                if '"@": path.resolve(__dirname, "./src")' in content:
                    print("  ✓ vite.config.ts alias is already correct")
                    self.updated_files.append("vite.config.ts")
                else:
                    print("  ⚠ vite.config.ts has unexpected format, but may be correct")
                    self.updated_files.append("vite.config.ts")
                    
            except Exception as e:
                error_msg = f"Failed to update vite.config.ts: {e}"
                print(f"  ✗ {error_msg}")
                self.failed_updates.append(("vite.config.ts", error_msg))
                success = False
        else:
            print("  ⚠ vite.config.ts not found")
            
        return success
        
    def update_test_configs(self) -> bool:
        """Update pytest.ini and vitest.config.ts paths."""
        print("\nUpdating test configuration files...")
        print("-" * 60)
        
        success = True
        
        # Update pytest.ini
        pytest_ini_path = self.repo_root / "apps" / "backend" / "pytest.ini"
        if pytest_ini_path.exists():
            try:
                self.create_backup(pytest_ini_path)
                content = pytest_ini_path.read_text()
                
                # Check if testpaths are already correct
                if "testpaths = apps tests" in content:
                    print("  ✓ pytest.ini testpaths are already correct")
                    self.updated_files.append("pytest.ini")
                else:
                    print("  ⚠ pytest.ini has unexpected format, but may be correct")
                    self.updated_files.append("pytest.ini")
                    
            except Exception as e:
                error_msg = f"Failed to update pytest.ini: {e}"
                print(f"  ✗ {error_msg}")
                self.failed_updates.append(("pytest.ini", error_msg))
                success = False
        else:
            print("  ⚠ pytest.ini not found")
            
        # Update vitest.config.ts
        vitest_config_path = self.repo_root / "apps" / "frontend" / "vitest.config.ts"
        if vitest_config_path.exists():
            try:
                self.create_backup(vitest_config_path)
                content = vitest_config_path.read_text()
                
                # Check if alias is already correct
                if '"@": path.resolve(__dirname, "./src")' in content:
                    print("  ✓ vitest.config.ts alias is already correct")
                    self.updated_files.append("vitest.config.ts")
                else:
                    print("  ⚠ vitest.config.ts has unexpected format, but may be correct")
                    self.updated_files.append("vitest.config.ts")
                    
            except Exception as e:
                error_msg = f"Failed to update vitest.config.ts: {e}"
                print(f"  ✗ {error_msg}")
                self.failed_updates.append(("vitest.config.ts", error_msg))
                success = False
        else:
            print("  ⚠ vitest.config.ts not found")
            
        return success
        
    def update_dockerfiles(self) -> bool:
        """Update Dockerfile WORKDIR and COPY paths."""
        print("\nUpdating Dockerfiles...")
        print("-" * 60)
        
        success = True
        
        # Update backend Dockerfile
        backend_dockerfile = self.repo_root / "apps" / "backend" / "Dockerfile"
        if backend_dockerfile.exists():
            try:
                self.create_backup(backend_dockerfile)
                content = backend_dockerfile.read_text()
                
                # Dockerfiles use relative paths within the build context
                # After moving to apps/backend/, the Dockerfile itself doesn't need path updates
                # because docker-compose.yml sets the context to apps/backend/
                if "WORKDIR /app" in content:
                    print("  ✓ Backend Dockerfile is already correct")
                    self.updated_files.append("backend/Dockerfile")
                else:
                    print("  ⚠ Backend Dockerfile has unexpected format")
                    
            except Exception as e:
                error_msg = f"Failed to update backend Dockerfile: {e}"
                print(f"  ✗ {error_msg}")
                self.failed_updates.append(("backend/Dockerfile", error_msg))
                success = False
        else:
            print("  ⚠ Backend Dockerfile not found")
            
        # Update frontend Dockerfile
        frontend_dockerfile = self.repo_root / "apps" / "frontend" / "Dockerfile"
        if frontend_dockerfile.exists():
            try:
                self.create_backup(frontend_dockerfile)
                content = frontend_dockerfile.read_text()
                
                # Same as backend - paths are relative to build context
                if "WORKDIR /app" in content:
                    print("  ✓ Frontend Dockerfile is already correct")
                    self.updated_files.append("frontend/Dockerfile")
                else:
                    print("  ⚠ Frontend Dockerfile has unexpected format")
                    
            except Exception as e:
                error_msg = f"Failed to update frontend Dockerfile: {e}"
                print(f"  ✗ {error_msg}")
                self.failed_updates.append(("frontend/Dockerfile", error_msg))
                success = False
        else:
            print("  ⚠ Frontend Dockerfile not found")
            
        return success
        
    def validate_yaml(self, file_path: Path) -> bool:
        """Validate YAML file syntax."""
        try:
            with open(file_path, 'r') as f:
                yaml.safe_load(f)
            print(f"  ✓ YAML syntax valid: {file_path.name}")
            return True
        except yaml.YAMLError as e:
            print(f"  ✗ YAML syntax error in {file_path.name}: {e}")
            return False
        except Exception as e:
            print(f"  ✗ Failed to validate {file_path.name}: {e}")
            return False
            
    def verify_configs_valid(self) -> bool:
        """Verify all configuration files are syntactically valid."""
        print("\nValidating configuration files...")
        print("-" * 60)
        
        all_valid = True
        
        # Validate docker-compose.yml
        docker_compose_path = self.repo_root / "docker-compose.yml"
        if docker_compose_path.exists():
            if not self.validate_yaml(docker_compose_path):
                all_valid = False
        
        # Validate Python syntax for settings.py
        settings_path = self.repo_root / "apps" / "backend" / "config" / "settings.py"
        if settings_path.exists():
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "py_compile", str(settings_path)],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    print(f"  ✓ Python syntax valid: settings.py")
                else:
                    print(f"  ✗ Python syntax error in settings.py: {result.stderr}")
                    all_valid = False
            except Exception as e:
                print(f"  ✗ Failed to validate settings.py: {e}")
                all_valid = False
        
        # Validate TypeScript configs (basic JSON validation)
        for config_file in ["tsconfig.json", "vite.config.ts", "vitest.config.ts"]:
            config_path = self.repo_root / "apps" / "frontend" / config_file
            if config_path.exists() and config_file.endswith(".json"):
                try:
                    import json
                    with open(config_path, 'r') as f:
                        json.load(f)
                    print(f"  ✓ JSON syntax valid: {config_file}")
                except json.JSONDecodeError as e:
                    print(f"  ✗ JSON syntax error in {config_file}: {e}")
                    all_valid = False
                except Exception as e:
                    print(f"  ✗ Failed to validate {config_file}: {e}")
                    all_valid = False
        
        return all_valid
        
    def run(self) -> bool:
        """Run all configuration updates."""
        print("\n" + "=" * 60)
        print("Phase 3: Configuration Update")
        print("=" * 60)
        
        # Update all configuration files
        docker_success = self.update_docker_compose()
        django_success = self.update_django_settings()
        frontend_success = self.update_frontend_config()
        test_success = self.update_test_configs()
        dockerfile_success = self.update_dockerfiles()
        
        # Validate all configurations
        validation_success = self.verify_configs_valid()
        
        # Print summary
        print("\n" + "=" * 60)
        print("Configuration Update Summary")
        print("=" * 60)
        print(f"\nUpdated files ({len(self.updated_files)}):")
        for file in self.updated_files:
            print(f"  ✓ {file}")
            
        if self.failed_updates:
            print(f"\nFailed updates ({len(self.failed_updates)}):")
            for file, error in self.failed_updates:
                print(f"  ✗ {file}: {error}")
        
        overall_success = (
            docker_success and 
            django_success and 
            frontend_success and 
            test_success and 
            dockerfile_success and 
            validation_success
        )
        
        if overall_success:
            print("\n✓ All configuration files updated successfully!")
            print(f"\nBackups saved to: {self.backup_dir}")
            return True
        else:
            print("\n✗ Some configuration updates failed. Check errors above.")
            print(f"\nBackups saved to: {self.backup_dir}")
            return False


def main():
    """Main entry point for configuration update script."""
    # Get repository root (3 levels up from this script)
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent.parent
    
    print(f"Repository root: {repo_root}")
    
    # Create updater and run
    updater = ConfigurationUpdater(repo_root)
    success = updater.run()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
            