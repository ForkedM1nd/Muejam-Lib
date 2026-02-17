"""
Token Service Implementation

Handles token generation, validation, and lifecycle management.
"""
import secrets
import hashlib
from datetime import datetime, timedelta
from ..interfaces import ITokenService
from ..types import TokenData, TokenValidationResult, Token
from ..constants import TOKEN_EXPIRATION_HOURS, TOKEN_ENTROPY_BYTES
from ..repositories.token_repository import TokenRepository


class TokenService(ITokenService):
    """
    Service for managing password reset tokens.
    
    Implements cryptographically secure token generation with 256 bits of entropy,
    token validation with expiration checking, and token invalidation.
    """
    
    def __init__(self, token_repository: TokenRepository):
        """
        Initialize the TokenService.
        
        Args:
            token_repository: Repository for token persistence
        """
        self.token_repository = token_repository
    
    async def generate_token(self, user_id: str) -> TokenData:
        """
        Generate a cryptographically secure token.
        
        Uses secrets.token_urlsafe with 32 bytes (256 bits) of entropy
        as required by Requirement 2.1. The token is hashed using SHA-256
        before storage for security.
        
        Args:
            user_id: The user ID for whom the token is generated
            
        Returns:
            TokenData with token string and expiration timestamp
        """
        # Generate cryptographically secure random token with 256 bits of entropy
        # Requirement 2.1: Use cryptographically secure random number generator with at least 256 bits
        raw_token = secrets.token_urlsafe(TOKEN_ENTROPY_BYTES)
        
        # Calculate expiration time (1 hour from now)
        # Requirement 2.2: Set token expiration to 1 hour from generation time
        created_at = datetime.utcnow()
        expires_at = created_at + timedelta(hours=TOKEN_EXPIRATION_HOURS)
        
        # Hash the token using SHA-256 for secure storage
        token_hash = self._hash_token(raw_token)
        
        # Invalidate all previous tokens for this user
        # Requirement 2.5: Invalidate all previous tokens when a new token is generated
        await self.token_repository.invalidate_all_by_user_id(user_id)
        
        # Create token record in database
        token_record = Token(
            id=secrets.token_urlsafe(16),  # Generate unique ID for the token record
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            created_at=created_at,
            used_at=None,
            invalidated=False
        )
        
        await self.token_repository.create(token_record)
        
        # Return the raw token (not the hash) to be sent to the user
        return TokenData(token=raw_token, expires_at=expires_at)
    
    def _hash_token(self, token: str) -> str:
        """
        Hash a token using SHA-256.
        
        Args:
            token: The raw token string
            
        Returns:
            Hexadecimal string representation of the hash
        """
        return hashlib.sha256(token.encode('utf-8')).hexdigest()
    
    async def validate_token(self, token: str) -> TokenValidationResult:
        """
        Validate token and check expiration.
        
        Checks token existence, expiration status, and usage status.
        
        Args:
            token: The raw token string to validate
            
        Returns:
            TokenValidationResult with validation status and user_id if valid
        """
        # Hash the token to look it up in the database
        token_hash = self._hash_token(token)
        
        # Find the token in the database
        token_record = await self.token_repository.find_by_token(token_hash)
        
        # Check if token exists
        if token_record is None:
            # Requirement 4.3: Invalid token should display error message
            return TokenValidationResult(
                valid=False,
                user_id=None,
                reason="Token does not exist or is invalid"
            )
        
        # Check if token has been manually invalidated
        if token_record.invalidated:
            # Requirement 2.5: Invalidated tokens should be rejected
            return TokenValidationResult(
                valid=False,
                user_id=None,
                reason="Token has been invalidated"
            )
        
        # Check if token has already been used
        # Requirement 2.4: Used tokens should be rejected
        # Requirement 4.4: Previously used token should display specific error
        if token_record.used_at is not None:
            return TokenValidationResult(
                valid=False,
                user_id=None,
                reason="Token has already been used"
            )
        
        # Check if token has expired
        # Requirement 2.3: Expired tokens should be rejected
        # Requirement 4.2: Expired token should display error message
        current_time = datetime.utcnow()
        if current_time > token_record.expires_at:
            return TokenValidationResult(
                valid=False,
                user_id=None,
                reason="Token has expired"
            )
        
        # Token is valid
        # Requirement 4.1: Valid token should allow form display
        return TokenValidationResult(
            valid=True,
            user_id=token_record.user_id,
            reason=None
        )
    
    async def invalidate_token(self, token: str) -> None:
        """
        Invalidate a specific token.
        
        Marks the token as used and invalidated to prevent reuse.
        
        Args:
            token: The raw token string to invalidate
        """
        # Hash the token to look it up in the database
        token_hash = self._hash_token(token)
        
        # Find the token in the database
        token_record = await self.token_repository.find_by_token(token_hash)
        
        if token_record is not None:
            # Mark token as used and invalidated
            # Requirement 2.4: Token should be invalidated immediately after use
            token_record.used_at = datetime.utcnow()
            token_record.invalidated = True
            
            # Update the token in the database
            await self.token_repository.update(token_record)
    
    async def invalidate_all_user_tokens(self, user_id: str) -> None:
        """
        Invalidate all tokens for a user.
        
        Used when generating a new token or when a password is reset.
        
        Args:
            user_id: The user ID whose tokens should be invalidated
        """
        # Requirement 2.5: Invalidate all previous tokens when new token is generated
        await self.token_repository.invalidate_all_by_user_id(user_id)
