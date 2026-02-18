"""
Unit tests for email verification service.

Requirements: 5.1, 5.2
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta, timezone
from apps.users.email_verification.service import EmailVerificationService


class TestEmailVerificationService:
    """Test cases for EmailVerificationService."""
    
    @pytest.mark.asyncio
    @patch('apps.users.email_verification.service.Prisma')
    @patch('apps.users.email_verification.service.resend.Emails.send')
    async def test_create_verification_success(self, mock_send, mock_prisma_class):
        """Test successful verification creation and email sending."""
        # Setup mocks
        mock_db = AsyncMock()
        mock_prisma_class.return_value = mock_db
        
        mock_verification = MagicMock()
        mock_verification.id = 'verification-id'
        mock_verification.token = 'test-token'
        mock_db.emailverification.create = AsyncMock(return_value=mock_verification)
        
        mock_send.return_value = {'id': 'email-id'}
        
        # Test
        service = EmailVerificationService()
        token = await service.create_verification('user-id', 'test@example.com')
        
        # Assertions
        assert token is not None
        assert len(token) > 0
        mock_db.emailverification.create.assert_called_once()
        mock_send.assert_called_once()
        
        # Verify email parameters
        call_args = mock_send.call_args[0][0]
        assert call_args['to'] == ['test@example.com']
        assert 'Verify Your Email' in call_args['subject']
        assert token in call_args['html']
    
    @pytest.mark.asyncio
    @patch('apps.users.email_verification.service.Prisma')
    async def test_verify_token_success(self, mock_prisma_class):
        """Test successful token verification."""
        # Setup mocks
        mock_db = AsyncMock()
        mock_prisma_class.return_value = mock_db
        
        mock_verification = MagicMock()
        mock_verification.id = 'verification-id'
        mock_verification.user_id = 'user-id'
        mock_verification.expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        mock_verification.verified_at = None
        
        mock_db.emailverification.find_first = AsyncMock(return_value=mock_verification)
        mock_db.emailverification.update = AsyncMock()
        
        # Test
        service = EmailVerificationService()
        user_id = await service.verify_token('test-token')
        
        # Assertions
        assert user_id == 'user-id'
        mock_db.emailverification.update.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('apps.users.email_verification.service.Prisma')
    async def test_verify_token_expired(self, mock_prisma_class):
        """Test verification with expired token."""
        # Setup mocks
        mock_db = AsyncMock()
        mock_prisma_class.return_value = mock_db
        
        mock_verification = MagicMock()
        mock_verification.id = 'verification-id'
        mock_verification.user_id = 'user-id'
        mock_verification.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)  # Expired
        mock_verification.verified_at = None
        
        mock_db.emailverification.find_first = AsyncMock(return_value=mock_verification)
        
        # Test
        service = EmailVerificationService()
        user_id = await service.verify_token('test-token')
        
        # Assertions
        assert user_id is None
    
    @pytest.mark.asyncio
    @patch('apps.users.email_verification.service.Prisma')
    async def test_verify_token_not_found(self, mock_prisma_class):
        """Test verification with non-existent token."""
        # Setup mocks
        mock_db = AsyncMock()
        mock_prisma_class.return_value = mock_db
        mock_db.emailverification.find_first = AsyncMock(return_value=None)
        
        # Test
        service = EmailVerificationService()
        user_id = await service.verify_token('invalid-token')
        
        # Assertions
        assert user_id is None
    
    @pytest.mark.asyncio
    @patch('apps.users.email_verification.service.Prisma')
    async def test_is_email_verified_true(self, mock_prisma_class):
        """Test checking verification status for verified user."""
        # Setup mocks
        mock_db = AsyncMock()
        mock_prisma_class.return_value = mock_db
        
        mock_verification = MagicMock()
        mock_verification.verified_at = datetime.now(timezone.utc)
        
        mock_db.emailverification.find_first = AsyncMock(return_value=mock_verification)
        
        # Test
        service = EmailVerificationService()
        is_verified = await service.is_email_verified('user-id')
        
        # Assertions
        assert is_verified is True
    
    @pytest.mark.asyncio
    @patch('apps.users.email_verification.service.Prisma')
    async def test_is_email_verified_false(self, mock_prisma_class):
        """Test checking verification status for unverified user."""
        # Setup mocks
        mock_db = AsyncMock()
        mock_prisma_class.return_value = mock_db
        mock_db.emailverification.find_first = AsyncMock(return_value=None)
        
        # Test
        service = EmailVerificationService()
        is_verified = await service.is_email_verified('user-id')
        
        # Assertions
        assert is_verified is False
    
    @pytest.mark.asyncio
    @patch('apps.users.email_verification.service.Prisma')
    @patch('apps.users.email_verification.service.resend.Emails.send')
    async def test_resend_verification_success(self, mock_send, mock_prisma_class):
        """Test resending verification email."""
        # Setup mocks
        mock_db = AsyncMock()
        mock_prisma_class.return_value = mock_db
        
        # User is not verified
        mock_db.emailverification.find_first = AsyncMock(return_value=None)
        mock_db.emailverification.delete_many = AsyncMock()
        
        mock_verification = MagicMock()
        mock_verification.token = 'new-token'
        mock_db.emailverification.create = AsyncMock(return_value=mock_verification)
        
        mock_send.return_value = {'id': 'email-id'}
        
        # Test
        service = EmailVerificationService()
        success = await service.resend_verification('user-id', 'test@example.com')
        
        # Assertions
        assert success is True
        mock_db.emailverification.delete_many.assert_called_once()
        mock_send.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('apps.users.email_verification.service.Prisma')
    async def test_resend_verification_already_verified(self, mock_prisma_class):
        """Test resending verification when already verified."""
        # Setup mocks
        mock_db = AsyncMock()
        mock_prisma_class.return_value = mock_db
        
        # User is already verified
        mock_verification = MagicMock()
        mock_verification.verified_at = datetime.now(timezone.utc)
        mock_db.emailverification.find_first = AsyncMock(return_value=mock_verification)
        
        # Test
        service = EmailVerificationService()
        success = await service.resend_verification('user-id', 'test@example.com')
        
        # Assertions
        assert success is False
    
    def test_generate_token(self):
        """Test token generation produces secure tokens."""
        service = EmailVerificationService()
        
        # Generate multiple tokens
        tokens = [service._generate_token() for _ in range(10)]
        
        # Assertions
        assert len(tokens) == 10
        assert len(set(tokens)) == 10  # All unique
        for token in tokens:
            assert len(token) > 32  # Secure length
            assert isinstance(token, str)
