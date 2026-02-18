# Task 22.1: Create TOTPDevice and BackupCode Models - Implementation Summary

## Overview

This task implements the database models and encryption infrastructure required for Two-Factor Authentication (2FA) using TOTP (Time-based One-Time Password).

**Requirements Validated:** 7.1, 7.2

## Changes Made

### 1. Prisma Schema Updates

Added two new models to `apps/backend/prisma/schema.prisma`:

#### TOTPDevice Model
```prisma
model TOTPDevice {
  id           String    @id @default(uuid())
  user_id      String
  secret       String
  name         String    @default("Authenticator")
  confirmed    Boolean   @default(false)
  created_at   DateTime  @default(now())
  last_used_at DateTime?

  @@index([user_id])
  @@index([confirmed])
}
```

**Fields:**
- `id`: Unique identifier for the TOTP device
- `user_id`: Reference to the user who owns this device
- `secret`: Encrypted TOTP secret (base32 encoded)
- `name`: User-friendly name for the device (default: "Authenticator")
- `confirmed`: Whether the device has been verified by the user
- `created_at`: Timestamp when the device was created
- `last_used_at`: Timestamp of last successful authentication

**Indexes:**
- `user_id`: For efficient lookup of user's TOTP devices
- `confirmed`: For filtering confirmed vs unconfirmed devices

#### BackupCode Model
```prisma
model BackupCode {
  id         String    @id @default(uuid())
  user_id    String
  code_hash  String    @unique
  used_at    DateTime?
  created_at DateTime  @default(now())

  @@index([user_id])
  @@index([code_hash])
}
```

**Fields:**
- `id`: Unique identifier for the backup code
- `user_id`: Reference to the user who owns this code
- `code_hash`: Bcrypt hash of the backup code (for secure storage)
- `used_at`: Timestamp when the code was used (null if unused)
- `created_at`: Timestamp when the code was generated

**Indexes:**
- `user_id`: For efficient lookup of user's backup codes
- `code_hash`: For fast verification of backup codes

### 2. Encryption Utilities

Created `apps/backend/apps/core/encryption.py` with the following functions:

#### `get_encryption_key() -> bytes`
- Retrieves encryption key from `ENCRYPTION_KEY` environment variable
- Auto-generates temporary key for development/testing
- Caches key during test runs for consistency
- Raises error in production if key not configured

#### `encrypt(plaintext: str) -> str`
- Encrypts plaintext string using Fernet symmetric encryption
- Returns base64-encoded ciphertext
- Handles empty strings and None values gracefully

#### `decrypt(ciphertext: str) -> str`
- Decrypts ciphertext back to plaintext
- Raises `InvalidToken` if ciphertext is corrupted or tampered
- Handles empty strings and None values gracefully

**Encryption Details:**
- Algorithm: Fernet (AES-128-CBC with HMAC authentication)
- Key derivation: PBKDF2 with SHA256
- Includes timestamp for key rotation support
- Provides integrity verification via HMAC

### 3. Dependencies

Added to `apps/backend/requirements.txt`:
```
cryptography==42.0.5
```

### 4. Documentation

Created `apps/backend/apps/core/README_ENCRYPTION.md` with:
- Setup instructions for encryption keys
- Usage examples for encrypting/decrypting TOTP secrets
- Security considerations and best practices
- Key management and rotation procedures
- Error handling guidance
- Testing examples

### 5. Tests

Created `apps/backend/apps/core/tests/test_encryption.py` with comprehensive test coverage:

**Test Classes:**
- `TestEncryption`: Core encryption functionality tests (11 tests)
- `TestEncryptionIntegration`: Integration tests for TOTP use case (2 tests)

**Test Coverage:**
- ✅ Encryption/decryption roundtrip
- ✅ Empty string handling
- ✅ None value handling
- ✅ Long string encryption
- ✅ Special characters
- ✅ Unicode characters
- ✅ Invalid ciphertext detection
- ✅ Tampered ciphertext detection
- ✅ Key retrieval
- ✅ Deterministic decryption
- ✅ TOTP secret encryption
- ✅ Multiple independent secrets

**Test Results:** All 13 tests passing ✅

## Security Considerations

### TOTP Secret Storage
- Secrets are encrypted at rest using Fernet symmetric encryption
- Encryption key must be stored securely (environment variable)
- Different keys should be used for each environment
- Keys should never be committed to version control

### Backup Code Storage
- Backup codes are hashed using bcrypt (not encrypted)
- Codes are single-use and invalidated after use
- Each user typically has 10 backup codes

### Key Management
- Production requires explicit `ENCRYPTION_KEY` configuration
- Development/testing auto-generates temporary keys
- Key rotation is supported via Fernet's timestamp mechanism
- Lost encryption keys mean lost TOTP secrets (unrecoverable)

## Database Migration

To apply the schema changes:

```bash
cd apps/backend
prisma generate  # Generate Prisma client
prisma db push   # Apply schema to database
```

## Environment Setup

For production deployment, generate and configure encryption key:

```bash
# Generate key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Add to environment
export ENCRYPTION_KEY="your-generated-key-here"
```

## Next Steps

This task provides the foundation for 2FA implementation. Future tasks will include:

1. **Task 22.2**: Implement 2FA setup flow
   - Generate TOTP secrets
   - Create QR codes for authenticator apps
   - Generate backup codes
   - Verify setup with test code

2. **Task 22.3**: Implement 2FA login flow
   - Verify TOTP codes during login
   - Support backup code authentication
   - Track device usage

3. **Task 22.4**: Implement 2FA management
   - Disable 2FA
   - Regenerate backup codes
   - View remaining backup codes
   - Email notifications for 2FA changes

## Files Created/Modified

### Created:
- `apps/backend/apps/core/encryption.py` - Encryption utilities
- `apps/backend/apps/core/README_ENCRYPTION.md` - Documentation
- `apps/backend/apps/core/tests/test_encryption.py` - Tests
- `apps/backend/TASK_22.1_2FA_MODELS_SUMMARY.md` - This file

### Modified:
- `apps/backend/prisma/schema.prisma` - Added TOTPDevice and BackupCode models
- `apps/backend/requirements.txt` - Added cryptography dependency

## Validation

✅ Prisma schema includes TOTPDevice model with encrypted secret field  
✅ Prisma schema includes BackupCode model with hashed code field  
✅ Encryption utility implemented with Fernet  
✅ Decryption utility implemented  
✅ Comprehensive test coverage (13 tests passing)  
✅ Documentation created  
✅ Dependencies added  
✅ Prisma client generated successfully  

**Requirements 7.1 and 7.2 validated:** Database models and encryption infrastructure are in place for TOTP-based Two-Factor Authentication.
