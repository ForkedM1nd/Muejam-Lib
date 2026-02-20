"""
Unit tests for Shadowban Service.

Tests shadowban creation, checking, and content filtering.

Requirements: 5.12
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from apps.moderation.shadowban import ShadowbanService


@pytest.fixture
def shadowban_service():
    """Create ShadowbanService instance."""
    return ShadowbanService()


@pytest.fixture
def mock_db():
    """Create mock Prisma database client."""
    db = MagicMock()
    db.connect = AsyncMock()
    db.disconnect = AsyncMock()
    db.shadowban = MagicMock()
    db.moderatorrole = MagicMock()
    return db


class TestShadowban:
    """Test suite for shadowban functionality."""
    
    @pytest.mark.asyncio
    async def test_apply_shadowban(self, shadowban_service, mock_db):
        """
        Test applying a shadowban to a user.
        
        Requirements: 5.12
        """
        # Arrange
        user_id = "user-123"
        applied_by = "admin-456"
        reason = "Suspicious activity detected"
        
        mock_shadowban = MagicMock()
        mock_shadowban.id = "shadowban-789"
        mock_shadowban.user_id = user_id
        mock_shadowban.applied_by = applied_by
        mock_shadowban.reason = reason
        mock_shadowban.applied_at = datetime.now(timezone.utc)
        mock_shadowban.is_active = True
        
        mock_db.shadowban.update_many = AsyncMock(return_value=0)
        mock_db.shadowban.create = AsyncMock(return_value=mock_shadowban)
        
        # Act
        with patch('apps.moderation.shadowban.Prisma', return_value=mock_db):
            result = await shadowban_service.apply_shadowban(
                user_id=user_id,
                applied_by=applied_by,
                reason=reason
            )
        
        # Assert
        assert result['user_id'] == user_id
        assert result['applied_by'] == applied_by
        assert result['reason'] == reason
        assert result['is_active'] is True
        
        # Verify old shadowbans were deactivated
        mock_db.shadowban.update_many.assert_called_once()
        
        # Verify new shadowban was created
        mock_db.shadowban.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_check_shadowban_active(self, shadowban_service, mock_db):
        """
        Test checking an active shadowban.
        
        Requirements: 5.12
        """
        # Arrange
        user_id = "user-123"
        
        mock_shadowban = MagicMock()
        mock_shadowban.id = "shadowban-789"
        mock_shadowban.user_id = user_id
        mock_shadowban.applied_by = "admin-456"
        mock_shadowban.reason = "Test reason"
        mock_shadowban.applied_at = datetime.now(timezone.utc)
        mock_shadowban.is_active = True
        
        mock_db.shadowban.find_first = AsyncMock(return_value=mock_shadowban)
        
        # Act
        with patch('apps.moderation.shadowban.Prisma', return_value=mock_db):
            result = await shadowban_service.check_shadowban(user_id)
        
        # Assert
        assert result is not None
        assert result['user_id'] == user_id
        assert result['is_active'] is True
    
    @pytest.mark.asyncio
    async def test_check_shadowban_not_shadowbanned(self, shadowban_service, mock_db):
        """
        Test checking shadowban for non-shadowbanned user.
        
        Requirements: 5.12
        """
        # Arrange
        user_id = "user-123"
        mock_db.shadowban.find_first = AsyncMock(return_value=None)
        
        # Act
        with patch('apps.moderation.shadowban.Prisma', return_value=mock_db):
            result = await shadowban_service.check_shadowban(user_id)
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    async def test_is_shadowbanned_true(self, shadowban_service, mock_db):
        """
        Test is_shadowbanned returns True for shadowbanned user.
        
        Requirements: 5.12
        """
        # Arrange
        user_id = "user-123"
        
        mock_shadowban = MagicMock()
        mock_shadowban.id = "shadowban-789"
        mock_shadowban.user_id = user_id
        mock_shadowban.is_active = True
        
        mock_db.shadowban.find_first = AsyncMock(return_value=mock_shadowban)
        
        # Act
        with patch('apps.moderation.shadowban.Prisma', return_value=mock_db):
            result = await shadowban_service.is_shadowbanned(user_id)
        
        # Assert
        assert result is True
    
    @pytest.mark.asyncio
    async def test_is_shadowbanned_false(self, shadowban_service, mock_db):
        """
        Test is_shadowbanned returns False for non-shadowbanned user.
        
        Requirements: 5.12
        """
        # Arrange
        user_id = "user-123"
        mock_db.shadowban.find_first = AsyncMock(return_value=None)
        
        # Act
        with patch('apps.moderation.shadowban.Prisma', return_value=mock_db):
            result = await shadowban_service.is_shadowbanned(user_id)
        
        # Assert
        assert result is False
    
    @pytest.mark.asyncio
    async def test_remove_shadowban(self, shadowban_service, mock_db):
        """
        Test removing a shadowban.
        """
        # Arrange
        user_id = "user-123"
        removed_by = "admin-456"
        
        mock_db.shadowban.update_many = AsyncMock(return_value=1)
        
        # Act
        with patch('apps.moderation.shadowban.Prisma', return_value=mock_db):
            result = await shadowban_service.remove_shadowban(user_id, removed_by)
        
        # Assert
        assert result is True
        mock_db.shadowban.update_many.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_remove_shadowban_no_active(self, shadowban_service, mock_db):
        """
        Test removing shadowban when no active shadowban exists.
        """
        # Arrange
        user_id = "user-123"
        removed_by = "admin-456"
        
        mock_db.shadowban.update_many = AsyncMock(return_value=0)
        
        # Act
        with patch('apps.moderation.shadowban.Prisma', return_value=mock_db):
            result = await shadowban_service.remove_shadowban(user_id, removed_by)
        
        # Assert
        assert result is False
    
    @pytest.mark.asyncio
    async def test_filter_shadowbanned_content_no_shadowbans(self, shadowban_service, mock_db):
        """
        Test content filtering when no users are shadowbanned.
        
        Requirements: 5.12
        """
        # Arrange
        content_list = [
            {'id': '1', 'user_id': 'user-1', 'content': 'Test 1'},
            {'id': '2', 'user_id': 'user-2', 'content': 'Test 2'},
        ]
        
        mock_db.shadowban.find_many = AsyncMock(return_value=[])
        
        # Act
        with patch('apps.moderation.shadowban.Prisma', return_value=mock_db):
            result = await shadowban_service.filter_shadowbanned_content(
                content_list,
                requesting_user_id='user-3'
            )
        
        # Assert
        assert len(result) == 2
        assert result == content_list
    
    @pytest.mark.asyncio
    async def test_filter_shadowbanned_content_hides_from_others(self, shadowban_service, mock_db):
        """
        Test that shadowbanned content is hidden from other users.
        
        Requirements: 5.12
        """
        # Arrange
        content_list = [
            {'id': '1', 'user_id': 'user-1', 'content': 'Test 1'},
            {'id': '2', 'user_id': 'user-2', 'content': 'Test 2'},  # Shadowbanned
            {'id': '3', 'user_id': 'user-3', 'content': 'Test 3'},
        ]
        
        mock_shadowban = MagicMock()
        mock_shadowban.user_id = 'user-2'
        
        mock_db.shadowban.find_many = AsyncMock(return_value=[mock_shadowban])
        mock_db.moderatorrole.find_first = AsyncMock(return_value=None)
        
        # Act
        with patch('apps.moderation.shadowban.Prisma', return_value=mock_db):
            result = await shadowban_service.filter_shadowbanned_content(
                content_list,
                requesting_user_id='user-1'
            )
        
        # Assert
        assert len(result) == 2
        assert result[0]['user_id'] == 'user-1'
        assert result[1]['user_id'] == 'user-3'
    
    @pytest.mark.asyncio
    async def test_filter_shadowbanned_content_shows_to_self(self, shadowban_service, mock_db):
        """
        Test that shadowbanned users can see their own content.
        
        Requirements: 5.12
        """
        # Arrange
        content_list = [
            {'id': '1', 'user_id': 'user-1', 'content': 'Test 1'},
            {'id': '2', 'user_id': 'user-2', 'content': 'Test 2'},  # Shadowbanned
        ]
        
        mock_shadowban = MagicMock()
        mock_shadowban.user_id = 'user-2'
        
        mock_db.shadowban.find_many = AsyncMock(return_value=[mock_shadowban])
        mock_db.moderatorrole.find_first = AsyncMock(return_value=None)
        
        # Act
        with patch('apps.moderation.shadowban.Prisma', return_value=mock_db):
            result = await shadowban_service.filter_shadowbanned_content(
                content_list,
                requesting_user_id='user-2'  # Shadowbanned user viewing their own content
            )
        
        # Assert
        assert len(result) == 2  # Should see all content including their own
    
    @pytest.mark.asyncio
    async def test_filter_shadowbanned_content_shows_to_moderator(self, shadowban_service, mock_db):
        """
        Test that moderators can see shadowbanned content.
        
        Requirements: 5.12
        """
        # Arrange
        content_list = [
            {'id': '1', 'user_id': 'user-1', 'content': 'Test 1'},
            {'id': '2', 'user_id': 'user-2', 'content': 'Test 2'},  # Shadowbanned
        ]
        
        mock_shadowban = MagicMock()
        mock_shadowban.user_id = 'user-2'
        
        mock_moderator_role = MagicMock()
        mock_moderator_role.user_id = 'moderator-1'
        mock_moderator_role.is_active = True
        
        mock_db.shadowban.find_many = AsyncMock(return_value=[mock_shadowban])
        mock_db.moderatorrole.find_first = AsyncMock(return_value=mock_moderator_role)
        
        # Act
        with patch('apps.moderation.shadowban.Prisma', return_value=mock_db):
            result = await shadowban_service.filter_shadowbanned_content(
                content_list,
                requesting_user_id='moderator-1'
            )
        
        # Assert
        assert len(result) == 2  # Moderator should see all content
    
    @pytest.mark.asyncio
    async def test_filter_shadowbanned_content_with_author_id(self, shadowban_service, mock_db):
        """
        Test content filtering works with 'author_id' field (for stories).
        
        Requirements: 5.12
        """
        # Arrange
        content_list = [
            {'id': '1', 'author_id': 'user-1', 'title': 'Story 1'},
            {'id': '2', 'author_id': 'user-2', 'title': 'Story 2'},  # Shadowbanned
        ]
        
        mock_shadowban = MagicMock()
        mock_shadowban.user_id = 'user-2'
        
        mock_db.shadowban.find_many = AsyncMock(return_value=[mock_shadowban])
        mock_db.moderatorrole.find_first = AsyncMock(return_value=None)
        
        # Act
        with patch('apps.moderation.shadowban.Prisma', return_value=mock_db):
            result = await shadowban_service.filter_shadowbanned_content(
                content_list,
                requesting_user_id='user-3'
            )
        
        # Assert
        assert len(result) == 1
        assert result[0]['author_id'] == 'user-1'
    
    @pytest.mark.asyncio
    async def test_get_shadowban_history(self, shadowban_service, mock_db):
        """
        Test retrieving shadowban history for a user.
        """
        # Arrange
        user_id = "user-123"
        
        mock_shadowbans = [
            MagicMock(
                id="shadowban-1",
                applied_by="admin-1",
                reason="First offense",
                applied_at=datetime.now(timezone.utc),
                is_active=False
            ),
            MagicMock(
                id="shadowban-2",
                applied_by="admin-2",
                reason="Second offense",
                applied_at=datetime.now(timezone.utc),
                is_active=True
            )
        ]
        
        mock_db.shadowban.find_many = AsyncMock(return_value=mock_shadowbans)
        
        # Act
        with patch('apps.moderation.shadowban.Prisma', return_value=mock_db):
            result = await shadowban_service.get_shadowban_history(user_id)
        
        # Assert
        assert len(result) == 2
        assert result[0]['id'] == "shadowban-1"
        assert result[0]['is_active'] is False
        assert result[1]['id'] == "shadowban-2"
        assert result[1]['is_active'] is True
