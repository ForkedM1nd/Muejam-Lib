"""
Unit tests for sync conflict resolution.

Tests the conflict detection and resolution functionality for data synchronization.
"""

import pytest
from datetime import datetime, timedelta, timezone
from apps.core.sync_conflict_service import SyncConflictService, ConflictDetails


class TestConflictDetection:
    """Test conflict detection logic."""
    
    def test_no_conflict_when_server_data_missing(self):
        """Test that no conflict is detected when server data doesn't exist."""
        client_data = {'offset': 100}
        server_data = None
        
        conflict = SyncConflictService.detect_conflict(
            resource_type='reading_progress',
            resource_id='test_123',
            client_data=client_data,
            server_data=server_data,
            client_timestamp=datetime.now(timezone.utc)
        )
        
        assert conflict is None
    
    def test_conflict_when_client_timestamp_missing(self):
        """Test that conflict is detected when client has no timestamp."""
        client_data = {'offset': 100}
        server_data = {
            'offset': 50,
            'updated_at': datetime.now(timezone.utc)
        }
        
        conflict = SyncConflictService.detect_conflict(
            resource_type='reading_progress',
            resource_id='test_123',
            client_data=client_data,
            server_data=server_data,
            client_timestamp=None
        )
        
        assert conflict is not None
        assert conflict['conflict_detected'] is True
        assert conflict['reason'] == 'missing_client_timestamp'
    
    def test_conflict_when_server_modified_after_client_sync(self):
        """Test that conflict is detected when server data is newer."""
        client_timestamp = datetime.now(timezone.utc) - timedelta(hours=2)
        server_timestamp = datetime.now(timezone.utc) - timedelta(hours=1)
        
        client_data = {'offset': 100}
        server_data = {
            'offset': 150,
            'updated_at': server_timestamp
        }
        
        conflict = SyncConflictService.detect_conflict(
            resource_type='reading_progress',
            resource_id='test_123',
            client_data=client_data,
            server_data=server_data,
            client_timestamp=client_timestamp
        )
        
        assert conflict is not None
        assert conflict['conflict_detected'] is True
        assert conflict['reason'] == 'stale_data'
        assert len(conflict['conflicts']) > 0
    
    def test_no_conflict_when_server_not_modified(self):
        """Test that no conflict when server hasn't been modified since client sync."""
        client_timestamp = datetime.now(timezone.utc) - timedelta(hours=1)
        server_timestamp = datetime.now(timezone.utc) - timedelta(hours=2)
        
        client_data = {'offset': 100}
        server_data = {
            'offset': 50,
            'updated_at': server_timestamp
        }
        
        conflict = SyncConflictService.detect_conflict(
            resource_type='reading_progress',
            resource_id='test_123',
            client_data=client_data,
            server_data=server_data,
            client_timestamp=client_timestamp
        )
        
        assert conflict is None
    
    def test_no_conflict_when_values_match(self):
        """Test that no conflict when client and server values match."""
        client_timestamp = datetime.now(timezone.utc) - timedelta(hours=2)
        server_timestamp = datetime.now(timezone.utc) - timedelta(hours=1)
        
        client_data = {'offset': 100}
        server_data = {
            'offset': 100,  # Same value
            'updated_at': server_timestamp
        }
        
        conflict = SyncConflictService.detect_conflict(
            resource_type='reading_progress',
            resource_id='test_123',
            client_data=client_data,
            server_data=server_data,
            client_timestamp=client_timestamp
        )
        
        assert conflict is None


class TestFieldConflictDetection:
    """Test field-level conflict detection."""
    
    def test_detect_numeric_field_conflict(self):
        """Test detection of numeric field conflicts."""
        client_data = {'offset': 100, 'progress': 75}
        server_data = {'offset': 150, 'progress': 80}
        
        conflicts = SyncConflictService._detect_field_conflicts(
            client_data, server_data
        )
        
        assert len(conflicts) == 2
        assert any(c.field == 'offset' for c in conflicts)
        assert any(c.field == 'progress' for c in conflicts)
    
    def test_detect_text_field_conflict(self):
        """Test detection of text field conflicts."""
        client_data = {'content': 'Client version'}
        server_data = {'content': 'Server version'}
        
        conflicts = SyncConflictService._detect_field_conflicts(
            client_data, server_data
        )
        
        assert len(conflicts) == 1
        assert conflicts[0].field == 'content'
        assert conflicts[0].client_value == 'Client version'
        assert conflicts[0].server_value == 'Server version'
    
    def test_detect_boolean_field_conflict(self):
        """Test detection of boolean field conflicts."""
        client_data = {'published': True}
        server_data = {'published': False}
        
        conflicts = SyncConflictService._detect_field_conflicts(
            client_data, server_data
        )
        
        assert len(conflicts) == 1
        assert conflicts[0].field == 'published'
        assert conflicts[0].resolution_strategy == SyncConflictService.STRATEGY_MANUAL
    
    def test_exclude_metadata_fields(self):
        """Test that metadata fields are excluded from conflict detection."""
        client_data = {
            'id': 'test_123',
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc),
            'user_id': 'user_123',
            'offset': 100
        }
        server_data = {
            'id': 'test_123',
            'created_at': datetime.now(timezone.utc) - timedelta(days=1),
            'updated_at': datetime.now(timezone.utc) - timedelta(hours=1),
            'user_id': 'user_123',
            'offset': 150
        }
        
        conflicts = SyncConflictService._detect_field_conflicts(
            client_data, server_data
        )
        
        # Only offset should be detected as conflict
        assert len(conflicts) == 1
        assert conflicts[0].field == 'offset'


class TestResolutionStrategy:
    """Test resolution strategy determination."""
    
    def test_numeric_field_client_wins_when_greater(self):
        """Test that client wins for numeric fields when value is greater."""
        strategy = SyncConflictService._determine_resolution_strategy(
            'offset', 150, 100
        )
        
        assert strategy == SyncConflictService.STRATEGY_CLIENT_WINS
    
    def test_numeric_field_server_wins_when_greater(self):
        """Test that server wins for numeric fields when value is greater."""
        strategy = SyncConflictService._determine_resolution_strategy(
            'offset', 100, 150
        )
        
        assert strategy == SyncConflictService.STRATEGY_SERVER_WINS
    
    def test_boolean_field_requires_manual_resolution(self):
        """Test that boolean fields require manual resolution."""
        strategy = SyncConflictService._determine_resolution_strategy(
            'published', True, False
        )
        
        assert strategy == SyncConflictService.STRATEGY_MANUAL
    
    def test_text_field_requires_manual_resolution(self):
        """Test that text fields require manual resolution."""
        strategy = SyncConflictService._determine_resolution_strategy(
            'content', 'Client text', 'Server text'
        )
        
        assert strategy == SyncConflictService.STRATEGY_MANUAL


class TestVersionComparison:
    """Test version comparison logic."""
    
    def test_compare_equal_versions(self):
        """Test comparison of equal versions."""
        result = SyncConflictService.compare_versions('1.0.0', '1.0.0')
        assert result == 'equal'
    
    def test_compare_client_newer_version(self):
        """Test comparison when client version is newer."""
        result = SyncConflictService.compare_versions('2.0.0', '1.0.0')
        assert result == 'client_newer'
    
    def test_compare_server_newer_version(self):
        """Test comparison when server version is newer."""
        result = SyncConflictService.compare_versions('1.0.0', '2.0.0')
        assert result == 'server_newer'
    
    def test_compare_missing_versions(self):
        """Test comparison with missing versions."""
        result = SyncConflictService.compare_versions(None, '1.0.0')
        assert result == 'unknown'
        
        result = SyncConflictService.compare_versions('1.0.0', None)
        assert result == 'unknown'


class TestTimestampComparison:
    """Test timestamp comparison logic."""
    
    def test_compare_equal_timestamps(self):
        """Test comparison of equal timestamps."""
        timestamp = datetime.now(timezone.utc)
        result = SyncConflictService.compare_timestamps(timestamp, timestamp)
        assert result == 'equal'
    
    def test_compare_client_newer_timestamp(self):
        """Test comparison when client timestamp is newer."""
        client_ts = datetime.now(timezone.utc)
        server_ts = datetime.now(timezone.utc) - timedelta(hours=1)
        
        result = SyncConflictService.compare_timestamps(client_ts, server_ts)
        assert result == 'client_newer'
    
    def test_compare_server_newer_timestamp(self):
        """Test comparison when server timestamp is newer."""
        client_ts = datetime.now(timezone.utc) - timedelta(hours=1)
        server_ts = datetime.now(timezone.utc)
        
        result = SyncConflictService.compare_timestamps(client_ts, server_ts)
        assert result == 'server_newer'
    
    def test_compare_missing_timestamps(self):
        """Test comparison with missing timestamps."""
        result = SyncConflictService.compare_timestamps(None, datetime.now(timezone.utc))
        assert result == 'unknown'
        
        result = SyncConflictService.compare_timestamps(datetime.now(timezone.utc), None)
        assert result == 'unknown'


class TestResolutionGuidance:
    """Test resolution guidance generation."""
    
    def test_guidance_for_missing_client_timestamp(self):
        """Test guidance when client timestamp is missing."""
        guidance = SyncConflictService._generate_resolution_guidance(
            [], 'missing_client_timestamp'
        )
        
        assert guidance['recommended_action'] == 'fetch_latest'
        assert len(guidance['options']) > 0
        assert 'timestamp' in guidance['details'].lower()
    
    def test_guidance_for_auto_resolvable_conflicts(self):
        """Test guidance for auto-resolvable conflicts."""
        conflicts = [
            ConflictDetails(
                resource_type='reading_progress',
                resource_id='test_123',
                field='offset',
                client_value=100,
                server_value=150,
                client_timestamp=datetime.now(timezone.utc),
                server_timestamp=datetime.now(timezone.utc),
                resolution_strategy=SyncConflictService.STRATEGY_SERVER_WINS
            )
        ]
        
        guidance = SyncConflictService._generate_resolution_guidance(
            conflicts, 'stale_data'
        )
        
        assert guidance['recommended_action'] == 'auto_resolve'
        assert 'automatic' in guidance['details'].lower()
    
    def test_guidance_for_manual_resolution_required(self):
        """Test guidance when manual resolution is required."""
        conflicts = [
            ConflictDetails(
                resource_type='story',
                resource_id='story_123',
                field='content',
                client_value='Client content',
                server_value='Server content',
                client_timestamp=datetime.now(timezone.utc),
                server_timestamp=datetime.now(timezone.utc),
                resolution_strategy=SyncConflictService.STRATEGY_MANUAL
            )
        ]
        
        guidance = SyncConflictService._generate_resolution_guidance(
            conflicts, 'stale_data'
        )
        
        assert guidance['recommended_action'] == 'manual_resolution'
        assert 'manual' in guidance['details'].lower()


class TestConflictDetails:
    """Test ConflictDetails dataclass."""
    
    def test_conflict_details_to_dict(self):
        """Test conversion of ConflictDetails to dictionary."""
        conflict = ConflictDetails(
            resource_type='reading_progress',
            resource_id='test_123',
            field='offset',
            client_value=100,
            server_value=150,
            client_timestamp=datetime(2024, 1, 1, 12, 0, 0),
            server_timestamp=datetime(2024, 1, 1, 13, 0, 0),
            resolution_strategy=SyncConflictService.STRATEGY_SERVER_WINS
        )
        
        result = conflict.to_dict()
        
        assert result['resource_type'] == 'reading_progress'
        assert result['resource_id'] == 'test_123'
        assert result['field'] == 'offset'
        assert result['client_value'] == 100
        assert result['server_value'] == 150
        assert result['resolution_strategy'] == SyncConflictService.STRATEGY_SERVER_WINS
        assert 'client_timestamp' in result
        assert 'server_timestamp' in result
