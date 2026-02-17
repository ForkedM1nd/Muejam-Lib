"""
Service interfaces for the password reset feature.

These interfaces define the contracts for all services in the password reset system.
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
from .types import (
    TokenData,
    TokenValidationResult,
    ResetResult,
    ValidationResult,
    AuditEvent,
)


class ITokenService(ABC):
    """Interface for token generation and validation."""
    
    @abstractmethod
    async def generate_token(self, user_id: str) -> TokenData:
        """
        Generates a cryptographically secure token.
        
        Args:
            user_id: The user ID for whom the token is generated
            
        Returns:
            TokenData with token string and expiration timestamp
        """
        pass
    
    @abstractmethod
    async def validate_token(self, token: str) -> TokenValidationResult:
        """
        Validates token and checks expiration.
        
        Args:
            token: The token to validate
            
        Returns:
            TokenValidationResult with validation status and user ID if valid
        """
        pass
    
    @abstractmethod
    async def invalidate_token(self, token: str) -> None:
        """
        Invalidates a specific token.
        
        Args:
            token: The token to invalidate
        """
        pass
    
    @abstractmethod
    async def invalidate_all_user_tokens(self, user_id: str) -> None:
        """
        Invalidates all tokens for a user.
        
        Args:
            user_id: The user ID
        """
        pass


class IRateLimitService(ABC):
    """Interface for rate limiting."""
    
    @abstractmethod
    async def is_user_rate_limited(self, email: str) -> bool:
        """
        Checks if a user has exceeded rate limits.
        
        Args:
            email: User's email address
            
        Returns:
            True if rate limit exceeded
        """
        pass
    
    @abstractmethod
    async def is_ip_rate_limited(self, ip_address: str) -> bool:
        """
        Checks if an IP address has exceeded rate limits.
        
        Args:
            ip_address: The IP address
            
        Returns:
            True if rate limit exceeded
        """
        pass
    
    @abstractmethod
    async def record_attempt(self, email: str, ip_address: str) -> None:
        """
        Records a password reset attempt.
        
        Args:
            email: User's email address
            ip_address: Request origin IP
        """
        pass


class IEmailService(ABC):
    """Interface for email operations."""
    
    @abstractmethod
    async def send_password_reset_email(
        self,
        email: str,
        token: str,
        expiration_time: datetime
    ) -> bool:
        """
        Sends password reset email.
        
        Args:
            email: Recipient email address
            token: Reset token to include in link
            expiration_time: Token expiration timestamp
            
        Returns:
            True if email sent successfully
        """
        pass
    
    @abstractmethod
    async def send_password_reset_confirmation(self, email: str) -> bool:
        """
        Sends password reset confirmation email.
        
        Args:
            email: Recipient email address
            
        Returns:
            True if email sent successfully
        """
        pass


class IPasswordValidator(ABC):
    """Interface for password validation."""
    
    @abstractmethod
    async def validate_password(self, password: str, user_id: str) -> ValidationResult:
        """
        Validates password meets security requirements.
        
        Args:
            password: The password to validate
            user_id: User ID to check against previous passwords
            
        Returns:
            ValidationResult with validation status and error messages
        """
        pass
    
    @abstractmethod
    def passwords_match(self, password: str, confirm_password: str) -> bool:
        """
        Checks if passwords match.
        
        Args:
            password: The password
            confirm_password: The confirmation password
            
        Returns:
            True if passwords match
        """
        pass


class ISessionManager(ABC):
    """Interface for session management."""
    
    @abstractmethod
    async def invalidate_all_sessions(self, user_id: str) -> None:
        """
        Invalidates all active sessions for a user.
        
        Args:
            user_id: The user ID
        """
        pass


class IAuditLogger(ABC):
    """Interface for audit logging."""
    
    @abstractmethod
    async def log_password_reset_request(self, event: AuditEvent) -> None:
        """
        Logs a password reset request.
        
        Args:
            event: The audit event details
        """
        pass
    
    @abstractmethod
    async def log_token_validation(self, event: AuditEvent) -> None:
        """
        Logs a token validation attempt.
        
        Args:
            event: The audit event details
        """
        pass
    
    @abstractmethod
    async def log_password_reset(self, event: AuditEvent) -> None:
        """
        Logs a successful password reset.
        
        Args:
            event: The audit event details
        """
        pass
    
    @abstractmethod
    async def log_rate_limit_violation(self, event: AuditEvent) -> None:
        """
        Logs a rate limit violation.
        
        Args:
            event: The audit event details
        """
        pass


class IPasswordResetService(ABC):
    """Interface for the main password reset orchestration service."""
    
    @abstractmethod
    async def request_password_reset(self, email: str, ip_address: str) -> bool:
        """
        Initiates a password reset request.
        
        Args:
            email: User's email address
            ip_address: Request origin IP for rate limiting
            
        Returns:
            Success indicator (always true to prevent email enumeration)
        """
        pass
    
    @abstractmethod
    async def validate_token(self, token: str) -> TokenValidationResult:
        """
        Validates a reset token.
        
        Args:
            token: The reset token from the email link
            
        Returns:
            Token validation result with user context if valid
        """
        pass
    
    @abstractmethod
    async def reset_password(
        self,
        token: str,
        new_password: str,
        confirm_password: str,
        ip_address: str
    ) -> ResetResult:
        """
        Resets user password with token validation.
        
        Args:
            token: The reset token
            new_password: The new password
            confirm_password: Password confirmation
            ip_address: Request origin IP for logging
            
        Returns:
            ResetResult with success indicator and any validation errors
        """
        pass
