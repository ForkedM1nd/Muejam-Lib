"""
Tests for API Key Authentication

Requirements: 6.10
"""

import pytest
from datetime import datetime, timedelta
from django.utils import timezone
from apps.core.api_key_auth import APIKeyService


class TestAPIKeyService:
    """Test suite for APIKeyService"""
    
    @pytest.mark.asyncio
    async def test_generate_api_key(self):
        """Test API key generation"""
        key = APIKeyService.generate_api_key()
        
        # Should be 64 characters (32 bytes in hex)
        assert len(key) == 64
        # Should be hexadecimal
        assert all(c in '0123456789abcdef' for c in key)
    
    @pytest.mark.asyncio
    async def test_hash_api_key(self):
        """Test API key hashing"""
        key = "test-api-key-12345"
        hash1 = APIKeyService.hash_api_key(key)
        hash2 = APIKeyService.hash_api_key(key)
        
        # Same key should produce same hash
        assert hash1 == hash2
        # Hash should be 64 characters (SHA-256 in hex)
        assert len(hash1) == 64
        # Different keys should produce different hashes
        different_hash = APIKeyService.hash_api_key("different-key")
        assert hash1 != different_hash
    
    @pytest.mark.asyncio
    async def test_create_api_key(self):
        """Test creating an API key"""
        user_id = "test-user-123"
        name = "Test API Key"
        
        api_key_obj, plain_key = await APIKeyService.create_api_key(
            user_id=user_id,
            name=name,
            expires_in_days=30
        )
        
        # Verify API key object
        assert api_key_obj.name == name
        assert api_key_obj.user_id == user_id
        assert api_key_obj.is_active is True
        assert len(plain_key) == 64
        
        # Verify expiration is approximately 30 days from now
        expected_expiry = timezone.now() + timedelta(days=30)
        time_diff = abs((api_key_obj.expires_at - expected_expiry).total_seconds())
        assert time_diff < 60  # Within 1 minute
        
        # Clean up
        await APIKeyService.revoke_api_key(api_key_obj.id)
    
    @pytest.mark.asyncio
    async def test_validate_api_key(self):
        """Test validating an API key"""
        user_id = "test-user-456"
        
        # Create API key
        api_key_obj, plain_key = await APIKeyService.create_api_key(
            user_id=user_id,
            name="Validation Test Key"
        )
        
        # Validate with correct key
        validated = await APIKeyService.validate_api_key(plain_key)
        assert validated is not None
        assert validated.id == api_key_obj.id
        assert validated.last_used_at is not None
        
        # Validate with incorrect key
        invalid = await APIKeyService.validate_api_key("invalid-key-12345")
        assert invalid is None
        
        # Clean up
        await APIKeyService.revoke_api_key(api_key_obj.id)
    
    @pytest.mark.asyncio
    async def test_revoke_api_key(self):
        """Test revoking an API key"""
        user_id = "test-user-789"
        
        # Create API key
        api_key_obj, plain_key = await APIKeyService.create_api_key(
            user_id=user_id,
            name="Revoke Test Key"
        )
        
        # Verify it works
        validated = await APIKeyService.validate_api_key(plain_key)
        assert validated is not None
        
        # Revoke the key
        revoked = await APIKeyService.revoke_api_key(api_key_obj.id)
        assert revoked.is_active is False
        
        # Verify it no longer works
        validated_after_revoke = await APIKeyService.validate_api_key(plain_key)
        assert validated_after_revoke is None
    
    @pytest.mark.asyncio
    async def test_rotate_api_key(self):
        """Test rotating an API key"""
        user_id = "test-user-rotate"
        
        # Create API key
        original_key_obj, original_plain_key = await APIKeyService.create_api_key(
            user_id=user_id,
            name="Rotate Test Key"
        )
        
        # Rotate the key
        rotated_key_obj, new_plain_key = await APIKeyService.rotate_api_key(
            original_key_obj.id
        )
        
        # Verify the key ID is the same
        assert rotated_key_obj.id == original_key_obj.id
        # Verify the plain key is different
        assert new_plain_key != original_plain_key
        
        # Verify old key no longer works
        old_validated = await APIKeyService.validate_api_key(original_plain_key)
        assert old_validated is None
        
        # Verify new key works
        new_validated = await APIKeyService.validate_api_key(new_plain_key)
        assert new_validated is not None
        assert new_validated.id == original_key_obj.id
        
        # Clean up
        await APIKeyService.revoke_api_key(rotated_key_obj.id)
    
    @pytest.mark.asyncio
    async def test_list_user_api_keys(self):
        """Test listing user API keys"""
        user_id = "test-user-list"
        
        # Create multiple API keys
        key1_obj, _ = await APIKeyService.create_api_key(
            user_id=user_id,
            name="Key 1"
        )
        key2_obj, _ = await APIKeyService.create_api_key(
            user_id=user_id,
            name="Key 2"
        )
        
        # List active keys
        active_keys = await APIKeyService.list_user_api_keys(user_id)
        assert len(active_keys) >= 2
        assert any(k.id == key1_obj.id for k in active_keys)
        assert any(k.id == key2_obj.id for k in active_keys)
        
        # Revoke one key
        await APIKeyService.revoke_api_key(key1_obj.id)
        
        # List active keys (should not include revoked)
        active_keys_after = await APIKeyService.list_user_api_keys(user_id)
        assert not any(k.id == key1_obj.id for k in active_keys_after)
        assert any(k.id == key2_obj.id for k in active_keys_after)
        
        # List all keys including inactive
        all_keys = await APIKeyService.list_user_api_keys(
            user_id,
            include_inactive=True
        )
        assert any(k.id == key1_obj.id for k in all_keys)
        assert any(k.id == key2_obj.id for k in all_keys)
        
        # Clean up
        await APIKeyService.revoke_api_key(key2_obj.id)
    
    @pytest.mark.asyncio
    async def test_api_key_with_permissions(self):
        """Test creating API key with scoped permissions"""
        user_id = "test-user-perms"
        permissions = {
            "read": True,
            "write": False,
            "resources": ["stories", "whispers"]
        }
        
        api_key_obj, plain_key = await APIKeyService.create_api_key(
            user_id=user_id,
            name="Permissions Test Key",
            permissions=permissions
        )
        
        # Verify permissions are stored
        assert api_key_obj.permissions == permissions
        
        # Verify permissions are returned on validation
        validated = await APIKeyService.validate_api_key(plain_key)
        assert validated.permissions == permissions
        
        # Clean up
        await APIKeyService.revoke_api_key(api_key_obj.id)
    
    @pytest.mark.asyncio
    async def test_expired_api_key(self):
        """Test that expired API keys are rejected"""
        user_id = "test-user-expired"
        
        # Create API key that expires in 0 days (immediately)
        api_key_obj, plain_key = await APIKeyService.create_api_key(
            user_id=user_id,
            name="Expired Test Key",
            expires_in_days=0
        )
        
        # Validation should fail for expired key
        validated = await APIKeyService.validate_api_key(plain_key)
        assert validated is None
        
        # Clean up
        await APIKeyService.revoke_api_key(api_key_obj.id)


class TestAPIKeyGeneration:
    """Test API key generation properties"""
    
    def test_api_key_uniqueness(self):
        """Test that generated API keys are unique"""
        keys = set()
        for _ in range(100):
            key = APIKeyService.generate_api_key()
            assert key not in keys, "Generated duplicate API key"
            keys.add(key)
    
    def test_api_key_format(self):
        """Test that API keys have correct format"""
        for _ in range(10):
            key = APIKeyService.generate_api_key()
            # Should be 64 characters
            assert len(key) == 64
            # Should be lowercase hexadecimal
            assert key.islower()
            assert all(c in '0123456789abcdef' for c in key)
