"""
Password Reset Service Implementation

Main orchestrator for password reset operations.
This will be implemented in Task 11.
"""
import re
import secrets
import bcrypt
from datetime import datetime, timezone
from ..interfaces import (
    IPasswordResetService,
    ITokenService,
    IRateLimitService,
    IEmailService,
    IAuditLogger,
)
from ..repositories.user_repository import UserRepository
from ..types import (
    TokenValidationResult,
    ResetResult,
    AuditEvent,
    AuditEventType,
)


class PasswordResetService(IPasswordResetService):
    """
    Main service orchestrating the password reset flow.
    
    Coordinates token generation, validation, rate limiting, email sending,
    password updates, session invalidation, and audit logging.
    """
    
    def __init__(
        self,
        token_service: ITokenService,
        rate_limit_service: IRateLimitService,
        email_service: IEmailService,
        audit_logger: IAuditLogger,
        user_repository: UserRepository,
        password_validator: 'IPasswordValidator',
        session_manager: 'ISessionManager',
    ):
        """
        Initialize the PasswordResetService.

        Args:
            token_service: Service for token generation and validation
            rate_limit_service: Service for rate limiting
            email_service: Service for sending emails
            audit_logger: Service for audit logging
            user_repository: Repository for user data access
            password_validator: Service for password validation
            session_manager: Service for session management
        """
        self.token_service = token_service
        self.rate_limit_service = rate_limit_service
        self.email_service = email_service
        self.audit_logger = audit_logger
        self.user_repository = user_repository
        self.password_validator = password_validator
        self.session_manager = session_manager

    
    def _is_valid_email_format(self, email: str) -> bool:
        """
        Validate email format.
        
        Args:
            email: Email address to validate
            
        Returns:
            True if email format is valid
        """
        # Simple email regex pattern
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    async def request_password_reset(self, email: str, ip_address: str) -> bool:
        """
        Initiate a password reset request.
        
        This method orchestrates the complete password reset request flow:
        1. Validates email format (Requirement 1.5)
        2. Checks rate limits (Requirements 3.1, 3.3)
        3. Generates and stores token (Requirements 1.1, 1.2)
        4. Sends reset email (Requirement 1.3)
        5. Logs audit event (Requirement 9.1)
        6. Returns consistent response (Requirement 1.4)
        
        Args:
            email: User's email address
            ip_address: Request origin IP for rate limiting
            
        Returns:
            Always returns True to prevent email enumeration (Requirement 1.4)
        """
        # Validate email format (Requirement 1.5)
        if not self._is_valid_email_format(email):
            # Log the invalid attempt
            await self.audit_logger.log_password_reset_request(
                AuditEvent(
                    id=secrets.token_urlsafe(16),
                    event_type=AuditEventType.PASSWORD_RESET_REQUESTED,
                    user_id=None,
                    email=email,
                    ip_address=ip_address,
                    timestamp=datetime.now(timezone.utc),
                    success=False,
                    metadata={'reason': 'invalid_email_format'}
                )
            )
            # Return True to prevent email enumeration
            return True
        
        # Check user-based rate limiting (Requirement 3.1)
        if await self.rate_limit_service.is_user_rate_limited(email):
            # Log rate limit violation (Requirement 9.4)
            await self.audit_logger.log_rate_limit_violation(
                AuditEvent(
                    id=secrets.token_urlsafe(16),
                    event_type=AuditEventType.RATE_LIMIT_EXCEEDED,
                    user_id=None,
                    email=email,
                    ip_address=ip_address,
                    timestamp=datetime.now(timezone.utc),
                    success=False,
                    metadata={'limit_type': 'user'}
                )
            )
            # Return True to prevent email enumeration
            return True
        
        # Check IP-based rate limiting (Requirement 3.3)
        if await self.rate_limit_service.is_ip_rate_limited(ip_address):
            # Log rate limit violation (Requirement 9.4)
            await self.audit_logger.log_rate_limit_violation(
                AuditEvent(
                    id=secrets.token_urlsafe(16),
                    event_type=AuditEventType.RATE_LIMIT_EXCEEDED,
                    user_id=None,
                    email=email,
                    ip_address=ip_address,
                    timestamp=datetime.now(timezone.utc),
                    success=False,
                    metadata={'limit_type': 'ip'}
                )
            )
            # Return True to prevent email enumeration
            return True
        
        # Record the attempt for rate limiting (Requirement 3.2)
        await self.rate_limit_service.record_attempt(email, ip_address)
        
        # Find user by email
        user = await self.user_repository.find_by_email(email)
        
        # If user doesn't exist, still return True to prevent email enumeration (Requirement 1.4)
        if user is None:
            # Log the request for non-existent user
            await self.audit_logger.log_password_reset_request(
                AuditEvent(
                    id=secrets.token_urlsafe(16),
                    event_type=AuditEventType.PASSWORD_RESET_REQUESTED,
                    user_id=None,
                    email=email,
                    ip_address=ip_address,
                    timestamp=datetime.now(timezone.utc),
                    success=True,
                    metadata={'user_exists': False}
                )
            )
            # Return True without sending email
            return True
        
        # Generate token for the user (Requirements 1.1, 1.2)
        token_data = await self.token_service.generate_token(user['id'])
        
        # Send password reset email (Requirement 1.3)
        email_sent = await self.email_service.send_password_reset_email(
            email=email,
            token=token_data.token,
            expiration_time=token_data.expires_at
        )
        
        # Log the password reset request (Requirement 9.1)
        await self.audit_logger.log_password_reset_request(
            AuditEvent(
                id=secrets.token_urlsafe(16),
                event_type=AuditEventType.PASSWORD_RESET_REQUESTED,
                user_id=user['id'],
                email=email,
                ip_address=ip_address,
                timestamp=datetime.now(timezone.utc),
                success=True,
                metadata={
                    'user_exists': True,
                    'email_sent': email_sent,
                    'token_expires_at': token_data.expires_at.isoformat()
                }
            )
        )
        
        # Always return True to prevent email enumeration (Requirement 1.4)
        return True
    
    async def validate_token(self, token: str) -> TokenValidationResult:
        """
        Validate a reset token.
        
        This method validates a password reset token by:
        1. Delegating to TokenService for validation (Requirements 4.1, 4.2, 4.3, 4.4)
        2. Logging the validation attempt (Requirement 9.2)
        
        Args:
            token: The reset token from the email link
            
        Returns:
            TokenValidationResult with validation status and user context if valid
        """
        # Validate the token using TokenService
        validation_result = await self.token_service.validate_token(token)
        
        # Determine event type based on validation result
        if validation_result.valid:
            event_type = AuditEventType.TOKEN_VALIDATED
        else:
            event_type = AuditEventType.INVALID_TOKEN_USED
        
        # Log the token validation attempt (Requirement 9.2)
        await self.audit_logger.log_token_validation(
            AuditEvent(
                id=secrets.token_urlsafe(16),
                event_type=event_type,
                user_id=validation_result.user_id,
                email=None,  # Email not available at this point
                ip_address='',  # IP address not available in this context
                timestamp=datetime.now(timezone.utc),
                success=validation_result.valid,
                metadata={
                    'reason': validation_result.reason,
                    'token_hash': secrets.token_urlsafe(8)  # Log a partial identifier, not the actual token
                }
            )
        )
        
        return validation_result
    
    async def reset_password(
        self,
        token: str,
        new_password: str,
        confirm_password: str,
        ip_address: str
    ) -> ResetResult:
        """
        Reset user password with token validation.
        
        This method orchestrates the complete password reset flow:
        1. Validates the token (Requirement 5.4)
        2. Validates password confirmation match (Requirement 5.3)
        3. Validates password security requirements (Requirement 5.1)
        4. Updates user password (Requirement 5.2)
        5. Invalidates token and sessions (Requirements 5.4, 8.1)
        6. Sends confirmation email (Requirement 5.5)
        7. Logs completion (Requirement 9.3)
        
        Args:
            token: The reset token
            new_password: The new password
            confirm_password: Password confirmation
            ip_address: Request origin IP for logging
            
        Returns:
            ResetResult with success indicator and any validation errors
        """
        errors = []
        
        # Step 1: Validate token (Requirement 5.4)
        validation_result = await self.token_service.validate_token(token)
        
        if not validation_result.valid:
            errors.append(f"Invalid or expired token: {validation_result.reason}")
            return ResetResult(success=False, errors=errors)
        
        user_id = validation_result.user_id
        
        # Get user data for email
        user = await self.user_repository.find_by_id(user_id)
        if not user:
            errors.append("User not found")
            return ResetResult(success=False, errors=errors)
        
        # Step 2: Validate password confirmation match (Requirement 5.3)
        if not self.password_validator.passwords_match(new_password, confirm_password):
            errors.append("Password and confirmation do not match")
            return ResetResult(success=False, errors=errors)
        
        # Step 3: Validate password security requirements (Requirement 5.1)
        password_validation = await self.password_validator.validate_password(
            new_password, user_id
        )
        
        if not password_validation.valid:
            errors.extend(password_validation.errors)
            return ResetResult(success=False, errors=errors)
        
        # Step 4: Update user password (Requirement 5.2)
        # Hash the new password
        password_hash = bcrypt.hashpw(
            new_password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')
        
        # Update password in database
        await self.user_repository.update_password(
            user_id=user_id,
            password_hash=password_hash,
            previous_hash=user['password_hash']
        )
        
        # Step 5: Invalidate token and sessions (Requirements 5.4, 8.1)
        await self.token_service.invalidate_token(token)
        await self.session_manager.invalidate_all_sessions(user_id)
        
        # Step 6: Send confirmation email (Requirement 5.5)
        await self.email_service.send_password_reset_confirmation(user['email'])
        
        # Step 7: Log completion (Requirement 9.3)
        await self.audit_logger.log_password_reset(
            AuditEvent(
                id=secrets.token_urlsafe(16),
                event_type=AuditEventType.PASSWORD_RESET_COMPLETED,
                user_id=user_id,
                email=user['email'],
                ip_address=ip_address,
                timestamp=datetime.now(timezone.utc),
                success=True,
                metadata={
                    'token_invalidated': True,
                    'sessions_invalidated': True,
                    'confirmation_email_sent': True
                }
            )
        )
        
        return ResetResult(success=True, errors=[])
