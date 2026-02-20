"""
Tests for certificate pinning functionality.

Requirements: 11.1, 11.2
"""

import pytest
from django.test import RequestFactory
from unittest.mock import patch, MagicMock
from apps.security.certificate_pinning_service import CertificatePinningService
from apps.security.views import get_certificate_fingerprints, verify_certificate_fingerprint


class TestCertificatePinningService:
    """Test certificate pinning service."""
    
    def test_get_mock_fingerprints_in_development(self):
        """Test that mock fingerprints are returned in development."""
        with patch('apps.security.certificate_pinning_service.settings') as mock_settings:
            mock_settings.ENVIRONMENT = 'development'
            mock_settings.API_DOMAIN = 'api.test.com'
            
            fingerprints = CertificatePinningService.get_certificate_fingerprints()
            
            assert 'sha256' in fingerprints
            assert 'sha1' in fingerprints
            assert 'domain' in fingerprints
            assert fingerprints['domain'] == 'api.test.com'
            assert len(fingerprints['sha256']) > 0
            assert len(fingerprints['sha1']) > 0
    
    def test_verify_fingerprint_success(self):
        """Test successful fingerprint verification."""
        with patch('apps.security.certificate_pinning_service.settings') as mock_settings:
            mock_settings.ENVIRONMENT = 'development'
            mock_settings.API_DOMAIN = 'api.test.com'
            
            # Get mock fingerprints
            fingerprints = CertificatePinningService.get_certificate_fingerprints()
            test_fingerprint = fingerprints['sha256'][0]
            
            # Verify it
            is_valid = CertificatePinningService.verify_fingerprint(test_fingerprint, 'sha256')
            
            assert is_valid is True
    
    def test_verify_fingerprint_failure(self):
        """Test fingerprint verification with invalid fingerprint."""
        with patch('apps.security.certificate_pinning_service.settings') as mock_settings:
            mock_settings.ENVIRONMENT = 'development'
            mock_settings.API_DOMAIN = 'api.test.com'
            
            # Try to verify an invalid fingerprint
            invalid_fingerprint = 'FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF'
            is_valid = CertificatePinningService.verify_fingerprint(invalid_fingerprint, 'sha256')
            
            assert is_valid is False
    
    def test_verify_fingerprint_without_colons(self):
        """Test fingerprint verification works with or without colons."""
        with patch('apps.security.certificate_pinning_service.settings') as mock_settings:
            mock_settings.ENVIRONMENT = 'development'
            mock_settings.API_DOMAIN = 'api.test.com'
            
            # Get mock fingerprints
            fingerprints = CertificatePinningService.get_certificate_fingerprints()
            test_fingerprint = fingerprints['sha256'][0]
            
            # Remove colons
            fingerprint_no_colons = test_fingerprint.replace(':', '')
            
            # Verify it still works
            is_valid = CertificatePinningService.verify_fingerprint(fingerprint_no_colons, 'sha256')
            
            assert is_valid is True


class TestCertificatePinningViews:
    """Test certificate pinning API endpoints."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
    
    def test_get_certificate_fingerprints_success(self):
        """Test successful retrieval of certificate fingerprints."""
        with patch('apps.security.certificate_pinning_service.settings') as mock_settings:
            mock_settings.ENVIRONMENT = 'development'
            mock_settings.API_DOMAIN = 'api.test.com'
            
            request = self.factory.get('/v1/security/certificate/fingerprints')
            request.client_type = 'mobile-ios'
            
            response = get_certificate_fingerprints(request)
            
            assert response.status_code == 200
            assert 'sha256' in response.data
            assert 'sha1' in response.data
            assert 'domain' in response.data
    
    def test_verify_certificate_fingerprint_success(self):
        """Test successful fingerprint verification via API."""
        with patch('apps.security.certificate_pinning_service.settings') as mock_settings:
            mock_settings.ENVIRONMENT = 'development'
            mock_settings.API_DOMAIN = 'api.test.com'
            
            # Get a valid fingerprint
            fingerprints = CertificatePinningService.get_certificate_fingerprints()
            valid_fingerprint = fingerprints['sha256'][0]
            
            request = self.factory.post(
                '/v1/security/certificate/verify',
                data={'fingerprint': valid_fingerprint, 'algorithm': 'sha256'},
                content_type='application/json'
            )
            request.client_type = 'mobile-android'
            
            response = verify_certificate_fingerprint(request)
            
            assert response.status_code == 200
            assert response.data['valid'] is True
            assert response.data['algorithm'] == 'sha256'
    
    def test_verify_certificate_fingerprint_invalid(self):
        """Test fingerprint verification with invalid fingerprint."""
        with patch('apps.security.certificate_pinning_service.settings') as mock_settings:
            mock_settings.ENVIRONMENT = 'development'
            mock_settings.API_DOMAIN = 'api.test.com'
            
            invalid_fingerprint = 'FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF'
            
            request = self.factory.post(
                '/v1/security/certificate/verify',
                data={'fingerprint': invalid_fingerprint, 'algorithm': 'sha256'},
                content_type='application/json'
            )
            request.client_type = 'mobile-ios'
            
            response = verify_certificate_fingerprint(request)
            
            assert response.status_code == 200
            assert response.data['valid'] is False
    
    def test_verify_certificate_fingerprint_missing_fingerprint(self):
        """Test verification endpoint with missing fingerprint."""
        request = self.factory.post(
            '/v1/security/certificate/verify',
            data={'algorithm': 'sha256'},
            content_type='application/json'
        )
        request.client_type = 'mobile-ios'
        
        response = verify_certificate_fingerprint(request)
        
        assert response.status_code == 400
        assert 'error' in response.data
        assert response.data['error']['code'] == 'MISSING_FIELD'
    
    def test_verify_certificate_fingerprint_invalid_algorithm(self):
        """Test verification endpoint with invalid algorithm."""
        request = self.factory.post(
            '/v1/security/certificate/verify',
            data={'fingerprint': 'AA:BB:CC', 'algorithm': 'md5'},
            content_type='application/json'
        )
        request.client_type = 'mobile-android'
        
        response = verify_certificate_fingerprint(request)
        
        assert response.status_code == 400
        assert 'error' in response.data
        assert response.data['error']['code'] == 'INVALID_FIELD_VALUE'
