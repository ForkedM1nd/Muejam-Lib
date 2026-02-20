"""
Unit tests for mobile configuration endpoints.

Tests the GET and PUT endpoints for mobile configuration management.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from rest_framework.test import APIRequestFactory, force_authenticate
from apps.core.mobile_config_views import (
    get_mobile_config,
    update_mobile_config
)


@pytest.fixture
def request_factory():
    """Create a request factory for testing."""
    return APIRequestFactory()


@pytest.fixture
def make_admin_request(request_factory):
    """Factory for authenticated admin PUT requests."""
    def _make(path, data=None):
        request = request_factory.put(path, data=data or {}, format='json')
        request.clerk_user_id = 'admin_user_123'

        mock_user = Mock()
        mock_user.is_authenticated = True
        mock_user.is_staff = True
        mock_user.is_superuser = True
        mock_user.role = 'ADMINISTRATOR'

        force_authenticate(request, user=mock_user)
        request.user_profile = Mock(id='admin_user_123', username='admin', is_admin=True)
        return request

    return _make


@pytest.fixture
def mock_config_service():
    """Create a mock MobileConfigService."""
    with patch('apps.core.mobile_config_views.MobileConfigService') as mock_service:
        service_instance = Mock()
        mock_service.return_value = service_instance
        yield service_instance


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

    def test_update_mobile_config_requires_platform_parameter(
        self, make_admin_request
    ):
        """Test that update_mobile_config requires 'platform' parameter."""
        request = make_admin_request('/v1/config/mobile', {'config': {'features': {}}})
        response = update_mobile_config(request)

        assert response.status_code == 400
        assert response.data['error']['code'] == 'MISSING_PARAMETER'
        assert 'platform' in response.data['error']['message']

    def test_update_mobile_config_validates_platform(
        self, make_admin_request
    ):
        """Test that update_mobile_config validates platform parameter."""
        request = make_admin_request(
            '/v1/config/mobile?platform=invalid',
            {'config': {'features': {}}},
        )
        response = update_mobile_config(request)

        assert response.status_code == 400
        assert response.data['error']['code'] == 'INVALID_PLATFORM'

    def test_update_mobile_config_requires_config_field(
        self, make_admin_request
    ):
        """Test that update_mobile_config requires 'config' field."""
        request = make_admin_request('/v1/config/mobile?platform=ios', {})
        response = update_mobile_config(request)

        assert response.status_code == 400
        assert response.data['error']['code'] == 'MISSING_FIELD'
        assert 'config' in response.data['error']['message']

    def test_update_mobile_config_validates_config_type(
        self, make_admin_request
    ):
        """Test that update_mobile_config validates config is a dictionary."""
        request = make_admin_request('/v1/config/mobile?platform=ios', {'config': 'not a dict'})
        response = update_mobile_config(request)

        assert response.status_code == 400
        assert response.data['error']['code'] == 'INVALID_FIELD_TYPE'

    def test_update_mobile_config_updates_ios_config(
        self, make_admin_request, mock_config_service
    ):
        """Test that update_mobile_config updates iOS configuration."""
        request_data = {
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
        request = make_admin_request('/v1/config/mobile?platform=ios', request_data)
        
        # Mock service response
        mock_updated_config = {
            'id': 'config_123',
            'platform': 'ios',
            'min_version': '1.5.0',
            'config': request_data['config'],
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

    def test_update_mobile_config_updates_android_config(
        self, make_admin_request, mock_config_service
    ):
        """Test that update_mobile_config updates Android configuration."""
        request_data = {
            'config': {
                'features': {
                    'push_notifications': True,
                    'material_design': True
                }
            }
        }
        request = make_admin_request('/v1/config/mobile?platform=android', request_data)
        
        # Mock service response
        mock_updated_config = {
            'id': 'config_456',
            'platform': 'android',
            'min_version': '1.0.0',
            'config': request_data['config'],
            'updated_at': datetime.now().isoformat()
        }
        mock_config_service.update_config = AsyncMock(
            return_value=mock_updated_config
        )

        response = update_mobile_config(request)

        assert response.status_code == 200
        assert response.data['platform'] == 'android'

    def test_update_mobile_config_allows_optional_min_version(
        self, make_admin_request, mock_config_service
    ):
        """Test that update_mobile_config allows optional min_version."""
        request_data = {
            'config': {
                'features': {'push_notifications': True}
            }
            # No min_version provided
        }
        request = make_admin_request('/v1/config/mobile?platform=ios', request_data)
        
        mock_updated_config = {
            'id': 'config_123',
            'platform': 'ios',
            'min_version': '1.0.0',  # Existing version maintained
            'config': request_data['config'],
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

    def test_get_and_update_config_workflow(
        self, request_factory, make_admin_request, mock_config_service
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
        put_payload = {
            'config': {
                'features': {'push_notifications': True}
            }
        }
        put_request = make_admin_request('/v1/config/mobile?platform=ios', put_payload)
        
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
