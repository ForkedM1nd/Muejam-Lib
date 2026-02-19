"""
Mobile Configuration Service

Manages mobile app configuration including feature flags, settings,
and version support checking for iOS and Android platforms.

Requirements:
- 16.1: Provide endpoints for mobile clients to retrieve feature flags
- 16.2: Provide endpoints for mobile clients to retrieve app configuration settings
- 16.3: Support versioned configuration retrieval
- 16.5: Allow different configurations per platform (iOS vs Android)
"""

import logging
from typing import Dict, Any, Optional
from packaging import version
from prisma import Prisma

logger = logging.getLogger(__name__)


class MobileConfigService:
    """Service for managing mobile app configuration"""
    
    def __init__(self):
        self.db = Prisma()
    
    async def get_config(self, platform: str, app_version: str) -> Dict[str, Any]:
        """
        Get mobile configuration for platform and version.
        
        Args:
            platform: 'ios' or 'android'
            app_version: App version string (e.g., '1.2.3')
            
        Returns:
            Configuration dictionary with feature flags and settings
            
        Raises:
            ValueError: If platform is invalid or version is not supported
        """
        if platform not in ['ios', 'android']:
            raise ValueError(f"Invalid platform: {platform}. Must be 'ios' or 'android'")
        
        await self.db.connect()
        try:
            config = await self.db.mobileconfig.find_unique(
                where={'platform': platform}
            )
            
            if not config:
                logger.warning(f"No configuration found for platform: {platform}")
                return self._get_default_config(platform)
            
            # Check version support
            if not self._is_version_supported(app_version, config.min_version):
                raise ValueError(
                    f"App version {app_version} is not supported. "
                    f"Minimum version required: {config.min_version}"
                )
            
            return {
                'id': config.id,
                'platform': config.platform,
                'min_version': config.min_version,
                'config': config.config,
                'updated_at': config.updated_at.isoformat()
            }
        finally:
            await self.db.disconnect()
    
    async def update_config(
        self,
        platform: str,
        config_data: Dict[str, Any],
        min_version: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update mobile configuration for a platform.
        
        Args:
            platform: 'ios' or 'android'
            config_data: Configuration dictionary with feature flags and settings
            min_version: Optional minimum supported app version
            
        Returns:
            Updated configuration dictionary
            
        Raises:
            ValueError: If platform is invalid
        """
        if platform not in ['ios', 'android']:
            raise ValueError(f"Invalid platform: {platform}. Must be 'ios' or 'android'")
        
        await self.db.connect()
        try:
            # Build update data
            update_data = {'config': config_data}
            if min_version is not None:
                update_data['min_version'] = min_version
            
            # Upsert configuration
            config = await self.db.mobileconfig.upsert(
                where={'platform': platform},
                data={
                    'create': {
                        'platform': platform,
                        'min_version': min_version or '1.0.0',
                        'config': config_data
                    },
                    'update': update_data
                }
            )
            
            logger.info(
                f"Mobile configuration updated for platform: {platform}",
                extra={
                    'platform': platform,
                    'min_version': config.min_version,
                    'config_keys': list(config_data.keys())
                }
            )
            
            return {
                'id': config.id,
                'platform': config.platform,
                'min_version': config.min_version,
                'config': config.config,
                'updated_at': config.updated_at.isoformat()
            }
        finally:
            await self.db.disconnect()
    
    def is_version_supported(self, platform: str, app_version: str) -> bool:
        """
        Check if app version is supported for the platform.
        
        This is a synchronous wrapper that can be used without async context.
        For async operations, use _is_version_supported directly with database access.
        
        Args:
            platform: 'ios' or 'android'
            app_version: App version string (e.g., '1.2.3')
            
        Returns:
            True if version is supported, False otherwise
        """
        import asyncio
        
        async def _check():
            await self.db.connect()
            try:
                config = await self.db.mobileconfig.find_unique(
                    where={'platform': platform}
                )
                
                if not config:
                    # If no config exists, allow all versions
                    return True
                
                return self._is_version_supported(app_version, config.min_version)
            finally:
                await self.db.disconnect()
        
        return asyncio.run(_check())
    
    def _is_version_supported(self, app_version: str, min_version: str) -> bool:
        """
        Compare app version against minimum supported version.
        
        Args:
            app_version: App version string (e.g., '1.2.3')
            min_version: Minimum supported version string (e.g., '1.0.0')
            
        Returns:
            True if app_version >= min_version, False otherwise
        """
        try:
            return version.parse(app_version) >= version.parse(min_version)
        except Exception as e:
            logger.error(
                f"Error comparing versions: {e}",
                extra={
                    'app_version': app_version,
                    'min_version': min_version
                }
            )
            # If version parsing fails, allow the request
            return True
    
    def _get_default_config(self, platform: str) -> Dict[str, Any]:
        """
        Get default configuration when no config exists for platform.
        
        Args:
            platform: 'ios' or 'android'
            
        Returns:
            Default configuration dictionary
        """
        return {
            'id': None,
            'platform': platform,
            'min_version': '1.0.0',
            'config': {
                'features': {
                    'push_notifications': True,
                    'offline_mode': True,
                    'deep_linking': True,
                    'biometric_auth': True
                },
                'settings': {
                    'max_upload_size_mb': 50,
                    'cache_duration_hours': 24,
                    'sync_interval_minutes': 15
                }
            },
            'updated_at': None
        }
    
    async def initialize_default_configs(self):
        """
        Initialize default configurations for iOS and Android platforms.
        """
        await self.db.connect()
        try:
            default_configs = [
                {
                    'platform': 'ios',
                    'min_version': '1.0.0',
                    'config': {
                        'features': {
                            'push_notifications': True,
                            'offline_mode': True,
                            'deep_linking': True,
                            'biometric_auth': True,
                            'face_id': True,
                            'haptic_feedback': True
                        },
                        'settings': {
                            'max_upload_size_mb': 50,
                            'cache_duration_hours': 24,
                            'sync_interval_minutes': 15,
                            'image_quality': 0.85
                        },
                        'api': {
                            'base_url': 'https://api.muejam.com',
                            'timeout_seconds': 30
                        }
                    }
                },
                {
                    'platform': 'android',
                    'min_version': '1.0.0',
                    'config': {
                        'features': {
                            'push_notifications': True,
                            'offline_mode': True,
                            'deep_linking': True,
                            'biometric_auth': True,
                            'fingerprint': True,
                            'material_design': True
                        },
                        'settings': {
                            'max_upload_size_mb': 50,
                            'cache_duration_hours': 24,
                            'sync_interval_minutes': 15,
                            'image_quality': 0.85
                        },
                        'api': {
                            'base_url': 'https://api.muejam.com',
                            'timeout_seconds': 30
                        }
                    }
                }
            ]
            
            for config_data in default_configs:
                await self.db.mobileconfig.upsert(
                    where={'platform': config_data['platform']},
                    data={
                        'create': config_data,
                        'update': {}  # Don't overwrite existing configs
                    }
                )
            
            logger.info("Default mobile configurations initialized")
        finally:
            await self.db.disconnect()
