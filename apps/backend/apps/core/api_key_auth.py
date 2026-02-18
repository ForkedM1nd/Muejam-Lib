"""
API Key Authentication Module

This module provides API key authentication for external integrations.
It supports key generation, rotation, and secure validation.

Requirements: 6.10
"""

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from django.utils import timezone
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from prisma import Prisma
from prisma.models import APIKey


class APIKeyService:
    """Service for managing API keys"""
    
    @staticmethod
    def generate_api_key() -> str:
        """
        Generate a secure random API key.
        
        Returns:
            str: A 64-character hexadecimal API key
        """
        return secrets.token_hex(32)
    
    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """
        Hash an API key using SHA-256.
        
        Args:
            api_key: The plain text API key
            
        Returns:
            str: The hashed API key
        """
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    @staticmethod
    async def create_api_key(
        user_id: str,
        name: str,
        expires_in_days: int = 365,
        permissions: Optional[Dict[str, Any]] = None
    ) -> tuple[APIKey, str]:
        """
        Create a new API key for a user.
        
        Args:
            user_id: The user ID to associate with the API key
            name: A descriptive name for the API key
            expires_in_days: Number of days until the key expires (default: 365)
            permissions: Optional scoped permissions for the key
            
        Returns:
            tuple: (APIKey model instance, plain text API key)
            
        Note:
            The plain text API key is only returned once during creation.
            It should be securely stored by the client.
        """
        import json
        
        db = Prisma()
        await db.connect()
        
        try:
            # Generate API key
            plain_key = APIKeyService.generate_api_key()
            key_hash = APIKeyService.hash_api_key(plain_key)
            
            # Calculate expiration date
            expires_at = timezone.now() + timedelta(days=expires_in_days)
            
            # Convert permissions to JSON string for Prisma
            permissions_json = json.dumps(permissions or {})
            
            # Create API key record
            api_key = await db.apikey.create(
                data={
                    'key_hash': key_hash,
                    'name': name,
                    'user_id': user_id,
                    'expires_at': expires_at,
                    'is_active': True,
                    'permissions': permissions_json
                }
            )
            
            return api_key, plain_key
        finally:
            await db.disconnect()
    
    @staticmethod
    async def rotate_api_key(api_key_id: str) -> tuple[APIKey, str]:
        """
        Rotate an existing API key by generating a new key.
        
        Args:
            api_key_id: The ID of the API key to rotate
            
        Returns:
            tuple: (Updated APIKey model instance, new plain text API key)
            
        Raises:
            ValueError: If the API key doesn't exist
        """
        db = Prisma()
        await db.connect()
        
        try:
            # Get existing API key
            existing_key = await db.apikey.find_unique(where={'id': api_key_id})
            if not existing_key:
                raise ValueError(f"API key with ID {api_key_id} not found")
            
            # Generate new API key
            plain_key = APIKeyService.generate_api_key()
            key_hash = APIKeyService.hash_api_key(plain_key)
            
            # Update API key record
            updated_key = await db.apikey.update(
                where={'id': api_key_id},
                data={
                    'key_hash': key_hash,
                    'last_used_at': None,  # Reset last used timestamp
                }
            )
            
            return updated_key, plain_key
        finally:
            await db.disconnect()
    
    @staticmethod
    async def revoke_api_key(api_key_id: str) -> APIKey:
        """
        Revoke an API key by marking it as inactive.
        
        Args:
            api_key_id: The ID of the API key to revoke
            
        Returns:
            APIKey: The updated API key model instance
            
        Raises:
            ValueError: If the API key doesn't exist
        """
        db = Prisma()
        await db.connect()
        
        try:
            api_key = await db.apikey.update(
                where={'id': api_key_id},
                data={'is_active': False}
            )
            
            if not api_key:
                raise ValueError(f"API key with ID {api_key_id} not found")
            
            return api_key
        finally:
            await db.disconnect()
    
    @staticmethod
    async def validate_api_key(plain_key: str) -> Optional[APIKey]:
        """
        Validate an API key and return the associated key record.
        
        Args:
            plain_key: The plain text API key to validate
            
        Returns:
            Optional[APIKey]: The API key record if valid, None otherwise
        """
        db = Prisma()
        await db.connect()
        
        try:
            key_hash = APIKeyService.hash_api_key(plain_key)
            
            # Find active, non-expired API key
            api_key = await db.apikey.find_first(
                where={
                    'key_hash': key_hash,
                    'is_active': True,
                    'expires_at': {'gt': timezone.now()}
                }
            )
            
            if api_key:
                # Update last used timestamp and return updated record
                api_key = await db.apikey.update(
                    where={'id': api_key.id},
                    data={'last_used_at': timezone.now()}
                )
            
            return api_key
        finally:
            await db.disconnect()
    
    @staticmethod
    async def list_user_api_keys(user_id: str, include_inactive: bool = False) -> list[APIKey]:
        """
        List all API keys for a user.
        
        Args:
            user_id: The user ID
            include_inactive: Whether to include inactive keys (default: False)
            
        Returns:
            list[APIKey]: List of API key records
        """
        db = Prisma()
        await db.connect()
        
        try:
            where_clause = {'user_id': user_id}
            if not include_inactive:
                where_clause['is_active'] = True
            
            api_keys = await db.apikey.find_many(
                where=where_clause,
                order={'created_at': 'desc'}
            )
            
            return api_keys
        finally:
            await db.disconnect()


class APIKeyAuthentication(BaseAuthentication):
    """
    Django REST Framework authentication class for API key authentication.
    
    This authentication class checks for an API key in the X-API-Key header
    and validates it against the database.
    
    Usage:
        Add to REST_FRAMEWORK settings:
        
        REST_FRAMEWORK = {
            'DEFAULT_AUTHENTICATION_CLASSES': [
                'apps.core.api_key_auth.APIKeyAuthentication',
                # ... other authentication classes
            ]
        }
    """
    
    keyword = 'X-API-Key'
    
    def authenticate(self, request):
        """
        Authenticate the request using API key.
        
        Args:
            request: The Django request object
            
        Returns:
            tuple: (user, auth) if authentication succeeds, None otherwise
            
        Raises:
            AuthenticationFailed: If the API key is invalid or expired
        """
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            # No API key provided, let other authentication methods handle it
            return None
        
        # Validate API key (synchronous wrapper for async function)
        import asyncio
        try:
            api_key_obj = asyncio.run(APIKeyService.validate_api_key(api_key))
        except Exception as e:
            raise AuthenticationFailed(f'API key validation failed: {str(e)}')
        
        if not api_key_obj:
            raise AuthenticationFailed('Invalid or expired API key')
        
        # Return a tuple of (user_id, api_key_obj)
        # Note: In a real implementation, you'd fetch the actual user object
        # For now, we'll use a simple dict to represent the user
        user = {
            'id': api_key_obj.user_id,
            'is_authenticated': True,
            'api_key_permissions': api_key_obj.permissions
        }
        
        return (user, api_key_obj)
    
    def authenticate_header(self, request):
        """
        Return the authentication header to use in 401 responses.
        
        Args:
            request: The Django request object
            
        Returns:
            str: The authentication header value
        """
        return self.keyword
