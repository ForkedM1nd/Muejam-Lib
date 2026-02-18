"""
Two-Factor Authentication Service.

This service handles TOTP-based 2FA setup, verification, and backup code management.

Requirements: 7.1, 7.2, 7.3, 7.5, 7.6
"""

import io
import secrets
import bcrypt
import pyotp
import qrcode
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone

from prisma import Prisma
from apps.core.encryption import encrypt, decrypt


class TwoFactorAuthService:
    """
    Service for managing Two-Factor Authentication with TOTP.
    
    This service provides:
    - TOTP secret generation and QR code creation
    - Backup code generation and management
    - TOTP token verification
    - Backup code verification
    """
    
    def __init__(self):
        self.prisma = Prisma()
    
    async def setup_2fa(self, user_id: str, user_email: str) -> Dict:
        """
        Initialize 2FA setup for a user.
        
        Generates a TOTP secret, creates a QR code for authenticator apps,
        and generates 10 backup codes.
        
        Args:
            user_id: The user's ID
            user_email: The user's email address (for QR code label)
            
        Returns:
            Dict containing:
                - secret: The TOTP secret (base32 encoded)
                - qr_code: Base64 encoded PNG image of QR code
                - backup_codes: List of 10 backup codes (plain text)
                
        Requirements: 7.1, 7.2
        """
        # Generate TOTP secret
        secret = pyotp.random_base32()
        
        # Create unconfirmed TOTP device
        encrypted_secret = encrypt(secret)
        
        await self.prisma.connect()
        try:
            # Check if user already has an unconfirmed device and delete it
            existing_device = await self.prisma.totpdevice.find_first(
                where={
                    'user_id': user_id,
                    'confirmed': False
                }
            )
            if existing_device:
                await self.prisma.totpdevice.delete(
                    where={'id': existing_device.id}
                )
            
            # Create new unconfirmed device
            await self.prisma.totpdevice.create(
                data={
                    'user_id': user_id,
                    'secret': encrypted_secret,
                    'name': 'Authenticator',
                    'confirmed': False
                }
            )
            
            # Generate QR code
            qr_code_data = self._generate_qr_code(secret, user_email)
            
            # Generate backup codes
            backup_codes = await self._generate_backup_codes(user_id)
            
            return {
                'secret': secret,
                'qr_code': qr_code_data,
                'backup_codes': backup_codes
            }
        finally:
            await self.prisma.disconnect()
    
    def _generate_qr_code(self, secret: str, user_email: str) -> str:
        """
        Generate a QR code for the TOTP secret.
        
        Args:
            secret: The TOTP secret (base32 encoded)
            user_email: The user's email address
            
        Returns:
            Base64 encoded PNG image of the QR code
        """
        # Create TOTP instance
        totp = pyotp.TOTP(secret)
        
        # Generate provisioning URI
        provisioning_uri = totp.provisioning_uri(
            name=user_email,
            issuer_name='MueJam Library'
        )
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        import base64
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return qr_code_base64
    
    async def _generate_backup_codes(self, user_id: str, count: int = 10) -> List[str]:
        """
        Generate backup codes for a user.
        
        Args:
            user_id: The user's ID
            count: Number of backup codes to generate (default: 10)
            
        Returns:
            List of backup codes (plain text)
            
        Requirements: 7.2
        """
        # Delete any existing unused backup codes for this user
        await self.prisma.backupcode.delete_many(
            where={
                'user_id': user_id,
                'used_at': None
            }
        )
        
        codes = []
        for _ in range(count):
            # Generate a random 8-character code
            code = self._generate_random_code(8)
            
            # Hash the code with bcrypt
            code_hash = bcrypt.hashpw(code.encode(), bcrypt.gensalt()).decode()
            
            # Store in database
            await self.prisma.backupcode.create(
                data={
                    'user_id': user_id,
                    'code_hash': code_hash
                }
            )
            
            codes.append(code)
        
        return codes
    
    def _generate_random_code(self, length: int = 8) -> str:
        """
        Generate a random alphanumeric code.
        
        Args:
            length: Length of the code (default: 8)
            
        Returns:
            Random alphanumeric code
        """
        # Use secrets for cryptographically strong random generation
        # Use uppercase letters and digits for easier manual entry
        alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'  # Exclude similar chars (I, O, 0, 1)
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    async def verify_2fa_setup(self, user_id: str, token: str) -> bool:
        """
        Verify 2FA setup by validating a TOTP token.
        
        This confirms the user has successfully configured their authenticator app.
        
        Args:
            user_id: The user's ID
            token: The TOTP token from the user's authenticator app
            
        Returns:
            True if token is valid and device is confirmed, False otherwise
            
        Requirements: 7.3
        """
        await self.prisma.connect()
        try:
            # Get unconfirmed device
            device = await self.prisma.totpdevice.find_first(
                where={
                    'user_id': user_id,
                    'confirmed': False
                }
            )
            
            if not device:
                return False
            
            # Decrypt secret
            secret = decrypt(device.secret)
            
            # Verify token
            totp = pyotp.TOTP(secret)
            if totp.verify(token, valid_window=1):
                # Confirm the device
                await self.prisma.totpdevice.update(
                    where={'id': device.id},
                    data={'confirmed': True}
                )
                return True
            
            return False
        finally:
            await self.prisma.disconnect()
    
    async def verify_totp(self, user_id: str, token: str) -> bool:
        """
        Verify a TOTP token for login.
        
        Args:
            user_id: The user's ID
            token: The TOTP token from the user's authenticator app
            
        Returns:
            True if token is valid, False otherwise
            
        Requirements: 7.5
        """
        await self.prisma.connect()
        try:
            # Get confirmed device
            device = await self.prisma.totpdevice.find_first(
                where={
                    'user_id': user_id,
                    'confirmed': True
                }
            )
            
            if not device:
                return False
            
            # Decrypt secret
            secret = decrypt(device.secret)
            
            # Verify token
            totp = pyotp.TOTP(secret)
            if totp.verify(token, valid_window=1):
                # Update last used timestamp
                await self.prisma.totpdevice.update(
                    where={'id': device.id},
                    data={'last_used_at': datetime.now(timezone.utc)}
                )
                return True
            
            return False
        finally:
            await self.prisma.disconnect()
    
    async def verify_backup_code(self, user_id: str, code: str) -> Tuple[bool, Optional[int]]:
        """
        Verify a backup code for login.
        
        Args:
            user_id: The user's ID
            code: The backup code to verify
            
        Returns:
            Tuple of (is_valid, remaining_codes):
                - is_valid: True if code is valid and unused, False otherwise
                - remaining_codes: Number of remaining unused backup codes (None if invalid)
                
        Requirements: 7.6
        """
        await self.prisma.connect()
        try:
            # Get all unused backup codes for this user
            backup_codes = await self.prisma.backupcode.find_many(
                where={
                    'user_id': user_id,
                    'used_at': None
                }
            )
            
            # Try to match the code
            for backup_code in backup_codes:
                if bcrypt.checkpw(code.encode(), backup_code.code_hash.encode()):
                    # Mark as used
                    await self.prisma.backupcode.update(
                        where={'id': backup_code.id},
                        data={'used_at': datetime.now(timezone.utc)}
                    )
                    
                    # Count remaining codes
                    remaining = await self.prisma.backupcode.count(
                        where={
                            'user_id': user_id,
                            'used_at': None
                        }
                    )
                    
                    return True, remaining
            
            return False, None
        finally:
            await self.prisma.disconnect()
    
    def has_2fa_enabled_sync(self, user_id: str) -> bool:
        """
        Synchronous version of has_2fa_enabled.
        
        This replaces the async version to avoid the nest_asyncio anti-pattern
        that was causing performance issues and potential deadlocks.
        
        Args:
            user_id: The user's ID
            
        Returns:
            True if user has a confirmed TOTP device, False otherwise
        """
        self.prisma.connect()
        try:
            device = self.prisma.totpdevice.find_first(
                where={
                    'user_id': user_id,
                    'confirmed': True
                }
            )
            return device is not None
        finally:
            self.prisma.disconnect()
    
    async def has_2fa_enabled(self, user_id: str) -> bool:
        """
        Check if a user has 2FA enabled.
        
        Args:
            user_id: The user's ID
            
        Returns:
            True if user has a confirmed TOTP device, False otherwise
        """
        await self.prisma.connect()
        try:
            device = await self.prisma.totpdevice.find_first(
                where={
                    'user_id': user_id,
                    'confirmed': True
                }
            )
            return device is not None
        finally:
            await self.prisma.disconnect()

    def has_2fa_enabled_sync(self, user_id: str) -> bool:
        """
        Synchronous version of has_2fa_enabled.

        This replaces the async version to avoid the nest_asyncio anti-pattern
        that was causing performance issues and potential deadlocks.

        Args:
            user_id: The user's ID

        Returns:
            True if user has a confirmed TOTP device, False otherwise
        """
        self.prisma.connect()
        try:
            device = self.prisma.totpdevice.find_first(
                where={
                    'user_id': user_id,
                    'confirmed': True
                }
            )
            return device is not None
        finally:
            self.prisma.disconnect()

    
    async def disable_2fa(self, user_id: str) -> bool:
        """
        Disable 2FA for a user.
        
        Deletes the TOTP device and all backup codes.
        
        Args:
            user_id: The user's ID
            
        Returns:
            True if 2FA was disabled, False if user didn't have 2FA enabled
        """
        await self.prisma.connect()
        try:
            # Delete TOTP device
            deleted_device = await self.prisma.totpdevice.delete_many(
                where={'user_id': user_id}
            )
            
            # Delete backup codes
            await self.prisma.backupcode.delete_many(
                where={'user_id': user_id}
            )
            
            return deleted_device > 0
        finally:
            await self.prisma.disconnect()
    
    async def regenerate_backup_codes(self, user_id: str) -> List[str]:
        """
        Regenerate backup codes for a user.
        
        Deletes all existing backup codes and generates new ones.
        
        Args:
            user_id: The user's ID
            
        Returns:
            List of new backup codes (plain text)
        """
        await self.prisma.connect()
        try:
            return await self._generate_backup_codes(user_id)
        finally:
            await self.prisma.disconnect()
    
    async def get_remaining_backup_codes_count(self, user_id: str) -> int:
        """
        Get the number of remaining unused backup codes for a user.
        
        Args:
            user_id: The user's ID
            
        Returns:
            Number of unused backup codes
        """
        await self.prisma.connect()
        try:
            count = await self.prisma.backupcode.count(
                where={
                    'user_id': user_id,
                    'used_at': None
                }
            )
            return count
        finally:
            await self.prisma.disconnect()
