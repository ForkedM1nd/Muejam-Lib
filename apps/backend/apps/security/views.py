"""Security views."""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from .certificate_pinning_service import CertificatePinningService
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_certificate_fingerprints(request):
    """
    Get certificate fingerprints for certificate pinning.
    
    This endpoint allows mobile clients to retrieve the current SSL/TLS
    certificate fingerprints for the API server. Mobile apps can use these
    fingerprints to implement certificate pinning, protecting against
    man-in-the-middle attacks.
    
    Requirements: 11.1, 11.2
    
    Returns:
        200 OK: Certificate fingerprints in multiple hash formats
        {
            "sha256": ["AA:BB:CC:..."],
            "sha1": ["AA:BB:CC:..."],
            "domain": "api.muejam.com",
            "valid_until": "2025-12-31T23:59:59Z",
            "subject": {"CN": "api.muejam.com"},
            "issuer": {"CN": "Let's Encrypt Authority X3"}
        }
        
        500 Internal Server Error: Error retrieving certificate
    """
    try:
        fingerprints = CertificatePinningService.get_certificate_fingerprints()
        
        # Log the request for security monitoring
        client_type = getattr(request, 'client_type', 'unknown')
        logger.info(
            f"Certificate fingerprints requested by {client_type} client",
            extra={
                'client_type': client_type,
                'user_agent': request.META.get('HTTP_USER_AGENT', 'unknown'),
                'ip_address': request.META.get('REMOTE_ADDR', 'unknown')
            }
        )
        
        return Response(fingerprints, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(
            f"Error retrieving certificate fingerprints: {str(e)}",
            exc_info=True
        )
        return Response(
            {
                'error': {
                    'code': 'CERTIFICATE_ERROR',
                    'message': 'Unable to retrieve certificate fingerprints',
                    'details': {
                        'technical_message': str(e)
                    }
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_certificate_fingerprint(request):
    """
    Verify a certificate fingerprint.
    
    This endpoint allows mobile clients to verify a fingerprint they have
    against the current server certificate. This can be used for testing
    certificate pinning implementations.
    
    Requirements: 11.1, 11.4
    
    Request body:
        {
            "fingerprint": "AA:BB:CC:DD:...",
            "algorithm": "sha256"  // optional, defaults to sha256
        }
    
    Returns:
        200 OK: Fingerprint verification result
        {
            "valid": true,
            "algorithm": "sha256",
            "message": "Fingerprint matches current certificate"
        }
        
        400 Bad Request: Invalid request format
    """
    try:
        fingerprint = request.data.get('fingerprint')
        algorithm = request.data.get('algorithm', 'sha256')
        
        if not fingerprint:
            return Response(
                {
                    'error': {
                        'code': 'MISSING_FIELD',
                        'message': 'Fingerprint is required',
                        'details': {
                            'field': 'fingerprint'
                        }
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if algorithm not in ['sha256', 'sha1']:
            return Response(
                {
                    'error': {
                        'code': 'INVALID_FIELD_VALUE',
                        'message': 'Algorithm must be sha256 or sha1',
                        'details': {
                            'field': 'algorithm',
                            'provided': algorithm,
                            'allowed': ['sha256', 'sha1']
                        }
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Extract request metadata for logging
        client_type = getattr(request, 'client_type', 'unknown')
        user_id = str(request.user.id) if request.user.is_authenticated else None
        ip_address = request.META.get('REMOTE_ADDR', 'unknown')
        app_version = request.META.get('HTTP_X_APP_VERSION')
        request_id = getattr(request, 'request_id', None)
        user_agent = request.META.get('HTTP_USER_AGENT', 'unknown')
        
        # Determine platform from client type
        platform = None
        if client_type.startswith('mobile'):
            platform = client_type
        
        # Verify the fingerprint with enhanced logging
        is_valid = CertificatePinningService.verify_fingerprint(
            provided_fingerprint=fingerprint,
            algorithm=algorithm,
            user_id=user_id,
            ip_address=ip_address,
            platform=platform,
            app_version=app_version,
            request_id=request_id,
            user_agent=user_agent
        )
        
        return Response(
            {
                'valid': is_valid,
                'algorithm': algorithm,
                'message': 'Fingerprint matches current certificate' if is_valid 
                          else 'Fingerprint does not match current certificate'
            },
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(
            f"Error verifying certificate fingerprint: {str(e)}",
            exc_info=True
        )
        return Response(
            {
                'error': {
                    'code': 'VERIFICATION_ERROR',
                    'message': 'Unable to verify certificate fingerprint',
                    'details': {
                        'technical_message': str(e)
                    }
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
