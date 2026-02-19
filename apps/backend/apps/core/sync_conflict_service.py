"""
Sync Conflict Resolution Service for Mobile Backend Integration.

This module provides conflict detection and resolution guidance for
data synchronization operations.

Validates Requirements: 10.4
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class ConflictDetails:
    """Details about a detected sync conflict."""
    
    resource_type: str
    resource_id: str
    field: str
    client_value: Any
    server_value: Any
    client_timestamp: datetime
    server_timestamp: datetime
    resolution_strategy: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert conflict details to dictionary format."""
        return {
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'field': self.field,
            'client_value': self.client_value,
            'server_value': self.server_value,
            'client_timestamp': self.client_timestamp.isoformat() if self.client_timestamp else None,
            'server_timestamp': self.server_timestamp.isoformat() if self.server_timestamp else None,
            'resolution_strategy': self.resolution_strategy,
        }


class SyncConflictService:
    """
    Service for detecting and resolving sync conflicts.
    
    Provides version/timestamp comparison and conflict resolution guidance.
    """
    
    # Resolution strategies
    STRATEGY_SERVER_WINS = 'server_wins'
    STRATEGY_CLIENT_WINS = 'client_wins'
    STRATEGY_MANUAL = 'manual_resolution_required'
    STRATEGY_MERGE = 'merge_possible'
    
    @staticmethod
    def detect_conflict(
        resource_type: str,
        resource_id: str,
        client_data: Dict[str, Any],
        server_data: Dict[str, Any],
        client_timestamp: Optional[datetime] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Detect conflicts between client and server data.
        
        Args:
            resource_type: Type of resource (e.g., 'story', 'whisper', 'reading_progress')
            resource_id: Unique identifier of the resource
            client_data: Data submitted by client
            server_data: Current data on server
            client_timestamp: Timestamp of client's last sync (optional)
            
        Returns:
            Conflict details dictionary if conflict detected, None otherwise
        """
        # If server data doesn't exist, no conflict (new resource)
        if not server_data:
            return None
        
        # Extract timestamps for comparison
        server_updated_at = server_data.get('updated_at')
        if isinstance(server_updated_at, str):
            server_updated_at = datetime.fromisoformat(server_updated_at.replace('Z', '+00:00'))
        
        # If client has no timestamp, assume stale data
        if not client_timestamp:
            return SyncConflictService._create_conflict_response(
                resource_type=resource_type,
                resource_id=resource_id,
                client_data=client_data,
                server_data=server_data,
                client_timestamp=None,
                server_timestamp=server_updated_at,
                conflicts=[],
                reason='missing_client_timestamp'
            )
        
        # Check if server data was modified after client's last sync
        if server_updated_at and server_updated_at > client_timestamp:
            # Detect specific field conflicts
            conflicts = SyncConflictService._detect_field_conflicts(
                client_data, server_data
            )
            
            if conflicts:
                return SyncConflictService._create_conflict_response(
                    resource_type=resource_type,
                    resource_id=resource_id,
                    client_data=client_data,
                    server_data=server_data,
                    client_timestamp=client_timestamp,
                    server_timestamp=server_updated_at,
                    conflicts=conflicts,
                    reason='stale_data'
                )
        
        # No conflict detected
        return None
    
    @staticmethod
    def _detect_field_conflicts(
        client_data: Dict[str, Any],
        server_data: Dict[str, Any]
    ) -> List[ConflictDetails]:
        """
        Detect conflicts at the field level.
        
        Args:
            client_data: Data from client
            server_data: Data from server
            
        Returns:
            List of field-level conflicts
        """
        conflicts = []
        
        # Fields to check for conflicts (exclude metadata fields)
        excluded_fields = {
            'id', 'created_at', 'updated_at', 'deleted_at',
            'user_id', 'author_id'
        }
        
        # Check each field in client data
        for field, client_value in client_data.items():
            if field in excluded_fields:
                continue
            
            server_value = server_data.get(field)
            
            # If values differ, we have a conflict
            if client_value != server_value:
                # Determine resolution strategy based on field type
                strategy = SyncConflictService._determine_resolution_strategy(
                    field, client_value, server_value
                )
                
                conflict = ConflictDetails(
                    resource_type='',  # Will be set by caller
                    resource_id='',    # Will be set by caller
                    field=field,
                    client_value=client_value,
                    server_value=server_value,
                    client_timestamp=None,  # Will be set by caller
                    server_timestamp=None,  # Will be set by caller
                    resolution_strategy=strategy
                )
                conflicts.append(conflict)
        
        return conflicts
    
    @staticmethod
    def _determine_resolution_strategy(
        field: str,
        client_value: Any,
        server_value: Any
    ) -> str:
        """
        Determine the appropriate resolution strategy for a field conflict.
        
        Args:
            field: Field name
            client_value: Value from client
            server_value: Value from server
            
        Returns:
            Resolution strategy identifier
        """
        # For boolean fields, require manual resolution
        if isinstance(client_value, bool) and isinstance(server_value, bool):
            return SyncConflictService.STRATEGY_MANUAL
        
        # For numeric fields (like offset, progress), use latest value
        if isinstance(client_value, (int, float)) and isinstance(server_value, (int, float)):
            # If client value is greater, client wins (e.g., reading progress)
            if client_value > server_value:
                return SyncConflictService.STRATEGY_CLIENT_WINS
            else:
                return SyncConflictService.STRATEGY_SERVER_WINS
        
        # For text fields, require manual resolution
        if isinstance(client_value, str) and isinstance(server_value, str):
            return SyncConflictService.STRATEGY_MANUAL
        
        # Default to server wins for safety
        return SyncConflictService.STRATEGY_SERVER_WINS
    
    @staticmethod
    def _create_conflict_response(
        resource_type: str,
        resource_id: str,
        client_data: Dict[str, Any],
        server_data: Dict[str, Any],
        client_timestamp: Optional[datetime],
        server_timestamp: Optional[datetime],
        conflicts: List[ConflictDetails],
        reason: str
    ) -> Dict[str, Any]:
        """
        Create a structured conflict response.
        
        Args:
            resource_type: Type of resource
            resource_id: Resource identifier
            client_data: Client's data
            server_data: Server's data
            client_timestamp: Client's last sync timestamp
            server_timestamp: Server's last update timestamp
            conflicts: List of detected conflicts
            reason: Reason for conflict
            
        Returns:
            Structured conflict response dictionary
        """
        # Update conflict details with resource info
        for conflict in conflicts:
            conflict.resource_type = resource_type
            conflict.resource_id = resource_id
            conflict.client_timestamp = client_timestamp
            conflict.server_timestamp = server_timestamp
        
        return {
            'conflict_detected': True,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'reason': reason,
            'client_timestamp': client_timestamp.isoformat() if client_timestamp else None,
            'server_timestamp': server_timestamp.isoformat() if server_timestamp else None,
            'conflicts': [c.to_dict() for c in conflicts],
            'server_data': server_data,
            'resolution_guidance': SyncConflictService._generate_resolution_guidance(
                conflicts, reason
            )
        }
    
    @staticmethod
    def _generate_resolution_guidance(
        conflicts: List[ConflictDetails],
        reason: str
    ) -> Dict[str, Any]:
        """
        Generate guidance for resolving conflicts.
        
        Args:
            conflicts: List of detected conflicts
            reason: Reason for conflict
            
        Returns:
            Resolution guidance dictionary
        """
        guidance = {
            'recommended_action': '',
            'options': [],
            'details': ''
        }
        
        if reason == 'missing_client_timestamp':
            guidance['recommended_action'] = 'fetch_latest'
            guidance['options'] = [
                'Fetch latest server data and discard client changes',
                'Force update with client data (may overwrite server changes)'
            ]
            guidance['details'] = (
                'Client data does not include a timestamp. '
                'Recommend fetching latest server data to avoid data loss.'
            )
        elif reason == 'stale_data':
            # Analyze conflicts to determine recommendation
            auto_resolvable = all(
                c.resolution_strategy in [
                    SyncConflictService.STRATEGY_SERVER_WINS,
                    SyncConflictService.STRATEGY_CLIENT_WINS
                ]
                for c in conflicts
            )
            
            if auto_resolvable:
                guidance['recommended_action'] = 'auto_resolve'
                guidance['options'] = [
                    'Apply automatic resolution based on field-specific strategies',
                    'Fetch latest server data and retry',
                    'Force update with client data'
                ]
                guidance['details'] = (
                    'Conflicts can be automatically resolved using field-specific strategies. '
                    'Review conflict details to understand which values will be used.'
                )
            else:
                guidance['recommended_action'] = 'manual_resolution'
                guidance['options'] = [
                    'Review conflicts and manually merge changes',
                    'Fetch latest server data and discard client changes',
                    'Force update with client data (may cause data loss)'
                ]
                guidance['details'] = (
                    'Manual resolution required due to conflicting changes. '
                    'Review both client and server values to determine correct resolution.'
                )
        
        return guidance
    
    @staticmethod
    def compare_versions(
        client_version: Optional[str],
        server_version: Optional[str]
    ) -> str:
        """
        Compare version strings to determine which is newer.
        
        Args:
            client_version: Client's version string
            server_version: Server's version string
            
        Returns:
            'client_newer', 'server_newer', 'equal', or 'unknown'
        """
        if not client_version or not server_version:
            return 'unknown'
        
        if client_version == server_version:
            return 'equal'
        
        # Simple string comparison (can be enhanced with semantic versioning)
        if client_version > server_version:
            return 'client_newer'
        else:
            return 'server_newer'
    
    @staticmethod
    def compare_timestamps(
        client_timestamp: Optional[datetime],
        server_timestamp: Optional[datetime]
    ) -> str:
        """
        Compare timestamps to determine which is newer.
        
        Args:
            client_timestamp: Client's timestamp
            server_timestamp: Server's timestamp
            
        Returns:
            'client_newer', 'server_newer', 'equal', or 'unknown'
        """
        if not client_timestamp or not server_timestamp:
            return 'unknown'
        
        if client_timestamp == server_timestamp:
            return 'equal'
        elif client_timestamp > server_timestamp:
            return 'client_newer'
        else:
            return 'server_newer'
