"""
Property-based tests for Mobile Configuration Service

Tests universal properties that should hold across all valid inputs.
Uses Hypothesis for property-based testing.
"""

import pytest
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from apps.core.mobile_config_service import MobileConfigService


# Strategies for generating test data
platforms = st.sampled_from(['ios', 'android'])
invalid_platforms = st.text().filter(lambda x: x not in ['ios', 'android'])
# Use ASCII digits only for version strings
version_strings = st.from_regex(r'^[0-9]+\.[0-9]+\.[0-9]+$', fullmatch=True)
config_dicts = st.fixed_dictionaries({
    'features': st.dictionaries(
        st.text(min_size=1, max_size=20),
        st.booleans()
    ),
    'settings': st.dictionaries(
        st.text(min_size=1, max_size=20),
        st.one_of(st.integers(min_value=1), st.floats(min_value=0.1, max_value=1.0))
    )
})


@pytest.fixture
def service():
    """Create service instance with mocked database"""
    service = MobileConfigService()
    db = MagicMock()
    db.connect = AsyncMock()
    db.disconnect = AsyncMock()
    service.db = db
    return service


class TestProperty28ConfigurationCacheHeaders:
    """
    Feature: mobile-backend-integration, Property 28: Configuration Cache Headers
    
    **Validates: Requirements 16.4**
    
    For any mobile configuration response, appropriate cache-control headers 
    SHALL be present to enable client-side caching.
    
    Note: This property is tested at the API endpoint level, not service level.
    The service provides the data; the view/middleware adds cache headers.
    """
    pass


class TestConfigurationRetrievalByPlatform:
    """
    Tests for configuration retrieval by platform (Requirement 16.1, 16.2, 16.5)
    
    Property: For any valid platform (ios/android), configuration retrieval 
    SHALL return platform-specific settings.
    """
    
    @given(platform=platforms, app_version=version_strings)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_valid_platform_returns_config(self, service, platform, app_version):
        """
        Property: Valid platform requests return configuration
        
        For any valid platform and version, get_config SHALL return a 
        configuration dictionary with required fields.
        """
        # Setup mock - use version 0.0.0 as min_version to accept all test versions
        mock_config = MagicMock()
        mock_config.id = f'config-{platform}-123'
        mock_config.platform = platform
        mock_config.min_version = '0.0.0'  # Accept all versions
        mock_config.config = {
            'features': {'test': True},
            'settings': {'value': 42}
        }
        mock_config.updated_at = datetime.now()
        
        service.db.mobileconfig.find_unique = AsyncMock(return_value=mock_config)
        
        # Execute
        result = await service.get_config(platform, app_version)
        
        # Verify required fields are present
        assert 'platform' in result
        assert 'min_version' in result
        assert 'config' in result
        assert 'updated_at' in result
        assert result['platform'] == platform
    
    @given(platform=invalid_platforms)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_invalid_platform_raises_error(self, service, platform):
        """
        Property: Invalid platform requests are rejected
        
        For any platform not in ['ios', 'android'], get_config SHALL 
        raise ValueError.
        """
        assume(len(platform) > 0)  # Skip empty strings
        
        with pytest.raises(ValueError, match="Invalid platform"):
            await service.get_config(platform, '1.0.0')
    
    @given(platform=platforms, config_data=config_dicts)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_platform_specific_config_isolation(self, service, platform, config_data):
        """
        Property: Platform configurations are isolated
        
        For any platform, updating its configuration SHALL not affect 
        the other platform's configuration.
        """
        # Setup mock
        mock_result = MagicMock()
        mock_result.id = f'config-{platform}-123'
        mock_result.platform = platform
        mock_result.min_version = '1.0.0'
        mock_result.config = config_data
        mock_result.updated_at = datetime.now()
        
        service.db.mobileconfig.upsert = AsyncMock(return_value=mock_result)
        
        # Execute
        result = await service.update_config(platform, config_data)
        
        # Verify the update is for the correct platform only
        assert result['platform'] == platform
        assert result['config'] == config_data
        
        # Verify upsert was called with correct platform
        call_args = service.db.mobileconfig.upsert.call_args
        assert call_args[1]['where']['platform'] == platform


class TestConfigurationUpdates:
    """
    Tests for configuration updates (Requirement 16.2)
    
    Property: Configuration updates SHALL persist and be retrievable.
    """
    
    @given(platform=platforms, config_data=config_dicts, min_version=version_strings)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_update_config_round_trip(self, service, platform, config_data, min_version):
        """
        Property: Configuration update round-trip consistency
        
        For any valid platform and configuration data, updating the config 
        SHALL return the same data that was provided.
        """
        # Setup mock
        mock_result = MagicMock()
        mock_result.id = f'config-{platform}-123'
        mock_result.platform = platform
        mock_result.min_version = min_version
        mock_result.config = config_data
        mock_result.updated_at = datetime.now()
        
        service.db.mobileconfig.upsert = AsyncMock(return_value=mock_result)
        
        # Execute
        result = await service.update_config(platform, config_data, min_version)
        
        # Verify round-trip consistency
        assert result['platform'] == platform
        assert result['min_version'] == min_version
        assert result['config'] == config_data
    
    @given(platform=invalid_platforms, config_data=config_dicts)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_update_invalid_platform_rejected(self, service, platform, config_data):
        """
        Property: Invalid platform updates are rejected
        
        For any invalid platform, update_config SHALL raise ValueError.
        """
        assume(len(platform) > 0)  # Skip empty strings
        
        with pytest.raises(ValueError, match="Invalid platform"):
            await service.update_config(platform, config_data)


class TestVersionSupportChecking:
    """
    Tests for version support checking (Requirement 16.3)
    
    Property: Version comparison SHALL be transitive and consistent.
    """
    
    @given(
        app_version=version_strings,
        min_version=version_strings
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_version_comparison_consistency(self, service, app_version, min_version):
        """
        Property: Version comparison is consistent
        
        For any two versions A and B:
        - If A >= B, then _is_version_supported(A, B) is True
        - If A < B, then _is_version_supported(A, B) is False
        """
        result = service._is_version_supported(app_version, min_version)
        
        # Parse versions for comparison
        from packaging import version
        app_v = version.parse(app_version)
        min_v = version.parse(min_version)
        
        if app_v >= min_v:
            assert result is True, f"{app_version} >= {min_version} should be supported"
        else:
            assert result is False, f"{app_version} < {min_version} should not be supported"
    
    @given(version_str=version_strings)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_version_reflexivity(self, service, version_str):
        """
        Property: Version comparison is reflexive
        
        For any version V, _is_version_supported(V, V) SHALL be True.
        """
        result = service._is_version_supported(version_str, version_str)
        assert result is True, f"Version {version_str} should support itself"
    
    @given(
        v1=version_strings,
        v2=version_strings,
        v3=version_strings
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_version_transitivity(self, service, v1, v2, v3):
        """
        Property: Version comparison is transitive
        
        For any versions A, B, C:
        If A >= B and B >= C, then A >= C
        """
        from packaging import version
        
        a = version.parse(v1)
        b = version.parse(v2)
        c = version.parse(v3)
        
        # Only test when transitivity applies
        if a >= b and b >= c:
            # Then A should be >= C
            result = service._is_version_supported(v1, v3)
            assert result is True, f"Transitivity: {v1} >= {v2} >= {v3}, so {v1} >= {v3}"
    
    @given(platform=platforms)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=1000)
    @pytest.mark.asyncio
    async def test_unsupported_version_rejected(self, service, platform):
        """
        Property: Unsupported versions are rejected
        
        For any app version less than min_version, get_config SHALL 
        raise ValueError.
        """
        # Setup mock with higher min_version
        mock_config = MagicMock()
        mock_config.platform = platform
        mock_config.min_version = '99.99.99'  # Very high version
        mock_config.config = {}
        mock_config.updated_at = datetime.now()
        
        service.db.mobileconfig.find_unique = AsyncMock(return_value=mock_config)
        
        # Execute and verify rejection with a version that's definitely lower
        with pytest.raises(ValueError, match="not supported"):
            await service.get_config(platform, '1.0.0')


class TestDefaultConfiguration:
    """
    Tests for default configuration behavior
    
    Property: When no configuration exists, default SHALL be provided.
    """
    
    @given(platform=platforms, app_version=version_strings)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_missing_config_returns_default(self, service, platform, app_version):
        """
        Property: Missing configuration returns valid default
        
        For any valid platform when no config exists, get_config SHALL 
        return a valid default configuration.
        """
        # Setup mock to return None (no config)
        service.db.mobileconfig.find_unique = AsyncMock(return_value=None)
        
        # Execute
        result = await service.get_config(platform, app_version)
        
        # Verify default config structure
        assert result['platform'] == platform
        assert 'config' in result
        assert 'features' in result['config']
        assert 'settings' in result['config']
        assert result['min_version'] == '1.0.0'
    
    @given(platform=platforms)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_default_config_structure(self, service, platform):
        """
        Property: Default configuration has required structure
        
        For any valid platform, _get_default_config SHALL return a 
        configuration with all required fields.
        """
        config = service._get_default_config(platform)
        
        # Verify structure
        assert config['platform'] == platform
        assert 'min_version' in config
        assert 'config' in config
        assert 'features' in config['config']
        assert 'settings' in config['config']
        
        # Verify essential features are present
        assert 'push_notifications' in config['config']['features']
        assert 'offline_mode' in config['config']['features']
        assert 'max_upload_size_mb' in config['config']['settings']


class TestErrorHandling:
    """
    Tests for error handling and edge cases
    
    Property: Invalid inputs SHALL be rejected with clear errors.
    """
    
    @given(
        invalid_version=st.text().filter(
            lambda x: not x or not any(c.isdigit() for c in x)
        )
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_invalid_version_fails_gracefully(self, service, invalid_version):
        """
        Property: Invalid version strings fail gracefully
        
        For any invalid version string, _is_version_supported SHALL 
        return True (fail open) to avoid blocking users.
        """
        assume(len(invalid_version) > 0)
        
        # Invalid versions should fail open (return True)
        result = service._is_version_supported(invalid_version, '1.0.0')
        assert result is True, "Invalid versions should fail open"
    
    @given(platform=platforms)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_database_disconnect_on_error(self, service, platform):
        """
        Property: Database is disconnected even on errors
        
        For any operation that raises an exception, the database 
        connection SHALL be properly closed.
        """
        # Reset mock call count for this example
        service.db.disconnect.reset_mock()
        
        # Setup mock to raise error
        service.db.mobileconfig.find_unique = AsyncMock(
            side_effect=Exception("Database error")
        )
        
        # Execute and catch error
        with pytest.raises(Exception):
            await service.get_config(platform, '1.0.0')
        
        # Verify disconnect was called
        assert service.db.disconnect.call_count >= 1, "Database should be disconnected on error"
