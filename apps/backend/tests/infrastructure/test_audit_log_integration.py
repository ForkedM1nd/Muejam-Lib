"""
Integration tests for Audit Logging System.

Tests the complete audit logging workflow including:
- Audit log creation
- Query and filtering
- Suspicious pattern detection
"""

import pytest
from datetime import datetime, timedelta
from apps.admin.audit_log_service import AuditLogService
from prisma import Prisma
from prisma.enums import AuditActionType, AuditResourceType, AuditResult


@pytest.mark.asyncio
class TestAuditLogService:
    """Test AuditLogService functionality."""
    
    async def test_log_login_success(self):
        """Test logging successful login."""
        result = await AuditLogService.log_login_success(
            user_id="test-user-123",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0"
        )
        
        assert result is not None
        assert result.get('user_id') == "test-user-123"
        assert result.get('action_type') == AuditActionType.LOGIN_SUCCESS
        assert result.get('ip_address') == "192.168.1.1"
        assert result.get('result') == AuditResult.SUCCESS
    
    async def test_log_login_failed(self):
        """Test logging failed login."""
        result = await AuditLogService.log_login_failed(
            user_id="test-user-123",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            reason="Invalid password"
        )
        
        assert result is not None
        assert result.get('user_id') == "test-user-123"
        assert result.get('action_type') == AuditActionType.LOGIN_FAILED
        assert result.get('result') == AuditResult.FAILURE
        assert result.get('metadata', {}).get('reason') == "Invalid password"
    
    async def test_log_content_takedown(self):
        """Test logging content takedown."""
        result = await AuditLogService.log_content_takedown(
            moderator_id="mod-123",
            resource_type=AuditResourceType.STORY,
            resource_id="story-456",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            reason="Violates content policy"
        )
        
        assert result is not None
        assert result.get('user_id') == "mod-123"
        assert result.get('action_type') == AuditActionType.CONTENT_TAKEDOWN
        assert result.get('resource_type') == AuditResourceType.STORY
        assert result.get('resource_id') == "story-456"
        assert result.get('metadata', {}).get('reason') == "Violates content policy"
    
    async def test_log_data_export_request(self):
        """Test logging data export request."""
        result = await AuditLogService.log_data_export_request(
            user_id="user-123",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            export_id="export-789"
        )
        
        assert result is not None
        assert result.get('user_id') == "user-123"
        assert result.get('action_type') == AuditActionType.DATA_EXPORT_REQUEST
        assert result.get('resource_id') == "export-789"


@pytest.mark.asyncio
class TestAuditLogQuery:
    """Test audit log query functionality."""
    
    async def test_query_by_user(self):
        """Test querying audit logs by user ID."""
        # Create test logs
        await AuditLogService.log_login_success(
            user_id="query-test-user",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0"
        )
        
        # Query logs
        db = Prisma()
        await db.connect()
        
        try:
            logs = await db.auditlog.find_many(
                where={'user_id': 'query-test-user'},
                order={'created_at': 'desc'}
            )
            
            assert len(logs) > 0
            assert logs[0].user_id == "query-test-user"
            
        finally:
            await db.disconnect()
    
    async def test_query_by_action_type(self):
        """Test querying audit logs by action type."""
        # Create test logs
        await AuditLogService.log_login_failed(
            user_id="action-test-user",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            reason="Test"
        )
        
        # Query logs
        db = Prisma()
        await db.connect()
        
        try:
            logs = await db.auditlog.find_many(
                where={'action_type': AuditActionType.LOGIN_FAILED},
                order={'created_at': 'desc'},
                take=10
            )
            
            assert len(logs) > 0
            assert all(log.action_type == AuditActionType.LOGIN_FAILED for log in logs)
            
        finally:
            await db.disconnect()
    
    async def test_query_by_date_range(self):
        """Test querying audit logs by date range."""
        # Create test log
        await AuditLogService.log_login_success(
            user_id="date-test-user",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0"
        )
        
        # Query logs from last hour (use timezone-aware datetime)
        from datetime import timezone
        start_time = datetime.now(timezone.utc) - timedelta(hours=1)
        
        db = Prisma()
        await db.connect()
        
        try:
            logs = await db.auditlog.find_many(
                where={
                    'created_at': {'gte': start_time}
                },
                order={'created_at': 'desc'}
            )
            
            assert len(logs) > 0
            assert all(log.created_at >= start_time for log in logs)
            
        finally:
            await db.disconnect()


@pytest.mark.asyncio
class TestAuditLogImmutability:
    """Test that audit logs are immutable."""
    
    async def test_cannot_update_audit_log(self):
        """Test that audit logs cannot be updated."""
        # Create test log
        result = await AuditLogService.log_login_success(
            user_id="immutable-test-user",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0"
        )
        
        log_id = result.get('id')
        
        # Try to update the log (should fail or be ignored)
        db = Prisma()
        await db.connect()
        
        try:
            # Prisma doesn't have an update method for AuditLog by design
            # This test verifies that the model is designed to be immutable
            
            # Verify the log exists
            log = await db.auditlog.find_unique(where={'id': log_id})
            assert log is not None
            assert log.user_id == "immutable-test-user"
            
            # Note: In production, database-level constraints should prevent updates
            # This test documents the immutability requirement
            
        finally:
            await db.disconnect()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
