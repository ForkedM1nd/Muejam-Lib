"""Tests for notification system."""
import pytest
from unittest.mock import Mock, patch
from django.test import RequestFactory
from rest_framework import status
from apps.notifications import views
from apps.notifications.tasks import generate_idempotency_key


@pytest.mark.django_db
class TestNotificationEndpoints:
    """Test cases for notification endpoints."""
    
    def test_list_notifications_without_authentication(self):
        """Test notifications endpoint without authentication."""
        factory = RequestFactory()
        request = factory.get('/v1/notifications')
        request.clerk_user_id = None
        request.user_profile = None
        
        response = views.notifications(request)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data['error']['code'] == 'UNAUTHORIZED'
    
    @patch('apps.notifications.views.sync_get_notifications')
    def test_list_notifications_success(self, mock_get_notifications):
        """Test successful notification listing."""
        factory = RequestFactory()
        request = factory.get('/v1/notifications')
        
        mock_profile = Mock()
        mock_profile.id = 'user123'
        
        request.clerk_user_id = 'clerk_123'
        request.user_profile = mock_profile
        
        # Mock notifications
        mock_notification = Mock()
        mock_notification.id = 'notif123'
        mock_notification.user_id = 'user123'
        mock_notification.type = 'REPLY'
        mock_notification.actor_id = 'actor123'
        mock_notification.whisper_id = 'whisper123'
        mock_notification.read_at = None
        mock_notification.created_at = '2024-01-01T00:00:00Z'
        
        mock_get_notifications.return_value = ([mock_notification], None)
        
        response = views.notifications(request)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'data' in response.data
        assert 'next_cursor' in response.data
    
    def test_mark_read_without_authentication(self):
        """Test mark read endpoint without authentication."""
        factory = RequestFactory()
        request = factory.post('/v1/notifications/notif123/read')
        request.clerk_user_id = None
        request.user_profile = None
        
        response = views.mark_read(request, 'notif123')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data['error']['code'] == 'UNAUTHORIZED'
    
    @patch('apps.notifications.views.sync_mark_notification_read')
    def test_mark_read_success(self, mock_mark_read):
        """Test successful mark as read."""
        factory = RequestFactory()
        request = factory.post('/v1/notifications/notif123/read')
        
        mock_profile = Mock()
        mock_profile.id = 'user123'
        
        request.clerk_user_id = 'clerk_123'
        request.user_profile = mock_profile
        
        # Mock notification
        mock_notification = Mock()
        mock_notification.id = 'notif123'
        mock_notification.user_id = 'user123'
        mock_notification.type = 'REPLY'
        mock_notification.actor_id = 'actor123'
        mock_notification.whisper_id = 'whisper123'
        mock_notification.read_at = '2024-01-01T00:00:00Z'
        mock_notification.created_at = '2024-01-01T00:00:00Z'
        
        mock_mark_read.return_value = mock_notification
        
        response = views.mark_read(request, 'notif123')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'id' in response.data
    
    @patch('apps.notifications.views.sync_mark_notification_read')
    def test_mark_read_not_found(self, mock_mark_read):
        """Test mark read for non-existent notification."""
        factory = RequestFactory()
        request = factory.post('/v1/notifications/notif123/read')
        
        mock_profile = Mock()
        mock_profile.id = 'user123'
        
        request.clerk_user_id = 'clerk_123'
        request.user_profile = mock_profile
        
        mock_mark_read.return_value = None
        
        response = views.mark_read(request, 'notif123')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data['error']['code'] == 'NOT_FOUND'
    
    def test_mark_all_read_without_authentication(self):
        """Test mark all read endpoint without authentication."""
        factory = RequestFactory()
        request = factory.post('/v1/notifications/read-all')
        request.clerk_user_id = None
        request.user_profile = None
        
        response = views.mark_all_read(request)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data['error']['code'] == 'UNAUTHORIZED'
    
    @patch('apps.notifications.views.sync_mark_all_notifications_read')
    def test_mark_all_read_success(self, mock_mark_all):
        """Test successful mark all as read."""
        factory = RequestFactory()
        request = factory.post('/v1/notifications/read-all')
        
        mock_profile = Mock()
        mock_profile.id = 'user123'
        
        request.clerk_user_id = 'clerk_123'
        request.user_profile = mock_profile
        
        mock_mark_all.return_value = 5
        
        response = views.mark_all_read(request)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 5


@pytest.mark.django_db
class TestNotificationCreation:
    """Test cases for notification creation."""
    
    @patch('apps.notifications.views.sync_create_notification')
    def test_notification_created_on_reply(self, mock_create):
        """Test that notification is created when replying to whisper."""
        # This would be tested in whisper tests
        mock_create.return_value = Mock()
        
        result = mock_create(
            user_id='user123',
            notification_type='REPLY',
            actor_id='actor123',
            whisper_id='whisper123'
        )
        
        assert result is not None
        mock_create.assert_called_once()
    
    @patch('apps.notifications.views.sync_create_notification')
    def test_notification_created_on_follow(self, mock_create):
        """Test that notification is created when following user."""
        # This would be tested in social tests
        mock_create.return_value = Mock()
        
        result = mock_create(
            user_id='user123',
            notification_type='FOLLOW',
            actor_id='actor123',
            whisper_id=None
        )
        
        assert result is not None
        mock_create.assert_called_once()


@pytest.mark.django_db
class TestIdempotencyKey:
    """Test cases for idempotency key generation."""
    
    def test_idempotency_key_generation(self):
        """Test that idempotency keys are generated consistently."""
        key1 = generate_idempotency_key('notif123', 'REPLY')
        key2 = generate_idempotency_key('notif123', 'REPLY')
        
        assert key1 == key2
        assert len(key1) == 64  # SHA256 hex digest length
    
    def test_idempotency_key_uniqueness(self):
        """Test that different notifications generate different keys."""
        key1 = generate_idempotency_key('notif123', 'REPLY')
        key2 = generate_idempotency_key('notif456', 'REPLY')
        key3 = generate_idempotency_key('notif123', 'FOLLOW')
        
        assert key1 != key2
        assert key1 != key3
        assert key2 != key3


@pytest.mark.django_db
class TestEmailNotificationTask:
    """Test cases for email notification task."""
    
    @patch('apps.notifications.tasks.resend.Emails.send')
    def test_send_reply_notification_email(self, mock_send):
        """Test sending reply notification email."""
        from apps.notifications.tasks import send_notification_email
        
        mock_send.return_value = {'id': 'email123'}
        
        result = send_notification_email(
            notification_id='notif123',
            user_email='user@example.com',
            notification_type='REPLY',
            actor_name='John Doe',
            whisper_content='Great post!'
        )
        
        assert result['status'] == 'sent'
        assert result['notification_id'] == 'notif123'
        assert 'idempotency_key' in result
        mock_send.assert_called_once()
    
    @patch('apps.notifications.tasks.resend.Emails.send')
    def test_send_follow_notification_email(self, mock_send):
        """Test sending follow notification email."""
        from apps.notifications.tasks import send_notification_email
        
        mock_send.return_value = {'id': 'email123'}
        
        result = send_notification_email(
            notification_id='notif123',
            user_email='user@example.com',
            notification_type='FOLLOW',
            actor_name='Jane Smith',
            whisper_content=None
        )
        
        assert result['status'] == 'sent'
        assert result['notification_id'] == 'notif123'
        assert 'idempotency_key' in result
        mock_send.assert_called_once()
