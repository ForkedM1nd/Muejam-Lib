"""
Audit Logger Implementation

Records security-relevant events with structured logging.
"""
import logging
import json
from typing import Dict, Any
from ..interfaces import IAuditLogger
from ..types import AuditEvent, AuditEventType


class AuditLogger(IAuditLogger):
    """
    Service for logging security audit events.
    
    Implements comprehensive logging of all password reset activities
    for security monitoring and incident investigation.
    
    Uses structured JSON logging to ensure all required fields are captured
    and logs are machine-readable for analysis.
    """
    
    def __init__(self, logger: logging.Logger = None):
        """
        Initialize the audit logger.
        
        Args:
            logger: Optional logger instance. If not provided, creates a new logger.
        """
        self.logger = logger or logging.getLogger('password_reset.audit')
        if not self.logger.handlers:
            # Configure default handler if none exists
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(message)s'))
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def _format_log_entry(self, event: AuditEvent) -> str:
        """
        Format audit event as structured JSON log entry.
        
        Args:
            event: The audit event to format
            
        Returns:
            JSON string with all required fields
        """
        log_data: Dict[str, Any] = {
            'id': event.id,
            'event_type': event.event_type.value,
            'timestamp': event.timestamp.isoformat(),
            'ip_address': event.ip_address,
            'success': event.success,
        }
        
        # Add optional fields if present
        if event.user_id:
            log_data['user_id'] = event.user_id
        if event.email:
            log_data['email'] = event.email
        if event.metadata:
            log_data['metadata'] = event.metadata
        
        return json.dumps(log_data)
    
    async def log_password_reset_request(self, event: AuditEvent) -> None:
        """
        Log a password reset request.
        
        Captures: email address, timestamp, and IP address.
        Validates: Requirements 9.1
        
        Args:
            event: The audit event details
        """
        if event.event_type != AuditEventType.PASSWORD_RESET_REQUESTED:
            raise ValueError(
                f"Invalid event type for password reset request: {event.event_type}"
            )
        
        log_entry = self._format_log_entry(event)
        self.logger.info(f"PASSWORD_RESET_REQUEST: {log_entry}")
    
    async def log_token_validation(self, event: AuditEvent) -> None:
        """
        Log a token validation attempt.
        
        Captures: token identifier, validation result, and timestamp.
        Validates: Requirements 9.2
        
        Args:
            event: The audit event details
        """
        if event.event_type not in (
            AuditEventType.TOKEN_VALIDATED,
            AuditEventType.INVALID_TOKEN_USED
        ):
            raise ValueError(
                f"Invalid event type for token validation: {event.event_type}"
            )
        
        log_entry = self._format_log_entry(event)
        self.logger.info(f"TOKEN_VALIDATION: {log_entry}")
    
    async def log_password_reset(self, event: AuditEvent) -> None:
        """
        Log a successful password reset.
        
        Captures: user account identifier, timestamp, and IP address.
        Validates: Requirements 9.3
        
        Args:
            event: The audit event details
        """
        if event.event_type != AuditEventType.PASSWORD_RESET_COMPLETED:
            raise ValueError(
                f"Invalid event type for password reset: {event.event_type}"
            )
        
        log_entry = self._format_log_entry(event)
        self.logger.info(f"PASSWORD_RESET_COMPLETED: {log_entry}")
    
    async def log_rate_limit_violation(self, event: AuditEvent) -> None:
        """
        Log a rate limit violation.
        
        Captures: email address or IP address, timestamp, and rate limit type.
        Validates: Requirements 9.4
        
        Args:
            event: The audit event details
        """
        if event.event_type != AuditEventType.RATE_LIMIT_EXCEEDED:
            raise ValueError(
                f"Invalid event type for rate limit violation: {event.event_type}"
            )
        
        log_entry = self._format_log_entry(event)
        self.logger.warning(f"RATE_LIMIT_VIOLATION: {log_entry}")
