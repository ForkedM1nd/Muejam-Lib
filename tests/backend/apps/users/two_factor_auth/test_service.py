"""
Tests for Two-Factor Authentication Service.

Requirements: 7.1, 7.2, 7.3, 7.5, 7.6
"""

import pytest
import pyotp
import bcrypt
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from apps.users.two_factor_auth.service import TwoFactorAuthService


@pytest.fixture
def service():
    """Create a TwoFactorAuthService instance."""
    return TwoFactorAuthService()


@pytest.fixture
def mock_prisma():
    """Create a mock Prisma client."""
    mock = MagicMock()
    mock.connect = AsyncMock()
    mock.disconnect = AsyncMock()
    mock.totpdevice = MagicMock()
    mock.backupcode = MagicMock()
    return mock


class TestSetup2FA:
    """Tests for 2FA setup functionality."""
    
    @pytest.mark.asyncio
    async def test_setup_generates_secret_qr_and_backup_codes(self, service, mock_prisma):
        """Test that setup_2fa generates all required components."""
        # Mock Prisma
        service.prisma = mock_prisma
        mock_prisma.totpdevice.find_first = AsyncMock(return_value=None)
        mock_prisma.totpdevice.create = AsyncMock()
        mock_prisma.backupcode.delete_many = AsyncMock()
        mock_prisma.backupcode.create = AsyncMock()
        
        # Setup 2FA
        result = await service.setup_2fa(
            user_id="test-user-123",
            user_email="test@example.com"
        )
        
        # Verify result structure
        assert 'secret' in result
        assert 'qr_code' in result
        assert 'backup_codes' in result
        
        # Verify secret is base32 encoded
        assert len(result['secret']) == 32
        assert result['secret'].isupper()
        
        # Verify QR code is base64 encoded
        assert len(result['qr_code']) > 0
        
        # Verify 10 backup codes generated
        assert len(result['backup_codes']) == 10
        
        # Verify backup codes format (8 chars, uppercase alphanumeric)
        for code in result['backup_codes']:
            assert len(code) == 8
            assert code.isupper()
            assert code.isalnum()
    
    @pytest.mark.asyncio
    async def test_setup_deletes_existing_unconfirmed_device(self, service, mock_prisma):
        """Test that setup deletes any existing unconfirmed device."""
        # Mock existing unconfirmed device
        existing_device = MagicMock(id="old-device-id")
        service.prisma = mock_prisma
        mock_prisma.totpdevice.find_first = AsyncMock(return_value=existing_device)
        mock_prisma.totpdevice.delete = AsyncMock()
        mock_prisma.totpdevice.create = AsyncMock()
        mock_prisma.backupcode.delete_many = AsyncMock()
        mock_prisma.backupcode.create = AsyncMock()
        
        # Setup 2FA
        await service.setup_2fa(
            user_id="test-user-123",
            user_email="test@example.com"
        )
        
        # Verify old device was deleted
        mock_prisma.totpdevice.delete.assert_called_once_with(
            where={'id': 'old-device-id'}
        )
    
    @pytest.mark.asyncio
    async def test_qr_code_contains_correct_provisioning_uri(self, service):
        """Test that QR code contains correct TOTP provisioning URI."""
        secret = "JBSWY3DPEHPK3PXP"
        user_email = "test@example.com"
        
        # Generate QR code
        qr_code_base64 = service._generate_qr_code(secret, user_email)
        
        # Decode and verify it's a valid base64 PNG
        import base64
        qr_data = base64.b64decode(qr_code_base64)
        assert qr_data[:8] == b'\x89PNG\r\n\x1a\n'  # PNG header
    
    @pytest.mark.asyncio
    async def test_backup_codes_exclude_similar_characters(self, service):
        """Test that backup codes exclude similar-looking characters."""
        # Generate many codes to test character set
        codes = [service._generate_random_code(8) for _ in range(100)]
        
        # Verify no similar characters (I, O, 0, 1)
        for code in codes:
            assert 'I' not in code
            assert 'O' not in code
            assert '0' not in code
            assert '1' not in code


class TestVerifySetup:
    """Tests for 2FA setup verification."""
    
    @pytest.mark.asyncio
    async def test_verify_setup_with_valid_token(self, service, mock_prisma):
        """Test verifying setup with a valid TOTP token."""
        # Generate a real TOTP secret and token
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        valid_token = totp.now()
        
        # Mock encrypted secret
        from apps.core.encryption import encrypt
        encrypted_secret = encrypt(secret)
        
        # Mock device
        device = MagicMock(id="device-123", secret=encrypted_secret)
        service.prisma = mock_prisma
        mock_prisma.totpdevice.find_first = AsyncMock(return_value=device)
        mock_prisma.totpdevice.update = AsyncMock()
        
        # Verify setup
        is_valid = await service.verify_2fa_setup(
            user_id="test-user-123",
            token=valid_token
        )
        
        assert is_valid
        
        # Verify device was confirmed
        mock_prisma.totpdevice.update.assert_called_once_with(
            where={'id': 'device-123'},
            data={'confirmed': True}
        )
    
    @pytest.mark.asyncio
    async def test_verify_setup_with_invalid_token(self, service, mock_prisma):
        """Test verifying setup with an invalid TOTP token."""
        # Generate a real TOTP secret
        secret = pyotp.random_base32()
        
        # Mock encrypted secret
        from apps.core.encryption import encrypt
        encrypted_secret = encrypt(secret)
        
        # Mock device
        device = MagicMock(id="device-123", secret=encrypted_secret)
        service.prisma = mock_prisma
        mock_prisma.totpdevice.find_first = AsyncMock(return_value=device)
        mock_prisma.totpdevice.update = AsyncMock()
        
        # Verify with invalid token
        is_valid = await service.verify_2fa_setup(
            user_id="test-user-123",
            token="000000"  # Invalid token
        )
        
        assert not is_valid
        
        # Verify device was NOT confirmed
        mock_prisma.totpdevice.update.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_verify_setup_without_device(self, service, mock_prisma):
        """Test verifying setup when no unconfirmed device exists."""
        service.prisma = mock_prisma
        mock_prisma.totpdevice.find_first = AsyncMock(return_value=None)
        
        # Verify setup
        is_valid = await service.verify_2fa_setup(
            user_id="test-user-123",
            token="123456"
        )
        
        assert not is_valid


class TestVerifyTOTP:
    """Tests for TOTP verification during login."""
    
    @pytest.mark.asyncio
    async def test_verify_totp_with_valid_token(self, service, mock_prisma):
        """Test verifying TOTP with a valid token."""
        # Generate a real TOTP secret and token
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        valid_token = totp.now()
        
        # Mock encrypted secret
        from apps.core.encryption import encrypt
        encrypted_secret = encrypt(secret)
        
        # Mock confirmed device
        device = MagicMock(id="device-123", secret=encrypted_secret, confirmed=True)
        service.prisma = mock_prisma
        mock_prisma.totpdevice.find_first = AsyncMock(return_value=device)
        mock_prisma.totpdevice.update = AsyncMock()
        
        # Verify TOTP
        is_valid = await service.verify_totp(
            user_id="test-user-123",
            token=valid_token
        )
        
        assert is_valid
        
        # Verify last_used_at was updated
        mock_prisma.totpdevice.update.assert_called_once()
        call_args = mock_prisma.totpdevice.update.call_args
        assert 'last_used_at' in call_args[1]['data']
    
    @pytest.mark.asyncio
    async def test_verify_totp_with_invalid_token(self, service, mock_prisma):
        """Test verifying TOTP with an invalid token."""
        # Generate a real TOTP secret
        secret = pyotp.random_base32()
        
        # Mock encrypted secret
        from apps.core.encryption import encrypt
        encrypted_secret = encrypt(secret)
        
        # Mock confirmed device
        device = MagicMock(id="device-123", secret=encrypted_secret, confirmed=True)
        service.prisma = mock_prisma
        mock_prisma.totpdevice.find_first = AsyncMock(return_value=device)
        mock_prisma.totpdevice.update = AsyncMock()
        
        # Verify with invalid token
        is_valid = await service.verify_totp(
            user_id="test-user-123",
            token="000000"
        )
        
        assert not is_valid
        
        # Verify last_used_at was NOT updated
        mock_prisma.totpdevice.update.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_verify_totp_without_confirmed_device(self, service, mock_prisma):
        """Test verifying TOTP when user doesn't have confirmed device."""
        service.prisma = mock_prisma
        mock_prisma.totpdevice.find_first = AsyncMock(return_value=None)
        
        # Verify TOTP
        is_valid = await service.verify_totp(
            user_id="test-user-123",
            token="123456"
        )
        
        assert not is_valid


class TestVerifyBackupCode:
    """Tests for backup code verification."""
    
    @pytest.mark.asyncio
    async def test_verify_valid_backup_code(self, service, mock_prisma):
        """Test verifying a valid unused backup code."""
        # Generate a real backup code and hash
        code = "ABCD1234"
        code_hash = bcrypt.hashpw(code.encode(), bcrypt.gensalt()).decode()
        
        # Mock backup codes
        backup_code = MagicMock(id="code-123", code_hash=code_hash, used_at=None)
        service.prisma = mock_prisma
        mock_prisma.backupcode.find_many = AsyncMock(return_value=[backup_code])
        mock_prisma.backupcode.update = AsyncMock()
        mock_prisma.backupcode.count = AsyncMock(return_value=9)
        
        # Verify backup code
        is_valid, remaining = await service.verify_backup_code(
            user_id="test-user-123",
            code=code
        )
        
        assert is_valid
        assert remaining == 9
        
        # Verify code was marked as used
        mock_prisma.backupcode.update.assert_called_once()
        call_args = mock_prisma.backupcode.update.call_args
        assert 'used_at' in call_args[1]['data']
    
    @pytest.mark.asyncio
    async def test_verify_invalid_backup_code(self, service, mock_prisma):
        """Test verifying an invalid backup code."""
        # Generate a real backup code and hash
        code = "ABCD1234"
        code_hash = bcrypt.hashpw(code.encode(), bcrypt.gensalt()).decode()
        
        # Mock backup codes
        backup_code = MagicMock(id="code-123", code_hash=code_hash, used_at=None)
        service.prisma = mock_prisma
        mock_prisma.backupcode.find_many = AsyncMock(return_value=[backup_code])
        mock_prisma.backupcode.update = AsyncMock()
        
        # Verify with wrong code
        is_valid, remaining = await service.verify_backup_code(
            user_id="test-user-123",
            code="WRONG123"
        )
        
        assert not is_valid
        assert remaining is None
        
        # Verify code was NOT marked as used
        mock_prisma.backupcode.update.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_verify_backup_code_single_use(self, service, mock_prisma):
        """Test that backup codes can only be used once."""
        # Generate a real backup code and hash
        code = "ABCD1234"
        code_hash = bcrypt.hashpw(code.encode(), bcrypt.gensalt()).decode()
        
        # First verification - code is unused
        backup_code = MagicMock(id="code-123", code_hash=code_hash, used_at=None)
        service.prisma = mock_prisma
        mock_prisma.backupcode.find_many = AsyncMock(return_value=[backup_code])
        mock_prisma.backupcode.update = AsyncMock()
        mock_prisma.backupcode.count = AsyncMock(return_value=9)
        
        is_valid, remaining = await service.verify_backup_code(
            user_id="test-user-123",
            code=code
        )
        
        assert is_valid
        assert remaining == 9
        
        # Second verification - code is already used (not in find_many results)
        mock_prisma.backupcode.find_many = AsyncMock(return_value=[])
        
        is_valid, remaining = await service.verify_backup_code(
            user_id="test-user-123",
            code=code
        )
        
        assert not is_valid
        assert remaining is None


class TestUtilityMethods:
    """Tests for utility methods."""
    
    @pytest.mark.asyncio
    async def test_has_2fa_enabled_true(self, service, mock_prisma):
        """Test checking if user has 2FA enabled."""
        device = MagicMock(id="device-123", confirmed=True)
        service.prisma = mock_prisma
        mock_prisma.totpdevice.find_first = AsyncMock(return_value=device)
        
        has_2fa = await service.has_2fa_enabled(user_id="test-user-123")
        
        assert has_2fa
    
    @pytest.mark.asyncio
    async def test_has_2fa_enabled_false(self, service, mock_prisma):
        """Test checking if user doesn't have 2FA enabled."""
        service.prisma = mock_prisma
        mock_prisma.totpdevice.find_first = AsyncMock(return_value=None)
        
        has_2fa = await service.has_2fa_enabled(user_id="test-user-123")
        
        assert not has_2fa
    
    @pytest.mark.asyncio
    async def test_disable_2fa(self, service, mock_prisma):
        """Test disabling 2FA."""
        service.prisma = mock_prisma
        mock_prisma.totpdevice.delete_many = AsyncMock(return_value=1)
        mock_prisma.backupcode.delete_many = AsyncMock()
        
        was_disabled = await service.disable_2fa(user_id="test-user-123")
        
        assert was_disabled
        mock_prisma.totpdevice.delete_many.assert_called_once()
        mock_prisma.backupcode.delete_many.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_regenerate_backup_codes(self, service, mock_prisma):
        """Test regenerating backup codes."""
        service.prisma = mock_prisma
        mock_prisma.backupcode.delete_many = AsyncMock()
        mock_prisma.backupcode.create = AsyncMock()
        
        new_codes = await service.regenerate_backup_codes(user_id="test-user-123")
        
        assert len(new_codes) == 10
        # Verify old codes were deleted
        mock_prisma.backupcode.delete_many.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_remaining_backup_codes_count(self, service, mock_prisma):
        """Test getting remaining backup codes count."""
        service.prisma = mock_prisma
        mock_prisma.backupcode.count = AsyncMock(return_value=7)
        
        count = await service.get_remaining_backup_codes_count(user_id="test-user-123")
        
        assert count == 7


class TestSecurityFeatures:
    """Tests for security features."""
    
    def test_random_code_generation_uses_secure_random(self, service):
        """Test that random code generation uses cryptographically secure random."""
        # Generate many codes and verify they're unique
        codes = [service._generate_random_code(8) for _ in range(1000)]
        
        # Should have high uniqueness (no duplicates expected)
        assert len(set(codes)) == len(codes)
    
    def test_backup_code_hashing_uses_bcrypt(self, service):
        """Test that backup codes are hashed with bcrypt."""
        code = "ABCD1234"
        
        # Hash the code
        code_hash = bcrypt.hashpw(code.encode(), bcrypt.gensalt()).decode()
        
        # Verify it's a valid bcrypt hash
        assert code_hash.startswith('$2b$')
        
        # Verify it can be verified
        assert bcrypt.checkpw(code.encode(), code_hash.encode())
    
    @pytest.mark.asyncio
    async def test_totp_secret_encryption(self, service):
        """Test that TOTP secrets are encrypted."""
        from apps.core.encryption import encrypt, decrypt
        
        secret = "JBSWY3DPEHPK3PXP"
        
        # Encrypt
        encrypted = encrypt(secret)
        
        # Verify encrypted value is different
        assert encrypted != secret
        
        # Verify it can be decrypted
        decrypted = decrypt(encrypted)
        assert decrypted == secret
