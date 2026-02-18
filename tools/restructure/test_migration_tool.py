#!/usr/bin/env python3
"""
Simple test script to verify migration_tool.py functionality.
"""

from pathlib import Path
from migration_tool import MigrationTool, Checkpoint


def test_checkpoint_creation():
    """Test checkpoint creation and tracking."""
    print("Testing checkpoint creation...")
    
    repo_root = Path(__file__).parent.parent.parent
    tool = MigrationTool(repo_root)
    
    # Create a test checkpoint
    checkpoint = tool.create_checkpoint(
        name="test_checkpoint",
        description="Testing checkpoint functionality"
    )
    
    print(f"✓ Created checkpoint: {checkpoint.name}")
    print(f"  Timestamp: {checkpoint.timestamp}")
    print(f"  Git commit: {checkpoint.git_commit[:8] if checkpoint.git_commit else 'None'}")
    print(f"  Description: {checkpoint.description}")
    
    # List all checkpoints
    checkpoints = tool.rollback_manager.list_checkpoints()
    print(f"\n✓ Total checkpoints: {len(checkpoints)}")
    
    return True


def test_file_mover():
    """Test FileMover initialization."""
    print("\nTesting FileMover...")
    
    repo_root = Path(__file__).parent.parent.parent
    tool = MigrationTool(repo_root)
    
    print(f"✓ FileMover initialized")
    print(f"  Repo root: {tool.file_mover.repo_root}")
    print(f"  Moved files: {len(tool.file_mover.get_moved_files())}")
    print(f"  Failed moves: {len(tool.file_mover.get_failed_moves())}")
    
    return True


def test_path_updater():
    """Test PathUpdater initialization."""
    print("\nTesting PathUpdater...")
    
    repo_root = Path(__file__).parent.parent.parent
    tool = MigrationTool(repo_root)
    
    print(f"✓ PathUpdater initialized")
    print(f"  Repo root: {tool.path_updater.repo_root}")
    print(f"  Updated files: {len(tool.path_updater.get_updated_files())}")
    print(f"  Failed updates: {len(tool.path_updater.get_failed_updates())}")
    
    return True


def test_validator():
    """Test Validator initialization."""
    print("\nTesting Validator...")
    
    repo_root = Path(__file__).parent.parent.parent
    tool = MigrationTool(repo_root)
    
    print(f"✓ Validator initialized")
    print(f"  Repo root: {tool.validator.repo_root}")
    print(f"  Validation errors: {len(tool.validator.get_validation_errors())}")
    
    return True


def test_file_tracker():
    """Test FileTracker integration."""
    print("\nTesting FileTracker...")
    
    repo_root = Path(__file__).parent.parent.parent
    tool = MigrationTool(repo_root)
    
    print(f"✓ FileTracker initialized")
    print(f"  Repo root: {tool.file_tracker.repo_root}")
    print(f"  Log file: {tool.file_tracker.log_file}")
    print(f"  Recorded movements: {tool.file_tracker.get_movements_count()}")
    
    # Test movement report
    report = tool.file_tracker.generate_movement_report()
    print(f"  Total movements: {report['total_movements']}")
    print(f"  Movements by phase: {report['by_phase']}")
    print(f"  Movements by type: {report['by_type']}")
    
    return True


def test_config_updater():
    """Test ConfigUpdater integration."""
    print("\nTesting ConfigUpdater...")
    
    repo_root = Path(__file__).parent.parent.parent
    tool = MigrationTool(repo_root)
    
    print(f"✓ ConfigUpdater initialized")
    print(f"  Repo root: {tool.config_updater.repo_root}")
    print(f"  Updated files: {len(tool.config_updater.get_updated_files())}")
    print(f"  Errors: {len(tool.config_updater.get_errors())}")
    
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("Migration Tool Core Structure Tests")
    print("=" * 60)
    
    tests = [
        test_checkpoint_creation,
        test_file_mover,
        test_path_updater,
        test_validator,
        test_file_tracker,
        test_config_updater,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test failed: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    import sys
    sys.exit(0 if main() else 1)
