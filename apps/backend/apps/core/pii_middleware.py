"""
PII Detection Middleware

Provides middleware and decorators for detecting PII in content submissions.
Warns users when PII is detected and automatically redacts sensitive PII types.
"""

import logging
from functools import wraps
from rest_framework.response import Response
from rest_framework import status

from .pii_detector import PIIDetector

logger = logging.getLogger(__name__)


def detect_pii_in_content(content_fields=None):
    """
    Decorator to detect PII in content before submission.
    
    Scans specified fields for PII and:
    - Warns users when PII is detected
    - Automatically redacts high-severity PII (SSN, credit cards)
    - Allows user to confirm submission after warning
    
    Args:
        content_fields: List of field names to scan for PII.
                       If None, scans common fields: ['content', 'blurb', 'bio']
    
    Usage:
        @detect_pii_in_content(content_fields=['title', 'blurb'])
        def create_story(request):
            ...
    
    Requirements:
        - 9.1: Detect PII patterns in content
        - 9.2: Warn users when PII is detected
        - 9.3: Allow confirmation or editing
        - 9.4: Auto-redact SSN and credit cards
        - 9.5: Log PII detection without storing values
    """
    if content_fields is None:
        content_fields = ['content', 'blurb', 'bio', 'display_name']
    
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Only check POST and PUT requests
            if request.method not in ['POST', 'PUT', 'PATCH']:
                return view_func(request, *args, **kwargs)
            
            # Check if user has confirmed PII warning
            pii_confirmed = request.data.get('pii_confirmed', False)
            
            # Initialize PII detector
            detector = PIIDetector()
            
            # Scan all specified fields for PII
            all_detections = []
            fields_with_pii = {}
            
            for field in content_fields:
                if field in request.data and request.data[field]:
                    content = str(request.data[field])
                    detections = detector.detect_pii(content)
                    
                    if detections:
                        all_detections.extend(detections)
                        fields_with_pii[field] = detections
            
            # If PII detected
            if all_detections:
                # Log PII detection event (without storing actual PII values)
                # Requirement 9.5
                logger.warning(
                    f"PII detected in content submission",
                    extra={
                        'user_id': getattr(request, 'clerk_user_id', None),
                        'pii_types': detector.get_detected_types(all_detections),
                        'fields': list(fields_with_pii.keys()),
                        'endpoint': request.path,
                        'method': request.method
                    }
                )
                
                # Auto-redact high-severity PII (Requirement 9.4)
                if detector.should_auto_redact(all_detections):
                    auto_redact_types = detector.get_auto_redact_types(all_detections)
                    
                    # Redact PII in request data
                    for field in fields_with_pii:
                        if field in request.data:
                            original_content = str(request.data[field])
                            redacted_content = detector.redact_pii(
                                original_content,
                                auto_redact_types
                            )
                            # Update request data with redacted content
                            request.data[field] = redacted_content
                
                # If user hasn't confirmed, return warning (Requirements 9.2, 9.3)
                if not pii_confirmed:
                    # Build warning response
                    pii_warnings = []
                    for field, detections in fields_with_pii.items():
                        for detection in detections:
                            pii_warnings.append({
                                'field': field,
                                'type': detection.type,
                                'severity': detection.severity,
                                'message': detection.message,
                                'auto_redacted': detection.auto_redact
                            })
                    
                    return Response(
                        {
                            'warning': {
                                'code': 'PII_DETECTED',
                                'message': 'Personally identifiable information detected in your content',
                                'details': pii_warnings,
                                'action_required': 'Please review and either edit your content or confirm submission by including "pii_confirmed": true in your request'
                            }
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Proceed with original view function
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def check_profile_pii(request_data, fields=None):
    """
    Check profile fields for PII and prevent update if detected.
    
    Used for profile updates where PII should be blocked entirely.
    
    Args:
        request_data: Request data dictionary
        fields: List of fields to check (default: ['bio', 'display_name'])
    
    Returns:
        tuple: (has_pii: bool, error_response: Response or None)
    
    Requirements:
        - 9.7: Prevent profile updates with PII
    """
    if fields is None:
        fields = ['bio', 'display_name']
    
    detector = PIIDetector()
    
    for field in fields:
        if field in request_data and request_data[field]:
            content = str(request_data[field])
            detections = detector.detect_pii(content)
            
            if detections:
                # Log detection
                logger.warning(
                    f"PII detected in profile field: {field}",
                    extra={
                        'pii_types': detector.get_detected_types(detections),
                        'field': field
                    }
                )
                
                # Build error response
                pii_types = [d.type for d in detections]
                error_response = Response(
                    {
                        'error': {
                            'code': 'PII_IN_PROFILE',
                            'message': f'Personally identifiable information detected in {field}',
                            'details': {
                                'field': field,
                                'pii_types': pii_types,
                                'message': 'Please remove personal information such as email addresses, phone numbers, or other sensitive data from your profile'
                            }
                        }
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
                
                return True, error_response
    
    return False, None
