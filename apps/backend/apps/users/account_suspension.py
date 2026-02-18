"""
Account Suspension Service for managing user account suspensions.

This service handles:
- Creating account suspensions with configurable duration
- Checking suspension status
- Enforcing suspension in authentication
- Automatic expiration of temporary suspensions

Requirements: 5.13, 5.14
"""
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from prisma import Prisma

logger = logging.getLogger(__name__)


class AccountSuspensionService:
    """
    Service for managing account suspensions.
    
    Implements:
    - Suspension creation with temporary or permanent duration
    - Suspension status checking
    - Automatic expiration handling
    """
    
    async def suspend_account(
        self,
        user_id: str,
        suspended_by: str,
        reason: str,
        expires_at: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Suspend a user account.
        
        Args:
            user_id: ID of user to suspend
            suspended_by: ID of administrator performing suspension
            reason: Reason for suspension
            expires_at: Optional expiration datetime (None = permanent)
            
        Returns:
            Dictionary with suspension details
            
        Requirements: 5.13
        """
        db = Prisma()
        await db.connect()
        
        try:
            # Deactivate any existing active suspensions
            await db.accountsuspension.update_many(
                where={
                    'user_id': user_id,
                    'is_active': True
                },
                data={'is_active': False}
            )
            
            # Create new suspension
            suspension = await db.accountsuspension.create(
                data={
                    'user_id': user_id,
                    'suspended_by': suspended_by,
                    'reason': reason,
                    'expires_at': expires_at,
                    'is_active': True
                }
            )
            
            logger.info(
                f"Account suspended: user_id={user_id}, "
                f"suspended_by={suspended_by}, "
                f"expires_at={expires_at}, "
                f"reason={reason[:50]}"
            )
            
            return {
                'id': suspension.id,
                'user_id': suspension.user_id,
                'suspended_by': suspension.suspended_by,
                'reason': suspension.reason,
                'suspended_at': suspension.suspended_at,
                'expires_at': suspension.expires_at,
                'is_permanent': suspension.expires_at is None
            }
            
        finally:
            await db.disconnect()
    
    async def check_suspension(
        self,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Check if a user account is currently suspended.
        
        Automatically handles expiration of temporary suspensions.
        
        Args:
            user_id: ID of user to check
            
        Returns:
            Suspension details if suspended, None if not suspended
            
        Requirements: 5.14
        """
        db = Prisma()
        await db.connect()
        
        try:
            # Get active suspension
            suspension = await db.accountsuspension.find_first(
                where={
                    'user_id': user_id,
                    'is_active': True
                },
                order_by={'suspended_at': 'desc'}
            )
            
            if not suspension:
                return None
            
            # Check if temporary suspension has expired
            if suspension.expires_at:
                now = datetime.now(timezone.utc)
                if now >= suspension.expires_at:
                    # Suspension has expired, deactivate it
                    await db.accountsuspension.update(
                        where={'id': suspension.id},
                        data={'is_active': False}
                    )
                    
                    logger.info(
                        f"Suspension expired for user {user_id}, "
                        f"suspension_id={suspension.id}"
                    )
                    
                    return None
            
            # Suspension is active
            return {
                'id': suspension.id,
                'user_id': suspension.user_id,
                'suspended_by': suspension.suspended_by,
                'reason': suspension.reason,
                'suspended_at': suspension.suspended_at,
                'expires_at': suspension.expires_at,
                'is_permanent': suspension.expires_at is None
            }
            
        finally:
            await db.disconnect()
    
    async def lift_suspension(
        self,
        user_id: str,
        lifted_by: str
    ) -> bool:
        """
        Manually lift an active suspension.
        
        Args:
            user_id: ID of user to unsuspend
            lifted_by: ID of administrator lifting suspension
            
        Returns:
            True if suspension was lifted, False if no active suspension
        """
        db = Prisma()
        await db.connect()
        
        try:
            # Deactivate active suspensions
            result = await db.accountsuspension.update_many(
                where={
                    'user_id': user_id,
                    'is_active': True
                },
                data={'is_active': False}
            )
            
            if result > 0:
                logger.info(
                    f"Suspension lifted for user {user_id} by {lifted_by}"
                )
                return True
            
            return False
            
        finally:
            await db.disconnect()
    
    async def get_suspension_history(
        self,
        user_id: str
    ) -> list[Dict[str, Any]]:
        """
        Get suspension history for a user.
        
        Args:
            user_id: ID of user
            
        Returns:
            List of suspension records
        """
        db = Prisma()
        await db.connect()
        
        try:
            suspensions = await db.accountsuspension.find_many(
                where={'user_id': user_id},
                order_by={'suspended_at': 'desc'}
            )
            
            return [
                {
                    'id': s.id,
                    'suspended_by': s.suspended_by,
                    'reason': s.reason,
                    'suspended_at': s.suspended_at,
                    'expires_at': s.expires_at,
                    'is_active': s.is_active,
                    'is_permanent': s.expires_at is None
                }
                for s in suspensions
            ]
            
        finally:
            await db.disconnect()
