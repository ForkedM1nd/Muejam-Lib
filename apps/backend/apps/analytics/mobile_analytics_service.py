"""
Mobile Analytics Service for Mobile Backend Integration

This service tracks mobile-specific analytics including:
- API response times per client type
- Push notification delivery rates
- Media upload success rates

Requirements: 14.2, 14.3, 14.4
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict
from threading import Lock

logger = logging.getLogger(__name__)


class MobileAnalyticsService:
    """
    Service for tracking mobile-specific analytics.
    
    Tracks:
    - API response times per client type
    - Push notification delivery rates
    - Media upload success rates
    
    Requirements: 14.2, 14.3, 14.4
    """
    
    def __init__(self):
        """Initialize mobile analytics service."""
        self._lock = Lock()
        
        # API response time tracking per client type
        self._api_response_times: Dict[str, List[float]] = defaultdict(list)
        self._api_request_counts: Dict[str, int] = defaultdict(int)
        
        # Push notification tracking
        self._notification_sent: int = 0
        self._notification_failed: int = 0
        self._notification_invalid_token: int = 0
        
        # Media upload tracking
        self._upload_success: int = 0
        self._upload_failed: int = 0
        self._upload_total_size: int = 0
        
        logger.info("MobileAnalyticsService initialized")
    
    def track_api_response_time(
        self,
        client_type: str,
        response_time_ms: float,
        endpoint: str,
        method: str,
        status_code: int
    ) -> None:
        """
        Track API response time for a specific client type.
        
        Args:
            client_type: Client type (web, mobile-ios, mobile-android)
            response_time_ms: Response time in milliseconds
            endpoint: API endpoint path
            method: HTTP method
            status_code: HTTP status code
        
        Requirements: 14.2
        """
        with self._lock:
            self._api_response_times[client_type].append(response_time_ms)
            self._api_request_counts[client_type] += 1
            
            logger.debug(
                f"API response tracked: {client_type} - {method} {endpoint} - "
                f"{response_time_ms:.2f}ms - {status_code}"
            )
    
    def track_notification_delivery(
        self,
        status: str,
        platform: str,
        user_id: str
    ) -> None:
        """
        Track push notification delivery attempt.
        
        Args:
            status: Delivery status ('sent', 'failed', 'invalid_token')
            platform: Platform ('ios' or 'android')
            user_id: User ID
        
        Requirements: 14.3
        """
        with self._lock:
            if status == 'sent':
                self._notification_sent += 1
            elif status == 'invalid_token':
                self._notification_invalid_token += 1
            else:
                self._notification_failed += 1
            
            logger.debug(
                f"Notification delivery tracked: {status} - {platform} - user {user_id}"
            )
    
    def track_media_upload(
        self,
        success: bool,
        file_size: int,
        client_type: str,
        filename: str
    ) -> None:
        """
        Track media upload attempt.
        
        Args:
            success: Whether upload was successful
            file_size: Size of uploaded file in bytes
            client_type: Client type
            filename: Original filename
        
        Requirements: 14.4
        """
        with self._lock:
            if success:
                self._upload_success += 1
                self._upload_total_size += file_size
            else:
                self._upload_failed += 1
            
            logger.debug(
                f"Media upload tracked: {'success' if success else 'failed'} - "
                f"{client_type} - {filename} - {file_size} bytes"
            )
    
    def get_api_response_metrics(self) -> Dict:
        """
        Get API response time metrics per client type.
        
        Returns:
            Dictionary with response time statistics per client type
        
        Requirements: 14.2
        """
        with self._lock:
            metrics = {}
            
            for client_type, response_times in self._api_response_times.items():
                if not response_times:
                    continue
                
                metrics[client_type] = {
                    'request_count': self._api_request_counts[client_type],
                    'avg_response_time_ms': sum(response_times) / len(response_times),
                    'min_response_time_ms': min(response_times),
                    'max_response_time_ms': max(response_times),
                    'p50_response_time_ms': self._calculate_percentile(response_times, 50),
                    'p95_response_time_ms': self._calculate_percentile(response_times, 95),
                    'p99_response_time_ms': self._calculate_percentile(response_times, 99),
                }
            
            return metrics
    
    def get_notification_metrics(self) -> Dict:
        """
        Get push notification delivery metrics.
        
        Returns:
            Dictionary with notification delivery statistics
        
        Requirements: 14.3
        """
        with self._lock:
            total_attempts = (
                self._notification_sent +
                self._notification_failed +
                self._notification_invalid_token
            )
            
            if total_attempts == 0:
                delivery_rate = 0.0
                failure_rate = 0.0
                invalid_token_rate = 0.0
            else:
                delivery_rate = (self._notification_sent / total_attempts) * 100
                failure_rate = (self._notification_failed / total_attempts) * 100
                invalid_token_rate = (self._notification_invalid_token / total_attempts) * 100
            
            return {
                'total_attempts': total_attempts,
                'sent': self._notification_sent,
                'failed': self._notification_failed,
                'invalid_token': self._notification_invalid_token,
                'delivery_rate_percent': delivery_rate,
                'failure_rate_percent': failure_rate,
                'invalid_token_rate_percent': invalid_token_rate,
            }
    
    def get_upload_metrics(self) -> Dict:
        """
        Get media upload metrics.
        
        Returns:
            Dictionary with upload statistics
        
        Requirements: 14.4
        """
        with self._lock:
            total_attempts = self._upload_success + self._upload_failed
            
            if total_attempts == 0:
                success_rate = 0.0
                avg_file_size = 0
            else:
                success_rate = (self._upload_success / total_attempts) * 100
                avg_file_size = (
                    self._upload_total_size / self._upload_success
                    if self._upload_success > 0
                    else 0
                )
            
            return {
                'total_attempts': total_attempts,
                'successful': self._upload_success,
                'failed': self._upload_failed,
                'success_rate_percent': success_rate,
                'total_size_bytes': self._upload_total_size,
                'avg_file_size_bytes': avg_file_size,
            }
    
    def get_all_mobile_metrics(self) -> Dict:
        """
        Get all mobile analytics metrics.
        
        Returns:
            Dictionary containing all mobile metrics
        
        Requirements: 14.2, 14.3, 14.4
        """
        return {
            'api_response_times': self.get_api_response_metrics(),
            'push_notifications': self.get_notification_metrics(),
            'media_uploads': self.get_upload_metrics(),
            'timestamp': datetime.now().isoformat(),
        }
    
    def _calculate_percentile(self, values: List[float], percentile: int) -> float:
        """
        Calculate percentile value from a list of values.
        
        Args:
            values: List of numeric values
            percentile: Percentile to calculate (0-100)
        
        Returns:
            Percentile value
        """
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int((percentile / 100) * len(sorted_values))
        
        # Ensure index is within bounds
        if index >= len(sorted_values):
            index = len(sorted_values) - 1
        
        return sorted_values[index]
    
    def reset_metrics(self) -> None:
        """
        Reset all metrics to initial state.
        
        Useful for testing or periodic resets.
        """
        with self._lock:
            self._api_response_times.clear()
            self._api_request_counts.clear()
            self._notification_sent = 0
            self._notification_failed = 0
            self._notification_invalid_token = 0
            self._upload_success = 0
            self._upload_failed = 0
            self._upload_total_size = 0
            
            logger.info("Mobile analytics metrics reset")


# Global mobile analytics service instance
_mobile_analytics_service: Optional[MobileAnalyticsService] = None


def get_mobile_analytics_service() -> MobileAnalyticsService:
    """
    Get the global mobile analytics service instance.
    
    Returns:
        Global MobileAnalyticsService instance
    """
    global _mobile_analytics_service
    if _mobile_analytics_service is None:
        _mobile_analytics_service = MobileAnalyticsService()
    return _mobile_analytics_service


def reset_mobile_analytics_service() -> None:
    """
    Reset the global mobile analytics service instance.
    
    Useful for testing.
    """
    global _mobile_analytics_service
    _mobile_analytics_service = None
