"""
Unit tests for AuditLogger.

Tests the structured logging functionality for all audit events.
"""
import pytest
import json
import logging
from datetime import datetime
from unittest.mock import Mock, patch
from ..services.audit_logger import AuditLogger
from ..types import AuditEvent, AuditEventType


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    logger = Mock(spec=logging.Logger)
    logger.handlers = []  # Mock the handlers attribute
    return logger


@pytest.fixture
def audit_logger(mock_logger):
    """Create an AuditLogger instance with mock logger."""
    return AuditLogger(logger=mock_logger)


@pytest.fixture
def sample_timestamp():
    """Create a sample timestamp for testing."""
    return datetime(2024, 1, 15, 10, 30, 0)


class TestAuditLoggerPasswordResetRequest:
    """Tests for log_password_reset_request method."""
    
    @pytest.mark.asyncio
    async def test_logs_password_reset_request_with_all_fields(
        self, audit_logger, mock_logger, sample_timestamp
    ):
        """Test logging password reset request with all required fields."""
        event = AuditEvent(
            id="evt_123",
            event_type=AuditEventType.PASSWORD_RESET_REQUESTED,
            user_id="user_456",
            email="test@example.com",
            ip_address="192.168.1.1",
            timestamp=sample_timestamp,
            success=True,
            metadata={"source": "web"}
        )
        
        await audit_logger.log_password_reset_request(event)
        
        # Verify logger was called
        mock_logger.info.assert_called_once()
        log_message = mock_logger.info.call_args[0][0]
        
        # Verify log message format
        assert "PASSWORD_RESET_REQUEST:" in log_message
        
        # Extract and verify JSON content
        json_part = log_message.split("PASSWORD_RESET_REQUEST: ")[1]
        log_data = json.loads(json_part)
        
        assert log_data["id"] == "evt_123"
        assert log_data["event_type"] == "PASSWORD_RESET_REQUESTED"
        assert log_data["user_id"] == "user_456"
        assert log_data["email"] == "test@example.com"
        assert log_data["ip_address"] == "192.168.1.1"
        assert log_data["timestamp"] == "2024-01-15T10:30:00"
        assert log_data["success"] is True
        assert log_data["metadata"]["source"] == "web"
    
    @pytest.mark.asyncio
    async def test_logs_password_reset_request_without_optional_fields(
        self, audit_logger, mock_logger, sample_timestamp
    ):
        """Test logging password reset request without optional fields."""
        event = AuditEvent(
            id="evt_789",
            event_type=AuditEventType.PASSWORD_RESET_REQUESTED,
            user_id=None,
            email="test@example.com",
            ip_address="10.0.0.1",
            timestamp=sample_timestamp,
            success=True,
            metadata={}
        )
        
        await audit_logger.log_password_reset_request(event)
        
        mock_logger.info.assert_called_once()
        log_message = mock_logger.info.call_args[0][0]
        json_part = log_message.split("PASSWORD_RESET_REQUEST: ")[1]
        log_data = json.loads(json_part)
        
        # Verify optional fields are not present when None
        assert "user_id" not in log_data
        assert log_data["email"] == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_raises_error_for_invalid_event_type(
        self, audit_logger, sample_timestamp
    ):
        """Test that invalid event type raises ValueError."""
        event = AuditEvent(
            id="evt_invalid",
            event_type=AuditEventType.TOKEN_VALIDATED,
            user_id=None,
            email="test@example.com",
            ip_address="192.168.1.1",
            timestamp=sample_timestamp,
            success=True,
            metadata={}
        )
        
        with pytest.raises(ValueError, match="Invalid event type"):
            await audit_logger.log_password_reset_request(event)


class TestAuditLoggerTokenValidation:
    """Tests for log_token_validation method."""
    
    @pytest.mark.asyncio
    async def test_logs_successful_token_validation(
        self, audit_logger, mock_logger, sample_timestamp
    ):
        """Test logging successful token validation."""
        event = AuditEvent(
            id="evt_token_123",
            event_type=AuditEventType.TOKEN_VALIDATED,
            user_id="user_456",
            email=None,
            ip_address="192.168.1.1",
            timestamp=sample_timestamp,
            success=True,
            metadata={"token_id": "tok_abc123"}
        )
        
        await audit_logger.log_token_validation(event)
        
        mock_logger.info.assert_called_once()
        log_message = mock_logger.info.call_args[0][0]
        
        assert "TOKEN_VALIDATION:" in log_message
        json_part = log_message.split("TOKEN_VALIDATION: ")[1]
        log_data = json.loads(json_part)
        
        assert log_data["event_type"] == "TOKEN_VALIDATED"
        assert log_data["success"] is True
        assert log_data["metadata"]["token_id"] == "tok_abc123"
    
    @pytest.mark.asyncio
    async def test_logs_invalid_token_used(
        self, audit_logger, mock_logger, sample_timestamp
    ):
        """Test logging invalid token usage."""
        event = AuditEvent(
            id="evt_invalid_token",
            event_type=AuditEventType.INVALID_TOKEN_USED,
            user_id=None,
            email=None,
            ip_address="192.168.1.1",
            timestamp=sample_timestamp,
            success=False,
            metadata={"reason": "token_expired"}
        )
        
        await audit_logger.log_token_validation(event)
        
        mock_logger.info.assert_called_once()
        log_message = mock_logger.info.call_args[0][0]
        json_part = log_message.split("TOKEN_VALIDATION: ")[1]
        log_data = json.loads(json_part)
        
        assert log_data["event_type"] == "INVALID_TOKEN_USED"
        assert log_data["success"] is False
        assert log_data["metadata"]["reason"] == "token_expired"


class TestAuditLoggerPasswordReset:
    """Tests for log_password_reset method."""
    
    @pytest.mark.asyncio
    async def test_logs_successful_password_reset(
        self, audit_logger, mock_logger, sample_timestamp
    ):
        """Test logging successful password reset."""
        event = AuditEvent(
            id="evt_reset_123",
            event_type=AuditEventType.PASSWORD_RESET_COMPLETED,
            user_id="user_789",
            email="user@example.com",
            ip_address="10.0.0.5",
            timestamp=sample_timestamp,
            success=True,
            metadata={"sessions_invalidated": 3}
        )
        
        await audit_logger.log_password_reset(event)
        
        mock_logger.info.assert_called_once()
        log_message = mock_logger.info.call_args[0][0]
        
        assert "PASSWORD_RESET_COMPLETED:" in log_message
        json_part = log_message.split("PASSWORD_RESET_COMPLETED: ")[1]
        log_data = json.loads(json_part)
        
        assert log_data["event_type"] == "PASSWORD_RESET_COMPLETED"
        assert log_data["user_id"] == "user_789"
        assert log_data["ip_address"] == "10.0.0.5"
        assert log_data["success"] is True
    
    @pytest.mark.asyncio
    async def test_raises_error_for_wrong_event_type(
        self, audit_logger, sample_timestamp
    ):
        """Test that wrong event type raises ValueError."""
        event = AuditEvent(
            id="evt_wrong",
            event_type=AuditEventType.RATE_LIMIT_EXCEEDED,
            user_id="user_789",
            email=None,
            ip_address="10.0.0.5",
            timestamp=sample_timestamp,
            success=False,
            metadata={}
        )
        
        with pytest.raises(ValueError, match="Invalid event type"):
            await audit_logger.log_password_reset(event)


class TestAuditLoggerRateLimitViolation:
    """Tests for log_rate_limit_violation method."""
    
    @pytest.mark.asyncio
    async def test_logs_user_rate_limit_violation(
        self, audit_logger, mock_logger, sample_timestamp
    ):
        """Test logging user-based rate limit violation."""
        event = AuditEvent(
            id="evt_rate_limit_1",
            event_type=AuditEventType.RATE_LIMIT_EXCEEDED,
            user_id=None,
            email="spammer@example.com",
            ip_address="192.168.1.100",
            timestamp=sample_timestamp,
            success=False,
            metadata={"limit_type": "user", "attempts": 4}
        )
        
        await audit_logger.log_rate_limit_violation(event)
        
        # Rate limit violations should use warning level
        mock_logger.warning.assert_called_once()
        log_message = mock_logger.warning.call_args[0][0]
        
        assert "RATE_LIMIT_VIOLATION:" in log_message
        json_part = log_message.split("RATE_LIMIT_VIOLATION: ")[1]
        log_data = json.loads(json_part)
        
        assert log_data["event_type"] == "RATE_LIMIT_EXCEEDED"
        assert log_data["email"] == "spammer@example.com"
        assert log_data["metadata"]["limit_type"] == "user"
        assert log_data["metadata"]["attempts"] == 4
    
    @pytest.mark.asyncio
    async def test_logs_ip_rate_limit_violation(
        self, audit_logger, mock_logger, sample_timestamp
    ):
        """Test logging IP-based rate limit violation."""
        event = AuditEvent(
            id="evt_rate_limit_2",
            event_type=AuditEventType.RATE_LIMIT_EXCEEDED,
            user_id=None,
            email=None,
            ip_address="10.0.0.99",
            timestamp=sample_timestamp,
            success=False,
            metadata={"limit_type": "ip", "attempts": 11}
        )
        
        await audit_logger.log_rate_limit_violation(event)
        
        mock_logger.warning.assert_called_once()
        log_message = mock_logger.warning.call_args[0][0]
        json_part = log_message.split("RATE_LIMIT_VIOLATION: ")[1]
        log_data = json.loads(json_part)
        
        assert log_data["ip_address"] == "10.0.0.99"
        assert log_data["metadata"]["limit_type"] == "ip"


class TestAuditLoggerFormatting:
    """Tests for log formatting functionality."""
    
    def test_format_log_entry_with_all_fields(self, audit_logger, sample_timestamp):
        """Test formatting log entry with all fields present."""
        event = AuditEvent(
            id="evt_full",
            event_type=AuditEventType.PASSWORD_RESET_REQUESTED,
            user_id="user_123",
            email="test@example.com",
            ip_address="192.168.1.1",
            timestamp=sample_timestamp,
            success=True,
            metadata={"key": "value"}
        )
        
        log_entry = audit_logger._format_log_entry(event)
        log_data = json.loads(log_entry)
        
        assert log_data["id"] == "evt_full"
        assert log_data["event_type"] == "PASSWORD_RESET_REQUESTED"
        assert log_data["user_id"] == "user_123"
        assert log_data["email"] == "test@example.com"
        assert log_data["ip_address"] == "192.168.1.1"
        assert log_data["timestamp"] == "2024-01-15T10:30:00"
        assert log_data["success"] is True
        assert log_data["metadata"]["key"] == "value"
    
    def test_format_log_entry_omits_none_values(self, audit_logger, sample_timestamp):
        """Test that None values are omitted from log entry."""
        event = AuditEvent(
            id="evt_minimal",
            event_type=AuditEventType.TOKEN_VALIDATED,
            user_id=None,
            email=None,
            ip_address="10.0.0.1",
            timestamp=sample_timestamp,
            success=True,
            metadata={}
        )
        
        log_entry = audit_logger._format_log_entry(event)
        log_data = json.loads(log_entry)
        
        assert "user_id" not in log_data
        assert "email" not in log_data
        assert log_data["ip_address"] == "10.0.0.1"
