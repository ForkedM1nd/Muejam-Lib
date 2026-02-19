"""
Mobile Security Logging Service

Provides specialized logging for mobile-specific security events including:
- Certificate pinning failures
- Suspicious mobile traffic patterns
- Mobile app attestation attempts

Requirements: 11.4
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from infrastructure.logging_config import get_logger, StructuredLogger

logger = get_logger(__name__)


class MobileSecurityLogger:
    """
    Service for logging mobile-specific security events.
    
    Implements structured logging for:
    - Certificate pinning failures (Requirement 11.1, 11.2)
    - Suspicious mobile traffic patterns (Requirement 11.3)
    - Mobile app attestation attempts (Requirement 11.5)
    
    Requirements: 11.4
    """
    
    @staticmethod
    def log_certificate_pinning_failure(
        user_id: Optional[str],
        ip_address: str,
        platform: str,
        app_version: Optional[str],
        provided_fingerprint: Optional[str],
        expected_fingerprint: str,
        request_id: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """
        Log certificate pinning validation failure.
        
        This indicates a potential MITM attack or client misconfiguration.
        
        Args:
            user_id: User ID if authenticated
            ip_address: Client IP address
            platform: Mobile platform ('ios' or 'android')
            app_version: Mobile app version
            provided_fingerprint: Certificate fingerprint provided by client
            expected_fingerprint: Expected certificate fingerprint
            request_id: Request ID for tracing
            user_agent: User agent string
            
        Requirements: 11.1, 11.2, 11.4
        """
        logger.error(
            'Certificate pinning validation failed',
            event_type='mobile_security',
            security_event='certificate_pinning_failure',
            user_id=user_id,
            ip_address=ip_address,
            platform=platform,
            app_version=app_version,
            provided_fingerprint=provided_fingerprint,
            expected_fingerprint=expected_fingerprint,
            request_id=request_id,
            user_agent=user_agent,
            severity='high',
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    
    @staticmethod
    def log_certificate_pinning_success(
        user_id: Optional[str],
        ip_address: str,
        platform: str,
        app_version: Optional[str],
        fingerprint: str,
        request_id: Optional[str] = None
    ):
        """
        Log successful certificate pinning validation.
        
        Args:
            user_id: User ID if authenticated
            ip_address: Client IP address
            platform: Mobile platform ('ios' or 'android')
            app_version: Mobile app version
            fingerprint: Validated certificate fingerprint
            request_id: Request ID for tracing
            
        Requirements: 11.1, 11.2, 11.4
        """
        logger.info(
            'Certificate pinning validation successful',
            event_type='mobile_security',
            security_event='certificate_pinning_success',
            user_id=user_id,
            ip_address=ip_address,
            platform=platform,
            app_version=app_version,
            fingerprint=fingerprint,
            request_id=request_id,
            severity='info',
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    
    @staticmethod
    def log_suspicious_traffic_pattern(
        user_id: Optional[str],
        ip_address: str,
        platform: str,
        pattern_type: str,
        pattern_details: Dict[str, Any],
        request_id: Optional[str] = None,
        severity: str = 'medium'
    ):
        """
        Log suspicious mobile traffic pattern detection.
        
        Pattern types include:
        - rapid_requests: Too many requests in short time
        - unusual_endpoints: Access to unusual endpoint combinations
        - abnormal_timing: Requests at unusual times or intervals
        - geographic_anomaly: Requests from unusual locations
        - version_mismatch: Outdated or suspicious app version
        - device_fingerprint_change: Device fingerprint changed
        
        Args:
            user_id: User ID if authenticated
            ip_address: Client IP address
            platform: Mobile platform ('ios' or 'android')
            pattern_type: Type of suspicious pattern detected
            pattern_details: Additional details about the pattern
            request_id: Request ID for tracing
            severity: Severity level ('low', 'medium', 'high', 'critical')
            
        Requirements: 11.3, 11.4
        """
        logger.warning(
            f'Suspicious mobile traffic pattern detected: {pattern_type}',
            event_type='mobile_security',
            security_event='suspicious_traffic_pattern',
            user_id=user_id,
            ip_address=ip_address,
            platform=platform,
            pattern_type=pattern_type,
            pattern_details=pattern_details,
            request_id=request_id,
            severity=severity,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    
    @staticmethod
    def log_app_attestation_attempt(
        user_id: Optional[str],
        ip_address: str,
        platform: str,
        app_version: str,
        attestation_result: str,
        attestation_details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
        failure_reason: Optional[str] = None
    ):
        """
        Log mobile app attestation attempt.
        
        App attestation verifies that the request is coming from a genuine
        mobile app and not a modified or emulated version.
        
        Args:
            user_id: User ID if authenticated
            ip_address: Client IP address
            platform: Mobile platform ('ios' or 'android')
            app_version: Mobile app version
            attestation_result: Result ('success', 'failure', 'error')
            attestation_details: Additional attestation details
            request_id: Request ID for tracing
            failure_reason: Reason for failure if applicable
            
        Requirements: 11.5, 11.4
        """
        log_level = 'info' if attestation_result == 'success' else 'warning'
        severity = 'info' if attestation_result == 'success' else 'high'
        
        log_method = logger.info if log_level == 'info' else logger.warning
        
        log_method(
            f'Mobile app attestation attempt: {attestation_result}',
            event_type='mobile_security',
            security_event='app_attestation_attempt',
            user_id=user_id,
            ip_address=ip_address,
            platform=platform,
            app_version=app_version,
            attestation_result=attestation_result,
            attestation_details=attestation_details or {},
            request_id=request_id,
            failure_reason=failure_reason,
            severity=severity,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    
    @staticmethod
    def log_mobile_security_event(
        event_type: str,
        user_id: Optional[str],
        ip_address: str,
        platform: str,
        details: Dict[str, Any],
        severity: str = 'medium',
        request_id: Optional[str] = None
    ):
        """
        Log a general mobile security event.
        
        Use this for mobile security events that don't fit the specific
        categories above.
        
        Args:
            event_type: Type of security event
            user_id: User ID if authenticated
            ip_address: Client IP address
            platform: Mobile platform ('ios' or 'android')
            details: Event details
            severity: Severity level ('low', 'medium', 'high', 'critical')
            request_id: Request ID for tracing
            
        Requirements: 11.4
        """
        log_method = logger.info if severity == 'low' else logger.warning
        
        log_method(
            f'Mobile security event: {event_type}',
            event_type='mobile_security',
            security_event=event_type,
            user_id=user_id,
            ip_address=ip_address,
            platform=platform,
            details=details,
            severity=severity,
            request_id=request_id,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    
    @staticmethod
    def log_rate_limit_violation(
        user_id: Optional[str],
        ip_address: str,
        platform: str,
        endpoint: str,
        limit_type: str,
        current_count: int,
        limit: int,
        request_id: Optional[str] = None
    ):
        """
        Log mobile client rate limit violation.
        
        Args:
            user_id: User ID if authenticated
            ip_address: Client IP address
            platform: Mobile platform ('ios' or 'android')
            endpoint: API endpoint
            limit_type: Type of rate limit ('per_minute', 'per_hour', 'per_day')
            current_count: Current request count
            limit: Rate limit threshold
            request_id: Request ID for tracing
            
        Requirements: 11.4
        """
        logger.warning(
            f'Mobile rate limit violation: {endpoint}',
            event_type='mobile_security',
            security_event='rate_limit_violation',
            user_id=user_id,
            ip_address=ip_address,
            platform=platform,
            endpoint=endpoint,
            limit_type=limit_type,
            current_count=current_count,
            limit=limit,
            request_id=request_id,
            severity='medium',
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    
    @staticmethod
    def log_invalid_client_type(
        ip_address: str,
        provided_client_type: str,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None
    ):
        """
        Log invalid client type header.
        
        Args:
            ip_address: Client IP address
            provided_client_type: Invalid client type provided
            user_agent: User agent string
            request_id: Request ID for tracing
            
        Requirements: 11.4
        """
        logger.warning(
            f'Invalid client type provided: {provided_client_type}',
            event_type='mobile_security',
            security_event='invalid_client_type',
            ip_address=ip_address,
            provided_client_type=provided_client_type,
            user_agent=user_agent,
            request_id=request_id,
            severity='low',
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    
    @staticmethod
    def log_device_token_anomaly(
        user_id: str,
        device_token: str,
        platform: str,
        anomaly_type: str,
        details: Dict[str, Any],
        request_id: Optional[str] = None
    ):
        """
        Log device token anomaly.
        
        Anomaly types include:
        - multiple_registrations: Same token registered multiple times
        - platform_mismatch: Token format doesn't match platform
        - suspicious_token: Token appears to be fake or invalid
        - rapid_changes: Device token changing too frequently
        
        Args:
            user_id: User ID
            device_token: Device token (truncated for logging)
            platform: Mobile platform ('ios' or 'android')
            anomaly_type: Type of anomaly detected
            details: Additional details
            request_id: Request ID for tracing
            
        Requirements: 11.4
        """
        # Truncate token for logging (show first/last 8 chars)
        if len(device_token) > 16:
            truncated_token = f"{device_token[:8]}...{device_token[-8:]}"
        else:
            truncated_token = device_token[:8] + "..."
        
        logger.warning(
            f'Device token anomaly detected: {anomaly_type}',
            event_type='mobile_security',
            security_event='device_token_anomaly',
            user_id=user_id,
            device_token=truncated_token,
            platform=platform,
            anomaly_type=anomaly_type,
            details=details,
            request_id=request_id,
            severity='medium',
            timestamp=datetime.now(timezone.utc).isoformat()
        )


# Export public API
__all__ = ['MobileSecurityLogger']
