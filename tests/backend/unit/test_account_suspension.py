"""
Unit tests for Account Suspension Service.

Tests suspension creation, checking, expiration, and enforcement.

Requirements: 5.13, 5.14
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from apps.users.account_suspension import AccountSuspensionService


@pytest.fixture
def suspension_service():
    """Create AccountSuspensionService instance."""
    return AccountSuspensionService()


@pytest.fixture
def mock_db():
    """Create mock Prisma database client."""
    db = MagicMock()
    db.connect = AsyncMock()
    db.disconnect = AsyncMock()
    db.accountsuspension = MagicMock()
    return db


class TestAccountSuspension:
    """Test suite for account suspension functionality."""
    
    @pytest.mark.asyncio
    async def test_suspend_account_temporary(self, suspension_service, mock_db):
        """
        Test creating a temporary account suspension.
        
        Requirements: 5.13
        """
        # Arrange
        user_id = "user-123"
        suspended_by = "admin-456"
        reason = "Spam behavior detected"
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        
        mock_suspension = MagicMock()
        mock_suspension.id = "suspension-789"
        mock_suspension.user_id = user_id
        mock_suspension.suspended_by = suspended_by
        mock_suspension.reason = reason
        mock_suspension.suspended_at = datetime.now(timezone.utc)
        mock_suspension.expires_at = expires_at
        
        mock_db.accountsuspension.update_many = AsyncMock(return_value=0)
        mock_db.accountsuspension.create = AsyncMock(return_value=mock_suspension)
        
        # Act
        with patch('infrastructure.account_suspension.Prisma', return_value=mock_db):
            result = await suspension_service.suspend_account(
                user_id=user_id,
                suspended_by=suspended_by,
                reason=reason,
                expires_at=expires_at
            )
        
        # Assert
        assert result['user_id'] == user_id
        assert result['suspended_by'] == suspended_by
        assert result['reason'] == reason
        assert result['expires_at'] == expires_at
        assert result['is_permanent'] is False
        
        # Verify old suspensions were deactivated
        mock_db.accountsuspension.update_many.assert_called_once()
        
        # Verify new suspension was created
        mock_db.accountsuspension.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_suspend_account_permanent(self, suspension_service, mock_db):
        """
        Test creating a permanent account suspension.
        
        Requirements: 5.13
        """
        # Arrange
        user_id = "user-123"
        suspended_by = "admin-456"
        reason = "Severe ToS violation"
        
        mock_suspension = MagicMock()
        mock_suspension.id = "suspension-789"
        mock_suspension.user_id = user_id
        mock_suspension.suspended_by = suspended_by
        mock_suspension.reason = reason
        mock_suspension.suspended_at = datetime.now(timezone.utc)
        mock_suspension.expires_at = None
        
        mock_db.accountsuspension.update_many = AsyncMock(return_value=0)
        mock_db.accountsuspension.create = AsyncMock(return_value=mock_suspension)
        
        # Act
        with patch('infrastructure.account_suspension.Prisma', return_value=mock_db):
            result = await suspension_service.suspend_account(
                user_id=user_id,
                suspended_by=suspended_by,
                reason=reason,
                expires_at=None
            )
        
        # Assert
        assert result['user_id'] == user_id
        assert result['expires_at'] is None
        assert result['is_permanent'] is True
    
    @pytest.mark.asyncio
    async def test_check_suspension_active(self, suspension_service, mock_db):
        """
        Test checking an active suspension.
        
        Requirements: 5.14
        """
        # Arrange
        user_id = "user-123"
        
        mock_suspension = MagicMock()
        mock_suspension.id = "suspension-789"
        mock_suspension.user_id = user_id
        mock_suspension.suspended_by = "admin-456"
        mock_suspension.reason = "Test reason"
        mock_suspension.suspended_at = datetime.now(timezone.utc)
        mock_suspension.expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        
        mock_db.accountsuspension.find_first = AsyncMock(return_value=mock_suspension)
        
        # Act
        with patch('infrastructure.account_suspension.Prisma', return_value=mock_db):
            result = await suspension_service.check_suspension(user_id)
        
        # Assert
        assert result is not None
        assert result['user_id'] == user_id
        assert result['is_permanent'] is False
    
    @pytest.mark.asyncio
    async def test_check_suspension_not_suspended(self, suspension_service, mock_db):
        """
        Test checking suspension for non-suspended user.
        
        Requirements: 5.14
        """
        # Arrange
        user_id = "user-123"
        mock_db.accountsuspension.find_first = AsyncMock(return_value=None)
        
        # Act
        with patch('infrastructure.account_suspension.Prisma', return_value=mock_db):
            result = await suspension_service.check_suspension(user_id)
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    async def test_check_suspension_expired(self, suspension_service, mock_db):
        """
        Test that expired suspensions are automatically deactivated.
        
        Requirements: 5.14
        """
        # Arrange
        user_id = "user-123"
        
        mock_suspension = MagicMock()
        mock_suspension.id = "suspension-789"
        mock_suspension.user_id = user_id
        mock_suspension.expires_at = datetime.now(timezone.utc) - timedelta(days=1)  # Expired
        
        mock_db.accountsuspension.find_first = AsyncMock(return_value=mock_suspension)
        mock_db.accountsuspension.update = AsyncMock()
        
        # Act
        with patch('infrastructure.account_suspension.Prisma', return_value=mock_db):
            result = await suspension_service.check_suspension(user_id)
        
        # Assert
        assert result is None
        
        # Verify suspension was deactivated
        mock_db.accountsuspension.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_lift_suspension(self, suspension_service, mock_db):
        """
        Test manually lifting a suspension.
        """
        # Arrange
        user_id = "user-123"
        lifted_by = "admin-456"
        
        mock_db.accountsuspension.update_many = AsyncMock(return_value=1)
        
        # Act
        with patch('infrastructure.account_suspension.Prisma', return_value=mock_db):
            result = await suspension_service.lift_suspension(user_id, lifted_by)
        
        # Assert
        assert result is True
        mock_db.accountsuspension.update_many.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_lift_suspension_no_active(self, suspension_service, mock_db):
        """
        Test lifting suspension when no active suspension exists.
        """
        # Arrange
        user_id = "user-123"
        lifted_by = "admin-456"
        
        mock_db.accountsuspension.update_many = AsyncMock(return_value=0)
        
        # Act
        with patch('infrastructure.account_suspension.Prisma', return_value=mock_db):
            result = await suspension_service.lift_suspension(user_id, lifted_by)
        
        # Assert
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_suspension_history(self, suspension_service, mock_db):
        """
        Test retrieving suspension history for a user.
        """
        # Arrange
        user_id = "user-123"
        
        mock_suspensions = [
            MagicMock(
                id="suspension-1",
                suspended_by="admin-1",
                reason="First offense",
                suspended_at=datetime.now(timezone.utc) - timedelta(days=30),
                expires_at=datetime.now(timezone.utc) - timedelta(days=23),
                is_active=False
            ),
            MagicMock(
                id="suspension-2",
                suspended_by="admin-2",
                reason="Second offense",
                suspended_at=datetime.now(timezone.utc),
                expires_at=None,
                is_active=True
            )
        ]
        
        mock_db.accountsuspension.find_many = AsyncMock(return_value=mock_suspensions)
        
        # Act
        with patch('infrastructure.account_suspension.Prisma', return_value=mock_db):
            result = await suspension_service.get_suspension_history(user_id)
        
        # Assert
        assert len(result) == 2
        assert result[0]['id'] == "suspension-1"
        assert result[0]['is_active'] is False
        assert result[1]['id'] == "suspension-2"
        assert result[1]['is_active'] is True
        assert result[1]['is_permanent'] is True
