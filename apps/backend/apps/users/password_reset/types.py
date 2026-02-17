"""
Type definitions for the password reset feature.

These types correspond to the interfaces defined in the design document.
"""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List


class AuditEventType(Enum):
    """Types of audit events for password reset operations."""
    PASSWORD_RESET_REQUESTED = 'PASSWORD_RESET_REQUESTED'
    TOKEN_VALIDATED = 'TOKEN_VALIDATED'
    PASSWORD_RESET_COMPLETED = 'PASSWORD_RESET_COMPLETED'
    RATE_LIMIT_EXCEEDED = 'RATE_LIMIT_EXCEEDED'
    INVALID_TOKEN_USED = 'INVALID_TOKEN_USED'


@dataclass
class TokenData:
    """Data returned when generating a token."""
    token: str
    expires_at: datetime


@dataclass
class TokenValidationResult:
    """Result of token validation."""
    valid: bool
    user_id: Optional[str] = None
    reason: Optional[str] = None


@dataclass
class ResetResult:
    """Result of password reset operation."""
    success: bool
    errors: List[str]


@dataclass
class ValidationResult:
    """Result of password validation."""
    valid: bool
    errors: List[str]


@dataclass
class Token:
    """Represents a password reset token in the database."""
    id: str
    user_id: str
    token_hash: str
    expires_at: datetime
    created_at: datetime
    used_at: Optional[datetime] = None
    invalidated: bool = False


@dataclass
class RateLimitEntry:
    """Tracks rate limiting attempts in cache."""
    key: str
    attempts: int
    window_start: datetime
    expires_at: datetime


@dataclass
class AuditEvent:
    """Represents a security audit log entry."""
    id: str
    event_type: AuditEventType
    user_id: Optional[str]
    email: Optional[str]
    ip_address: str
    timestamp: datetime
    success: bool
    metadata: Dict[str, Any]


@dataclass
class ErrorResponse:
    """Standard error response format."""
    success: bool = False
    error: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.error is None:
            self.error = {}
