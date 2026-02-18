"""
PII Detection Configuration Service

Manages configuration for PII detection including sensitivity levels,
whitelists for false positives, and custom patterns.

Requirements:
- 9.8: Allow administrators to configure PII detection sensitivity
- 9.9: Manage whitelist for false positive patterns
"""

import logging
from typing import List, Dict, Any, Optional
from prisma import Prisma
from prisma.enums import PIIType, PIISensitivity

logger = logging.getLogger(__name__)


class PIIConfigService:
    """Service for managing PII detection configuration"""
    
    def __init__(self):
        self.db = Prisma()
    
    async def get_config(self, pii_type: PIIType) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a specific PII type.
        
        Args:
            pii_type: The PII type to get configuration for
            
        Returns:
            Configuration dictionary or None if not found
        """
        await self.db.connect()
        try:
            config = await self.db.piidetectionconfig.find_unique(
                where={'pii_type': pii_type}
            )
            
            if config:
                return {
                    'id': config.id,
                    'pii_type': config.pii_type,
                    'sensitivity': config.sensitivity,
                    'enabled': config.enabled,
                    'whitelist': config.whitelist,
                    'pattern': config.pattern,
                    'updated_at': config.updated_at.isoformat(),
                    'updated_by': config.updated_by
                }
            return None
        finally:
            await self.db.disconnect()
    
    async def get_all_configs(self) -> List[Dict[str, Any]]:
        """
        Get all PII detection configurations.
        
        Returns:
            List of configuration dictionaries
        """
        await self.db.connect()
        try:
            configs = await self.db.piidetectionconfig.find_many(
                order={'pii_type': 'asc'}
            )
            
            return [
                {
                    'id': config.id,
                    'pii_type': config.pii_type,
                    'sensitivity': config.sensitivity,
                    'enabled': config.enabled,
                    'whitelist': config.whitelist,
                    'pattern': config.pattern,
                    'updated_at': config.updated_at.isoformat(),
                    'updated_by': config.updated_by
                }
                for config in configs
            ]
        finally:
            await self.db.disconnect()
    
    async def update_config(
        self,
        pii_type: PIIType,
        user_id: str,
        sensitivity: Optional[PIISensitivity] = None,
        enabled: Optional[bool] = None,
        whitelist: Optional[List[str]] = None,
        pattern: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update configuration for a specific PII type.
        
        Args:
            pii_type: The PII type to configure
            user_id: ID of the administrator making the change
            sensitivity: Detection sensitivity level
            enabled: Whether detection is enabled
            whitelist: List of patterns to whitelist (false positives)
            pattern: Custom regex pattern for detection
            
        Returns:
            Updated configuration dictionary
        """
        await self.db.connect()
        try:
            # Build update data
            update_data = {'updated_by': user_id}
            
            if sensitivity is not None:
                update_data['sensitivity'] = sensitivity
            if enabled is not None:
                update_data['enabled'] = enabled
            if whitelist is not None:
                update_data['whitelist'] = whitelist
            if pattern is not None:
                update_data['pattern'] = pattern
            
            # Upsert configuration
            config = await self.db.piidetectionconfig.upsert(
                where={'pii_type': pii_type},
                data={
                    'create': {
                        'pii_type': pii_type,
                        'updated_by': user_id,
                        **update_data
                    },
                    'update': update_data
                }
            )
            
            logger.info(
                f"PII detection config updated",
                extra={
                    'pii_type': pii_type,
                    'updated_by': user_id,
                    'changes': update_data
                }
            )
            
            return {
                'id': config.id,
                'pii_type': config.pii_type,
                'sensitivity': config.sensitivity,
                'enabled': config.enabled,
                'whitelist': config.whitelist,
                'pattern': config.pattern,
                'updated_at': config.updated_at.isoformat(),
                'updated_by': config.updated_by
            }
        finally:
            await self.db.disconnect()
    
    async def add_to_whitelist(
        self,
        pii_type: PIIType,
        user_id: str,
        patterns: List[str]
    ) -> Dict[str, Any]:
        """
        Add patterns to the whitelist for a PII type.
        
        Args:
            pii_type: The PII type
            user_id: ID of the administrator making the change
            patterns: List of patterns to add to whitelist
            
        Returns:
            Updated configuration dictionary
        """
        await self.db.connect()
        try:
            # Get current config
            config = await self.db.piidetectionconfig.find_unique(
                where={'pii_type': pii_type}
            )
            
            # Get current whitelist
            current_whitelist = config.whitelist if config else []
            
            # Add new patterns (avoid duplicates)
            updated_whitelist = list(set(current_whitelist + patterns))
            
            # Update config
            return await self.update_config(
                pii_type=pii_type,
                user_id=user_id,
                whitelist=updated_whitelist
            )
        finally:
            await self.db.disconnect()
    
    async def remove_from_whitelist(
        self,
        pii_type: PIIType,
        user_id: str,
        patterns: List[str]
    ) -> Dict[str, Any]:
        """
        Remove patterns from the whitelist for a PII type.
        
        Args:
            pii_type: The PII type
            user_id: ID of the administrator making the change
            patterns: List of patterns to remove from whitelist
            
        Returns:
            Updated configuration dictionary
        """
        await self.db.connect()
        try:
            # Get current config
            config = await self.db.piidetectionconfig.find_unique(
                where={'pii_type': pii_type}
            )
            
            if not config:
                raise ValueError(f"No configuration found for PII type: {pii_type}")
            
            # Remove patterns from whitelist
            updated_whitelist = [
                p for p in config.whitelist if p not in patterns
            ]
            
            # Update config
            return await self.update_config(
                pii_type=pii_type,
                user_id=user_id,
                whitelist=updated_whitelist
            )
        finally:
            await self.db.disconnect()
    
    async def initialize_default_configs(self, user_id: str = 'system'):
        """
        Initialize default configurations for all PII types.
        
        Args:
            user_id: ID to record as creator (default: 'system')
        """
        await self.db.connect()
        try:
            default_configs = [
                {
                    'pii_type': PIIType.EMAIL,
                    'sensitivity': PIISensitivity.MODERATE,
                    'enabled': True,
                    'whitelist': [],
                    'updated_by': user_id
                },
                {
                    'pii_type': PIIType.PHONE,
                    'sensitivity': PIISensitivity.MODERATE,
                    'enabled': True,
                    'whitelist': ['555-0100', '555-0199'],  # Common fictional numbers
                    'updated_by': user_id
                },
                {
                    'pii_type': PIIType.SSN,
                    'sensitivity': PIISensitivity.STRICT,
                    'enabled': True,
                    'whitelist': [],
                    'updated_by': user_id
                },
                {
                    'pii_type': PIIType.CREDIT_CARD,
                    'sensitivity': PIISensitivity.STRICT,
                    'enabled': True,
                    'whitelist': [],
                    'updated_by': user_id
                }
            ]
            
            for config_data in default_configs:
                await self.db.piidetectionconfig.upsert(
                    where={'pii_type': config_data['pii_type']},
                    data={
                        'create': config_data,
                        'update': {}  # Don't overwrite existing configs
                    }
                )
            
            logger.info("Default PII detection configs initialized")
        finally:
            await self.db.disconnect()
