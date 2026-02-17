"""
Unit tests for EmailService.

Tests email composition and delivery for password reset emails.
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock
from apps.users.password_reset.services.email_service import EmailService


@pytest.fixture
def email_service():
    """Create EmailService instance for testing."""
    return EmailService(
        frontend_url='http://localhost:3000',
        from_email='test@muejam.com'
    )


@pytest.fixture
def sample_token():
    """Sample token for testing."""
    return 'abc123def456ghi789jkl012mno345pqr678stu901vwx234yz'


@pytest.fixture
def sample_expiration():
    """Sample expiration time (1 hour from now)."""
    return datetime.now(timezone.utc) + timedelta(hours=1)


class TestEmailService:
    """Test suite for EmailService."""
    
    @pytest.mark.asyncio
    @patch('apps.users.password_reset.services.email_service.resend.Emails.send')
    async def test_send_password_reset_email_success(
        self,
        mock_send,
        email_service,
        sample_token,
        sample_expiration
    ):
        """
        Test successful password reset email sending.
        
        Requirements:
            - 1.3: Send password reset email containing the token
            - 7.1: Include direct link with embedded token
            - 7.2: Include clear instructions
            - 7.3: Include expiration time
            - 7.4: Include security warning
        """
        # Mock successful email send
        mock_send.return_value = {'id': 'email-123'}
        
        # Send email
        result = await email_service.send_password_reset_email(
            email='user@example.com',
            token=sample_token,
            expiration_time=sample_expiration
        )
        
        # Verify result
        assert result is True
        
        # Verify email was sent with correct parameters
        mock_send.assert_called_once()
        call_args = mock_send.call_args[0][0]
        
        assert call_args['from'] == 'test@muejam.com'
        assert call_args['to'] == ['user@example.com']
        assert call_args['subject'] == 'Reset Your Password'
        
        # Verify email content includes required elements
        html_content = call_args['html']
        
        # Requirement 7.1: Reset link with embedded token
        assert f'token={sample_token}' in html_content
        assert 'http://localhost:3000/reset-password' in html_content
        
        # Requirement 7.2: Clear instructions
        assert 'Reset Password' in html_content
        assert 'Click the button below' in html_content or 'click' in html_content.lower()
        
        # Requirement 7.3: Expiration time
        assert 'expire' in html_content.lower()
        assert 'minutes' in html_content.lower()
        
        # Requirement 7.4: Security warning
        assert 'did not request' in html_content.lower()
        assert 'ignore this email' in html_content.lower()
    
    @pytest.mark.asyncio
    @patch('apps.users.password_reset.services.email_service.resend.Emails.send')
    async def test_send_password_reset_email_failure(
        self,
        mock_send,
        email_service,
        sample_token,
        sample_expiration
    ):
        """
        Test email sending failure handling.
        
        Requirements:
            - 7.5: Log error when email fails to send
        """
        # Mock email send failure
        mock_send.side_effect = Exception('SMTP connection failed')
        
        # Send email
        result = await email_service.send_password_reset_email(
            email='user@example.com',
            token=sample_token,
            expiration_time=sample_expiration
        )
        
        # Verify result indicates failure
        assert result is False
    
    @pytest.mark.asyncio
    @patch('apps.users.password_reset.services.email_service.resend.Emails.send')
    async def test_send_password_reset_confirmation_success(
        self,
        mock_send,
        email_service
    ):
        """
        Test successful password reset confirmation email.
        
        Requirements:
            - 5.5: Send confirmation email after successful password reset
        """
        # Mock successful email send
        mock_send.return_value = {'id': 'email-456'}
        
        # Send confirmation email
        result = await email_service.send_password_reset_confirmation(
            email='user@example.com'
        )
        
        # Verify result
        assert result is True
        
        # Verify email was sent with correct parameters
        mock_send.assert_called_once()
        call_args = mock_send.call_args[0][0]
        
        assert call_args['from'] == 'test@muejam.com'
        assert call_args['to'] == ['user@example.com']
        assert call_args['subject'] == 'Your Password Has Been Reset'
        
        # Verify email content
        html_content = call_args['html']
        
        # Should confirm password was reset
        assert 'successfully reset' in html_content.lower()
        
        # Should include login link
        assert '/login' in html_content
        
        # Should include security notice
        assert 'did not make this change' in html_content.lower()
    
    @pytest.mark.asyncio
    @patch('apps.users.password_reset.services.email_service.resend.Emails.send')
    async def test_send_password_reset_confirmation_failure(
        self,
        mock_send,
        email_service
    ):
        """Test confirmation email sending failure handling."""
        # Mock email send failure
        mock_send.side_effect = Exception('Email service unavailable')
        
        # Send confirmation email
        result = await email_service.send_password_reset_confirmation(
            email='user@example.com'
        )
        
        # Verify result indicates failure
        assert result is False
    
    @pytest.mark.asyncio
    @patch('apps.users.password_reset.services.email_service.resend.Emails.send')
    async def test_email_content_includes_all_required_elements(
        self,
        mock_send,
        email_service,
        sample_token,
        sample_expiration
    ):
        """
        Test that password reset email includes all required content elements.
        
        Requirements:
            - 7.1: Direct link with embedded token
            - 7.2: Clear instructions
            - 7.3: Expiration time
            - 7.4: Security warning
        """
        # Mock successful email send
        mock_send.return_value = {'id': 'email-789'}
        
        # Send email
        await email_service.send_password_reset_email(
            email='user@example.com',
            token=sample_token,
            expiration_time=sample_expiration
        )
        
        # Get the HTML content
        html_content = mock_send.call_args[0][0]['html']
        
        # Verify all required elements are present
        required_elements = [
            # 7.1: Reset link with token
            f'token={sample_token}',
            '/reset-password',
            
            # 7.2: Instructions
            'Reset Password',
            'password',
            
            # 7.3: Expiration information
            'expire',
            'minutes',
            
            # 7.4: Security warning
            'did not request',
            'ignore',
        ]
        
        for element in required_elements:
            assert element.lower() in html_content.lower(), \
                f"Required element '{element}' not found in email content"
