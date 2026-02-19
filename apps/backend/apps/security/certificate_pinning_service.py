"""
Certificate pinning service for mobile clients.

Provides certificate fingerprint verification to support certificate pinning
in mobile applications, protecting against man-in-the-middle attacks.

Requirements: 11.1, 11.2
"""

import hashlib
import ssl
import socket
from typing import Dict, List, Optional
from django.conf import settings
import logging

from apps.security.mobile_security_logger import MobileSecurityLogger

logger = logging.getLogger(__name__)


class CertificatePinningService:
    """
    Service for managing certificate pinning for mobile clients.
    
    Provides certificate fingerprints that mobile clients can use to verify
    the server's SSL/TLS certificate, preventing MITM attacks.
    """
    
    @staticmethod
    def get_certificate_fingerprints() -> Dict[str, List[str]]:
        """
        Get current certificate fingerprints for the API server.
        
        Returns multiple hash algorithms for compatibility with different
        mobile platforms (iOS uses SHA-256, Android supports multiple).
        
        Returns:
            Dictionary with fingerprints in different hash formats:
            {
                'sha256': ['fingerprint1', 'fingerprint2'],  # Primary cert + backup
                'sha1': ['fingerprint1', 'fingerprint2'],    # Legacy support
                'domain': 'api.muejam.com',
                'valid_until': '2025-12-31T23:59:59Z'
            }
        """
        try:
            # Get domain from settings
            domain = getattr(settings, 'API_DOMAIN', 'api.muejam.com')
            
            # In production, get actual certificate from the server
            if getattr(settings, 'ENVIRONMENT', 'development') == 'production':
                fingerprints = CertificatePinningService._get_live_certificate_fingerprints(domain)
            else:
                # In development/test, return mock fingerprints
                fingerprints = CertificatePinningService._get_mock_fingerprints(domain)
            
            logger.info(f"Certificate fingerprints retrieved for domain: {domain}")
            return fingerprints
            
        except Exception as e:
            logger.error(f"Error retrieving certificate fingerprints: {str(e)}")
            raise
    
    @staticmethod
    def _get_live_certificate_fingerprints(domain: str) -> Dict[str, any]:
        """
        Retrieve actual certificate fingerprints from the live server.
        
        Args:
            domain: Domain name to retrieve certificate from
            
        Returns:
            Dictionary with certificate fingerprints and metadata
        """
        try:
            # Connect to the server and get certificate
            context = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    # Get certificate in DER format
                    cert_der = ssock.getpeercert(binary_form=True)
                    cert_info = ssock.getpeercert()
                    
                    # Calculate fingerprints
                    sha256_fingerprint = hashlib.sha256(cert_der).hexdigest()
                    sha1_fingerprint = hashlib.sha1(cert_der).hexdigest()
                    
                    # Format fingerprints with colons (standard format)
                    sha256_formatted = ':'.join(
                        sha256_fingerprint[i:i+2] for i in range(0, len(sha256_fingerprint), 2)
                    )
                    sha1_formatted = ':'.join(
                        sha1_fingerprint[i:i+2] for i in range(0, len(sha1_fingerprint), 2)
                    )
                    
                    # Get certificate validity period
                    valid_until = cert_info.get('notAfter', 'Unknown')
                    
                    return {
                        'sha256': [sha256_formatted.upper()],
                        'sha1': [sha1_formatted.upper()],
                        'domain': domain,
                        'valid_until': valid_until,
                        'subject': dict(x[0] for x in cert_info.get('subject', [])),
                        'issuer': dict(x[0] for x in cert_info.get('issuer', []))
                    }
                    
        except Exception as e:
            logger.error(f"Error retrieving live certificate for {domain}: {str(e)}")
            raise
    
    @staticmethod
    def _get_mock_fingerprints(domain: str) -> Dict[str, any]:
        """
        Return mock fingerprints for development/testing.
        
        Args:
            domain: Domain name
            
        Returns:
            Dictionary with mock certificate fingerprints
        """
        return {
            'sha256': [
                'AA:BB:CC:DD:EE:FF:00:11:22:33:44:55:66:77:88:99:AA:BB:CC:DD:EE:FF:00:11:22:33:44:55:66:77:88:99'
            ],
            'sha1': [
                'AA:BB:CC:DD:EE:FF:00:11:22:33:44:55:66:77:88:99:AA:BB:CC:DD'
            ],
            'domain': domain,
            'valid_until': '2025-12-31T23:59:59Z',
            'subject': {'CN': domain},
            'issuer': {'CN': 'Development CA'},
            'note': 'Development environment - mock fingerprints'
        }
    
    @staticmethod
    def verify_fingerprint(
        provided_fingerprint: str,
        algorithm: str = 'sha256',
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        platform: Optional[str] = None,
        app_version: Optional[str] = None,
        request_id: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """
        Verify a provided fingerprint against current certificate.
        
        Args:
            provided_fingerprint: Fingerprint to verify
            algorithm: Hash algorithm used ('sha256' or 'sha1')
            user_id: User ID if authenticated (for logging)
            ip_address: Client IP address (for logging)
            platform: Mobile platform (for logging)
            app_version: App version (for logging)
            request_id: Request ID (for logging)
            user_agent: User agent string (for logging)
            
        Returns:
            True if fingerprint matches, False otherwise
        """
        try:
            current_fingerprints = CertificatePinningService.get_certificate_fingerprints()
            expected_fingerprints = current_fingerprints.get(algorithm, [])
            
            # Normalize fingerprints (remove colons, convert to uppercase)
            provided_normalized = provided_fingerprint.replace(':', '').upper()
            expected_normalized = [fp.replace(':', '').upper() for fp in expected_fingerprints]
            
            is_valid = provided_normalized in expected_normalized
            
            if is_valid:
                logger.info(f"Certificate fingerprint verified successfully ({algorithm})")
                
                # Log successful validation
                if ip_address and platform:
                    MobileSecurityLogger.log_certificate_pinning_success(
                        user_id=user_id,
                        ip_address=ip_address,
                        platform=platform,
                        app_version=app_version,
                        fingerprint=provided_fingerprint,
                        request_id=request_id
                    )
            else:
                logger.warning(f"Certificate fingerprint verification failed ({algorithm})")
                
                # Log pinning failure
                if ip_address and platform:
                    expected_fp = expected_fingerprints[0] if expected_fingerprints else 'unknown'
                    MobileSecurityLogger.log_certificate_pinning_failure(
                        user_id=user_id,
                        ip_address=ip_address,
                        platform=platform,
                        app_version=app_version,
                        provided_fingerprint=provided_fingerprint,
                        expected_fingerprint=expected_fp,
                        request_id=request_id,
                        user_agent=user_agent
                    )
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Error verifying certificate fingerprint: {str(e)}")
            
            # Log error as security event
            if ip_address and platform:
                MobileSecurityLogger.log_mobile_security_event(
                    event_type='certificate_verification_error',
                    user_id=user_id,
                    ip_address=ip_address,
                    platform=platform,
                    details={
                        'error': str(e),
                        'algorithm': algorithm,
                        'provided_fingerprint': provided_fingerprint
                    },
                    severity='high',
                    request_id=request_id
                )
            
            return False
