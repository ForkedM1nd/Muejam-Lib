"""Tests for PII detection service."""

import pytest
from apps.core.pii_detector import PIIDetector, PIIDetection


class TestPIIDetector:
    """Test suite for PIIDetector service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.detector = PIIDetector()
    
    def test_detect_email(self):
        """Test email detection."""
        text = "Contact me at john.doe@example.com for more info"
        detections = self.detector.detect_pii(text)
        
        assert len(detections) == 1
        assert detections[0].type == 'email'
        assert detections[0].severity == 'medium'
        assert not detections[0].auto_redact
    
    def test_detect_phone_number(self):
        """Test phone number detection."""
        text = "Call me at (555) 123-4567"
        detections = self.detector.detect_pii(text)
        
        assert len(detections) == 1
        assert detections[0].type == 'phone'
        assert detections[0].severity == 'medium'
    
    def test_detect_ssn(self):
        """Test SSN detection."""
        text = "My SSN is 123-45-6789"
        detections = self.detector.detect_pii(text)
        
        assert len(detections) == 1
        assert detections[0].type == 'ssn'
        assert detections[0].severity == 'high'
        assert detections[0].auto_redact
    
    def test_detect_credit_card(self):
        """Test credit card detection with Luhn validation."""
        # Valid credit card number (passes Luhn check)
        text = "My card is 5425-2334-3010-9903"
        detections = self.detector.detect_pii(text)
        
        assert len(detections) == 1
        assert detections[0].type == 'credit_card'
        assert detections[0].severity == 'high'
        assert detections[0].auto_redact
    
    def test_invalid_credit_card_not_detected(self):
        """Test that invalid credit card numbers are not detected."""
        # Invalid credit card number (fails Luhn check)
        text = "Random numbers 1234-5678-9012-3456"
        detections = self.detector.detect_pii(text)
        
        # Should not detect as credit card
        credit_card_detections = [d for d in detections if d.type == 'credit_card']
        assert len(credit_card_detections) == 0
    
    def test_detect_multiple_pii_types(self):
        """Test detection of multiple PII types in same text."""
        text = "Email: test@example.com, Phone: 555-123-4567, SSN: 123-45-6789"
        detections = self.detector.detect_pii(text)
        
        assert len(detections) == 3
        types = [d.type for d in detections]
        assert 'email' in types
        assert 'phone' in types
        assert 'ssn' in types
    
    def test_no_pii_detected(self):
        """Test that clean text returns no detections."""
        text = "This is a normal story with no personal information"
        detections = self.detector.detect_pii(text)
        
        assert len(detections) == 0
    
    def test_redact_ssn(self):
        """Test SSN redaction."""
        text = "My SSN is 123-45-6789 and I live here"
        redacted = self.detector.redact_pii(text, ['ssn'])
        
        assert '123-45-6789' not in redacted
        assert 'XXX-XX-XXXX' in redacted
        assert 'and I live here' in redacted
    
    def test_redact_credit_card(self):
        """Test credit card redaction."""
        text = "Card number: 5425-2334-3010-9903"
        redacted = self.detector.redact_pii(text, ['credit_card'])
        
        assert '5425-2334-3010-9903' not in redacted
        assert 'XXXX-XXXX-XXXX-XXXX' in redacted
    
    def test_redact_multiple_types(self):
        """Test redacting multiple PII types."""
        text = "SSN: 123-45-6789, Card: 5425-2334-3010-9903"
        redacted = self.detector.redact_pii(text, ['ssn', 'credit_card'])
        
        assert '123-45-6789' not in redacted
        assert '5425-2334-3010-9903' not in redacted
        assert 'XXX-XX-XXXX' in redacted
        assert 'XXXX-XXXX-XXXX-XXXX' in redacted
    
    def test_get_detected_types(self):
        """Test extracting detected PII types."""
        detections = [
            PIIDetection('email', 'medium', 'Email detected'),
            PIIDetection('phone', 'medium', 'Phone detected'),
        ]
        
        types = self.detector.get_detected_types(detections)
        assert types == ['email', 'phone']
    
    def test_should_auto_redact(self):
        """Test checking if auto-redaction is needed."""
        detections_with_redact = [
            PIIDetection('email', 'medium', 'Email', auto_redact=False),
            PIIDetection('ssn', 'high', 'SSN', auto_redact=True),
        ]
        
        assert self.detector.should_auto_redact(detections_with_redact)
        
        detections_no_redact = [
            PIIDetection('email', 'medium', 'Email', auto_redact=False),
            PIIDetection('phone', 'medium', 'Phone', auto_redact=False),
        ]
        
        assert not self.detector.should_auto_redact(detections_no_redact)
    
    def test_get_auto_redact_types(self):
        """Test getting list of types requiring auto-redaction."""
        detections = [
            PIIDetection('email', 'medium', 'Email', auto_redact=False),
            PIIDetection('ssn', 'high', 'SSN', auto_redact=True),
            PIIDetection('credit_card', 'high', 'Card', auto_redact=True),
        ]
        
        redact_types = self.detector.get_auto_redact_types(detections)
        assert redact_types == ['ssn', 'credit_card']
    
    def test_luhn_algorithm_validation(self):
        """Test Luhn algorithm for credit card validation."""
        # Valid credit card numbers
        assert self.detector._is_valid_credit_card('5425233430109903')
        assert self.detector._is_valid_credit_card('374245455400126')
        assert self.detector._is_valid_credit_card('4111111111111111')
        
        # Invalid credit card numbers
        assert not self.detector._is_valid_credit_card('1234567890123456')
        assert not self.detector._is_valid_credit_card('0000000000000000')
        assert not self.detector._is_valid_credit_card('1111111111111111')
    
    def test_phone_number_formats(self):
        """Test various phone number formats."""
        formats = [
            "(555) 123-4567",
            "555-123-4567",
            "555.123.4567",
            "+1 555-123-4567",
        ]
        
        for phone_format in formats:
            text = f"Call me at {phone_format}"
            detections = self.detector.detect_pii(text)
            phone_detections = [d for d in detections if d.type == 'phone']
            assert len(phone_detections) >= 1, f"Failed to detect: {phone_format}"
