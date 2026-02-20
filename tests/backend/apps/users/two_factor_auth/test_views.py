"""
Tests for Two-Factor Authentication API endpoints.

Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.7, 7.8
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status
from apps.users.two_factor_auth import views


@pytest.fixture
def factory():
    """Create an API request factory."""
    return APIRequestFactory()


@pytest.fixture
def mock_clerk_user():
    """Create a mock Clerk user."""
    mock_user = MagicMock()
    mock_user.id = "test-user-123"
    mock_user.primary_email_address_id = "email-123"
    
    mock_email = MagicMock()
    mock_email.id = "email-123"
    mock_email.email_address = "test@example.com"
    mock_user.email_addresses = [mock_email]
    
    return mock_user


def create_authenticated_request(factory, method, path, data=None):
    """Helper to create an authenticated request with clerk_user_id."""
    if method == 'GET':
        request = factory.get(path)
    elif method == 'POST':
        request = factory.post(path, data, format='json')
    elif method == 'DELETE':
        request = factory.delete(path)
    else:
        raise ValueError(f"Unsupported method: {method}")
    
    # Mock authentication middleware attributes
    request.clerk_user_id = "test-user-123"
    request.user_profile = MagicMock(id="test-user-123")
    request.auth_error = None

    user = MagicMock()
    user.is_authenticated = True
    force_authenticate(request, user=user)
    
    return request


class TestSetup2FA:
    """Tests for POST /api/auth/2fa/setup endpoint."""
    
    @patch('apps.users.two_factor_auth.views.clerk')
    @patch('apps.users.two_factor_auth.views.TwoFactorAuthService')
    def test_setup_2fa_success(self, mock_service_class, mock_clerk, factory, mock_clerk_user):
        """Test successful 2FA setup initialization."""
        mock_clerk.users.get.return_value = mock_clerk_user
        
        mock_service = MagicMock()
        mock_service.has_2fa_enabled = AsyncMock(return_value=False)
        mock_service.setup_2fa = AsyncMock(return_value={
            'secret': 'JBSWY3DPEHPK3PXP',
            'qr_code': 'base64encodedqrcode',
            'backup_codes': ['CODE1234', 'CODE5678']
        })
        mock_service_class.return_value = mock_service
        
        request = create_authenticated_request(factory, 'POST', '/v1/users/2fa/setup')
        response = views.setup_2fa(request)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'secret' in response.data
        assert 'qr_code' in response.data
        assert 'backup_codes' in response.data
    
    @patch('apps.users.two_factor_auth.views.clerk')
    @patch('apps.users.two_factor_auth.views.TwoFactorAuthService')
    def test_setup_2fa_already_enabled(self, mock_service_class, mock_clerk, factory, mock_clerk_user):
        """Test setup fails when 2FA is already enabled."""
        mock_clerk.users.get.return_value = mock_clerk_user
        
        mock_service = MagicMock()
        mock_service.has_2fa_enabled = AsyncMock(return_value=True)
        mock_service_class.return_value = mock_service
        
        request = create_authenticated_request(factory, 'POST', '/v1/users/2fa/setup')
        response = views.setup_2fa(request)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestVerifySetup2FA:
    """Tests for POST /api/auth/2fa/verify-setup endpoint."""
    
    @patch('apps.users.two_factor_auth.views.TwoFactorAuthService')
    def test_verify_setup_success(self, mock_service_class, factory):
        """Test successful 2FA setup verification."""
        mock_service = MagicMock()
        mock_service.verify_2fa_setup = AsyncMock(return_value=True)
        mock_service_class.return_value = mock_service
        
        request = create_authenticated_request(factory, 'POST', '/v1/users/2fa/verify-setup', {'token': '123456'})
        response = views.verify_setup_2fa(request)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['enabled'] is True
    
    @patch('apps.users.two_factor_auth.views.TwoFactorAuthService')
    def test_verify_setup_invalid_token(self, mock_service_class, factory):
        """Test verification fails with invalid token."""
        mock_service = MagicMock()
        mock_service.verify_2fa_setup = AsyncMock(return_value=False)
        mock_service_class.return_value = mock_service
        
        request = create_authenticated_request(factory, 'POST', '/v1/users/2fa/verify-setup', {'token': '999999'})
        response = views.verify_setup_2fa(request)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_verify_setup_missing_token(self, factory):
        """Test verification fails without token."""
        request = create_authenticated_request(factory, 'POST', '/v1/users/2fa/verify-setup', {})
        response = views.verify_setup_2fa(request)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestVerify2FA:
    """Tests for POST /api/auth/2fa/verify endpoint."""
    
    @patch('apps.users.two_factor_auth.views.TwoFactorAuthService')
    def test_verify_2fa_success(self, mock_service_class, factory):
        """Test successful 2FA verification during login."""
        mock_service = MagicMock()
        mock_service.has_2fa_enabled = AsyncMock(return_value=True)
        mock_service.verify_totp = AsyncMock(return_value=True)
        mock_service_class.return_value = mock_service
        
        request = create_authenticated_request(factory, 'POST', '/v1/users/2fa/verify', {'token': '123456'})
        response = views.verify_2fa(request)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['verified'] is True
    
    @patch('apps.users.two_factor_auth.views.TwoFactorAuthService')
    def test_verify_2fa_not_enabled(self, mock_service_class, factory):
        """Test verification fails when 2FA is not enabled."""
        mock_service = MagicMock()
        mock_service.has_2fa_enabled = AsyncMock(return_value=False)
        mock_service_class.return_value = mock_service
        
        request = create_authenticated_request(factory, 'POST', '/v1/users/2fa/verify', {'token': '123456'})
        response = views.verify_2fa(request)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestVerifyBackupCode:
    """Tests for POST /api/auth/2fa/backup-code endpoint."""
    
    @patch('apps.users.two_factor_auth.views.TwoFactorAuthService')
    def test_verify_backup_code_success(self, mock_service_class, factory):
        """Test successful backup code verification."""
        mock_service = MagicMock()
        mock_service.has_2fa_enabled = AsyncMock(return_value=True)
        mock_service.verify_backup_code = AsyncMock(return_value=(True, 9))
        mock_service_class.return_value = mock_service
        
        request = create_authenticated_request(factory, 'POST', '/v1/users/2fa/backup-code', {'code': 'ABCD1234'})
        response = views.verify_backup_code(request)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['verified'] is True
        assert response.data['remaining_codes'] == 9
    
    @patch('apps.users.two_factor_auth.views.TwoFactorAuthService')
    def test_verify_backup_code_invalid(self, mock_service_class, factory):
        """Test verification fails with invalid backup code."""
        mock_service = MagicMock()
        mock_service.has_2fa_enabled = AsyncMock(return_value=True)
        mock_service.verify_backup_code = AsyncMock(return_value=(False, None))
        mock_service_class.return_value = mock_service
        
        request = create_authenticated_request(factory, 'POST', '/v1/users/2fa/backup-code', {'code': 'INVALID1'})
        response = views.verify_backup_code(request)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestDisable2FA:
    """Tests for DELETE /api/auth/2fa endpoint."""
    
    @patch('apps.users.two_factor_auth.views.TwoFactorAuthService')
    def test_disable_2fa_success(self, mock_service_class, factory):
        """Test successful 2FA disabling."""
        mock_service = MagicMock()
        mock_service.has_2fa_enabled = AsyncMock(return_value=True)
        mock_service.disable_2fa = AsyncMock(return_value=True)
        mock_service_class.return_value = mock_service
        
        request = create_authenticated_request(factory, 'DELETE', '/v1/users/2fa/')
        response = views.disable_2fa(request)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['disabled'] is True
    
    @patch('apps.users.two_factor_auth.views.TwoFactorAuthService')
    def test_disable_2fa_not_enabled(self, mock_service_class, factory):
        """Test disabling fails when 2FA is not enabled."""
        mock_service = MagicMock()
        mock_service.has_2fa_enabled = AsyncMock(return_value=False)
        mock_service_class.return_value = mock_service
        
        request = create_authenticated_request(factory, 'DELETE', '/v1/users/2fa/')
        response = views.disable_2fa(request)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestRegenerateBackupCodes:
    """Tests for POST /api/auth/2fa/regenerate-backup-codes endpoint."""
    
    @patch('apps.users.two_factor_auth.views.TwoFactorAuthService')
    def test_regenerate_backup_codes_success(self, mock_service_class, factory):
        """Test successful backup codes regeneration."""
        mock_service = MagicMock()
        mock_service.has_2fa_enabled = AsyncMock(return_value=True)
        mock_service.regenerate_backup_codes = AsyncMock(return_value=[
            'NEW12345', 'NEW67890', 'NEW11111', 'NEW22222', 'NEW33333',
            'NEW44444', 'NEW55555', 'NEW66666', 'NEW77777', 'NEW88888'
        ])
        mock_service_class.return_value = mock_service
        
        request = create_authenticated_request(factory, 'POST', '/v1/users/2fa/regenerate-backup-codes')
        response = views.regenerate_backup_codes(request)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['backup_codes']) == 10
    
    @patch('apps.users.two_factor_auth.views.TwoFactorAuthService')
    def test_regenerate_backup_codes_not_enabled(self, mock_service_class, factory):
        """Test regeneration fails when 2FA is not enabled."""
        mock_service = MagicMock()
        mock_service.has_2fa_enabled = AsyncMock(return_value=False)
        mock_service_class.return_value = mock_service
        
        request = create_authenticated_request(factory, 'POST', '/v1/users/2fa/regenerate-backup-codes')
        response = views.regenerate_backup_codes(request)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
