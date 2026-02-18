# Encryption Utilities

This module provides encryption and decryption utilities for sensitive data storage, specifically designed for TOTP secrets in the Two-Factor Authentication system.

## Overview

The encryption module uses **Fernet** symmetric encryption from the `cryptography` library, which provides:
- AES-128 encryption in CBC mode
- HMAC authentication for integrity verification
- Automatic key derivation and IV generation
- Built-in timestamp support for key rotation

## Requirements

**Validates: Requirements 7.1, 7.2**

- 7.1: Two-Factor Authentication with TOTP
- 7.2: Secure storage of TOTP secrets

## Setup

### 1. Install Dependencies

```bash
pip install cryptography
```

### 2. Generate Encryption Key

Generate a new encryption key for your environment:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 3. Configure Environment

Add the encryption key to your environment variables:

```bash
# .env
ENCRYPTION_KEY=your-generated-key-here
```

**Important:** 
- Use a different key for each environment (development, staging, production)
- Never commit encryption keys to version control
- Store production keys securely (e.g., AWS Secrets Manager, HashiCorp Vault)

## Usage

### Encrypting Data

```python
from apps.core.encryption import encrypt

# Encrypt a TOTP secret
secret = "JBSWY3DPEHPK3PXP"
encrypted_secret = encrypt(secret)

# Store encrypted_secret in database
totp_device.secret = encrypted_secret
await totp_device.save()
```

### Decrypting Data

```python
from apps.core.encryption import decrypt

# Retrieve encrypted secret from database
totp_device = await TOTPDevice.prisma().find_unique(where={"id": device_id})

# Decrypt the secret
secret = decrypt(totp_device.secret)

# Use the decrypted secret
import pyotp
totp = pyotp.TOTP(secret)
is_valid = totp.verify(user_token)
```

## Security Considerations

### Key Management

1. **Key Generation**: Use `Fernet.generate_key()` to generate cryptographically secure keys
2. **Key Storage**: Store keys in secure environment variables or secret management systems
3. **Key Rotation**: Plan for periodic key rotation (Fernet supports timestamp-based rotation)
4. **Key Backup**: Securely backup encryption keys - lost keys mean lost data

### Best Practices

1. **Never log decrypted values**: Always log encrypted values or redacted placeholders
2. **Minimize decryption**: Only decrypt when necessary for operations
3. **Use in-memory only**: Don't write decrypted values to disk or cache
4. **Audit access**: Log all encryption/decryption operations for security auditing

### Development vs Production

- **Development**: The module auto-generates a temporary key if `ENCRYPTION_KEY` is not set
- **Production**: The module raises `ValueError` if `ENCRYPTION_KEY` is not configured

This ensures you never accidentally run production without proper encryption keys.

## Error Handling

### Invalid Token Error

If decryption fails, `cryptography.fernet.InvalidToken` is raised:

```python
from cryptography.fernet import InvalidToken
from apps.core.encryption import decrypt

try:
    secret = decrypt(encrypted_value)
except InvalidToken:
    # Handle corrupted or tampered data
    logger.error("Failed to decrypt TOTP secret - data may be corrupted")
    # Consider invalidating the TOTP device
```

Common causes:
- Data corruption in database
- Wrong encryption key (e.g., key was rotated)
- Tampered ciphertext
- Invalid base64 encoding

## Testing

```python
import pytest
from apps.core.encryption import encrypt, decrypt

def test_encryption_roundtrip():
    """Test that encryption and decryption work correctly."""
    plaintext = "JBSWY3DPEHPK3PXP"
    
    # Encrypt
    encrypted = encrypt(plaintext)
    assert encrypted != plaintext
    
    # Decrypt
    decrypted = decrypt(encrypted)
    assert decrypted == plaintext

def test_empty_string():
    """Test handling of empty strings."""
    assert encrypt("") == ""
    assert decrypt("") == ""

def test_different_encryptions():
    """Test that same plaintext produces different ciphertexts."""
    plaintext = "JBSWY3DPEHPK3PXP"
    
    encrypted1 = encrypt(plaintext)
    encrypted2 = encrypt(plaintext)
    
    # Fernet includes timestamp and IV, so ciphertexts differ
    assert encrypted1 != encrypted2
    
    # But both decrypt to same plaintext
    assert decrypt(encrypted1) == plaintext
    assert decrypt(encrypted2) == plaintext
```

## Key Rotation

When rotating encryption keys:

1. Keep the old key available temporarily
2. Decrypt all data with old key
3. Re-encrypt with new key
4. Update all records in database
5. Remove old key after migration complete

Example migration script:

```python
from apps.core.encryption import decrypt, encrypt
from prisma import Prisma

async def rotate_totp_secrets(old_key: str, new_key: str):
    """Rotate TOTP device secrets to new encryption key."""
    prisma = Prisma()
    await prisma.connect()
    
    # Get all TOTP devices
    devices = await prisma.totpdevice.find_many()
    
    for device in devices:
        # Decrypt with old key
        old_fernet = Fernet(old_key.encode())
        secret = old_fernet.decrypt(device.secret.encode()).decode()
        
        # Re-encrypt with new key
        new_fernet = Fernet(new_key.encode())
        new_encrypted = new_fernet.encrypt(secret.encode()).decode()
        
        # Update database
        await prisma.totpdevice.update(
            where={"id": device.id},
            data={"secret": new_encrypted}
        )
    
    await prisma.disconnect()
```

## Implementation Details

### Fernet Specification

Fernet uses:
- **Encryption**: AES-128-CBC
- **Authentication**: HMAC using SHA256
- **Key Derivation**: PBKDF2 with SHA256
- **Encoding**: Base64 URL-safe encoding

### Ciphertext Format

Fernet ciphertext includes:
1. Version byte (0x80)
2. Timestamp (8 bytes)
3. IV (16 bytes)
4. Ciphertext (variable length)
5. HMAC (32 bytes)

This ensures:
- Integrity verification (HMAC)
- Timestamp-based key rotation support
- Protection against replay attacks

## Related Documentation

- [Cryptography Library Documentation](https://cryptography.io/en/latest/fernet/)
- [TOTP Implementation](../users/README_2FA.md) (to be created)
- [Security Best Practices](../../docs/SECURITY.md) (to be created)
