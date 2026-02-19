"""
Mobile Security Middleware

Middleware for detecting and logging suspicious mobile traffic patterns.

Requirements: 11.3, 11.4
"""

import time
from typing import Optional
from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import logging

from apps.security.mobile_security_logger import MobileSecurityLogger

logger = logging.getLogger(__name__)


class MobileSecurityMiddleware(MiddlewareMixin):
    """
    Middleware for detecting and logging suspicious mobile traffic patterns.
    
    Detects:
    - Rapid request patterns (too many requests in short time)
    - Unusual endpoint access patterns
    - Suspicious user agent strings
    - Version mismatches
    
    Requirements: 11.3, 11.4
    """
    
    # Track request counts per IP/user for rate pattern detection
    _request_tracker = defaultdict(list)
    
    # Suspicious patterns thresholds
    RAPID_REQUEST_THRESHOLD = 50  # requests per minute
    RAPID_REQUEST_WINDOW = 60  # seconds
    
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """
        Process incoming request and detect suspicious patterns.
        
        Args:
            request: Django request object
            
        Returns:
            None to continue processing, or HttpResponse to short-circuit
        """
        # Only check mobile clients
        client_type = getattr(request, 'client_type', None)
        if not client_type or not client_type.startswith('mobile'):
            return None
        
        # Extract request metadata
        ip_address = self._get_client_ip(request)
        user_id = self._get_user_id(request)
        request_id = getattr(request, 'request_id', None)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        platform = 'mobile-ios' if 'ios' in client_type else 'mobile-android'
        
        # Check for rapid requests
        self._check_rapid_requests(
            ip_address=ip_address,
            user_id=user_id,
            platform=platform,
            request_id=request_id
        )
        
        # Check for suspicious user agent
        self._check_suspicious_user_agent(
            user_agent=user_agent,
            ip_address=ip_address,
            user_id=user_id,
            platform=platform,
            request_id=request_id
        )
        
        # Check for version anomalies
        app_version = request.META.get('HTTP_X_APP_VERSION')
        if app_version:
            self._check_version_anomaly(
                app_version=app_version,
                platform=platform,
                ip_address=ip_address,
                user_id=user_id,
                request_id=request_id
            )
        
        return None
    
    def _get_client_ip(self, request: HttpRequest) -> str:
        """Extract client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        return ip
    
    def _get_user_id(self, request: HttpRequest) -> Optional[str]:
        """Extract user ID from request if authenticated."""
        if hasattr(request, 'user') and request.user.is_authenticated:
            return str(request.user.id)
        return None
    
    def _check_rapid_requests(
        self,
        ip_address: str,
        user_id: Optional[str],
        platform: str,
        request_id: Optional[str]
    ):
        """
        Check for rapid request patterns.
        
        Args:
            ip_address: Client IP address
            user_id: User ID if authenticated
            platform: Mobile platform
            request_id: Request ID for tracing
        """
        # Use user_id if available, otherwise IP
        tracker_key = user_id or ip_address
        
        now = time.time()
        
        # Add current request timestamp
        self._request_tracker[tracker_key].append(now)
        
        # Remove old timestamps outside the window
        cutoff = now - self.RAPID_REQUEST_WINDOW
        self._request_tracker[tracker_key] = [
            ts for ts in self._request_tracker[tracker_key]
            if ts > cutoff
        ]
        
        # Check if threshold exceeded
        request_count = len(self._request_tracker[tracker_key])
        if request_count > self.RAPID_REQUEST_THRESHOLD:
            MobileSecurityLogger.log_suspicious_traffic_pattern(
                user_id=user_id,
                ip_address=ip_address,
                platform=platform,
                pattern_type='rapid_requests',
                pattern_details={
                    'request_count': request_count,
                    'time_window_seconds': self.RAPID_REQUEST_WINDOW,
                    'threshold': self.RAPID_REQUEST_THRESHOLD
                },
                request_id=request_id,
                severity='high'
            )
    
    def _check_suspicious_user_agent(
        self,
        user_agent: str,
        ip_address: str,
        user_id: Optional[str],
        platform: str,
        request_id: Optional[str]
    ):
        """
        Check for suspicious user agent strings.
        
        Args:
            user_agent: User agent string
            ip_address: Client IP address
            user_id: User ID if authenticated
            platform: Mobile platform
            request_id: Request ID for tracing
        """
        suspicious_patterns = [
            'curl',
            'wget',
            'python',
            'java',
            'bot',
            'crawler',
            'spider',
            'scraper'
        ]
        
        user_agent_lower = user_agent.lower()
        
        for pattern in suspicious_patterns:
            if pattern in user_agent_lower:
                MobileSecurityLogger.log_suspicious_traffic_pattern(
                    user_id=user_id,
                    ip_address=ip_address,
                    platform=platform,
                    pattern_type='suspicious_user_agent',
                    pattern_details={
                        'user_agent': user_agent,
                        'matched_pattern': pattern,
                        'description': 'User agent suggests automated tool or bot'
                    },
                    request_id=request_id,
                    severity='medium'
                )
                break
    
    def _check_version_anomaly(
        self,
        app_version: str,
        platform: str,
        ip_address: str,
        user_id: Optional[str],
        request_id: Optional[str]
    ):
        """
        Check for version anomalies.
        
        Args:
            app_version: App version string
            platform: Mobile platform
            ip_address: Client IP address
            user_id: User ID if authenticated
            request_id: Request ID for tracing
        """
        # Check for obviously fake versions
        suspicious_versions = [
            '0.0.0',
            '1.0.0',
            '99.99.99',
            'test',
            'dev',
            'debug'
        ]
        
        if app_version.lower() in suspicious_versions:
            MobileSecurityLogger.log_suspicious_traffic_pattern(
                user_id=user_id,
                ip_address=ip_address,
                platform=platform,
                pattern_type='suspicious_app_version',
                pattern_details={
                    'app_version': app_version,
                    'description': 'App version appears to be fake or test version'
                },
                request_id=request_id,
                severity='medium'
            )
        
        # Check for extremely old versions (potential security risk)
        try:
            major_version = int(app_version.split('.')[0])
            if major_version < 1:
                MobileSecurityLogger.log_suspicious_traffic_pattern(
                    user_id=user_id,
                    ip_address=ip_address,
                    platform=platform,
                    pattern_type='outdated_app_version',
                    pattern_details={
                        'app_version': app_version,
                        'description': 'App version is extremely outdated'
                    },
                    request_id=request_id,
                    severity='low'
                )
        except (ValueError, IndexError):
            # Invalid version format
            MobileSecurityLogger.log_suspicious_traffic_pattern(
                user_id=user_id,
                ip_address=ip_address,
                platform=platform,
                pattern_type='invalid_app_version',
                pattern_details={
                    'app_version': app_version,
                    'description': 'App version format is invalid'
                },
                request_id=request_id,
                severity='low'
            )


# Export public API
__all__ = ['MobileSecurityMiddleware']
