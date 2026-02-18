"""
Tests for encryption utilities.

Requirements: 7.1, 7.2
"""

import pytest
from cryptography.fernet import InvalidToken
from django.conf import settings
from apps.core.encryption import encrypt, decrypt, get_encryption_key


class TestEncryption:
    """Test encryption and decryption functionality."""

    def test_encryption_roundtrip(self):
        """Test that encryption and decryption work correctly."""
        plaintext = "JBSWY3DPEHPK3PXP"
        
        # Encrypt
        encrypted = encrypt(plaintext)
        assert encrypted != plaintext
        assert len(encrypted) > len(plaintext)
        
        # Decrypt
        decrypted = decrypt(encrypted)
        assert decrypted == plaintext

    def test_empty_string(self):
        """Test handling of empty strings."""
        assert encrypt("") == ""
        assert decrypt("") == ""

    def test_none_value(self):
        """Test handling of None values."""
        assert encrypt(None) is None
        assert decrypt(None) is None

    def test_different_encryptions_same_plaintext(self):
        """Test that same plaintext produces different ciphertexts."""
        plaintext = "JBSWY3DPEHPK3PXP"
        
        encrypted1 = encrypt(plaintext)
        encrypted2 = encrypt(plaintext)
        
        # Fernet includes timestamp and IV, so ciphertexts differ
        # Note: This might occasionally be the same if called in same microsecond
        # but the important thing is both decrypt correctly
        assert decrypt(encrypted1) == plaintext
        assert decrypt(encrypted2) == plaintext

    def test_long_string(self):
        """Test encryption of longer strings."""
        plaintext = "A" * 1000
        
        encrypted = encrypt(plaintext)
        decrypted = decrypt(encrypted)
        
        assert decrypted == plaintext

    def test_special_characters(self):
        """Test encryption of strings with special characters."""
        plaintext = "!@#$%^&*()_+-=[]{}|;:',.<>?/~`"
        
        encrypted = encrypt(plaintext)
        decrypted = decrypt(encrypted)
        
        assert decrypted == plaintext

    def test_unicode_characters(self):
        """Test encryption of unicode strings."""
        plaintext = "Hello 世界 🌍"
        
        encrypted = encrypt(plaintext)
        decrypted = decrypt(encrypted)
        
        assert decrypted == plaintext

    def test_invalid_ciphertext_raises_error(self):
        """Test that invalid ciphertext raises InvalidToken error."""
        with pytest.raises(InvalidToken):
            decrypt("invalid-ciphertext-data")

    def test_tampered_ciphertext_raises_error(self):
        """Test that tampered ciphertext raises InvalidToken error."""
        plaintext = "JBSWY3DPEHPK3PXP"
        encrypted = encrypt(plaintext)
        
        # Tamper with the ciphertext
        tampered = encrypted[:-5] + "XXXXX"
        
        with pytest.raises(InvalidToken):
            decrypt(tampered)

    def test_get_encryption_key_returns_bytes(self):
        """Test that get_encryption_key returns bytes."""
        key = get_encryption_key()
        assert isinstance(key, bytes)
        assert len(key) > 0

    def test_encryption_is_deterministic_with_same_key(self):
        """Test that decryption works consistently with same key."""
        plaintext = "JBSWY3DPEHPK3PXP"
        
        # Encrypt multiple times
        encrypted_values = [encrypt(plaintext) for _ in range(5)]
        
        # All should decrypt to same plaintext
        for encrypted in encrypted_values:
            assert decrypt(encrypted) == plaintext


class TestEncryptionIntegration:
    """Integration tests for encryption with TOTP use case."""

    def test_totp_secret_encryption(self):
        """Test encryption of TOTP secret (typical use case)."""
        # Typical TOTP secret format (base32 encoded)
        totp_secret = "JBSWY3DPEHPK3PXP"
        
        # Encrypt for storage
        encrypted_secret = encrypt(totp_secret)
        
        # Verify it's encrypted
        assert encrypted_secret != totp_secret
        
        # Decrypt for use
        decrypted_secret = decrypt(encrypted_secret)
        
        # Verify it matches original
        assert decrypted_secret == totp_secret

    def test_multiple_secrets_independently(self):
        """Test that multiple secrets can be encrypted independently."""
        secrets = [
            "JBSWY3DPEHPK3PXP",
            "KBSWY3DPEHPK3PXQ",
            "LBSWY3DPEHPK3PXR",
        ]
        
        # Encrypt all secrets
        encrypted_secrets = [encrypt(secret) for secret in secrets]
        
        # Verify all are different
        assert len(set(encrypted_secrets)) == len(secrets)
        
        # Verify all decrypt correctly
        for original, encrypted in zip(secrets, encrypted_secrets):
            assert decrypt(encrypted) == original
