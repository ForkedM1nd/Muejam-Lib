"""
Unit tests for UserRepository.

Tests the data access layer for user password management.
"""
import pytest
import bcrypt
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from ..repositories.user_repository import UserRepository


@pytest.fixture
def mock_prisma():
    """Create a mock Prisma client."""
    mock_db = MagicMock()
    mock_db.is_connected = MagicMock(return_value=True)
    mock_db.connect = AsyncMock()
    mock_db.user = MagicMock()
    return mock_db


@pytest.fixture
def user_repository(mock_prisma):
    """Create a UserRepository with mocked database."""
    return UserRepository(db=mock_prisma)


@pytest.fixture
def sample_user():
    """Sample user data for testing."""
    password = "TestPassword123!"
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    return {
        'id': 'user-123',
        'email': 'test@example.com',
        'password_hash': password_hash,
        'previous_password_hashes': [],
        'created_at': datetime.now(),
        'updated_at': datetime.now(),
    }


class TestFindByEmail:
    """Tests for find_by_email method."""
    
    @pytest.mark.asyncio
    async def test_find_existing_user(self, user_repository, mock_prisma, sample_user):
        """Test finding a user that exists."""
        # Create mock user object
        mock_user = MagicMock()
        mock_user.id = sample_user['id']
        mock_user.email = sample_user['email']
        mock_user.password_hash = sample_user['password_hash']
        mock_user.previous_password_hashes = sample_user['previous_password_hashes']
        mock_user.created_at = sample_user['created_at']
        mock_user.updated_at = sample_user['updated_at']
        
        mock_prisma.user.find_unique = AsyncMock(return_value=mock_user)
        
        result = await user_repository.find_by_email('test@example.com')
        
        assert result is not None
        assert result['id'] == sample_user['id']
        assert result['email'] == sample_user['email']
        assert result['password_hash'] == sample_user['password_hash']
        mock_prisma.user.find_unique.assert_called_once_with(
            where={'email': 'test@example.com'}
        )
    
    @pytest.mark.asyncio
    async def test_find_nonexistent_user(self, user_repository, mock_prisma):
        """Test finding a user that doesn't exist."""
        mock_prisma.user.find_unique = AsyncMock(return_value=None)
        
        result = await user_repository.find_by_email('nonexistent@example.com')
        
        assert result is None
        mock_prisma.user.find_unique.assert_called_once_with(
            where={'email': 'nonexistent@example.com'}
        )


class TestFindById:
    """Tests for find_by_id method."""
    
    @pytest.mark.asyncio
    async def test_find_existing_user(self, user_repository, mock_prisma, sample_user):
        """Test finding a user by ID that exists."""
        mock_user = MagicMock()
        mock_user.id = sample_user['id']
        mock_user.email = sample_user['email']
        mock_user.password_hash = sample_user['password_hash']
        mock_user.previous_password_hashes = sample_user['previous_password_hashes']
        mock_user.created_at = sample_user['created_at']
        mock_user.updated_at = sample_user['updated_at']
        
        mock_prisma.user.find_unique = AsyncMock(return_value=mock_user)
        
        result = await user_repository.find_by_id('user-123')
        
        assert result is not None
        assert result['id'] == sample_user['id']
        assert result['email'] == sample_user['email']
        mock_prisma.user.find_unique.assert_called_once_with(
            where={'id': 'user-123'}
        )
    
    @pytest.mark.asyncio
    async def test_find_nonexistent_user(self, user_repository, mock_prisma):
        """Test finding a user by ID that doesn't exist."""
        mock_prisma.user.find_unique = AsyncMock(return_value=None)
        
        result = await user_repository.find_by_id('nonexistent-id')
        
        assert result is None


class TestUpdatePassword:
    """Tests for update_password method."""
    
    @pytest.mark.asyncio
    async def test_update_password_success(self, user_repository, mock_prisma, sample_user):
        """Test successfully updating a password."""
        old_hash = sample_user['password_hash']
        new_hash = bcrypt.hashpw(b"NewPassword456!", bcrypt.gensalt()).decode('utf-8')
        
        # Mock finding the user
        mock_user = MagicMock()
        mock_user.id = sample_user['id']
        mock_user.previous_password_hashes = []
        
        mock_prisma.user.find_unique = AsyncMock(return_value=mock_user)
        mock_prisma.user.update = AsyncMock()
        
        await user_repository.update_password('user-123', new_hash, old_hash)
        
        # Verify update was called with correct data
        mock_prisma.user.update.assert_called_once()
        call_args = mock_prisma.user.update.call_args
        assert call_args[1]['where'] == {'id': 'user-123'}
        assert call_args[1]['data']['password_hash'] == new_hash
        assert old_hash in call_args[1]['data']['previous_password_hashes']
    
    @pytest.mark.asyncio
    async def test_update_password_maintains_history(self, user_repository, mock_prisma):
        """Test that password history is maintained correctly."""
        hash1 = "hash1"
        hash2 = "hash2"
        hash3 = "hash3"
        new_hash = "new_hash"
        
        # Mock user with existing password history
        mock_user = MagicMock()
        mock_user.id = 'user-123'
        mock_user.previous_password_hashes = [hash1, hash2]
        
        mock_prisma.user.find_unique = AsyncMock(return_value=mock_user)
        mock_prisma.user.update = AsyncMock()
        
        await user_repository.update_password('user-123', new_hash, hash3)
        
        # Verify history is maintained
        call_args = mock_prisma.user.update.call_args
        previous_hashes = call_args[1]['data']['previous_password_hashes']
        assert previous_hashes == [hash3, hash1, hash2]
    
    @pytest.mark.asyncio
    async def test_update_password_limits_history(self, user_repository, mock_prisma):
        """Test that password history is limited to 5 entries."""
        existing_hashes = ['hash1', 'hash2', 'hash3', 'hash4', 'hash5']
        current_hash = 'hash6'
        new_hash = 'new_hash'
        
        mock_user = MagicMock()
        mock_user.id = 'user-123'
        mock_user.previous_password_hashes = existing_hashes
        
        mock_prisma.user.find_unique = AsyncMock(return_value=mock_user)
        mock_prisma.user.update = AsyncMock()
        
        await user_repository.update_password('user-123', new_hash, current_hash)
        
        # Verify history is limited to 5
        call_args = mock_prisma.user.update.call_args
        previous_hashes = call_args[1]['data']['previous_password_hashes']
        assert len(previous_hashes) == 5
        assert previous_hashes[0] == current_hash
        assert 'hash5' not in previous_hashes
    
    @pytest.mark.asyncio
    async def test_update_password_user_not_found(self, user_repository, mock_prisma):
        """Test updating password for non-existent user raises error."""
        mock_prisma.user.find_unique = AsyncMock(return_value=None)
        
        with pytest.raises(ValueError, match="User with id .* not found"):
            await user_repository.update_password('nonexistent', 'new_hash', 'old_hash')


class TestGetPreviousPasswordHashes:
    """Tests for get_previous_password_hashes method."""
    
    @pytest.mark.asyncio
    async def test_get_hashes_with_history(self, user_repository, mock_prisma):
        """Test getting password hashes when user has history."""
        current_hash = "current_hash"
        previous_hashes = ["hash1", "hash2", "hash3"]
        
        mock_user = MagicMock()
        mock_user.password_hash = current_hash
        mock_user.previous_password_hashes = previous_hashes
        
        mock_prisma.user.find_unique = AsyncMock(return_value=mock_user)
        
        result = await user_repository.get_previous_password_hashes('user-123')
        
        # Should return current hash plus previous hashes
        assert len(result) == 4
        assert result[0] == current_hash
        assert result[1:] == previous_hashes
    
    @pytest.mark.asyncio
    async def test_get_hashes_no_history(self, user_repository, mock_prisma):
        """Test getting password hashes when user has no history."""
        current_hash = "current_hash"
        
        mock_user = MagicMock()
        mock_user.password_hash = current_hash
        mock_user.previous_password_hashes = None
        
        mock_prisma.user.find_unique = AsyncMock(return_value=mock_user)
        
        result = await user_repository.get_previous_password_hashes('user-123')
        
        # Should return only current hash
        assert len(result) == 1
        assert result[0] == current_hash
    
    @pytest.mark.asyncio
    async def test_get_hashes_user_not_found(self, user_repository, mock_prisma):
        """Test getting hashes for non-existent user returns empty list."""
        mock_prisma.user.find_unique = AsyncMock(return_value=None)
        
        result = await user_repository.get_previous_password_hashes('nonexistent')
        
        assert result == []


class TestDatabaseConnection:
    """Tests for database connection handling."""
    
    @pytest.mark.asyncio
    async def test_connects_if_not_connected(self, mock_prisma):
        """Test that repository connects to database if not already connected."""
        mock_prisma.is_connected = MagicMock(return_value=False)
        mock_prisma.user.find_unique = AsyncMock(return_value=None)
        
        repository = UserRepository(db=mock_prisma)
        await repository.find_by_email('test@example.com')
        
        mock_prisma.connect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_skips_connect_if_already_connected(self, mock_prisma):
        """Test that repository doesn't reconnect if already connected."""
        mock_prisma.is_connected = MagicMock(return_value=True)
        mock_prisma.user.find_unique = AsyncMock(return_value=None)
        
        repository = UserRepository(db=mock_prisma)
        await repository.find_by_email('test@example.com')
        
        mock_prisma.connect.assert_not_called()
