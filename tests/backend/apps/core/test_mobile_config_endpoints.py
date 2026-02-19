"""
Unit tests for mobile configuration endpoints.

Tests the GET and PUT endpoints for mobile configuration management.
"""

import pytest
from datetime import datetime
from django.test import RequestFactory
from unittest.mock import Mock, patch, AsyncMock
from apps.core.mobile_config_views import (
    get_mobile_config,
    update_mobile_config
)


@pytest.fixture
def request_factory():
    """Create a request factory for testing."""
    return RequestFactory()


@pytest.fixture
def authenticated_admin_request(request_factory):
    """Create an authenticated admin request."""
    request = request_factory.put('/v1/config/mobile')
    request.clerk_user_id = 'admin_user_123'
    
    # Mock user with admin permissions
    mock_user = Mock()
    mock_user.is_authenticated = True
    mock_user.is_staff = True
    mock_user.is_superuser = True
    request.user = mock_user
    
    request.user_profile = Mock(
        id='admin_user_123',
        username='admin',
        is_admin=True
    )
    return request


@pytest.fixture
def mock_config_service():
    """Create a mock MobileConfigService."""
    with patch('apps.core.mobile_config_views.MobileConfigService') as mock_service:
        service_instance = Mock()
        mock_service.return_value = service_instance
        yield service_instance


@pytest.fixture
def mock_admin_permission():
    """Mock the IsAdministrator permission to always allow access."""
    with patch('apps.core.mobile_config_views.IsAdministrator') as mock_perm:
        mock_perm_instance = Mock()
        mock_perm_instance.has_permission.return_value = True
        mock_perm.return_value = mock_perm_instance
        yield mock_perm


class TestGetMobileConfig:
    """Test get_mobile_config endpoint."""
    
    def test_get_mobile_config_requires_platform_parameter(
        self, request_factory
    ):
        """Test that get_mobile_config requires 'platform' parameter."""
        request = request_factory.get('/v1/config/mobile')
        
        response = get_mobile_config(request)
        
        assert response.status_code == 400
        assert response.data['error']['code'] == 'MISSING_PARAMETER'
        assert 'platform' in response.data['error']['message']
    
    def test_get_mobile_config_requires_version_parameter(
        self, request_factory
    ):
        """Test that get_mobile_config requires 'version' parameter."""
        request = request_factory.get('/v1/config/mobile?platform=ios')
        
        response = get_mobile_config(request)
        
        assert response.status_code == 400
        assert response.data['error']['code'] == 'MISSING_PARAMETER'
        assert 'version' in response.data['error']['message']
    
    def test_get_mobile_config_validates_platform(
        self, request_factory
    ):
        """Test that get_mobile_config validates platform parameter."""
        request = request_factory.get(
            '/v1/config/mobile?platform=invalid&version=1.0.0'
        )
        
        response = get_mobile_config(request)
        
        assert response.status_code == 400
        assert response.data['error']['code'] == 'INVALID_PLATFORM'
    
    def test_get_mobile_config_returns_ios_config(
        self, request_factory, mock_config_service
    ):
        """Test that get_mobile_config returns iOS configuration."""
        request = request_factory.get(
            '/v1/config/mobile?platform=ios&version=1.2.3'
        )
        
        # Mock service response
        mock_config = {
            'id': 'config_123',
            'platform': 'ios',
            'min_version': '1.0.0',
            'config': {
                'features': {
                    'push_notifications': True,
                    'offline_mode': True,
                    'face_id': True
                },
                'settings': {
                    'max_upload_size_mb': 50
                }
            },
            'updated_at': datetime.now().isoformat()
        }
        mock_config_service.get_config = AsyncMock(return_value=mock_config)
        
        response = get_mobile_config(request)
        
        assert response.status_code == 200
        assert response.data['platform'] == 'ios'
        assert 'features' in response.data['config']
        assert 'Cache-Control' in response
        assert 'ETag' in response
    
    def test_get_mobile_config_returns_android_config(
        self, request_factory, mock_config_service
    ):
        """Test that get_mobile_config returns Android configuration."""
        request = request_factory.get(
            '/v1/config/mobile?platform=android&version=1.2.3'
        )
        
        # Mock service response
        mock_config = {
            'id': 'config_456',
            'platform': 'android',
            'min_version': '1.0.0',
            'config': {
                'features': {
                    'push_notifications': True,
                    'offline_mode': True,
                    'fingerprint': True
                },
                'settings': {
                    'max_upload_size_mb': 50
                }
            },
            'updated_at': datetime.now().isoformat()
        }
        mock_config_service.get_config = AsyncMock(return_value=mock_config)
        
        response = get_mobile_config(request)
        
        assert response.status_code == 200
        assert response.data['platform'] == 'android'
        assert 'features' in response.data['config']
    
    def test_get_mobile_config_rejects_unsupported_version(
        self, request_factory, mock_config_service
    ):
        """Test that get_mobile_config rejects unsupported app versions."""
        request = request_factory.get(
            '/v1/config/mobile?platform=ios&version=0.5.0'
        )
        
        # Mock service to raise ValueError for unsupported version
        mock_config_service.get_config = AsyncMock(
            side_effect=ValueError(
                'App version 0.5.0 is not supported. Minimum version required: 1.0.0'
            )
        )
        
        response = get_mobile_config(request)
        
        assert response.status_code == 403
        assert response.data['error']['code'] == 'VERSION_NOT_SUPPORTED'
    
    def test_get_mobile_config_includes_cache_headers(
        self, request_factory, mock_config_service
    ):
        """Test that get_mobile_config includes appropriate cache headers."""
        request = request_factory.get(
            '/v1/config/mobile?platform=ios&version=1.2.3'
        )
        
        mock_config = {
            'id': 'config_123',
            'platform': 'ios',
            'min_version': '1.0.0',
            'config': {'features': {}},
            'updated_at': '2024-01-01T00:00:00'
        }
        mock_config_service.get_config = AsyncMock(return_value=mock_config)
        
        response = get_mobile_config(request)
        
        assert response.status_code == 200
        assert 'Cache-Control' in response
        assert 'public' in response['Cache-Control']
        assert 'max-age=3600' in response['Cache-Control']
        assert 'ETag' in response


class TestUpdateMobileConfig:
    """Test update_mobile_config endpoint."""
    
    @patch('rest_framework.decorators.permission_classes', lambda x: lambda f: f)
    def test_update_mobile_config_requires_platform_parameter(
        self, authenticated_admin_request
    ):
        """Test that update_mobile_config requires 'platform' parameter."""
        authenticated_admin_request.data = {
            'config': {'features': {}}
        }
        
        response = update_mobile_config(authenticated_admin_request)
        
        assert response.status_code == 400
        assert response.data['error']['code'] == 'MISSING_PARAMETER'
        assert 'platform' in response.data['error']['message']
    
    @patch('rest_framework.decorators.permission_classes', lambda x: lambda f: f)
    def test_update_mobile_config_validates_platform(
        self, request_factory
    ):
        """Test that update_mobile_config validates platform parameter."""
        request = request_factory.put(
            '/v1/config/mobile?platform=invalid'
        )
        request.clerk_user_id = 'admin_user_123'
        request.data = {'config': {'features': {}}}
        
        # Mock user with admin permissions
        mock_user = Mock()
        mock_user.is_authenticated = True
        mock_user.is_staff = True
        request.user = mock_user
        
        response = update_mobile_config(request)
        
        assert response.status_code == 400
        assert response.data['error']['code'] == 'INVALID_PLATFORM'
    
    @patch('rest_framework.decorators.permission_classes', lambda x: lambda f: f)
    def test_update_mobile_config_requires_config_field(
        self, request_factory
    ):
        """Test that update_mobile_config requires 'config' field."""
        request = request_factory.put(
            '/v1/config/mobile?platform=ios'
        )
        request.clerk_user_id = 'admin_user_123'
        request.data = {}
        
        # Mock user with admin permissions
        mock_user = Mock()
        mock_user.is_authenticated = True
        mock_user.is_staff = True
        request.user = mock_user
        
        response = update_mobile_config(request)
        
        assert response.status_code == 400
        assert response.data['error']['code'] == 'MISSING_FIELD'
        assert 'config' in response.data['error']['message']
    
    @patch('rest_framework.decorators.permission_classes', lambda x: lambda f: f)
    def test_update_mobile_config_validates_config_type(
        self, request_factory
    ):
        """Test that update_mobile_config validates config is a dictionary."""
        request = request_factory.put(
            '/v1/config/mobile?platform=ios'
        )
        request.clerk_user_id = 'admin_user_123'
        request.data = {'config': 'not a dict'}
        
        # Mock user with admin permissions
        mock_user = Mock()
        mock_user.is_authenticated = True
        mock_user.is_staff = True
        request.user = mock_user
        
        response = update_mobile_config(request)
        
        assert response.status_code == 400
        assert response.data['error']['code'] == 'INVALID_FIELD_TYPE'
    
    @patch('rest_framework.decorators.permission_classes', lambda x: lambda f: f)
    def test_update_mobile_config_updates_ios_config(
        self, request_factory, mock_config_service
    ):
        """Test that update_mobile_config updates iOS configuration."""
        request = request_factory.put(
            '/v1/config/mobile?platform=ios'
        )
        request.clerk_user_id = 'admin_user_123'
        request.data = {
            'config': {
                'features': {
                    'push_notifications': True,
                    'offline_mode': False
                },
                'settings': {
                    'max_upload_size_mb': 100
                }
            },
            'min_version': '1.5.0'
        }
        
        # Mock user with admin permissions
        mock_user = Mock()
        mock_user.is_authenticated = True
        mock_user.is_staff = True
        request.user = mock_user
        
        # Mock service response
        mock_updated_config = {
            'id': 'config_123',
            'platform': 'ios',
            'min_version': '1.5.0',
            'config': request.data['config'],
            'updated_at': datetime.now().isoformat()
        }
        mock_config_service.update_config = AsyncMock(
            return_value=mock_updated_config
        )
        
        response = update_mobile_config(request)
        
        assert response.status_code == 200
        assert response.data['platform'] == 'ios'
        assert response.data['min_version'] == '1.5.0'
        assert response.data['config']['settings']['max_upload_size_mb'] == 100
    
    @patch('rest_framework.decorators.permission_classes', lambda x: lambda f: f)
    def test_update_mobile_config_updates_android_config(
        self, request_factory, mock_config_service
    ):
        """Test that update_mobile_config updates Android configuration."""
        request = request_factory.put(
            '/v1/config/mobile?platform=android'
        )
        request.clerk_user_id = 'admin_user_123'
        request.data = {
            'config': {
                'features': {
                    'push_notifications': True,
                    'material_design': True
                }
            }
        }
        
        # Mock user with admin permissions
        mock_user = Mock()
        mock_user.is_authenticated = True
        mock_user.is_staff = True
        request.user = mock_user
        
        # Mock service response
        mock_updated_config = {
            'id': 'config_456',
            'platform': 'android',
            'min_version': '1.0.0',
            'config': request.data['config'],
            'updated_at': datetime.now().isoformat()
        }
        mock_config_service.update_config = AsyncMock(
            return_value=mock_updated_config
        )
        
        response = update_mobile_config(request)
        
        assert response.status_code == 200
        assert response.data['platform'] == 'android'
    
    @patch('rest_framework.decorators.permission_classes', lambda x: lambda f: f)
    def test_update_mobile_config_allows_optional_min_version(
        self, request_factory, mock_config_service
    ):
        """Test that update_mobile_config allows optional min_version."""
        request = request_factory.put(
            '/v1/config/mobile?platform=ios'
        )
        request.clerk_user_id = 'admin_user_123'
        request.data = {
            'config': {
                'features': {'push_notifications': True}
            }
            # No min_version provided
        }
        
        # Mock user with admin permissions
        mock_user = Mock()
        mock_user.is_authenticated = True
        mock_user.is_staff = True
        request.user = mock_user
        
        mock_updated_config = {
            'id': 'config_123',
            'platform': 'ios',
            'min_version': '1.0.0',  # Existing version maintained
            'config': request.data['config'],
            'updated_at': datetime.now().isoformat()
        }
        mock_config_service.update_config = AsyncMock(
            return_value=mock_updated_config
        )
        
        response = update_mobile_config(request)
        
        assert response.status_code == 200
        # Verify service was called with None for min_version
        mock_config_service.update_config.assert_called_once()
        call_args = mock_config_service.update_config.call_args
        assert call_args.kwargs['min_version'] is None


class TestMobileConfigEndpointsIntegration:
    """Integration tests for mobile config endpoints."""
    
    @patch('rest_framework.decorators.permission_classes', lambda x: lambda f: f)
    def test_get_and_update_config_workflow(
        self, request_factory, mock_config_service
    ):
        """Test complete workflow of getting and updating config."""
        # First, get the current config
        get_request = request_factory.get(
            '/v1/config/mobile?platform=ios&version=1.0.0'
        )
        
        initial_config = {
            'id': 'config_123',
            'platform': 'ios',
            'min_version': '1.0.0',
            'config': {
                'features': {'push_notifications': False}
            },
            'updated_at': datetime.now().isoformat()
        }
        mock_config_service.get_config = AsyncMock(return_value=initial_config)
        
        get_response = get_mobile_config(get_request)
        assert get_response.status_code == 200
        assert get_response.data['config']['features']['push_notifications'] is False
        
        # Then, update the config
        put_request = request_factory.put(
            '/v1/config/mobile?platform=ios'
        )
        put_request.clerk_user_id = 'admin_user_123'
        put_request.data = {
            'config': {
                'features': {'push_notifications': True}
            }
        }
        
        # Mock user with admin permissions
        mock_user = Mock()
        mock_user.is_authenticated = True
        mock_user.is_staff = True
        put_request.user = mock_user
        
        updated_config = {
            'id': 'config_123',
            'platform': 'ios',
            'min_version': '1.0.0',
            'config': {
                'features': {'push_notifications': True}
            },
            'updated_at': datetime.now().isoformat()
        }
        mock_config_service.update_config = AsyncMock(return_value=updated_config)
        
        put_response = update_mobile_config(put_request)
        assert put_response.status_code == 200
        assert put_response.data['config']['features']['push_notifications'] is True
