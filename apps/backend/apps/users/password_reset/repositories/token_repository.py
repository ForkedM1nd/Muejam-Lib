"""
Token Repository Implementation

Data access layer for password reset tokens.
"""
from typing import Optional
from datetime import datetime
from prisma import Prisma
from ..types import Token


class TokenRepository:
    """
    Repository for managing password reset token persistence.
    
    Provides methods to create, find, update, and delete tokens
    in the database using Prisma ORM.
    """
    
    def __init__(self, db: Optional[Prisma] = None):
        """
        Initialize the repository.
        
        Args:
            db: Optional Prisma client instance. If not provided, a new one will be created.
        """
        self.db = db or Prisma()
    
    async def create(self, token: Token) -> Token:
        """
        Create a new token in the database.
        
        Args:
            token: Token object to create
            
        Returns:
            Created Token object
        """
        if not self.db.is_connected():
            await self.db.connect()
        
        db_token = await self.db.passwordresettoken.create(
            data={
                'id': token.id,
                'user_id': token.user_id,
                'token_hash': token.token_hash,
                'expires_at': token.expires_at,
                'created_at': token.created_at,
                'used_at': token.used_at,
                'invalidated': token.invalidated,
            }
        )
        
        return Token(
            id=db_token.id,
            user_id=db_token.user_id,
            token_hash=db_token.token_hash,
            expires_at=db_token.expires_at,
            created_at=db_token.created_at,
            used_at=db_token.used_at,
            invalidated=db_token.invalidated,
        )
    
    async def find_by_token(self, token_hash: str) -> Optional[Token]:
        """
        Find a token by its hash value.
        
        Args:
            token_hash: The SHA-256 hash of the token
            
        Returns:
            Token object if found, None otherwise
        """
        if not self.db.is_connected():
            await self.db.connect()
        
        db_token = await self.db.passwordresettoken.find_unique(
            where={'token_hash': token_hash}
        )
        
        if not db_token:
            return None
        
        return Token(
            id=db_token.id,
            user_id=db_token.user_id,
            token_hash=db_token.token_hash,
            expires_at=db_token.expires_at,
            created_at=db_token.created_at,
            used_at=db_token.used_at,
            invalidated=db_token.invalidated,
        )
    
    async def find_latest_by_user_id(self, user_id: str) -> Optional[Token]:
        """
        Find the most recent token for a user.
        
        Args:
            user_id: The user ID
            
        Returns:
            Most recent Token object if found, None otherwise
        """
        if not self.db.is_connected():
            await self.db.connect()
        
        db_token = await self.db.passwordresettoken.find_first(
            where={'user_id': user_id},
            order={'created_at': 'desc'}
        )
        
        if not db_token:
            return None
        
        return Token(
            id=db_token.id,
            user_id=db_token.user_id,
            token_hash=db_token.token_hash,
            expires_at=db_token.expires_at,
            created_at=db_token.created_at,
            used_at=db_token.used_at,
            invalidated=db_token.invalidated,
        )
    
    async def update(self, token: Token) -> Token:
        """
        Update an existing token.
        
        Args:
            token: Token object with updated values
            
        Returns:
            Updated Token object
        """
        if not self.db.is_connected():
            await self.db.connect()
        
        db_token = await self.db.passwordresettoken.update(
            where={'id': token.id},
            data={
                'used_at': token.used_at,
                'invalidated': token.invalidated,
            }
        )
        
        return Token(
            id=db_token.id,
            user_id=db_token.user_id,
            token_hash=db_token.token_hash,
            expires_at=db_token.expires_at,
            created_at=db_token.created_at,
            used_at=db_token.used_at,
            invalidated=db_token.invalidated,
        )
    
    async def invalidate_all_by_user_id(self, user_id: str) -> None:
        """
        Invalidate all tokens for a user.
        
        Args:
            user_id: The user ID
        """
        if not self.db.is_connected():
            await self.db.connect()
        
        await self.db.passwordresettoken.update_many(
            where={
                'user_id': user_id,
                'invalidated': False,
            },
            data={'invalidated': True}
        )
    
    async def delete(self, token_id: str) -> None:
        """
        Delete a token.
        
        Args:
            token_id: The token ID to delete
        """
        if not self.db.is_connected():
            await self.db.connect()
        
        await self.db.passwordresettoken.delete(
            where={'id': token_id}
        )

