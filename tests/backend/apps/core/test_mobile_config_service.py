"""
Unit tests for Mobile Configuration Service

Tests configuration retrieval, updates, version support checking,
and platform-specific configurations.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from apps.core.mobile_config_service import MobileConfigService


@pytest.fixture
def mock_db():
    """Mock Prisma database client"""
    db = MagicMock()
    db.connect = AsyncMock()
    db.disconnect = AsyncMock()
    return db


@pytest.fixture
def service(mock_db):
    """Create service instance with mocked database"""
    service = MobileConfigService()
    service.db = mock_db
    return service


@pytest.fixture
def sample_ios_config():
    """Sample iOS configuration"""
    return {
        'id': 'config-ios-123',
        'platform': 'ios',
        'min_version': '1.0.0',
        'config': {
            'features': {
                'push_notifications': True,
                'offline_mode': True,
                'face_id': True
            },
            'settings': {
                'max_upload_size_mb': 50,
                'cache_duration_hours': 24
            }
        },
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    }


@pytest.fixture
def sample_android_config():
    """Sample Android configuration"""
    return {
        'id': 'config-android-456',
        'platform': 'android',
        'min_version': '2.0.0',
        'config': {
            'features': {
                'push_notifications': True,
                'offline_mode': True,
                'fingerprint': True
            },
            'settings': {
                'max_upload_size_mb': 50,
                'cache_duration_hours': 24
            }
        },
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    }


class TestGetConfig:
    """Tests for get_config method"""
    
    @pytest.mark.asyncio
    async def test_get_config_ios_success(self, service, mock_db, sample_ios_config):
        """Test successful iOS configuration retrieval"""
        # Setup mock
        mock_config = MagicMock()
        mock_config.id = sample_ios_config['id']
        mock_config.platform = sample_ios_config['platform']
        mock_config.min_version = sample_ios_config['min_version']
        mock_config.config = sample_ios_config['config']
        mock_config.updated_at = sample_ios_config['updated_at']
        
        mock_db.mobileconfig.find_unique = AsyncMock(return_value=mock_config)
        
        # Execute
        result = await service.get_config('ios', '1.2.0')
        
        # Verify
        assert result['platform'] == 'ios'
        assert result['min_version'] == '1.0.0'
        assert 'features' in result['config']
        assert result['config']['features']['push_notifications'] is True
        mock_db.mobileconfig.find_unique.assert_called_once_with(
            where={'platform': 'ios'}
        )
    
    @pytest.mark.asyncio
    async def test_get_config_android_success(self, service, mock_db, sample_android_config):
        """Test successful Android configuration retrieval"""
        # Setup mock
        mock_config = MagicMock()
        mock_config.id = sample_android_config['id']
        mock_config.platform = sample_android_config['platform']
        mock_config.min_version = sample_android_config['min_version']
        mock_config.config = sample_android_config['config']
        mock_config.updated_at = sample_android_config['updated_at']
        
        mock_db.mobileconfig.find_unique = AsyncMock(return_value=mock_config)
        
        # Execute
        result = await service.get_config('android', '2.1.0')
        
        # Verify
        assert result['platform'] == 'android'
        assert result['min_version'] == '2.0.0'
        assert 'features' in result['config']
    
    @pytest.mark.asyncio
    async def test_get_config_invalid_platform(self, service, mock_db):
        """Test get_config with invalid platform"""
        with pytest.raises(ValueError, match="Invalid platform"):
            await service.get_config('windows', '1.0.0')
    
    @pytest.mark.asyncio
    async def test_get_config_unsupported_version(self, service, mock_db, sample_ios_config):
        """Test get_config with unsupported app version"""
        # Setup mock
        mock_config = MagicMock()
        mock_config.min_version = '2.0.0'
        mock_config.platform = 'ios'
        mock_config.config = {}
        mock_config.updated_at = datetime.now()
        
        mock_db.mobileconfig.find_unique = AsyncMock(return_value=mock_config)
        
        # Execute and verify
        with pytest.raises(ValueError, match="not supported"):
            await service.get_config('ios', '1.0.0')
    
    @pytest.mark.asyncio
    async def test_get_config_no_config_returns_default(self, service, mock_db):
        """Test get_config returns default when no config exists"""
        mock_db.mobileconfig.find_unique = AsyncMock(return_value=None)
        
        # Execute
        result = await service.get_config('ios', '1.0.0')
        
        # Verify default config is returned
        assert result['platform'] == 'ios'
        assert result['min_version'] == '1.0.0'
        assert 'features' in result['config']
        assert result['config']['features']['push_notifications'] is True


class TestUpdateConfig:
    """Tests for update_config method"""
    
    @pytest.mark.asyncio
    async def test_update_config_creates_new(self, service, mock_db):
        """Test update_config creates new configuration"""
        new_config = {
            'features': {'push_notifications': True},
            'settings': {'max_upload_size_mb': 100}
        }
        
        mock_result = MagicMock()
        mock_result.id = 'new-config-id'
        mock_result.platform = 'ios'
        mock_result.min_version = '1.5.0'
        mock_result.config = new_config
        mock_result.updated_at = datetime.now()
        
        mock_db.mobileconfig.upsert = AsyncMock(return_value=mock_result)
        
        # Execute
        result = await service.update_config('ios', new_config, '1.5.0')
        
        # Verify
        assert result['platform'] == 'ios'
        assert result['min_version'] == '1.5.0'
        assert result['config'] == new_config
        mock_db.mobileconfig.upsert.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_config_updates_existing(self, service, mock_db):
        """Test update_config updates existing configuration"""
        updated_config = {
            'features': {'push_notifications': False},
            'settings': {'max_upload_size_mb': 75}
        }
        
        mock_result = MagicMock()
        mock_result.id = 'existing-config-id'
        mock_result.platform = 'android'
        mock_result.min_version = '2.0.0'
        mock_result.config = updated_config
        mock_result.updated_at = datetime.now()
        
        mock_db.mobileconfig.upsert = AsyncMock(return_value=mock_result)
        
        # Execute
        result = await service.update_config('android', updated_config)
        
        # Verify
        assert result['platform'] == 'android'
        assert result['config'] == updated_config
    
    @pytest.mark.asyncio
    async def test_update_config_invalid_platform(self, service, mock_db):
        """Test update_config with invalid platform"""
        with pytest.raises(ValueError, match="Invalid platform"):
            await service.update_config('linux', {})
    
    @pytest.mark.asyncio
    async def test_update_config_without_min_version(self, service, mock_db):
        """Test update_config without specifying min_version"""
        config_data = {'features': {'test': True}}
        
        mock_result = MagicMock()
        mock_result.id = 'config-id'
        mock_result.platform = 'ios'
        mock_result.min_version = '1.0.0'
        mock_result.config = config_data
        mock_result.updated_at = datetime.now()
        
        mock_db.mobileconfig.upsert = AsyncMock(return_value=mock_result)
        
        # Execute
        result = await service.update_config('ios', config_data)
        
        # Verify default min_version is used in create
        assert result['platform'] == 'ios'
        call_args = mock_db.mobileconfig.upsert.call_args
        assert call_args[1]['data']['create']['min_version'] == '1.0.0'


class TestVersionSupport:
    """Tests for version support checking"""
    
    def test_is_version_supported_exact_match(self, service):
        """Test version support with exact version match"""
        assert service._is_version_supported('1.0.0', '1.0.0') is True
    
    def test_is_version_supported_newer_version(self, service):
        """Test version support with newer app version"""
        assert service._is_version_supported('2.0.0', '1.0.0') is True
        assert service._is_version_supported('1.5.0', '1.0.0') is True
        assert service._is_version_supported('1.0.1', '1.0.0') is True
    
    def test_is_version_supported_older_version(self, service):
        """Test version support with older app version"""
        assert service._is_version_supported('1.0.0', '2.0.0') is False
        assert service._is_version_supported('1.0.0', '1.5.0') is False
        assert service._is_version_supported('1.0.0', '1.0.1') is False
    
    def test_is_version_supported_complex_versions(self, service):
        """Test version support with complex version strings"""
        assert service._is_version_supported('1.2.3', '1.2.0') is True
        assert service._is_version_supported('2.0.0-beta', '1.9.9') is True
        assert service._is_version_supported('1.0.0', '1.0.0-rc1') is True
    
    def test_is_version_supported_invalid_version_allows_request(self, service):
        """Test that invalid version strings allow the request (fail open)"""
        # Invalid versions should return True to avoid blocking users
        assert service._is_version_supported('invalid', '1.0.0') is True
        assert service._is_version_supported('1.0.0', 'invalid') is True


class TestDefaultConfig:
    """Tests for default configuration"""
    
    def test_get_default_config_ios(self, service):
        """Test default iOS configuration"""
        config = service._get_default_config('ios')
        
        assert config['platform'] == 'ios'
        assert config['min_version'] == '1.0.0'
        assert 'features' in config['config']
        assert 'settings' in config['config']
        assert config['config']['features']['push_notifications'] is True
        assert config['config']['settings']['max_upload_size_mb'] == 50
    
    def test_get_default_config_android(self, service):
        """Test default Android configuration"""
        config = service._get_default_config('android')
        
        assert config['platform'] == 'android'
        assert config['min_version'] == '1.0.0'
        assert 'features' in config['config']
        assert 'settings' in config['config']


class TestInitializeDefaultConfigs:
    """Tests for initializing default configurations"""
    
    @pytest.mark.asyncio
    async def test_initialize_default_configs(self, service, mock_db):
        """Test initialization of default configurations"""
        mock_db.mobileconfig.upsert = AsyncMock()
        
        # Execute
        await service.initialize_default_configs()
        
        # Verify both iOS and Android configs are created
        assert mock_db.mobileconfig.upsert.call_count == 2
        
        # Check iOS config
        ios_call = mock_db.mobileconfig.upsert.call_args_list[0]
        assert ios_call[1]['where']['platform'] == 'ios'
        assert 'features' in ios_call[1]['data']['create']['config']
        
        # Check Android config
        android_call = mock_db.mobileconfig.upsert.call_args_list[1]
        assert android_call[1]['where']['platform'] == 'android'
        assert 'features' in android_call[1]['data']['create']['config']


class TestEdgeCases:
    """Tests for edge cases and error handling"""
    
    @pytest.mark.asyncio
    async def test_get_config_database_error(self, service, mock_db):
        """Test get_config handles database errors"""
        mock_db.mobileconfig.find_unique = AsyncMock(
            side_effect=Exception("Database error")
        )
        
        with pytest.raises(Exception, match="Database error"):
            await service.get_config('ios', '1.0.0')
        
        # Verify disconnect is called even on error
        mock_db.disconnect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_config_database_error(self, service, mock_db):
        """Test update_config handles database errors"""
        mock_db.mobileconfig.upsert = AsyncMock(
            side_effect=Exception("Database error")
        )
        
        with pytest.raises(Exception, match="Database error"):
            await service.update_config('ios', {})
        
        # Verify disconnect is called even on error
        mock_db.disconnect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_config_empty_version_string(self, service, mock_db):
        """Test get_config with empty version string"""
        mock_config = MagicMock()
        mock_config.platform = 'ios'
        mock_config.min_version = '1.0.0'
        mock_config.config = {}
        mock_config.updated_at = datetime.now()
        
        mock_db.mobileconfig.find_unique = AsyncMock(return_value=mock_config)
        
        # Empty version should be handled gracefully (fail open)
        result = await service.get_config('ios', '')
        assert result is not None
