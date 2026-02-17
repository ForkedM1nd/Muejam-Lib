"""
User Repository Implementation

Data access layer for user password management.
Implements methods to find users and update passwords with secure hashing.
"""
from typing import Optional, List
import bcrypt
from prisma import Prisma
from prisma.models import User


class UserRepository:
    """
    Repository for managing user password data.
    
    Provides methods to find users and update passwords with
    secure hashing and previous password tracking.
    """
    
    def __init__(self, db: Optional[Prisma] = None):
        """
        Initialize the repository.
        
        Args:
            db: Optional Prisma client instance. If not provided, creates a new one.
        """
        self.db = db or Prisma()
    
    async def find_by_email(self, email: str) -> Optional[dict]:
        """
        Find a user by email address.
        
        Args:
            email: The user's email address
            
        Returns:
            User data as dict if found, None otherwise
        """
        if not self.db.is_connected():
            await self.db.connect()
        
        user = await self.db.user.find_unique(
            where={'email': email}
        )
        
        if user:
            return {
                'id': user.id,
                'email': user.email,
                'password_hash': user.password_hash,
                'previous_password_hashes': user.previous_password_hashes or [],
                'created_at': user.created_at,
                'updated_at': user.updated_at,
            }
        return None
    
    async def find_by_id(self, user_id: str) -> Optional[dict]:
        """
        Find a user by ID.
        
        Args:
            user_id: The user's unique identifier
            
        Returns:
            User data as dict if found, None otherwise
        """
        if not self.db.is_connected():
            await self.db.connect()
        
        user = await self.db.user.find_unique(
            where={'id': user_id}
        )
        
        if user:
            return {
                'id': user.id,
                'email': user.email,
                'password_hash': user.password_hash,
                'previous_password_hashes': user.previous_password_hashes or [],
                'created_at': user.created_at,
                'updated_at': user.updated_at,
            }
        return None
    
    async def update_password(
        self,
        user_id: str,
        password_hash: str,
        previous_hash: str
    ) -> None:
        """
        Update user password and store previous hash.
        
        This method:
        1. Updates the current password hash
        2. Adds the previous password hash to the history
        3. Maintains a list of previous hashes for comparison (Requirement 6.3)
        
        Args:
            user_id: The user's unique identifier
            password_hash: The new password hash (Requirement 6.5)
            previous_hash: The current password hash to store in history
        """
        if not self.db.is_connected():
            await self.db.connect()
        
        # Get current user to access previous hashes
        user = await self.db.user.find_unique(
            where={'id': user_id}
        )
        
        if not user:
            raise ValueError(f"User with id {user_id} not found")
        
        # Build updated list of previous hashes
        previous_hashes = user.previous_password_hashes or []
        updated_previous_hashes = [previous_hash] + previous_hashes
        
        # Limit to last 5 password hashes to prevent unbounded growth
        updated_previous_hashes = updated_previous_hashes[:5]
        
        # Update the user's password and previous hashes
        await self.db.user.update(
            where={'id': user_id},
            data={
                'password_hash': password_hash,
                'previous_password_hashes': updated_previous_hashes,
            }
        )
    
    async def get_previous_password_hashes(self, user_id: str) -> List[str]:
        """
        Get list of previous password hashes for a user.
        
        Used for validating that new passwords don't match previous passwords
        (Requirement 6.3).
        
        Args:
            user_id: The user's unique identifier
            
        Returns:
            List of previous password hashes
        """
        if not self.db.is_connected():
            await self.db.connect()
        
        user = await self.db.user.find_unique(
            where={'id': user_id}
        )
        
        if not user:
            return []
        
        # Return both current and previous hashes for comparison
        hashes = [user.password_hash]
        if user.previous_password_hashes:
            hashes.extend(user.previous_password_hashes)
        
        return hashes

