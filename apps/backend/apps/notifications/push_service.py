"""
Push Notification Service for Mobile Backend Integration

This service manages push notifications to mobile devices using:
- Firebase Cloud Messaging (FCM) for Android
- Apple Push Notification service (APNs) for iOS

Implements Requirements 4.1, 4.2, 5.1, 5.2 from mobile-backend-integration spec.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

import httpx
from django.conf import settings

from prisma import Prisma
from apps.analytics.mobile_analytics_service import get_mobile_analytics_service

logger = logging.getLogger(__name__)


class InvalidTokenException(Exception):
    """Exception raised when a device token is invalid."""
    pass


class PushNotificationService:
    """
    Service for managing push notifications to mobile devices.
    
    Integrates with FCM (Android) and APNs (iOS) for notification delivery.
    """
    
    def __init__(self):
        """Initialize push notification service with FCM and APNs clients."""
        self.prisma = Prisma()
        self.fcm_server_key = getattr(settings, 'FCM_SERVER_KEY', None)
        self.fcm_url = 'https://fcm.googleapis.com/fcm/send'
        
        # APNs configuration
        self.apns_key_id = getattr(settings, 'APNS_KEY_ID', None)
        self.apns_team_id = getattr(settings, 'APNS_TEAM_ID', None)
        self.apns_bundle_id = getattr(settings, 'APNS_BUNDLE_ID', None)
        self.apns_key_path = getattr(settings, 'APNS_KEY_PATH', None)
        self.apns_use_sandbox = getattr(settings, 'APNS_USE_SANDBOX', True)
        
        # APNs endpoint
        if self.apns_use_sandbox:
            self.apns_url = 'https://api.sandbox.push.apple.com'
        else:
            self.apns_url = 'https://api.push.apple.com'
        
        # Retry configuration
        self.max_retries = 5
        self.retry_delays = [1, 2, 4, 8, 16]  # Exponential backoff in seconds
        
        # Analytics service
        self.analytics_service = get_mobile_analytics_service()
    
    async def _ensure_connected(self):
        """Ensure Prisma client is connected."""
        if not self.prisma.is_connected():
            await self.prisma.connect()
    
    async def register_device(
        self,
        user_id: str,
        token: str,
        platform: str,
        app_version: Optional[str] = None
    ) -> Dict:
        """
        Register a device token for push notifications.
        
        Args:
            user_id: User ID
            token: Device token from FCM/APNs
            platform: 'ios' or 'android'
            app_version: Optional app version string
            
        Returns:
            Device token record
            
        Raises:
            ValueError: If platform is not 'ios' or 'android'
        """
        if platform not in ['ios', 'android']:
            raise ValueError(f"Invalid platform: {platform}. Must be 'ios' or 'android'")
        
        await self._ensure_connected()
        
        try:
            # Check if token already exists
            existing_token = await self.prisma.devicetoken.find_unique(
                where={'token': token}
            )
            
            if existing_token:
                # Update existing token
                device_token = await self.prisma.devicetoken.update(
                    where={'token': token},
                    data={
                        'user_id': user_id,
                        'platform': platform,
                        'app_version': app_version,
                        'is_active': True,
                        'last_used_at': datetime.now()
                    }
                )
                logger.info(f"Updated device token for user {user_id}, platform {platform}")
            else:
                # Create new token
                device_token = await self.prisma.devicetoken.create(
                    data={
                        'user_id': user_id,
                        'token': token,
                        'platform': platform,
                        'app_version': app_version,
                        'is_active': True,
                        'last_used_at': datetime.now()
                    }
                )
                logger.info(f"Registered new device token for user {user_id}, platform {platform}")
            
            return {
                'id': device_token.id,
                'user_id': device_token.user_id,
                'platform': device_token.platform,
                'app_version': device_token.app_version,
                'is_active': device_token.is_active,
                'created_at': device_token.created_at.isoformat(),
                'last_used_at': device_token.last_used_at.isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error registering device token: {str(e)}")
            raise
    
    async def unregister_device(self, token: str) -> bool:
        """
        Unregister a device token.
        
        Args:
            token: Device token to unregister
            
        Returns:
            True if successful
        """
        await self._ensure_connected()
        
        try:
            device_token = await self.prisma.devicetoken.find_unique(
                where={'token': token}
            )
            
            if device_token:
                await self.prisma.devicetoken.update(
                    where={'token': token},
                    data={'is_active': False}
                )
                logger.info(f"Unregistered device token: {token[:20]}...")
                return True
            else:
                logger.warning(f"Device token not found: {token[:20]}...")
                return False
        
        except Exception as e:
            logger.error(f"Error unregistering device token: {str(e)}")
            raise
    
    async def get_user_devices(self, user_id: str) -> List[Dict]:
        """
        Get all active device tokens for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of device token records
        """
        await self._ensure_connected()
        
        try:
            devices = await self.prisma.devicetoken.find_many(
                where={
                    'user_id': user_id,
                    'is_active': True
                }
            )
            
            return [
                {
                    'id': device.id,
                    'token': device.token,
                    'platform': device.platform,
                    'app_version': device.app_version,
                    'last_used_at': device.last_used_at.isoformat()
                }
                for device in devices
            ]
        
        except Exception as e:
            logger.error(f"Error getting user devices: {str(e)}")
            raise
    
    async def send_notification(
        self,
        user_id: str,
        title: str,
        body: str,
        data: Optional[Dict] = None
    ) -> Dict:
        """
        Send push notification to all user's devices.
        
        Args:
            user_id: User ID to send notification to
            title: Notification title
            body: Notification body text
            data: Optional additional data payload
            
        Returns:
            Delivery status summary
        """
        await self._ensure_connected()
        
        # Get all active devices for user
        devices = await self.get_user_devices(user_id)
        
        if not devices:
            logger.warning(f"No active devices found for user {user_id}")
            return {
                'user_id': user_id,
                'total_devices': 0,
                'sent': 0,
                'failed': 0,
                'results': []
            }
        
        results = []
        sent_count = 0
        failed_count = 0
        
        # Send to each device
        for device in devices:
            platform = device['platform']
            token = device['token']
            
            payload = {
                'title': title,
                'body': body,
                'data': data or {}
            }
            
            try:
                # Send with retry logic
                success = await self._send_with_retry(token, platform, payload, device['id'])
                
                if success:
                    sent_count += 1
                    status = 'sent'
                else:
                    failed_count += 1
                    status = 'failed'
                
                # Log the notification
                await self._log_notification(
                    device_token_id=device['id'],
                    payload=payload,
                    status=status
                )
                
                # Track notification delivery in analytics
                self.analytics_service.track_notification_delivery(
                    status=status,
                    platform=platform,
                    user_id=user_id
                )
                
                results.append({
                    'device_id': device['id'],
                    'platform': platform,
                    'status': status
                })
            
            except Exception as e:
                logger.error(f"Error sending notification to device {device['id']}: {str(e)}")
                failed_count += 1
                
                await self._log_notification(
                    device_token_id=device['id'],
                    payload=payload,
                    status='failed',
                    error_message=str(e)
                )
                
                # Track notification failure in analytics
                self.analytics_service.track_notification_delivery(
                    status='failed',
                    platform=platform,
                    user_id=user_id
                )
                
                results.append({
                    'device_id': device['id'],
                    'platform': platform,
                    'status': 'failed',
                    'error': str(e)
                })
        
        return {
            'user_id': user_id,
            'total_devices': len(devices),
            'sent': sent_count,
            'failed': failed_count,
            'results': results
        }
    
    async def _send_with_retry(
        self,
        token: str,
        platform: str,
        payload: Dict,
        device_id: str
    ) -> bool:
        """
        Send notification with exponential backoff retry logic.
        
        Args:
            token: Device token
            platform: Platform ('ios' or 'android')
            payload: Notification payload
            device_id: Device ID for logging
            
        Returns:
            True if successful, False otherwise
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                if platform == 'android':
                    success = await self._send_to_fcm(token, payload)
                elif platform == 'ios':
                    success = await self._send_to_apns(token, payload)
                else:
                    logger.error(f"Unknown platform: {platform}")
                    return False
                
                if success:
                    if attempt > 0:
                        logger.info(f"Notification sent successfully on attempt {attempt + 1}")
                    return True
                
                # If not the last attempt, wait before retrying
                if attempt < self.max_retries - 1:
                    delay = self.retry_delays[attempt]
                    logger.warning(
                        f"Notification delivery failed (attempt {attempt + 1}/{self.max_retries}), "
                        f"retrying in {delay}s"
                    )
                    await asyncio.sleep(delay)
            
            except InvalidTokenException as e:
                # Token is invalid, don't retry
                logger.info(f"Token is invalid, stopping retries: {str(e)}")
                
                # Track invalid token in analytics
                await self._track_invalid_token_analytics(device_id)
                
                return False
                
            except Exception as e:
                last_error = str(e)
                logger.error(f"Error on attempt {attempt + 1}: {str(e)}")
                
                # If not the last attempt, wait before retrying
                if attempt < self.max_retries - 1:
                    delay = self.retry_delays[attempt]
                    logger.warning(f"Retrying in {delay}s after error")
                    await asyncio.sleep(delay)
        
        logger.error(
            f"Failed to send notification after {self.max_retries} attempts. "
            f"Last error: {last_error}"
        )
        return False
    
    async def _send_to_fcm(self, token: str, payload: Dict) -> bool:
        """
        Send notification via Firebase Cloud Messaging.
        
        Args:
            token: FCM device token
            payload: Notification payload
            
        Returns:
            True if successful, False otherwise
        """
        if not self.fcm_server_key:
            logger.error("FCM_SERVER_KEY not configured")
            return False
        
        headers = {
            'Authorization': f'Bearer {self.fcm_server_key}',
            'Content-Type': 'application/json'
        }
        
        fcm_payload = {
            'to': token,
            'notification': {
                'title': payload['title'],
                'body': payload['body']
            },
            'data': payload.get('data', {})
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.fcm_url,
                    headers=headers,
                    json=fcm_payload,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success') == 1:
                        logger.info(f"FCM notification sent successfully")
                        return True
                    else:
                        error = result.get('results', [{}])[0].get('error', 'Unknown error')
                        logger.error(f"FCM notification failed: {error}")
                        
                        # Handle invalid token - mark as inactive and don't retry
                        if error in ['InvalidRegistration', 'NotRegistered', 'MismatchSenderId']:
                            logger.warning(f"Invalid FCM token detected: {error}")
                            await self._handle_invalid_token(token)
                            raise InvalidTokenException(f"FCM token is invalid: {error}")
                        
                        return False
                else:
                    logger.error(f"FCM request failed with status {response.status_code}")
                    return False
        
        except httpx.TimeoutException as e:
            logger.error(f"FCM request timeout: {str(e)}")
            raise  # Re-raise to trigger retry
        except httpx.NetworkError as e:
            logger.error(f"FCM network error: {str(e)}")
            raise  # Re-raise to trigger retry
        except InvalidTokenException:
            # Re-raise to stop retries
            raise
        except Exception as e:
            logger.error(f"Error sending FCM notification: {str(e)}")
            return False
    
    async def _send_to_apns(self, token: str, payload: Dict) -> bool:
        """
        Send notification via Apple Push Notification service.
        
        Args:
            token: APNs device token
            payload: Notification payload
            
        Returns:
            True if successful, False otherwise
        """
        if not all([self.apns_key_id, self.apns_team_id, self.apns_bundle_id]):
            logger.error("APNs configuration incomplete")
            return False
        
        # APNs payload format
        apns_payload = {
            'aps': {
                'alert': {
                    'title': payload['title'],
                    'body': payload['body']
                },
                'sound': 'default'
            }
        }
        
        # Add custom data
        if payload.get('data'):
            apns_payload.update(payload['data'])
        
        headers = {
            'apns-topic': self.apns_bundle_id,
            'apns-push-type': 'alert',
            'apns-priority': '10'
        }
        
        # Note: In production, you would need to implement JWT authentication
        # for APNs using the key file. For now, this is a simplified version.
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f'{self.apns_url}/3/device/{token}',
                    headers=headers,
                    json=apns_payload,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    logger.info(f"APNs notification sent successfully")
                    return True
                else:
                    logger.error(f"APNs request failed with status {response.status_code}: {response.text}")
                    
                    # Handle invalid token - mark as inactive and don't retry
                    # 400: Bad request (invalid token format)
                    # 410: Token no longer active
                    if response.status_code in [400, 410]:
                        logger.warning(f"Invalid APNs token detected: status {response.status_code}")
                        await self._handle_invalid_token(token)
                        raise InvalidTokenException(f"APNs token is invalid: status {response.status_code}")
                    
                    return False
        
        except httpx.TimeoutException as e:
            logger.error(f"APNs request timeout: {str(e)}")
            raise  # Re-raise to trigger retry
        except httpx.NetworkError as e:
            logger.error(f"APNs network error: {str(e)}")
            raise  # Re-raise to trigger retry
        except InvalidTokenException:
            # Re-raise to stop retries
            raise
        except Exception as e:
            logger.error(f"Error sending APNs notification: {str(e)}")
            return False
    
    async def _handle_invalid_token(self, token: str):
        """
        Mark device token as inactive when delivery fails due to invalid token.
        
        Args:
            token: Device token to mark as inactive
        """
        try:
            await self._ensure_connected()
            
            # Find the device token
            device_token = await self.prisma.devicetoken.find_unique(
                where={'token': token}
            )
            
            if device_token and device_token.is_active:
                # Mark as inactive
                await self.prisma.devicetoken.update(
                    where={'token': token},
                    data={'is_active': False}
                )
                logger.info(f"Marked invalid token as inactive: {token[:20]}...")
                
                # Log the invalid token event
                await self._log_notification(
                    device_token_id=device_token.id,
                    payload={'reason': 'invalid_token'},
                    status='invalid_token',
                    error_message='Token marked as invalid by push service'
                )
                
                # Track in analytics
                self.analytics_service.track_notification_delivery(
                    status='invalid_token',
                    platform=device_token.platform,
                    user_id=device_token.user_id
                )
            else:
                logger.warning(f"Token not found or already inactive: {token[:20]}...")
                
        except Exception as e:
            logger.error(f"Error handling invalid token: {str(e)}")
    
    async def _track_invalid_token_analytics(self, device_id: str):
        """
        Track invalid token in analytics.
        
        Args:
            device_id: Device ID
        """
        try:
            await self._ensure_connected()
            
            # Get device info for analytics
            device = await self.prisma.devicetoken.find_unique(
                where={'id': device_id}
            )
            
            if device:
                self.analytics_service.track_notification_delivery(
                    status='invalid_token',
                    platform=device.platform,
                    user_id=device.user_id
                )
        except Exception as e:
            logger.error(f"Error tracking invalid token analytics: {str(e)}")
    
    async def _log_notification(
        self,
        device_token_id: str,
        payload: Dict,
        status: str,
        notification_id: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        """
        Log push notification delivery attempt.
        
        Args:
            device_token_id: Device token ID
            payload: Notification payload
            status: Delivery status ('sent', 'failed', 'invalid_token')
            notification_id: Optional notification ID
            error_message: Optional error message
        """
        try:
            await self.prisma.pushnotificationlog.create(
                data={
                    'device_token_id': device_token_id,
                    'notification_id': notification_id,
                    'payload': json.dumps(payload),
                    'status': status,
                    'error_message': error_message
                }
            )
        except Exception as e:
            logger.error(f"Error logging notification: {str(e)}")
    
    async def close(self):
        """Close Prisma connection."""
        if self.prisma.is_connected():
            await self.prisma.disconnect()
