#!/usr/bin/env python3
"""
Unit tests for File Movement Tracker

Tests the FileMovement dataclass and FileTracker functionality.
"""

import json
import pytest
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

from file_tracker import FileMovement, FileTracker


class TestFileMovement:
    """Test FileMovement dataclass."""
    
    def test_file_movement_creation(self):
        """Test creating a FileMovement instance."""
        timestamp = datetime.now()
        movement = FileMovement(
            old_path="apps/backend/test.py",
            new_path="tests/backend/test.py",
            file_type="test",
            phase=1,
            timestamp=timestamp,
            reason="Reorganize tests"
        )
        
        assert movement.old_path == "apps/backend/test.py"
        assert movement.new_path == "tests/backend/test.py"
        assert movement.file_type == "test"
        assert movement.phase == 1
        assert movement.timestamp == timestamp
        assert movement.reason == "Reorganize tests"
    
    def test_file_movement_to_dict(self):
        """Test converting FileMovement to dictionary."""
        timestamp = datetime(2024, 1, 15, 10, 30, 0)
        movement = FileMovement(
            old_path="old/path.py",
            new_path="new/path.py",
            file_type="code",
            phase=2,
            timestamp=timestamp,
            reason="Test reason"
        )
        
        result = movement.to_dict()
        
        assert result['old_path'] == "old/path.py"
        assert result['new_path'] == "new/path.py"
        assert result['file_type'] == "code"
        assert result['phase'] == 2
        assert result['timestamp'] == timestamp.isoformat()
        assert result['reason'] == "Test reason"
    
    def test_file_movement_from_dict(self):
        """Test creating FileMovement from dictionary."""
        data = {
            'old_path': "old/path.py",
            'new_path': "new/path.py",
            'file_type': "code",
            'phase': 2,
            'timestamp': "2024-01-15T10:30:00",
            'reason': "Test reason"
        }
        
        movement = FileMovement.from_dict(data)
        
        assert movement.old_path == "old/path.py"
        assert movement.new_path == "new/path.py"
        assert movement.file_type == "code"
        assert movement.phase == 2
        assert movement.timestamp == datetime(2024, 1, 15, 10, 30, 0)
        assert movement.reason == "Test reason"
    
    def test_file_movement_roundtrip(self):
        """Test converting to dict and back preserves data."""
        original = FileMovement(
            old_path="test.py",
            new_path="new_test.py",
            file_type="test",
            phase=1,
            timestamp=datetime.now(),
            reason="Testing"
        )
        
        data = original.to_dict()
        restored = FileMovement.from_dict(data)
        
        assert restored.old_path == original.old_path
        assert restored.new_path == original.new_path
        assert restored.file_type == original.file_type
        assert restored.phase == original.phase
        assert restored.reason == original.reason


class TestFileTracker:
    """Test FileTracker functionality."""
    
    @pytest.fixture
    def temp_repo(self):
        """Create a temporary repository directory."""
        with TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            (repo_path / "tools" / "restructure").mkdir(parents=True)
            yield repo_path
    
    def test_file_tracker_initialization(self, temp_repo):
        """Test FileTracker initialization."""
        tracker = FileTracker(temp_repo)
        
        assert tracker.repo_root == temp_repo
        assert tracker.log_file == temp_repo / "tools" / "restructure" / "file_movements.json"
        assert tracker.movements == []
    
    def test_file_tracker_custom_log_file(self, temp_repo):
        """Test FileTracker with custom log file path."""
        custom_log = temp_repo / "custom_log.json"
        tracker = FileTracker(temp_repo, log_file=custom_log)
        
        assert tracker.log_file == custom_log
    
    def test_log_movement(self, temp_repo):
        """Test logging a single file movement."""
        tracker = FileTracker(temp_repo)
        
        movement = tracker.log_movement(
            old_path="old/file.py",
            new_path="new/file.py",
            file_type="code",
            phase=1,
            reason="Reorganization"
        )
        
        assert movement.old_path == "old/file.py"
        assert movement.new_path == "new/file.py"
        assert movement.file_type == "code"
        assert movement.phase == 1
        assert movement.reason == "Reorganization"
        assert len(tracker.movements) == 1
    
    def test_log_movement_persists(self, temp_repo):
        """Test that logged movements are persisted to file."""
        tracker = FileTracker(temp_repo)
        
        tracker.log_movement(
            old_path="test.py",
            new_path="new_test.py",
            file_type="test",
            phase=1,
            reason="Test"
        )
        
        # Create new tracker instance to load from file
        tracker2 = FileTracker(temp_repo)
        
        assert len(tracker2.movements) == 1
        assert tracker2.movements[0].old_path == "test.py"
        assert tracker2.movements[0].new_path == "new_test.py"
    
    def test_log_movements_batch(self, temp_repo):
        """Test logging multiple movements at once."""
        tracker = FileTracker(temp_repo)
        
        movements_data = [
            {
                'old_path': "file1.py",
                'new_path': "new/file1.py",
                'file_type': "code",
                'phase': 1,
                'reason': "Batch move"
            },
            {
                'old_path': "file2.py",
                'new_path': "new/file2.py",
                'file_type': "code",
                'phase': 1,
                'reason': "Batch move"
            }
        ]
        
        created = tracker.log_movements_batch(movements_data)
        
        assert len(created) == 2
        assert len(tracker.movements) == 2
        assert tracker.movements[0].old_path == "file1.py"
        assert tracker.movements[1].old_path == "file2.py"
    
    def test_get_movements_by_phase(self, temp_repo):
        """Test querying movements by phase."""
        tracker = FileTracker(temp_repo)
        
        tracker.log_movement("file1.py", "new1.py", "code", 1, "Phase 1")
        tracker.log_movement("file2.py", "new2.py", "code", 2, "Phase 2")
        tracker.log_movement("file3.py", "new3.py", "code", 1, "Phase 1")
        
        phase1_movements = tracker.get_movements_by_phase(1)
        phase2_movements = tracker.get_movements_by_phase(2)
        
        assert len(phase1_movements) == 2
        assert len(phase2_movements) == 1
        assert all(m.phase == 1 for m in phase1_movements)
        assert all(m.phase == 2 for m in phase2_movements)
    
    def test_get_movements_by_type(self, temp_repo):
        """Test querying movements by file type."""
        tracker = FileTracker(temp_repo)
        
        tracker.log_movement("code.py", "new_code.py", "code", 1, "")
        tracker.log_movement("test.py", "new_test.py", "test", 1, "")
        tracker.log_movement("doc.md", "new_doc.md", "doc", 1, "")
        tracker.log_movement("code2.py", "new_code2.py", "code", 1, "")
        
        code_movements = tracker.get_movements_by_type("code")
        test_movements = tracker.get_movements_by_type("test")
        doc_movements = tracker.get_movements_by_type("doc")
        
        assert len(code_movements) == 2
        assert len(test_movements) == 1
        assert len(doc_movements) == 1
    
    def test_get_movement_for_file(self, temp_repo):
        """Test finding movement for a specific file."""
        tracker = FileTracker(temp_repo)
        
        tracker.log_movement("old/path.py", "new/path.py", "code", 1, "")
        tracker.log_movement("other/file.py", "new/file.py", "code", 1, "")
        
        movement = tracker.get_movement_for_file("old/path.py")
        
        assert movement is not None
        assert movement.old_path == "old/path.py"
        assert movement.new_path == "new/path.py"
    
    def test_get_movement_for_file_not_found(self, temp_repo):
        """Test finding movement for non-existent file."""
        tracker = FileTracker(temp_repo)
        
        tracker.log_movement("file.py", "new_file.py", "code", 1, "")
        
        movement = tracker.get_movement_for_file("nonexistent.py")
        
        assert movement is None
    
    def test_get_new_path(self, temp_repo):
        """Test getting new path for a file."""
        tracker = FileTracker(temp_repo)
        
        tracker.log_movement("old/path.py", "new/path.py", "code", 1, "")
        
        new_path = tracker.get_new_path("old/path.py")
        
        assert new_path == "new/path.py"
    
    def test_get_new_path_not_found(self, temp_repo):
        """Test getting new path for non-existent file."""
        tracker = FileTracker(temp_repo)
        
        new_path = tracker.get_new_path("nonexistent.py")
        
        assert new_path is None
    
    def test_get_all_movements(self, temp_repo):
        """Test getting all movements."""
        tracker = FileTracker(temp_repo)
        
        tracker.log_movement("file1.py", "new1.py", "code", 1, "")
        tracker.log_movement("file2.py", "new2.py", "code", 1, "")
        
        all_movements = tracker.get_all_movements()
        
        assert len(all_movements) == 2
        # Verify it's a copy, not the original list
        all_movements.append(None)
        assert len(tracker.movements) == 2
    
    def test_get_movements_count(self, temp_repo):
        """Test getting count of movements."""
        tracker = FileTracker(temp_repo)
        
        assert tracker.get_movements_count() == 0
        
        tracker.log_movement("file1.py", "new1.py", "code", 1, "")
        assert tracker.get_movements_count() == 1
        
        tracker.log_movement("file2.py", "new2.py", "code", 1, "")
        assert tracker.get_movements_count() == 2
    
    def test_get_movements_by_date_range(self, temp_repo):
        """Test querying movements by date range."""
        tracker = FileTracker(temp_repo)
        
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        tomorrow = now + timedelta(days=1)
        
        # Manually create movements with specific timestamps
        movement1 = FileMovement("file1.py", "new1.py", "code", 1, yesterday, "")
        movement2 = FileMovement("file2.py", "new2.py", "code", 1, now, "")
        movement3 = FileMovement("file3.py", "new3.py", "code", 1, tomorrow, "")
        
        tracker.movements = [movement1, movement2, movement3]
        
        # Query for movements from yesterday to now
        movements = tracker.get_movements_by_date_range(yesterday, now)
        
        assert len(movements) == 2
        assert movements[0].old_path == "file1.py"
        assert movements[1].old_path == "file2.py"
    
    def test_generate_movement_report(self, temp_repo):
        """Test generating movement report."""
        tracker = FileTracker(temp_repo)
        
        tracker.log_movement("file1.py", "new1.py", "code", 1, "")
        tracker.log_movement("file2.py", "new2.py", "test", 1, "")
        tracker.log_movement("file3.py", "new3.py", "code", 2, "")
        
        report = tracker.generate_movement_report()
        
        assert report['total_movements'] == 3
        assert report['by_phase'][1] == 2
        assert report['by_phase'][2] == 1
        assert report['by_type']['code'] == 2
        assert report['by_type']['test'] == 1
        assert 'first_movement' in report
        assert 'last_movement' in report
    
    def test_generate_movement_report_empty(self, temp_repo):
        """Test generating report with no movements."""
        tracker = FileTracker(temp_repo)
        
        report = tracker.generate_movement_report()
        
        assert report['total_movements'] == 0
        assert report['by_phase'] == {}
        assert report['by_type'] == {}
        assert report['first_movement'] is None
        assert report['last_movement'] is None
    
    def test_export_to_markdown(self, temp_repo):
        """Test exporting movements to Markdown."""
        tracker = FileTracker(temp_repo)
        
        tracker.log_movement("file1.py", "new1.py", "code", 1, "Phase 1 move")
        tracker.log_movement("file2.py", "new2.py", "test", 2, "Phase 2 move")
        
        output_path = temp_repo / "movements.md"
        tracker.export_to_markdown(output_path)
        
        assert output_path.exists()
        content = output_path.read_text()
        
        assert "# File Movement History" in content
        assert "Total movements: 2" in content
        assert "## Movements by Phase" in content
        assert "### Phase 1" in content
        assert "### Phase 2" in content
        assert "file1.py" in content
        assert "file2.py" in content
    
    def test_clear_movements(self, temp_repo):
        """Test clearing all movements."""
        tracker = FileTracker(temp_repo)
        
        tracker.log_movement("file1.py", "new1.py", "code", 1, "")
        tracker.log_movement("file2.py", "new2.py", "code", 1, "")
        
        assert len(tracker.movements) == 2
        
        tracker.clear_movements()
        
        assert len(tracker.movements) == 0
        
        # Verify it's persisted
        tracker2 = FileTracker(temp_repo)
        assert len(tracker2.movements) == 0
    
    def test_load_corrupted_file(self, temp_repo):
        """Test loading from corrupted JSON file."""
        log_file = temp_repo / "tools" / "restructure" / "file_movements.json"
        log_file.write_text("invalid json {{{", encoding='utf-8')
        
        tracker = FileTracker(temp_repo)
        
        # Should initialize with empty movements list
        assert tracker.movements == []
    
    def test_multiple_file_types(self, temp_repo):
        """Test tracking different file types."""
        tracker = FileTracker(temp_repo)
        
        file_types = ['code', 'doc', 'test', 'config', 'artifact']
        
        for i, file_type in enumerate(file_types):
            tracker.log_movement(
                f"file{i}.ext",
                f"new{i}.ext",
                file_type,
                1,
                f"Move {file_type}"
            )
        
        for file_type in file_types:
            movements = tracker.get_movements_by_type(file_type)
            assert len(movements) == 1
            assert movements[0].file_type == file_type


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
