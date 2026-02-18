"""
PII Detection Service

Detects Personally Identifiable Information (PII) in user-generated content
to prevent accidental exposure of sensitive information.

Supports detection of:
- Email addresses
- Phone numbers (US and international formats)
- Social Security Numbers (SSN)
- Credit card numbers (with Luhn algorithm validation)
"""

import re
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class PIIDetection:
    """Represents a detected PII instance"""
    type: str
    severity: str  # 'low', 'medium', 'high'
    message: str
    auto_redact: bool = False


class PIIDetector:
    """
    Service for detecting PII in text content.
    
    Uses regex patterns to identify common PII types and validates
    credit card numbers using the Luhn algorithm.
    """
    
    # Regex patterns for PII detection
    EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    
    # Phone patterns - US and international
    PHONE_PATTERN = r'\b(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
    
    # SSN pattern - XXX-XX-XXXX
    SSN_PATTERN = r'\b\d{3}-\d{2}-\d{4}\b'
    
    # Credit card pattern - 4 groups of 4 digits with optional separators
    CREDIT_CARD_PATTERN = r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
    
    def detect_pii(self, text: str) -> List[PIIDetection]:
        """
        Scan text for PII and return list of detected PII types.
        
        Args:
            text: The text content to scan
            
        Returns:
            List of PIIDetection objects for each detected PII type
        """
        detected = []
        
        # Email detection
        if re.search(self.EMAIL_PATTERN, text):
            detected.append(PIIDetection(
                type='email',
                severity='medium',
                message='Email address detected',
                auto_redact=False
            ))
        
        # Phone number detection
        if re.search(self.PHONE_PATTERN, text):
            detected.append(PIIDetection(
                type='phone',
                severity='medium',
                message='Phone number detected',
                auto_redact=False
            ))
        
        # SSN detection
        if re.search(self.SSN_PATTERN, text):
            detected.append(PIIDetection(
                type='ssn',
                severity='high',
                message='Social Security Number detected',
                auto_redact=True
            ))
        
        # Credit card detection with Luhn validation
        credit_card_matches = re.finditer(self.CREDIT_CARD_PATTERN, text)
        for match in credit_card_matches:
            card_number = re.sub(r'[-\s]', '', match.group())
            if self._is_valid_credit_card(card_number):
                detected.append(PIIDetection(
                    type='credit_card',
                    severity='high',
                    message='Credit card number detected',
                    auto_redact=True
                ))
                break  # Only report once even if multiple cards found
        
        return detected
    
    def redact_pii(self, text: str, pii_types: List[str]) -> str:
        """
        Automatically redact specified PII types from text.
        
        Args:
            text: The text content to redact
            pii_types: List of PII types to redact ('ssn', 'credit_card')
            
        Returns:
            Text with specified PII types redacted
        """
        redacted = text
        
        if 'ssn' in pii_types:
            redacted = re.sub(self.SSN_PATTERN, 'XXX-XX-XXXX', redacted)
        
        if 'credit_card' in pii_types:
            redacted = re.sub(
                self.CREDIT_CARD_PATTERN,
                'XXXX-XXXX-XXXX-XXXX',
                redacted
            )
        
        return redacted
    
    def _is_valid_credit_card(self, card_number: str) -> bool:
        """
        Validate credit card number using Luhn algorithm.
        
        Args:
            card_number: Credit card number string (digits only)
            
        Returns:
            True if valid according to Luhn algorithm, False otherwise
        """
        if not card_number.isdigit():
            return False
        
        if len(card_number) < 13 or len(card_number) > 19:
            return False
        
        # Reject obviously invalid patterns
        if card_number == '0' * len(card_number):  # All zeros
            return False
        if card_number == '1' * len(card_number):  # All ones
            return False
        
        # Luhn algorithm implementation
        def luhn_checksum(card_num):
            digits = [int(d) for d in card_num]
            # Reverse the digits
            digits = digits[::-1]
            
            # Double every second digit (starting from index 1)
            for i in range(1, len(digits), 2):
                digits[i] *= 2
                # If result is > 9, subtract 9
                if digits[i] > 9:
                    digits[i] -= 9
            
            return sum(digits) % 10
        
        return luhn_checksum(card_number) == 0
    
    def get_detected_types(self, detections: List[PIIDetection]) -> List[str]:
        """
        Extract list of detected PII types from detection results.
        
        Args:
            detections: List of PIIDetection objects
            
        Returns:
            List of PII type strings
        """
        return [d.type for d in detections]
    
    def should_auto_redact(self, detections: List[PIIDetection]) -> bool:
        """
        Check if any detected PII should be automatically redacted.
        
        Args:
            detections: List of PIIDetection objects
            
        Returns:
            True if any detection requires auto-redaction
        """
        return any(d.auto_redact for d in detections)
    
    def get_auto_redact_types(self, detections: List[PIIDetection]) -> List[str]:
        """
        Get list of PII types that should be auto-redacted.
        
        Args:
            detections: List of PIIDetection objects
            
        Returns:
            List of PII types requiring auto-redaction
        """
        return [d.type for d in detections if d.auto_redact]
