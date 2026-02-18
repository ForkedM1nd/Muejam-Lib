# Two-Factor Authentication Service

This module provides TOTP-based Two-Factor Authentication (2FA) functionality for the MueJam Library platform.

## Overview

The `TwoFactorAuthService` handles all aspects of 2FA including:
- TOTP secret generation and QR code creation
- Backup code generation and management
- TOTP token verification
- Backup code verification

## Requirements

**Validates: Requirements 7.1, 7.2, 7.3, 7.5, 7.6**

- 7.1: Allow users to enable 2FA using TOTP authenticator apps
- 7.2: Generate QR code and backup codes when enabling 2FA
- 7.3: Require user to verify 2FA setup with valid TOTP code
- 7.5: Allow users to use backup codes if they cannot access authenticator app
- 7.6: Invalidate backup codes after use and display remaining codes

## Dependencies

```bash
pip install pyotp qrcode[pil] bcrypt
```

- `pyotp`: TOTP implementation
- `qrcode`: QR code generation
- `bcrypt`: Secure backup code hashing

## Database Models

### TOTPDevice

Stores TOTP device information:
- `id`: Unique identifier
- `user_id`: User who owns the device
- `secret`: Encrypted TOTP secret (using Fernet encryption)
- `name`: Device name (default: "Authenticator")
- `confirmed`: Whether device has been verified
- `created_at`: Creation timestamp
- `last_used_at`: Last successful verification timestamp

### BackupCode

Stores backup codes:
- `id`: Unique identifier
- `user_id`: User who owns the code
- `code_hash`: Bcrypt hash of the backup code
- `used_at`: Timestamp when code was used (null if unused)
- `created_at`: Creation timestamp

## Usage

### 1. Setup 2FA

Initialize 2FA setup for a user:

```python
from apps.users.two_factor_auth import TwoFactorAuthService

service = TwoFactorAuthService()

# Setup 2FA
result = await service.setup_2fa(
    user_id="user-123",
    user_email="user@example.com"
)

# Result contains:
# - secret: TOTP secret (base32 encoded)
# - qr_code: Base64 encoded PNG image
# - backup_codes: List of 10 backup codes
```

### 2. Verify Setup

Confirm 2FA setup by verifying a TOTP token:

```python
# User enters token from authenticator app
is_valid = await service.verify_2fa_setup(
    user_id="user-123",
    token="123456"
)

if is_valid:
    # 2FA is now enabled and confirmed
    print("2FA setup complete!")
```

### 3. Verify TOTP During Login

Verify a TOTP token during login:

```python
is_valid = await service.verify_totp(
    user_id="user-123",
    token="123456"
)

if is_valid:
    # Allow login
    print("TOTP verified!")
```

### 4. Verify Backup Code

Verify a backup code during login:

```python
is_valid, remaining = await service.verify_backup_code(
    user_id="user-123",
    code="ABCD1234"
)

if is_valid:
    print(f"Backup code verified! {remaining} codes remaining.")
```

### 5. Check if 2FA is Enabled

```python
has_2fa = await service.has_2fa_enabled(user_id="user-123")
```

### 6. Disable 2FA

```python
was_disabled = await service.disable_2fa(user_id="user-123")
```

### 7. Regenerate Backup Codes

```python
new_codes = await service.regenerate_backup_codes(user_id="user-123")
# Returns list of 10 new backup codes
```

### 8. Get Remaining Backup Codes Count

```python
count = await service.get_remaining_backup_codes_count(user_id="user-123")
print(f"User has {count} backup codes remaining")
```

## Security Features

### TOTP Secret Storage

- Secrets are encrypted at rest using Fernet symmetric encryption
- Encryption key is stored in environment variable `ENCRYPTION_KEY`
- See [Encryption Documentation](../../../../../docs/features/security/encryption.md) for key management

### Backup Code Storage

- Backup codes are hashed using bcrypt (not encrypted)
- Codes are single-use and invalidated after use
- Each user gets 10 backup codes by default

### Token Verification

- TOTP tokens use 30-second time windows
- `valid_window=1` allows for clock skew (±30 seconds)
- Tokens are 6 digits by default

### Backup Code Generation

- Uses `secrets` module for cryptographically strong randomness
- Excludes similar-looking characters (I, O, 0, 1) for easier manual entry
- 8 characters long (uppercase letters and digits)

## QR Code Format

The QR code contains a provisioning URI in the format:

```
otpauth://totp/MueJam%20Library:user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=MueJam%20Library
```

This URI is compatible with all major authenticator apps:
- Google Authenticator
- Microsoft Authenticator
- Authy
- 1Password
- etc.

## Error Handling

### Invalid Token

If TOTP verification fails, the method returns `False`. Common causes:
- Incorrect token
- Clock skew beyond valid window
- Device not confirmed
- User doesn't have 2FA enabled

### Invalid Backup Code

If backup code verification fails, returns `(False, None)`. Common causes:
- Incorrect code
- Code already used
- User doesn't have backup codes

### Decryption Errors

If secret decryption fails (e.g., wrong encryption key), `cryptography.fernet.InvalidToken` is raised.

## Testing

Example test cases:

```python
import pytest
from apps.users.two_factor_auth import TwoFactorAuthService

@pytest.mark.asyncio
async def test_2fa_setup():
    """Test 2FA setup generates secret, QR code, and backup codes."""
    service = TwoFactorAuthService()
    
    result = await service.setup_2fa(
        user_id="test-user",
        user_email="test@example.com"
    )
    
    assert 'secret' in result
    assert 'qr_code' in result
    assert 'backup_codes' in result
    assert len(result['backup_codes']) == 10

@pytest.mark.asyncio
async def test_totp_verification():
    """Test TOTP token verification."""
    service = TwoFactorAuthService()
    
    # Setup 2FA
    result = await service.setup_2fa(
        user_id="test-user",
        user_email="test@example.com"
    )
    
    # Generate valid token
    import pyotp
    totp = pyotp.TOTP(result['secret'])
    token = totp.now()
    
    # Verify setup
    is_valid = await service.verify_2fa_setup(
        user_id="test-user",
        token=token
    )
    assert is_valid

@pytest.mark.asyncio
async def test_backup_code_single_use():
    """Test backup codes can only be used once."""
    service = TwoFactorAuthService()
    
    # Setup 2FA
    result = await service.setup_2fa(
        user_id="test-user",
        user_email="test@example.com"
    )
    
    # Confirm setup
    import pyotp
    totp = pyotp.TOTP(result['secret'])
    await service.verify_2fa_setup("test-user", totp.now())
    
    # Use first backup code
    code = result['backup_codes'][0]
    is_valid, remaining = await service.verify_backup_code("test-user", code)
    assert is_valid
    assert remaining == 9
    
    # Try to use same code again
    is_valid, remaining = await service.verify_backup_code("test-user", code)
    assert not is_valid
    assert remaining is None
```

## API Integration

This service is designed to be used by API endpoints. See the API implementation for:
- POST /api/auth/2fa/setup
- POST /api/auth/2fa/verify-setup
- POST /api/auth/2fa/verify
- POST /api/auth/2fa/backup-code
- DELETE /api/auth/2fa
- POST /api/auth/2fa/regenerate-backup-codes

## Related Documentation

- [Encryption Utilities](../../../../../docs/features/security/encryption.md)
- [Requirements Document](../../../../.kiro/specs/production-readiness/requirements.md)
- [Design Document](../../../../.kiro/specs/production-readiness/design.md)
