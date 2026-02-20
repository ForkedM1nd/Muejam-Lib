"""
Unit tests for push notification service.

Tests the PushNotificationService for device token registration,
notification sending, and integration with FCM and APNs.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime

from apps.notifications.push_service import PushNotificationService


@pytest.mark.asyncio
@pytest.mark.django_db
class TestDeviceTokenRegistration:
    """Test cases for device token registration."""
    
    async def test_register_device_android(self):
        """Test registering an Android device token."""
        service = PushNotificationService()
        
        with patch.object(service, '_ensure_connected', new_callable=AsyncMock), \
             patch('prisma.actions.DeviceTokenActions.find_unique', new_callable=AsyncMock, return_value=None), \
             patch('prisma.actions.DeviceTokenActions.create', new_callable=AsyncMock) as mock_create:
            
            mock_token = Mock()
            mock_token.id = 'device123'
            mock_token.user_id = 'user123'
            mock_token.token = 'fcm_token_123'
            mock_token.platform = 'android'
            mock_token.app_version = '1.0.0'
            mock_token.is_active = True
            mock_token.created_at = datetime.now()
            mock_token.last_used_at = datetime.now()
            
            mock_create.return_value = mock_token
            
            result = await service.register_device(
                user_id='user123',
                token='fcm_token_123',
                platform='android',
                app_version='1.0.0'
            )
            
            assert result['id'] == 'device123'
            assert result['user_id'] == 'user123'
            assert result['platform'] == 'android'
            assert result['app_version'] == '1.0.0'
            assert result['is_active'] is True
            
            mock_create.assert_called_once()
    
    async def test_register_device_ios(self):
        """Test registering an iOS device token."""
        service = PushNotificationService()
        
        with patch.object(service, '_ensure_connected', new_callable=AsyncMock), \
             patch('prisma.actions.DeviceTokenActions.find_unique', new_callable=AsyncMock, return_value=None), \
             patch('prisma.actions.DeviceTokenActions.create', new_callable=AsyncMock) as mock_create:
            
            mock_token = Mock()
            mock_token.id = 'device456'
            mock_token.user_id = 'user456'
            mock_token.token = 'apns_token_456'
            mock_token.platform = 'ios'
            mock_token.app_version = '1.0.0'
            mock_token.is_active = True
            mock_token.created_at = datetime.now()
            mock_token.last_used_at = datetime.now()
            
            mock_create.return_value = mock_token
            
            result = await service.register_device(
                user_id='user456',
                token='apns_token_456',
                platform='ios',
                app_version='1.0.0'
            )
            
            assert result['id'] == 'device456'
            assert result['user_id'] == 'user456'
            assert result['platform'] == 'ios'
            assert result['is_active'] is True
    
    async def test_register_device_invalid_platform(self):
        """Test registering device with invalid platform."""
        service = PushNotificationService()
        
        with pytest.raises(ValueError) as exc_info:
            await service.register_device(
                user_id='user123',
                token='token123',
                platform='windows',
                app_version='1.0.0'
            )
        
        assert "Invalid platform" in str(exc_info.value)
    
    async def test_register_device_updates_existing_token(self):
        """Test that registering an existing token updates it."""
        service = PushNotificationService()
        
        with patch.object(service, '_ensure_connected', new_callable=AsyncMock), \
             patch('prisma.actions.DeviceTokenActions.find_unique', new_callable=AsyncMock) as mock_find, \
             patch('prisma.actions.DeviceTokenActions.update', new_callable=AsyncMock) as mock_update:
            
            # Existing token
            existing_token = Mock()
            existing_token.id = 'device123'
            existing_token.user_id = 'old_user'
            existing_token.token = 'token123'
            
            mock_find.return_value = existing_token
            
            # Updated token
            updated_token = Mock()
            updated_token.id = 'device123'
            updated_token.user_id = 'new_user'
            updated_token.token = 'token123'
            updated_token.platform = 'android'
            updated_token.app_version = '2.0.0'
            updated_token.is_active = True
            updated_token.created_at = datetime.now()
            updated_token.last_used_at = datetime.now()
            
            mock_update.return_value = updated_token
            
            result = await service.register_device(
                user_id='new_user',
                token='token123',
                platform='android',
                app_version='2.0.0'
            )
            
            assert result['user_id'] == 'new_user'
            assert result['app_version'] == '2.0.0'
            mock_update.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.django_db
class TestDeviceTokenUnregistration:
    """Test cases for device token unregistration."""
    
    async def test_unregister_device_success(self):
        """Test successfully unregistering a device."""
        service = PushNotificationService()
        
        with patch.object(service, '_ensure_connected', new_callable=AsyncMock), \
             patch('prisma.actions.DeviceTokenActions.find_unique', new_callable=AsyncMock) as mock_find, \
             patch('prisma.actions.DeviceTokenActions.update', new_callable=AsyncMock) as mock_update:
            
            mock_token = Mock()
            mock_token.id = 'device123'
            mock_token.token = 'token123'
            
            mock_find.return_value = mock_token
            mock_update.return_value = mock_token
            
            result = await service.unregister_device('token123')
            
            assert result is True
            mock_update.assert_called_once()
    
    async def test_unregister_device_not_found(self):
        """Test unregistering a non-existent device."""
        service = PushNotificationService()
        
        with patch.object(service, '_ensure_connected', new_callable=AsyncMock), \
             patch('prisma.actions.DeviceTokenActions.find_unique', new_callable=AsyncMock, return_value=None):
            
            result = await service.unregister_device('nonexistent_token')
            
            assert result is False


@pytest.mark.asyncio
@pytest.mark.django_db
class TestGetUserDevices:
    """Test cases for retrieving user devices."""
    
    async def test_get_user_devices_multiple(self):
        """Test getting multiple devices for a user."""
        service = PushNotificationService()
        
        with patch.object(service, '_ensure_connected', new_callable=AsyncMock), \
             patch('prisma.actions.DeviceTokenActions.find_many', new_callable=AsyncMock) as mock_find:
            
            mock_device1 = Mock()
            mock_device1.id = 'device1'
            mock_device1.token = 'token1'
            mock_device1.platform = 'android'
            mock_device1.app_version = '1.0.0'
            mock_device1.last_used_at = datetime.now()
            
            mock_device2 = Mock()
            mock_device2.id = 'device2'
            mock_device2.token = 'token2'
            mock_device2.platform = 'ios'
            mock_device2.app_version = '1.0.0'
            mock_device2.last_used_at = datetime.now()
            
            mock_find.return_value = [mock_device1, mock_device2]
            
            result = await service.get_user_devices('user123')
            
            assert len(result) == 2
            assert result[0]['platform'] == 'android'
            assert result[1]['platform'] == 'ios'
    
    async def test_get_user_devices_none(self):
        """Test getting devices for user with no devices."""
        service = PushNotificationService()
        
        with patch.object(service, '_ensure_connected', new_callable=AsyncMock), \
             patch('prisma.actions.DeviceTokenActions.find_many', new_callable=AsyncMock, return_value=[]):
            
            result = await service.get_user_devices('user123')
            
            assert len(result) == 0


@pytest.mark.asyncio
@pytest.mark.django_db
class TestSendNotification:
    """Test cases for sending push notifications."""
    
    async def test_send_notification_no_devices(self):
        """Test sending notification to user with no devices."""
        service = PushNotificationService()
        
        with patch.object(service, 'get_user_devices', new_callable=AsyncMock, return_value=[]):
            
            result = await service.send_notification(
                user_id='user123',
                title='Test Notification',
                body='This is a test'
            )
            
            assert result['total_devices'] == 0
            assert result['sent'] == 0
            assert result['failed'] == 0
    
    async def test_send_notification_to_android_device(self):
        """Test sending notification to Android device."""
        service = PushNotificationService()
        
        mock_device = {
            'id': 'device1',
            'token': 'fcm_token',
            'platform': 'android',
            'app_version': '1.0.0',
            'last_used_at': datetime.now().isoformat()
        }
        
        with patch.object(service, 'get_user_devices', new_callable=AsyncMock, return_value=[mock_device]), \
             patch.object(service, '_send_to_fcm', new_callable=AsyncMock, return_value=True), \
             patch.object(service, '_log_notification', new_callable=AsyncMock):
            
            result = await service.send_notification(
                user_id='user123',
                title='Test Notification',
                body='This is a test',
                data={'key': 'value'}
            )
            
            assert result['total_devices'] == 1
            assert result['sent'] == 1
            assert result['failed'] == 0
    
    async def test_send_notification_to_ios_device(self):
        """Test sending notification to iOS device."""
        service = PushNotificationService()
        
        mock_device = {
            'id': 'device1',
            'token': 'apns_token',
            'platform': 'ios',
            'app_version': '1.0.0',
            'last_used_at': datetime.now().isoformat()
        }
        
        with patch.object(service, 'get_user_devices', new_callable=AsyncMock, return_value=[mock_device]), \
             patch.object(service, '_send_to_apns', new_callable=AsyncMock, return_value=True), \
             patch.object(service, '_log_notification', new_callable=AsyncMock):
            
            result = await service.send_notification(
                user_id='user123',
                title='Test Notification',
                body='This is a test'
            )
            
            assert result['total_devices'] == 1
            assert result['sent'] == 1
            assert result['failed'] == 0
    
    async def test_send_notification_mixed_success_failure(self):
        """Test sending notification with mixed success and failure."""
        service = PushNotificationService()
        
        mock_devices = [
            {
                'id': 'device1',
                'token': 'token1',
                'platform': 'android',
                'app_version': '1.0.0',
                'last_used_at': datetime.now().isoformat()
            },
            {
                'id': 'device2',
                'token': 'token2',
                'platform': 'ios',
                'app_version': '1.0.0',
                'last_used_at': datetime.now().isoformat()
            }
        ]
        
        with patch.object(service, 'get_user_devices', new_callable=AsyncMock, return_value=mock_devices), \
             patch.object(service, '_send_to_fcm', new_callable=AsyncMock, return_value=True), \
             patch.object(service, '_send_to_apns', new_callable=AsyncMock, return_value=False), \
             patch.object(service, '_log_notification', new_callable=AsyncMock):
            
            result = await service.send_notification(
                user_id='user123',
                title='Test Notification',
                body='This is a test'
            )
            
            assert result['total_devices'] == 2
            assert result['sent'] == 1
            assert result['failed'] == 1


@pytest.mark.asyncio
@pytest.mark.django_db
class TestFCMIntegration:
    """Test cases for FCM integration."""
    
    async def test_send_to_fcm_success(self):
        """Test successful FCM notification."""
        service = PushNotificationService()
        service.fcm_server_key = 'test_key'
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'success': 1}
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            result = await service._send_to_fcm(
                token='fcm_token',
                payload={'title': 'Test', 'body': 'Message'}
            )
            
            assert result is True
    
    async def test_send_to_fcm_invalid_token(self):
        """Test FCM with invalid token."""
        service = PushNotificationService()
        service.fcm_server_key = 'test_key'
        from apps.notifications.push_service import InvalidTokenException
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'success': 0,
            'results': [{'error': 'InvalidRegistration'}]
        }
        
        with patch('httpx.AsyncClient') as mock_client, \
             patch.object(service, '_handle_invalid_token', new_callable=AsyncMock) as mock_handle:
            
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            with pytest.raises(InvalidTokenException):
                await service._send_to_fcm(
                    token='invalid_token',
                    payload={'title': 'Test', 'body': 'Message'}
                )

            mock_handle.assert_called_once_with('invalid_token')
    
    async def test_send_to_fcm_no_server_key(self):
        """Test FCM without server key configured."""
        service = PushNotificationService()
        service.fcm_server_key = None
        
        result = await service._send_to_fcm(
            token='fcm_token',
            payload={'title': 'Test', 'body': 'Message'}
        )
        
        assert result is False


@pytest.mark.asyncio
@pytest.mark.django_db
class TestAPNsIntegration:
    """Test cases for APNs integration."""
    
    async def test_send_to_apns_success(self):
        """Test successful APNs notification."""
        service = PushNotificationService()
        service.apns_key_id = 'key123'
        service.apns_team_id = 'team123'
        service.apns_bundle_id = 'com.example.app'
        
        mock_response = Mock()
        mock_response.status_code = 200
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            result = await service._send_to_apns(
                token='apns_token',
                payload={'title': 'Test', 'body': 'Message'}
            )
            
            assert result is True
    
    async def test_send_to_apns_invalid_token(self):
        """Test APNs with invalid token."""
        service = PushNotificationService()
        service.apns_key_id = 'key123'
        service.apns_team_id = 'team123'
        service.apns_bundle_id = 'com.example.app'
        from apps.notifications.push_service import InvalidTokenException
        
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = 'BadDeviceToken'
        
        with patch('httpx.AsyncClient') as mock_client, \
             patch.object(service, '_handle_invalid_token', new_callable=AsyncMock) as mock_handle:
            
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            with pytest.raises(InvalidTokenException):
                await service._send_to_apns(
                    token='invalid_token',
                    payload={'title': 'Test', 'body': 'Message'}
                )

            mock_handle.assert_called_once_with('invalid_token')
    
    async def test_send_to_apns_incomplete_config(self):
        """Test APNs without complete configuration."""
        service = PushNotificationService()
        service.apns_key_id = None
        service.apns_team_id = None
        service.apns_bundle_id = None
        
        result = await service._send_to_apns(
            token='apns_token',
            payload={'title': 'Test', 'body': 'Message'}
        )
        
        assert result is False


@pytest.mark.asyncio
@pytest.mark.django_db
class TestNotificationLogging:
    """Test cases for notification logging."""
    
    async def test_log_notification_success(self):
        """Test logging successful notification."""
        service = PushNotificationService()
        
        with patch.object(service, '_ensure_connected', new_callable=AsyncMock), \
             patch('prisma.actions.PushNotificationLogActions.create', new_callable=AsyncMock) as mock_create:
            
            await service._log_notification(
                device_token_id='device123',
                payload={'title': 'Test', 'body': 'Message'},
                status='sent',
                notification_id='notif123'
            )
            
            mock_create.assert_called_once()
            call_args = mock_create.call_args[1]['data']
            assert call_args['device_token_id'] == 'device123'
            assert call_args['status'] == 'sent'
            assert call_args['notification_id'] == 'notif123'
    
    async def test_log_notification_failure(self):
        """Test logging failed notification."""
        service = PushNotificationService()
        
        with patch.object(service, '_ensure_connected', new_callable=AsyncMock), \
             patch('prisma.actions.PushNotificationLogActions.create', new_callable=AsyncMock) as mock_create:
            
            await service._log_notification(
                device_token_id='device123',
                payload={'title': 'Test', 'body': 'Message'},
                status='failed',
                error_message='Connection timeout'
            )
            
            mock_create.assert_called_once()
            call_args = mock_create.call_args[1]['data']
            assert call_args['status'] == 'failed'
            assert call_args['error_message'] == 'Connection timeout'



@pytest.mark.asyncio
@pytest.mark.django_db
class TestRetryLogic:
    """Test cases for notification retry logic with exponential backoff."""
    
    async def test_send_with_retry_success_first_attempt(self):
        """Test successful send on first attempt (no retry needed)."""
        service = PushNotificationService()
        
        with patch.object(service, '_send_to_fcm', new_callable=AsyncMock, return_value=True):
            
            result = await service._send_with_retry(
                token='fcm_token',
                platform='android',
                payload={'title': 'Test', 'body': 'Message'},
                device_id='device123'
            )
            
            assert result is True
            # Should only call once, no retries
            service._send_to_fcm.assert_called_once()
    
    async def test_send_with_retry_success_after_failures(self):
        """Test successful send after initial failures with exponential backoff."""
        service = PushNotificationService()
        
        # Fail twice, then succeed
        with patch.object(service, '_send_to_fcm', new_callable=AsyncMock) as mock_send, \
             patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            
            mock_send.side_effect = [False, False, True]
            
            result = await service._send_with_retry(
                token='fcm_token',
                platform='android',
                payload={'title': 'Test', 'body': 'Message'},
                device_id='device123'
            )
            
            assert result is True
            assert mock_send.call_count == 3
            
            # Verify exponential backoff delays
            assert mock_sleep.call_count == 2
            mock_sleep.assert_any_call(1)  # First retry delay
            mock_sleep.assert_any_call(2)  # Second retry delay
    
    async def test_send_with_retry_all_attempts_fail(self):
        """Test all retry attempts fail."""
        service = PushNotificationService()
        
        with patch.object(service, '_send_to_fcm', new_callable=AsyncMock, return_value=False), \
             patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            
            result = await service._send_with_retry(
                token='fcm_token',
                platform='android',
                payload={'title': 'Test', 'body': 'Message'},
                device_id='device123'
            )
            
            assert result is False
            assert service._send_to_fcm.call_count == 5  # max_retries
            
            # Verify exponential backoff delays (4 delays for 5 attempts)
            assert mock_sleep.call_count == 4
            mock_sleep.assert_any_call(1)
            mock_sleep.assert_any_call(2)
            mock_sleep.assert_any_call(4)
            mock_sleep.assert_any_call(8)
    
    async def test_send_with_retry_stops_on_invalid_token(self):
        """Test retry stops when token is marked as invalid."""
        service = PushNotificationService()
        
        from apps.notifications.push_service import InvalidTokenException
        
        with patch.object(service, '_send_to_fcm', new_callable=AsyncMock) as mock_send, \
             patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            
            # First attempt raises InvalidTokenException
            mock_send.side_effect = InvalidTokenException("Token is invalid")
            
            result = await service._send_with_retry(
                token='fcm_token',
                platform='android',
                payload={'title': 'Test', 'body': 'Message'},
                device_id='device123'
            )
            
            assert result is False
            # Should only attempt once before stopping
            assert mock_send.call_count == 1
            # Should not sleep/retry
            assert mock_sleep.call_count == 0
    
    async def test_send_with_retry_exponential_backoff_delays(self):
        """Test that exponential backoff uses correct delay sequence."""
        service = PushNotificationService()
        
        with patch.object(service, '_send_to_apns', new_callable=AsyncMock, return_value=False), \
             patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            
            await service._send_with_retry(
                token='apns_token',
                platform='ios',
                payload={'title': 'Test', 'body': 'Message'},
                device_id='device123'
            )
            
            # Verify the exact sequence of delays: 1, 2, 4, 8
            expected_delays = [1, 2, 4, 8]
            actual_delays = [call[0][0] for call in mock_sleep.call_args_list]
            assert actual_delays == expected_delays
    
    async def test_send_with_retry_network_error_triggers_retry(self):
        """Test that network errors trigger retry with exponential backoff."""
        service = PushNotificationService()
        
        with patch.object(service, '_send_to_fcm', new_callable=AsyncMock) as mock_send, \
             patch.object(service, '_ensure_connected', new_callable=AsyncMock), \
             patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            
            # Raise network error twice, then succeed
            mock_send.side_effect = [
                Exception("Network error"),
                Exception("Timeout"),
                True
            ]
            
            result = await service._send_with_retry(
                token='fcm_token',
                platform='android',
                payload={'title': 'Test', 'body': 'Message'},
                device_id='device123'
            )
            
            assert result is True
            assert mock_send.call_count == 3
            assert mock_sleep.call_count == 2


@pytest.mark.asyncio
@pytest.mark.django_db
class TestInvalidTokenHandling:
    """Test cases for invalid token handling."""
    
    async def test_fcm_invalid_registration_triggers_invalid_token_handler(self):
        """Test that FCM InvalidRegistration error triggers invalid token handler."""
        service = PushNotificationService()
        service.fcm_server_key = 'test_key'
        
        from apps.notifications.push_service import InvalidTokenException
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'success': 0,
            'results': [{'error': 'InvalidRegistration'}]
        }
        
        with patch('httpx.AsyncClient') as mock_client, \
             patch.object(service, '_handle_invalid_token', new_callable=AsyncMock) as mock_handle:
            
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            with pytest.raises(InvalidTokenException):
                await service._send_to_fcm('invalid_token', {'title': 'Test', 'body': 'Message'})
            
            mock_handle.assert_called_once_with('invalid_token')
    
    async def test_apns_bad_device_token_triggers_invalid_token_handler(self):
        """Test that APNs 400/410 status triggers invalid token handler."""
        service = PushNotificationService()
        service.apns_key_id = 'key123'
        service.apns_team_id = 'team123'
        service.apns_bundle_id = 'com.example.app'
        
        from apps.notifications.push_service import InvalidTokenException
        
        mock_response = Mock()
        mock_response.status_code = 410
        mock_response.text = 'Unregistered'
        
        with patch('httpx.AsyncClient') as mock_client, \
             patch.object(service, '_handle_invalid_token', new_callable=AsyncMock) as mock_handle:
            
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            with pytest.raises(InvalidTokenException):
                await service._send_to_apns('invalid_token', {'title': 'Test', 'body': 'Message'})
            
            mock_handle.assert_called_once_with('invalid_token')


@pytest.mark.asyncio
@pytest.mark.django_db
class TestDeliveryStatusTracking:
    """Test cases for delivery status tracking."""
    
    async def test_notification_log_tracks_sent_status(self):
        """Test that successful notifications are logged with 'sent' status."""
        service = PushNotificationService()
        
        mock_device = {
            'id': 'device1',
            'token': 'fcm_token',
            'platform': 'android',
            'app_version': '1.0.0',
            'last_used_at': datetime.now().isoformat()
        }
        
        with patch.object(service, 'get_user_devices', new_callable=AsyncMock, return_value=[mock_device]), \
             patch.object(service, '_send_with_retry', new_callable=AsyncMock, return_value=True), \
             patch.object(service, '_log_notification', new_callable=AsyncMock) as mock_log:
            
            await service.send_notification(
                user_id='user123',
                title='Test',
                body='Message'
            )
            
            # Verify notification was logged with 'sent' status
            mock_log.assert_called_once()
            log_call = mock_log.call_args
            assert log_call[1]['status'] == 'sent'
            assert log_call[1]['device_token_id'] == 'device1'
    
    async def test_notification_log_tracks_failed_status(self):
        """Test that failed notifications are logged with 'failed' status."""
        service = PushNotificationService()
        
        mock_device = {
            'id': 'device1',
            'token': 'fcm_token',
            'platform': 'android',
            'app_version': '1.0.0',
            'last_used_at': datetime.now().isoformat()
        }
        
        with patch.object(service, 'get_user_devices', new_callable=AsyncMock, return_value=[mock_device]), \
             patch.object(service, '_send_with_retry', new_callable=AsyncMock, return_value=False), \
             patch.object(service, '_log_notification', new_callable=AsyncMock) as mock_log:
            
            await service.send_notification(
                user_id='user123',
                title='Test',
                body='Message'
            )
            
            # Verify notification was logged with 'failed' status
            mock_log.assert_called_once()
            log_call = mock_log.call_args
            assert log_call[1]['status'] == 'failed'
    
    async def test_notification_log_includes_error_message(self):
        """Test that failed notifications include error message in log."""
        service = PushNotificationService()
        
        mock_device = {
            'id': 'device1',
            'token': 'fcm_token',
            'platform': 'android',
            'app_version': '1.0.0',
            'last_used_at': datetime.now().isoformat()
        }
        
        with patch.object(service, 'get_user_devices', new_callable=AsyncMock, return_value=[mock_device]), \
             patch.object(service, '_send_with_retry', new_callable=AsyncMock, side_effect=Exception("Network timeout")), \
             patch.object(service, '_log_notification', new_callable=AsyncMock) as mock_log:
            
            await service.send_notification(
                user_id='user123',
                title='Test',
                body='Message'
            )
            
            # Verify error message was logged
            mock_log.assert_called_once()
            log_call = mock_log.call_args
            assert log_call[1]['status'] == 'failed'
            assert 'Network timeout' in log_call[1]['error_message']
    
    async def test_send_notification_returns_delivery_summary(self):
        """Test that send_notification returns comprehensive delivery summary."""
        service = PushNotificationService()
        
        mock_devices = [
            {
                'id': 'device1',
                'token': 'token1',
                'platform': 'android',
                'app_version': '1.0.0',
                'last_used_at': datetime.now().isoformat()
            },
            {
                'id': 'device2',
                'token': 'token2',
                'platform': 'ios',
                'app_version': '1.0.0',
                'last_used_at': datetime.now().isoformat()
            },
            {
                'id': 'device3',
                'token': 'token3',
                'platform': 'android',
                'app_version': '1.0.0',
                'last_used_at': datetime.now().isoformat()
            }
        ]
        
        with patch.object(service, 'get_user_devices', new_callable=AsyncMock, return_value=mock_devices), \
             patch.object(service, '_send_with_retry', new_callable=AsyncMock) as mock_send, \
             patch.object(service, '_log_notification', new_callable=AsyncMock):
            
            # First succeeds, second fails, third succeeds
            mock_send.side_effect = [True, False, True]
            
            result = await service.send_notification(
                user_id='user123',
                title='Test',
                body='Message'
            )
            
            # Verify delivery summary
            assert result['user_id'] == 'user123'
            assert result['total_devices'] == 3
            assert result['sent'] == 2
            assert result['failed'] == 1
            assert len(result['results']) == 3
            
            # Verify individual results
            assert result['results'][0]['status'] == 'sent'
            assert result['results'][1]['status'] == 'failed'
            assert result['results'][2]['status'] == 'sent'
