"""
Tests for PasswordResetService

Tests the main orchestration service for password reset operations.
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, Mock, patch
from apps.users.password_reset.services.password_reset_service import PasswordResetService
from apps.users.password_reset.types import TokenData, AuditEventType


@pytest.fixture
def mock_token_service():
    """Mock token service."""
    service = AsyncMock()
    service.generate_token.return_value = TokenData(
        token='test-token-123',
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
    )
    return service


@pytest.fixture
def mock_rate_limit_service():
    """Mock rate limit service."""
    service = AsyncMock()
    service.is_user_rate_limited.return_value = False
    service.is_ip_rate_limited.return_value = False
    service.record_attempt.return_value = None
    return service


@pytest.fixture
def mock_email_service():
    """Mock email service."""
    service = AsyncMock()
    service.send_password_reset_email.return_value = True
    return service


@pytest.fixture
def mock_audit_logger():
    """Mock audit logger."""
    logger = AsyncMock()
    logger.log_password_reset_request.return_value = None
    logger.log_rate_limit_violation.return_value = None
    return logger


@pytest.fixture
def mock_user_repository():
    """Mock user repository."""
    repo = AsyncMock()
    repo.find_by_email.return_value = {
        'id': 'user-123',
        'email': 'test@example.com',
        'password_hash': 'hashed_password',
    }
    return repo


@pytest.fixture
def mock_password_validator():
    """Mock password validator."""
    validator = Mock()
    validator.passwords_match = Mock(return_value=True)
    validator.validate_password = AsyncMock(return_value=Mock(valid=True, errors=[]))
    return validator


@pytest.fixture
def mock_session_manager():
    """Mock session manager."""
    manager = AsyncMock()
    manager.invalidate_all_sessions.return_value = None
    return manager


@pytest.fixture
def password_reset_service(
    mock_token_service,
    mock_rate_limit_service,
    mock_email_service,
    mock_audit_logger,
    mock_user_repository,
    mock_password_validator,
    mock_session_manager
):
    """Create PasswordResetService with mocked dependencies."""
    return PasswordResetService(
        token_service=mock_token_service,
        rate_limit_service=mock_rate_limit_service,
        email_service=mock_email_service,
        audit_logger=mock_audit_logger,
        user_repository=mock_user_repository,
        password_validator=mock_password_validator,
        session_manager=mock_session_manager,
    )


class TestRequestPasswordReset:
    """Tests for request_password_reset method."""
    
    @pytest.mark.asyncio
    async def test_valid_email_successful_flow(
        self,
        password_reset_service,
        mock_token_service,
        mock_rate_limit_service,
        mock_email_service,
        mock_audit_logger,
        mock_user_repository
    ):
        """Test successful password reset request with valid email."""
        email = 'test@example.com'
        ip_address = '192.168.1.1'
        
        result = await password_reset_service.request_password_reset(email, ip_address)
        
        # Should return True
        assert result is True
        
        # Should check rate limits
        mock_rate_limit_service.is_user_rate_limited.assert_called_once_with(email)
        mock_rate_limit_service.is_ip_rate_limited.assert_called_once_with(ip_address)
        
        # Should record attempt
        mock_rate_limit_service.record_attempt.assert_called_once_with(email, ip_address)
        
        # Should find user
        mock_user_repository.find_by_email.assert_called_once_with(email)
        
        # Should generate token
        mock_token_service.generate_token.assert_called_once_with('user-123')
        
        # Should send email
        mock_email_service.send_password_reset_email.assert_called_once()
        
        # Should log audit event
        mock_audit_logger.log_password_reset_request.assert_called_once()
        call_args = mock_audit_logger.log_password_reset_request.call_args[0][0]
        assert call_args.event_type == AuditEventType.PASSWORD_RESET_REQUESTED
        assert call_args.email == email
        assert call_args.ip_address == ip_address
        assert call_args.success is True
    
    @pytest.mark.asyncio
    async def test_invalid_email_format(
        self,
        password_reset_service,
        mock_audit_logger,
        mock_user_repository,
        mock_token_service
    ):
        """Test password reset request with invalid email format (Requirement 1.5)."""
        invalid_emails = [
            'not-an-email',
            'missing@domain',
            '@nodomain.com',
            'spaces in@email.com',
            'double@@domain.com',
        ]
        
        for email in invalid_emails:
            result = await password_reset_service.request_password_reset(email, '192.168.1.1')
            
            # Should still return True to prevent enumeration
            assert result is True
            
            # Should NOT find user or generate token
            mock_user_repository.find_by_email.assert_not_called()
            mock_token_service.generate_token.assert_not_called()
            
            # Should log the invalid attempt
            mock_audit_logger.log_password_reset_request.assert_called()
            
            # Reset mocks for next iteration
            mock_audit_logger.reset_mock()
            mock_user_repository.reset_mock()
            mock_token_service.reset_mock()
    
    @pytest.mark.asyncio
    async def test_nonexistent_user_returns_true(
        self,
        password_reset_service,
        mock_user_repository,
        mock_token_service,
        mock_email_service,
        mock_audit_logger
    ):
        """Test that nonexistent user still returns True (Requirement 1.4)."""
        # Mock user not found
        mock_user_repository.find_by_email.return_value = None
        
        email = 'nonexistent@example.com'
        ip_address = '192.168.1.1'
        
        result = await password_reset_service.request_password_reset(email, ip_address)
        
        # Should return True to prevent email enumeration
        assert result is True
        
        # Should NOT generate token or send email
        mock_token_service.generate_token.assert_not_called()
        mock_email_service.send_password_reset_email.assert_not_called()
        
        # Should still log the request
        mock_audit_logger.log_password_reset_request.assert_called_once()
        call_args = mock_audit_logger.log_password_reset_request.call_args[0][0]
        assert call_args.metadata['user_exists'] is False
    
    @pytest.mark.asyncio
    async def test_user_rate_limited(
        self,
        password_reset_service,
        mock_rate_limit_service,
        mock_audit_logger,
        mock_token_service
    ):
        """Test user rate limiting (Requirement 3.1)."""
        # Mock user rate limited
        mock_rate_limit_service.is_user_rate_limited.return_value = True
        
        email = 'test@example.com'
        ip_address = '192.168.1.1'
        
        result = await password_reset_service.request_password_reset(email, ip_address)
        
        # Should return True to prevent enumeration
        assert result is True
        
        # Should NOT generate token
        mock_token_service.generate_token.assert_not_called()
        
        # Should log rate limit violation
        mock_audit_logger.log_rate_limit_violation.assert_called_once()
        call_args = mock_audit_logger.log_rate_limit_violation.call_args[0][0]
        assert call_args.event_type == AuditEventType.RATE_LIMIT_EXCEEDED
        assert call_args.metadata['limit_type'] == 'user'
    
    @pytest.mark.asyncio
    async def test_ip_rate_limited(
        self,
        password_reset_service,
        mock_rate_limit_service,
        mock_audit_logger,
        mock_token_service
    ):
        """Test IP rate limiting (Requirement 3.3)."""
        # Mock IP rate limited
        mock_rate_limit_service.is_ip_rate_limited.return_value = True
        
        email = 'test@example.com'
        ip_address = '192.168.1.1'
        
        result = await password_reset_service.request_password_reset(email, ip_address)
        
        # Should return True to prevent enumeration
        assert result is True
        
        # Should NOT generate token
        mock_token_service.generate_token.assert_not_called()
        
        # Should log rate limit violation
        mock_audit_logger.log_rate_limit_violation.assert_called_once()
        call_args = mock_audit_logger.log_rate_limit_violation.call_args[0][0]
        assert call_args.event_type == AuditEventType.RATE_LIMIT_EXCEEDED
        assert call_args.metadata['limit_type'] == 'ip'
    
    @pytest.mark.asyncio
    async def test_email_send_failure_still_returns_true(
        self,
        password_reset_service,
        mock_email_service,
        mock_audit_logger
    ):
        """Test that email send failure still returns True."""
        # Mock email send failure
        mock_email_service.send_password_reset_email.return_value = False
        
        email = 'test@example.com'
        ip_address = '192.168.1.1'
        
        result = await password_reset_service.request_password_reset(email, ip_address)
        
        # Should still return True
        assert result is True
        
        # Should log the request with email_sent=False
        mock_audit_logger.log_password_reset_request.assert_called_once()
        call_args = mock_audit_logger.log_password_reset_request.call_args[0][0]
        assert call_args.metadata['email_sent'] is False
    
    @pytest.mark.asyncio
    async def test_consistent_response_time(
        self,
        password_reset_service,
        mock_user_repository
    ):
        """Test that response is consistent for valid and invalid emails."""
        import time
        
        # Test with existing user
        mock_user_repository.find_by_email.return_value = {
            'id': 'user-123',
            'email': 'test@example.com',
            'password_hash': 'hashed',
        }
        
        start = time.time()
        result1 = await password_reset_service.request_password_reset('test@example.com', '192.168.1.1')
        time1 = time.time() - start
        
        # Test with nonexistent user
        mock_user_repository.find_by_email.return_value = None
        
        start = time.time()
        result2 = await password_reset_service.request_password_reset('nonexistent@example.com', '192.168.1.1')
        time2 = time.time() - start
        
        # Both should return True
        assert result1 is True
        assert result2 is True
        
        # Response times should be similar (within 100ms)
        # This is a basic check - in production, more sophisticated timing attack prevention may be needed
        assert abs(time1 - time2) < 0.1


class TestValidateToken:
    """Tests for validate_token method."""
    
    @pytest.mark.asyncio
    async def test_valid_token(
        self,
        password_reset_service,
        mock_token_service,
        mock_audit_logger
    ):
        """Test validation of a valid token (Requirement 4.1)."""
        from ..types import TokenValidationResult
        
        # Mock valid token
        mock_token_service.validate_token.return_value = TokenValidationResult(
            valid=True,
            user_id='user-123',
            reason=None
        )
        
        token = 'valid-token-123'
        result = await password_reset_service.validate_token(token)
        
        # Should return valid result
        assert result.valid is True
        assert result.user_id == 'user-123'
        assert result.reason is None
        
        # Should validate token
        mock_token_service.validate_token.assert_called_once_with(token)
        
        # Should log validation attempt (Requirement 9.2)
        mock_audit_logger.log_token_validation.assert_called_once()
        call_args = mock_audit_logger.log_token_validation.call_args[0][0]
        assert call_args.event_type == AuditEventType.TOKEN_VALIDATED
        assert call_args.user_id == 'user-123'
        assert call_args.success is True
    
    @pytest.mark.asyncio
    async def test_expired_token(
        self,
        password_reset_service,
        mock_token_service,
        mock_audit_logger
    ):
        """Test validation of an expired token (Requirement 4.2)."""
        from ..types import TokenValidationResult
        
        # Mock expired token
        mock_token_service.validate_token.return_value = TokenValidationResult(
            valid=False,
            user_id=None,
            reason='Token has expired'
        )
        
        token = 'expired-token-123'
        result = await password_reset_service.validate_token(token)
        
        # Should return invalid result
        assert result.valid is False
        assert result.user_id is None
        assert result.reason == 'Token has expired'
        
        # Should log validation attempt (Requirement 9.2)
        mock_audit_logger.log_token_validation.assert_called_once()
        call_args = mock_audit_logger.log_token_validation.call_args[0][0]
        assert call_args.event_type == AuditEventType.INVALID_TOKEN_USED
        assert call_args.success is False
        assert call_args.metadata['reason'] == 'Token has expired'
    
    @pytest.mark.asyncio
    async def test_invalid_token(
        self,
        password_reset_service,
        mock_token_service,
        mock_audit_logger
    ):
        """Test validation of an invalid token (Requirement 4.3)."""
        from ..types import TokenValidationResult
        
        # Mock invalid token
        mock_token_service.validate_token.return_value = TokenValidationResult(
            valid=False,
            user_id=None,
            reason='Token does not exist or is invalid'
        )
        
        token = 'invalid-token-123'
        result = await password_reset_service.validate_token(token)
        
        # Should return invalid result
        assert result.valid is False
        assert result.user_id is None
        assert result.reason == 'Token does not exist or is invalid'
        
        # Should log validation attempt (Requirement 9.2)
        mock_audit_logger.log_token_validation.assert_called_once()
        call_args = mock_audit_logger.log_token_validation.call_args[0][0]
        assert call_args.event_type == AuditEventType.INVALID_TOKEN_USED
        assert call_args.success is False
    
    @pytest.mark.asyncio
    async def test_used_token(
        self,
        password_reset_service,
        mock_token_service,
        mock_audit_logger
    ):
        """Test validation of a previously used token (Requirement 4.4)."""
        from ..types import TokenValidationResult
        
        # Mock used token
        mock_token_service.validate_token.return_value = TokenValidationResult(
            valid=False,
            user_id=None,
            reason='Token has already been used'
        )
        
        token = 'used-token-123'
        result = await password_reset_service.validate_token(token)
        
        # Should return invalid result
        assert result.valid is False
        assert result.user_id is None
        assert result.reason == 'Token has already been used'
        
        # Should log validation attempt (Requirement 9.2)
        mock_audit_logger.log_token_validation.assert_called_once()
        call_args = mock_audit_logger.log_token_validation.call_args[0][0]
        assert call_args.event_type == AuditEventType.INVALID_TOKEN_USED
        assert call_args.success is False
        assert call_args.metadata['reason'] == 'Token has already been used'
    
    @pytest.mark.asyncio
    async def test_invalidated_token(
        self,
        password_reset_service,
        mock_token_service,
        mock_audit_logger
    ):
        """Test validation of a manually invalidated token."""
        from ..types import TokenValidationResult
        
        # Mock invalidated token
        mock_token_service.validate_token.return_value = TokenValidationResult(
            valid=False,
            user_id=None,
            reason='Token has been invalidated'
        )
        
        token = 'invalidated-token-123'
        result = await password_reset_service.validate_token(token)
        
        # Should return invalid result
        assert result.valid is False
        assert result.user_id is None
        assert result.reason == 'Token has been invalidated'
        
        # Should log validation attempt (Requirement 9.2)
        mock_audit_logger.log_token_validation.assert_called_once()
        call_args = mock_audit_logger.log_token_validation.call_args[0][0]
        assert call_args.event_type == AuditEventType.INVALID_TOKEN_USED
        assert call_args.success is False



class TestResetPassword:
    """Tests for reset_password method."""
    
    @pytest.mark.asyncio
    async def test_successful_password_reset(
        self,
        password_reset_service,
        mock_token_service,
        mock_password_validator,
        mock_user_repository,
        mock_session_manager,
        mock_email_service,
        mock_audit_logger
    ):
        """Test successful password reset flow (Requirements 5.1, 5.2, 5.3, 5.4, 5.5, 8.1, 9.3)."""
        from ..types import TokenValidationResult
        
        # Mock valid token
        mock_token_service.validate_token.return_value = TokenValidationResult(
            valid=True,
            user_id='user-123',
            reason=None
        )
        
        # Mock user data
        mock_user_repository.find_by_id.return_value = {
            'id': 'user-123',
            'email': 'test@example.com',
            'password_hash': '$2b$12$oldhashedpassword',
        }
        
        token = 'valid-token-123'
        new_password = 'NewP@ssw0rd123'
        confirm_password = 'NewP@ssw0rd123'
        ip_address = '192.168.1.1'
        
        result = await password_reset_service.reset_password(
            token, new_password, confirm_password, ip_address
        )
        
        # Should return success
        assert result.success is True
        assert len(result.errors) == 0
        
        # Should validate token
        mock_token_service.validate_token.assert_called_once_with(token)
        
        # Should check password match
        mock_password_validator.passwords_match.assert_called_once_with(
            new_password, confirm_password
        )
        
        # Should validate password
        mock_password_validator.validate_password.assert_called_once_with(
            new_password, 'user-123'
        )
        
        # Should update password
        mock_user_repository.update_password.assert_called_once()
        
        # Should invalidate token
        mock_token_service.invalidate_token.assert_called_once_with(token)
        
        # Should invalidate sessions
        mock_session_manager.invalidate_all_sessions.assert_called_once_with('user-123')
        
        # Should send confirmation email
        mock_email_service.send_password_reset_confirmation.assert_called_once_with('test@example.com')
        
        # Should log password reset
        mock_audit_logger.log_password_reset.assert_called_once()
        call_args = mock_audit_logger.log_password_reset.call_args[0][0]
        assert call_args.event_type == AuditEventType.PASSWORD_RESET_COMPLETED
        assert call_args.user_id == 'user-123'
        assert call_args.email == 'test@example.com'
        assert call_args.ip_address == ip_address
        assert call_args.success is True
    
    @pytest.mark.asyncio
    async def test_invalid_token(
        self,
        password_reset_service,
        mock_token_service,
        mock_password_validator,
        mock_user_repository
    ):
        """Test password reset with invalid token (Requirement 5.4)."""
        from ..types import TokenValidationResult
        
        # Mock invalid token
        mock_token_service.validate_token.return_value = TokenValidationResult(
            valid=False,
            user_id=None,
            reason='Token has expired'
        )
        
        token = 'invalid-token-123'
        new_password = 'NewP@ssw0rd123'
        confirm_password = 'NewP@ssw0rd123'
        ip_address = '192.168.1.1'
        
        result = await password_reset_service.reset_password(
            token, new_password, confirm_password, ip_address
        )
        
        # Should return failure
        assert result.success is False
        assert len(result.errors) > 0
        assert 'Invalid or expired token' in result.errors[0]
        
        # Should NOT update password
        mock_user_repository.update_password.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_password_mismatch(
        self,
        password_reset_service,
        mock_token_service,
        mock_password_validator,
        mock_user_repository
    ):
        """Test password reset with mismatched passwords (Requirement 5.3)."""
        from ..types import TokenValidationResult
        
        # Mock valid token
        mock_token_service.validate_token.return_value = TokenValidationResult(
            valid=True,
            user_id='user-123',
            reason=None
        )
        
        # Mock user data
        mock_user_repository.find_by_id.return_value = {
            'id': 'user-123',
            'email': 'test@example.com',
            'password_hash': '$2b$12$oldhashedpassword',
        }
        
        # Mock password mismatch
        mock_password_validator.passwords_match.return_value = False
        
        token = 'valid-token-123'
        new_password = 'NewP@ssw0rd123'
        confirm_password = 'DifferentP@ssw0rd123'
        ip_address = '192.168.1.1'
        
        result = await password_reset_service.reset_password(
            token, new_password, confirm_password, ip_address
        )
        
        # Should return failure
        assert result.success is False
        assert len(result.errors) > 0
        assert 'Password and confirmation do not match' in result.errors
        
        # Should NOT update password
        mock_user_repository.update_password.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_weak_password(
        self,
        password_reset_service,
        mock_token_service,
        mock_password_validator,
        mock_user_repository
    ):
        """Test password reset with weak password (Requirement 5.1)."""
        from ..types import TokenValidationResult, ValidationResult
        
        # Mock valid token
        mock_token_service.validate_token.return_value = TokenValidationResult(
            valid=True,
            user_id='user-123',
            reason=None
        )
        
        # Mock user data
        mock_user_repository.find_by_id.return_value = {
            'id': 'user-123',
            'email': 'test@example.com',
            'password_hash': '$2b$12$oldhashedpassword',
        }
        
        # Mock password validation failure
        mock_password_validator.validate_password.return_value = ValidationResult(
            valid=False,
            errors=['Password must be at least 8 characters long']
        )
        
        token = 'valid-token-123'
        new_password = 'weak'
        confirm_password = 'weak'
        ip_address = '192.168.1.1'
        
        result = await password_reset_service.reset_password(
            token, new_password, confirm_password, ip_address
        )
        
        # Should return failure
        assert result.success is False
        assert len(result.errors) > 0
        assert 'Password must be at least 8 characters long' in result.errors
        
        # Should NOT update password
        mock_user_repository.update_password.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_user_not_found(
        self,
        password_reset_service,
        mock_token_service,
        mock_user_repository
    ):
        """Test password reset when user is not found."""
        from ..types import TokenValidationResult
        
        # Mock valid token
        mock_token_service.validate_token.return_value = TokenValidationResult(
            valid=True,
            user_id='user-123',
            reason=None
        )
        
        # Mock user not found
        mock_user_repository.find_by_id.return_value = None
        
        token = 'valid-token-123'
        new_password = 'NewP@ssw0rd123'
        confirm_password = 'NewP@ssw0rd123'
        ip_address = '192.168.1.1'
        
        result = await password_reset_service.reset_password(
            token, new_password, confirm_password, ip_address
        )
        
        # Should return failure
        assert result.success is False
        assert len(result.errors) > 0
        assert 'User not found' in result.errors
        
        # Should NOT update password
        mock_user_repository.update_password.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_password_hashing(
        self,
        password_reset_service,
        mock_token_service,
        mock_password_validator,
        mock_user_repository,
        mock_session_manager,
        mock_email_service,
        mock_audit_logger
    ):
        """Test that password is hashed before storage (Requirement 6.5)."""
        from ..types import TokenValidationResult
        import bcrypt
        
        # Mock valid token
        mock_token_service.validate_token.return_value = TokenValidationResult(
            valid=True,
            user_id='user-123',
            reason=None
        )
        
        # Mock user data
        mock_user_repository.find_by_id.return_value = {
            'id': 'user-123',
            'email': 'test@example.com',
            'password_hash': '$2b$12$oldhashedpassword',
        }
        
        token = 'valid-token-123'
        new_password = 'NewP@ssw0rd123'
        confirm_password = 'NewP@ssw0rd123'
        ip_address = '192.168.1.1'
        
        result = await password_reset_service.reset_password(
            token, new_password, confirm_password, ip_address
        )
        
        # Should return success
        assert result.success is True
        
        # Should update password with hashed value
        mock_user_repository.update_password.assert_called_once()
        call_args = mock_user_repository.update_password.call_args
        
        # Verify password_hash is a bcrypt hash
        password_hash = call_args.kwargs['password_hash']
        assert password_hash.startswith('$2b$')
        
        # Verify the hash matches the password
        assert bcrypt.checkpw(new_password.encode('utf-8'), password_hash.encode('utf-8'))
        
        # Verify the hash is NOT the plaintext password
        assert password_hash != new_password
