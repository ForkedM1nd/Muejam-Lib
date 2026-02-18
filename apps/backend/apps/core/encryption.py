"""
Encryption utilities for sensitive data.

This module provides encryption and decryption functions for sensitive data
such as TOTP secrets. Uses Fernet symmetric encryption (AES-128 in CBC mode).

Requirements: 7.1, 7.2
"""

import os
from cryptography.fernet import Fernet
from django.conf import settings


# Cache for test encryption key to ensure consistency within test runs
_test_key_cache = None


def get_encryption_key() -> bytes:
    """
    Get the encryption key from settings.
    
    The key should be set in the ENCRYPTION_KEY environment variable.
    If not set, generates a temporary key for development/testing.
    
    Returns:
        bytes: The encryption key
        
    Raises:
        ValueError: If ENCRYPTION_KEY is not set in production (when DEBUG=False and not in test mode)
    """
    global _test_key_cache
    
    key = getattr(settings, 'ENCRYPTION_KEY', None)
    
    if not key:
        # Check if we're in test mode
        import sys
        is_testing = 'pytest' in sys.modules or 'test' in sys.argv
        
        # In development or testing, generate a temporary key (cached for tests)
        if settings.DEBUG or is_testing:
            if _test_key_cache is None:
                _test_key_cache = Fernet.generate_key()
            return _test_key_cache
        else:
            raise ValueError(
                "ENCRYPTION_KEY must be set in production. "
                "Generate one with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
            )
    
    # Convert string key to bytes if necessary
    if isinstance(key, str):
        key = key.encode()
    
    return key


def encrypt(plaintext: str) -> str:
    """
    Encrypt a plaintext string.
    
    Args:
        plaintext: The string to encrypt
        
    Returns:
        str: The encrypted string (base64 encoded)
        
    Example:
        >>> encrypted = encrypt("my-secret-totp-key")
        >>> decrypted = decrypt(encrypted)
        >>> assert decrypted == "my-secret-totp-key"
    """
    if not plaintext:
        return plaintext
    
    key = get_encryption_key()
    fernet = Fernet(key)
    
    # Encrypt and return as string
    encrypted_bytes = fernet.encrypt(plaintext.encode())
    return encrypted_bytes.decode()


def decrypt(ciphertext: str) -> str:
    """
    Decrypt an encrypted string.
    
    Args:
        ciphertext: The encrypted string (base64 encoded)
        
    Returns:
        str: The decrypted plaintext string
        
    Raises:
        cryptography.fernet.InvalidToken: If the ciphertext is invalid or corrupted
    """
    if not ciphertext:
        return ciphertext
    
    key = get_encryption_key()
    fernet = Fernet(key)
    
    # Decrypt and return as string
    decrypted_bytes = fernet.decrypt(ciphertext.encode())
    return decrypted_bytes.decode()
