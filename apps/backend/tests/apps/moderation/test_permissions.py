"""Tests for moderation permission system."""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from rest_framework.response import Response
from rest_framework import status
from apps.moderation.permissions import (
    require_moderator_role,
    require_administrator,
    check_action_permission,
    can_perform_action,
    get_user_moderator_role
)


class MockModeratorRole:
    """Mock ModeratorRole object."""
    def __init__(self, role, is_active=True):
        self.role = role
        self.is_active = is_active


class MockRequest:
    """Mock request object."""
    def __init__(self, user_profile_id=None, moderator_role=None):
        self.user_profile = Mock()
        self.user_profile.id = user_profile_id
        self.moderator_role = moderator_role
        self.data = {}


@pytest.mark.asyncio
async def test_can_perform_action_administrator():
    """Test that administrators can perform any action."""
    with patch('apps.moderation.permissions.get_user_moderator_role', 
               return_value=MockModeratorRole('ADMINISTRATOR')):
        
        # Test all action types
        for action in ['DISMISS', 'WARN', 'HIDE', 'DELETE', 'SUSPEND']:
            can_perform, error = await can_perform_action('user123', action)
            assert can_perform is True
            assert error == ""


@pytest.mark.asyncio
async def test_can_perform_action_senior_moderator():
    """Test that senior moderators can perform allowed actions."""
    with patch('apps.moderation.permissions.get_user_moderator_role',
               return_value=MockModeratorRole('SENIOR_MODERATOR')):
        
        # Allowed actions
        for action in ['DISMISS', 'WARN', 'HIDE']:
            can_perform, error = await can_perform_action('user123', action)
            assert can_perform is True
            assert error == ""
        
        # Disallowed actions
        for action in ['DELETE', 'SUSPEND']:
            can_perform, error = await can_perform_action('user123', action)
            assert can_perform is False
            assert 'Senior Moderators cannot' in error


@pytest.mark.asyncio
async def test_can_perform_action_moderator():
    """Test that moderators can only dismiss low-priority reports."""
    with patch('apps.moderation.permissions.get_user_moderator_role',
               return_value=MockModeratorRole('MODERATOR')):
        
        # Can dismiss low-priority reports
        can_perform, error = await can_perform_action('user123', 'DISMISS', 'low')
        assert can_perform is True
        assert error == ""
        
        # Cannot dismiss medium or high-priority reports
        for priority in ['medium', 'high']:
            can_perform, error = await can_perform_action('user123', 'DISMISS', priority)
            assert can_perform is False
            assert 'low-priority' in error
        
        # Cannot perform other actions
        for action in ['WARN', 'HIDE', 'DELETE', 'SUSPEND']:
            can_perform, error = await can_perform_action('user123', action)
            assert can_perform is False
            assert 'cannot perform' in error


@pytest.mark.asyncio
async def test_can_perform_action_no_moderator_role():
    """Test that users without moderator role cannot perform actions."""
    with patch('apps.moderation.permissions.get_user_moderator_role',
               return_value=None):
        
        can_perform, error = await can_perform_action('user123', 'DISMISS')
        assert can_perform is False
        assert 'does not have moderator permissions' in error


def test_require_moderator_role_decorator_no_auth():
    """Test that decorator returns 401 for unauthenticated requests."""
    @require_moderator_role()
    def test_view(request):
        return Response({'success': True})
    
    # Request without user_profile
    request = Mock()
    request.user_profile = None
    
    response = test_view(request)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert 'Authentication required' in str(response.data)


def test_require_moderator_role_decorator_no_moderator_role():
    """Test that decorator returns 403 for non-moderators."""
    @require_moderator_role()
    def test_view(request):
        return Response({'success': True})
    
    request = MockRequest(user_profile_id='user123')
    
    with patch('apps.moderation.permissions.get_user_moderator_role',
               return_value=AsyncMock(return_value=None)):
        with patch('asyncio.run', return_value=None):
            response = test_view(request)
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert 'Moderator access required' in str(response.data)


def test_require_moderator_role_decorator_wrong_role():
    """Test that decorator returns 403 for insufficient role."""
    @require_moderator_role(['ADMINISTRATOR'])
    def test_view(request):
        return Response({'success': True})
    
    request = MockRequest(user_profile_id='user123')
    
    with patch('asyncio.run', return_value=MockModeratorRole('MODERATOR')):
        response = test_view(request)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert 'Insufficient permissions' in str(response.data)


def test_require_moderator_role_decorator_success():
    """Test that decorator allows access for correct role."""
    @require_moderator_role(['ADMINISTRATOR'])
    def test_view(request):
        return Response({'success': True})
    
    request = MockRequest(user_profile_id='user123')
    
    with patch('asyncio.run', return_value=MockModeratorRole('ADMINISTRATOR')):
        response = test_view(request)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {'success': True}


def test_require_administrator_decorator():
    """Test that require_administrator decorator works correctly."""
    @require_administrator
    def test_view(request):
        return Response({'success': True})
    
    request = MockRequest(user_profile_id='user123')
    
    # Test with non-admin role
    with patch('asyncio.run', return_value=MockModeratorRole('MODERATOR')):
        response = test_view(request)
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    # Test with admin role
    with patch('asyncio.run', return_value=MockModeratorRole('ADMINISTRATOR')):
        response = test_view(request)
        assert response.status_code == status.HTTP_200_OK


def test_check_action_permission_decorator_no_action_type():
    """Test that decorator returns 400 when action_type is missing."""
    @check_action_permission
    def test_view(request):
        return Response({'success': True})
    
    request = MockRequest(user_profile_id='user123')
    request.data = {}
    
    response = test_view(request)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'action_type is required' in str(response.data)


def test_check_action_permission_decorator_forbidden():
    """Test that decorator returns 403 for unauthorized action."""
    @check_action_permission
    def test_view(request):
        return Response({'success': True})
    
    request = MockRequest(user_profile_id='user123')
    request.data = {
        'action_type': 'DELETE',
        'report_id': 'report123'
    }
    
    async def mock_get_priority(report_id):
        return None
    
    async def mock_can_perform(user_id, action_type, priority):
        return (False, 'Insufficient permissions')
    
    with patch('apps.moderation.permissions.get_report_priority', side_effect=mock_get_priority):
        with patch('apps.moderation.permissions.can_perform_action', side_effect=mock_can_perform):
            response = test_view(request)
            assert response.status_code == status.HTTP_403_FORBIDDEN


def test_check_action_permission_decorator_success():
    """Test that decorator allows action when permissions are correct."""
    @check_action_permission
    def test_view(request):
        return Response({'success': True})
    
    request = MockRequest(user_profile_id='user123')
    request.data = {
        'action_type': 'DISMISS',
        'report_id': 'report123'
    }
    
    async def mock_get_priority(report_id):
        return 'low'
    
    async def mock_can_perform(user_id, action_type, priority):
        return (True, '')
    
    with patch('apps.moderation.permissions.get_report_priority', side_effect=mock_get_priority):
        with patch('apps.moderation.permissions.can_perform_action', side_effect=mock_can_perform):
            response = test_view(request)
            assert response.status_code == status.HTTP_200_OK
            assert response.data == {'success': True}


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
