"""
Unit tests for TokenService.

Tests token generation, validation, and lifecycle management.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock
from ..services.token_service import TokenService
from ..types import Token, TokenData
from ..constants import TOKEN_EXPIRATION_HOURS


class TestTokenServiceGeneration:
    """Tests for token generation functionality."""
    
    @pytest.fixture
    def mock_token_repository(self):
        """Create a mock token repository."""
        repo = AsyncMock()
        repo.create = AsyncMock()
        repo.invalidate_all_by_user_id = AsyncMock()
        return repo
    
    @pytest.fixture
    def token_service(self, mock_token_repository):
        """Create a TokenService instance with mocked repository."""
        return TokenService(mock_token_repository)
    
    @pytest.mark.asyncio
    async def test_generate_token_returns_token_data(self, token_service):
        """Test that generate_token returns TokenData with token and expiration."""
        user_id = "test-user-123"
        
        result = await token_service.generate_token(user_id)
        
        assert isinstance(result, TokenData)
        assert isinstance(result.token, str)
        assert len(result.token) > 0
        assert isinstance(result.expires_at, datetime)
    
    @pytest.mark.asyncio
    async def test_generate_token_has_sufficient_entropy(self, token_service):
        """Test that generated tokens have sufficient length (256 bits = 32 bytes)."""
        user_id = "test-user-123"
        
        result = await token_service.generate_token(user_id)
        
        # token_urlsafe(32) generates a URL-safe base64 string from 32 bytes
        # Base64 encoding increases size by ~33%, so 32 bytes -> ~43 characters
        assert len(result.token) >= 40  # Allow some variance
    
    @pytest.mark.asyncio
    async def test_generate_token_sets_correct_expiration(self, token_service):
        """Test that token expiration is set to 1 hour from creation."""
        user_id = "test-user-123"
        before_generation = datetime.utcnow()
        
        result = await token_service.generate_token(user_id)
        
        after_generation = datetime.utcnow()
        expected_expiration = before_generation + timedelta(hours=TOKEN_EXPIRATION_HOURS)
        
        # Allow 1 second tolerance for test execution time
        assert abs((result.expires_at - expected_expiration).total_seconds()) < 1
    
    @pytest.mark.asyncio
    async def test_generate_token_creates_unique_tokens(self, token_service):
        """Test that multiple token generations produce unique tokens."""
        user_id = "test-user-123"
        
        token1 = await token_service.generate_token(user_id)
        token2 = await token_service.generate_token(user_id)
        
        assert token1.token != token2.token
    
    @pytest.mark.asyncio
    async def test_generate_token_invalidates_previous_tokens(self, token_service, mock_token_repository):
        """Test that generating a new token invalidates all previous tokens for the user."""
        user_id = "test-user-123"
        
        await token_service.generate_token(user_id)
        
        mock_token_repository.invalidate_all_by_user_id.assert_called_once_with(user_id)
    
    @pytest.mark.asyncio
    async def test_generate_token_stores_hashed_token(self, token_service, mock_token_repository):
        """Test that the token is hashed before storage."""
        user_id = "test-user-123"
        
        result = await token_service.generate_token(user_id)
        
        # Verify create was called
        mock_token_repository.create.assert_called_once()
        
        # Get the Token object that was passed to create
        stored_token = mock_token_repository.create.call_args[0][0]
        
        # Verify the stored token_hash is different from the raw token
        assert stored_token.token_hash != result.token
        
        # Verify the hash is a hex string (SHA-256 produces 64 hex characters)
        assert len(stored_token.token_hash) == 64
        assert all(c in '0123456789abcdef' for c in stored_token.token_hash)
    
    @pytest.mark.asyncio
    async def test_generate_token_stores_correct_user_id(self, token_service, mock_token_repository):
        """Test that the correct user_id is stored with the token."""
        user_id = "test-user-456"
        
        await token_service.generate_token(user_id)
        
        stored_token = mock_token_repository.create.call_args[0][0]
        assert stored_token.user_id == user_id
    
    @pytest.mark.asyncio
    async def test_generate_token_sets_unused_state(self, token_service, mock_token_repository):
        """Test that newly generated tokens are marked as unused."""
        user_id = "test-user-123"
        
        await token_service.generate_token(user_id)
        
        stored_token = mock_token_repository.create.call_args[0][0]
        assert stored_token.used_at is None
        assert stored_token.invalidated is False


class TestTokenServiceHashing:
    """Tests for token hashing functionality."""
    
    @pytest.fixture
    def token_service(self):
        """Create a TokenService instance."""
        mock_repo = AsyncMock()
        return TokenService(mock_repo)
    
    def test_hash_token_produces_consistent_hash(self, token_service):
        """Test that hashing the same token produces the same hash."""
        token = "test-token-123"
        
        hash1 = token_service._hash_token(token)
        hash2 = token_service._hash_token(token)
        
        assert hash1 == hash2
    
    def test_hash_token_produces_different_hashes_for_different_tokens(self, token_service):
        """Test that different tokens produce different hashes."""
        token1 = "test-token-123"
        token2 = "test-token-456"
        
        hash1 = token_service._hash_token(token1)
        hash2 = token_service._hash_token(token2)
        
        assert hash1 != hash2
    
    def test_hash_token_produces_sha256_hash(self, token_service):
        """Test that the hash is a valid SHA-256 hash (64 hex characters)."""
        token = "test-token-123"
        
        hash_result = token_service._hash_token(token)
        
        assert len(hash_result) == 64
        assert all(c in '0123456789abcdef' for c in hash_result)


class TestTokenServiceValidation:
    """Tests for token validation functionality."""
    
    @pytest.fixture
    def mock_token_repository(self):
        """Create a mock token repository."""
        repo = AsyncMock()
        repo.find_by_token = AsyncMock()
        repo.update = AsyncMock()
        repo.invalidate_all_by_user_id = AsyncMock()
        return repo
    
    @pytest.fixture
    def token_service(self, mock_token_repository):
        """Create a TokenService instance with mocked repository."""
        return TokenService(mock_token_repository)
    
    @pytest.mark.asyncio
    async def test_validate_token_returns_valid_for_valid_token(self, token_service, mock_token_repository):
        """Test that a valid, unexpired, unused token is validated successfully."""
        token = "valid-token-123"
        user_id = "user-456"
        
        # Create a valid token record
        token_record = Token(
            id="token-id-1",
            user_id=user_id,
            token_hash=token_service._hash_token(token),
            expires_at=datetime.utcnow() + timedelta(hours=1),
            created_at=datetime.utcnow(),
            used_at=None,
            invalidated=False
        )
        mock_token_repository.find_by_token.return_value = token_record
        
        result = await token_service.validate_token(token)
        
        assert result.valid is True
        assert result.user_id == user_id
        assert result.reason is None
    
    @pytest.mark.asyncio
    async def test_validate_token_rejects_nonexistent_token(self, token_service, mock_token_repository):
        """Test that a token that doesn't exist in the database is rejected."""
        token = "nonexistent-token"
        mock_token_repository.find_by_token.return_value = None
        
        result = await token_service.validate_token(token)
        
        assert result.valid is False
        assert result.user_id is None
        assert "does not exist" in result.reason.lower() or "invalid" in result.reason.lower()
    
    @pytest.mark.asyncio
    async def test_validate_token_rejects_expired_token(self, token_service, mock_token_repository):
        """Test that an expired token is rejected (Requirement 2.3)."""
        token = "expired-token"
        
        # Create an expired token record
        token_record = Token(
            id="token-id-2",
            user_id="user-789",
            token_hash=token_service._hash_token(token),
            expires_at=datetime.utcnow() - timedelta(hours=1),  # Expired 1 hour ago
            created_at=datetime.utcnow() - timedelta(hours=2),
            used_at=None,
            invalidated=False
        )
        mock_token_repository.find_by_token.return_value = token_record
        
        result = await token_service.validate_token(token)
        
        assert result.valid is False
        assert result.user_id is None
        assert "expired" in result.reason.lower()
    
    @pytest.mark.asyncio
    async def test_validate_token_rejects_used_token(self, token_service, mock_token_repository):
        """Test that a previously used token is rejected (Requirement 2.4)."""
        token = "used-token"
        
        # Create a used token record
        token_record = Token(
            id="token-id-3",
            user_id="user-101",
            token_hash=token_service._hash_token(token),
            expires_at=datetime.utcnow() + timedelta(hours=1),
            created_at=datetime.utcnow(),
            used_at=datetime.utcnow() - timedelta(minutes=10),  # Used 10 minutes ago
            invalidated=False
        )
        mock_token_repository.find_by_token.return_value = token_record
        
        result = await token_service.validate_token(token)
        
        assert result.valid is False
        assert result.user_id is None
        assert "used" in result.reason.lower()
    
    @pytest.mark.asyncio
    async def test_validate_token_rejects_invalidated_token(self, token_service, mock_token_repository):
        """Test that a manually invalidated token is rejected (Requirement 2.5)."""
        token = "invalidated-token"
        
        # Create an invalidated token record
        token_record = Token(
            id="token-id-4",
            user_id="user-202",
            token_hash=token_service._hash_token(token),
            expires_at=datetime.utcnow() + timedelta(hours=1),
            created_at=datetime.utcnow(),
            used_at=None,
            invalidated=True  # Manually invalidated
        )
        mock_token_repository.find_by_token.return_value = token_record
        
        result = await token_service.validate_token(token)
        
        assert result.valid is False
        assert result.user_id is None
        assert "invalidated" in result.reason.lower()
    
    @pytest.mark.asyncio
    async def test_validate_token_hashes_token_before_lookup(self, token_service, mock_token_repository):
        """Test that the token is hashed before database lookup."""
        token = "test-token-hash"
        expected_hash = token_service._hash_token(token)
        
        mock_token_repository.find_by_token.return_value = None
        
        await token_service.validate_token(token)
        
        # Verify find_by_token was called with the hashed token
        mock_token_repository.find_by_token.assert_called_once_with(expected_hash)


class TestTokenServiceInvalidation:
    """Tests for token invalidation functionality."""
    
    @pytest.fixture
    def mock_token_repository(self):
        """Create a mock token repository."""
        repo = AsyncMock()
        repo.find_by_token = AsyncMock()
        repo.update = AsyncMock()
        repo.invalidate_all_by_user_id = AsyncMock()
        return repo
    
    @pytest.fixture
    def token_service(self, mock_token_repository):
        """Create a TokenService instance with mocked repository."""
        return TokenService(mock_token_repository)
    
    @pytest.mark.asyncio
    async def test_invalidate_token_marks_token_as_used(self, token_service, mock_token_repository):
        """Test that invalidating a token marks it as used."""
        token = "token-to-invalidate"
        
        # Create a valid token record
        token_record = Token(
            id="token-id-5",
            user_id="user-303",
            token_hash=token_service._hash_token(token),
            expires_at=datetime.utcnow() + timedelta(hours=1),
            created_at=datetime.utcnow(),
            used_at=None,
            invalidated=False
        )
        mock_token_repository.find_by_token.return_value = token_record
        
        await token_service.invalidate_token(token)
        
        # Verify the token was updated with used_at and invalidated set
        mock_token_repository.update.assert_called_once()
        updated_token = mock_token_repository.update.call_args[0][0]
        assert updated_token.used_at is not None
        assert updated_token.invalidated is True
    
    @pytest.mark.asyncio
    async def test_invalidate_token_handles_nonexistent_token(self, token_service, mock_token_repository):
        """Test that invalidating a nonexistent token doesn't raise an error."""
        token = "nonexistent-token"
        mock_token_repository.find_by_token.return_value = None
        
        # Should not raise an exception
        await token_service.invalidate_token(token)
        
        # Verify update was not called
        mock_token_repository.update.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_invalidate_all_user_tokens_calls_repository(self, token_service, mock_token_repository):
        """Test that invalidating all user tokens calls the repository method."""
        user_id = "user-404"
        
        await token_service.invalidate_all_user_tokens(user_id)
        
        mock_token_repository.invalidate_all_by_user_id.assert_called_once_with(user_id)
    
    @pytest.mark.asyncio
    async def test_invalidate_token_sets_used_at_timestamp(self, token_service, mock_token_repository):
        """Test that invalidating a token sets the used_at timestamp to current time."""
        token = "token-timestamp-test"
        
        token_record = Token(
            id="token-id-6",
            user_id="user-505",
            token_hash=token_service._hash_token(token),
            expires_at=datetime.utcnow() + timedelta(hours=1),
            created_at=datetime.utcnow(),
            used_at=None,
            invalidated=False
        )
        mock_token_repository.find_by_token.return_value = token_record
        
        before_invalidation = datetime.utcnow()
        await token_service.invalidate_token(token)
        after_invalidation = datetime.utcnow()
        
        updated_token = mock_token_repository.update.call_args[0][0]
        
        # Verify used_at is between before and after timestamps
        assert updated_token.used_at >= before_invalidation
        assert updated_token.used_at <= after_invalidation
