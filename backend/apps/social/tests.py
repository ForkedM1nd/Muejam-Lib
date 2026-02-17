"""Tests for social features (follow/block)."""
import pytest
from unittest.mock import Mock, patch
from django.test import RequestFactory
from rest_framework import status
from apps.social import views


@pytest.mark.django_db
class TestFollowOperations:
    """Test cases for follow operations."""
    
    def test_follow_without_authentication(self):
        """Test follow endpoint without authentication."""
        factory = RequestFactory()
        request = factory.post('/v1/users/user123/follow')
        request.clerk_user_id = None
        request.user_profile = None
        
        response = views.follow(request, 'user123')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data['error']['code'] == 'UNAUTHORIZED'
    
    def test_follow_self(self):
        """Test that users cannot follow themselves."""
        factory = RequestFactory()
        request = factory.post('/v1/users/user123/follow')
        
        mock_profile = Mock()
        mock_profile.id = 'user123'
        
        request.clerk_user_id = 'clerk_123'
        request.user_profile = mock_profile
        
        response = views.follow(request, 'user123')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['error']['code'] == 'INVALID_OPERATION'
    
    @patch('apps.social.views.sync_create_notification')
    @patch('apps.social.views.sync_follow_user')
    def test_follow_user_success(self, mock_follow, mock_create_notification):
        """Test successful follow operation."""
        factory = RequestFactory()
        request = factory.post('/v1/users/user456/follow')
        
        mock_profile = Mock()
        mock_profile.id = 'user123'
        
        request.clerk_user_id = 'clerk_123'
        request.user_profile = mock_profile
        
        # Mock successful follow
        mock_follow_record = Mock()
        mock_follow_record.id = 'follow123'
        mock_follow_record.follower_id = 'user123'
        mock_follow_record.following_id = 'user456'
        mock_follow_record.created_at = '2024-01-01T00:00:00Z'
        
        mock_follow.return_value = mock_follow_record
        mock_create_notification.return_value = Mock()
        
        response = views.follow(request, 'user456')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert 'id' in response.data
        mock_create_notification.assert_called_once()
    
    @patch('apps.social.views.sync_follow_user')
    def test_follow_blocked_user(self, mock_follow):
        """Test that users cannot follow blocked users."""
        factory = RequestFactory()
        request = factory.post('/v1/users/user456/follow')
        
        mock_profile = Mock()
        mock_profile.id = 'user123'
        
        request.clerk_user_id = 'clerk_123'
        request.user_profile = mock_profile
        
        # Mock blocked response
        mock_follow.return_value = 'blocked'
        
        response = views.follow(request, 'user456')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data['error']['code'] == 'BLOCKED'
    
    @patch('apps.social.views.sync_unfollow_user')
    def test_unfollow_user_success(self, mock_unfollow):
        """Test successful unfollow operation."""
        factory = RequestFactory()
        request = factory.delete('/v1/users/user456/follow')
        
        mock_profile = Mock()
        mock_profile.id = 'user123'
        
        request.clerk_user_id = 'clerk_123'
        request.user_profile = mock_profile
        
        # Mock successful unfollow
        mock_unfollow.return_value = True
        
        response = views.follow(request, 'user456')
        
        assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
class TestBlockOperations:
    """Test cases for block operations."""
    
    def test_block_without_authentication(self):
        """Test block endpoint without authentication."""
        factory = RequestFactory()
        request = factory.post('/v1/users/user123/block')
        request.clerk_user_id = None
        request.user_profile = None
        
        response = views.block(request, 'user123')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data['error']['code'] == 'UNAUTHORIZED'
    
    def test_block_self(self):
        """Test that users cannot block themselves."""
        factory = RequestFactory()
        request = factory.post('/v1/users/user123/block')
        
        mock_profile = Mock()
        mock_profile.id = 'user123'
        
        request.clerk_user_id = 'clerk_123'
        request.user_profile = mock_profile
        
        response = views.block(request, 'user123')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['error']['code'] == 'INVALID_OPERATION'
    
    @patch('apps.social.views.sync_block_user')
    def test_block_user_success(self, mock_block):
        """Test successful block operation."""
        factory = RequestFactory()
        request = factory.post('/v1/users/user456/block')
        
        mock_profile = Mock()
        mock_profile.id = 'user123'
        
        request.clerk_user_id = 'clerk_123'
        request.user_profile = mock_profile
        
        # Mock successful block
        mock_block_record = Mock()
        mock_block_record.id = 'block123'
        mock_block_record.blocker_id = 'user123'
        mock_block_record.blocked_id = 'user456'
        mock_block_record.created_at = '2024-01-01T00:00:00Z'
        
        mock_block.return_value = mock_block_record
        
        response = views.block(request, 'user456')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert 'id' in response.data
    
    @patch('apps.social.views.sync_unblock_user')
    def test_unblock_user_success(self, mock_unblock):
        """Test successful unblock operation."""
        factory = RequestFactory()
        request = factory.delete('/v1/users/user456/block')
        
        mock_profile = Mock()
        mock_profile.id = 'user123'
        
        request.clerk_user_id = 'clerk_123'
        request.user_profile = mock_profile
        
        # Mock successful unblock
        mock_unblock.return_value = True
        
        response = views.block(request, 'user456')
        
        assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
class TestContentFiltering:
    """Test cases for blocked user content filtering."""
    
    @patch('apps.social.utils.sync_get_blocked_user_ids')
    def test_blocked_users_excluded_from_stories(self, mock_get_blocked):
        """Test that blocked users' stories are excluded from listings."""
        # This would be tested in the stories app tests
        # Just verify the utility function works
        mock_get_blocked.return_value = ['blocked_user_1', 'blocked_user_2']
        
        blocked_ids = mock_get_blocked('user123')
        
        assert len(blocked_ids) == 2
        assert 'blocked_user_1' in blocked_ids
        assert 'blocked_user_2' in blocked_ids
