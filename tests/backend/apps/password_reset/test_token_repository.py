"""
Tests for TokenRepository

Tests the data access layer for password reset tokens.
"""
import pytest
import pytest_asyncio
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from apps.users.password_reset.repositories.token_repository import TokenRepository
from apps.users.password_reset.types import Token
from prisma import Prisma


@pytest_asyncio.fixture
async def db():
    """Create a test database connection."""
    client = Prisma()
    await client.connect()
    yield client
    await client.disconnect()


@pytest_asyncio.fixture
async def token_repository(db):
    """Create a TokenRepository instance."""
    return TokenRepository(db)


@pytest.fixture
def sample_token():
    """Create a sample token for testing."""
    return Token(
        id=str(uuid4()),
        user_id='test-user-123',
        token_hash='test-hash-abc123',
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        created_at=datetime.now(timezone.utc),
        used_at=None,
        invalidated=False,
    )


@pytest.mark.asyncio
async def test_create_token(token_repository, sample_token, db):
    """Test creating a token in the database."""
    # Create the token
    created_token = await token_repository.create(sample_token)
    
    # Verify the token was created
    assert created_token.id == sample_token.id
    assert created_token.user_id == sample_token.user_id
    assert created_token.token_hash == sample_token.token_hash
    assert created_token.invalidated is False
    assert created_token.used_at is None
    
    # Clean up
    await db.passwordresettoken.delete(where={'id': created_token.id})


@pytest.mark.asyncio
async def test_find_by_token(token_repository, sample_token, db):
    """Test finding a token by its hash."""
    # Create a token first
    await token_repository.create(sample_token)
    
    # Find the token
    found_token = await token_repository.find_by_token(sample_token.token_hash)
    
    # Verify the token was found
    assert found_token is not None
    assert found_token.token_hash == sample_token.token_hash
    assert found_token.user_id == sample_token.user_id
    
    # Clean up
    await db.passwordresettoken.delete(where={'id': sample_token.id})


@pytest.mark.asyncio
async def test_find_by_token_not_found(token_repository):
    """Test finding a token that doesn't exist."""
    found_token = await token_repository.find_by_token('nonexistent-hash')
    assert found_token is None


@pytest.mark.asyncio
async def test_find_latest_by_user_id(token_repository, db):
    """Test finding the most recent token for a user."""
    user_id = 'test-user-456'
    
    # Create multiple tokens for the same user
    token1 = Token(
        id=str(uuid4()),
        user_id=user_id,
        token_hash='hash-1',
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        created_at=datetime.now(timezone.utc) - timedelta(minutes=10),
        used_at=None,
        invalidated=False,
    )
    
    token2 = Token(
        id=str(uuid4()),
        user_id=user_id,
        token_hash='hash-2',
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        created_at=datetime.now(timezone.utc) - timedelta(minutes=5),
        used_at=None,
        invalidated=False,
    )
    
    token3 = Token(
        id=str(uuid4()),
        user_id=user_id,
        token_hash='hash-3',
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        created_at=datetime.now(timezone.utc),
        used_at=None,
        invalidated=False,
    )
    
    await token_repository.create(token1)
    await token_repository.create(token2)
    await token_repository.create(token3)
    
    # Find the latest token
    latest_token = await token_repository.find_latest_by_user_id(user_id)
    
    # Verify it's the most recent one
    assert latest_token is not None
    assert latest_token.token_hash == 'hash-3'
    
    # Clean up
    await db.passwordresettoken.delete(where={'id': token1.id})
    await db.passwordresettoken.delete(where={'id': token2.id})
    await db.passwordresettoken.delete(where={'id': token3.id})


@pytest.mark.asyncio
async def test_find_latest_by_user_id_not_found(token_repository):
    """Test finding latest token for a user with no tokens."""
    latest_token = await token_repository.find_latest_by_user_id('nonexistent-user')
    assert latest_token is None


@pytest.mark.asyncio
async def test_update_token(token_repository, sample_token, db):
    """Test updating a token."""
    # Create a token first
    await token_repository.create(sample_token)
    
    # Update the token
    sample_token.used_at = datetime.now(timezone.utc)
    sample_token.invalidated = True
    
    updated_token = await token_repository.update(sample_token)
    
    # Verify the token was updated
    assert updated_token.used_at is not None
    assert updated_token.invalidated is True
    
    # Clean up
    await db.passwordresettoken.delete(where={'id': sample_token.id})


@pytest.mark.asyncio
async def test_invalidate_all_by_user_id(token_repository, db):
    """Test invalidating all tokens for a user."""
    user_id = 'test-user-789'
    
    # Create multiple tokens for the same user
    token1 = Token(
        id=str(uuid4()),
        user_id=user_id,
        token_hash='hash-a',
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        created_at=datetime.now(timezone.utc),
        used_at=None,
        invalidated=False,
    )
    
    token2 = Token(
        id=str(uuid4()),
        user_id=user_id,
        token_hash='hash-b',
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        created_at=datetime.now(timezone.utc),
        used_at=None,
        invalidated=False,
    )
    
    await token_repository.create(token1)
    await token_repository.create(token2)
    
    # Invalidate all tokens
    await token_repository.invalidate_all_by_user_id(user_id)
    
    # Verify all tokens are invalidated
    found_token1 = await token_repository.find_by_token('hash-a')
    found_token2 = await token_repository.find_by_token('hash-b')
    
    assert found_token1.invalidated is True
    assert found_token2.invalidated is True
    
    # Clean up
    await db.passwordresettoken.delete(where={'id': token1.id})
    await db.passwordresettoken.delete(where={'id': token2.id})


@pytest.mark.asyncio
async def test_delete_token(token_repository, sample_token, db):
    """Test deleting a token."""
    # Create a token first
    await token_repository.create(sample_token)
    
    # Delete the token
    await token_repository.delete(sample_token.id)
    
    # Verify the token was deleted
    found_token = await token_repository.find_by_token(sample_token.token_hash)
    assert found_token is None

