"""
Integration tests for requestPasswordReset method

Tests the complete flow with real service implementations.
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from ..services.password_reset_service import PasswordResetService
from ..services.token_service import TokenService
from ..services.rate_limit_service import RateLimitService
from ..services.email_service import EmailService
from ..services.audit_logger import AuditLogger
from ..repositories.token_repository import TokenRepository
from ..repositories.user_repository import UserRepository


@pytest.fixture
def mock_token_repository():
    """Mock token repository."""
    repo = AsyncMock()
    repo.create.return_value = None
    repo.invalidate_all_by_user_id.return_value = None
    return repo


@pytest.fixture
def mock_user_repository():
    """Mock user repository."""
    repo = AsyncMock()
    repo.find_by_email.return_value = {
        'id': 'user-123',
        'email': 'test@example.com',
        'password_hash': 'hashed_password',
        'previous_password_hashes': [],
    }
    return repo


@pytest.fixture
def token_service(mock_token_repository):
    """Create real TokenService with mocked repository."""
    return TokenService(token_repository=mock_token_repository)


@pytest.fixture
def rate_limit_service():
    """Create real RateLimitService."""
    return RateLimitService()


@pytest.fixture
def mock_email_service():
    """Mock email service to avoid actual email sending."""
    service = AsyncMock()
    service.send_password_reset_email.return_value = True
    return service


@pytest.fixture
def audit_logger():
    """Create real AuditLogger."""
    import logging
    logger = logging.getLogger('test_audit')
    logger.setLevel(logging.INFO)
    return AuditLogger(logger=logger)


@pytest.fixture
def mock_password_validator():
    """Mock password validator for integration tests."""
    from unittest.mock import Mock, AsyncMock
    validator = Mock()
    validator.passwords_match = Mock(return_value=True)
    validator.validate_password = AsyncMock(return_value=Mock(valid=True, errors=[]))
    return validator


@pytest.fixture
def mock_session_manager():
    """Mock session manager for integration tests."""
    manager = AsyncMock()
    manager.invalidate_all_sessions.return_value = None
    return manager


@pytest.fixture
def password_reset_service_integration(
    token_service,
    rate_limit_service,
    mock_email_service,
    audit_logger,
    mock_user_repository,
    mock_password_validator,
    mock_session_manager
):
    """Create PasswordResetService with real implementations."""
    return PasswordResetService(
        token_service=token_service,
        rate_limit_service=rate_limit_service,
        email_service=mock_email_service,
        audit_logger=audit_logger,
        user_repository=mock_user_repository,
        password_validator=mock_password_validator,
        session_manager=mock_session_manager,
    )


class TestRequestPasswordResetIntegration:
    """Integration tests for request_password_reset."""
    
    @pytest.mark.asyncio
    async def test_complete_flow_with_real_services(
        self,
        password_reset_service_integration,
        mock_email_service,
        mock_token_repository,
        rate_limit_service
    ):
        """Test complete password reset request flow with real service implementations."""
        try:
            email = 'test@example.com'
            ip_address = '192.168.1.1'
            
            result = await password_reset_service_integration.request_password_reset(email, ip_address)
            
            # Should return True
            assert result is True
            
            # Should create token in repository
            mock_token_repository.create.assert_called_once()
            token_record = mock_token_repository.create.call_args[0][0]
            assert token_record.user_id == 'user-123'
            assert token_record.expires_at is not None
            
            # Should invalidate previous tokens
            mock_token_repository.invalidate_all_by_user_id.assert_called_once_with('user-123')
            
            # Should send email
            mock_email_service.send_password_reset_email.assert_called_once()
            call_args = mock_email_service.send_password_reset_email.call_args
            assert call_args[1]['email'] == email
            assert 'token' in call_args[1]
            assert 'expiration_time' in call_args[1]
        finally:
            await rate_limit_service.clear_cache()
    
    @pytest.mark.asyncio
    async def test_rate_limiting_enforcement(
        self,
        password_reset_service_integration,
        mock_email_service,
        mock_token_repository,
        rate_limit_service
    ):
        """Test that rate limiting is enforced (Requirement 3.1)."""
        try:
            email = 'test@example.com'
            ip_address = '192.168.1.1'
            
            # Make 3 requests (should all succeed)
            for i in range(3):
                result = await password_reset_service_integration.request_password_reset(email, ip_address)
                assert result is True
            
            # Reset mocks to check 4th request
            mock_email_service.reset_mock()
            mock_token_repository.reset_mock()
            
            # 4th request should be rate limited
            result = await password_reset_service_integration.request_password_reset(email, ip_address)
            
            # Should still return True (to prevent enumeration)
            assert result is True
            
            # Should NOT generate token or send email
            mock_token_repository.create.assert_not_called()
            mock_email_service.send_password_reset_email.assert_not_called()
        finally:
            await rate_limit_service.clear_cache()
    
    @pytest.mark.asyncio
    async def test_ip_rate_limiting_enforcement(
        self,
        password_reset_service_integration,
        mock_email_service,
        mock_token_repository,
        rate_limit_service
    ):
        """Test that IP rate limiting is enforced (Requirement 3.3)."""
        try:
            ip_address = '192.168.1.1'
            
            # Make 10 requests from same IP with different emails
            for i in range(10):
                email = f'user{i}@example.com'
                result = await password_reset_service_integration.request_password_reset(email, ip_address)
                assert result is True
            
            # Reset mocks to check 11th request
            mock_email_service.reset_mock()
            mock_token_repository.reset_mock()
            
            # 11th request should be rate limited
            result = await password_reset_service_integration.request_password_reset('user11@example.com', ip_address)
            
            # Should still return True
            assert result is True
            
            # Should NOT generate token or send email
            mock_token_repository.create.assert_not_called()
            mock_email_service.send_password_reset_email.assert_not_called()
        finally:
            await rate_limit_service.clear_cache()
    
    @pytest.mark.asyncio
    async def test_token_generation_with_256_bits_entropy(
        self,
        password_reset_service_integration,
        mock_token_repository,
        rate_limit_service
    ):
        """Test that generated tokens have sufficient entropy (Requirement 2.1)."""
        try:
            email = 'test@example.com'
            ip_address = '192.168.1.1'
            
            result = await password_reset_service_integration.request_password_reset(email, ip_address)
            
            assert result is True
            
            # Check token was created
            mock_token_repository.create.assert_called_once()
            token_record = mock_token_repository.create.call_args[0][0]
            
            # Token hash should be 64 characters (SHA-256 hex)
            assert len(token_record.token_hash) == 64
            
            # Token should have expiration set to 1 hour from creation
            time_diff = (token_record.expires_at - token_record.created_at).total_seconds()
            assert 3599 <= time_diff <= 3601  # Allow 1 second tolerance
        finally:
            await rate_limit_service.clear_cache()
    
    @pytest.mark.asyncio
    async def test_audit_logging_captures_all_fields(
        self,
        password_reset_service_integration,
        audit_logger,
        rate_limit_service
    ):
        """Test that audit logging captures all required fields (Requirement 9.1)."""
        try:
            email = 'test@example.com'
            ip_address = '192.168.1.1'
            
            with patch.object(audit_logger, 'logger') as mock_logger:
                result = await password_reset_service_integration.request_password_reset(email, ip_address)
                
                assert result is True
                
                # Should have logged the request
                mock_logger.info.assert_called()
                log_message = mock_logger.info.call_args[0][0]
                
                # Verify log contains required fields
                assert 'PASSWORD_RESET_REQUEST' in log_message
                assert email in log_message
                assert ip_address in log_message
                assert 'user-123' in log_message
        finally:
            await rate_limit_service.clear_cache()
    
    @pytest.mark.asyncio
    async def test_email_enumeration_prevention(
        self,
        password_reset_service_integration,
        mock_user_repository,
        mock_email_service,
        mock_token_repository,
        rate_limit_service
    ):
        """Test that response is consistent for valid and invalid emails (Requirement 1.4)."""
        try:
            ip_address = '192.168.1.1'
            
            # Test with existing user
            mock_user_repository.find_by_email.return_value = {
                'id': 'user-123',
                'email': 'existing@example.com',
                'password_hash': 'hashed',
            }
            result1 = await password_reset_service_integration.request_password_reset('existing@example.com', ip_address)
            
            # Test with non-existing user
            mock_user_repository.find_by_email.return_value = None
            result2 = await password_reset_service_integration.request_password_reset('nonexistent@example.com', ip_address)
            
            # Both should return True
            assert result1 is True
            assert result2 is True
            
            # Email should only be sent for existing user
            assert mock_email_service.send_password_reset_email.call_count == 1
            
            # Token should only be created for existing user
            assert mock_token_repository.create.call_count == 1
        finally:
            await rate_limit_service.clear_cache()
    
    @pytest.mark.asyncio
    async def test_invalid_email_format_handling(
        self,
        password_reset_service_integration,
        mock_user_repository,
        mock_token_repository,
        rate_limit_service
    ):
        """Test that invalid email formats are rejected (Requirement 1.5)."""
        try:
            invalid_emails = [
                'not-an-email',
                'missing@',
                '@nodomain.com',
                'no-at-sign.com',
            ]
            
            for email in invalid_emails:
                result = await password_reset_service_integration.request_password_reset(email, '192.168.1.1')
                
                # Should return True to prevent enumeration
                assert result is True
                
                # Should NOT look up user or create token
                mock_user_repository.find_by_email.assert_not_called()
                mock_token_repository.create.assert_not_called()
                
                # Reset mocks
                mock_user_repository.reset_mock()
                mock_token_repository.reset_mock()
        finally:
            await rate_limit_service.clear_cache()
