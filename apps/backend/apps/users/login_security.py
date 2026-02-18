"""
Login Security Monitor Service

This service detects suspicious login patterns and sends security alerts.
Implements requirements 6.13, 6.14, 6.15 from the production-readiness spec.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from prisma import Prisma
from prisma.enums import AuthEventType
import httpx

logger = logging.getLogger(__name__)


class LoginSecurityMonitor:
    """
    Monitors login activity for suspicious patterns and sends security alerts.
    
    Features:
    - Detects logins from new locations (IP addresses)
    - Detects unusual access times based on user's typical login patterns
    - Sends email alerts for suspicious activity
    - Logs all authentication events
    """
    
    def __init__(self):
        self.db = Prisma()
    
    async def check_login(self, user_id: str, request) -> Dict[str, Any]:
        """
        Check login for suspicious patterns and log the event.
        
        Args:
            user_id: The user's ID
            request: Django request object
            
        Returns:
            Dict with suspicious activity flags and details
        """
        ip_address = self._get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Initialize result
        result = {
            'is_suspicious': False,
            'reasons': [],
            'ip_address': ip_address
        }
        
        # Check for new location
        is_new_location = await self._is_new_location(user_id, ip_address)
        if is_new_location:
            result['is_suspicious'] = True
            result['reasons'].append('new_location')
            await self._send_security_alert(
                user_id, 
                'new_location', 
                {'ip_address': ip_address}
            )
        
        # Check for unusual time
        is_unusual_time = await self._is_unusual_time(user_id)
        if is_unusual_time:
            result['is_suspicious'] = True
            result['reasons'].append('unusual_time')
            await self._send_security_alert(
                user_id,
                'unusual_time',
                {'time': timezone.now().isoformat()}
            )
        
        # Log authentication event
        await self._log_auth_event(
            user_id=user_id,
            event_type=AuthEventType.LOGIN_SUCCESS,
            ip_address=ip_address,
            user_agent=user_agent,
            success=True,
            metadata={
                'suspicious': result['is_suspicious'],
                'reasons': result['reasons']
            }
        )
        
        return result
    
    async def log_failed_login(self, email: str, request) -> None:
        """
        Log a failed login attempt.
        
        Args:
            email: Email address used in failed login
            request: Django request object
        """
        ip_address = self._get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        await self._log_auth_event(
            user_id=None,
            event_type=AuthEventType.LOGIN_FAILED,
            ip_address=ip_address,
            user_agent=user_agent,
            success=False,
            metadata={'email': email}
        )
    
    async def log_logout(self, user_id: str, request) -> None:
        """
        Log a logout event.
        
        Args:
            user_id: The user's ID
            request: Django request object
        """
        ip_address = self._get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        await self._log_auth_event(
            user_id=user_id,
            event_type=AuthEventType.LOGOUT,
            ip_address=ip_address,
            user_agent=user_agent,
            success=True
        )
    
    async def _is_new_location(self, user_id: str, ip_address: str) -> bool:
        """
        Check if the IP address is new for this user.
        
        Args:
            user_id: The user's ID
            ip_address: IP address to check
            
        Returns:
            True if this is a new location, False otherwise
        """
        try:
            await self.db.connect()
            
            # Check if user has logged in from this IP before
            previous_login = await self.db.authenticationevent.find_first(
                where={
                    'user_id': user_id,
                    'ip_address': ip_address,
                    'event_type': AuthEventType.LOGIN_SUCCESS,
                    'success': True
                }
            )
            
            return previous_login is None
            
        except Exception as e:
            logger.error(f"Error checking new location: {e}")
            return False
        finally:
            await self.db.disconnect()
    
    async def _is_unusual_time(self, user_id: str) -> bool:
        """
        Check if the current login time is unusual for this user.
        
        Analyzes the user's login history to determine typical login hours.
        A login is considered unusual if it's outside the user's typical pattern.
        
        Args:
            user_id: The user's ID
            
        Returns:
            True if this is an unusual time, False otherwise
        """
        try:
            await self.db.connect()
            
            # Get user's login history from the last 30 days
            thirty_days_ago = timezone.now() - timedelta(days=30)
            
            login_history = await self.db.authenticationevent.find_many(
                where={
                    'user_id': user_id,
                    'event_type': AuthEventType.LOGIN_SUCCESS,
                    'success': True,
                    'created_at': {
                        'gte': thirty_days_ago
                    }
                },
                order={'created_at': 'desc'},
                take=50  # Analyze last 50 logins
            )
            
            # Need at least 5 previous logins to establish a pattern
            if len(login_history) < 5:
                return False
            
            # Extract hours from login history
            login_hours = [event.created_at.hour for event in login_history]
            
            # Calculate average and standard deviation
            avg_hour = sum(login_hours) / len(login_hours)
            variance = sum((h - avg_hour) ** 2 for h in login_hours) / len(login_hours)
            std_dev = variance ** 0.5
            
            # Current hour
            current_hour = timezone.now().hour
            
            # Consider unusual if more than 2 standard deviations from average
            # or if std_dev is very small (consistent pattern) and current hour differs significantly
            if std_dev < 2:
                # Very consistent pattern - flag if more than 3 hours different
                return abs(current_hour - avg_hour) > 3
            else:
                # More variable pattern - use 2 standard deviations
                return abs(current_hour - avg_hour) > (2 * std_dev)
            
        except Exception as e:
            logger.error(f"Error checking unusual time: {e}")
            return False
        finally:
            await self.db.disconnect()
    
    async def _send_security_alert(
        self, 
        user_id: str, 
        alert_type: str, 
        context: Dict[str, Any]
    ) -> None:
        """
        Send a security alert email to the user.
        
        Args:
            user_id: The user's ID
            alert_type: Type of alert ('new_location' or 'unusual_time')
            context: Additional context for the alert
        """
        try:
            await self.db.connect()
            
            # Get user profile to get email from Clerk
            user_profile = await self.db.userprofile.find_unique(
                where={'id': user_id}
            )
            
            if not user_profile:
                logger.error(f"User profile not found for user_id: {user_id}")
                return
            
            # Prepare email content based on alert type
            if alert_type == 'new_location':
                subject = "New Login Location Detected - MueJam Library"
                message = f"""
Hello,

We detected a login to your MueJam Library account from a new location:

IP Address: {context.get('ip_address', 'Unknown')}
Time: {timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

If this was you, you can safely ignore this email. If you don't recognize this activity, 
please secure your account immediately by changing your password.

Best regards,
MueJam Library Security Team
"""
            elif alert_type == 'unusual_time':
                subject = "Unusual Login Time Detected - MueJam Library"
                message = f"""
Hello,

We detected a login to your MueJam Library account at an unusual time:

Time: {context.get('time', timezone.now().isoformat())}

This login occurred outside your typical usage pattern. If this was you, you can safely 
ignore this email. If you don't recognize this activity, please secure your account 
immediately by changing your password.

Best regards,
MueJam Library Security Team
"""
            else:
                logger.warning(f"Unknown alert type: {alert_type}")
                return
            
            # For now, we'll use Django's send_mail
            # In production, this should use Resend or another email service
            # Note: We need to get the actual email from Clerk
            # For now, we'll log the alert
            logger.info(
                f"Security alert for user {user_id}: {alert_type}",
                extra={'context': context}
            )
            
            # TODO: Integrate with Resend email service
            # send_mail(
            #     subject=subject,
            #     message=message,
            #     from_email=settings.DEFAULT_FROM_EMAIL,
            #     recipient_list=[user_email],
            #     fail_silently=False,
            # )
            
        except Exception as e:
            logger.error(f"Error sending security alert: {e}")
        finally:
            await self.db.disconnect()
    
    async def _log_auth_event(
        self,
        user_id: Optional[str],
        event_type: AuthEventType,
        ip_address: str,
        user_agent: str,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log an authentication event to the database.
        
        Args:
            user_id: The user's ID (None for failed logins)
            event_type: Type of authentication event
            ip_address: IP address of the request
            user_agent: User agent string
            success: Whether the authentication was successful
            metadata: Additional metadata to store
        """
        try:
            await self.db.connect()
            
            # Get location from IP (optional, can be enhanced with IP geolocation service)
            location = await self._get_location_from_ip(ip_address)
            
            # Convert metadata to proper JSON format - always provide a dict
            import json
            metadata_json = json.dumps(metadata if metadata is not None else {})
            
            await self.db.authenticationevent.create(
                data={
                    'user_id': user_id,
                    'event_type': event_type,
                    'ip_address': ip_address,
                    'user_agent': user_agent,
                    'location': location,
                    'success': success,
                    'metadata': metadata_json
                }
            )
            
            logger.info(
                f"Logged auth event: {event_type} for user {user_id}",
                extra={
                    'user_id': user_id,
                    'event_type': event_type,
                    'ip_address': ip_address,
                    'success': success
                }
            )
            
        except Exception as e:
            logger.error(f"Error logging auth event: {e}")
        finally:
            await self.db.disconnect()
    
    def _get_client_ip(self, request) -> str:
        """
        Extract the client IP address from the request.
        
        Args:
            request: Django request object
            
        Returns:
            IP address as string
        """
        # Check for X-Forwarded-For header (common in load balancers)
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # Take the first IP in the chain
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        
        return ip
    
    async def _get_location_from_ip(self, ip_address: str) -> Optional[str]:
        """
        Get approximate location from IP address.
        
        This is a placeholder for IP geolocation service integration.
        In production, you would use a service like MaxMind GeoIP2 or ipapi.
        
        Args:
            ip_address: IP address to lookup
            
        Returns:
            Location string (e.g., "New York, US") or None
        """
        # Skip for localhost/private IPs
        if ip_address in ['127.0.0.1', 'localhost'] or ip_address.startswith('192.168.'):
            return 'Local'
        
        try:
            # Using a free IP geolocation API (ipapi.co)
            # In production, consider using a paid service for better reliability
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f'https://ipapi.co/{ip_address}/json/')
                if response.status_code == 200:
                    data = response.json()
                    city = data.get('city', '')
                    country = data.get('country_name', '')
                    if city and country:
                        return f"{city}, {country}"
                    elif country:
                        return country
        except Exception as e:
            logger.debug(f"Could not get location for IP {ip_address}: {e}")
        
        return None


# Singleton instance
login_security_monitor = LoginSecurityMonitor()
